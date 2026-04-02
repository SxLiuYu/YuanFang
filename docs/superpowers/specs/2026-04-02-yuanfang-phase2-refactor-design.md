# YuanFang Phase 2 重构设计文档

> **目标:** 拆分 routes/agent.py（500+行巨型文件），提取 SkillEngine，创建 CrewAI 协作层
> **架构:** 分层路由 + SkillEngine 独立 + CrewAI 团队协作
> **基于:** Phase 1 设计文档

---

## 📋 现状问题

| 问题 | 现状 | 影响 |
|------|------|------|
| **routes/agent.py 过大** | 500+行，混合路由+业务逻辑+SkillEngine | 修改风险极高，无法独立测试 |
| **SkillEngine 重复** | core/skill_engine.py 存在，但 routes/agent.py 底部又嵌入了完整副本 | 代码重复，维护困难 |
| **LobsterArmyCrew 缺失** | `from agents import LobsterArmyCrew` 但 agents/__init__.py 为空 | API `/api/agent/crew` 无法工作 |
| **路由未分层** | 所有端点堆在一个 Blueprint | 无法按功能独立加载/禁用 |

---

## 🏗️ 目标架构

```
routes/
  __init__.py          # 合并所有 blueprint（从各子模块导入）
  personality.py       # /api/personality/* 路由
  memory.py            # /api/memory/* 路由
  skills.py            # /api/skills/* 路由
  kairos.py            # /api/kairos/* 路由
  hyper.py             # /api/hyper/* 路由
  agent.py             # 保留 /api/agent/* (crew/single agent)

core/
  skill_engine.py      # SkillEngine 独立模块（从 routes/agent.py 提取）
  skill_engine.py      # 兼容入口（warnings 重定向到新位置）

agents/
  __init__.py         # 导出 HyperAgent, LobsterArmyCrew
  crew/
    __init__.py
    lobster_army_crew.py  # CrewAI 团队协作层
    base.py              # Crew 基类

skills/                   # YuanFang 业务 skills（Superpowers 格式）
  ha_control/
    SKILL.md
  conversation/
    SKILL.md
```

---

## 🔧 关键设计决策

### 决策1：SkillEngine 归属

**结论**：保留在 `core/skill_engine.py`

routes/agent.py 底部的 SkillEngine 是冗余副本（原始代码把它和路由写在同一个文件）。提取到 `core/skill_engine.py`，routes/agent.py 中的副本删除。

### 决策2：Blueprint 分层策略

每个功能域一个子 Blueprint，主 `routes/__init__.py` 聚合：

```python
# routes/personality.py
personality_bp = Blueprint("personality", __name__)
@personality_bp.route('/api/personality/status', methods=['GET'])
def personality_status(): ...

# routes/__init__.py
from routes.personality import personality_bp
from routes.memory import memory_bp
from routes.skills import skills_bp
from routes.kairos import kairos_bp
from routes.hyper import hyper_bp
from routes.agent import agent_bp  # 保留（crew + single agent）

def register_all_blueprints(app):
    for bp in [personality_bp, memory_bp, skills_bp, kairos_bp, hyper_bp, agent_bp]:
        app.register_blueprint(bp)
```

main.py 改为：
```python
from routes import register_all_blueprints
register_all_blueprints(app)
```

### 决策3：LobsterArmyCrew 实现

```python
# agents/crew/lobster_army_crew.py
from crewai import Crew, Agent, Task

class LobsterArmyCrew:
    def __init__(self):
        self.crew = Crew(
            agents=[...],  # researcher, executor, reporter
            tasks=[...],
            verbose=True
        )

    def run(self, task: str) -> dict:
        result = self.crew.kickoff(inputs={"task": task})
        return {"result": result, "crew": "LobsterArmy"}
```

如果 crewai 未安装或 API 不可用，退化为单 Agent 执行。

### 决策4：Superpowers Skill 适配

Superpowers skill 格式（SKILL.md + references/）适配到 YuanFang：

```
skills/
  {domain}/
    SKILL.md           # Superpowers 格式描述
    references/        # YuanFang-specific 参考实现
    yuanfang_adapter.py # 适配器：将 SKILL.md 转为 SkillEngine 可用格式
```

---

## 📄 文件操作清单

### 新建文件

```
routes/personality.py      # /api/personality/* 路由
routes/memory.py           # /api/memory/* 路由
routes/skills.py           # /api/skills/* 路由
routes/kairos.py           # /api/kairos/* 路由
routes/hyper.py            # /api/hyper/* 路由
routes/__init__.py         # 聚合所有 blueprint
agents/crew/
  __init__.py
  lobster_army_crew.py     # CrewAI 实现
  base.py                  # Crew 基类
skills/
  yuanfang_adapter.py       # Superpowers → YuanFang 适配器
  ha_control/
    SKILL.md
  conversation/
    SKILL.md
```

### 修改文件

```
routes/agent.py           # 删除技能引擎代码，仅保留 /api/agent/* 路由，thin文件
core/skill_engine.py      # 保留（已经是独立模块）
main.py                   # 更新 blueprint 注册方式
agents/__init__.py         # 导出 HyperAgent, LobsterArmyCrew
```

### 删除文件

```
routes/agent.py 中的 SkillEngine 副本（底部大段代码）
```

---

## ✅ Phase 2 完成标准

1. `python main.py` 启动无 ImportError
2. `/api/personality/status`、`/api/memory/report`、`/api/skills/report`、`/api/kairos/status`、`/api/hyper/status` 全部正常返回
3. `/api/agent/crew` 端点可访问（不报错 500）
4. 所有 Phase 1 测试继续通过
5. 新增 Phase 2 测试且通过

---

*文档版本: v1.0 | 日期: 2026-04-02 | 状态: 待执行*
