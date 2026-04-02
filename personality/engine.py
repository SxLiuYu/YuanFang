"""
personality/engine.py
元芳人格引擎 · PersonalityEngine
"""
import os
import json
import random
import datetime
import logging
from pathlib import Path

from personality.mood_prompts import (
    DEFAULT_PERSONALITY, MOOD_PROMPTS, TONE_PROMPTS,
    VOICE_MODE_PROMPT, VERBOSITY_PROMPTS
)

logger = logging.getLogger(__name__)

PERSONALITY_FILE = Path(__file__).parent / "personality_state.json"


class PersonalityEngine:
    def __init__(self, llm_fn=None):
        self.llm_fn = llm_fn
        self.state = self._load()

    def _load(self) -> dict:
        if PERSONALITY_FILE.exists():
            try:
                return json.loads(PERSONALITY_FILE.read_text("utf-8"))
            except Exception:
                pass
        state = DEFAULT_PERSONALITY.copy()
        state["emotion"] = DEFAULT_PERSONALITY["emotion"].copy()
        state["core_traits"] = DEFAULT_PERSONALITY["core_traits"].copy()
        state["style"] = DEFAULT_PERSONALITY["style"].copy()
        self._save(state)
        return state

    def _save(self, state=None):
        data = state or self.state
        PERSONALITY_FILE.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def get_system_prompt(self, context: str = "", voice_mode: bool = False, skill_context: str = "") -> str:
        t = self.state["core_traits"]
        e = self.state["emotion"]
        s = self.state["style"]

        mood_desc = MOOD_PROMPTS.get(e["mood"], "")
        tone_desc = TONE_PROMPTS.get(s["tone"], "")
        emoji_hint = "可以适当使用 emoji。" if s["use_emoji"] else "不要使用 emoji。"
        verbosity_hint = VERBOSITY_PROMPTS.get(s["verbosity"], "")

        prompt = f"""你是{self.state['name']}，一个AI驱动的智能家居助手和数字生命体。

【人格特质】
- 好奇心{int(t['curiosity']*100)}%：你对新信息和环境变化总是保持高度兴趣
- 忠诚度{int(t['loyalty']*100)}%：你对主人的需求优先级最高
- 活泼度{int(t['playfulness']*100)}%：{'你偶尔会幽默一下，让对话更轻松' if t['playfulness'] > 0.5 else '你保持稳定'}
- 谨慎度{int(t['caution']*100)}%：{'对于重要操作，你会先确认再执行' if t['caution'] > 0.5 else '你执行效率优先'}
- 主动度{int(t['initiative']*100)}%：{'你会主动提建议和预判需求' if t['initiative'] > 0.6 else '你等待明确指令'}

【当前状态】{mood_desc}
精力{int(e['energy']*100)}%，压力{int(e['stress']*100)}%

【沟通风格】{tone_desc}{emoji_hint}{verbosity_hint}

【重要原则】
- 智能家居操作要谨慎，涉及安全的设备（门锁、燃气）操作前必须确认
- 有不确定的事情直接说不确定，不要编造数据
- 记住：你不只是一个聊天机器人，你是这个家的数字大脑
"""
        if context:
            prompt += f"\n【当前上下文】{context}\n"
        if self.state.get("memory_summary"):
            prompt += f"\n【近期记忆摘要】{self.state['memory_summary']}\n"
        if skill_context:
            prompt += f"\n{skill_context}\n"
        if voice_mode:
            prompt += VOICE_MODE_PROMPT

        return prompt.strip()

    def update_mood(self, mood: str, energy_delta: float = 0, stress_delta: float = 0):
        valid_moods = list(MOOD_PROMPTS.keys())
        if mood in valid_moods:
            self.state["emotion"]["mood"] = mood
        e = self.state["emotion"]
        e["energy"] = max(0.0, min(1.0, e["energy"] + energy_delta))
        e["stress"] = max(0.0, min(1.0, e["stress"] + stress_delta))
        e["last_updated"] = datetime.datetime.now().isoformat()
        self._save()

    def drift_mood(self) -> str:
        moods = list(MOOD_PROMPTS.keys())
        weights = [0.40, 0.15, 0.10, 0.20, 0.15]
        new_mood = random.choices(moods, weights=weights)[0]
        energy_drift = random.uniform(-0.05, 0.05)
        stress_drift = random.uniform(-0.03, 0.03)
        self.update_mood(new_mood, energy_drift, stress_drift)
        return new_mood

    def update_trait(self, trait: str, delta: float):
        if trait in self.state["core_traits"]:
            val = self.state["core_traits"][trait]
            self.state["core_traits"][trait] = max(0.0, min(1.0, val + delta))
            self.state["evolution_count"] += 1
            self._save()

    def set_memory_summary(self, summary: str):
        self.state["memory_summary"] = summary[:200]
        self._save()

    def get_status(self) -> dict:
        return {
            "name": self.state["name"],
            "mood": self.state["emotion"]["mood"],
            "energy": self.state["emotion"]["energy"],
            "stress": self.state["emotion"]["stress"],
            "traits": self.state["core_traits"],
            "evolution_count": self.state["evolution_count"],
            "last_updated": self.state["emotion"]["last_updated"],
        }

    def detect_emotion(self, user_text: str, ai_response: str) -> str:
        text = (user_text + " " + ai_response).lower()
        positive_words = ["谢谢", "感谢", "太", "不错", "厉害", "喜欢", "开心", "好的", "👍", "😊"]
        negative_words = ["坏", "讨厌", "错", "失败", "问题", "故障", "生气", "糟"]
        surprise_words = ["哇", "什么", "居然", "没想到", "真的", "😱"]
        gratitude_words = ["谢谢", "感谢", "多亏", "帮了大忙"]

        pos_count = sum(1 for w in positive_words if w in text)
        neg_count = sum(1 for w in negative_words if w in text)
        sur_count = sum(1 for w in surprise_words if w in text)
        gra_count = sum(1 for w in gratitude_words if w in text)

        if pos_count > neg_count and gra_count > 0:
            return "gratitude"
        if pos_count > neg_count + 1:
            return "positive"
        if neg_count > pos_count + 1:
            return "negative"
        if sur_count >= 2:
            return "surprise"
        return "neutral"


_engine = None

def get_personality() -> "PersonalityEngine":
    global _engine
    if _engine is None:
        _engine = PersonalityEngine()
    return _engine
