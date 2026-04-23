using System.Collections.ObjectModel;
using System.Windows.Controls;
using System.Windows.Input;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Microsoft.Extensions.DependencyInjection;
using OpenClaw.Desktop.Views;

namespace OpenClaw.Desktop.ViewModels;

public partial class MainViewModel : BaseViewModel
{
    [ObservableProperty]
    private UserControl? _currentView;

    [ObservableProperty]
    private string _currentViewTitle = "首页";

    [ObservableProperty]
    private MenuItem? _selectedMenuItem;

    private readonly HomeViewModel _homeViewModel;
    private readonly VoiceControlViewModel _voiceControlViewModel;
    private readonly FamilyGroupViewModel _familyGroupViewModel;
    private readonly HardwareViewModel _hardwareViewModel;
    private readonly AnalyticsViewModel _analyticsViewModel;
    private readonly HealthViewModel _healthViewModel;
    private readonly FinanceViewModel _financeViewModel;
    private readonly TasksViewModel _tasksViewModel;
    private readonly SettingsViewModel _settingsViewModel;
    private readonly Services.TrayService? _trayService;

    public ObservableCollection<MenuItem> MenuItems { get; }

    public ICommand NavigateToSettingsCommand { get; }
    public ICommand MinimizeToTrayCommand { get; }

    public MainViewModel() : this(null!, null!, null!, null!, null!, null!, null!, null!, null!, null!) { }

    public MainViewModel(
        HomeViewModel homeViewModel,
        VoiceControlViewModel voiceControlViewModel,
        FamilyGroupViewModel familyGroupViewModel,
        HardwareViewModel hardwareViewModel,
        AnalyticsViewModel analyticsViewModel,
        HealthViewModel healthViewModel,
        FinanceViewModel financeViewModel,
        TasksViewModel tasksViewModel,
        SettingsViewModel settingsViewModel,
        Services.TrayService? trayService)
    {
        _homeViewModel = homeViewModel;
        _voiceControlViewModel = voiceControlViewModel;
        _familyGroupViewModel = familyGroupViewModel;
        _hardwareViewModel = hardwareViewModel;
        _analyticsViewModel = analyticsViewModel;
        _healthViewModel = healthViewModel;
        _financeViewModel = financeViewModel;
        _tasksViewModel = tasksViewModel;
        _settingsViewModel = settingsViewModel;
        _trayService = trayService;

        MenuItems = new ObservableCollection<MenuItem>
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

        _selectedMenuItem = MenuItems[0];
        NavigateToView(_selectedMenuItem);

        _homeViewModel.NavigateRequested += (s, e) =>
        {
            var menuItem = MenuItems.FirstOrDefault(m => m.ViewType == e.ViewType);
            if (menuItem != null)
                SelectedMenuItem = menuItem;
        };

        NavigateToSettingsCommand = new RelayCommand(() =>
        {
            SelectedMenuItem = MenuItems.FirstOrDefault(m => m.ViewType == "Settings")!;
        });

        MinimizeToTrayCommand = new RelayCommand(() =>
        {
            _trayService?.MinimizeToTray();
        });
    }

    partial void OnSelectedMenuItemChanged(MenuItem? value)
    {
        if (value != null)
        {
            CurrentViewTitle = value.Title;
            NavigateToView(value);
        }
    }

    private void NavigateToView(MenuItem item)
    {
        CurrentView = item.ViewType switch
        {
            "Home" => App.ServiceProvider.GetRequiredService<HomeView>(),
            "VoiceControl" => App.ServiceProvider.GetRequiredService<VoiceControlView>(),
            "FamilyGroup" => App.ServiceProvider.GetRequiredService<FamilyGroupView>(),
            "Hardware" => App.ServiceProvider.GetRequiredService<HardwareView>(),
            "Analytics" => App.ServiceProvider.GetRequiredService<AnalyticsView>(),
            "Health" => App.ServiceProvider.GetRequiredService<HealthView>(),
            "Finance" => App.ServiceProvider.GetRequiredService<FinanceView>(),
            "Tasks" => App.ServiceProvider.GetRequiredService<TasksView>(),
            "Settings" => App.ServiceProvider.GetRequiredService<SettingsView>(),
            _ => CurrentView
        };
    }
}

public class MenuItem
{
    public string Title { get; set; } = string.Empty;
    public string Icon { get; set; } = string.Empty;
    public string ViewType { get; set; } = string.Empty;
}