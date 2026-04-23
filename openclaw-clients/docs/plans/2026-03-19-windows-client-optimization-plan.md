# Windows 客户端优化实施计划

**日期**: 2026-03-19  
**状态**: 待执行  
**预计时间**: 2 小时

---

## 一、优化目标

完善原生 Windows 应用（WPF .NET 8），补全缺失的视图文件，更新依赖注入配置，确保所有 4 个新功能模块可用。

---

## 二、需要创建的文件

### 2.1 硬件集成模块

**文件列表**：

1. **ViewModels/HardwareViewModel.cs**
   - 功能：设备管理、蓝牙扫描、健康数据展示
   - 主要属性：
     - `ObservableCollection<HardwareDevice> Devices` - 设备列表
     - `ObservableCollection<BluetoothDevice> ScannedDevices` - 扫描到的蓝牙设备
     - `HealthSummary? HealthSummary` - 健康数据摘要
   - 主要命令：
     - `LoadDevicesCommand` - 加载设备列表
     - `ScanBluetoothCommand` - 扫描蓝牙设备
     - `PairDeviceCommand` - 配对蓝牙设备
     - `ControlDeviceCommand` - 控制设备

2. **Views/HardwareView.xaml**
   - 布局：左侧设备列表，右侧健康数据仪表盘
   - 组件：
     - 设备列表 ListView
     - 健康数据卡片（心率、步数、睡眠、卡路里）
     - 蓝牙扫描按钮和结果列表
     - 设备控制面板

3. **Views/HardwareView.xaml.cs**
   - 代码后置文件，初始化组件

### 2.2 高级分析模块

**文件列表**：

1. **ViewModels/AnalyticsViewModel.cs**
   - 功能：健康评分、消费洞察、异常预警、报告生成
   - 主要属性：
     - `double HealthScore` - 健康评分（0-100）
     - `FinanceInsight? FinanceInsight` - 消费洞察
     - `ObservableCollection<Anomaly> Anomalies` - 异常列表
   - 主要命令：
     - `RefreshHealthScoreCommand` - 刷新健康评分
     - `GetFinanceInsightsCommand` - 获取消费洞察
     - `CheckAnomaliesCommand` - 检测异常
     - `GenerateReportCommand` - 生成报告

2. **Views/AnalyticsView.xaml**
   - 布局：标签页式（健康评分、消费洞察、异常预警、报告）
   - 组件：
     - 健康评分仪表盘（LiveCharts2 圆形进度条）
     - 消费图表（饼图、柱状图）
     - 异常列表
     - 报告导出按钮

3. **Views/AnalyticsView.xaml.cs**
   - 代码后置文件，初始化组件

### 2.3 模型文件

**Models/AnalyticsModels.cs**：
- `HealthScore` - 健康评分模型
- `FinanceInsight` - 消费洞察模型
- `Anomaly` - 异常预警模型
- `Report` - 报告模型

### 2.4 转换器

**Converters/BoolToVisibilityConverter.cs**：
- 将布尔值转换为 Visibility 枚举

**Converters/RoleToVisibilityConverter.cs**：
- 根据成员角色控制按钮可见性

---

## 三、需要修改的文件

### 3.1 App.xaml.cs

**修改内容**：更新依赖注入配置

```csharp
private void ConfigureServices(IServiceCollection services)
{
    // 注册 API 客户端
    services.AddSingleton<ApiClient>();
    
    // 注册 API 服务
    services.AddSingleton<VoiceApiService>();
    services.AddSingleton<FamilyApiService>();
    services.AddSingleton<HardwareApiService>();
    
    // 注册服务
    services.AddSingleton<VoiceService>();
    services.AddSingleton<TrayService>();
    services.AddSingleton<VoiceRecognitionService>();
    services.AddSingleton<TTSService>();
    
    // 注册 ViewModel
    services.AddSingleton<MainViewModel>();
    services.AddSingleton<VoiceControlViewModel>();
    services.AddSingleton<FamilyGroupViewModel>();
    services.AddSingleton<HardwareViewModel>();
    services.AddSingleton<AnalyticsViewModel>();
    services.AddSingleton<HealthViewModel>();
    services.AddSingleton<FinanceViewModel>();
    
    // 注册视图
    services.AddTransient<VoiceControlView>();
    services.AddTransient<FamilyGroupView>();
    services.AddTransient<HardwareView>();
    services.AddTransient<AnalyticsView>();
    
    // 注册主窗口
    services.AddSingleton<MainWindow>();
}
```

### 3.2 ViewModels/MainViewModel.cs

**修改内容**：添加新的菜单项和导航逻辑

