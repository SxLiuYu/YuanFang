package com.openclaw.homeassistant;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * 家庭任务板服务
 * 支持任务分配、积分系统、排行榜
 */
public class TaskService {
    
    private static final String TAG = "TaskService";
    private static final String PREFS_NAME = "family_tasks";
    
    private final Context context;
    private final SharedPreferences prefs;
    private final SimpleDateFormat dateFormat;
    
    public interface TaskListener {
        void onTaskCompleted(String taskName, String memberName, int points);
        void onPointsUpdated(String memberName, int totalPoints);
    }
    
    private static TaskListener listener;
    
    public TaskService(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        this.dateFormat = new SimpleDateFormat("yyyy-MM-dd", Locale.CHINA);
    }
    
    public static void setListener(TaskListener listener) {
        TaskService.listener = listener;
    }
    
    /**
     * 创建任务
     */
    public void createTask(String taskName, String description, String assignedTo, 
                          int points, String dueDate, String repeatRule, String createdBy) {
        Log.d(TAG, "创建任务：" + taskName + " -> " + assignedTo);
        
        try {
            JSONObject task = new JSONObject();
            task.put("id", generateId());
            task.put("name", taskName);
            task.put("description", description != null ? description : "");
            task.put("assigned_to", assignedTo);
            task.put("points", points);
            task.put("due_date", dueDate != null ? dueDate : "");
            task.put("repeat_rule", repeatRule != null ? repeatRule : "");
            task.put("status", "pending");
            task.put("created_by", createdBy);
            task.put("created_at", dateFormat.format(new Date()));
            
            String key = "task_" + task.getString("id");
            prefs.edit().putString(key, task.toString()).apply();
            
            // 如果是每日重复任务，设置提醒
            if (repeatRule != null && repeatRule.contains("daily")) {
                scheduleTaskReminder(task.getString("id"), taskName, "08:00");
            }
            
        } catch (Exception e) {
            Log.e(TAG, "创建任务失败", e);
        }
    }
    
