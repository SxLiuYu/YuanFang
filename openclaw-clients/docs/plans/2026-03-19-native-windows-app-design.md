# 原生 Windows 应用 + 新功能设计文档

**日期**: 2026-03-19  
**版本**: v1.0  
**技术栈**: WPF (.NET 8) + FastAPI (后端)  
**开发模式**: Windows 客户端 + 后端 API 扩展并行开发

---

## 一、项目背景

### 1.1 现状分析

**已有客户端**:
- ✅ Electron Desktop: 跨平台，基础功能（AI 对话、语音）
- ✅ Flutter Mobile: 完整功能，Android/iOS
- ✅ Web: 浏览器基础功能
- ✅ CLI: 命令行测试工具

**已完成功能**:
- 第一批: 智能提醒、生物识别锁、数据导出
- 第二批: 通知监听、自然语言记账、桌面小组件
- 第三批: 语音交互、场景自动化、智能家居

**测试覆盖**: 39 个测试用例全部通过  
**API 端点**: 150+

### 1.2 需求

1. **创建原生 Windows 应用**（WPF .NET 8）
2. **新增四大功能模块**：
   - 语音完全控制 + 智能建议
   - 家庭群组协作
   - 硬件集成（智能手表、智能音箱、健康设备）
   - 高级分析报告
3. **同时开发**：Windows 客户端 + 后端 API 扩展

---

## 二、技术架构

### 2.1 Windows 客户端架构

**技术选型**:
- UI 框架: WPF (.NET 8)
- MVVM 框架: CommunityToolkit.Mvvm
- UI 组件库: MaterialDesignThemes 5.0
- 图表库: LiveChartsCore.SkiaSharpView.WPF
- HTTP 客户端: RestSharp
- 数据库: SQLite (Microsoft.Data.Sqlite)
- Windows 集成: Windows SDK Contracts

**项目结构**:
```
OpenClaw.Desktop/
├── Core/
│   ├── AppConfiguration.cs
│   ├── ServiceLocator.cs
│   └── Constants.cs
├── Services/
│   ├── Api/
│   │   ├── ApiClient.cs
│   │   ├── FamilyApiService.cs
│   │   ├── VoiceApiService.cs
│   │   ├── HardwareApiService.cs
│   │   └── AnalyticsApiService.cs
│   ├── Windows/
│   │   ├── TrayService.cs
│   │   ├── NotificationService.cs
│   │   ├── HotkeyService.cs
│   │   └── AutostartService.cs
│   ├── Hardware/
│   │   ├── BluetoothService.cs
│   │   ├── WatchService.cs
│   │   └── SpeakerService.cs
│   └── Voice/
│       ├── VoiceRecognitionService.cs
│       ├── VoiceCommandService.cs
│       └── TTSService.cs
├── ViewModels/
│   ├── MainViewModel.cs
│   ├── VoiceControlViewModel.cs
│   ├── FamilyGroupViewModel.cs
│   ├── HardwareViewModel.cs
│   └── AnalyticsViewModel.cs
├── Views/
│   ├── VoiceControlView.xaml
│   ├── FamilyGroupView.xaml
│   ├── HardwareView.xaml
│   └── AnalyticsView.xaml
├── Models/
│   ├── FamilyModels.cs
│   ├── VoiceModels.cs
│   ├── HardwareModels.cs
│   └── AnalyticsModels.cs
└── Resources/
    └── Icons/
```

### 2.2 后端 API 扩展

**新增 4 个服务模块**:

**1. 家庭协作服务** (`backend/services/family_service.py`)
- 群组管理
- 成员管理
- 位置共享
- 共享日历

**2. 语音增强服务** (`backend/services/voice_enhanced_service.py`)
- 设备控制命令
- 场景控制命令
- 智能建议引擎
- 自然语言日程解析

**3. 硬件集成服务** (`backend/services/hardware_service.py`)
- 设备抽象层
- 智能手表数据接收
- 智能音箱回调
- 蓝牙设备管理

**4. 高级分析服务** (`backend/services/analytics_service.py`)
- 健康评分算法
- 消费洞察分析
- 异常检测引擎
- 报告生成

**API 端点**:

