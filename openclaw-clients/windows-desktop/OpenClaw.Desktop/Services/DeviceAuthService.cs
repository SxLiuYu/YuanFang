using System;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;
using OpenClaw.Desktop.Models;

namespace OpenClaw.Desktop.Services
{
    public class DeviceAuthService : IDisposable
    {
        private static readonly string ConfigFilePath = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.ApplicationData),
            "OpenClaw",
            "device_auth.json");
        
        private readonly HttpClient _httpClient;
        private string _serverUrl;
        private DeviceInfo? _deviceInfo;
        private bool _disposed;
        
        public event EventHandler<DeviceAuthEventArgs>? AuthStatusChanged;
        
        public string DeviceId => _deviceInfo?.DeviceId ?? GenerateDeviceId();
        public string? Token => _deviceInfo?.Token;
        public bool IsConfirmed => _deviceInfo?.IsConfirmed ?? false;
        public string? CurrentTempId { get; private set; }
        
        public DeviceAuthService(string serverUrl = "http://localhost:8000")
        {
            _serverUrl = serverUrl;
            _httpClient = new HttpClient { Timeout = TimeSpan.FromSeconds(30) };
            
            LoadDeviceInfo();
        }
        
        public void SetServerUrl(string serverUrl)
        {
            _serverUrl = serverUrl;
        }
        
        private string GenerateDeviceId()
        {
            var deviceId = Environment.MachineName + "_" + Environment.UserName;
            using var sha = System.Security.Cryptography.SHA256.Create();
            var hash = sha.ComputeHash(Encoding.UTF8.GetBytes(deviceId));
            return Convert.ToBase64String(hash).Replace("/", "_").Replace("+", "-").Substring(0, 32);
        }
        
        private void LoadDeviceInfo()
        {
            try
            {
                if (File.Exists(ConfigFilePath))
                {
                    var json = File.ReadAllText(ConfigFilePath);
                    _deviceInfo = JsonConvert.DeserializeObject<DeviceInfo>(json);
                    
                    if (_deviceInfo != null)
                    {
                        System.Diagnostics.Debug.WriteLine($"设备信息已加载: {_deviceInfo.DeviceId}, 已确认: {_deviceInfo.IsConfirmed}");
                    }
                }
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"加载设备信息失败: {ex.Message}");
            }
        }
        
        private void SaveDeviceInfo()
        {
            try
            {
                var directory = Path.GetDirectoryName(ConfigFilePath);
                if (!string.IsNullOrEmpty(directory) && !Directory.Exists(directory))
                {
                    Directory.CreateDirectory(directory);
                }
                
                var json = JsonConvert.SerializeObject(_deviceInfo, Formatting.Indented);
                File.WriteAllText(ConfigFilePath, json);
                
                System.Diagnostics.Debug.WriteLine($"设备信息已保存: {_deviceInfo?.DeviceId}");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"保存设备信息失败: {ex.Message}");
            }
        }
        
        public async Task<DeviceAuthResult> RegisterOrLoginAsync()
        {
            try
            {
                var deviceName = Environment.MachineName;
                var deviceModel = $"Windows {Environment.OSVersion.Version.Major}.{Environment.OSVersion.Version.Minor}";
                
                var requestData = new
                {
                    device_id = DeviceId,
                    device_name = deviceName,
                    device_model = deviceModel
                };
                
                var content = new StringContent(
                    JsonConvert.SerializeObject(requestData),
                    Encoding.UTF8,
                    "application/json");
                
                var response = await _httpClient.PostAsync($"{_serverUrl}/device/register", content);
                var responseContent = await response.Content.ReadAsStringAsync();
                var result = JsonConvert.DeserializeObject<DeviceAuthResult>(responseContent);
                
                if (result == null)
                {
                    return new DeviceAuthResult { Success = false, Error = "无效的响应" };
                }
                
                if (result.Confirmed && !string.IsNullOrEmpty(result.Token))
                {
                    _deviceInfo = new DeviceInfo
                    {
                        DeviceId = DeviceId,
                        DeviceName = deviceName,
                        DeviceModel = deviceModel,
                        Token = result.Token,
                        IsConfirmed = true,
                        ConfirmedAt = DateTime.Now
                    };
                    
                    SaveDeviceInfo();
                    
                    AuthStatusChanged?.Invoke(this, new DeviceAuthEventArgs
                    {
                        Status = "confirmed",
                        Message = "设备已认证"
                    });
                }
                else if (result.Status == "pending" && !string.IsNullOrEmpty(result.TempId))
                {
                    CurrentTempId = result.TempId;
                    
                    AuthStatusChanged?.Invoke(this, new DeviceAuthEventArgs
                    {
                        Status = "pending",
                        Message = result.Message ?? "请查看飞书获取确认码",
                        TempId = result.TempId
                    });
                }
                
                return result;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"设备注册失败: {ex.Message}");
                
                return new DeviceAuthResult
                {
                    Success = false,
                    Error = ex.Message
                };
            }
        }
        
        public async Task<DeviceAuthResult> ConfirmDeviceAsync(string tempId, string confirmCode)
        {
            try
            {
                var requestData = new
                {
                    temp_id = tempId,
                    confirm_code = confirmCode.ToUpper()
                };
                
                var content = new StringContent(
                    JsonConvert.SerializeObject(requestData),
                    Encoding.UTF8,
                    "application/json");
                
                var response = await _httpClient.PostAsync($"{_serverUrl}/device/confirm", content);
                var responseContent = await response.Content.ReadAsStringAsync();
                var result = JsonConvert.DeserializeObject<DeviceAuthResult>(responseContent);
                
                if (result == null)
                {
                    return new DeviceAuthResult { Success = false, Error = "无效的响应" };
                }
                
                if (result.Confirmed && !string.IsNullOrEmpty(result.Token))
                {
                    _deviceInfo = new DeviceInfo
                    {
                        DeviceId = DeviceId,
                        DeviceName = result.DeviceName ?? Environment.MachineName,
                        DeviceModel = $"Windows {Environment.OSVersion.Version.Major}.{Environment.OSVersion.Version.Minor}",
                        Token = result.Token,
                        IsConfirmed = true,
                        ConfirmedAt = DateTime.Now
                    };
                    
                    SaveDeviceInfo();
                    CurrentTempId = null;
                    
                    AuthStatusChanged?.Invoke(this, new DeviceAuthEventArgs
                    {
                        Status = "confirmed",
                        Message = "设备登录成功"
                    });
                }
                
                return result;
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"设备确认失败: {ex.Message}");
                
                return new DeviceAuthResult
                {
                    Success = false,
                    Error = ex.Message
                };
            }
        }
        
        public async Task<bool> CheckStatusAsync()
        {
            try
            {
                var response = await _httpClient.GetAsync($"{_serverUrl}/device/status?device_id={DeviceId}");
                var responseContent = await response.Content.ReadAsStringAsync();
                var result = JsonConvert.DeserializeObject<DeviceAuthResult>(responseContent);
                
                return result?.Confirmed ?? false;
            }
            catch
            {
                return false;
            }
        }
        
        public void Logout()
        {
            try
            {
                if (File.Exists(ConfigFilePath))
                {
                    File.Delete(ConfigFilePath);
                }
                
                _deviceInfo = null;
                CurrentTempId = null;
                
                AuthStatusChanged?.Invoke(this, new DeviceAuthEventArgs
                {
                    Status = "logout",
                    Message = "设备已登出"
                });
                
                System.Diagnostics.Debug.WriteLine("设备已登出");
            }
            catch (Exception ex)
            {
                System.Diagnostics.Debug.WriteLine($"登出失败: {ex.Message}");
            }
        }
        
        public void Dispose()
        {
            if (_disposed) return;
            
            _httpClient?.Dispose();
            _disposed = true;
            
            GC.SuppressFinalize(this);
        }
    }
    
    public class DeviceAuthEventArgs : EventArgs
    {
        public string Status { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public string? TempId { get; set; }
    }
}