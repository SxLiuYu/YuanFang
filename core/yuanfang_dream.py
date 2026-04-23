"""
core/yuanfang_dream.py
元芳梦想系统 · DreamSystem
KAIROS 洞察生成：观察 → 洞察 → 梦想
"""
import os
import json
import logging
import datetime
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DREAM_DIR = Path(__file__).parent.parent / "data" / "dream"
DREAM_DIR.mkdir(parents=True, exist_ok=True)


class DreamMemory:
    """梦想记忆 — 存储洞察和观察"""
    def __init__(self):
        self.insights: list[dict] = []
        self.observations: list[dict] = []
        self.dreams: list[dict] = []
        self._load()

    def _load(self):
        for fname in ["insights.json", "observations.json", "dreams.json"]:
            fpath = DREAM_DIR / fname
            if fpath.exists():
                try:
                    data = json.loads(fpath.read_text("utf-8"))
                    if "insights" in fname:
                        self.insights = data
                    elif "observations" in fname:
                        self.observations = data
                    elif "dreams" in fname:
                        self.dreams = data
                except Exception:
                    pass

    def _save(self, data: list, name: str):
        fpath = DREAM_DIR / f"{name}.json"
        fpath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_insight(self, insight: dict):
        self.insights.append(insight)
        if len(self.insights) > 200:
            self.insights = self.insights[-200:]
        self._save(self.insights, "insights")

    def add_observation(self, obs: dict):
        self.observations.append(obs)
        if len(self.observations) > 500:
            self.observations = self.observations[-500:]
        self._save(self.observations, "observations")

    def add_dream(self, dream: dict):
        self.dreams.append(dream)
        if len(self.dreams) > 100:
            self.dreams = self.dreams[-100:]
        self._save(self.dreams, "dreams")


class DreamSystem:
    """
    元芳梦想系统
    核心能力：
    1. 观察记录 — 从 KAIROS 收集环境/行为数据
    2. 洞察生成 — 分析模式，生成洞察
    3. 梦想演化 — 基于洞察提出"梦想"（目标）
    """

    def __init__(self):
        self.memory = DreamMemory()
        self._llm_fn = None
        logger.info("[DreamSystem] Initialized")

    def set_llm_fn(self, fn):
        self._llm_fn = fn

    def observe(self, observation_type: str, data: dict) -> dict:
        """记录观察"""
        obs = {
            "type": observation_type,
            "data": data,
            "timestamp": datetime.datetime.now().isoformat(),
        }
        self.memory.add_observation(obs)
        return obs

    def generate_insight(self, context: dict) -> Optional[dict]:
        """使用 LLM 分析观察，生成洞察"""
        if not self._llm_fn:
            return None

        recent_obs = self.memory.observations[-20:]
        if len(recent_obs) < 3:
            return None

        prompt = f"""你是元芳的梦想系统（DreamSystem）。分析以下观察记录，生成有价值的洞察。

观察记录：
{json.dumps(recent_obs, ensure_ascii=False, indent=2)[:2000]}

分析要求：
1. 识别重复出现的模式
2. 发现异常或值得注意的变化
3. 提出可能改善建议

输出 JSON（必须返回合法 JSON）：
{{
  "insight": "洞察内容",
  "pattern": "发现的模式",
  "confidence": 0.0-1.0,
  "suggestion": "改进建议"
}}

只返回 JSON。"""

        try:
            response = self._llm_fn([{"role": "user", "content": prompt}])
            text = response if isinstance(response, str) else response.get("content", "")
            # Extract JSON
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            insight = json.loads(text.strip())
            insight["timestamp"] = datetime.datetime.now().isoformat()
            self.memory.add_insight(insight)
            return insight
        except Exception as e:
            logger.warning(f"[DreamSystem] Insight generation failed: {e}")
            return None

    def evolve_dream(self, topic: str = None) -> Optional[dict]:
        """基于洞察，生成或更新梦想（目标）"""
        if not self._llm_fn:
            return None

        insights = self.memory.insights[-10:]
        if not insights:
            return None

        prompt = f"""你是元芳的梦想系统。基于以下洞察，提出一个具体的、可实现的梦想（目标）。

洞察：
{json.dumps(insights, ensure_ascii=False, indent=2)}

梦想格式 JSON：
{{
  "title": "梦想标题",
  "description": "梦想描述",
  "why": "为什么重要",
  "steps": ["步骤1", "步骤2", "步骤3"],
  "obstacles": ["障碍1", "障碍2"],
  "metrics": {{"指标1": 0, "指标2": 0}}
}}

只返回 JSON。"""

        try:
            response = self._llm_fn([{"role": "user", "content": prompt}])
            text = response if isinstance(response, str) else response.get("content", "")
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            dream = json.loads(text.strip())
            dream["created_at"] = datetime.datetime.now().isoformat()
            self.memory.add_dream(dream)
            return dream
        except Exception as e:
            logger.warning(f"[DreamSystem] Dream evolution failed: {e}")
            return None

    def run(self) -> dict:
        """运行一次完整的观察-洞察-梦想循环"""
        return {
            "insights_count": len(self.memory.insights),
            "observations_count": len(self.memory.observations),
            "dreams_count": len(self.memory.dreams),
            "message": "Dream system running",
        }

    def status(self) -> dict:
        return {
            "insights": len(self.memory.insights),
            "observations": len(self.memory.observations),
            "dreams": len(self.memory.dreams),
        }

    def get_consolidated_insights(self, n: int = 20) -> list[dict]:
        insights = self.memory.insights[-n:]
        return sorted(insights, key=lambda x: x.get("timestamp", ""), reverse=True)


_dream: Optional[DreamSystem] = None


def get_dream_system() -> DreamSystem:
    global _dream
    if _dream is None:
        _dream = DreamSystem()
    return _dream
