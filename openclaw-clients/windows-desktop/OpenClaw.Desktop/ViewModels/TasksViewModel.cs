using System.Collections.ObjectModel;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;

namespace OpenClaw.Desktop.ViewModels;

public partial class TasksViewModel : BaseViewModel
{
    public ObservableCollection<TaskItem> Tasks { get; }

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(AddTaskCommand))]
    private string _newTaskText = string.Empty;

    public IRelayCommand AddTaskCommand { get; }
    public IRelayCommand<TaskItem> ToggleTaskCommand { get; }
    public IRelayCommand<TaskItem> DeleteTaskCommand { get; }

    public TasksViewModel()
    {
        Tasks = new ObservableCollection<TaskItem>();
        AddTaskCommand = new RelayCommand(AddTask, () => !string.IsNullOrWhiteSpace(NewTaskText));
        ToggleTaskCommand = new RelayCommand<TaskItem>(ToggleTask);
        DeleteTaskCommand = new RelayCommand<TaskItem>(DeleteTask);

        Tasks.Add(new TaskItem { Title = "完成WPF项目设置", IsCompleted = true });
        Tasks.Add(new TaskItem { Title = "添加Material Design样式", IsCompleted = true });
        Tasks.Add(new TaskItem { Title = "实现MVVM模式", IsCompleted = false });
    }

    private void AddTask()
    {
        if (string.IsNullOrWhiteSpace(NewTaskText)) return;
        Tasks.Add(new TaskItem { Title = NewTaskText, IsCompleted = false });
        NewTaskText = string.Empty;
    }

    private void ToggleTask(TaskItem? task)
    {
        if (task != null)
            task.IsCompleted = !task.IsCompleted;
    }

    private void DeleteTask(TaskItem? task)
    {
        if (task != null)
            Tasks.Remove(task);
    }
}

public partial class TaskItem : ObservableObject
{
    [ObservableProperty]
    private string _title = string.Empty;

    [ObservableProperty]
    private bool _isCompleted;
}