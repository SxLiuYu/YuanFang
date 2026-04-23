using System;

namespace OpenClaw.Desktop.Models;

public class Reminder
{
    public int Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public DateTime DateTime { get; set; }
    public bool IsCompleted { get; set; }
    public ReminderPriority Priority { get; set; }
    public ReminderRepeat Repeat { get; set; }
    public string? Sound { get; set; }
    public bool IsVoiceEnabled { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}

public enum ReminderPriority
{
    Low = 0,
    Normal = 1,
    High = 2,
    Urgent = 3
}

public enum ReminderRepeat
{
    None = 0,
    Daily = 1,
    Weekly = 2,
    Monthly = 3,
    Yearly = 4,
    Custom = 5
}

public class ReminderGroup
{
    public DateTime Date { get; set; }
    public List<Reminder> Reminders { get; set; } = new();
}