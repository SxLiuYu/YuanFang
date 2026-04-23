using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using OpenClaw.Desktop.Services;
using OpenClaw.Desktop.Models;

namespace OpenClaw.Desktop.ViewModels;

public partial class SettingsViewModel : BaseViewModel
{
    private readonly ApiClient? _apiClient;
    private readonly ConfigService? _configService;

    [ObservableProperty]
    private bool _launchAtStartup = true;

    [ObservableProperty]
    private bool _minimizeToTray = true;

    [ObservableProperty]
    private bool _showNotifications = true;

    [ObservableProperty]
    private string _serverUrl = "http://localhost:8000";

    [ObservableProperty]
    private string _apiToken = "";

    [ObservableProperty]
    private bool _isLightTheme = true;

    [ObservableProperty]
    private bool _isDarkTheme;

    [ObservableProperty]
    private string _connectionStatus = "";

    [ObservableProperty]
    private bool _isConnected;

    [ObservableProperty]
    private bool _isTesting;

    [ObservableProperty]
    private string _userName = "用户";

    public IRelayCommand TestConnectionCommand { get; }
    public IRelayCommand ClearCacheCommand { get; }
    public IRelayCommand ExportDataCommand { get; }
    public IRelayCommand SaveCommand { get; }

    public SettingsViewModel() : this(null, null) { }

    public SettingsViewModel(ApiClient? apiClient, ConfigService? configService)
    {
        _apiClient = apiClient;
        _configService = configService;

        TestConnectionCommand = new AsyncRelayCommand(TestConnectionAsync, () => !IsTesting);
        ClearCacheCommand = new RelayCommand(ClearCache);
        ExportDataCommand = new RelayCommand(ExportData);
        SaveCommand = new RelayCommand(Save);

        LoadConfig();
    }

    private void LoadConfig()
    {
        if (_configService?.Config == null) return;

        var config = _configService.Config;
        LaunchAtStartup = config.LaunchAtStartup;
        MinimizeToTray = config.MinimizeToTray;
        ShowNotifications = config.ShowNotifications;
        ServerUrl = config.ServerUrl;
        ApiToken = config.ApiToken;
        IsLightTheme = config.Theme == "Light";
        IsDarkTheme = config.Theme == "Dark";
        UserName = config.UserName;
    }

    private void Save()
    {
        if (_configService?.Config == null) return;

        _configService.Config.LaunchAtStartup = LaunchAtStartup;
        _configService.Config.MinimizeToTray = MinimizeToTray;
        _configService.Config.ShowNotifications = ShowNotifications;
        _configService.Config.ServerUrl = ServerUrl;
        _configService.Config.ApiToken = ApiToken;
        _configService.Config.Theme = IsLightTheme ? "Light" : "Dark";
        _configService.Config.UserName = UserName;
        
        _configService.Save();
    }

    partial void OnIsLightThemeChanged(bool value)
    {
        if (value)
        {
            IsDarkTheme = false;
            Save();
        }
    }

    partial void OnIsDarkThemeChanged(bool value)
    {
        if (value)
        {
            IsLightTheme = false;
            Save();
        }
    }

    partial void OnLaunchAtStartupChanged(bool value) => Save();
    partial void OnMinimizeToTrayChanged(bool value) => Save();
    partial void OnShowNotificationsChanged(bool value) => Save();
    partial void OnServerUrlChanged(string value) { if (_configService != null) Save(); }
    partial void OnApiTokenChanged(string value) { if (_configService != null) Save(); }
    partial void OnUserNameChanged(string value) => Save();

    private async Task TestConnectionAsync()
    {
        if (_apiClient == null || IsTesting) return;

        IsTesting = true;
        ConnectionStatus = "Testing...";

        try
        {
            var result = await _apiClient.TestConnectionAsync();
            IsConnected = result;
            ConnectionStatus = result ? "Connected" : "Connection failed";
        }
        catch
        {
            IsConnected = false;
            ConnectionStatus = "Connection failed";
        }
        finally
        {
            IsTesting = false;
        }
    }

    private void ClearCache()
    {
        try
        {
            var cachePath = System.IO.Path.Combine(
                System.Environment.GetFolderPath(System.Environment.SpecialFolder.ApplicationData),
                "OpenClaw",
                "Cache");
            
            if (System.IO.Directory.Exists(cachePath))
            {
                System.IO.Directory.Delete(cachePath, true);
                System.IO.Directory.CreateDirectory(cachePath);
            }
            
            System.Windows.MessageBox.Show("Cache cleared successfully!", "Info", 
                System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
        }
        catch (System.Exception ex)
        {
            System.Windows.MessageBox.Show($"Failed to clear cache: {ex.Message}", "Error",
                System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Error);
        }
    }

    private void ExportData()
    {
        var dialog = new Microsoft.Win32.SaveFileDialog
        {
            Filter = "JSON files (*.json)|*.json",
            FileName = "openclaw_data_export.json"
        };

        if (dialog.ShowDialog() == true)
        {
            try
            {
                var exportData = new
                {
                    ExportedAt = System.DateTime.Now,
                    Settings = _configService?.Config
                };

                var json = Newtonsoft.Json.JsonConvert.SerializeObject(exportData, Newtonsoft.Json.Formatting.Indented);
                System.IO.File.WriteAllText(dialog.FileName, json);

                System.Windows.MessageBox.Show($"Data exported to {dialog.FileName}", "Info",
                    System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Information);
            }
            catch (System.Exception ex)
            {
                System.Windows.MessageBox.Show($"Failed to export: {ex.Message}", "Error",
                    System.Windows.MessageBoxButton.OK, System.Windows.MessageBoxImage.Error);
            }
        }
    }
}