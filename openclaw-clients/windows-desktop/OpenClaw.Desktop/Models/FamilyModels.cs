using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace OpenClaw.Desktop.Models
{
    public class FamilyGroupCreate
    {
        [JsonProperty("name")]
        public string Name { get; set; } = "";

        [JsonProperty("owner_id")]
        public string OwnerId { get; set; } = "";
    }

    public class FamilyGroup
    {
        [JsonProperty("id")]
        public string Id { get; set; } = "";

        [JsonProperty("name")]
        public string Name { get; set; } = "";

        [JsonProperty("owner_id")]
        public string OwnerId { get; set; } = "";

        [JsonProperty("members")]
        public List<FamilyMember> Members { get; set; } = new();

        [JsonProperty("invite_code")]
        public string InviteCode { get; set; } = "";

        [JsonProperty("settings")]
        public Dictionary<string, object> Settings { get; set; } = new();

        [JsonProperty("created_at")]
        public DateTime CreatedAt { get; set; }

        [JsonProperty("updated_at")]
        public DateTime UpdatedAt { get; set; }
    }

    public class FamilyMember
    {
        [JsonProperty("user_id")]
        public string UserId { get; set; } = "";

        [JsonProperty("name")]
        public string Name { get; set; } = "";

        [JsonProperty("role")]
        public string Role { get; set; } = "member";

        [JsonProperty("avatar", NullValueHandling = NullValueHandling.Ignore)]
        public string? Avatar { get; set; }

        [JsonProperty("location", NullValueHandling = NullValueHandling.Ignore)]
        public MemberLocation? Location { get; set; }

        [JsonProperty("last_active", NullValueHandling = NullValueHandling.Ignore)]
        public DateTime? LastActive { get; set; }
    }

    public class MemberLocation
    {
        [JsonProperty("latitude")]
        public double Latitude { get; set; }

        [JsonProperty("longitude")]
        public double Longitude { get; set; }

        [JsonProperty("address", NullValueHandling = NullValueHandling.Ignore)]
        public string? Address { get; set; }

        [JsonProperty("accuracy", NullValueHandling = NullValueHandling.Ignore)]
        public double? Accuracy { get; set; }

        [JsonProperty("timestamp")]
        public DateTime Timestamp { get; set; }
    }

    public class LocationShareRequest
    {
        [JsonProperty("user_id")]
        public string UserId { get; set; } = "";

        [JsonProperty("latitude")]
        public double Latitude { get; set; }

        [JsonProperty("longitude")]
        public double Longitude { get; set; }

        [JsonProperty("address", NullValueHandling = NullValueHandling.Ignore)]
        public string? Address { get; set; }

        [JsonProperty("accuracy", NullValueHandling = NullValueHandling.Ignore)]
        public double? Accuracy { get; set; }
    }

    public class SharedScheduleCreate
    {
        [JsonProperty("group_id")]
        public string GroupId { get; set; } = "";

        [JsonProperty("title")]
        public string Title { get; set; } = "";

        [JsonProperty("description", NullValueHandling = NullValueHandling.Ignore)]
        public string? Description { get; set; }

        [JsonProperty("start_time")]
        public DateTime StartTime { get; set; }

        [JsonProperty("end_time", NullValueHandling = NullValueHandling.Ignore)]
        public DateTime? EndTime { get; set; }

        [JsonProperty("assignees")]
        public List<string> Assignees { get; set; } = new();

        [JsonProperty("reminders")]
        public List<int> Reminders { get; set; } = new();
    }

    public class SharedSchedule
    {
        [JsonProperty("id")]
        public string Id { get; set; } = "";

        [JsonProperty("group_id")]
        public string GroupId { get; set; } = "";

        [JsonProperty("title")]
        public string Title { get; set; } = "";

        [JsonProperty("description", NullValueHandling = NullValueHandling.Ignore)]
        public string? Description { get; set; }

        [JsonProperty("start_time")]
        public DateTime StartTime { get; set; }

        [JsonProperty("end_time", NullValueHandling = NullValueHandling.Ignore)]
        public DateTime? EndTime { get; set; }

        [JsonProperty("assignees")]
        public List<string> Assignees { get; set; } = new();

        [JsonProperty("reminders")]
        public List<int> Reminders { get; set; } = new();

        [JsonProperty("status")]
        public string Status { get; set; } = "pending";

        [JsonProperty("created_by")]
        public string CreatedBy { get; set; } = "";

        [JsonProperty("created_at")]
        public DateTime CreatedAt { get; set; }
    }

    public class UserGroupInfo
    {
        [JsonProperty("id")]
        public string Id { get; set; } = "";

        [JsonProperty("name")]
        public string Name { get; set; } = "";

        [JsonProperty("owner_id")]
        public string OwnerId { get; set; } = "";

        [JsonProperty("invite_code")]
        public string InviteCode { get; set; } = "";

        [JsonProperty("my_role")]
        public string MyRole { get; set; } = "";

        [JsonProperty("created_at")]
        public DateTime CreatedAt { get; set; }
    }
}