using System.Windows;
using OpenClaw.Desktop.Services;
using OpenClaw.Desktop.ViewModels;

namespace OpenClaw.Desktop.Views
{
    public partial class DeviceConfirmWindow : Window
    {
        private readonly DeviceConfirmViewModel _viewModel;
        
        public DeviceConfirmWindow(DeviceAuthService authService)
        {
            InitializeComponent();
            
            _viewModel = new DeviceConfirmViewModel(authService);
            DataContext = _viewModel;
            
            _viewModel.Confirmed += OnConfirmed;
            _viewModel.Cancelled += OnCancelled;
            
            Loaded += async (s, e) => await _viewModel.InitializeAsync();
            
            ConfirmCodeBox.Focus();
        }
        
        private void OnConfirmed(object? sender, System.EventArgs e)
        {
            Dispatcher.Invoke(() =>
            {
                DialogResult = true;
                Close();
            });
        }
        
        private void OnCancelled(object? sender, System.EventArgs e)
        {
            Dispatcher.Invoke(() =>
            {
                DialogResult = false;
                Close();
            });
        }
    }
}