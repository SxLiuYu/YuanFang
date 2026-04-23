using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace OpenClaw.Desktop.Models
{
    public class HardwareDevice
    {
        [JsonProperty("id")]
        public string Id { get; set; } = "";

        [JsonProperty("name")]
        public string Name { get; set; } = "";

        [JsonProperty("type")]
        public string Type { get; set; } = "";

        [JsonProperty("brand")]
        public string? Brand { get; set; }

        [JsonProperty("model")]
        public string? Model { get; set; }

        [JsonProperty("status")]
        public string Status { get; set; } = "offline";

        [JsonProperty("battery_level")]
        public int? BatteryLevel { get; set; }

        [JsonProperty("last_sync")]
        public DateTime? LastSync { get; set; }

        [JsonProperty("metadata")]
        public Dictionary<string, object> Metadata { get; set; } = new();
    }

    public class WatchDataSync
    {
        [JsonProperty("device_id")]
        public string DeviceId { get; set; } = "";

        [JsonProperty("user_id")]
        public string UserId { get; set; } = "";

        [JsonProperty("timestamp")]
        public DateTime Timestamp { get; set; }

        [JsonProperty("heart_rate")]
        public int? HeartRate { get; set; }

        [JsonProperty("steps")]
        public int? Steps { get; set; }

        [JsonProperty("sleep_duration")]
        public int? SleepDuration { get; set; }

        [JsonProperty("calories")]
        public int? Calories { get; set; }
    }

    public class DeviceHealthSummary
    {
        [JsonProperty("avg_heart_rate")]
        public double? AvgHeartRate { get; set; }

        [JsonProperty("max_heart_rate")]
        public int? MaxHeartRate { get; set; }

        [JsonProperty("min_heart_rate")]
        public int? MinHeartRate { get; set; }

        [JsonProperty("total_steps")]
        public int? TotalSteps { get; set; }

        [JsonProperty("avg_sleep")]
        public double? AvgSleep { get; set; }

        [JsonProperty("total_calories")]
        public int? TotalCalories { get; set; }
    }

    public class BluetoothDevice
    {
        [JsonProperty("device_id")]
        public string DeviceId { get; set; } = "";

        [JsonProperty("name")]
        public string Name { get; set; } = "";

        [JsonProperty("type")]
        public string Type { get; set; } = "";

        [JsonProperty("rssi")]
        public int Rssi { get; set; }

        [JsonProperty("is_paired")]
        public bool IsPaired { get; set; }
    }
}