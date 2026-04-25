# routes/memory_sync.py
"""
Memory Sync Routes — OpenClaw ↔ YuanFang 记忆打通
"""
from flask import Blueprint, request, jsonify
import logging
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

logger = logging.getLogger(__name__)
memory_bp = Blueprint("memory_sync", __name__, url_prefix="/api/memory")

# YuanFang 数据路径
YuanFang_ROOT = Path(__file__).parent.parent
CONVERSATION_LOG = YuanFang_ROOT / "data" / "conversation_log.json"
EMOTIONAL_JSON = YuanFang_ROOT / "memory" / "emotional.json"
OPENCLAW_MEMORY = Path("~/.openclaw/workspace/MEMORY.md").expanduser()
IMPORTANT_NOTES = YuanFang_ROOT / "data" / "important_notes.md"

# 重要信息关键词（从对话中提取）
IMPORTANT_PATTERNS = [
    (r"IP[:\s]+(\d+\.\d+\.\d+\.\d+)", "IP地址"),
    (r"(?:密码|password)[:\s]+(\S+)", "密码"),
    (r"(?:手机|phone|mobile)[:\s]+(\S+)", "联系方式"),
    (r"(?:GitHub|github)[:\s]+(\S+)", "GitHub相关"),
    (r"(?:记住|remember|别忘了)", "待办/提醒"),
    (r"(?:喜欢|prefer|讨厌|hate)", "偏好"),
]


def _read_json(path: Path, default=None):
    if path.exists():
        try:
            return json.loads(path.read_text("utf-8"))
        except:
            pass
    return default if default is not None else []


def _read_lines(path: Path) -> list:
    if path.exists():
        return path.read_text("utf-8").splitlines()
    return []


def init_memory_routes(app):
    app.register_blueprint(memory_bp)
    logger.info("[Memory] 路由已注册: /api/memory")


# ==================== 对话记录 ====================

@memory_bp.route("/conversations", methods=["GET"])
def get_conversations():
    """获取最近的对话记录"""
    limit = int(request.args.get("limit", 20))
    logs = _read_json(CONVERSATION_LOG, [])
    return jsonify({
        "conversations": logs[-limit:],
        "count": len(logs),
    })


@memory_bp.route("/conversations/recent", methods=["GET"])
def recent_conversations():
    """获取最近 N 天的对话"""
    days = int(request.args.get("days", 7))
    logs = _read_json(CONVERSATION_LOG, [])
    
    cutoff = datetime.now() - timedelta(days=days)
    recent = []
    for entry in reversed(logs):
        try:
            ts = datetime.fromisoformat(entry.get("timestamp", ""))
            if ts >= cutoff:
                recent.append(entry)
        except:
            pass
    
    return jsonify({
        "conversations": recent,
        "count": len(recent),
        "days": days,
    })


# ==================== 情感记忆 ====================

@memory_bp.route("/emotional", methods=["GET"])
def get_emotional():
    """获取情感记忆摘要"""
    entries = _read_json(EMOTIONAL_JSON, [])
    top_k = int(request.args.get("top_k", 20))
    emotion = request.args.get("emotion", None)
    
    if emotion:
        entries = [e for e in entries if e.get("emotion") == emotion]
    
    entries = sorted(entries, key=lambda x: x.get("intensity", 0), reverse=True)[:top_k]
    
    stats = {}
    for e in _read_json(EMOTIONAL_JSON, []):
        em = e.get("emotion", "neutral")
        stats[em] = stats.get(em, 0) + 1
    
    return jsonify({
        "entries": entries,
        "stats": stats,
        "total": len(_read_json(EMOTIONAL_JSON, [])),
    })


# ==================== 重要信息提取 ====================

@memory_bp.route("/important", methods=["GET"])
def get_important():
    """获取已标记的重要笔记"""
    if not IMPORTANT_NOTES.exists():
        return jsonify({"notes": [], "count": 0})
    
    content = IMPORTANT_NOTES.read_text("utf-8")
    return jsonify({
        "content": content,
        "count": len(content.split("\n## ")) - 1,
    })