    /**
     * 完成任务
     */
    public void completeTask(String taskId, String completedBy) {
        Log.d(TAG, "完成任务：" + taskId);
        
        try {
            String key = "task_" + taskId;
            String taskStr = prefs.getString(key, null);
            
            if (taskStr != null) {
                JSONObject task = new JSONObject(taskStr);
                task.put("status", "completed");
                task.put("completed_at", dateFormat.format(new Date()));
                task.put("completed_by", completedBy);
                
                prefs.edit().putString(key, task.toString()).apply();
                
                // 添加积分
                int points = task.getInt("points");
                String memberName = task.getString("assigned_to");
                addPoints(memberName, points, "完成任务：" + task.getString("name"));
                
                // 通知监听器
                if (listener != null) {
                    listener.onTaskCompleted(task.getString("name"), memberName, points);
                }
                
                // 发送通知
                NotificationHelper.sendHealthNotification(
                    context,
                    "✅ 任务完成",
                    memberName + " 完成了 \"" + task.getString("name") + "\"，获得 " + points + " 积分"
                );
                
                // 如果是重复任务，创建下一个周期的任务
                String repeatRule = task.optString("repeat_rule", "");
                if (!repeatRule.isEmpty()) {
                    createNextRecurringTask(task, repeatRule);
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "完成任务失败", e);
        }
    }
    
    /**
     * 创建下一个周期的重复任务
     */
    private void createNextRecurringTask(JSONObject task, String repeatRule) {
        try {
            // 解析重复规则
            if (repeatRule.contains("daily")) {
                // 每日重复，创建明天的任务
                String nextDueDate = calculateNextDate(1);
                createTask(
                    task.getString("name"),
                    task.getString("description"),
                    task.getString("assigned_to"),
                    task.getInt("points"),
                    nextDueDate,
                    repeatRule,
                    task.getString("created_by")
                );
            } else if (repeatRule.contains("weekly")) {
                // 每周重复，创建下周的任务
                String nextDueDate = calculateNextDate(7);
                createTask(
                    task.getString("name"),
                    task.getString("description"),
                    task.getString("assigned_to"),
                    task.getInt("points"),
                    nextDueDate,
                    repeatRule,
                    task.getString("created_by")
                );
            }
        } catch (Exception e) {
            Log.e(TAG, "创建重复任务失败", e);
        }
    }
    
    private String calculateNextDate(int daysToAdd) {
        // 简化实现，实际应使用 Calendar 计算
        return dateFormat.format(new Date(System.currentTimeMillis() + daysToAdd * 86400000));
    }
    
    /**
     * 添加积分
     */
    public void addPoints(String memberName, int points, String reason) {
        Log.d(TAG, "添加积分：" + memberName + " +" + points);
        
        try {
            // 获取当前积分
            int currentPoints = getMemberPoints(memberName);
            int newPoints = currentPoints + points;
            
            // 更新积分
            prefs.edit().putInt("points_" + memberName, newPoints).apply();
            
            // 记录积分日志
            JSONObject log = new JSONObject();
            log.put("member", memberName);
            log.put("points", points);
            log.put("reason", reason);
            log.put("timestamp", System.currentTimeMillis());
            
            String logKey = "points_log_" + System.currentTimeMillis();
            prefs.edit().putString(logKey, log.toString()).apply();
            
            // 通知监听器
            if (listener != null) {
                listener.onPointsUpdated(memberName, newPoints);
            }
            
        } catch (Exception e) {
            Log.e(TAG, "添加积分失败", e);
        }
    }
    
    /**
     * 获取成员积分
     */
    public int getMemberPoints(String memberName) {
        return prefs.getInt("points_" + memberName, 0);
    }
    
    /**
     * 获取积分排行榜
     */
    public List<Map<String, Object>> getLeaderboard() {
        List<Map<String, Object>> leaderboard = new ArrayList<>();
        
        // 获取所有成员积分（简化实现，实际应维护成员列表）
        String[] members = {"爸爸", "妈妈", "孩子"};
        
        for (String member : members) {
            int points = getMemberPoints(member);
            
            Map<String, Object> data = new HashMap<>();
            data.put("name", member);
            data.put("points", points);
            
            leaderboard.add(data);
        }
        
        // 按积分排序
        leaderboard.sort((a, b) -> (Integer)b.get("points") - (Integer)a.get("points"));
        
        return leaderboard;
    }
    
    /**
     * 获取待办任务列表
     */
    public List<Map<String, Object>> getPendingTasks() {
        List<Map<String, Object>> tasks = new ArrayList<>();
        
        Map<String, ?> all = prefs.getAll();
        for (Map.Entry<String, ?> entry : all.entrySet()) {
            if (entry.getKey().startsWith("task_")) {
                try {
                    JSONObject task = new JSONObject(entry.getValue().toString());
                    if ("pending".equals(task.getString("status"))) {
                        Map<String, Object> taskData = new HashMap<>();
                        taskData.put("id", task.getString("id"));
                        taskData.put("name", task.getString("name"));
                        taskData.put("assigned_to", task.getString("assigned_to"));
                        taskData.put("points", task.getInt("points"));
                        taskData.put("due_date", task.optString("due_date", ""));
                        tasks.add(taskData);
                    }
                } catch (Exception e) {
                    // ignore
                }
            }
        }
        
        return tasks;
    }
    
    /**
     * 兑换奖励
     */
    public void redeemReward(String memberName, String rewardName, int costPoints) {
        int currentPoints = getMemberPoints(memberName);
        
        if (currentPoints >= costPoints) {
            // 扣除积分
            addPoints(memberName, -costPoints, "兑换奖励：" + rewardName);
            
            // 发送通知
            NotificationHelper.sendHealthNotification(
                context,
                "🎁 奖励兑换",
                memberName + " 兑换了 \"" + rewardName + "\"，消耗 " + costPoints + " 积分"
            );
        } else {
            NotificationHelper.sendHealthNotification(
                context,
                "❌ 积分不足",
                "需要 " + costPoints + " 积分，当前只有 " + currentPoints + " 积分"
            );
        }
    }
    
    /**
     * 生成唯一 ID
     */
    private String generateId() {
        return String.valueOf(System.currentTimeMillis());
    }
    
    /**
     * 预设常用任务模板
     */
    public void createDefaultTasks() {
        // 每日任务
        createTask("整理床铺", "", "孩子", 5, "", "daily", "系统");
        createTask("洗碗", "", "爸爸", 10, "", "daily", "系统");
        createTask("倒垃圾", "", "妈妈", 8, "", "daily", "系统");
        
        // 每周任务
        createTask("大扫除", "全屋清洁", "全家", 50, "", "weekly", "系统");
        createTask("超市采购", "购买一周食材", "妈妈", 30, "", "weekly", "系统");
    }
    
    // ========== 兼容旧代码的方法 ==========
    
    private boolean running = false;
    
    public boolean isRunning() {
        return running;
    }
    
    public void start() {
        running = true;
        Log.d(TAG, "任务服务已启动");
    }
    
    public void stop() {
        running = false;
        Log.d(TAG, "任务服务已停止");
    }

    // ========== 任务提醒功能 ==========

    /**
     * 设置任务提醒
     * @param taskId 任务ID
     * @param taskName 任务名称
     * @param time 提醒时间 (格式: "HH:mm")
     */
    public void scheduleTaskReminder(String taskId, String taskName, String time) {
        try {
            AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);

            // 解析时间
            String[] parts = time.split(":");
            int hour = Integer.parseInt(parts[0]);
            int minute = Integer.parseInt(parts[1]);

            // 设置提醒时间
            Calendar calendar = Calendar.getInstance();
            calendar.set(Calendar.HOUR_OF_DAY, hour);
            calendar.set(Calendar.MINUTE, minute);
            calendar.set(Calendar.SECOND, 0);

            // 如果时间已过，设置为明天
            if (calendar.getTimeInMillis() < System.currentTimeMillis()) {
                calendar.add(Calendar.DAY_OF_MONTH, 1);
            }

            // 创建 Intent
            Intent intent = new Intent(context, TaskReminderReceiver.class);
            intent.putExtra("task_id", taskId);
            intent.putExtra("task_name", taskName);

            // 创建 PendingIntent
            PendingIntent pendingIntent = PendingIntent.getBroadcast(
                    context,
                    taskId.hashCode(),
                    intent,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
            );

            // 设置每日重复提醒
            alarmManager.setRepeating(
                    AlarmManager.RTC_WAKEUP,
                    calendar.getTimeInMillis(),
                    AlarmManager.INTERVAL_DAY,
                    pendingIntent
            );

            Log.d(TAG, "已设置任务提醒：" + taskName + " - " + time);

        } catch (Exception e) {
            Log.e(TAG, "设置任务提醒失败", e);
        }
    }

