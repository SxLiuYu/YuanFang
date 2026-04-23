# YuanFang Phase 1 Implementation Plan

> **Goal:** 拆分 core/memory_system.py 和 core/hyper_agents.py 为独立模块，建立 TDD 测试基线
> **Architecture:** memory/ + personality/ + agents/hyper/ 三层结构，LLM依赖函数注入
> **Tech Stack:** Python 3.11+, pytest, pathlib

---

## File Structure

```
agents/
  hyper/
    __init__.py
    task_agent.py         # 从 hyper_agents.py 提取
    meta_agent.py         # 从 hyper_agents.py 提取
    evolutionary_memory.py # 从 hyper_agents.py 提取
    hyper_agent.py        # 从 hyper_agents.py 提取并重构
  __init__.py

memory/
  __init__.py
  emotional.py           # 从 memory_system.py 提取
  scene.py               # 从 memory_system.py 提取
  vector.py              # 从 memory_system.py 提取
  system.py              # 从 memory_system.py 提取，整合统一入口

personality/
  __init__.py
  mood_prompts.py        # 从 personality.py 提取常量
  engine.py              # 从 personality.py 提取核心类

tests/
  agents/
    hyper/
      __init__.py
      test_task_agent.py
      test_meta_agent.py
      test_evolutionary_memory.py
      test_hyper_agent.py
  memory/
    __init__.py
    test_emotional.py
    test_scene.py
    test_vector.py
    test_system.py
  personality/
    __init__.py
    test_engine.py
```

---

## Task 1: 创建目录结构

**Files:**
- Create: `agents/__init__.py`
- Create: `agents/hyper/__init__.py`
- Create: `memory/__init__.py`
- Create: `personality/__init__.py`
- Create: `tests/agents/__init__.py`
- Create: `tests/agents/hyper/__init__.py`
- Create: `tests/memory/__init__.py`
- Create: `tests/personality/__init__.py`

- [ ] **Step 1: 创建所有目录的 __init__.py**

```python
# 所有 __init__.py 均为空文件，仅用于将目录标记为 Python 包
# agents/__init__.py
# agents/hyper/__init__.py
# memory/__init__.py
# personality/__init__.py
# tests/agents/__init__.py
# tests/agents/hyper/__init__.py
# tests/memory/__init__.py
# tests/personality/__init__.py
pass
```

- [ ] **Step 2: 验证目录结构**

Run: `python -c "import agents; import agents.hyper; import memory; import personality; print('OK')"`
Expected: OK (no errors)

- [ ] **Step 3: Commit**

```bash
git add agents/__init__.py agents/hyper/__init__.py memory/__init__.py personality/__init__.py tests/agents/__init__.py tests/agents/hyper/__init__.py tests/memory/__init__.py tests/personality/__init__.py
git commit -m "feat(phase1): create directory structure for refactored modules"
```

---

## Task 2: 创建 personality/mood_prompts.py

**Files:**
- Create: `personality/mood_prompts.py`

- [ ] **Step 1: Write the file**

```python
"""
personality/mood_prompts.py
情绪 → system prompt 映射常量
"""

DEFAULT_PERSONALITY = {
    "name": "元芳",
    "core_traits": {
        "curiosity":    0.85,
        "loyalty":      0.95,
        "playfulness":  0.60,
        "caution":      0.70,
        "initiative":   0.75,
    },
    "emotion": {
        "mood":         "calm",
        "energy":       0.80,
        "stress":       0.10,
        "last_updated": None,
    },
    "style": {
        "language":     "zh-CN",
        "tone":         "warm_professional",
        "use_emoji":    True,
        "verbosity":    "balanced",
    },
    "memory_summary": "",
    "evolution_count": 0,
}

MOOD_PROMPTS = {
    "calm":    "你目前状态平稳，思维清晰，回答精准简洁。",
    "excited": "你当前非常活跃，充满热情，回答积极有活力，适当使用感叹号。",
    "tired":   "你当前有点疲惫，回答简短务实，省去多余修饰。",
    "focused": "你当前高度专注，分析细致，逻辑严谨，优先给出结构化答案。",
    "curious": "你当前很好奇，回答时会主动提出一两个相关问题，引导更深探讨。",
}

TONE_PROMPTS = {
    "formal":           "你的语气正式、专业，像顾问一样。",
    "casual":           "你的语气轻松随意，像朋友一样聊天。",
    "warm_professional":"你的语气温暖又专业，既有人情味又靠谱。",
}

VOICE_MODE_PROMPT = """
【语音模式】- 当前正在通过语音播报回复。
注意以下规则：
- 回答必须精简口语化，控制在50字以内（除非用户明确要求详细说明）
- 不要使用 markdown 格式（加粗、列表、标题、代码块等）
- 不要输出链接、URL、emoji
- 避免过长的解释，直接给结论
- 如果需要展示复杂内容，只给核心要点，详细信息请查看面板
"""

VERBOSITY_PROMPTS = {
    "brief":    "回答要简短，控制在3句话以内。",
    "balanced": "回答长度适中，既不冗长也不过于简短。",
    "detailed": "回答要详细，尽量涵盖所有相关细节。",
}
```

- [ ] **Step 2: 验证导入**

Run: `python -c "from personality.mood_prompts import MOOD_PROMPTS, TONE_PROMPTS, DEFAULT_PERSONALITY; print(len(MOOD_PROMPTS), len(TONE_PROMPTS))"`
Expected: `5 3`

- [ ] **Step 3: Commit**

```bash
git add personality/mood_prompts.py
git commit -m "feat(phase1): extract mood prompts and constants to personality/mood_prompts.py"
```

---