@memory_bp.route("/important", methods=["POST"])
def add_important():
    """添加重要笔记"""
    data = request.get_json() or {}
    content = data.get("content", "").strip()
    if not content:
        return jsonify({"error": "内容不能为空"}), 400
    
    IMPORTANT_NOTES.parent.mkdir(parents=True, exist_ok=True)
    with open(IMPORTANT_NOTES, "a", encoding="utf-8") as f:
        f.write(f"\n## {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"{content}\n")
    
    return jsonify({"status": "ok", "added": True})


# ==================== 记忆同步 ====================

@memory_bp.route("/sync", methods=["POST"])
def sync_to_openclaw():
    """
    同步重要记忆到 OpenClaw MEMORY.md
    从对话记录中提取关键信息，追加到 MEMORY.md
    """
    days = int(request.get_json() or {}).get("days", 7)
    
    if not OPENCLAW_MEMORY.exists():
        return jsonify({"error": "OpenClaw MEMORY.md 不存在", "path": str(OPENCLAW_MEMORY)}), 404
    
    logs = _read_json(CONVERSATION_LOG, [])
    cutoff = datetime.now() - timedelta(days=days)
    
    # 提取重要对话
    important_entries = []
    for entry in logs:
        try:
            ts = datetime.fromisoformat(entry.get("timestamp", ""))
            if ts >= cutoff:
                user_text = entry.get("user_text", "")
                assistant_text = entry.get("assistant_text", "")
                # 提取关键信息
                facts = _extract_facts(user_text + " " + assistant_text)
                if facts:
                    important_entries.append({
                        "timestamp": entry.get("timestamp", ""),
                        "facts": facts,
                        "user": user_text[:100],
                        "assistant": assistant_text[:100],
                    })
        except:
            pass
    
    if not important_entries:
        return jsonify({"synced": 0, "message": "没有新的重要信息"})
    
    # 追加到 MEMORY.md
    try:
        existing = OPENCLAW_MEMORY.read_text("utf-8")
        
        sync_block = f"\n\n## 🔄 YuanFang 对话同步 ({datetime.now().strftime('%Y-%m-%d')})\n"
        for ie in important_entries:
            sync_block += f"\n### {ie['timestamp'][:16]}\n"
            for fact in ie['facts']:
                sync_block += f"- {fact}\n"
        
        # 避免重复同步
        if sync_block not in existing:
            OPENCLAW_MEMORY.write_text(existing + sync_block, "utf-8")
            return jsonify({
                "synced": len(important_entries),
                "facts": sum(len(ie['facts']) for ie in important_entries),
                "path": str(OPENCLAW_MEMORY),
            })
        else:
            return jsonify({"synced": 0, "message": "已是最新"})
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def _extract_facts(text: str) -> list:
    """从文本中提取关键事实"""
    facts = []
    text_lower = text.lower()
    
    extractors = [
        # 项目/技术
        (r"(?:用了?|使用|基于|基于) (\w+(?:\s+\w+){0,3}?\S+)", "技术/项目"),
        # IP地址
        (r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", "IP地址"),
        # 文件路径
        (r"(?:/[\w\-./]+(?:py|md|json|sh))", "文件路径"),
        # 端口号
        (r"端口[是为]?[:\s]*(\d+)", "端口"),
        # 决定/决策
        (r"(?:决定|采用|选择|用|不用|不要)", "决策"),
        # 错误/问题
        (r"(?:错误|失败|Error|Failed|bug|问题)", "问题"),
        # 成功/完成
        (r"(?:成功|完成|完成|✅|好了)", "状态"),
    ]
    
    for pattern, label in extractors:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for m in matches[:2]:  # 每个pattern最多取2个
            if len(str(m)) > 3 and len(str(m)) < 100:
                facts.append(f"[{label}] {m}")
    
    return list(dict.fromkeys(facts))  # 去重保持顺序


# ==================== 健康检查 ====================

@memory_bp.route("/status", methods=["GET"])
def status():
    """记忆系统状态"""
    logs = _read_json(CONVERSATION_LOG, [])
    emotional = _read_json(EMOTIONAL_JSON, [])
    
    return jsonify({
        "conversation_log": {
            "path": str(CONVERSATION_LOG),
            "exists": CONVERSATION_LOG.exists(),
            "count": len(logs),
        },
        "emotional_memory": {
            "path": str(EMOTIONAL_JSON),
            "exists": EMOTIONAL_JSON.exists(),
            "count": len(emotional),
        },
        "important_notes": {
            "path": str(IMPORTANT_NOTES),
            "exists": IMPORTANT_NOTES.exists(),
        },
        "openclaw_memory": {
            "path": str(OPENCLAW_MEMORY),
            "exists": OPENCLAW_MEMORY.exists(),
        },
    })
