using System.Windows;
using System.Windows.Input;
using OpenClaw.Desktop.Services;
using OpenClaw.Desktop.ViewModels;

namespace OpenClaw.Desktop;

public partial class MainWindow : Window
{
    private readonly TrayService _trayService;
    private const int HotkeyId = 9000;

    public MainWindow(MainViewModel viewModel, TrayService trayService)
    {
        InitializeComponent();
        DataContext = viewModel;
        _trayService = trayService;
        
        _trayService.SetMainWindow(this);
        
        Loaded += MainWindow_Loaded;
        Closed += MainWindow_Closed;
    }

    private void MainWindow_Loaded(object sender, RoutedEventArgs e)
    {
        RegisterGlobalHotkey();
    }

    private void MainWindow_Closed(object? sender, EventArgs e)
    {
        UnregisterHotkey();
    }

    private void RegisterGlobalHotkey()
    {
        var helper = new System.Windows.Interop.WindowInteropHelper(this);
        var hwnd = helper.Handle;
        
        var source = System.Windows.Interop.HwndSource.FromHwnd(hwnd);
        source?.AddHook(WndProc);

        RegisterHotKey(hwnd, HotkeyId, (uint)ModifierKeys.Control | (uint)ModifierKeys.Shift, (uint)KeyInterop.VirtualKeyFromKey(Key.O));
    }

    private void UnregisterHotkey()
    {
        var helper = new System.Windows.Interop.WindowInteropHelper(this);
        UnregisterHotKey(helper.Handle, HotkeyId);
    }

    private IntPtr WndProc(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
    {
        const int WM_HOTKEY = 0x0312;
        
        if (msg == WM_HOTKEY && wParam.ToInt32() == HotkeyId)
        {
            if (Visibility == Visibility.Visible)
            {
                Hide();
            }
            else
            {
                Show();
                Activate();
            }
            handled = true;
        }
        
        return IntPtr.Zero;
    }

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern bool RegisterHotKey(IntPtr hWnd, int id, uint fsModifiers, uint vk);

    [System.Runtime.InteropServices.DllImport("user32.dll")]
    private static extern bool UnregisterHotKey(IntPtr hWnd, int id);
}