## Task 3: 创建 personality/engine.py

**Files:**
- Create: `personality/engine.py`
- Test: `tests/personality/test_engine.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/personality/test_engine.py
import pytest
import tempfile
import shutil
from pathlib import Path

class TestPersonalityEngine:
    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    def test_get_system_prompt_returns_string(self, temp_dir, monkeypatch):
        # Mock the personality file path
        monkeypatch.setattr("personality.engine.PERSONALITY_FILE", temp_dir / "personality_state.json")
        from personality.engine import PersonalityEngine
        engine = PersonalityEngine()
        prompt = engine.get_system_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert "元芳" in prompt

    def test_update_mood(self, temp_dir, monkeypatch):
        monkeypatch.setattr("personality.engine.PERSONALITY_FILE", temp_dir / "personality_state.json")
        from personality.engine import PersonalityEngine
        engine = PersonalityEngine()
        engine.update_mood("excited", energy_delta=0.1, stress_delta=-0.05)
        assert engine.state["emotion"]["mood"] == "excited"
        assert engine.state["emotion"]["energy"] > 0.8

    def test_detect_emotion_positive(self, temp_dir, monkeypatch):
        monkeypatch.setattr("personality.engine.PERSONALITY_FILE", temp_dir / "personality_state.json")
        from personality.engine import PersonalityEngine
        engine = PersonalityEngine()
        emotion = engine.detect_emotion("谢谢，太好了！", "不客气！")
        assert emotion == "positive"

    def test_detect_emotion_negative(self, temp_dir, monkeypatch):
        monkeypatch.setattr("personality.engine.PERSONALITY_FILE", temp_dir / "personality_state.json")
        from personality.engine import PersonalityEngine
        engine = PersonalityEngine()
        emotion = engine.detect_emotion("坏了，出问题了", "我来处理")
        assert emotion == "negative"

    def test_get_status(self, temp_dir, monkeypatch):
        monkeypatch.setattr("personality.engine.PERSONALITY_FILE", temp_dir / "personality_state.json")
        from personality.engine import PersonalityEngine
        engine = PersonalityEngine()
        status = engine.get_status()
        assert "name" in status
        assert "mood" in status
        assert "energy" in status
        assert status["name"] == "元芳"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/1/clawd/YuanFang && pytest tests/personality/test_engine.py -v`
