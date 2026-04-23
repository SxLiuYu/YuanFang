# 家庭服务 App 功能提案 v2.0

**创建时间**: 2026-03-04  
**优先级**: P0-P1  
**状态**: 待开发

---

## 📋 功能概览

| 功能 | 优先级 | 预计工时 | 技术难度 |
|------|--------|----------|----------|
| 智能家居统一控制 | P0 | 3 天 | ⭐⭐⭐⭐ |
| 家庭账本 | P0 | 2 天 | ⭐⭐⭐ |
| 家庭任务板 | P1 | 2 天 | ⭐⭐ |
| 智能购物清单 | P1 | 2 天 | ⭐⭐⭐ |

---

## 1️⃣ 智能家居统一控制

### 痛点
- 多个品牌 App 切换麻烦（米家、HomeKit、涂鸦等）
- 无法跨品牌联动
- 缺少统一能耗监控

### 功能设计

#### 核心功能
- ✅ **多平台接入**：米家、HomeKit、涂鸦、天猫精灵
- ✅ **统一设备列表**：所有设备在一个界面控制
- ✅ **场景编排**：自定义 IFTTT 规则
- ✅ **能耗统计**：各设备用电量分析
- ✅ **异常告警**：设备离线/异常状态推送

#### 技术架构
```
┌─────────────────────────────────────┐
│      Android/iOS App (UI 层)        │
└─────────────────────────────────────┘
                  ↕
┌─────────────────────────────────────┐
│   SmartHomeService.java (统一接口)   │
└─────────────────────────────────────┘
                  ↕
┌──────────┬──────────┬──────────────┐
│ 米家适配器 │ HomeKit  │ 涂鸦适配器   │
│ Adapter  │ Adapter  │ Adapter      │
└──────────┴──────────┴──────────────┘
                  ↕
┌─────────────────────────────────────┐
│     各品牌云平台 API / 本地网关      │
└─────────────────────────────────────┘
```

#### 数据库设计
```sql
-- 设备表
CREATE TABLE smart_devices (
    id INTEGER PRIMARY KEY,
    device_id TEXT UNIQUE,
    device_name TEXT,
    device_type TEXT,  -- light, switch, sensor, camera
    platform TEXT,     -- mihome, homekit, tuya
    room TEXT,
    is_online BOOLEAN,
    last_seen TIMESTAMP
);

-- 场景表
CREATE TABLE smart_scenes (
    id INTEGER PRIMARY KEY,
    scene_name TEXT,
    scene_type TEXT,  -- manual, auto, schedule
    triggers TEXT,    -- JSON: [{"type": "time", "value": "07:00"}]
    actions TEXT,     -- JSON: [{"device_id": "xxx", "action": "on"}]
    is_enabled BOOLEAN
);

-- 能耗记录表
CREATE TABLE energy_records (
    id INTEGER PRIMARY KEY,
    device_id TEXT,
    power_consumption REAL,  -- kWh
    recorded_at TIMESTAMP
);
```

---

## 2️⃣ 家庭账本

### 痛点
- 家庭成员消费分散，难以统计
- 预算超支无预警
- 缺少分类报表

### 功能设计

#### 核心功能
- ✅ **收支记录**：支持分类、标签、备注
- ✅ **家庭共享**：多成员同步账本
- ✅ **预算管理**：月度/年度预算设置
- ✅ **智能报表**：饼图/折线图/趋势分析
- ✅ **语音记账**：AI 自动识别分类

#### 技术架构
```
┌─────────────────────────────────────┐
│   FamilyFinanceActivity.java        │
│   - 记账界面                         │
│   - 报表展示                         │
│   - 预算管理                         │
└─────────────────────────────────────┘
                  ↕
┌─────────────────────────────────────┐
│   FinanceService.java               │
│   - 数据 CRUD                        │
│   - 统计分析                         │
│   - 预算预警                         │
└─────────────────────────────────────┘
                  ↕
┌─────────────────────────────────────┐
│   RoomDB (本地) + 云端同步 (可选)    │
└─────────────────────────────────────┘
```

#### 数据库设计
```sql
-- 账目表
CREATE TABLE transactions (
    id INTEGER PRIMARY KEY,
    amount REAL,
    type TEXT,  -- income, expense
    category TEXT,  -- 餐饮，交通，购物，娱乐，医疗，教育
    subcategory TEXT,
    note TEXT,
    recorded_by TEXT,
    recorded_at TIMESTAMP,
    family_id TEXT  -- 家庭 ID，用于共享
);

-- 预算表
CREATE TABLE budgets (
    id INTEGER PRIMARY KEY,
    category TEXT,
    amount REAL,
    period TEXT,  -- monthly, yearly
    start_date DATE,
    end_date DATE
);

-- 家庭成员表
CREATE TABLE family_members (
    id INTEGER PRIMARY KEY,
    member_name TEXT,
    role TEXT,  -- admin, member
    joined_at TIMESTAMP
);
```

