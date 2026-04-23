using System.Collections.Generic;
using System.Threading.Tasks;
using OpenClaw.Desktop.Models;

namespace OpenClaw.Desktop.Services.Api
{
    public class HardwareApiService
    {
        private readonly ApiClient _apiClient;
        private readonly string _baseUrl = "http://localhost:8082/api/v1/hardware";

        public HardwareApiService(ApiClient apiClient)
        {
            _apiClient = apiClient;
        }

        public async Task<List<HardwareDevice>> GetDevicesAsync(string? deviceType = null, string? status = null)
        {
            var url = $"{_baseUrl}/devices";
            var @params = new List<string>();
            if (!string.IsNullOrEmpty(deviceType)) @params.Add($"device_type={deviceType}");
            if (!string.IsNullOrEmpty(status)) @params.Add($"status={status}");
            if (@params.Count > 0) url += "?" + string.Join("&", @params);
            return await _apiClient.GetAsync<List<HardwareDevice>>(url) ?? new List<HardwareDevice>();
        }

        public async Task<HardwareDevice?> GetDeviceAsync(string deviceId)
        {
            return await _apiClient.GetAsync<HardwareDevice>($"{_baseUrl}/devices/{deviceId}");
        }

        public async Task<Dictionary<string, object>> ControlDeviceAsync(string deviceId, string action, Dictionary<string, object>? @params = null)
        {
            var request = new { device_id = deviceId, action, @params };
            return await _apiClient.PostAsync<Dictionary<string, object>>($"{_baseUrl}/devices/{deviceId}/control", request)
                ?? new Dictionary<string, object>();
        }

        public async Task<HealthSummary?> GetHealthSummaryAsync(string deviceId, string userId)
        {
            return await _apiClient.GetAsync<HealthSummary>($"{_baseUrl}/devices/{deviceId}/watch/summary?user_id={userId}");
        }

        public async Task<List<BluetoothDevice>> ScanBluetoothAsync()
        {
            return await _apiClient.GetAsync<List<BluetoothDevice>>($"{_baseUrl}/bluetooth/scan")
                ?? new List<BluetoothDevice>();
        }

        public async Task<Dictionary<string, object>> PairBluetoothAsync(string deviceId, string name, string type)
        {
            var url = $"{_baseUrl}/bluetooth/pair?device_id={deviceId}&device_name={name}&device_type={type}";
            return await _apiClient.PostAsync<Dictionary<string, object>>(url, null)
                ?? new Dictionary<string, object>();
        }
    }
}