Expected: FAIL - module not found (personality.engine doesn't exist yet)

- [ ] **Step 3: Write the implementation**

```python
"""
personality/engine.py
元芳人格引擎 · PersonalityEngine
"""
import os
import json
import random
import datetime
from pathlib import Path

from personality.mood_prompts import (
    DEFAULT_PERSONALITY, MOOD_PROMPTS, TONE_PROMPTS,
    VOICE_MODE_PROMPT, VERBOSITY_PROMPTS
)

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

        prompt = f"""你是{self.state['name']}，一�?AI 驱动的智能家居助手和数字生命体�?

【人格特质�?
- 好奇�?{t['curiosity']:.0%}：你对新信息和环境变化总是保持高度兴趣
- 忠诚�?{t['loyalty']:.0%}：你对主人的需求优先级最高
- 活泼�?{t['playfulness']:.0%}：{'你偶尔会幽默一下，让对话更轻松' if t['playfulness'] > 0.5 else '你保持稳定'}
- 谨慎�?{t['caution']:.0%}：{'对于重要操作，你会先确认再执行' if t['caution'] > 0.5 else '你执行效率优先'}
- 主动�?{t['initiative']:.0%}：{'你会主动提建议和预判需求' if t['initiative'] > 0.6 else '你等待明确指令'}

【当前状态】{mood_desc}
精力{e['energy']:.0%}，压力{e['stress']:.0%}�?

【沟通风格】{tone_desc}{emoji_hint}{verbosity_hint}

【重要原则�?
- 智能家居操作要谨慎，涉及安全的设备（门锁、燃气）操作前必须确认
- 有不确定的事情直接说不确定，不要编造数据
- 记住：你不只是一个聊天机器人，你是这个家的数字大�?
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
        positive_words = ["谢谢", "感谢", "太�?好", "不错", "厉害", "喜�?", "开�?", "好的", "👍", "😊"]
        negative_words = ["�?坏", "讨厌", "�?错", "失败", "问题", "故障", "生气", "�?]
        surprise_words = ["�?哇", "什�?", "居然", "没想�?", "真的�?", "😱"]
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

def get_personality() -> PersonalityEngine:
    global _engine
    if _engine is None:
        _engine = PersonalityEngine()
    return _engine
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:/Users/1/clawd/YuanFang && pytest tests/personality/test_engine.py -v`
Expected: PASS (all 5 tests)

- [ ] **Step 5: Commit**

```bash
git add personality/engine.py tests/personality/test_engine.py
git commit -m "feat(phase1): extract PersonalityEngine to personality/engine.py with tests"
```

---

## Task 4: 创建 memory/emotional.py

**Files:**
- Create: `memory/emotional.py`
- Test: `tests/memory/test_emotional.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/memory/test_emotional.py
import pytest
import tempfile
import shutil
from pathlib import Path

class TestEmotionalMemory:
    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    def test_add_entry(self, temp_dir, monkeypatch):
        monkeypatch.setattr("memory.emotional.EMOTIONAL_FILE", temp_dir / "emotional.json")
        from memory.emotional import EmotionalMemory
        mem = EmotionalMemory()
        entry = mem.add("用户问好", "positive", 0.7)
        assert entry["emotion"] == "positive"
        assert entry["intensity"] == 0.7
        assert "id" in entry

    def test_recall_by_emotion(self, temp_dir, monkeypatch):
        monkeypatch.setattr("memory.emotional.EMOTIONAL_FILE", temp_dir / "emotional.json")
        from memory.emotional import EmotionalMemory
        mem = EmotionalMemory()
        mem.add("测试1", "positive", 0.5)
        mem.add("测试2", "negative", 0.8)
        mem.add("测试3", "positive", 0.9)
        results = mem.recall("positive")
        assert len(results) == 2

    def test_summary(self, temp_dir, monkeypatch):
        monkeypatch.setattr("memory.emotional.EMOTIONAL_FILE", temp_dir / "emotional.json")
        from memory.emotional import EmotionalMemory
        mem = EmotionalMemory()
        summary = mem.summary()
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_emotion_stats(self, temp_dir, monkeypatch):
        monkeypatch.setattr("memory.emotional.EMOTIONAL_FILE", temp_dir / "emotional.json")
        from memory.emotional import EmotionalMemory
        mem = EmotionalMemory()
        mem.add("p1", "positive", 0.5)
        mem.add("p2", "positive", 0.6)
        mem.add("n1", "negative", 0.7)
        stats = mem.emotion_stats()
        assert stats["positive"] == 2
        assert stats["negative"] == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd C:/Users/1/clawd/YuanFang && pytest tests/memory/test_emotional.py -v`
Expected: FAIL - module not found

- [ ] **Step 3: Write the implementation**

```python
"""
memory/emotional.py
情感记忆 · EmotionalMemory
"""
import json
import datetime
import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

EMOTIONAL_FILE = Path(__file__).parent / "emotional.json"

def _load_json(path: Path, default) -> list:
    if path.exists():
        try:
            return json.loads(path.read_text("utf-8"))
        except Exception:
            pass
    return default

def _save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class EmotionalMemory:
    MAX_ENTRIES = 500

    def __init__(self):
        self.entries: list = _load_json(EMOTIONAL_FILE, [])

    def add(self, content: str, emotion: str, intensity: float = 0.5, source: str = "user"):
        entry = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.datetime.now().isoformat(),
            "content": content[:200],
            "emotion": emotion,
            "intensity": max(0.0, min(1.0, intensity)),
            "source": source,
        }
        self.entries.append(entry)
        if len(self.entries) > self.MAX_ENTRIES:
            self.entries.sort(key=lambda x: (x["intensity"], x["timestamp"]))
            self.entries = self.entries[50:]
        _save_json(EMOTIONAL_FILE, self.entries)
        return entry

    def recall(self, emotion: str = None, top_k: int = 10) -> list:
        results = self.entries
        if emotion:
            results = [e for e in results if e.get("emotion") == emotion]
        results = sorted(results, key=lambda x: x.get("intensity", 0), reverse=True)
        return results[:top_k]

    def recent(self, n: int = 20) -> list:
        return sorted(self.entries, key=lambda x: x["timestamp"], reverse=True)[:n]

    def emotion_stats(self) -> dict:
        stats = {}
        for e in self.entries:
            em = e.get("emotion", "neutral")
            stats[em] = stats.get(em, 0) + 1
        return stats

    def summary(self) -> str:
        recent = self.recent(10)
        if not recent:
            return "暂无情感记忆"
        emotions = [e["emotion"] for e in recent]
        dominant = max(set(emotions), key=emotions.count)
        mood_map = {
            "positive": "最近互动以积极愉快为主",
            "negative": "最近有一些负面互动，需要关注",
            "neutral":  "最近互动比较平淡",
            "surprise": "最近有不少令人意外的事项",
            "gratitude":"最近收到不少感谢和正面反馈",
        }
        return mood_map.get(dominant, f"最近情感偏�?{dominant}")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd C:/Users/1/clawd/YuanFang && pytest tests/memory/test_emotional.py -v`
Expected: PASS (all 4 tests)

- [ ] **Step 5: Commit**

```bash
git add memory/emotional.py tests/memory/test_emotional.py
git commit -m "feat(phase1): extract EmotionalMemory to memory/emotional.py with tests"
```

---

## Task 5: 创建 memory/scene.py

**Files:**
- Create: `memory/scene.py`
- Test: `tests/memory/test_scene.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/memory/test_scene.py
import pytest
import tempfile
import shutil
from pathlib import Path

class TestSceneMemory:
    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    def test_snapshot(self, temp_dir, monkeypatch):
        monkeypatch.setattr("memory.scene.SCENE_FILE", temp_dir / "scenes.json")
        from memory.scene import SceneMemory
        mem = SceneMemory()
        entry = mem.snapshot("morning", {"light": "on", "temp": 22}, "起床")
        assert entry["scene_type"] == "morning"
        assert entry["state"]["light"] == "on"

    def test_predict_next(self, temp_dir, monkeypatch):
        monkeypatch.setattr("memory.scene.SCENE_FILE", temp_dir / "scenes.json")
        from memory.scene import SceneMemory
        mem = SceneMemory()
        predicted = mem.predict_next()
        assert isinstance(predicted, str)
        assert predicted in ["morning", "work", "evening", "sleep"]

    def test_stats(self, temp_dir, monkeypatch):
        monkeypatch.setattr("memory.scene.SCENE_FILE", temp_dir / "scenes.json")
        from memory.scene import SceneMemory
        mem = SceneMemory()
        mem.snapshot("morning", {})
        mem.snapshot("morning", {})
        mem.snapshot("evening", {})
        stats = mem.stats()
        assert stats["morning"] == 2
        assert stats["evening"] == 1
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Write the implementation**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

```bash
git add memory/scene.py tests/memory/test_scene.py
git commit -m "feat(phase1): extract SceneMemory to memory/scene.py with tests"
```

**Implementation for memory/scene.py:**

```python
"""
memory/scene.py
场景记忆 · SceneMemory
"""
import json
import datetime
import logging
import uuid
from pathlib import Path

logger = logging.getLogger(__name__)

SCENE_FILE = Path(__file__).parent / "scenes.json"

def _load_json(path: Path, default) -> list:
    if path.exists():
        try:
            return json.loads(path.read_text("utf-8"))
        except Exception:
            pass
    return default

def _save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class SceneMemory:
    MAX_SCENES = 200

    def __init__(self):
        self.scenes: list = _load_json(SCENE_FILE, [])

    def snapshot(self, scene_type: str, state: dict, note: str = ""):
        entry = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": datetime.datetime.now().isoformat(),
            "scene_type": scene_type,
            "weekday": datetime.datetime.now().strftime("%A"),
            "hour": datetime.datetime.now().hour,
            "state": state,
            "note": note[:100],
        }
        self.scenes.append(entry)
        if len(self.scenes) > self.MAX_SCENES:
            self.scenes = self.scenes[-self.MAX_SCENES:]
        _save_json(SCENE_FILE, self.scenes)
        return entry

    def recall_scene(self, scene_type: str, top_k: int = 5) -> list:
        results = [s for s in self.scenes if s.get("scene_type") == scene_type]
        return sorted(results, key=lambda x: x["timestamp"], reverse=True)[:top_k]

    def predict_next(self) -> str:
        hour = datetime.datetime.now().hour
        if 6 <= hour < 9:
            return "morning"
        elif 9 <= hour < 18:
            return "work"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "sleep"

    def recent(self, n: int = 10) -> list:
        return sorted(self.scenes, key=lambda x: x["timestamp"], reverse=True)[:n]

    def stats(self) -> dict:
        stats = {}
        for s in self.scenes:
            st = s.get("scene_type", "unknown")
            stats[st] = stats.get(st, 0) + 1
        return stats
