using System;
using System.Collections.ObjectModel;
using System.Windows.Input;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace OpenClaw.Desktop.ViewModels;

public partial class HomeViewModel : BaseViewModel
{
    [ObservableProperty]
    private string _greeting = string.Empty;

    [ObservableProperty]
    private string _currentDate = string.Empty;

    [ObservableProperty]
    private string _userName = "用户";

    [ObservableProperty]
    private int _todaySteps;

    [ObservableProperty]
    private decimal _todayExpense;

    [ObservableProperty]
    private int _pendingTasks;

    [ObservableProperty]
    private int _completedTasks;

    public ObservableCollection<QuickAction> QuickActions { get; }
    public ObservableCollection<ActivityItem> RecentActivities { get; }

    public ICommand NavigateToVoiceCommand { get; }
    public ICommand NavigateToHealthCommand { get; }
    public ICommand NavigateToFinanceCommand { get; }
    public ICommand NavigateToTasksCommand { get; }

    public event EventHandler<NavigateEventArgs>? NavigateRequested;

    public HomeViewModel()
    {
        UpdateGreeting();
        
        QuickActions = new ObservableCollection<QuickAction>
        {
            new QuickAction { Title = "语音控制", Icon = "🎤", ViewType = "VoiceControl" },
            new QuickAction { Title = "健康管理", Icon = "❤️", ViewType = "Health" },
            new QuickAction { Title = "财务管理", Icon = "💰", ViewType = "Finance" },
            new QuickAction { Title = "任务管理", Icon = "✅", ViewType = "Tasks" }
        };

        RecentActivities = new ObservableCollection<ActivityItem>
        {
            new ActivityItem { Time = DateTime.Now.AddHours(-2), Description = "记录了一笔支出 - 午餐 ¥35" },
            new ActivityItem { Time = DateTime.Now.AddHours(-4), Description = "完成健康数据同步" },
            new ActivityItem { Time = DateTime.Now.AddDays(-1), Description = "添加了 3 个新任务" }
        };

        TodaySteps = 8234;
        TodayExpense = 1250.00m;
        PendingTasks = 5;
        CompletedTasks = 12;

        NavigateToVoiceCommand = new RelayCommand(() => NavigateTo("VoiceControl"));
        NavigateToHealthCommand = new RelayCommand(() => NavigateTo("Health"));
        NavigateToFinanceCommand = new RelayCommand(() => NavigateTo("Finance"));
        NavigateToTasksCommand = new RelayCommand(() => NavigateTo("Tasks"));
    }

    private void UpdateGreeting()
    {
        CurrentDate = DateTime.Now.ToString("yyyy年MM月dd日 dddd");
        
        var hour = DateTime.Now.Hour;
        Greeting = hour switch
        {
            >= 5 and < 12 => "早上好",
            >= 12 and < 14 => "中午好",
            >= 14 and < 18 => "下午好",
            _ => "晚上好"
        };
    }

    private void NavigateTo(string viewType)
    {
        NavigateRequested?.Invoke(this, new NavigateEventArgs { ViewType = viewType });
    }

    public void RefreshData()
    {
        UpdateGreeting();
        OnPropertyChanged(nameof(TodaySteps));
        OnPropertyChanged(nameof(TodayExpense));
        OnPropertyChanged(nameof(PendingTasks));
    }
}

public class QuickAction
{
    public string Title { get; set; } = string.Empty;
    public string Icon { get; set; } = string.Empty;
    public string ViewType { get; set; } = string.Empty;
}

public class ActivityItem
{
    public DateTime Time { get; set; }
    public string Description { get; set; } = string.Empty;

    public string TimeDisplay => Time switch
    {
        var t when (DateTime.Now - t).TotalMinutes < 60 => $"{(int)(DateTime.Now - t).TotalMinutes}分钟前",
        var t when (DateTime.Now - t).TotalHours < 24 => $"{(int)(DateTime.Now - t).TotalHours}小时前",
        var t when (DateTime.Now - t).TotalDays < 7 => $"{(int)(DateTime.Now - t).TotalDays}天前",
        _ => Time.ToString("MM-dd HH:mm")
    };
}

public class NavigateEventArgs : EventArgs
{
    public string ViewType { get; set; } = string.Empty;
}