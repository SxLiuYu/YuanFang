"""
YuanFang Skill Engine
Skill registration, matching, learning, and abstraction
"""
import os
import json
import uuid
import datetime
import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

SKILL_DIR = Path(__file__).parent / "skills"
SKILL_DIR.mkdir(exist_ok=True)

SKILL_INDEX_FILE = SKILL_DIR / "skill_index.json"


class Skill:
    """Single skill definition"""

    def __init__(self, name: str, description: str, category: str = "general",
                 trigger_patterns: list = None, ha_commands: list = None,
                 response_template: str = "", auto_learned: bool = False,
                 quality_score: float = 5.0, metadata: dict = None):
        self.id = str(uuid.uuid4())[:8]
        self.name = name
        self.description = description
        self.category = category
        self.trigger_patterns = trigger_patterns or []
        self.ha_commands = ha_commands or []
        self.response_template = response_template
        self.auto_learned = auto_learned
        self.quality_score = quality_score
        self.use_count = 0
        self.success_count = 0
        self.metadata = metadata or {}
        self.created_at = datetime.datetime.now().isoformat()
        self.last_used = None

    def to_dict(self) -> dict:
        return {
            "id": self.id, "name": self.name, "description": self.description,
            "category": self.category, "trigger_patterns": self.trigger_patterns,
            "ha_commands": self.ha_commands, "response_template": self.response_template,
            "auto_learned": self.auto_learned, "quality_score": self.quality_score,
            "use_count": self.use_count, "success_count": self.success_count,
            "metadata": self.metadata, "created_at": self.created_at,
            "last_used": self.last_used,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Skill":
        skill = cls.__new__(cls)
        for k, v in data.items():
            setattr(skill, k, v)
        return skill

    def match(self, query: str) -> float:
        if not self.trigger_patterns:
            return 0.0
        query_lower = query.lower()
        max_score = 0.0
        for pattern in self.trigger_patterns:
            pattern_lower = pattern.lower()
            if pattern_lower in query_lower:
                ratio = len(pattern_lower) / max(len(query_lower), 1)
                score = 0.5 + 0.5 * ratio
                max_score = max(max_score, score)
            else:
                words = pattern_lower.split()
                matched = sum(1 for w in words if w in query_lower)
                if matched > 0:
                    score = 0.3 * (matched / len(words))
                    max_score = max(max_score, score)
        return min(max_score, 1.0)

    def record_use(self, success: bool = True):
        self.use_count += 1
        if success:
            self.success_count += 1
        self.last_used = datetime.datetime.now().isoformat()
        if self.use_count >= 3:
            self.quality_score = round(self.success_count / self.use_count * 10, 1)


class SkillEngine:
    """
    YuanFang Skill Engine
    Core capabilities:
    1. Skill registration and management (manual + auto-learned)
    2. Intent -> skill matching (execute directly when matched)
    3. Skill abstraction (extract patterns from conversation history)
    4. Reuse statistics and quality evaluation
    """

    def __init__(self):
        self._skills: dict[str, Skill] = {}
        self._load_index()

    def _load_index(self):
        if SKILL_INDEX_FILE.exists():
            try:
                data = json.loads(SKILL_INDEX_FILE.read_text("utf-8"))
                for skill_id, skill_data in data.get("skills", {}).items():
                    self._skills[skill_id] = Skill.from_dict(skill_data)
                print(f"[SkillEngine] Loaded {len(self._skills)} skills")
            except Exception as e:
                print(f"[SkillEngine] Load failed: {e}")

    def _save_index(self):
        data = {"skills": {}, "categories": {}}
        for sid, skill in self._skills.items():
            data["skills"][sid] = skill.to_dict()
            cat = skill.category
            if cat not in data["categories"]:
                data["categories"][cat] = []
            data["categories"][cat].append(sid)
        SKILL_INDEX_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    # ──── Skill management ────

    def register(self, skill: Skill) -> str:
        self._skills[skill.id] = skill
        self._save_index()
        print(f"[SkillEngine] Registered {skill.name} ({skill.id}) [{skill.category}]")
        return skill.id

    def unregister(self, skill_id: str) -> bool:
        if skill_id in self._skills:
            name = self._skills[skill_id].name
            del self._skills[skill_id]
            self._save_index()
            print(f"[SkillEngine] Unregistered {name} ({skill_id})")
            return True
        return False

    def get(self, skill_id: str) -> Optional[Skill]:
        return self._skills.get(skill_id)

    def list_skills(self, category: str = None) -> list[dict]:
        skills = []
        for skill in self._skills.values():
            if category and skill.category != category:
                continue
            skills.append(skill.to_dict())
        return sorted(skills, key=lambda x: x.get("use_count", 0), reverse=True)

    # ──── Skill matching ────

    def match(self, query: str, threshold: float = 0.4, top_k: int = 3) -> list[tuple[Skill, float]]:
        results = []
        for skill in self._skills.values():
            score = skill.match(query)
            if score >= threshold:
                results.append((skill, score))
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def try_execute(self, query: str, ha_executor=None) -> Optional[dict]:
        matches = self.match(query, threshold=0.7, top_k=1)
        if not matches:
            return None

        skill, score = matches[0]
        print(f"[SkillEngine] Matched {skill.name} (confidence {score:.2f})")

        result = {
            "skill_id": skill.id,
            "skill_name": skill.name,
            "confidence": round(score, 2),
            "response": skill.response_template or f"Executed {skill.name}",
            "ha_executed": False,
        }

        if skill.ha_commands and ha_executor:
            try:
                ha_results = ha_executor(skill.ha_commands)
                result["ha_results"] = ha_results
                result["ha_executed"] = True
                success_count = sum(1 for r in ha_results if r.get("success"))
                if skill.response_template:
                    result["response"] = skill.response_template
                else:
                    result["response"] = f"Executed {skill.name}, {success_count}/{len(ha_results)} succeeded"
            except Exception as e:
                result["ha_error"] = str(e)

        skill.record_use(success=True)
        self._save_index()
        return result

    # ──── Skill learning ────

    def learn_from_interaction(self, user_text: str, ai_response: str,
                                ha_commands: list = None) -> Optional[Skill]:
        if not ha_commands:
            return None
        existing = self.match(user_text, threshold=0.6)
        if existing:
            return None
        skill_name = self._extract_skill_name(user_text)
        if not skill_name:
            return None
        trigger_patterns = self._extract_trigger_patterns(user_text)
        skill = Skill(
            name=skill_name,
            description=f"Auto-learned: {user_text[:50]}",
            category="ha_control",
            trigger_patterns=trigger_patterns,
            ha_commands=ha_commands,
            response_template=ai_response[:100] if ai_response else "",
            auto_learned=True,
            quality_score=5.0,
        )
        self.register(skill)
        print(f"[SkillEngine] Learned new skill: {skill_name}")
        return skill

    def _extract_skill_name(self, text: str) -> str:
        patterns = [
            r"[把将](.{2,10})(打开|关闭|开启|关掉|调到|设为)",
            r"(打开|关闭|开启|关掉|启动|停止)(.{2,15})",
            r"((晚安|早安|出门|回家|离家|在家)模式)",
            r"(全屋|所有(打开|关闭|开启|关掉))",
        ]
        for p in patterns:
            m = re.search(p, text)
            if m:
                name = m.group(0).strip()
                if 2 <= len(name) <= 20:
                    return name
        return None

    def _extract_trigger_patterns(self, text: str) -> list[str]:
        patterns = []
        action_words = ["打开", "关闭", "开启", "关掉", "启动", "停止", "调到", "设为",
                        "开灯", "关灯", "开空调", "关空调", "锁门", "开窗", "关窗",
                        "晚安", "早安", "出门", "回家", "离家", "在家"]
        for w in action_words:
            if w in text:
                patterns.append(w)
        device_words = ["灯", "空调", "窗帘", "门锁", "热水器", "加湿器", "电视", "音箱",
                        "卧室", "客厅", "厨房", "书房", "卫生间", "阳台"]
        for w in device_words:
            if w in text:
                patterns.append(w)
        return list(set(patterns))

    # ──── Skill abstraction ────

    def abstract_from_history(self, interactions: list[dict], min_occurrences: int = 3) -> list[Skill]:
        if not interactions or len(interactions) < min_occurrences:
            return []

        from collections import Counter
        pattern_counter = Counter()
        pattern_examples = {}

        for interaction in interactions:
            ha_cmds = interaction.get("ha_commands", [])
            if not ha_cmds:
                continue
            sig_parts = []
            for cmd in ha_cmds:
                if isinstance(cmd, dict):
                    sig = f"{cmd.get('entity_id', '?')}:{cmd.get('action', '?')}"
                    sig_parts.append(sig)
            if sig_parts:
                sig = " | ".join(sorted(sig_parts))
                pattern_counter[sig] += 1
                if sig not in pattern_examples:
                    pattern_examples[sig] = interaction.get("user_text", "")

        new_skills = []
        for sig, count in pattern_counter.most_common():
            if count < min_occurrences:
                break
            existing_match = False
            for skill in self._skills.values():
                if skill.ha_commands:
                    existing_sigs = [f"{c.get('entity_id','?')}:{c.get('action','?')}"
                                    for c in skill.ha_commands if isinstance(c, dict)]
                    if set(existing_sigs) == set(sig.split(" | ")):
                        existing_match = True
                        break
            if existing_match:
                continue

            example_text = pattern_examples.get(sig, "")
            skill_name = self._extract_skill_name(example_text) or f"AutoSkill_{sig[:20]}"
            actual_cmds = []
            for interaction in reversed(interactions):
                cmds = interaction.get("ha_commands", [])
                if cmds:
                    actual_cmds = cmds
                    break

            skill = Skill(
                name=skill_name,
                description=f"Abstracted from {count} interactions: {sig}",
                category="ha_control",
                trigger_patterns=self._extract_trigger_patterns(example_text),
                ha_commands=actual_cmds,
                auto_learned=True,
                quality_score=min(5.0 + count * 0.5, 9.0),
                metadata={"occurrence_count": count, "pattern_sig": sig},
            )
            self.register(skill)
            new_skills.append(skill)
            logger.info(f"Abstracted skill: {skill_name} (occurrence {count})")

        return new_skills

    # ──── Report ────

    def report(self) -> dict:
        total = len(self._skills)
        categories = {}
        for skill in self._skills.values():
            cat = skill.category
            if cat not in categories:
                categories[cat] = {"count": 0, "total_uses": 0}
            categories[cat]["count"] += 1
            categories[cat]["total_uses"] += skill.use_count

        auto_learned = sum(1 for s in self._skills.values() if s.auto_learned)
        total_uses = sum(s.use_count for s in self._skills.values())
        total_success = sum(s.success_count for s in self._skills.values())
        success_rate = (total_success / total_uses * 100) if total_uses > 0 else 0

        return {
            "total_skills": total,
            "auto_learned": auto_learned,
            "manual": total - auto_learned,
            "total_uses": total_uses,
            "success_rate": round(success_rate, 1),
            "categories": categories,
            "message": f"{total} skills (auto {auto_learned}), {total_uses} uses, {success_rate:.1f}% success",
        }

    def get_skill_prompt_context(self) -> str:
        if not self._skills:
            return ""
        lines = ["[Learned Skills] Direct execution available - no replanning needed:"]
        for skill in sorted(self._skills.values(), key=lambda s: s.use_count, reverse=True)[:10]:
            ha_desc = ""
            if skill.ha_commands:
                ha_desc = " -> " + ", ".join(
                    f"{c.get('entity_id','?')}({c.get('action','?')})"
                    for c in skill.ha_commands[:3] if isinstance(c, dict)
                )
            lines.append(f"- {skill.name}: {skill.description[:40]}{ha_desc}")
        return "\n".join(lines)


# ──── Builtin skills ────

def _create_builtin_skills() -> list[Skill]:
    return [
        Skill(
            name="晚安模式",
            description="关闭所有灯光，空调调至睡眠温度",
            category="ha_control",
            trigger_patterns=["晚安", "睡觉", "关灯睡觉", "睡眠模式"],
            ha_commands=[{"entity_id": "scene.good_night", "action": "activate_scene"}],
            response_template="晚安，已为你调整好睡眠环境",
            quality_score=8.0,
        ),
        Skill(
            name="早安模式",
            description="打开窗帘，开启客厅灯",
            category="ha_control",
            trigger_patterns=["早安", "早上好", "起床", "早上"],
            ha_commands=[{"entity_id": "scene.good_morning", "action": "activate_scene"}],
            response_template="早安！已为你开启晨间模式",
            quality_score=8.0,
        ),
        Skill(
            name="离家模式",
            description="关闭所有设备，锁门",
            category="ha_control",
            trigger_patterns=["出门", "离家", "走了", "上班", "外出"],
            ha_commands=[{"entity_id": "scene.leaving_home", "action": "activate_scene"}],
            response_template="已切换离家模式，所有设备已关闭",
            quality_score=8.0,
        ),
        Skill(
            name="回家模式",
            description="打开客厅灯和空调",
            category="ha_control",
            trigger_patterns=["回家", "到家了", "回来了", "开灯开空调"],
            ha_commands=[{"entity_id": "scene.coming_home", "action": "activate_scene"}],
            response_template="欢迎回家！已为你调整好环境",
            quality_score=8.0,
        ),
        Skill(
            name="全屋关灯",
            description="关闭所有灯光",
            category="ha_control",
            trigger_patterns=["全屋关灯", "关所有灯", "全部关灯", "把灯都关掉"],
            ha_commands=[{"entity_id": "scene.all_lights_off", "action": "activate_scene"}],
            response_template="已关闭全屋灯光",
            quality_score=9.0,
        ),
        Skill(
            name="环境报告",
            description="播报当前室内温湿度和空气质量",
            category="conversation",
            trigger_patterns=["环境", "温湿度", "空气质量", "家里什么情况"],
            response_template="当前室内温度{temp}度，湿度{humidity}%，空气质量{aqi}良好",
            quality_score=7.0,
        ),
    ]


# ──── Global singleton ────

_engine: "SkillEngine | None" = None


def get_skill_engine() -> "SkillEngine":
    global _engine
    if _engine is None:
        _engine = SkillEngine()
        if not _engine._skills:
            for skill in _create_builtin_skills():
                _engine.register(skill)
    return _engine


def _execute_ha_for_skill(commands: list) -> list:
    try:
        from routes.chat import _execute_ha_commands
        return _execute_ha_commands(commands)
    except ImportError:
        return [{"success": False, "result": "Cannot import HA executor"}]