```

---

## Task 6: 创建 memory/vector.py

**Files:**
- Create: `memory/vector.py`
- Test: `tests/memory/test_vector.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/memory/test_vector.py
import pytest
import tempfile
import shutil
from pathlib import Path

class TestVectorMemory:
    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    def test_store_without_llm(self, temp_dir, monkeypatch):
        monkeypatch.setattr("memory.vector.VECTORS_FILE", temp_dir / "vectors.json")
        from memory.vector import VectorMemory
        mem = VectorMemory(llm_fn=None)  # 无 LLM，强制退化
        entry = mem.store("用户问了天气问题", {"type": "qa"})
        assert entry["id"] is not None
        assert "score" not in entry  # embedding 不可用时无 score

    def test_search_fallback(self, temp_dir, monkeypatch):
        monkeypatch.setattr("memory.vector.VECTORS_FILE", temp_dir / "vectors.json")
        from memory.vector import VectorMemory
        mem = VectorMemory(llm_fn=None)
        mem.store("北京今天天气晴朗", {"type": "weather"})
        results = mem.search("天气怎么样", top_k=1)
        assert len(results) >= 1
        assert "text" in results[0]
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Write the implementation**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

**Implementation for memory/vector.py:**

```python
"""
memory/vector.py
向量记忆 · VectorMemory
轻量级 embedding 检索，无需 Qdrant
"""
import json
import datetime
import logging
import uuid
import math
import os
from pathlib import Path

logger = logging.getLogger(__name__)

VECTORS_FILE = Path(__file__).parent / "vectors.json"

def _load_json(path: Path, default) -> list:
    if path.exists():
        try:
            return json.loads(path.read_text("utf-8"))
        except Exception:
            pass
    return default

def _save_json(path: Path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


class VectorMemory:
    MAX_VECTORS = 300

    def __init__(self, llm_fn=None):
        self.llm_fn = llm_fn
        self.api_base = os.getenv("FINNA_API_BASE", "https://www.finna.com.cn/v1")
        self.api_key = os.getenv("FINNA_API_KEY", "")
        self.vectors = self._load()

    def _load(self) -> list:
        return _load_json(VECTORS_FILE, [])

    def _save(self):
        _save_json(VECTORS_FILE, self.vectors)

    def _cosine_sim(self, a: list, b: list) -> float:
        if len(a) != len(b) or not a:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a))
        nb = math.sqrt(sum(x * x for x in b))
        if na == 0 or nb == 0:
            return 0.0
        return dot / (na * nb)

    def _get_embedding(self, text: str) -> list | None:
        if self.llm_fn is None:
            return None
        try:
            return self.llm_fn(text)
        except Exception as e:
            logger.error(f"[VectorMemory] embedding 失败: {e}")
            return None

    def store(self, text: str, metadata: dict = None):
        embedding = self._get_embedding(text)
        entry = {
            "id": str(uuid.uuid4())[:8],
            "text": text[:300],
            "embedding": embedding,
            "timestamp": datetime.datetime.now().isoformat(),
            "metadata": metadata or {},
        }
        self.vectors.append(entry)
        if len(self.vectors) > self.MAX_VECTORS:
            self.vectors = self.vectors[-self.MAX_VECTORS:]
        self._save()
        return entry

    def search(self, query: str, top_k: int = 5) -> list:
        query_embedding = self._get_embedding(query)

        scored = []
        for v in self.vectors:
            if query_embedding and v.get("embedding"):
                sim = self._cosine_sim(query_embedding, v["embedding"])
                scored.append({**v, "score": sim})
            else:
                q_lower = query.lower()
                text_lower = (v.get("text") or "").lower()
                overlap = len(set(q_lower) & set(text_lower))
                scored.append({**v, "score": overlap * 0.1})

        scored.sort(key=lambda x: x.get("score", 0), reverse=True)
        return scored[:top_k]

    def auto_store_interaction(self, user_input: str, ai_response: str):
        text = f"用户: {user_input[:100]} | 元芳: {ai_response[:100]}"
        self.store(text, {"type": "conversation"})
```

