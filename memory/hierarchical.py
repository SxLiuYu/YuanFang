# memory/hierarchical.py
"""
分层记忆系统 — Hierarchical Memory
Hey Tuya OmniMem V2.0 启发，DeepSeek V4 稀疏记忆思路

三层结构：
- working:   当前会话，高活跃度，直接拼入 system prompt
- episodic:  跨会话情景，Qdrant/向量检索，按重要性评分
- long_term: 持久化压缩记忆，LLM summarization 后存储

重要性评分驱动，自动裁剪低价值记忆
"""
import time
import json
import threading
import logging
from pathlib import Path
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)


@dataclass
class MemoryEntry:
    """单条记忆条目"""
    content: str
    importance: float = 5.0        # 1-10 重要性评分
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    memory_type: str = "short"      # short | episodic | long
    embedding: Optional[list] = None
    tags: list[str] = field(default_factory=list)  # 标签：人/地点/设备/偏好
    source: str = "interaction"      # 来源：interaction/sensor/rule/manual

    def access(self):
        self.access_count += 1
        self.last_access = time.time()
        # 频繁访问自动提升重要性
        if self.access_count > 5:
            self.importance = min(10.0, self.importance + 0.1)

    def to_dict(self) -> dict:
        return {
            "content": self.content,
            "importance": self.importance,
            "access_count": self.access_count,
            "last_access": self.last_access,
            "memory_type": self.memory_type,
            "tags": self.tags,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MemoryEntry":
        return cls(
            content=d["content"],
            importance=d.get("importance", 5.0),
            access_count=d.get("access_count", 0),
            last_access=d.get("last_access", time.time()),
            memory_type=d.get("memory_type", "short"),
            tags=d.get("tags", []),
            source=d.get("source", "interaction"),
        )


class HierarchicalMemory:
    """
    三层稀疏记忆系统

    核心思想（DeepSeek V4 DSA 启发）：
    - 不所有记忆都以同等精度处理
    - 高重要性 + 高访问 = 精细存储
    - 低重要性 + 低访问 = 压缩或丢弃
    """

    MAX_WORKING = 20       # 工作记忆上限
    MAX_EPISODIC = 500     # 情景记忆上限
    COMPRESS_THRESHOLD = 100  # 触发压缩的条目数
    PERSIST_FILE = Path(__file__).parent / "hierarchical_memory.json"
    PERSIST_LOCK = threading.Lock()

    def __init__(self, llm_fn=None, vector_store=None):
        self.working: list[MemoryEntry] = []
        self.episodic: list[MemoryEntry] = []
        self.long_term_refs: dict[str, dict] = {}  # key -> compressed_summary
        self.llm_fn = llm_fn                       # LLM function for summarization
        self.vector_store = vector_store            # Qdrant or simple dict

        # 标签统计（用于快速查找）
        self._tag_index: dict[str, list[MemoryEntry]] = defaultdict(list)

        self._load()

    # ─── 添加记忆 ───────────────────────────────────────────────

    def add(
        self,
        content: str,
        memory_type: str = "short",
        importance: float = 5.0,
        tags: list[str] = None,
        source: str = "interaction",
        embedding: list = None,
    ) -> str:
        """
        添加记忆 — 重要性评分驱动自动分层

        Args:
            content: 记忆内容
            memory_type: short(工作) / episodic(情景) / long(长期压缩)
            importance: 1-10 重要性评分
            tags: 标签列表
            source: 来源
            embedding: 向量（可选）

        Returns:
            记忆 ID
        """
        entry = MemoryEntry(
            content=content,
            importance=importance,
            memory_type=memory_type,
            tags=tags or [],
            source=source,
            embedding=embedding,
        )

        if memory_type == "short":
            self.working.append(entry)
            self._prune_working()
        elif memory_type == "episodic":
            self.episodic.append(entry)
            self._update_tag_index(entry)
            self._prune_episodic()
        elif memory_type == "long":
            self._compress_and_store(entry)

        # 异步持久化
        threading.Thread(target=self._persist, daemon=True).start()
        return f"{memory_type[0]}_{int(entry.last_access * 1000)}"

    def add_interaction(self, role: str, content: str, importance: float = 5.0):
        """快捷方法：添加对话交互记忆"""
        tag = "user" if role == "user" else "assistant"
        self.add(
            content=f"[{role}] {content}",
            memory_type="episodic",
            importance=importance,
            tags=[tag, "conversation"],
            source="interaction",
        )

    def add_sensor_event(self, entity_id: str, value: any, importance: float = 5.0):
        """快捷方法：添加传感器事件记忆"""
        self.add(
            content=f"传感器 {entity_id} = {value}",
            memory_type="episodic",
            importance=importance,
            tags=["sensor", entity_id.split(".")[0] if "." in entity_id else "device"],
            source="sensor",
        )

    def add_device_action(self, action: str, entity_id: str, result: str = "success"):
        """快捷方法：添加设备操作记忆"""
        self.add(
            content=f"执行 {action} → {entity_id}，结果：{result}",
            memory_type="episodic",
            importance=6.0,
            tags=["device_action", entity_id.split(".")[0] if "." in entity_id else "device"],
            source="rule",
        )

    # ─── 检索 ─────────────────────────────────────────────────

    def get_working_context(self, max_entries: int = 10) -> str:
        """
        获取工作记忆上下文 — 直接拼入 system prompt
        按重要性排序，返回 top N
        """
        if not self.working:
            return ""

        scored = sorted(
            self.working,
            key=lambda e: e.importance * (1 + 0.1 * e.access_count),
            reverse=True,
        )
        top = scored[:max_entries]

        lines = ["[Working Memory] 近期重要信息："]
        for e in top:
            age_min = (time.time() - e.last_access) / 60
            lines.append(f"- [{e.tags[0] if e.tags else 'misc'}|★{e.importance:.0f}|{age_min:.0f}m] {e.content[:80]}")
        return "\n".join(lines)

    def search_episodic(self, query: str, tags: list[str] = None, top_k: int = 5) -> list[str]:
        """
        检索情景记忆
        支持关键词匹配 + 标签过滤
        """
        results = []
        search_tags = set(tags) if tags else None

        # 优先搜索有标签的记忆
        candidates = self.episodic
        if search_tags:
            tagged = []
            for t in search_tags:
                tagged.extend(self._tag_index.get(t, []))
            # 去重并合并
            seen = set()
            for e in tagged:
                if id(e) not in seen:
                    seen.add(id(e))
                    candidates.append(e)

        for e in candidates:
            score = e.importance / 10.0

            # 关键词匹配
            query_words = [w for w in query.split() if len(w) > 1]
            matched = sum(1 for w in query_words if w in e.content)
            if matched > 0:
                score += matched * 0.2

            # 标签匹配加分
            if search_tags and any(t in e.tags for t in search_tags):
                score += 0.3

            # 近期加权
            age_hours = (time.time() - e.last_access) / 3600
            if age_hours < 1:
                score *= 1.5
            elif age_hours < 24:
                score *= 1.2

            results.append((e, score))

        results.sort(key=lambda x: x[1], reverse=True)
        return [
            f"- [{'|'.join(e.tags[:2])}|★{e.importance:.0f}] {e.content[:100]}"
            for e, _ in results[:top_k]
        ]

    def search_long_term(self, query: str, top_k: int = 3) -> list[str]:
        """检索长期记忆（压缩存储的摘要）"""
        results = []
        query_words = set(query.split())
        for key, ref in self.long_term_refs.items():
            summary = ref.get("summary", "")
            hint = ref.get("original_hint", "")
            text = summary + hint
            matched = sum(1 for w in query_words if w in text)
            if matched > 0:
                results.append((ref, matched))
        results.sort(key=lambda x: x[1], reverse=True)
        return [
            f"- [长期记忆] {r[0].get('summary', '')[:100]}"
            for r, _ in results[:top_k]
        ]

    def get_full_context(self, query: str = "", max_working: int = 10, max_episodic: int = 5) -> str:
        """
        获取完整记忆上下文（供 LLM 使用）
        工作记忆 + 情景记忆 + 长期记忆
        """
        parts = []

        wm = self.get_working_context(max_working)
        if wm:
            parts.append(wm)

        em = self.search_episodic(query, top_k=max_episodic)
        if em:
            parts.append("[Episodic Memory] 相关情景记忆：\n" + "\n".join(em))

        lm = self.search_long_term(query, top_k=3)
        if lm:
            parts.append("[Long Term Memory] 长期记忆：\n" + "\n".join(lm))

        return "\n\n".join(parts) if parts else ""

    # ─── 裁剪 ─────────────────────────────────────────────────

    def _prune_working(self):
        """工作记忆裁剪 — 保留最重要和最新的"""
        if len(self.working) <= self.MAX_WORKING:
            return

        scored = sorted(
            self.working,
            key=lambda e: e.importance * (1 + 0.1 * e.access_count),
            reverse=True,
        )
        self.working = scored[: self.MAX_WORKING]

    def _prune_episodic(self):
        """情景记忆裁剪 — 超过上限则压缩最旧的低价值记忆"""
        if len(self.episodic) <= self.MAX_EPISODIC:
            return

        # 按 score 排序，将最低的压缩到长期记忆
        scored = sorted(
            self.episodic,
            key=lambda e: e.importance * (1 + 0.05 * e.access_count),
        )
        to_compress = scored[: len(self.episodic) - self.MAX_EPISODIC + 10]

        for entry in to_compress:
            self.episodic.remove(entry)
            self._compress_and_store(entry)
            # 从标签索引移除
            for tag in entry.tags:
                if entry in self._tag_index.get(tag, []):
                    self._tag_index[tag].remove(entry)

    def _compress_and_store(self, entry: MemoryEntry):
        """压缩存储 — LLM summarization"""
        key = f"lt_{int(entry.last_access * 1000)}"

        if self.llm_fn and len(entry.content) > 200:
            try:
                summary = self.llm_fn.chat_simple([
                    {"role": "user", "content": f"请用不超过50字概括以下内容的核心信息：{entry.content}"}
                ])
                if summary and len(summary) < len(entry.content):
                    self.long_term_refs[key] = {
                        "summary": summary,
                        "importance": entry.importance,
                        "original_hint": entry.content[:50],
                        "compressed_at": time.time(),
                        "tags": entry.tags,
                    }
                else:
                    self.long_term_refs[key] = {
                        "summary": entry.content[:100],
                        "importance": entry.importance,
                    }
            except Exception as e:
                logger.debug(f"[HierarchicalMemory] Compression failed: {e}")
                self.long_term_refs[key] = {
                    "summary": entry.content[:100],
                    "importance": entry.importance,
                }
        else:
            self.long_term_refs[key] = {
                "summary": entry.content[:100],
                "importance": entry.importance,
            }

        # 限制长期记忆大小
        if len(self.long_term_refs) > 1000:
            sorted_refs = sorted(
                self.long_term_refs.items(),
                key=lambda x: x[1].get("importance", 0),
                reverse=True,
            )
            self.long_term_refs = dict(sorted_refs[:500])

    def _update_tag_index(self, entry: MemoryEntry):
        """更新标签索引"""
        for tag in entry.tags:
            if entry not in self._tag_index[tag]:
                self._tag_index[tag].append(entry)

    # ─── 持久化 ───────────────────────────────────────────────

    def _persist(self):
        """异步持久化到文件"""
        with self.PERSIST_LOCK:
            try:
                data = {
                    "working": [e.to_dict() for e in self.working],
                    "episodic": [e.to_dict() for e in self.episodic],
                    "long_term": self.long_term_refs,
                    "saved_at": time.time(),
                }
                self.PERSIST_FILE.write_text(
                    json.dumps(data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception as e:
                logger.error(f"[HierarchicalMemory] Persist failed: {e}")

    def _load(self):
        """启动时从文件加载记忆"""
        if not self.PERSIST_FILE.exists():
            return
        try:
            data = json.loads(self.PERSIST_FILE.read_text("utf-8"))
            self.working = [MemoryEntry.from_dict(e) for e in data.get("working", [])]
            self.episodic = [MemoryEntry.from_dict(e) for e in data.get("episodic", [])]
            self.long_term_refs = data.get("long_term", {})
            for e in self.episodic:
                self._update_tag_index(e)
            logger.info(
                f"[HierarchicalMemory] Loaded: {len(self.working)} working, "
                f"{len(self.episodic)} episodic, {len(self.long_term_refs)} long_term"
            )
        except Exception as e:
            logger.error(f"[HierarchicalMemory] Load failed: {e}")

    # ─── 统计 ─────────────────────────────────────────────────

    def stats(self) -> dict:
        return {
            "working_count": len(self.working),
            "episodic_count": len(self.episodic),
            "long_term_count": len(self.long_term_refs),
            "total_tags": len(self._tag_index),
            "top_tags": sorted(
                [(t, len(es)) for t, es in self._tag_index.items()],
                key=lambda x: x[1],
                reverse=True,
            )[:10],
        }