    /**
     * 取消任务提醒
     */
    public void cancelTaskReminder(String taskId, String taskName) {
        try {
            AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);

            Intent intent = new Intent(context, TaskReminderReceiver.class);
            intent.putExtra("task_id", taskId);
            intent.putExtra("task_name", taskName);

            PendingIntent pendingIntent = PendingIntent.getBroadcast(
                    context,
                    taskId.hashCode(),
                    intent,
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
            );

            alarmManager.cancel(pendingIntent);
            Log.d(TAG, "已取消任务提醒：" + taskName);

        } catch (Exception e) {
            Log.e(TAG, "取消任务提醒失败", e);
        }
    }

    /**
     * 检查今日是否有未完成任务并发送提醒
     */
    public void checkAndRemindPendingTasks() {
        List<Map<String, Object>> pendingTasks = getPendingTasks();

        if (!pendingTasks.isEmpty()) {
            StringBuilder sb = new StringBuilder();
            sb.append("今日待办任务：\n");

            for (Map<String, Object> task : pendingTasks) {
                sb.append("• ").append(task.get("name"))
                  .append(" (").append(task.get("assigned_to")).append(")\n");
            }

            NotificationHelper.sendHealthNotification(
                    context,
                    "📋 今日待办提醒",
                    sb.toString()
            );
        }
    }
}
