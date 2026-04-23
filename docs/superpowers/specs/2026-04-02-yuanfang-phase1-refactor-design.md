# YuanFang Phase 1 重构设计文档

> **目标：** 将 `core/memory_system.py` 和 `core/hyper_agents.py` 拆分为独立模块，建立 TDD 测试基线

## 📋 现状

### 文件分布

| 文件 | 当前职责 | 问题 |
|------|---------|------|
| `core/memory_system.py` | EvolutionaryMemory + MemorySystem + VectorMemory + EmotionalMemory + SceneMemory（**两个不相关的系统混在一起**） | 1750行，单一文件职责过重 |
| `core/personality.py` | PersonalityEngine 人格引擎 | 与memory_system耦合 |
| `core/hyper_agents.py` | TaskAgent + MetaAgent + EvolutionaryMemory + HyperAgent | EvolutionaryMemory与memory_system重复定义 |
| `agents/` | 空目录，无代码 | 资源未利用 |

### 关键问题

1. **重复定义**：EvolutionaryMemory 在 `core/memory_system.py` 和 `core/hyper_agents.py` 中各有一份
2. **耦合严重**：MemorySystem 依赖 `core.llm_adapter.get_llm()`，人格引擎直接调用 LLM
3. **难以测试**：单一文件1000+行，无测试
4. **路径耦合**：使用 `__file__` 相对路径，模块边界模糊

---

## 🏗️ 目标架构

```
YuanFang/
├── agents/                         # Agent核心（新增）
│   ├── __init__.py
│   ├── hyper/                      # HyperAgent系统
│   │   ├── __init__.py
│   │   ├── task_agent.py           # TaskAgent
│   │   ├── meta_agent.py           # MetaAgent
│   │   ├── evolutionary_memory.py  # EvolutionaryMemory（从hyper_agents.py移出）
│   │   └── hyper_agent.py          # HyperAgent（整合层）
│   └── crew/                       # CrewAI团队（后续阶段）
│       └── lobstery_army_crew.py
│
├── memory/                         # 记忆系统（新增）
│   ├── __init__.py
│   ├── emotional.py               # EmotionalMemory
│   ├── scene.py                    # SceneMemory
│   ├── vector.py                   # VectorMemory（轻量级embedding）
│   └── system.py                   # MemorySystem统一入口
│
├── personality/                     # 人格引擎（从core/移出）
│   ├── __init__.py
│   ├── engine.py                   # PersonalityEngine
│   └── mood_prompts.py            # 情绪→system_prompt映射
│
├── adapters/                       # 外部集成（已有）
│   └── ...
│
├── core/                           # 核心入口（精简）
│   ├── __init__.py
│   ├── llm_adapter.py              # LLM统一适配器（已有，保留）
│   ├── app_state.py                # 全局状态（已有）
│   └── app_logging.py              # 日志（已有）
│
├── skills/                         # Superpowers skills
│   └── ...
│
├── services/                       # 基础设施服务（已有）
│   └── ...
│
└── tests/                          # TDD测试（新增）
    ├── agents/
    │   └── hyper/
    │       ├── test_task_agent.py
    │       ├── test_meta_agent.py
    │       ├── test_evolutionary_memory.py
    │       └── test_hyper_agent.py
    ├── memory/
    │   ├── test_emotional.py
    │   ├── test_scene.py
    │   ├── test_vector.py
    │   └── test_system.py
    └── personality/
        └── test_engine.py
```

---

## 🔧 关键设计决策

### 决策1：EvolutionaryMemory 归属

**结论**：保留在 `agents/hyper/evolutionary_memory.py`

理由：EvolutionaryMemory 是 HyperAgent 的专用组件，与通用记忆系统（情感/场景/向量）是不同层次。它是 TaskAgent→MetaAgent→HyperAgent 闭环的一部分，应该与 Agent 系统同目录。

### 决策2：模块间依赖关系

```
memory/           ← 无外部依赖（纯本地存储）
personality/     ← 无外部依赖
agents/hyper/    ← 可导入 memory/, personality/
core/            ← 可导入 agents/, memory/, personality/
routes/          ← 可导入 agents/, memory/, personality/, core/
```

**原则**：层级从上到下，禁止下层导入上层。core 是最低层，routes 是最高层。

### 决策3：LLM依赖处理

