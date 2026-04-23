using System;
using System.IO;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using Newtonsoft.Json;

namespace OpenClaw.Desktop.Models
{
    public class DeviceAuthResult
    {
        [JsonProperty("success")]
        public bool Success { get; set; }
        
        [JsonProperty("confirmed")]
        public bool Confirmed { get; set; }
        
        [JsonProperty("token")]
        public string? Token { get; set; }
        
        [JsonProperty("status")]
        public string? Status { get; set; }
        
        [JsonProperty("temp_id")]
        public string? TempId { get; set; }
        
        [JsonProperty("message")]
        public string? Message { get; set; }
        
        [JsonProperty("device_name")]
        public string? DeviceName { get; set; }
        
        [JsonProperty("error")]
        public string? Error { get; set; }
    }
    
    public class DeviceInfo
    {
        public string DeviceId { get; set; } = string.Empty;
        public string DeviceName { get; set; } = string.Empty;
        public string DeviceModel { get; set; } = string.Empty;
        public string Token { get; set; } = string.Empty;
        public bool IsConfirmed { get; set; }
        public DateTime ConfirmedAt { get; set; }
    }
}