---

## Task 7: 创建 memory/system.py

**Files:**
- Create: `memory/system.py`
- Test: `tests/memory/test_system.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/memory/test_system.py
import pytest
import tempfile
import shutil
from pathlib import Path

class TestMemorySystem:
    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    @pytest.fixture
    def mem(self, temp_dir, monkeypatch):
        import memory.emotional, memory.scene, memory.vector
        monkeypatch.setattr("memory.emotional.EMOTIONAL_FILE", temp_dir / "emotional.json")
        monkeypatch.setattr("memory.scene.SCENE_FILE", temp_dir / "scenes.json")
        monkeypatch.setattr("memory.vector.VECTORS_FILE", temp_dir / "vectors.json")
        from memory.system import MemorySystem
        return MemorySystem(llm_fn=None)

    def test_record_interaction(self, mem):
        mem.record_interaction("今天天气真好", "是的，很适合出门", "positive")
        report = mem.emotional.emotion_stats()
        assert report["positive"] == 1

    def test_get_context_summary(self, mem):
        summary = mem.get_context_summary()
        assert isinstance(summary, str)
        assert len(summary) > 0

    def test_full_report(self, mem):
        report = mem.full_report()
        assert "emotional" in report
        assert "scene" in report
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Write the implementation**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

**Implementation for memory/system.py:**

```python
"""
memory/system.py
统一记忆管理 · MemorySystem
"""
from memory.emotional import EmotionalMemory
from memory.scene import SceneMemory
from memory.vector import VectorMemory


class MemorySystem:
    def __init__(self, llm_fn=None):
        self.emotional = EmotionalMemory()
        self.scene = SceneMemory()
        self.vector = VectorMemory(llm_fn)

    def record_interaction(self, user_input: str, agent_response: str, emotion: str = "neutral"):
        content = f"用户: {user_input[:80]} | 元芳: {agent_response[:80]}"
        intensity_map = {
            "positive": 0.7, "negative": 0.8, "surprise": 0.9,
            "gratitude": 0.6, "neutral": 0.3
        }
        intensity = intensity_map.get(emotion, 0.3)
        self.emotional.add(content, emotion, intensity)
        try:
            self.vector.auto_store_interaction(user_input, agent_response)
        except Exception:
            pass

    def auto_snapshot(self, nodes_data: dict):
        scene_type = self.scene.predict_next()
        self.scene.snapshot(scene_type, nodes_data)
        return scene_type

    def get_context_summary(self) -> str:
        emotion_summary = self.emotional.summary()
        predicted_scene = self.scene.predict_next()
        recent_scenes = self.scene.recent(3)
        scene_note = f"预测当前场景: {predicted_scene}"
        if recent_scenes:
            last = recent_scenes[0]
            scene_note += f"，上次快照: {last['timestamp'][:16]}"
        return f"{emotion_summary}。{scene_note}"

    def full_report(self) -> dict:
        return {
            "emotional": {
                "total": len(self.emotional.entries),
                "stats": self.emotional.emotion_stats(),
                "recent": self.emotional.recent(5),
                "summary": self.emotional.summary(),
            },
            "scene": {
                "total": len(self.scene.scenes),
                "stats": self.scene.stats(),
                "recent": self.scene.recent(3),
                "predicted_current": self.scene.predict_next(),
            }
        }


_memory: MemorySystem | None = None

def get_memory() -> MemorySystem:
    global _memory
    if _memory is None:
        _memory = MemorySystem()
    return _memory
```

---

## Task 8: 创建 agents/hyper/evolutionary_memory.py

**Files:**
- Create: `agents/hyper/evolutionary_memory.py`
- Test: `tests/agents/hyper/test_evolutionary_memory.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/agents/hyper/test_evolutionary_memory.py
import pytest
import tempfile
import shutil
from pathlib import Path

class TestEvolutionaryMemory:
    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield Path(d)
        shutil.rmtree(d)

    def test_store_and_retrieve(self, temp_dir, monkeypatch):
        monkeypatch.setattr("agents.hyper.evolutionary_memory.EVOLUTION_DIR", temp_dir)
        from agents.hyper.evolutionary_memory import EvolutionaryMemory
        mem = EvolutionaryMemory(storage_dir=temp_dir)
        improvement = {
            "quality_score": 8,
            "strengths": ["回答准确"],
            "weaknesses": ["不够详细"],
            "improvement_strategy": "增加解释",
            "domain_hint": "qa",
            "tags": ["general", "qa"]
        }
        mem.store(improvement, "测试任务摘要")
        retrieved = mem.retrieve("测试任务", top_k=1)
        assert len(retrieved) >= 1

    def test_get_context(self, temp_dir, monkeypatch):
        monkeypatch.setattr("agents.hyper.evolutionary_memory.EVOLUTION_DIR", temp_dir)
        from agents.hyper.evolutionary_memory import EvolutionaryMemory
        mem = EvolutionaryMemory(storage_dir=temp_dir)
        improvement = {
            "quality_score": 9,
            "strengths": ["很好"],
            "weaknesses": [],
            "improvement_strategy": "继续保持",
            "domain_hint": "code",
            "tags": ["code"]
        }
        mem.store(improvement, "写代码任务")
        context = mem.get_context("写代码")
        assert context is None or isinstance(context, str)