**家庭协作 API** (`/api/v1/family/`):
```
POST   /family/groups                    # 创建家庭群组
GET    /family/groups/{id}               # 获取群组详情
POST   /family/groups/{id}/members       # 添加成员
DELETE /family/groups/{id}/members/{uid} # 移除成员
POST   /family/location/share            # 分享位置
GET    /family/location/members          # 获取成员位置
POST   /family/calendar/shared           # 创建共享日程
GET    /family/calendar/shared           # 获取共享日程
```

**语音控制 API** (`/api/v1/voice/`):
```
POST   /voice/control/device            # 设备控制
POST   /voice/control/scene             # 场景控制
GET    /voice/suggestions               # 智能建议
POST   /voice/schedule/parse            # 自然语言日程解析
```

**硬件集成 API** (`/api/v1/hardware/`):
```
GET    /hardware/devices                 # 获取设备列表
POST   /hardware/devices/watch/sync      # 智能手表数据同步
POST   /hardware/devices/speaker/command # 智能音箱命令
GET    /hardware/bluetooth/scan          # 蓝牙设备扫描
POST   /hardware/bluetooth/pair          # 蓝牙配对
```

**高级分析 API** (`/api/v1/analytics/`):
```
GET    /analytics/health/score           # 健康评分
GET    /analytics/finance/insights       # 消费洞察
GET    /analytics/anomalies              # 异常预警
GET    /analytics/report/weekly          # 周报
GET    /analytics/report/monthly         # 月报
```

---

## 三、功能模块设计

### 3.1 Phase 1: 语音完全控制 + 智能建议（2 周）

#### 3.1.1 后端实现

**文件**: `backend/services/voice_enhanced_service.py`

**核心功能**:
1. **设备控制命令扩展**
   - 支持自然语言控制智能家居
   - 示例: "打开客厅的灯"、"空调调到 26 度"
   - 意图识别 + 槽位提取 + 设备匹配

2. **场景控制命令**
   - 支持语音触发预设场景
   - 示例: "我要睡觉了"、"我出门了"
   - 场景模板库 + 自动执行

3. **智能建议引擎**
   - 基于用户历史行为生成建议
   - 时间/位置/习惯分析
   - 个性化推荐

4. **自然语言日程解析**
   - 示例: "明天下午 3 点开会"、"每周一早上 9 点例会"
   - 时间实体识别 + 日程创建

**数据模型**:
```python
class VoiceCommand(BaseModel):
    text: str
    context: Optional[Dict[str, Any]] = None
    device_id: Optional[str] = None
    
class VoiceSuggestion(BaseModel):
    type: str  # "device", "scene", "reminder", "habit"
    title: str
    description: str
    confidence: float
    action: Dict[str, Any]
```

#### 3.1.2 Windows 客户端实现

**文件**: 
- `ViewModels/VoiceControlViewModel.cs`
- `Views/VoiceControlView.xaml`
- `Services/Voice/VoiceRecognitionService.cs`
- `Services/Voice/VoiceCommandService.cs`

**核心功能**:
1. **全局热键唤醒**
   - 注册 Windows 全局热键（如 Win+V）
   - 系统托盘常驻
   - 快速唤醒语音交互

2. **语音反馈动画 UI**
   - MaterialDesign 风格
   - 声波动画
   - 实时文本显示

3. **智能建议卡片**
   - 卡片式布局
   - 一键执行建议
   - 学习用户偏好

**XAML 设计**:
```xml
<!-- VoiceControlView.xaml -->
<UserControl>
    <Grid>
        <!-- 声波动画区域 -->
        <Grid.Row="0">
            <lvc:CartesianChart Series="{Binding WaveSeries}" />
        </Grid>
        
        <!-- 识别文本显示 -->
        <Grid.Row="1">
            <TextBlock Text="{Binding RecognizedText}" />
        </Grid.Row>
        
        <!-- 智能建议卡片 -->
        <Grid.Row="2">
            <ItemsControl ItemsSource="{Binding Suggestions}">
                <DataTemplate>
                    <materialDesign:Card>
                        <StackPanel>
                            <TextBlock Text="{Binding Title}" />
                            <TextBlock Text="{Binding Description}" />
                            <Button Command="{Binding ExecuteCommand}" />
                        </StackPanel>
                    </materialDesign:Card>
                </DataTemplate>
            </ItemsControl>
        </Grid.Row>
    </Grid>
</UserControl>
```

