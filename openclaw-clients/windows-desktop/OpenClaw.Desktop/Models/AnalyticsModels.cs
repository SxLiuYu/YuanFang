using System;
using System.Collections.Generic;
using Newtonsoft.Json;

namespace OpenClaw.Desktop.Models
{
    public class HealthScoreResponse
    {
        [JsonProperty("success")]
        public bool Success { get; set; }

        [JsonProperty("score")]
        public double Score { get; set; }

        [JsonProperty("grade")]
        public string Grade { get; set; } = "";

        [JsonProperty("components")]
        public HealthComponents? Components { get; set; }

        [JsonProperty("suggestions")]
        public List<string> Suggestions { get; set; } = new();
    }

    public class HealthComponents
    {
        [JsonProperty("heart_rate")]
        public HealthMetric? HeartRate { get; set; }

        [JsonProperty("steps")]
        public HealthMetric? Steps { get; set; }

        [JsonProperty("sleep")]
        public HealthMetric? Sleep { get; set; }

        [JsonProperty("oxygen")]
        public HealthMetric? Oxygen { get; set; }
    }

    public class HealthMetric
    {
        [JsonProperty("score")]
        public double Score { get; set; }

        [JsonProperty("value")]
        public object? Value { get; set; }
    }

    public class FinanceInsightResponse
    {
        [JsonProperty("success")]
        public bool Success { get; set; }

        [JsonProperty("period_days")]
        public int PeriodDays { get; set; }

        [JsonProperty("total_income")]
        public double TotalIncome { get; set; }

        [JsonProperty("total_expense")]
        public double TotalExpense { get; set; }

        [JsonProperty("balance")]
        public double Balance { get; set; }

        [JsonProperty("categories")]
        public List<CategoryExpense> Categories { get; set; } = new();

        [JsonProperty("insights")]
        public List<string> Insights { get; set; } = new();
    }

    public class CategoryExpense
    {
        [JsonProperty("category")]
        public string Category { get; set; } = "";

        [JsonProperty("amount")]
        public double Amount { get; set; }
    }

    public class AnomalyResponse
    {
        [JsonProperty("type")]
        public string Type { get; set; } = "";

        [JsonProperty("severity")]
        public string Severity { get; set; } = "";

        [JsonProperty("message")]
        public string Message { get; set; } = "";

        [JsonProperty("details")]
        public Dictionary<string, object>? Details { get; set; }
    }

    public class ReportResponse
    {
        [JsonProperty("success")]
        public bool Success { get; set; }

        [JsonProperty("report_type")]
        public string ReportType { get; set; } = "";

        [JsonProperty("period")]
        public string Period { get; set; } = "";

        [JsonProperty("generated_at")]
        public DateTime GeneratedAt { get; set; }

        [JsonProperty("sections")]
        public Dictionary<string, object> Sections { get; set; } = new();
    }
}