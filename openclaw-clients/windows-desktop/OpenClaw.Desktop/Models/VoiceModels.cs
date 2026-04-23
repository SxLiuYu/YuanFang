using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace OpenClaw.Desktop.Models
{
    public class VoiceCommandRequest
    {
        [JsonProperty("text")]
        public string Text { get; set; } = "";

        [JsonProperty("context", NullValueHandling = NullValueHandling.Ignore)]
        public Dictionary<string, object>? Context { get; set; }

        [JsonProperty("device_id", NullValueHandling = NullValueHandling.Ignore)]
        public string? DeviceId { get; set; }

        [JsonProperty("user_id", NullValueHandling = NullValueHandling.Ignore)]
        public string? UserId { get; set; }
    }

    public class VoiceCommandResponse
    {
        [JsonProperty("success")]
        public bool Success { get; set; }

        [JsonProperty("intent")]
        public string Intent { get; set; } = "";

        [JsonProperty("slots")]
        public Dictionary<string, object> Slots { get; set; } = new();

        [JsonProperty("action", NullValueHandling = NullValueHandling.Ignore)]
        public Dictionary<string, object>? Action { get; set; }

        [JsonProperty("message")]
        public string Message { get; set; } = "";

        [JsonProperty("suggestions")]
        public List<VoiceSuggestion> Suggestions { get; set; } = new();
    }

    public class VoiceSuggestion
    {
        [JsonProperty("type")]
        public string Type { get; set; } = "";

        [JsonProperty("title")]
        public string Title { get; set; } = "";

        [JsonProperty("description")]
        public string Description { get; set; } = "";

        [JsonProperty("confidence")]
        public double Confidence { get; set; }

        [JsonProperty("action")]
        public Dictionary<string, object> Action { get; set; } = new();

        [JsonProperty("icon", NullValueHandling = NullValueHandling.Ignore)]
        public string? Icon { get; set; }
    }

    public class ScheduleParseRequest
    {
        [JsonProperty("text")]
        public string Text { get; set; } = "";

        [JsonProperty("user_id", NullValueHandling = NullValueHandling.Ignore)]
        public string? UserId { get; set; }
    }

    public class ScheduleParseResponse
    {
        [JsonProperty("success")]
        public bool Success { get; set; }

        [JsonProperty("title")]
        public string Title { get; set; } = "";

        [JsonProperty("start_time", NullValueHandling = NullValueHandling.Ignore)]
        public DateTime? StartTime { get; set; }

        [JsonProperty("end_time", NullValueHandling = NullValueHandling.Ignore)]
        public DateTime? EndTime { get; set; }

        [JsonProperty("recurrence", NullValueHandling = NullValueHandling.Ignore)]
        public string? Recurrence { get; set; }

        [JsonProperty("reminders")]
        public List<DateTime> Reminders { get; set; } = new();

        [JsonProperty("confidence")]
        public double Confidence { get; set; }
    }

    public class DeviceControlResult
    {
        public string Device { get; set; } = "";
        public string Action { get; set; } = "";
        public bool Success { get; set; }
        public string Message { get; set; } = "";
    }

    public class SceneControlResult
    {
        public string Scene { get; set; } = "";
        public string SceneName { get; set; } = "";
        public List<DeviceAction> Actions { get; set; } = new();
        public bool Success { get; set; }
        public string Message { get; set; } = "";
    }

    public class DeviceAction
    {
        public string Device { get; set; } = "";
        public string Action { get; set; } = "";
        public Dictionary<string, object>? Params { get; set; }
    }
}