### 3.2 Phase 2: 家庭群组协作（1.5 周）

#### 3.2.1 后端实现

**文件**: `backend/services/family_service.py`

**核心功能**:
1. **家庭群组管理**
   - 创建/加入群组
   - 成员角色（管理员/普通成员）
   - 邀请码机制

2. **位置共享**
   - 实时位置上报
   - 位置历史记录
   - 地理围栏通知

3. **共享日历**
   - 家庭日程创建
   - 分配任务给成员
   - 提醒通知

**数据模型**:
```python
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
    role: str  # "owner", "admin", "member"
    location: Optional[Location]
    
class Location(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime
    address: Optional[str]
```

#### 3.2.2 Windows 客户端实现

**文件**:
- `ViewModels/FamilyGroupViewModel.cs`
- `Views/FamilyGroupView.xaml`

**核心功能**:
1. **成员列表展示**
   - 头像 + 在线状态
   - 位置信息
   - 快速操作按钮

2. **位置地图展示**
   - 使用 Bing Maps SDK
   - 实时位置标注
   - 路线规划

3. **共享日历组件**
   - 月/周/日视图
   - 拖拽创建日程
   - 颜色分类

### 3.3 Phase 3: 硬件集成（2 周）

#### 3.3.1 后端实现

**文件**: `backend/services/hardware_service.py`

**核心功能**:
1. **设备抽象层**
   - 统一设备接口
   - 设备类型枚举（watch, speaker, health_device）
   - 设备状态管理

2. **智能手表数据同步**
   - 接收健康数据（心率、步数、睡眠）
   - 数据存储与分析
   - 异常检测

3. **智能音箱回调**
   - 设备注册
   - 语音命令回调
   - 设备状态推送

**数据模型**:
```python
class HardwareDevice(BaseModel):
    id: str
    name: str
    type: str  # "smart_watch", "smart_speaker", "health_device"
    status: str  # "online", "offline", "pairing"
    last_sync: datetime
    metadata: Dict[str, Any]
    
class WatchData(BaseModel):
    user_id: str
    device_id: str
    timestamp: datetime
    heart_rate: Optional[int]
    steps: Optional[int]
    sleep_duration: Optional[int]
    calories: Optional[int]
```

#### 3.3.2 Windows 客户端实现

**文件**:
- `ViewModels/HardwareViewModel.cs`
- `Views/HardwareView.xaml`
- `Services/Hardware/BluetoothService.cs`

**核心功能**:
1. **蓝牙设备管理**
   - 使用 Windows Bluetooth API
   - 设备扫描与配对
   - 连接状态管理

2. **设备状态监控**
   - 实时数据展示
   - 电量/连接状态
   - 异常告警

3. **数据同步**
   - 手动/自动同步
   - 数据可视化
   - 导出功能

### 3.4 Phase 4: 高级分析报告（1.5 周）

#### 3.4.1 后端实现

**文件**: `backend/services/analytics_service.py`

**核心功能**:
1. **健康评分算法**
   - 基于多维度数据（睡眠、运动、心率）
   - 权重动态调整
   - 历史趋势分析

2. **消费洞察分析**
   - 消费分类统计
   - 异常消费检测
   - 预算建议

3. **异常预警**
   - 数据异常检测（健康、财务）
   - 阈值告警
   - 趋势预警

**算法示例**:
```python
def calculate_health_score(user_id: str) -> float:
    """计算健康评分（0-100）"""
    # 获取最近 7 天数据
    health_data = get_health_data(user_id, days=7)
    
    # 睡眠评分（权重 30%）
    sleep_score = calculate_sleep_score(health_data.sleep) * 0.3
    
    # 运动评分（权重 40%）
    exercise_score = calculate_exercise_score(health_data.steps) * 0.4
    
    # 心率评分（权重 30%）
    heart_rate_score = calculate_heart_rate_score(health_data.heart_rate) * 0.3
    
    return sleep_score + exercise_score + heart_rate_score
```

