using System.Threading.Tasks;
using System.Windows.Input;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using OpenClaw.Desktop.Services;

namespace OpenClaw.Desktop.ViewModels
{
    public partial class DeviceConfirmViewModel : BaseViewModel
    {
        private readonly DeviceAuthService _authService;
        
        [ObservableProperty]
        private string _deviceName = string.Empty;
        
        [ObservableProperty]
        private string _tempId = string.Empty;
        
        [ObservableProperty]
        private string _confirmCode = string.Empty;
        
        [ObservableProperty]
        private string _statusMessage = "正在获取设备信息...";
        
        [ObservableProperty]
        private bool _isConfirming;
        
        [ObservableProperty]
        private int _remainingSeconds = 300;
        
        [ObservableProperty]
        private bool _canConfirm = true;
        
        public ICommand ConfirmCommand { get; }
        public ICommand ResendCommand { get; }
        public ICommand CancelCommand { get; }
        
        public event EventHandler? Confirmed;
        public event EventHandler? Cancelled;
        
        public DeviceConfirmViewModel(DeviceAuthService authService)
        {
            _authService = authService;
            
            ConfirmCommand = new AsyncRelayCommand(ConfirmAsync, () => CanConfirm && !IsConfirming);
            ResendCommand = new AsyncRelayCommand(ResendAsync, () => !IsConfirming);
            CancelCommand = new RelayCommand(Cancel);
            
            _authService.AuthStatusChanged += OnAuthStatusChanged;
        }
        
        public async Task InitializeAsync()
        {
            StatusMessage = "正在注册设备...";
            
            var result = await _authService.RegisterOrLoginAsync();
            
            if (result.Confirmed)
            {
                StatusMessage = "设备已认证";
                Confirmed?.Invoke(this, EventArgs.Empty);
            }
            else if (result.Status == "pending")
            {
                TempId = result.TempId ?? string.Empty;
                StatusMessage = result.Message ?? "请查看飞书获取确认码";
                DeviceName = Environment.MachineName;
                StartCountdown();
            }
            else
            {
                StatusMessage = $"注册失败: {result.Error ?? result.Message}";
            }
        }
        
        private async Task ConfirmAsync()
        {
            if (string.IsNullOrWhiteSpace(ConfirmCode) || ConfirmCode.Length != 6)
            {
                StatusMessage = "请输入 6 位确认码";
                return;
            }
            
            IsConfirming = true;
            CanConfirm = false;
            StatusMessage = "正在确认...";
            
            try
            {
                var result = await _authService.ConfirmDeviceAsync(TempId, ConfirmCode);
                
                if (result.Confirmed)
                {
                    StatusMessage = "设备登录成功！";
                    Confirmed?.Invoke(this, EventArgs.Empty);
                }
                else
                {
                    StatusMessage = result.Error ?? result.Message ?? "确认失败";
                    CanConfirm = true;
                }
            }
            finally
            {
                IsConfirming = false;
            }
        }
        
        private async Task ResendAsync()
        {
            IsConfirming = true;
            StatusMessage = "正在重新发送...";
            
            try
            {
                var result = await _authService.RegisterOrLoginAsync();
                
                if (result.Status == "pending")
                {
                    TempId = result.TempId ?? TempId;
                    StatusMessage = "已重新发送，请查看飞书";
                    RemainingSeconds = 300;
                }
                else if (result.Confirmed)
                {
                    StatusMessage = "设备已认证";
                    Confirmed?.Invoke(this, EventArgs.Empty);
                }
                else
                {
                    StatusMessage = $"发送失败: {result.Error}";
                }
            }
            finally
            {
                IsConfirming = false;
            }
        }
        
        private void Cancel()
        {
            Cancelled?.Invoke(this, EventArgs.Empty);
        }
        
        private void StartCountdown()
        {
            Task.Run(async () =>
            {
                while (RemainingSeconds > 0)
                {
                    await Task.Delay(1000);
                    RemainingSeconds--;
                    
                    if (RemainingSeconds <= 0)
                    {
                        CanConfirm = false;
                        StatusMessage = "确认码已过期，请重新发送";
                    }
                }
            });
        }
        
        private void OnAuthStatusChanged(object? sender, DeviceAuthEventArgs e)
        {
            if (e.Status == "confirmed")
            {
                StatusMessage = "设备已认证";
                Confirmed?.Invoke(this, EventArgs.Empty);
            }
        }
    }
}