```csharp
public partial class MainViewModel : BaseViewModel
{
    [ObservableProperty]
    private UserControl? _currentView;

    [ObservableProperty]
    private string _currentViewTitle = "首页";

    public ObservableCollection<MenuItem> MenuItems { get; } = new()
    {
        new MenuItem { Title = "首页", Icon = "Home", ViewType = "Home" },
        new MenuItem { Title = "语音控制", Icon = "Microphone", ViewType = "VoiceControl" },
        new MenuItem { Title = "家庭协作", Icon = "AccountGroup", ViewType = "FamilyGroup" },
        new MenuItem { Title = "硬件集成", Icon = "Watch", ViewType = "Hardware" },
        new MenuItem { Title = "数据分析", Icon = "ChartLine", ViewType = "Analytics" },
        new MenuItem { Title = "健康管理", Icon = "Heart", ViewType = "Health" },
        new MenuItem { Title = "财务管理", Icon = "CurrencyCny", ViewType = "Finance" },
        new MenuItem { Title = "任务管理", Icon = "CheckCircle", ViewType = "Tasks" },
        new MenuItem { Title = "设置", Icon = "Settings", ViewType = "Settings" }
    };

    [ObservableProperty]
    private MenuItem? _selectedMenuItem;

    partial void OnSelectedMenuItemChanged(MenuItem? value)
    {
        if (value != null)
        {
            CurrentViewTitle = value.Title;
            CurrentView = value.ViewType switch
            {
                "VoiceControl" => App.ServiceProvider.GetRequiredService<VoiceControlView>(),
                "FamilyGroup" => App.ServiceProvider.GetRequiredService<FamilyGroupView>(),
                "Hardware" => App.ServiceProvider.GetRequiredService<HardwareView>(),
                "Analytics" => App.ServiceProvider.GetRequiredService<AnalyticsView>(),
                // ... 其他视图
                _ => null
            };
        }
    }
}

public class MenuItem
{
    public string Title { get; set; } = "";
    public string Icon { get; set; } = "";
    public string ViewType { get; set; } = "";
}
```

### 3.3 MainWindow.xaml

**修改内容**：确保菜单项正确绑定（通常无需修改，因为已绑定到 MenuItems）

---

## 四、实施步骤

### Step 1: 创建 Models

1. 创建 `Models/AnalyticsModels.cs`
2. 定义所有分析相关模型

### Step 2: 创建 Converters

1. 创建 `Converters/` 目录
2. 创建 `BoolToVisibilityConverter.cs`
3. 创建 `RoleToVisibilityConverter.cs`

### Step 3: 创建 ViewModels

1. 创建 `ViewModels/HardwareViewModel.cs`
2. 创建 `ViewModels/AnalyticsViewModel.cs`

### Step 4: 创建 Views

1. 创建 `Views/HardwareView.xaml` 和 `.xaml.cs`
2. 创建 `Views/AnalyticsView.xaml` 和 `.xaml.cs`

### Step 5: 更新依赖注入

1. 修改 `App.xaml.cs`，注册所有新服务

### Step 6: 更新导航

1. 修改 `ViewModels/MainViewModel.cs`，添加菜单项和导航逻辑

### Step 7: 测试验证

1. 启动后端服务：`cd backend && python main.py`
2. 构建并运行 Windows 客户端
3. 验证所有视图可正常导航
4. 验证 API 调用正常

---

## 五、验收标准

### 5.1 功能验收

- [ ] 主窗口显示所有 9 个菜单项
- [ ] 点击"语音控制"可导航到 VoiceControlView
- [ ] 点击"家庭协作"可导航到 FamilyGroupView
- [ ] 点击"硬件集成"可导航到 HardwareView
- [ ] 点击"数据分析"可导航到 AnalyticsView
- [ ] 所有视图可正常加载和显示数据

### 5.2 代码质量

- [ ] 所有新增文件无编译错误
- [ ] ViewModel 使用 CommunityToolkit.Mvvm 的 ObservableProperty
- [ ] API 调用有错误处理
- [ ] UI 使用 MaterialDesign 组件

### 5.3 性能

- [ ] 视图切换流畅（< 500ms）
- [ ] API 请求响应正常（< 1s）
- [ ] 无内存泄漏

---

## 六、风险与应对

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| API 服务未启动 | 高 | 添加连接检查和错误提示 |
| 视图加载失败 | 中 | 添加 try-catch 和默认值 |
| 数据绑定错误 | 中 | 使用 F12 调试工具检查 |

---

## 七、后续优化建议

1. **添加单元测试**：为 ViewModel 编写 xUnit 测试
2. **添加加载动画**：在 API 请求时显示 Loading 指示器
3. **添加错误提示**：使用 MaterialDesign 的 Snackbar 显示错误
4. **优化响应式布局**：支持窗口缩放
5. **添加深色主题**：跟随系统主题切换

---

**计划完成！准备执行实施。**