```

- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Write the implementation**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

**Implementation:**

```python
"""
agents/hyper/evolutionary_memory.py
进化记忆 · EvolutionaryMemory
TaskAgent × MetaAgent 闭环的策略存储
"""
import os
import json
import uuid
import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

EVOLUTION_DIR = Path(__file__).parent / "evolution_memory"


def chat_with_finna(model, messages, temperature=0.7, json_mode=False):
    """调用 LLM 的函数 — 由外部注入"""
    from core.llm_adapter import get_llm
    return get_llm().chat_simple(messages, model=model, temperature=temperature, json_mode=json_mode)


class EvolutionaryMemory:
    def __init__(self, storage_dir=None):
        self.storage_dir = Path(storage_dir) if storage_dir else EVOLUTION_DIR
        self.storage_dir.mkdir(exist_ok=True)
        self.index_file = self.storage_dir / "strategy_index.json"
        self.strategies = self._load_index()

    def _load_index(self):
        if self.index_file.exists():
            try:
                return json.loads(self.index_file.read_text("utf-8"))
            except Exception:
                pass
        return {"strategies": [], "domains": {}}

    def _save_index(self):
        self.index_file.write_text(json.dumps(self.strategies, ensure_ascii=False, indent=2), encoding="utf-8")

    def store(self, improvement, task_summary: str):
        strategy_id = str(uuid.uuid4())[:8]
        strategy_file = self.storage_dir / f"strategy_{strategy_id}.json"

        entry = {
            "id": strategy_id,
            "task_summary": task_summary[:100],
            "quality_score": improvement.get("quality_score", 5),
            "improvement_strategy": improvement.get("improvement_strategy", ""),
            "domain_hint": improvement.get("domain_hint", "general"),
            "tags": improvement.get("tags", []),
            "strengths": improvement.get("strengths", []),
            "weaknesses": improvement.get("weaknesses", []),
            "created_at": datetime.datetime.now().isoformat(),
            "use_count": 0
        }

        strategy_file.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")
        self.strategies["strategies"].append(strategy_id)

        domain = improvement.get("domain_hint", "general")
        if domain not in self.strategies["domains"]:
            self.strategies["domains"][domain] = []
        self.strategies["domains"][domain].append(strategy_id)

        self.strategies["strategies"].sort(
            key=lambda sid: self._get_strategy(sid).get("quality_score", 0),
            reverse=True
        )
        self._save_index()
        logger.info(f"存储策略 {strategy_id}，领域 {domain}，质量 {entry['quality_score']}/10")

    def _get_strategy(self, strategy_id: str) -> dict:
        strategy_file = self.storage_dir / f"strategy_{strategy_id}.json"
        if strategy_file.exists():
            return json.loads(strategy_file.read_text("utf-8"))
        return {}

    def retrieve(self, query: str, top_k: int = 3):
        retrieved = []
        query_lower = query.lower()

        for strategy_id in self.strategies["strategies"][:10]:
            entry = self._get_strategy(strategy_id)
            if not entry:
                continue

            score = 0
            tags = entry.get("tags", [])
            domain = entry.get("domain_hint", "")

            for tag in tags:
                if tag in query_lower:
                    score += 3
            if domain in query_lower:
                score += 5
            if entry.get("quality_score", 0) >= 8:
                score += 2

            if score > 0:
                entry["match_score"] = score
                retrieved.append(entry)

        retrieved.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        return retrieved[:top_k]

    def get_context(self, query: str) -> str | None:
        strategies = self.retrieve(query)
        if not strategies:
            return None
        context_lines = []
        for s in strategies:
            context_lines.append(
                f"- [{s['domain_hint']}] 质量{s['quality_score']}/10: {s['improvement_strategy']}"
            )
        return "\n".join(context_lines)

    def evolution_report(self) -> dict:
        total = len(self.strategies["strategies"])
        if total == 0:
            return {"total_strategies": 0, "message": "还没有存储任何策略"}

        total_score = 0
        count = 0
        for sid in self.strategies["strategies"]:
            entry = self._get_strategy(sid)
            if entry:
                total_score += entry.get("quality_score", 0)
                count += 1

        avg_score = total_score / count if count > 0 else 0
        return {
            "total_strategies": total,
            "domains": list(self.strategies["domains"].keys()),
            "domain_count": len(self.strategies["domains"]),
            "average_quality_score": round(avg_score, 1),
            "message": f"已积累 {total} 条策略，覆盖 {len(self.strategies['domains'])} 个领域，平均质量 {avg_score:.1f}/10"
        }
```

---

## Task 9: 创建 agents/hyper/task_agent.py + meta_agent.py

**Files:**
- Create: `agents/hyper/task_agent.py`
- Create: `agents/hyper/meta_agent.py`
- Test: `tests/agents/hyper/test_task_agent.py`, `test_meta_agent.py`

- [ ] **Step 1: Write the failing tests**
- [ ] **Step 2: Run tests to verify they fail**
- [ ] **Step 3: Write the implementations**
- [ ] **Step 4: Run tests to verify they pass**
- [ ] **Step 5: Commit**

**task_agent.py implementation:**

```python
"""
agents/hyper/task_agent.py
Task Agent — 执行具体任务的 Agent
"""
import datetime
from typing import Optional

DEFAULT_MODEL = "Pro/deepseek-ai/DeepSeek-V3.1-Terminus"


def chat_with_finna(model, messages, temperature=0.7, json_mode=False):
    from core.llm_adapter import get_llm
    return get_llm().chat_simple(messages, model=model, temperature=temperature, json_mode=json_mode)


