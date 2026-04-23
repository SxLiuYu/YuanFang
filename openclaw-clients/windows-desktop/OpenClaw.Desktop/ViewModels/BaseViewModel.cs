using CommunityToolkit.Mvvm.ComponentModel;

namespace OpenClaw.Desktop.ViewModels;

public partial class BaseViewModel : ObservableObject
{
    [ObservableProperty]
    private bool _isLoading;

    [ObservableProperty]
    private string _statusMessage = string.Empty;
}