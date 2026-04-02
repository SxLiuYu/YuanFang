# YuanFang Phase 3 设计文档

## Phase 3 目标
1. 修复所有损坏/截断文件
2. 完成 Superpowers skill 适配层
3. 适配器统一抽象（HA, MQTT, Frigate）
4. SkillEngine 与路由深度集成

---

## 修复计划

### 需要重建的文件

**core/**
- `llm_adapter.py` — FinnA API 适配器（litellm 封装）
- `rule_engine.py` — 规则引擎（场景自动化）
- `yuanfang_dream.py` — 梦想系统（KAIROS 洞察生成）
- `app_state.py` ✅ 已重建

**routes/**
- `openai_compat.py` — OpenAI 兼容 API
- `ws_events.py` — WebSocket 事件处理
- `rules_users.py` — 规则和用户管理
- `chat.py` ✅ 已重建

**services/**
- `daemon_mode.py` — KAIROS 守护进程
- `kairos_tools.py` — KAIROS 工具集
- `notification_hub.py` — 通知中心
- `user_manager.py` — 用户管理
- `__init__.py` ✅ 已重建

**clients/**
- `telegram_bot.py` — Telegram Bot

---

## Superpowers Skill 适配

Superpowers skill 格式：
```
skills/{domain}/
  SKILL.md           # 描述
  references/        # YuanFang-specific 实现
```

适配器：`skills/yuanfang_adapter.py` — 将 SKILL.md 转为 SkillEngine 可用格式

## 适配器统一抽象

```
adapters/
  base.py           # 统一接口（AdapterBase）
  ha_adapter.py     # HomeAssistant
  mqtt_adapter.py   # MQTT
  frigate_adapter.py # Frigate NVR
```

---
