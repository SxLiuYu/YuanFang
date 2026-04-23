# 🔌 智能音箱技能集成指南

支持所有主流智能音箱平台，通过统一后端 API 实现。

---

## 📋 支持平台

| 平台 | 厂商 | 配置目录 | 状态 |
|------|------|---------|------|
| **天猫精灵** | 阿里巴巴 | `tmall/` | ✅ 配置就绪 |
| **小爱同学** | 小米 | `xiaomi/` | ✅ 配置就绪 |
| **小度音箱** | 百度 | `baidu/` | ✅ 配置就绪 |
| **华为小艺** | 华为 | `huawei/` | ✅ 配置就绪 |
| **京东叮咚** | 京东 | `jd/` | ✅ 配置就绪 |
| **三星 Bixby** | 三星 | `samsung/` | ✅ 配置就绪 |
| **Apple HomeKit** | 苹果 | `homekit/` | ✅ 配置就绪 |

---

## 🚀 快速开始

### 步骤 1：选择平台

编辑 `../config/config.yaml`，启用你需要的平台：

```yaml
smart_speaker_skills:
  tmall:
    enabled: true  # 启用天猫精灵
  xiaomi:
    enabled: true  # 启用小爱同学
  # ... 其他平台
```

### 步骤 2：在对应平台创建技能

#### 天猫精灵
1. 访问：https://open.aligenie.com/
2. 创建技能 → 选择"自定义技能"
3. 填写技能信息
4. 配置意图（intent）和语音样本
5. 设置 Webhook URL：`https://your-server.com/api/v1/smart-speaker/tmall`
6. 提交审核

#### 小爱同学
1. 访问：https://developers.xiaoai.mi.com/
2. 创建技能 → 选择"对话技能"
3. 配置意图和样本
4. 设置 Webhook
5. 提交审核

#### 小度音箱
1. 访问：https://duer.baidu.com/
2. 创建技能
3. 配置意图
4. 设置 Webhook
5. 提交审核

#### 华为小艺
1. 访问：https://developer.huawei.com/consumer/cn/HMS-AI/
2. 创建快应用技能
3. 配置意图
4. 设置 Webhook
5. 提交审核

#### 京东叮咚
1. 访问：https://open.jd.com/
2. 创建技能
3. 配置 Webhook
4. 提交审核

#### 三星 Bixby
1. 访问：https://developer.bixby.com/
2. 使用 Bixby Developer Studio 创建 Capsule
3. 配置意图和对话流
4. 提交认证

#### Apple HomeKit
1. 需要 Apple 开发者账号 + MFi 认证
2. 使用 HomeKit Accessory Simulator 测试
3. 实现 HomeKit Accessory Protocol (HAP)
4. 通过 MFi 认证后上架

---

## 📁 配置文件说明

每个平台的 `skill.yaml` 包含：

```yaml
skill:
  name: "技能名称"
  version: "1.0.0"
  skill_id: ""        # 平台分配的 ID
  skill_secret: ""    # 平台分配的密钥
  
  intents:            # 意图定义
    - name: "chat"
      samples:
        - "你好"
        - "聊天"
        
  webhook:
    url: "https://your-server.com/api/v1/smart-speaker/tmall"
```

---

## 🔧 后端 API 集成

所有平台的请求会统一路由到后端：

```
POST /api/v1/smart-speaker/{platform}
```

平台标识：
- `tmall` - 天猫精灵
- `xiaomi` - 小爱同学
- `baidu` - 小度
- `huawei` - 华为小艺
- `jd` - 京东叮咚
- `samsung` - 三星 Bixby
- `homekit` - Apple HomeKit

后端会自动：
1. 验证平台签名
2. 解析意图
3. 调用对应的服务（聊天/智能家居/账本等）
4. 返回语音响应

---

## 🎯 支持的意图

所有平台支持以下通用意图：

| 意图 | 功能 | 示例 |
|------|------|------|
| `chat` | AI 聊天 | "你好"、"陪我聊聊" |
| `smart_home_control` | 智能家居控制 | "打开客厅的灯"、"关闭空调" |
| `account_query` | 家庭账本查询 | "今天花了多少钱"、"查账单" |
| `task_management` | 任务管理 | "添加任务"、"提醒我买菜" |
| `shopping_list` | 购物清单 | "我要买苹果"、"购物清单上有什么" |
| `recipe_help` | 做菜助手 | "怎么做红烧肉"、"教我做饭" |

---

## 📝 发布清单

发布前检查：

- [ ] 技能配置完整（skill_id、skill_secret）
- [ ] Webhook URL 正确（需要公网 HTTPS）
- [ ] 后端服务已部署并可访问
- [ ] 意图和语音样本覆盖全面
- [ ] TTS 语音配置正确
- [ ] 测试账号已配置
- [ ] 通过平台测试
- [ ] 提交审核

---

## 🔗 相关文档

- [语音/视频架构设计](../docs/VOICE-VIDEO-ARCHITECTURE.md)
- [配置文件说明](../config/config.example.yaml)
- [后端 API 文档](../backend/README.md)

---

**提示**: 建议先在一个平台（如天猫精灵）完成开发和测试，验证流程后再扩展到其他平台。
