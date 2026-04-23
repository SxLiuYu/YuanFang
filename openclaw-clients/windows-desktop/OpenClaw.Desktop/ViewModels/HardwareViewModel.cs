using System;
using System.Collections.ObjectModel;
using System.Threading.Tasks;
using System.Windows.Input;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using OpenClaw.Desktop.Models;
using OpenClaw.Desktop.Services.Api;

namespace OpenClaw.Desktop.ViewModels
{
    public partial class HardwareViewModel : BaseViewModel
    {
        private readonly HardwareApiService _hardwareApiService;

        [ObservableProperty]
        private string _currentUserId = "user_default";

        [ObservableProperty]
        private bool _isLoading;

        [ObservableProperty]
        private bool _isScanning;

        [ObservableProperty]
        private HardwareDevice? _selectedDevice;

        [ObservableProperty]
        private HealthSummary? _healthSummary;

        public ObservableCollection<HardwareDevice> Devices { get; } = new();
        public ObservableCollection<BluetoothDevice> ScannedDevices { get; } = new();

        public ICommand LoadDevicesCommand { get; }
        public ICommand ScanBluetoothCommand { get; }
        public ICommand PairDeviceCommand { get; }
        public ICommand ControlDeviceCommand { get; }
        public ICommand RefreshHealthCommand { get; }

        public HardwareViewModel(HardwareApiService hardwareApiService)
        {
            _hardwareApiService = hardwareApiService;

            LoadDevicesCommand = new AsyncRelayCommand(LoadDevicesAsync);
            ScanBluetoothCommand = new AsyncRelayCommand(ScanBluetoothAsync);
            PairDeviceCommand = new AsyncRelayCommand<BluetoothDevice>(PairDeviceAsync);
            ControlDeviceCommand = new AsyncRelayCommand<string>(ControlDeviceAsync);
            RefreshHealthCommand = new AsyncRelayCommand(RefreshHealthAsync);
        }

        private async Task LoadDevicesAsync()
        {
            IsLoading = true;

            try
            {
                var devices = await _hardwareApiService.GetDevicesAsync();

                Devices.Clear();
                foreach (var device in devices)
                {
                    Devices.Add(device);
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"加载设备失败: {ex.Message}");
            }
            finally
            {
                IsLoading = false;
            }
        }

        private async Task ScanBluetoothAsync()
        {
            IsScanning = true;

            try
            {
                var devices = await _hardwareApiService.ScanBluetoothAsync();

                ScannedDevices.Clear();
                foreach (var device in devices)
                {
                    ScannedDevices.Add(device);
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"扫描蓝牙失败: {ex.Message}");
            }
            finally
            {
                IsScanning = false;
            }
        }

        private async Task PairDeviceAsync(BluetoothDevice? device)
        {
            if (device == null) return;

            try
            {
                var result = await _hardwareApiService.PairBluetoothAsync(
                    device.DeviceId,
                    device.Name,
                    device.Type
                );

                if (result.TryGetValue("success", out var success) && success is bool isSuccess && isSuccess)
                {
                    await LoadDevicesAsync();
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"配对失败: {ex.Message}");
            }
        }

        private async Task ControlDeviceAsync(string? action)
        {
            if (SelectedDevice == null || string.IsNullOrEmpty(action)) return;

            try
            {
                await _hardwareApiService.ControlDeviceAsync(SelectedDevice.Id, action);
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"控制失败: {ex.Message}");
            }
        }

        private async Task RefreshHealthAsync()
        {
            if (SelectedDevice == null) return;

            try
            {
                HealthSummary = await _hardwareApiService.GetHealthSummaryAsync(
                    SelectedDevice.Id,
                    CurrentUserId
                );
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"获取健康数据失败: {ex.Message}");
            }
        }

        public async Task InitializeAsync()
        {
            await LoadDevicesAsync();
        }
    }
}