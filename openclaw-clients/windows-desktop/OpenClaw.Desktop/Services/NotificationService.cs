using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace OpenClaw.Desktop.Services
{
    public class NotificationService : IDisposable
    {
        private readonly Dictionary<Guid, ScheduledNotification> _scheduledNotifications;
        private readonly Dictionary<Guid, Reminder> _activeReminders;
        private readonly Timer _reminderCheckTimer;
        private readonly Timer _cleanupTimer;
        private readonly DataService _dataService;
        private readonly object _lockObject;
        private bool _disposed;

        public event EventHandler<NotificationEventArgs>? NotificationActivated;
        public event EventHandler<NotificationEventArgs>? NotificationDismissed;
        public event EventHandler<ReminderEventArgs>? ReminderTriggered;
        public event EventHandler<NotificationErrorEventArgs>? ErrorOccurred;

        public bool IsInitialized { get; private set; }
        public int ActiveRemindersCount => _activeReminders.Count;
        public int ScheduledNotificationsCount => _scheduledNotifications.Count;

        public NotificationService(DataService? dataService = null)
        {
            _dataService = dataService ?? throw new ArgumentNullException(nameof(dataService));
            _scheduledNotifications = new Dictionary<Guid, ScheduledNotification>();
            _activeReminders = new Dictionary<Guid, Reminder>();
            _lockObject = new object();
            _reminderCheckTimer = new Timer(CheckReminders, null, TimeSpan.FromSeconds(1), TimeSpan.FromSeconds(30));
            _cleanupTimer = new Timer(CleanupExpiredNotifications, null, TimeSpan.FromMinutes(1), TimeSpan.FromMinutes(5));
        }

        public async Task InitializeAsync()
        {
            try
            {
                await LoadScheduledNotificationsAsync();
                await LoadRemindersAsync();
                IsInitialized = true;
            }
            catch (Exception ex)
            {
                ErrorOccurred?.Invoke(this, new NotificationErrorEventArgs
                {
                    Operation = "Initialize",
                    Message = "Failed to initialize notification service",
                    Exception = ex
                });
            }
        }

        public void ShowNotification(string title, string message, string? tag = null, NotificationType type = NotificationType.Info, int durationSeconds = 5)
        {
            System.Diagnostics.Debug.WriteLine($"[Notification] {type}: {title} - {message}");
            NotificationActivated?.Invoke(this, new NotificationEventArgs { Tag = tag ?? Guid.NewGuid().ToString(), Timestamp = DateTime.Now });
        }

        public void ShowNotificationWithActions(string title, string message, Dictionary<string, string> actions, string? tag = null)
        {
            System.Diagnostics.Debug.WriteLine($"[Notification] {title} - {message}");
        }

        public Guid ScheduleNotification(string title, string message, DateTime scheduledTime, NotificationType type = NotificationType.Info, bool repeat = false, TimeSpan? repeatInterval = null)
        {
            var id = Guid.NewGuid();
            var notification = new ScheduledNotification
            {
                Id = id,
                Title = title,
                Message = message,
                ScheduledTime = scheduledTime,
                Type = type,
                Repeat = repeat,
                RepeatInterval = repeatInterval,
                IsTriggered = false
            };

            lock (_lockObject)
            {
                _scheduledNotifications[id] = notification;
            }

            return id;
        }

        public bool CancelScheduledNotification(Guid notificationId)
        {
            lock (_lockObject)
            {
                return _scheduledNotifications.Remove(notificationId);
            }
        }

        public Guid CreateReminder(string title, string message, DateTime remindAt, bool repeat = false, TimeSpan? repeatInterval = null, List<DayOfWeek>? repeatDays = null)
        {
            var id = Guid.NewGuid();
            var reminder = new Reminder
            {
                Id = id,
                Title = title,
                Message = message,
                RemindAt = remindAt,
                Repeat = repeat,
                RepeatInterval = repeatInterval,
                RepeatDays = repeatDays,
                IsActive = true,
                LastTriggered = null
            };

            lock (_lockObject)
            {
                _activeReminders[id] = reminder;
            }

            return id;
        }

        public bool UpdateReminder(Guid reminderId, DateTime newTime)
        {
            lock (_lockObject)
            {
                if (_activeReminders.TryGetValue(reminderId, out var reminder))
                {
                    reminder.RemindAt = newTime;
                    return true;
                }
            }
            return false;
        }

        public bool DeleteReminder(Guid reminderId)
        {
            lock (_lockObject)
            {
                return _activeReminders.Remove(reminderId);
            }
        }

        public bool PauseReminder(Guid reminderId)
        {
            lock (_lockObject)
            {
                if (_activeReminders.TryGetValue(reminderId, out var reminder))
                {
                    reminder.IsActive = false;
                    return true;
                }
            }
            return false;
        }

        public bool ResumeReminder(Guid reminderId)
        {
            lock (_lockObject)
            {
                if (_activeReminders.TryGetValue(reminderId, out var reminder))
                {
                    reminder.IsActive = true;
                    return true;
                }
            }
            return false;
        }

        public IEnumerable<Reminder> GetActiveReminders()
        {
            lock (_lockObject)
            {
                return _activeReminders.Values.Where(r => r.IsActive).ToList();
            }
        }

        public IEnumerable<ScheduledNotification> GetScheduledNotifications()
        {
            lock (_lockObject)
            {
                return _scheduledNotifications.Values.Where(n => !n.IsTriggered).ToList();
            }
        }

        public void ClearAllNotifications()
        {
            System.Diagnostics.Debug.WriteLine("[Notification] Cleared all notifications");
        }

        public void RemoveNotification(string tag)
        {
            System.Diagnostics.Debug.WriteLine($"[Notification] Removed: {tag}");
        }

        private void CheckReminders(object? state)
        {
            var now = DateTime.Now;

            List<Reminder> remindersToTrigger;
            lock (_lockObject)
            {
                remindersToTrigger = _activeReminders.Values
                    .Where(r => r.IsActive && ShouldTriggerReminder(r, now))
                    .ToList();
            }

            foreach (var reminder in remindersToTrigger)
            {
                TriggerReminder(reminder);
            }

            List<ScheduledNotification> notificationsToTrigger;
            lock (_lockObject)
            {
                notificationsToTrigger = _scheduledNotifications.Values
                    .Where(n => !n.IsTriggered && n.ScheduledTime <= now)
                    .ToList();
            }

            foreach (var notification in notificationsToTrigger)
            {
                TriggerScheduledNotification(notification);
            }
        }

        private bool ShouldTriggerReminder(Reminder reminder, DateTime now)
        {
            if (reminder.RemindAt > now)
                return false;

            if (reminder.LastTriggered == null)
                return true;

            if (!reminder.Repeat)
                return false;

            var timeSinceLastTrigger = now - reminder.LastTriggered.Value;
            if (reminder.RepeatDays != null && reminder.RepeatDays.Count > 0)
            {
                if (!reminder.RepeatDays.Contains(now.DayOfWeek))
                    return false;
            }

            if (reminder.RepeatInterval.HasValue)
            {
                return timeSinceLastTrigger >= reminder.RepeatInterval.Value;
            }

            return timeSinceLastTrigger >= TimeSpan.FromDays(1);
        }

        private void TriggerReminder(Reminder reminder)
        {
            ShowNotification(reminder.Title, reminder.Message, $"reminder-{reminder.Id}", NotificationType.Reminder);

            ReminderTriggered?.Invoke(this, new ReminderEventArgs
            {
                ReminderId = reminder.Id,
                Title = reminder.Title,
                Message = reminder.Message,
                TriggeredAt = DateTime.Now
            });

            reminder.LastTriggered = DateTime.Now;

            if (!reminder.Repeat)
            {
                reminder.IsActive = false;
            }
        }

        private void TriggerScheduledNotification(ScheduledNotification notification)
        {
            ShowNotification(notification.Title, notification.Message, $"scheduled-{notification.Id}", notification.Type);

            notification.IsTriggered = true;

            if (notification.Repeat && notification.RepeatInterval.HasValue)
            {
                var nextTime = notification.ScheduledTime + notification.RepeatInterval.Value;
                ScheduleNotification(notification.Title, notification.Message, nextTime, notification.Type, true, notification.RepeatInterval);
            }
        }

        private void CleanupExpiredNotifications(object? state)
        {
            var now = DateTime.Now;

            lock (_lockObject)
            {
                var expiredNotifications = _scheduledNotifications.Values
                    .Where(n => n.IsTriggered && !n.Repeat && n.ScheduledTime < now.AddDays(-1))
                    .Select(n => n.Id)
                    .ToList();

                foreach (var id in expiredNotifications)
                {
                    _scheduledNotifications.Remove(id);
                }

                var expiredReminders = _activeReminders.Values
                    .Where(r => !r.IsActive && r.RemindAt < now.AddDays(-7))
                    .Select(r => r.Id)
                    .ToList();

                foreach (var id in expiredReminders)
                {
                    _activeReminders.Remove(id);
                }
            }
        }

        private Task LoadScheduledNotificationsAsync() => Task.CompletedTask;
        private Task LoadRemindersAsync() => Task.CompletedTask;

        public void Dispose()
        {
            if (_disposed)
                return;

            _reminderCheckTimer?.Dispose();
            _cleanupTimer?.Dispose();

            _disposed = true;
        }
    }

    public class ScheduledNotification
    {
        public Guid Id { get; set; }
        public string Title { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public DateTime ScheduledTime { get; set; }
        public NotificationType Type { get; set; }
        public bool Repeat { get; set; }
        public TimeSpan? RepeatInterval { get; set; }
        public bool IsTriggered { get; set; }
    }

    public class Reminder
    {
        public Guid Id { get; set; }
        public string Title { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public DateTime RemindAt { get; set; }
        public bool Repeat { get; set; }
        public TimeSpan? RepeatInterval { get; set; }
        public List<DayOfWeek>? RepeatDays { get; set; }
        public bool IsActive { get; set; }
        public DateTime? LastTriggered { get; set; }
    }

    public enum NotificationType
    {
        Info,
        Success,
        Warning,
        Error,
        Reminder
    }

    public class NotificationEventArgs : EventArgs
    {
        public string Tag { get; set; } = string.Empty;
        public DateTime Timestamp { get; set; }
    }

    public class ReminderEventArgs : EventArgs
    {
        public Guid ReminderId { get; set; }
        public string Title { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public DateTime TriggeredAt { get; set; }
    }

    public class NotificationErrorEventArgs : EventArgs
    {
        public string Operation { get; set; } = string.Empty;
        public string Message { get; set; } = string.Empty;
        public Exception? Exception { get; set; }
        public int ErrorCode { get; set; }
    }
}