当前问题：
- `EvolutionaryMemory` 不直接依赖 LLM（使用外部传入的 chat_fn）
- `VectorMemory` 通过 `get_llm().embed()` 获取 embedding
- `PersonalityEngine` 可选使用 LLM 做情感检测

**解决方案**：
- `VectorMemory` 延迟初始化 LLM 调用，LLM不可用时退化为关键词匹配（已有此逻辑，保留）
- `PersonalityEngine` 情感检测优先用关键词匹配，LLM检测作为可选增强
- 所有模块对 LLM 的依赖通过函数参数注入，**禁止在模块内部 import LLM适配器**

### 决策4：存储路径

所有持久化路径统一使用：
```python
from pathlib import Path

# 模块级别：相对于模块文件位置
MODULE_DIR = Path(__file__).parent
DATA_DIR = MODULE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
```

不再使用 `os.path.join(os.path.dirname(__file__), ...)` 混合格式。

### 决策5：接口设计

**MemorySystem**（统一入口）：
```python
class MemorySystem:
    def __init__(self, llm_fn=None):  # LLM函数注入
        self.emotional = EmotionalMemory()
        self.scene = SceneMemory()
        self.vector = VectorMemory(llm_fn)

    def record_interaction(self, user_input, agent_response, emotion="neutral"): ...
    def auto_snapshot(self, nodes_data): ...
    def get_context_summary(self) -> str: ...
    def full_report(self) -> dict: ...
```

**PersonalityEngine**（统一入口）：
```python
class PersonalityEngine:
    def __init__(self, llm_fn=None):  # LLM函数注入，可选
        ...

    def get_system_prompt(self, context="", voice_mode=False, skill_context="") -> str: ...
    def update_mood(self, mood, energy_delta=0, stress_delta=0): ...
    def detect_emotion(self, user_text, ai_response) -> str: ...  # 优先关键词，LLM作增强
```

**HyperAgent**（统一入口）：
```python
class HyperAgent:
    def __init__(self, memory_system=None, personality_engine=None):
        self.task_agent = TaskAgent()
        self.meta_agent = MetaAgent()
        self.memory = memory_system or EvolutionaryMemory()
        self.personality = personality_engine
```

---

## 🚫 已知Anti-Patterns（避免）

1. **不要在模块内部 `from core.llm_adapter import get_llm`** — 使用函数参数注入
2. **不要使用全局单例强制初始化** — 使用工厂函数 `get_xxx()` 返回延迟初始化的单例
3. **不要在 `__init__.py` 中做重导出** — 直接导入具体类，便于静态分析
4. **不要混用 `os.path` 和 `pathlib`** — 统一使用 `pathlib.Path`

---

## 📄 文件操作清单

### 新建文件

```
agents/hyper/__init__.py
agents/hyper/task_agent.py
agents/hyper/meta_agent.py
agents/hyper/evolutionary_memory.py
agents/hyper/hyper_agent.py
agents/__init__.py
memory/__init__.py
memory/emotional.py
memory/scene.py
memory/vector.py
memory/system.py
personality/__init__.py
personality/engine.py
personality/mood_prompts.py
tests/agents/hyper/test_task_agent.py
tests/agents/hyper/test_meta_agent.py
tests/agents/hyper/test_evolutionary_memory.py
tests/agents/hyper/test_hyper_agent.py
tests/memory/test_emotional.py
tests/memory/test_scene.py
tests/memory/test_vector.py
tests/memory/test_system.py
tests/personality/test_engine.py
```

### 修改文件

```
core/hyper_agents.py   → 删除旧代码，保留独立运行入口，更新导入
core/memory_system.py  → 删除（内容已拆分）
core/personality.py    → 删除（内容已移至 personality/）
main.py                → 更新导入路径
routes/agent.py        → 更新导入路径（如果导入路径变了）
```

### 删除文件

```
core/memory_system.py  → 内容已迁移
core/personality.py    → 内容已迁移
core/hyper_agents.py  → 内容已迁移，保留文件作为入口兼容
```

---

## ✅ Phase 1 完成标准

1. 所有 `import` 语句正确，无循环依赖
2. `main.py` 启动不报错
3. `/api/memory/report` `/api/personality/status` `/api/hyper/status` 三个接口正常返回
4. 所有新增模块有基础单元测试，且测试通过
5. `tests/` 目录下测试文件存在且可运行 `pytest tests/ -v`

---

*文档版本：v1.0 | 日期：2026-04-02 | 状态：待用户确认后执行*
