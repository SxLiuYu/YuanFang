using System.IO;
using System.Reflection;
using System.Windows;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using OpenClaw.Desktop.Services;
using OpenClaw.Desktop.Services.Api;
using OpenClaw.Desktop.Services.Voice;
using OpenClaw.Desktop.ViewModels;
using OpenClaw.Desktop.Views;

namespace OpenClaw.Desktop;

public partial class App : Application
{
    public static IServiceProvider ServiceProvider { get; private set; } = null!;
    public static IConfiguration Configuration { get; private set; } = null!;

    protected override void OnStartup(StartupEventArgs e)
    {
        base.OnStartup(e);

        try
        {
            var builder = new ConfigurationBuilder()
                .SetBasePath(Directory.GetCurrentDirectory())
                .AddJsonFile("appsettings.json", optional: true, reloadOnChange: true);

            Configuration = builder.Build();

            var serviceCollection = new ServiceCollection();
            ConfigureServices(serviceCollection);
            ServiceProvider = serviceCollection.BuildServiceProvider();

            var configService = ServiceProvider.GetRequiredService<ConfigService>();
            
            var deviceAuth = ServiceProvider.GetRequiredService<DeviceAuthService>();
            deviceAuth.SetServerUrl(configService.Config.ServerUrl);
            
            if (!deviceAuth.IsConfirmed)
            {
                var confirmWindow = ServiceProvider.GetRequiredService<DeviceConfirmWindow>();
                var result = confirmWindow.ShowDialog();
                
                if (result != true)
                {
                    Shutdown();
                    return;
                }
            }

            var mainWindow = ServiceProvider.GetRequiredService<MainWindow>();
            mainWindow.Show();

            ServiceProvider.GetRequiredService<TrayService>();
        }
        catch (Exception ex)
        {
            MessageBox.Show($"启动失败: {ex.Message}\n\n详情: {ex.StackTrace}", "OpenClaw Desktop 错误", MessageBoxButton.OK, MessageBoxImage.Error);
            Shutdown();
        }
    }

    private void ConfigureServices(IServiceCollection services)
    {
        // 配置服务
        services.AddSingleton<ConfigService>();
        
        // 设备认证
        services.AddSingleton<DeviceAuthService>();
        
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
        services.AddSingleton<HomeViewModel>();
        services.AddSingleton<MainViewModel>();
        services.AddSingleton<VoiceControlViewModel>();
        services.AddSingleton<FamilyGroupViewModel>();
        services.AddSingleton<HardwareViewModel>();
        services.AddSingleton<AnalyticsViewModel>();
        services.AddSingleton<HealthViewModel>();
        services.AddSingleton<FinanceViewModel>();
        services.AddSingleton<TasksViewModel>();
        services.AddSingleton<SettingsViewModel>();
        
        // Views
        services.AddTransient<HomeView>();
        services.AddTransient<VoiceControlView>();
        services.AddTransient<FamilyGroupView>();
        services.AddTransient<HardwareView>();
        services.AddTransient<AnalyticsView>();
        services.AddTransient<HealthView>();
        services.AddTransient<FinanceView>();
        services.AddTransient<TasksView>();
        services.AddTransient<SettingsView>();
        services.AddTransient<DeviceConfirmWindow>();
        
        // 主窗口
        services.AddSingleton<MainWindow>();
    }

    protected override void OnExit(ExitEventArgs e)
    {
        var trayService = ServiceProvider?.GetService<TrayService>();
        trayService?.Dispose();
        
        var deviceAuth = ServiceProvider?.GetService<DeviceAuthService>();
        deviceAuth?.Dispose();
        
        base.OnExit(e);
    }
}