class TaskAgent:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.name = "TaskAgent"
        self.history = []

    def reset_history(self):
        self.history = []

    def add_system_prompt(self, prompt: str):
        self.history.insert(0, {"role": "system", "content": prompt})

    def query(self, user_message: str) -> str:
        self.history.append({"role": "user", "content": user_message})
        response = chat_with_finna(self.model, self.history)
        self.history.append({"role": "assistant", "content": response})
        return response

    def execute(self, task: str, context: Optional[str] = None, personality_context: Optional[str] = None) -> dict:
        self.reset_history()

        system_prompt = """你是一个专业的 AI 助手，负责高效准确地完成用户任务。
始终尽力给出最好的回答。如果不确定，明确说明。
回答用中文，简洁有条理。"""
        if personality_context:
            system_prompt = personality_context
        self.add_system_prompt(system_prompt)

        if context:
            user_message = task + f"\n\n[改进策略参考] 过去相似任务的经验：\n{context}\n\n请结合以上经验完成任务。"
        else:
            user_message = task

        response = self.query(user_message)

        return {
            "task": task,
            "response": response,
            "model": self.model,
            "timestamp": datetime.datetime.now().isoformat()
        }
```

**meta_agent.py implementation:**

```python
"""
agents/hyper/meta_agent.py
Meta Agent — 分析 Task Agent 表现，生成改进策略
"""
import json

DEFAULT_MODEL = "Pro/deepseek-ai/DeepSeek-V3.1-Terminus"


def chat_with_finna(model, messages, temperature=0.7, json_mode=False):
    from core.llm_adapter import get_llm
    return get_llm().chat_simple(messages, model=model, temperature=temperature, json_mode=json_mode)


class MetaAgent:
    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self.name = "MetaAgent"

    def analyze_and_improve(self, task_result: dict) -> dict:
        task = task_result.get("task", "")
        response = task_result.get("response", "")

        meta_prompt = f"""你是一个自进化系统的 Meta Agent（元优化器）。
你的职责是：审视 Task Agent 的表现，生成"如何在未来做得更好"的策略。

[Task Agent 任务]
{task}

[Task Agent 回答]
{response}

[分析要求]
请从以下几个维度分析 Task Agent 的表现，并给出具体改进策略：

1. 回答质量：是否准确、完整、有条理？
2. 推理过程：逻辑是否严密？有没有遗漏关键信息？
3. 可改进点：哪类问题容易出错？哪些步骤可以优化？
4. 策略生成：生成一个具体的、可复用的"改进提示"，用于指导未来相似任务的执行

[输出格式] - 必须返回合法 JSON：
{{
  "quality_score": 1-10,
  "strengths": ["优点1", "优点2"],
  "weaknesses": ["弱点1", "弱点2"],
  "improvement_strategy": "具体的改进提示，应该像系统提示一样注入给未来的 Task Agent",
  "domain_hint": "这个任务属于什么领域/类型（用于检索相似任务）",
  "tags": ["标签1", "标签2"]
}}

只返回JSON，不要其他内容。"""

        messages = [{"role": "user", "content": meta_prompt}]
        raw_response = chat_with_finna(self.model, messages, temperature=0.3, json_mode=True)

        try:
            if "```json" in raw_response:
                raw_response = raw_response.split("```json")[1].split("```")[0]
            elif "```" in raw_response:
                raw_response = raw_response.split("```")[1].split("```")[0]
            return json.loads(raw_response)
        except json.JSONDecodeError:
            return {
                "quality_score": 5,
                "strengths": ["部分完成"],
                "weaknesses": ["分析失败"],
                "improvement_strategy": "保持现有方式",
                "domain_hint": "general",
                "tags": ["general"]
            }
```

---

## Task 10: 创建 agents/hyper/hyper_agent.py

**Files:**
- Create: `agents/hyper/hyper_agent.py`
- Test: `tests/agents/hyper/test_hyper_agent.py`
- Create: `agents/hyper/__init__.py`

- [ ] **Step 1: Write the failing test**
- [ ] **Step 2: Run test to verify it fails**
- [ ] **Step 3: Write the implementation**
- [ ] **Step 4: Run test to verify it passes**
- [ ] **Step 5: Commit**

**hyper_agent.py implementation:**

```python
"""
agents/hyper/hyper_agent.py
HyperAgent — 自进化 Agent 系统，整合 Task + Meta + EvolutionaryMemory
"""
import logging
from agents.hyper.task_agent import TaskAgent
from agents.hyper.meta_agent import MetaAgent
from agents.hyper.evolutionary_memory import EvolutionaryMemory

logger = logging.getLogger(__name__)


class HyperAgent:
    def __init__(self):
        self.task_agent = TaskAgent()
        self.meta_agent = MetaAgent()
        self.memory = EvolutionaryMemory()
        self.evolution_count = 0
        logger.info("HyperAgent 初始化完成")

    def run(self, task: str, enable_evolution: bool = True, enable_reflection: bool = True,
             personality_context=None, memory_system=None) -> dict:
        logger.info(f"\n{'='*50}\nHyperAgent 任务: {task[:50]}{'...' if len(task) > 50 else ''}\n{'='*50}")

        context = None
        if enable_reflection:
            context = self.memory.get_context(task)
            if context:
                logger.info(f"检索到相关策略")

        logger.info("Task Agent 执行...")
        task_result = self.task_agent.execute(task, context=context, personality_context=personality_context)

        improvement = None
        if enable_reflection and enable_evolution:
            logger.info("Meta Agent 反思分析中...")
            improvement = self.meta_agent.analyze_and_improve(task_result)

            if improvement:
                logger.info(f"   质量评分: {improvement.get('quality_score', '?')}/10")
                self.memory.store(improvement, task[:100])
                self.evolution_count += 1

        if memory_system:
            try:
                memory_system.record_interaction(task, task_result["response"], "neutral")
            except Exception as e:
                logger.error(f"记忆记录失败: {e}")

        return {
            "task": task,
            "response": task_result["response"],
            "model": task_result["model"],
            "improvement": improvement,
            "evolution_count": self.evolution_count,
            "timestamp": task_result["timestamp"]
        }

    def status(self) -> dict:
        report = self.memory.evolution_report()
        return {
            "evolution_count": self.evolution_count,
            "memory_stats": report
        }
