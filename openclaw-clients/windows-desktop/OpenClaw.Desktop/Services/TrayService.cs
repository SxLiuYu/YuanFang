using System;
using System.Windows;

namespace OpenClaw.Desktop.Services;

public class TrayService : IDisposable
{
    private Window? _mainWindow;
    private bool _disposed;

    public TrayService()
    {
    }

    public void SetMainWindow(Window window)
    {
        _mainWindow = window;
    }

    public void MinimizeToTray()
    {
        _mainWindow?.Hide();
    }

    public void ShowMainWindow()
    {
        if (_mainWindow == null) return;
        _mainWindow.Show();
        _mainWindow.WindowState = WindowState.Normal;
        _mainWindow.Activate();
    }

    public void ShowNotification(string title, string message)
    {
        System.Diagnostics.Debug.WriteLine($"[Notification] {title}: {message}");
    }

    public void ShowWarning(string title, string message)
    {
        System.Diagnostics.Debug.WriteLine($"[Warning] {title}: {message}");
    }

    public void ShowError(string title, string message)
    {
        System.Diagnostics.Debug.WriteLine($"[Error] {title}: {message}");
    }

    public void Dispose()
    {
        if (_disposed) return;
        _disposed = true;
        GC.SuppressFinalize(this);
    }
}