#### 3.4.2 Windows 客户端实现

**文件**:
- `ViewModels/AnalyticsViewModel.cs`
- `Views/AnalyticsView.xaml`

**核心功能**:
1. **数据可视化图表**
   - LiveCharts2 图表库
   - 折线图、柱状图、饼图
   - 动态更新

2. **报告导出**
   - PDF 导出
   - Excel 导出
   - 邮件发送

3. **仪表盘设计**
   - 健康评分仪表盘
   - 消费趋势图
   - 异常预警列表

---

## 四、技术实现细节

### 4.1 Windows 特有功能集成

#### 4.1.1 系统托盘

**实现方案**:
- 使用 `Hardcodet.NotifyIcon.Wpf` 库
- 托盘图标 + 右键菜单
- 双击唤醒主窗口
- 后台常驻运行

**代码示例**:
```csharp
public class TrayService
{
    private readonly TaskbarIcon _notifyIcon;
    
    public TrayService()
    {
        _notifyIcon = new TaskbarIcon
        {
            Icon = new Icon("Resources/Icons/app.ico"),
            ToolTipText = "OpenClaw 家庭助手",
            ContextMenu = CreateContextMenu()
        };
        
        _notifyIcon.DoubleClick += (s, e) => ShowMainWindow();
    }
}
```

#### 4.1.2 全局热键

**实现方案**:
- 使用 Windows API `RegisterHotKey`
- 全局监听热键组合
- 唤醒语音交互

**代码示例**:
```csharp
public class HotkeyService
{
    [DllImport("user32.dll")]
    private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);
    
    public void RegisterGlobalHotKey(Key key, ModifierKeys modifiers)
    {
        var hwnd = new WindowInteropHelper(Application.Current.MainWindow).Handle;
        RegisterHotKey(hwnd, HOTKEY_ID, (uint)modifiers, (uint)KeyInterop.VirtualKeyFromKey(key));
    }
}
```

#### 4.1.3 Windows 通知

**实现方案**:
- 使用 Windows SDK `ToastNotification`
- 支持按钮、图片、输入框
- 通知点击回调

**代码示例**:
```csharp
public class NotificationService
{
    public void ShowNotification(string title, string content, string imageUrl = null)
    {
        var toastContent = new ToastContentBuilder()
            .AddText(title)
            .AddText(content)
            .AddAppLogoOverride(new Uri(imageUrl))
            .AddButton("查看详情", ToastActivationType.Foreground, "action=view")
            .GetToastContent();
        
        var toast = new ToastNotification(toastContent.GetXml());
        ToastNotificationManager.CreateToastNotifier().Show(toast);
    }
}
```

#### 4.1.4 蓝牙设备管理

**实现方案**:
- 使用 `Windows.Devices.Bluetooth` API
- 设备扫描、配对、连接
- GATT 服务通信

**代码示例**:
```csharp
public class BluetoothService
{
    private BluetoothLEDevice _device;
    
    public async Task<List<BluetoothDevice>> ScanDevicesAsync()
    {
        var selector = BluetoothLEDevice.GetDeviceSelector();
        var devices = await DeviceInformation.FindAllAsync(selector);
        
        return devices.Select(d => new BluetoothDevice
        {
            Id = d.Id,
            Name = d.Name,
            IsConnected = d.Pairing.IsPaired
        }).ToList();
    }
    
    public async Task<bool> PairDeviceAsync(string deviceId)
    {
        _device = await BluetoothLEDevice.FromIdAsync(deviceId);
        var result = await _device.Pairing.PairAsync();
        return result.Status == DevicePairingResultStatus.Paired;
    }
}
```

### 4.2 数据库设计

#### 4.2.1 本地数据库（SQLite）

**表结构**:

**家庭群组表**:
```sql
CREATE TABLE family_groups (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    owner_id TEXT NOT NULL,
    invite_code TEXT UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE family_members (
    group_id TEXT,
    user_id TEXT,
    name TEXT,
    role TEXT,
    FOREIGN KEY (group_id) REFERENCES family_groups(id),
    PRIMARY KEY (group_id, user_id)
);
```

**硬件设备表**:
```sql
CREATE TABLE hardware_devices (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    status TEXT,
    last_sync DATETIME,
    metadata TEXT
);
```

