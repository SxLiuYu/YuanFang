# OpenClaw 家庭助手 - 代码逻辑文档

**版本**: v1.0  
**更新日期**: 2026-03-19  
**作者**: OpenClaw 开发团队

---

## 目录

1. [项目架构](#一项目架构)
2. [后端服务模块](#二后端服务模块)
3. [Windows 客户端模块](#三windows-客户端模块)
4. [API 端点设计](#四api-端点设计)
5. [数据模型设计](#五数据模型设计)
6. [数据库设计](#六数据库设计)
7. [核心算法](#七核心算法)
8. [关键代码解析](#八关键代码解析)

---

## 一、项目架构

### 1.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户界面层                            │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Windows WPF  │  │ Flutter Mobile│  │     Web      │      │
│  │   客户端      │  │     客户端     │  │    客户端     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ HTTP/REST API
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        API 服务层                            │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              FastAPI 后端服务 (Python)                 │  │
│  │  • 语音 API  • 家庭 API  • 硬件 API  • 分析 API        │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        业务逻辑层                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │语音服务   │  │家庭服务   │  │硬件服务   │  │分析服务   │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                        数据存储层                            │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │ family.db │  │hardware.db│  │analytics.db│  │ voice.db │   │
│  │  (SQLite) │  │  (SQLite) │  │  (SQLite)  │  │ (SQLite) │   │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 1.2 技术栈

**后端技术栈**：
- **语言**: Python 3.10+
- **框架**: FastAPI 0.100+
- **数据验证**: Pydantic 2.0+
- **数据库**: SQLite 3
- **HTTP 服务器**: Uvicorn
- **配置管理**: PyYAML

**Windows 客户端技术栈**：
- **框架**: WPF (.NET 8)
- **架构模式**: MVVM
- **MVVM 框架**: CommunityToolkit.Mvvm 8.2+
- **UI 组件库**: MaterialDesignThemes 5.0+
- **图表库**: LiveChartsCore.SkiaSharpView.WPF 2.0+
- **HTTP 客户端**: RestSharp 110+
- **JSON 处理**: Newtonsoft.Json 13+
- **依赖注入**: Microsoft.Extensions.DependencyInjection 8.0+
- **Windows 集成**: Windows SDK Contracts 10.0.22621

### 1.3 目录结构

```
openclaw-clients/
├── backend/                          # 后端服务
│   ├── main.py                       # 主入口 (API 路由)
│   ├── services/                     # 服务层 (69个服务文件)
│   │   ├── voice_enhanced_service.py # 语音增强服务
│   │   ├── family_service.py         # 家庭协作服务
│   │   ├── hardware_service.py       # 硬件集成服务
│   │   ├── analytics_service.py      # 高级分析服务
│   │   └── ...                       # 其他服务
│   ├── requirements.txt              # Python 依赖
│   ├── Dockerfile                    # Docker 镜像
│   └── docker-compose.yml            # Docker 编排
│
├── windows-desktop/                  # Windows 客户端
│   └── OpenClaw.Desktop/
│       ├── App.xaml                  # 应用程序定义
│       ├── App.xaml.cs               # 依赖注入配置
│       ├── MainWindow.xaml           # 主窗口
│       ├── Models/                   # 数据模型
│       │   ├── VoiceModels.cs
│       │   ├── FamilyModels.cs
│       │   ├── HardwareModels.cs
│       │   └── AnalyticsModels.cs
│       ├── ViewModels/               # 视图模型
│       │   ├── MainViewModel.cs
│       │   ├── VoiceControlViewModel.cs
│       │   ├── FamilyGroupViewModel.cs
│       │   ├── HardwareViewModel.cs
│       │   └── AnalyticsViewModel.cs
│       ├── Views/                    # 视图
│       │   ├── VoiceControlView.xaml
│       │   ├── FamilyGroupView.xaml
│       │   ├── HardwareView.xaml
│       │   └── AnalyticsView.xaml
│       ├── Services/                 # 服务层
│       │   ├── Api/
│       │   │   ├── ApiClient.cs
│       │   │   ├── VoiceApiService.cs
│       │   │   ├── FamilyApiService.cs
│       │   │   ├── HardwareApiService.cs
│       │   │   └── AnalyticsApiService.cs
│       │   └── Voice/
│       │       └── VoiceRecognitionService.cs
│       └── Converters/               # 值转换器
│           └── CommonConverters.cs
│
├── docs/                             # 文档
│   ├── CODE.md                       # 本文档
│   ├── FAMILY-SERVICES-FULL.md       # 功能设计文档
│   ├── VOICE-VIDEO-ARCHITECTURE.md   # 架构设计文档
│   └── plans/                        # 设计方案
│       └── 2026-03-19-native-windows-app-design.md
│
└── README.md                         # 项目说明
```

---

## 二、后端服务模块

### 2.1 语音增强服务 (voice_enhanced_service.py)

**文件位置**: `backend/services/voice_enhanced_service.py`  
**代码行数**: ~850 行  
**功能描述**: 设备控制、场景控制、智能建议、自然语言日程解析

#### 2.1.1 核心类设计

```python
class VoiceEnhancedService:
    """语音增强服务"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self._init_database()
        
        # 设备控制命令模式
        self.device_control_patterns = {
            "turn_on": [r"打开(.+)", r"开启(.+)"],
            "turn_off": [r"关闭(.+)", r"关掉(.+)"],
            "adjust": [r"把(.+)(调|设置)(到|为)(.+)"],
            "query": [r"查询(.+)状态"]
        }
        
        # 场景控制命令模式
        self.scene_control_patterns = {
            "home": [r"我(回)?家了", r"回家模式"],
            "leave": [r"我(出)?门了", r"离家模式"],
            "sleep": [r"我要睡觉(了)?", r"睡觉模式"],
            "work": [r"我要工作(了)?", r"工作模式"]
        }
        
        # 智能建议权重
        self.suggestion_weights = {
            "time": 0.3,
            "habit": 0.4,
            "context": 0.2,
            "popularity": 0.1
        }
```

#### 2.1.2 核心方法

**设备控制命令解析**:
```python
async def parse_device_control(self, text: str) -> Tuple[str, Dict[str, Any]]:
    """解析设备控制命令
    
    Args:
        text: 用户输入的语音文本
        
    Returns:
        (intent, slots): 意图和槽位信息
        
    Example:
        Input: "打开客厅的灯"
        Output: ("device_control", {"action": "turn_on", "device": "客厅的灯"})
    """
    text = text.strip()
    
    for action, patterns in self.device_control_patterns.items():
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                slots = {"action": action}
                
                if action in ["turn_on", "turn_off"]:
                    slots["device"] = match.group(1).strip()
                elif action == "adjust":
                    slots["device"] = match.groups()[0].strip()
                    slots["value"] = match.groups()[-1]
                    
                return "device_control", slots
    
    return "unknown", {}
```

**场景控制命令解析**:
```python
async def parse_scene_control(self, text: str) -> Tuple[str, Dict[str, Any]]:
    """解析场景控制命令
    
    Args:
        text: 用户输入的语音文本
        
    Returns:
        (intent, slots): 意图和槽位信息
        
    Example:
        Input: "我要睡觉了"
        Output: ("scene_control", {"scene": "sleep"})
    """
    for scene, patterns in self.scene_control_patterns.items():
        for pattern in patterns:
            if re.search(pattern, text):
                return "scene_control", {"scene": scene}
    
    return "unknown", {}
```

**智能建议生成**:
```python
async def get_suggestions(self, user_id: str = None, context: Dict[str, Any] = None) -> List[VoiceSuggestion]:
    """获取智能建议
    
    算法:
        1. 基于时间的建议（当前时段推荐）
        2. 基于习惯的建议（历史行为分析）
        3. 基于上下文的建议（当前场景）
        4. 综合评分并排序
    
    Returns:
        前 5 个最相关的建议
    """
    suggestions = []
    
    # 1. 基于时间的建议
    time_suggestions = await self._get_time_based_suggestions()
    suggestions.extend(time_suggestions)
    
    # 2. 基于习惯的建议
    habit_suggestions = await self._get_habit_based_suggestions(user_id)
    suggestions.extend(habit_suggestions)
    
    # 3. 基于上下文的建议
    if context:
        context_suggestions = await self._get_context_based_suggestions(context)
        suggestions.extend(context_suggestions)
    
    # 4. 计算综合得分并排序
    scored_suggestions = []
    for suggestion in suggestions:
        score = await self._calculate_suggestion_score(suggestion, user_id)
        scored_suggestions.append((score, suggestion))
    
    scored_suggestions.sort(key=lambda x: x[0], reverse=True)
    
    return [s[1] for s in scored_suggestions[:5]]
```

**自然语言日程解析**:
```python
async def parse_schedule(self, text: str, user_id: str = None) -> ScheduleParseResponse:
    """解析自然语言日程
    
    Args:
        text: 用户输入的语音文本
        
    Returns:
        ScheduleParseResponse: 解析结果
        
    Example:
        Input: "明天下午 3 点开会"
        Output: {
            "title": "开会",
            "start_time": "2026-03-20 15:00:00",
            "confidence": 0.85
        }
    """
    # 提取事件标题
    title = await self._extract_event_title(text)
    
    # 提取时间
    start_time, end_time, recurrence = await self._extract_time_info(text)
    
    # 计算置信度
    confidence = self._calculate_parse_confidence(title, start_time)
    
    return ScheduleParseResponse(
        success=True,
        title=title,
        start_time=start_time,
        end_time=end_time,
        recurrence=recurrence,
        confidence=confidence
    )
```

#### 2.1.3 数据库设计

```sql
-- 用户行为记录表
CREATE TABLE user_behaviors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT NOT NULL,
    action_type TEXT NOT NULL,
    action_data TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    context TEXT
);

-- 设备使用统计表
CREATE TABLE device_usage_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    action TEXT NOT NULL,
    count INTEGER DEFAULT 1,
    last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
    time_slot TEXT,
    UNIQUE(device_id, action, time_slot)
);
```

---

### 2.2 家庭协作服务 (family_service.py)

**文件位置**: `backend/services/family_service.py`  
**代码行数**: ~750 行  
**功能描述**: 群组管理、成员管理、位置共享、共享日程

#### 2.2.1 核心类设计

```python
class FamilyService:
    """家庭群组协作服务"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path
        self._init_database()
```

#### 2.2.2 核心方法

**创建家庭群组**:
```python
async def create_group(self, request: FamilyGroupCreate) -> Dict[str, Any]:
    """创建家庭群组
    
    流程:
        1. 生成群组 ID 和邀请码
        2. 插入群组记录
        3. 将创建者添加为管理员
        
    Returns:
        {"success": True, "group_id": "...", "invite_code": "..."}
    """
    group_id = str(uuid.uuid4())
    invite_code = self._generate_invite_code()  # 8位随机码
    now = datetime.now()
    
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    # 创建群组
    cursor.execute("""
        INSERT INTO family_groups (id, name, owner_id, invite_code, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (group_id, request.name, request.owner_id, invite_code, now))
    
    # 添加创建者为管理员
    cursor.execute("""
        INSERT INTO family_members (group_id, user_id, name, role, last_active)
        VALUES (?, ?, ?, 'owner', ?)
    """, (group_id, request.owner_id, request.owner_id, now))
    
    conn.commit()
    return {"success": True, "group_id": group_id, "invite_code": invite_code}
```

**位置共享**:
```python
async def share_location(self, group_id: str, request: LocationShare) -> Dict[str, Any]:
    """分享位置
    
    Args:
        group_id: 群组 ID
        request: 位置信息（latitude, longitude, address, accuracy）
        
    Returns:
        {"success": True, "message": "位置已分享"}
    """
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    # 验证成员身份
    cursor.execute("""
        SELECT user_id FROM family_members 
        WHERE group_id = ? AND user_id = ?
    """, (group_id, request.user_id))
    
    if not cursor.fetchone():
        return {"success": False, "message": "您不是群组成员"}
    
    # 保存位置
    cursor.execute("""
        INSERT INTO location_shares 
        (group_id, user_id, latitude, longitude, address, accuracy)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (group_id, request.user_id, request.latitude, request.longitude, 
          request.address, request.accuracy))
    
    conn.commit()
    return {"success": True, "message": "位置已分享"}
```

#### 2.2.3 数据库设计

```sql
-- 家庭群组表
CREATE TABLE family_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    invite_code TEXT UNIQUE,
    settings TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 群组成员表
CREATE TABLE family_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    role TEXT DEFAULT 'member',
    avatar TEXT,
    last_active DATETIME,
    FOREIGN KEY (group_id) REFERENCES family_groups(id),
    UNIQUE(group_id, user_id)
);

-- 位置共享表
CREATE TABLE location_shares (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL,
    address TEXT,
    accuracy REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 共享日程表
CREATE TABLE shared_schedules (
    id TEXT PRIMARY KEY,
    group_id TEXT NOT NULL,
    title TEXT NOT NULL,
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    assignees TEXT,
    status TEXT DEFAULT 'pending'
);
```

---

### 2.3 硬件集成服务 (hardware_service.py)

**文件位置**: `backend/services/hardware_service.py`  
**代码行数**: ~650 行  
**功能描述**: 设备管理、智能手表数据同步、蓝牙设备管理

#### 2.3.1 核心方法

**设备注册**:
```python
async def register_device(self, request: DeviceRegister) -> Dict[str, Any]:
    """注册设备
    
    Args:
        request: 设备信息（name, type, brand, model）
        
    Returns:
        {"success": True, "device_id": "..."}
    """
    device_id = str(uuid.uuid4())
    
    cursor.execute("""
        INSERT INTO hardware_devices (id, name, type, brand, model, metadata, status)
        VALUES (?, ?, ?, ?, ?, ?, 'online')
    """, (device_id, request.name, request.type, request.brand, request.model,
          json.dumps(request.metadata or {})))
    
    return {"success": True, "device_id": device_id}
```

**智能手表数据同步**:
```python
async def sync_watch_data(self, request: WatchDataSync) -> Dict[str, Any]:
    """同步智能手表数据
    
    Args:
        request: 手表数据（heart_rate, steps, sleep_duration, calories）
        
    Returns:
        {"success": True, "message": "数据同步成功"}
    """
    # 验证设备存在
    cursor.execute("""
        SELECT id FROM hardware_devices 
        WHERE id = ? AND type = 'smart_watch'
    """, (request.device_id,))
    
    if not cursor.fetchone():
        return {"success": False, "message": "智能手表设备不存在"}
    
    # 插入数据
    cursor.execute("""
        INSERT INTO watch_data 
        (device_id, user_id, timestamp, heart_rate, steps, sleep_duration, 
         calories, blood_oxygen, blood_pressure)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (request.device_id, request.user_id, request.timestamp,
          request.heart_rate, request.steps, request.sleep_duration,
          request.calories, request.blood_oxygen,
          json.dumps(request.blood_pressure) if request.blood_pressure else None))
    
    # 更新设备最后同步时间
    cursor.execute("""
        UPDATE hardware_devices SET last_sync = ?, status = 'online'
        WHERE id = ?
    """, (datetime.now(), request.device_id))
    
    return {"success": True, "message": "数据同步成功"}
```

**蓝牙设备扫描**:
```python
async def scan_bluetooth_devices(self) -> List[Dict[str, Any]]:
    """扫描蓝牙设备（模拟）
    
    Returns:
        [{"device_id": "...", "name": "...", "type": "...", "rssi": -45, "is_paired": False}]
    """
    # 模拟扫描结果（实际应调用 Windows Bluetooth API）
    mock_devices = [
        {"id": "bt_001", "name": "小米手环8", "type": "smart_watch", "rssi": -45, "is_paired": False},
        {"id": "bt_002", "name": "小爱音箱Pro", "type": "smart_speaker", "rssi": -60, "is_paired": True},
        {"id": "bt_003", "name": "华为体脂秤", "type": "health_device", "rssi": -70, "is_paired": False},
    ]
    
    return mock_devices
```

#### 2.3.2 数据库设计

```sql
-- 设备表
CREATE TABLE hardware_devices (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    brand TEXT,
    model TEXT,
    status TEXT DEFAULT 'offline',
    battery_level INTEGER,
    last_sync DATETIME,
    metadata TEXT
);

-- 手表数据表
CREATE TABLE watch_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    heart_rate INTEGER,
    steps INTEGER,
    sleep_duration INTEGER,
    calories INTEGER,
    blood_oxygen REAL,
    blood_pressure TEXT
);

-- 设备日志表
CREATE TABLE device_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    device_id TEXT NOT NULL,
    action TEXT NOT NULL,
    params TEXT,
    result TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

### 2.4 高级分析服务 (analytics_service.py)

**文件位置**: `backend/services/analytics_service.py`  
**代码行数**: ~500 行  
**功能描述**: 健康评分、消费洞察、异常预警、报告生成

#### 2.4.1 核心方法

**健康评分计算**:
```python
async def calculate_health_score(self, request: HealthScoreRequest) -> Dict[str, Any]:
    """计算健康评分（0-100）
    
    算法:
        score = heart_score * 0.3 + steps_score * 0.3 + sleep_score * 0.25 + oxygen_score * 0.15
    
    Returns:
        {
            "score": 85.5,
            "grade": "良好",
            "components": {"heart_rate": {...}, "steps": {...}, ...},
            "suggestions": [...]
        }
    """
    # 获取最近 7 天数据
    cursor.execute("""
        SELECT AVG(heart_rate), SUM(steps), AVG(sleep_duration), AVG(blood_oxygen)
        FROM watch_data
        WHERE user_id = ? AND timestamp >= datetime('now', '-7 days')
    """, (request.user_id,))
    
    row = cursor.fetchone()
    avg_hr, total_steps, avg_sleep, avg_oxygen = row
    
    # 计算各维度得分
    heart_score = self._calculate_heart_score(avg_hr)      # 60-100 bpm → 100分
    steps_score = self._calculate_steps_score(total_steps / 7)  # 10000步/天 → 100分
    sleep_score = self._calculate_sleep_score(avg_sleep)   # 7-9小时 → 100分
    oxygen_score = self._calculate_oxygen_score(avg_oxygen) # >95% → 100分
    
    # 加权平均
    total_score = (
        heart_score * 0.3 +
        steps_score * 0.3 +
        sleep_score * 0.25 +
        oxygen_score * 0.15
    )
    
    return {
        "score": round(total_score, 1),
        "grade": self._get_grade(total_score),
        "components": {
            "heart_rate": {"score": heart_score, "value": avg_hr},
            "steps": {"score": steps_score, "value": total_steps},
            "sleep": {"score": sleep_score, "value": avg_sleep},
            "oxygen": {"score": oxygen_score, "value": avg_oxygen}
        },
        "suggestions": self._get_health_suggestions(...)
    }
```

**消费洞察分析**:
```python
async def get_finance_insights(self, request: FinanceInsightRequest) -> Dict[str, Any]:
    """获取消费洞察
    
    Args:
        request: user_id, period_days
        
    Returns:
        {
            "total_income": 10000,
            "total_expense": 6500,
            "balance": 3500,
            "categories": [...],
            "insights": [...]
        }
    """
    # 消费分类统计
    cursor.execute("""
        SELECT category, SUM(amount) as total
        FROM transactions
        WHERE type = 'expense' AND date >= datetime('now', ?)
        GROUP BY category ORDER BY total DESC
    """, (f'-{request.period_days} days',))
    
    # 生成洞察
    insights = []
    if categories:
        top_category = categories[0]
        insights.append(f"最大支出类别: {top_category['category']}（{top_category['amount']}元）")
    
    if total_income > 0:
        savings_rate = (total_income - total_expense) / total_income * 100
        insights.append(f"储蓄率: {savings_rate:.1f}%")
    
    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "categories": categories[:5],
        "insights": insights
    }
```

**异常检测**:
```python
async def check_anomalies(self, request: AnomalyCheckRequest) -> List[Dict[str, Any]]:
    """检测异常
    
    Args:
        request: user_id, data_type ("health" | "finance")
        
    Returns:
        [{"type": "heart_rate_high", "severity": "warning", "message": "..."}]
    """
    anomalies = []
    
    if request.data_type == "health":
        # 检查心率异常
        cursor.execute("""
            SELECT MAX(heart_rate), MIN(heart_rate)
            FROM watch_data 
            WHERE user_id = ? AND timestamp >= datetime('now', '-1 day')
        """, (request.user_id,))
        
        max_hr, min_hr = cursor.fetchone()
        
        if max_hr and max_hr > 120:
            anomalies.append({
                "type": "heart_rate_high",
                "severity": "warning",
                "message": f"检测到心率异常偏高: 最高{max_hr}次/分"
            })
        
        # 检查血氧
        if min_oxygen and min_oxygen < 90:
            anomalies.append({
                "type": "blood_oxygen_low",
                "severity": "critical",
                "message": f"检测到血氧过低: 最低{min_oxygen}%"
            })
    
    return anomalies
```

---

## 三、Windows 客户端模块

### 3.1 MVVM 架构

**架构图**:
```
┌─────────────────────────────────────────────────────┐
│                      View (XAML)                     │
│  • 用户界面元素                                       │
│  • 数据绑定到 ViewModel                              │
│  • 触发 Command                                      │
└─────────────────────────────────────────────────────┘
                         │ Binding
                         ▼
┌─────────────────────────────────────────────────────┐
│                   ViewModel (C#)                     │
│  • ObservableProperty (自动属性通知)                  │
│  • RelayCommand (命令模式)                           │
│  • 业务逻辑处理                                      │
│  • 调用 Service                                      │
└─────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────┐
│                    Service (C#)                      │
│  • API 调用 (VoiceApiService, FamilyApiService...)  │
│  • 数据转换                                          │
│  • 错误处理                                          │
└─────────────────────────────────────────────────────┘
```

### 3.2 依赖注入配置

**文件**: `App.xaml.cs`

```csharp
private void ConfigureServices(IServiceCollection services)
{
    // API 客户端
    services.AddSingleton<ApiClient>();
    
    // API 服务
    services.AddSingleton<VoiceApiService>();
    services.AddSingleton<FamilyApiService>();
    services.AddSingleton<HardwareApiService>();
    services.AddSingleton<AnalyticsApiService>();
    
    // 服务
    services.AddSingleton<VoiceService>();
    services.AddSingleton<TrayService>();
    services.AddSingleton<VoiceRecognitionService>();
    services.AddSingleton<TTSService>();
    
    // ViewModel
    services.AddSingleton<MainViewModel>();
    services.AddSingleton<VoiceControlViewModel>();
    services.AddSingleton<FamilyGroupViewModel>();
    services.AddSingleton<HardwareViewModel>();
    services.AddSingleton<AnalyticsViewModel>();
    services.AddSingleton<HealthViewModel>();
    services.AddSingleton<FinanceViewModel>();
    
    // Views
    services.AddTransient<VoiceControlView>();
    services.AddTransient<FamilyGroupView>();
    services.AddTransient<HardwareView>();
    services.AddTransient<AnalyticsView>();
    
    // 主窗口
    services.AddSingleton<MainWindow>();
}
```

### 3.3 API 服务层

**基础 API 客户端**:
```csharp
public class ApiClient
{
    private readonly HttpClient _httpClient;
    private readonly string _baseUrl = "http://localhost:8082";
    
    public async Task<T?> GetAsync<T>(string endpoint)
    {
        var response = await _httpClient.GetAsync($"{_baseUrl}{endpoint}");
        response.EnsureSuccessStatusCode();
        
        var json = await response.Content.ReadAsStringAsync();
        var result = JsonConvert.DeserializeObject<ApiResponse<T>>(json);
        
        return result?.Data;
    }
    
    public async Task<T?> PostAsync<T>(string endpoint, object? data)
    {
        var json = JsonConvert.SerializeObject(data);
        var content = new StringContent(json, Encoding.UTF8, "application/json");
        
        var response = await _httpClient.PostAsync($"{_baseUrl}{endpoint}", content);
        response.EnsureSuccessStatusCode();
        
        var responseJson = await response.Content.ReadAsStringAsync();
        var result = JsonConvert.DeserializeObject<ApiResponse<T>>(responseJson);
        
        return result?.Data;
    }
}
```

**语音 API 服务**:
```csharp
public class VoiceApiService
{
    private readonly ApiClient _apiClient;
    private readonly string _baseUrl = "/api/v1/voice";
    
    public async Task<VoiceCommandResponse> ProcessCommandAsync(string text)
    {
        var request = new VoiceCommandRequest { Text = text };
        return await _apiClient.PostAsync<VoiceCommandResponse>(
            $"{_baseUrl}/command", request
        ) ?? new VoiceCommandResponse { Success = false };
    }
    
    public async Task<List<VoiceSuggestion>> GetSuggestionsAsync(string? userId = null)
    {
        var url = $"{_baseUrl}/suggestions";
        if (!string.IsNullOrEmpty(userId))
            url += $"?user_id={userId}";
            
        return await _apiClient.GetAsync<List<VoiceSuggestion>>(url) 
            ?? new List<VoiceSuggestion>();
    }
}
```

### 3.4 ViewModel 示例

**语音控制 ViewModel**:
```csharp
public partial class VoiceControlViewModel : BaseViewModel
{
    private readonly VoiceApiService _voiceApiService;
    private readonly VoiceRecognitionService _voiceRecognitionService;
    private readonly TTSService _ttsService;
    
    [ObservableProperty]
    private bool _isListening;
    
    [ObservableProperty]
    private string _recognizedText = "按下麦克风开始说话...";
    
    [ObservableProperty]
    private string _responseMessage = "";
    
    public ObservableCollection<VoiceSuggestion> Suggestions { get; } = new();
    
    public ICommand ToggleListeningCommand { get; }
    public ICommand ExecuteSuggestionCommand { get; }
    
    public VoiceControlViewModel(
        VoiceApiService voiceApiService,
        VoiceRecognitionService voiceRecognitionService,
        TTSService ttsService)
    {
        _voiceApiService = voiceApiService;
        _voiceRecognitionService = voiceRecognitionService;
        _ttsService = ttsService;
        
        ToggleListeningCommand = new AsyncRelayCommand(ToggleListeningAsync);
        ExecuteSuggestionCommand = new AsyncRelayCommand<VoiceSuggestion>(ExecuteSuggestionAsync);
        
        _voiceRecognitionService.Recognized += OnVoiceRecognized;
    }
    
    private async void OnVoiceRecognized(object? sender, string text)
    {
        RecognizedText = text;
        await ProcessCommandAsync(text);
    }
    
    private async Task ProcessCommandAsync(string text)
    {
        var response = await _voiceApiService.ProcessCommandAsync(text);
        
        if (response.Success)
        {
            ResponseMessage = response.Message;
            Suggestions.Clear();
            foreach (var suggestion in response.Suggestions)
                Suggestions.Add(suggestion);
            
            await _ttsService.SpeakAsync(response.Message);
        }
    }
}
```

---

## 四、API 端点设计

### 4.1 语音 API

| 方法 | 端点 | 功能 | 参数 |
|------|------|------|------|
| POST | `/api/v1/voice/control/device` | 设备控制 | `text`, `context` |
| POST | `/api/v1/voice/control/scene` | 场景控制 | `text`, `context` |
| GET | `/api/v1/voice/suggestions` | 获取智能建议 | `user_id` |
| POST | `/api/v1/voice/schedule/parse` | 日程解析 | `text`, `user_id` |
| POST | `/api/v1/voice/command` | 统一入口 | `text`, `context` |

### 4.2 家庭 API

| 方法 | 端点 | 功能 | 参数 |
|------|------|------|------|
| POST | `/api/v1/family/groups` | 创建群组 | `name`, `owner_id` |
| GET | `/api/v1/family/groups/{id}` | 群组详情 | `id` |
| PUT | `/api/v1/family/groups/{id}` | 更新群组 | `name`, `settings` |
| DELETE | `/api/v1/family/groups/{id}` | 删除群组 | `owner_id` |
| POST | `/api/v1/family/join` | 加入群组 | `invite_code`, `user_id`, `name` |
| POST | `/api/v1/family/groups/{id}/members` | 添加成员 | `user_id`, `name`, `role` |
| DELETE | `/api/v1/family/groups/{id}/members/{uid}` | 移除成员 | `operator_id` |
| POST | `/api/v1/family/location/share` | 分享位置 | `user_id`, `latitude`, `longitude` |
| GET | `/api/v1/family/groups/{id}/location/members` | 获取位置 | `id` |
| POST | `/api/v1/family/calendar/shared` | 创建共享日程 | `group_id`, `title`, `start_time` |
| GET | `/api/v1/family/groups/{id}/calendar/shared` | 获取共享日程 | `id`, `start_date`, `end_date` |

### 4.3 硬件 API

| 方法 | 端点 | 功能 | 参数 |
|------|------|------|------|
| GET | `/api/v1/hardware/devices` | 设备列表 | `device_type`, `status` |
| POST | `/api/v1/hardware/devices` | 注册设备 | `name`, `type`, `brand`, `model` |
| GET | `/api/v1/hardware/devices/{id}` | 设备详情 | `id` |
| POST | `/api/v1/hardware/devices/{id}/control` | 控制设备 | `action`, `params` |
| POST | `/api/v1/hardware/devices/watch/sync` | 同步手表数据 | `device_id`, `user_id`, `heart_rate`, `steps` |
| GET | `/api/v1/hardware/devices/{id}/watch/data` | 获取手表数据 | `id`, `user_id`, `days` |
| GET | `/api/v1/hardware/devices/{id}/watch/summary` | 健康摘要 | `id`, `user_id` |
| POST | `/api/v1/hardware/devices/speaker/command` | 音箱命令 | `device_id`, `command`, `content` |
| GET | `/api/v1/hardware/bluetooth/scan` | 扫描蓝牙 | - |
| POST | `/api/v1/hardware/bluetooth/pair` | 配对蓝牙 | `device_id`, `device_name`, `device_type` |

### 4.4 分析 API

| 方法 | 端点 | 功能 | 参数 |
|------|------|------|------|
| GET | `/api/v1/analytics/health/score` | 健康评分 | `user_id`, `device_id` |
| GET | `/api/v1/analytics/finance/insights` | 消费洞察 | `user_id`, `period_days` |
| GET | `/api/v1/analytics/anomalies` | 异常预警 | `user_id`, `data_type` |
| GET | `/api/v1/analytics/report/weekly` | 周报 | `user_id` |
| GET | `/api/v1/analytics/report/monthly` | 月报 | `user_id` |

---

## 五、数据模型设计

### 5.1 后端数据模型 (Pydantic)

```python
# 语音相关
class VoiceCommandRequest(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None
    user_id: Optional[str] = None

class VoiceCommandResponse(BaseModel):
    success: bool
    intent: str
    slots: Dict[str, Any]
    action: Optional[Dict[str, Any]] = None
    message: str
    suggestions: List[VoiceSuggestion] = []

class VoiceSuggestion(BaseModel):
    type: str
    title: str
    description: str
    confidence: float
    action: Dict[str, Any]

# 家庭相关
class FamilyGroup(BaseModel):
    id: str
    name: str
    owner_id: str
    members: List[FamilyMember]
    invite_code: str
    created_at: datetime

class FamilyMember(BaseModel):
    user_id: str
    name: str
    role: str
    location: Optional[Dict[str, Any]] = None

# 硬件相关
class HardwareDevice(BaseModel):
    id: str
    name: str
    type: str
    status: str
    battery_level: Optional[int] = None
    last_sync: Optional[datetime] = None

class WatchDataSync(BaseModel):
    device_id: str
    user_id: str
    timestamp: datetime
    heart_rate: Optional[int] = None
    steps: Optional[int] = None
    sleep_duration: Optional[int] = None

# 分析相关
class HealthScoreResponse(BaseModel):
    success: bool
    score: float
    grade: str
    components: Dict[str, Any]
    suggestions: List[str]
```

### 5.2 前端数据模型 (C#)

```csharp
// 语音相关
public class VoiceCommandRequest
{
    [JsonProperty("text")]
    public string Text { get; set; } = "";
    
    [JsonProperty("context")]
    public Dictionary<string, object>? Context { get; set; }
}

public class VoiceCommandResponse
{
    [JsonProperty("success")]
    public bool Success { get; set; }
    
    [JsonProperty("message")]
    public string Message { get; set; } = "";
    
    [JsonProperty("suggestions")]
    public List<VoiceSuggestion> Suggestions { get; set; } = new();
}

// 家庭相关
public class FamilyGroup
{
    [JsonProperty("id")]
    public string Id { get; set; } = "";
    
    [JsonProperty("name")]
    public string Name { get; set; } = "";
    
    [JsonProperty("members")]
    public List<FamilyMember> Members { get; set; } = new();
}

// 硬件相关
public class HardwareDevice
{
    [JsonProperty("id")]
    public string Id { get; set; } = "";
    
    [JsonProperty("name")]
    public string Name { get; set; } = "";
    
    [JsonProperty("status")]
    public string Status { get; set; } = "offline";
}

// 分析相关
public class HealthScoreResponse
{
    [JsonProperty("score")]
    public double Score { get; set; }
    
    [JsonProperty("grade")]
    public string Grade { get; set; } = "";
}
```

---

## 六、数据库设计

### 6.1 数据库文件

| 数据库 | 路径 | 用途 |
|-------|------|------|
| family.db | `data/family.db` | 家庭群组、成员、位置、日程 |
| hardware.db | `data/hardware.db` | 设备、手表数据、日志 |
| analytics.db | `data/analytics.db` | 分析缓存、异常记录 |
| voice_enhanced.db | `data/voice_enhanced.db` | 用户行为、设备统计 |

### 6.2 ER 图

```
family.db:
┌──────────────┐       ┌──────────────┐
│family_groups │       │family_members│
├──────────────┤       ├──────────────┤
│id (PK)       │◄──────│group_id (FK) │
│name          │       │user_id       │
│owner_id      │       │name          │
│invite_code   │       │role          │
└──────────────┘       └──────────────┘
       │                      │
       │                      │
       ▼                      ▼
┌──────────────┐       ┌──────────────┐
│location_shares│      │shared_schedules│
├──────────────┤       ├──────────────┤
│group_id (FK) │       │group_id (FK) │
│user_id       │       │title         │
│latitude      │       │start_time    │
│longitude     │       │assignees     │
└──────────────┘       └──────────────┘

hardware.db:
┌──────────────┐       ┌──────────────┐
│hardware_devices│     │watch_data    │
├──────────────┤       ├──────────────┤
│id (PK)       │◄──────│device_id (FK)│
│name          │       │user_id       │
│type          │       │heart_rate    │
│status        │       │steps         │
└──────────────┘       └──────────────┘
```

---

## 七、核心算法

### 7.1 健康评分算法

```python
def calculate_health_score(user_id: str) -> float:
    """计算健康评分（0-100）
    
    维度权重:
        - 心率: 30%
        - 步数: 30%
        - 睡眠: 25%
        - 血氧: 15%
    """
    # 获取最近 7 天数据
    health_data = get_health_data(user_id, days=7)
    
    # 心率评分（正常范围 60-100 bpm）
    def heart_score(hr):
        if 60 <= hr <= 100:
            return 100
        elif 50 <= hr < 60 or 100 < hr <= 110:
            return 80
        else:
            return 60
    
    # 步数评分（目标 10000 步/天）
    def steps_score(steps):
        if steps >= 10000:
            return 100
        elif steps >= 8000:
            return 90
        elif steps >= 5000:
            return 70
        else:
            return 50
    
    # 睡眠评分（理想 7-9 小时）
    def sleep_score(hours):
        if 7 <= hours <= 9:
            return 100
        elif 6 <= hours < 7 or 9 < hours <= 10:
            return 80
        else:
            return 60
    
    # 血氧评分（正常 >95%）
    def oxygen_score(oxygen):
        if oxygen >= 95:
            return 100
        elif oxygen >= 90:
            return 80
        else:
            return 60
    
    # 加权计算
    score = (
        heart_score(health_data.avg_heart_rate) * 0.3 +
        steps_score(health_data.avg_steps) * 0.3 +
        sleep_score(health_data.avg_sleep) * 0.25 +
        oxygen_score(health_data.avg_blood_oxygen) * 0.15
    )
    
    return round(score, 1)
```

### 7.2 智能建议算法

```python
async def get_suggestions(user_id: str) -> List[Suggestion]:
    """生成智能建议
    
    算法流程:
        1. 基于时间的建议（当前时段）
        2. 基于习惯的建议（历史行为）
        3. 基于上下文的建议（当前场景）
        4. 综合评分排序
    """
    suggestions = []
    now = datetime.now()
    
    # 1. 基于时间的建议
    if 6 <= now.hour < 9:
        suggestions.append(Suggestion(
            type="scene",
            title="起床模式",
            confidence=0.8,
            weights={"time": 0.8, "habit": 0, "context": 0}
        ))
    elif 18 <= now.hour < 22:
        suggestions.append(Suggestion(
            type="scene",
            title="回家模式",
            confidence=0.9,
            weights={"time": 0.9, "habit": 0, "context": 0}
        ))
    
    # 2. 基于习惯的建议
    user_behaviors = get_user_behaviors(user_id, days=7)
    frequent_actions = analyze_frequent_actions(user_behaviors)
    
    for action in frequent_actions:
        if action.count >= 3:  # 至少执行 3 次
            suggestions.append(Suggestion(
                type="habit",
                title=f"常用：{action.name}",
                confidence=min(0.5 + action.count * 0.05, 0.9),
                weights={"time": 0, "habit": 0.7, "context": 0}
            ))
    
    # 3. 综合评分
    for suggestion in suggestions:
        score = (
            suggestion.weights["time"] * 0.3 +
            suggestion.weights["habit"] * 0.4 +
            suggestion.weights["context"] * 0.2 +
            suggestion.confidence * 0.1
        )
        suggestion.final_score = score
    
    # 排序返回前 5
    return sorted(suggestions, key=lambda x: x.final_score, reverse=True)[:5]
```

### 7.3 异常检测算法

```python
def detect_health_anomalies(user_id: str) -> List[Anomaly]:
    """检测健康异常
    
    检测维度:
        - 心率异常（过高/过低）
        - 血氧异常（过低）
        - 睡眠异常（过短）
    """
    anomalies = []
    recent_data = get_recent_health_data(user_id, hours=24)
    
    # 心率检测
    if recent_data.max_heart_rate > 120:
        anomalies.append(Anomaly(
            type="heart_rate_high",
            severity="warning",
            message=f"心率偏高: 最高 {recent_data.max_heart_rate} 次/分"
        ))
    
    # 血氧检测
    if recent_data.min_blood_oxygen < 90:
        anomalies.append(Anomaly(
            type="blood_oxygen_low",
            severity="critical",
            message=f"血氧过低: 最低 {recent_data.min_blood_oxygen}%"
        ))
    
    # 睡眠检测
    if recent_data.sleep_duration < 5:
        anomalies.append(Anomaly(
            type="sleep_insufficient",
            severity="warning",
            message=f"睡眠不足: 仅 {recent_data.sleep_duration} 小时"
        ))
    
    return anomalies
```

---

## 八、关键代码解析

### 8.1 语音命令处理流程

```python
async def process_voice_command(text: str) -> VoiceCommandResponse:
    """
    处理流程:
        1. 文本预处理（去除空格、标点）
        2. 意图识别（设备控制 vs 场景控制 vs 其他）
        3. 槽位提取（设备名称、动作、参数）
        4. 执行动作
        5. 生成响应
        6. 生成建议
    """
    # Step 1: 预处理
    text = text.strip()
    
    # Step 2: 意图识别
    intent, slots = await parse_intent(text)
    
    # Step 3: 执行
    if intent == "device_control":
        result = await execute_device_control(slots)
    elif intent == "scene_control":
        result = await execute_scene_control(slots)
    else:
        return error_response("无法识别命令")
    
    # Step 4: 生成建议
    suggestions = await generate_suggestions(intent, slots)
    
    return VoiceCommandResponse(
        success=True,
        intent=intent,
        slots=slots,
        message=result.message,
        suggestions=suggestions
    )
```

### 8.2 家庭群组创建流程

```python
async def create_family_group(name: str, owner_id: str) -> Dict:
    """
    创建流程:
        1. 生成群组 ID (UUID)
        2. 生成邀请码 (8位随机)
        3. 插入群组记录
        4. 添加创建者为管理员
        5. 返回群组信息
    """
    # Step 1-2: 生成 ID 和邀请码
    group_id = str(uuid.uuid4())
    invite_code = generate_random_code(length=8)
    
    # Step 3: 创建群组
    db.execute("""
        INSERT INTO family_groups (id, name, owner_id, invite_code)
        VALUES (?, ?, ?, ?)
    """, (group_id, name, owner_id, invite_code))
    
    # Step 4: 添加管理员
    db.execute("""
        INSERT INTO family_members (group_id, user_id, name, role)
        VALUES (?, ?, ?, 'owner')
    """, (group_id, owner_id, owner_id))
    
    db.commit()
    
    return {
        "success": True,
        "group_id": group_id,
        "invite_code": invite_code
    }
```

### 8.3 健康数据同步流程

```python
async def sync_watch_data(device_id: str, user_id: str, data: Dict):
    """
    同步流程:
        1. 验证设备类型
        2. 插入健康数据
        3. 更新设备状态
        4. 触发异常检测
        5. 返回结果
    """
    # Step 1: 验证设备
    device = get_device(device_id)
    if device.type != "smart_watch":
        raise Error("设备类型不匹配")
    
    # Step 2: 插入数据
    db.execute("""
        INSERT INTO watch_data 
        (device_id, user_id, timestamp, heart_rate, steps, sleep_duration)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (device_id, user_id, datetime.now(), 
          data.heart_rate, data.steps, data.sleep_duration))
    
    # Step 3: 更新设备状态
    db.execute("""
        UPDATE hardware_devices 
        SET last_sync = ?, status = 'online'
        WHERE id = ?
    """, (datetime.now(), device_id))
    
    db.commit()
    
    # Step 4: 异常检测
    anomalies = await detect_health_anomalies(user_id)
    if anomalies:
        await send_anomaly_alerts(user_id, anomalies)
    
    return {"success": True, "anomalies": anomalies}
```

---

## 附录

### A. 命令行工具

```bash
# 启动后端
cd backend
python main.py

# 测试 API
curl http://localhost:8082/health

# 构建 Windows 客户端
cd windows-desktop/OpenClaw.Desktop
dotnet build
dotnet run

# 打包发布
dotnet publish -c Release -r win-x64 --self-contained
```

### B. 环境变量

```bash
# 后端配置
DASHSCOPE_API_KEY=sk-xxx        # 阿里云 API Key
DATABASE_URL=sqlite:///data/db  # 数据库路径
DEBUG=true                       # 调试模式

# Windows 客户端配置
API_BASE_URL=http://localhost:8082  # API 地址
```

### C. 常见问题

**Q1: 语音识别不准确？**
- 检查麦克风权限
- 说话清晰，避免噪音
- 尝试使用标准普通话

**Q2: 设备连接失败？**
- 确认蓝牙已开启
- 检查设备电量
- 重新扫描并配对

**Q3: 数据同步延迟？**
- 检查网络连接
- 确认后端服务运行中
- 查看设备在线状态

---

**文档版本**: v1.0  
**最后更新**: 2026-03-19