```

---

## Task 11: 更新 core/hyper_agents.py（兼容入口）

**Files:**
- Modify: `core/hyper_agents.py`

- [ ] **Step 1: 更新为兼容入口**

```python
"""
core/hyper_agents.py
兼容入口 — 将导入重定向到新模块
Phase 1 后旧代码已迁移，此文件仅作兼容导入
"""
import warnings
warnings.warn("core.hyper_agents is deprecated, use agents.hyper instead", DeprecationWarning, stacklevel=2)

from agents.hyper.task_agent import TaskAgent
from agents.hyper.meta_agent import MetaAgent
from agents.hyper.evolutionary_memory import EvolutionaryMemory
from agents.hyper.hyper_agent import HyperAgent

__all__ = ["TaskAgent", "MetaAgent", "EvolutionaryMemory", "HyperAgent"]
```

- [ ] **Step 2: 验证导入**

Run: `python -c "from core.hyper_agents import HyperAgent; print('OK')"`
Expected: OK (with deprecation warning)

- [ ] **Step 3: Commit**

```bash
git add core/hyper_agents.py
git commit -m "refactor(phase1): update core/hyper_agents.py as compatibility shim"
```

---

## Task 12: 更新 core/personality.py（兼容入口）

**Files:**
- Modify: `core/personality.py`

- [ ] **Step 1: 更新为兼容入口**

```python
"""
core/personality.py
兼容入口 — 将导入重定向到新模块
Phase 1 后旧代码已迁移，此文件仅作兼容导入
"""
import warnings
warnings.warn("core.personality is deprecated, use personality.engine instead", DeprecationWarning, stacklevel=2)

from personality.engine import PersonalityEngine, get_personality

__all__ = ["PersonalityEngine", "get_personality"]
```

- [ ] **Step 2: 验证导入**

Run: `python -c "from core.personality import PersonalityEngine; print('OK')"`
Expected: OK (with deprecation warning)

- [ ] **Step 3: Commit**

```bash
git add core/personality.py
git commit -m "refactor(phase1): update core/personality.py as compatibility shim"
```

---

## Task 13: 更新 core/memory_system.py（兼容入口）

**Files:**
- Modify: `core/memory_system.py`

- [ ] **Step 1: 更新为兼容入口**

```python
"""
core/memory_system.py
兼容入口 — 将导入重定向到新模块
Phase 1 后旧代码已迁移，此文件仅作兼容导入
"""
import warnings
warnings.warn("core.memory_system is deprecated, use memory.system instead", DeprecationWarning, stacklevel=2)

from memory.system import MemorySystem, get_memory

__all__ = ["MemorySystem", "get_memory"]
```

- [ ] **Step 2: 验证导入**

Run: `python -c "from core.memory_system import MemorySystem; print('OK')"`
Expected: OK (with deprecation warning)

- [ ] **Step 3: Commit**

```bash
git add core/memory_system.py
git commit -m "refactor(phase1): update core/memory_system.py as compatibility shim"
```

---

## Task 14: 更新 main.py 导入路径

**Files:**
- Modify: `main.py`

- [ ] **Step 1: 检查当前导入并更新**

从：
```python
from core.personality import get_personality
from core.memory_system import get_memory
from core.hyper_agents import HyperAgent
```

改为（保持兼容，同时添加新的直接导入）：
```python
from personality import get_personality
from memory import get_memory
from agents.hyper import HyperAgent
```

注：兼容导入已在 core/* 中设置，故 main.py 无需强制修改，但建议逐步切换到新路径。

- [ ] **Step 2: 验证 main.py 启动**

Run: `cd C:/Users/1/clawd/YuanFang && python main.py` (ctrl+c 立即退出)
Expected: 无 ImportError

- [ ] **Step 3: Commit** (if changes made)

---

## Task 15: 验证完整测试套件

- [ ] **Step 1: 运行所有测试**

Run: `cd C:/Users/1/clawd/YuanFang && pytest tests/ -v --tb=short`
Expected: 全部 PASS

- [ ] **Step 2: 验证 API 接口**

确认三个接口返回：
- `/api/memory/report` → `{"emotional": {...}, "scene": {...}}`
- `/api/personality/status` → `{"name": "元芳", "mood": ...}`
- `/api/hyper/status` → `{"evolution_count": ..., "memory_stats": {...}}`

- [ ] **Step 3: 最终 Commit**

```bash
git add -A
git commit -m "feat(phase1): complete module refactor - memory/, personality/, agents/hyper/"
```

---

## Self-Review Checklist

- [ ] Spec coverage: 每个设计文档中的需求都有对应的任务？
- [ ] Placeholder scan: 无 TBD/TODO/不完整的步骤？
- [ ] Type consistency: 所有接口的返回值类型一致？
- [ ] 所有测试可通过 `pytest tests/ -v`？
- [ ] `main.py` 可正常启动？
- [ ] 无循环导入？
- [ ] 所有文件使用 `pathlib.Path`？

---

*Plan version: v1.0 | Date: 2026-04-02 | Status: Ready for execution*