**分析数据缓存表**:
```sql
CREATE TABLE analytics_cache (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    data TEXT,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 五、测试策略

### 5.1 单元测试

**后端**:
- 每个服务模块独立测试
- Mock 外部依赖（API、数据库）
- 测试覆盖率 > 80%

**Windows 客户端**:
- ViewModel 单元测试（使用 xUnit）
- 服务层测试
- MVVM 绑定测试

### 5.2 集成测试

**后端**:
- API 端点集成测试
- 数据库集成测试
- 外部服务集成测试

**Windows 客户端**:
- API 集成测试
- 数据库集成测试
- Windows 特有功能测试（托盘、热键、通知）

### 5.3 端到端测试

**场景 1: 语音控制流程**
1. 用户按下热键 Win+V
2. 语音输入 "打开客厅的灯"
3. 系统识别并执行
4. 设备状态更新

**场景 2: 家庭协作流程**
1. 用户创建家庭群组
2. 成员加入群组
3. 共享位置
4. 创建共享日程

---

## 六、部署与发布

### 6.1 后端部署

**方案 1: Docker 部署**
```bash
cd backend
docker build -t openclaw-backend .
docker run -d -p 8082:8082 openclaw-backend
```

**方案 2: 直接部署**
```bash
cd backend
pip install -r requirements.txt
python main.py
```

### 6.2 Windows 客户端打包

**使用 MSIX 打包**:
1. 配置打包项目
2. 生成 MSIX 安装包
3. 发布到 Microsoft Store 或独立分发

**命令行打包**:
```bash
dotnet publish -c Release -r win-x64 --self-contained
```

---

## 七、开发计划

### 7.1 时间线

| 阶段 | 功能模块 | 时间 | 交付物 |
|------|---------|------|--------|
| Phase 1 | 语音完全控制 + 智能建议 | 2 周 | 后端服务 + Windows 客户端视图 |
| Phase 2 | 家庭群组协作 | 1.5 周 | 后端服务 + Windows 客户端视图 |
| Phase 3 | 硬件集成 | 2 周 | 后端服务 + Windows 客户端视图 |
| Phase 4 | 高级分析报告 | 1.5 周 | 后端服务 + Windows 客户端视图 |
| **总计** | **全部功能** | **7 周** | **完整原生 Windows 应用** |

### 7.2 里程碑

- **Week 2**: Phase 1 完成，可演示语音控制
- **Week 3.5**: Phase 2 完成，可演示家庭协作
- **Week 5.5**: Phase 3 完成，可演示硬件集成
- **Week 7**: Phase 4 完成，全部功能集成测试

---

## 八、风险与应对

### 8.1 技术风险

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| Windows API 兼容性问题 | 中 | 使用 Windows SDK 最新版本，兼容 Win10/11 |
| 蓝牙设备兼容性 | 中 | 提供设备白名单，主流设备优先支持 |
| 语音识别准确率 | 低 | 使用成熟 API，添加纠错机制 |

### 8.2 进度风险

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 后端 API 扩展延迟 | 高 | 优先实现核心功能，次要功能可延后 |
| Windows 特有功能调试 | 中 | 预留调试时间，建立调试日志系统 |
| 跨团队协作问题 | 中 | 使用 API 文档统一接口定义 |

---

## 九、验收标准

### 9.1 功能验收

- ✅ 语音控制成功执行率 > 95%
- ✅ 智能建议点击率 > 30%
- ✅ 家庭群组创建成功率 100%
- ✅ 硬件设备连接成功率 > 90%
- ✅ 分析报告生成成功率 100%

### 9.2 性能验收

- ✅ 应用启动时间 < 3 秒
- ✅ 语音识别响应时间 < 2 秒
- ✅ API 请求响应时间 < 500ms
- ✅ 内存占用 < 200MB
- ✅ CPU 占用 < 5%（空闲状态）

### 9.3 用户体验验收

- ✅ MaterialDesign 设计规范
- ✅ 支持深色/浅色主题
- ✅ 支持窗口缩放
- ✅ 支持键盘快捷键
- ✅ 支持系统托盘常驻

---

**设计完成！准备开始实现。**