---

## 3️⃣ 家庭任务板

### 痛点
- 家务分配不明确
- 孩子任务缺少激励
- 完成情况难追踪

### 功能设计

#### 核心功能
- ✅ **任务创建**：支持重复任务（每日/每周）
- ✅ **任务分配**：指定负责人
- ✅ **积分系统**：完成任务获得积分
- ✅ **排行榜**：家庭积分排名
- ✅ **奖励兑换**：积分换礼物/特权

#### 技术架构
```
┌─────────────────────────────────────┐
│   FamilyTaskActivity.java           │
│   - 任务列表                         │
│   - 任务创建/编辑                    │
│   - 积分排行榜                       │
└─────────────────────────────────────┘
                  ↕
┌─────────────────────────────────────┐
│   TaskService.java                  │
│   - 任务管理                         │
│   - 积分计算                         │
│   - 提醒推送                         │
└─────────────────────────────────────┘
```

#### 数据库设计
```sql
-- 任务表
CREATE TABLE tasks (
    id INTEGER PRIMARY KEY,
    task_name TEXT,
    task_description TEXT,
    assigned_to TEXT,  -- 负责人
    points INTEGER,    -- 完成奖励积分
    due_date TIMESTAMP,
    repeat_rule TEXT,  -- JSON: {"type": "weekly", "days": [1,3,5]}
    status TEXT,  -- pending, completed, overdue
    created_by TEXT
);

-- 积分记录表
CREATE TABLE points_log (
    id INTEGER PRIMARY KEY,
    member_name TEXT,
    points INTEGER,  -- 正数为获得，负数为消耗
    reason TEXT,
    recorded_at TIMESTAMP
);

-- 奖励表
CREATE TABLE rewards (
    id INTEGER PRIMARY KEY,
    reward_name TEXT,
    cost_points INTEGER,
    is_available BOOLEAN
);
```

---

## 4️⃣ 智能购物清单

### 痛点
- 忘记买什么
- 不知道哪家便宜
- 补货时机难把握

### 功能设计

#### 核心功能
- ✅ **语音/文字添加**：AI 自动分类
- ✅ **价格对比**：京东/淘宝/拼多多比价
- ✅ **补货提醒**：基于消耗频率智能预测
- ✅ **清单共享**：家庭成员实时同步
- ✅ **一键下单**：跳转电商平台

#### 技术架构
```
┌─────────────────────────────────────┐
│   ShoppingListActivity.java         │
│   - 清单管理                         │
│   - 价格对比                         │
│   - 补货提醒                         │
└─────────────────────────────────────┘
                  ↕
┌─────────────────────────────────────┐
│   ShoppingService.java              │
│   - 清单 CRUD                        │
│   - 价格爬取                         │
│   - 智能预测                         │
└─────────────────────────────────────┘
                  ↕
┌─────────────────────────────────────┐
│   电商平台 API / 爬虫                │
└─────────────────────────────────────┘
```

#### 数据库设计
```sql
-- 购物清单项
CREATE TABLE shopping_items (
    id INTEGER PRIMARY KEY,
    item_name TEXT,
    category TEXT,  -- 食品，日用，家电
    quantity INTEGER,
    unit TEXT,  -- 个，瓶，kg
    estimated_price REAL,
    is_purchased BOOLEAN,
    purchased_at TIMESTAMP,
    added_by TEXT
);

-- 价格历史记录
CREATE TABLE price_history (
    id INTEGER PRIMARY KEY,
    item_name TEXT,
    platform TEXT,  -- jd, tb, pdd
    price REAL,
    recorded_at TIMESTAMP
);

-- 消耗频率统计
CREATE TABLE consumption_stats (
    id INTEGER PRIMARY KEY,
    item_name TEXT,
    avg_days_between_purchases INTEGER,
    last_purchased_at TIMESTAMP
);
```

---

## 📅 开发计划

### 第一阶段（本周）
- [ ] 智能家居统一控制 - 基础框架
- [ ] 家庭账本 - 核心功能

### 第二阶段（下周）
- [ ] 家庭任务板
- [ ] 智能购物清单

### 第三阶段（优化迭代）
- [ ] AI 语音记账
- [ ] 电商平台比价
- [ ] 跨设备同步

---

## 🔗 相关资源

- 米家 API: https://miot-spec.org/
- HomeKit: https://developer.apple.com/homekit/
- 涂鸦云开发：https://iot.tuya.com/
- 京东开放平台：https://open.jd.com/
