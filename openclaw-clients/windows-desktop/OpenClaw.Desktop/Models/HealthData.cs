using System;

namespace OpenClaw.Desktop.Models;

public class HealthData
{
    public int Id { get; set; }
    public DateTime Date { get; set; }
    public int Steps { get; set; }
    public double Distance { get; set; }
    public int Calories { get; set; }
    public int HeartRate { get; set; }
    public int SleepHours { get; set; }
    public double Weight { get; set; }
    public string? Notes { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}

public class HealthSummary
{
    public double AverageSteps { get; set; }
    public double AverageHeartRate { get; set; }
    public double TotalDistance { get; set; }
    public int TotalCalories { get; set; }
    public double AverageSleep { get; set; }
    public DateTime PeriodStart { get; set; }
    public DateTime PeriodEnd { get; set; }
}