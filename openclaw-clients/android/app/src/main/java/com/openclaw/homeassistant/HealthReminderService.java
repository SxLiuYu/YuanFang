package com.openclaw.homeassistant;

import android.app.AlarmManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.os.Build;
import android.os.PowerManager;
import android.util.Log;

import java.util.Calendar;

/**
 * 健康提醒服务
 * 功能：久坐、喝水、眼保健提醒
 */
public class HealthReminderService {
    
    private static final String TAG = "HealthReminderService";
    private static final String PREFS_NAME = "health_reminders";
    
    private final Context context;
    private final AlarmManager alarmManager;
    private final PowerManager powerManager;
    private final SharedPreferences prefs;
    
    // 默认间隔 (分钟)
    private static final int DEFAULT_SIT_INTERVAL = 60;      // 久坐：60 分钟
    private static final int DEFAULT_WATER_INTERVAL = 120;   // 喝水：120 分钟
    private static final int DEFAULT_EYE_INTERVAL = 45;      // 眼保健：45 分钟
    
    // 开关状态
    private boolean sitReminderEnabled = true;
    private boolean waterReminderEnabled = true;
    private boolean eyeReminderEnabled = true;
    
    // 新增：生活提醒开关
    private boolean breakfastReminderEnabled = false;
    private boolean lunchReminderEnabled = true;
    private boolean dinnerReminderEnabled = true;
    private boolean sleepReminderEnabled = true;
    private boolean wakeUpReminderEnabled = true;
    
    // 间隔设置
    private int sitInterval = DEFAULT_SIT_INTERVAL;
    private int waterInterval = DEFAULT_WATER_INTERVAL;
    private int eyeInterval = DEFAULT_EYE_INTERVAL;
    
    // 工作时间段
    private int workStartHour = 9;
    private int workEndHour = 18;
    
    // 生活提醒时间
    private int breakfastHour = 8;
    private int breakfastMinute = 0;
    private int lunchHour = 12;
    private int lunchMinute = 0;
    private int dinnerHour = 18;
    private int dinnerMinute = 30;
    private int sleepHour = 23;
    private int sleepMinute = 0;
    private int wakeUpHour = 7;
    private int wakeUpMinute = 30;
    
    public interface HealthReminderListener {
        void onSitReminder();
        void onWaterReminder();
        void onEyeReminder();
        // 新增生活提醒
        void onBreakfastReminder();
        void onLunchReminder();
        void onDinnerReminder();
        void onSleepReminder();
        void onWakeUpReminder();
    }
    
    private static HealthReminderListener listener;
    
    public HealthReminderService(Context context) {
        this.context = context.getApplicationContext();
        this.alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        this.powerManager = (PowerManager) context.getSystemService(Context.POWER_SERVICE);
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        
        loadSettings();
    }
    
    public static void setListener(HealthReminderListener listener) {
        HealthReminderService.listener = listener;
    }
    
    /**
     * 加载设置
     */
    private void loadSettings() {
        sitReminderEnabled = prefs.getBoolean("sit_enabled", true);
        waterReminderEnabled = prefs.getBoolean("water_enabled", true);
        eyeReminderEnabled = prefs.getBoolean("eye_enabled", true);
        
        sitInterval = prefs.getInt("sit_interval", DEFAULT_SIT_INTERVAL);
        waterInterval = prefs.getInt("water_interval", DEFAULT_WATER_INTERVAL);
        eyeInterval = prefs.getInt("eye_interval", DEFAULT_EYE_INTERVAL);
        
        workStartHour = prefs.getInt("work_start", 9);
        workEndHour = prefs.getInt("work_end", 18);
        
        // 生活提醒设置
        breakfastReminderEnabled = prefs.getBoolean("breakfast_enabled", false);
        lunchReminderEnabled = prefs.getBoolean("lunch_enabled", true);
        dinnerReminderEnabled = prefs.getBoolean("dinner_enabled", true);
        sleepReminderEnabled = prefs.getBoolean("sleep_enabled", true);
        wakeUpReminderEnabled = prefs.getBoolean("wakeup_enabled", true);
        
        breakfastHour = prefs.getInt("breakfast_hour", 8);
        breakfastMinute = prefs.getInt("breakfast_minute", 0);
        lunchHour = prefs.getInt("lunch_hour", 12);
        lunchMinute = prefs.getInt("lunch_minute", 0);
        dinnerHour = prefs.getInt("dinner_hour", 18);
        dinnerMinute = prefs.getInt("dinner_minute", 30);
        sleepHour = prefs.getInt("sleep_hour", 23);
        sleepMinute = prefs.getInt("sleep_minute", 0);
        wakeUpHour = prefs.getInt("wakeup_hour", 7);
        wakeUpMinute = prefs.getInt("wakeup_minute", 30);
    }
    
    /**
     * 保存设置
     */
    public void saveSettings() {
        prefs.edit()
            .putBoolean("sit_enabled", sitReminderEnabled)
            .putBoolean("water_enabled", waterReminderEnabled)
            .putBoolean("eye_enabled", eyeReminderEnabled)
            .putInt("sit_interval", sitInterval)
            .putInt("water_interval", waterInterval)
            .putInt("eye_interval", eyeInterval)
            .putInt("work_start", workStartHour)
            .putInt("work_end", workEndHour)
            // 生活提醒设置
            .putBoolean("breakfast_enabled", breakfastReminderEnabled)
            .putBoolean("lunch_enabled", lunchReminderEnabled)
            .putBoolean("dinner_enabled", dinnerReminderEnabled)
            .putBoolean("sleep_enabled", sleepReminderEnabled)
            .putBoolean("wakeup_enabled", wakeUpReminderEnabled)
            .putInt("breakfast_hour", breakfastHour)
            .putInt("breakfast_minute", breakfastMinute)
            .putInt("lunch_hour", lunchHour)
            .putInt("lunch_minute", lunchMinute)
            .putInt("dinner_hour", dinnerHour)
            .putInt("dinner_minute", dinnerMinute)
            .putInt("sleep_hour", sleepHour)
            .putInt("sleep_minute", sleepMinute)
            .putInt("wakeup_hour", wakeUpHour)
            .putInt("wakeup_minute", wakeUpMinute)
            .apply();
    }
    
    /**
     * 启动所有提醒
     */
    public void startAllReminders() {
        loadSettings();
        
        if (sitReminderEnabled) startSitReminder();
        if (waterReminderEnabled) startWaterReminder();
        if (eyeReminderEnabled) startEyeReminder();
        
        // 生活提醒
        if (breakfastReminderEnabled) startBreakfastReminder();
        if (lunchReminderEnabled) startLunchReminder();
        if (dinnerReminderEnabled) startDinnerReminder();
        if (sleepReminderEnabled) startSleepReminder();
        if (wakeUpReminderEnabled) startWakeUpReminder();
        
        Log.d(TAG, "所有提醒已启动");
    }
    
    /**
     * 停止所有提醒
     */
    public void stopAllReminders() {
        stopSitReminder();
        stopWaterReminder();
        stopEyeReminder();
        stopBreakfastReminder();
        stopLunchReminder();
        stopDinnerReminder();
        stopSleepReminder();
        stopWakeUpReminder();
        
        Log.d(TAG, "所有提醒已停止");
    }
    
    // ============== 久坐提醒 ==============
    
    public void startSitReminder() {
        scheduleRepeatingAlarm("SIT_REMINDER", sitInterval);
        Log.d(TAG, "久坐提醒已启动：" + sitInterval + "分钟");
    }
    
    public void stopSitReminder() {
        cancelAlarm("SIT_REMINDER");
    }
    
    public void triggerSitReminder() {
        Log.d(TAG, "久坐提醒触发");
        if (listener != null) {
            listener.onSitReminder();
        }
    }
    
    // ============== 喝水提醒 ==============
    
    public void startWaterReminder() {
        scheduleRepeatingAlarm("WATER_REMINDER", waterInterval);
        Log.d(TAG, "喝水提醒已启动：" + waterInterval + "分钟");
    }
    
    public void stopWaterReminder() {
        cancelAlarm("WATER_REMINDER");
    }
    
    public void triggerWaterReminder() {
        Log.d(TAG, "喝水提醒触发");
        if (listener != null) {
            listener.onWaterReminder();
        }
    }
    
    // ============== 眼保健提醒 ==============
    
    public void startEyeReminder() {
        scheduleRepeatingAlarm("EYE_REMINDER", eyeInterval);
        Log.d(TAG, "眼保健提醒已启动：" + eyeInterval + "分钟");
    }
    
    public void stopEyeReminder() {
        cancelAlarm("EYE_REMINDER");
    }
    
    public void triggerEyeReminder() {
        Log.d(TAG, "眼保健提醒触发");
        if (listener != null) {
            listener.onEyeReminder();
        }
    }
    
    // ============== 闹钟调度 ==============
    
    private void scheduleRepeatingAlarm(String action, int intervalMinutes) {
        if (alarmManager == null) return;
        
        Intent intent = new Intent(context, HealthReminderReceiver.class);
        intent.setAction(action);
        
        PendingIntent pendingIntent = PendingIntent.getBroadcast(
            context, action.hashCode(), intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );
        
        // 取消旧的
        alarmManager.cancel(pendingIntent);
        
        // 计算下次触发时间 (下一个整点)
        Calendar calendar = Calendar.getInstance();
        calendar.set(Calendar.MINUTE, 0);
        calendar.set(Calendar.SECOND, 0);
        calendar.add(Calendar.MINUTE, intervalMinutes);
        
        // 检查是否在工作时间段
        if (!isWorkHours(calendar.get(Calendar.HOUR_OF_DAY))) {
            // 跳到下一个工作日开始
            calendar.set(Calendar.HOUR_OF_DAY, workStartHour);
            if (calendar.getTimeInMillis() <= System.currentTimeMillis()) {
                calendar.add(Calendar.DAY_OF_YEAR, 1);
            }
        }
        
        // 设置闹钟
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            alarmManager.setExactAndAllowWhileIdle(
                AlarmManager.RTC_WAKEUP,
                calendar.getTimeInMillis(),
                pendingIntent
            );
        } else {
            alarmManager.setExact(
                AlarmManager.RTC_WAKEUP,
                calendar.getTimeInMillis(),
                pendingIntent
            );
        }
    }
    
    private void cancelAlarm(String action) {
        if (alarmManager == null) return;
        
        Intent intent = new Intent(context, HealthReminderReceiver.class);
        intent.setAction(action);
        
        PendingIntent pendingIntent = PendingIntent.getBroadcast(
            context, action.hashCode(), intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );
        
        alarmManager.cancel(pendingIntent);
    }
    
    // ============== 工具方法 ==============
    
    private boolean isWorkHours(int hour) {
        return hour >= workStartHour && hour < workEndHour;
    }
    
    // ============== 生活提醒 ==============
    
    /**
     * 启动早餐提醒
     */
    public void startBreakfastReminder() {
        scheduleDailyAlarm("BREAKFAST_REMINDER", breakfastHour, breakfastMinute);
        Log.d(TAG, "早餐提醒已启动：" + breakfastHour + ":" + breakfastMinute);
    }
    
    public void stopBreakfastReminder() {
        cancelAlarm("BREAKFAST_REMINDER");
    }
    
    public void triggerBreakfastReminder() {
        Log.d(TAG, "早餐提醒触发");
        if (listener != null) listener.onBreakfastReminder();
    }
    
    /**
     * 启动午餐提醒
     */
    public void startLunchReminder() {
        scheduleDailyAlarm("LUNCH_REMINDER", lunchHour, lunchMinute);
        Log.d(TAG, "午餐提醒已启动：" + lunchHour + ":" + lunchMinute);
    }
    
    public void stopLunchReminder() {
        cancelAlarm("LUNCH_REMINDER");
    }
    
    public void triggerLunchReminder() {
        Log.d(TAG, "午餐提醒触发");
        if (listener != null) listener.onLunchReminder();
    }
    
    /**
     * 启动晚餐提醒
     */
    public void startDinnerReminder() {
        scheduleDailyAlarm("DINNER_REMINDER", dinnerHour, dinnerMinute);
        Log.d(TAG, "晚餐提醒已启动：" + dinnerHour + ":" + dinnerMinute);
    }
    
    public void stopDinnerReminder() {
        cancelAlarm("DINNER_REMINDER");
    }
    
    public void triggerDinnerReminder() {
        Log.d(TAG, "晚餐提醒触发");
        if (listener != null) listener.onDinnerReminder();
    }
    
    /**
     * 启动睡觉提醒
     */
    public void startSleepReminder() {
        scheduleDailyAlarm("SLEEP_REMINDER", sleepHour, sleepMinute);
        Log.d(TAG, "睡觉提醒已启动：" + sleepHour + ":" + sleepMinute);
    }
    
    public void stopSleepReminder() {
        cancelAlarm("SLEEP_REMINDER");
    }
    
    public void triggerSleepReminder() {
        Log.d(TAG, "睡觉提醒触发");
        if (listener != null) listener.onSleepReminder();
    }
    
    /**
     * 启动起床提醒
     */
    public void startWakeUpReminder() {
        scheduleDailyAlarm("WAKEUP_REMINDER", wakeUpHour, wakeUpMinute);
        Log.d(TAG, "起床提醒已启动：" + wakeUpHour + ":" + wakeUpMinute);
    }
    
    public void stopWakeUpReminder() {
        cancelAlarm("WAKEUP_REMINDER");
    }
    
    public void triggerWakeUpReminder() {
        Log.d(TAG, "起床提醒触发");
        if (listener != null) listener.onWakeUpReminder();
    }
    
    /**
     * 调度每日定时闹钟
     */
    private void scheduleDailyAlarm(String action, int hour, int minute) {
        if (alarmManager == null) return;
        
        Intent intent = new Intent(context, HealthReminderReceiver.class);
        intent.setAction(action);
        
        PendingIntent pendingIntent = PendingIntent.getBroadcast(
            context, action.hashCode(), intent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );
        
        // 取消旧的
        alarmManager.cancel(pendingIntent);
        
        // 计算下次触发时间
        Calendar calendar = Calendar.getInstance();
        calendar.set(Calendar.HOUR_OF_DAY, hour);
        calendar.set(Calendar.MINUTE, minute);
        calendar.set(Calendar.SECOND, 0);
        
        // 如果时间已过，设置为明天
        if (calendar.getTimeInMillis() <= System.currentTimeMillis()) {
            calendar.add(Calendar.DAY_OF_YEAR, 1);
        }
        
        // 设置闹钟
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            alarmManager.setExactAndAllowWhileIdle(
                AlarmManager.RTC_WAKEUP,
                calendar.getTimeInMillis(),
                pendingIntent
            );
        } else {
            alarmManager.setExact(
                AlarmManager.RTC_WAKEUP,
                calendar.getTimeInMillis(),
                pendingIntent
            );
        }
    }
    
    // ============== Getter/Setter ==============
    
    public boolean isSitReminderEnabled() { return sitReminderEnabled; }
    public void setSitReminderEnabled(boolean enabled) { 
        this.sitReminderEnabled = enabled; 
        if (enabled) startSitReminder(); else stopSitReminder();
    }
    
    public boolean isWaterReminderEnabled() { return waterReminderEnabled; }
    public void setWaterReminderEnabled(boolean enabled) { 
        this.waterReminderEnabled = enabled; 
        if (enabled) startWaterReminder(); else stopWaterReminder();
    }
    
    public boolean isEyeReminderEnabled() { return eyeReminderEnabled; }
    public void setEyeReminderEnabled(boolean enabled) { 
        this.eyeReminderEnabled = enabled; 
        if (enabled) startEyeReminder(); else stopEyeReminder();
    }
    
    // 生活提醒 Getter/Setter
    public boolean isBreakfastReminderEnabled() { return breakfastReminderEnabled; }
    public void setBreakfastReminderEnabled(boolean enabled) { 
        this.breakfastReminderEnabled = enabled; 
        if (enabled) startBreakfastReminder(); else stopBreakfastReminder();
    }
    
    public boolean isLunchReminderEnabled() { return lunchReminderEnabled; }
    public void setLunchReminderEnabled(boolean enabled) { 
        this.lunchReminderEnabled = enabled; 
        if (enabled) startLunchReminder(); else stopLunchReminder();
    }
    
    public boolean isDinnerReminderEnabled() { return dinnerReminderEnabled; }
    public void setDinnerReminderEnabled(boolean enabled) { 
        this.dinnerReminderEnabled = enabled; 
        if (enabled) startDinnerReminder(); else stopDinnerReminder();
    }
    
    public boolean isSleepReminderEnabled() { return sleepReminderEnabled; }
    public void setSleepReminderEnabled(boolean enabled) { 
        this.sleepReminderEnabled = enabled; 
        if (enabled) startSleepReminder(); else stopSleepReminder();
    }
    
    public boolean isWakeUpReminderEnabled() { return wakeUpReminderEnabled; }
    public void setWakeUpReminderEnabled(boolean enabled) { 
        this.wakeUpReminderEnabled = enabled; 
        if (enabled) startWakeUpReminder(); else stopWakeUpReminder();
    }
    
    public int getSitInterval() { return sitInterval; }
    public void setSitInterval(int minutes) { 
        this.sitInterval = minutes; 
        if (sitReminderEnabled) startSitReminder();
    }
    
    public int getWaterInterval() { return waterInterval; }
    public void setWaterInterval(int minutes) { 
        this.waterInterval = minutes; 
        if (waterReminderEnabled) startWaterReminder();
    }
    
    public int getEyeInterval() { return eyeInterval; }
    public void setEyeInterval(int minutes) { 
        this.eyeInterval = minutes; 
        if (eyeReminderEnabled) startEyeReminder();
    }
    
    public int getWorkStartHour() { return workStartHour; }
    public void setWorkStartHour(int hour) { this.workStartHour = hour; }
    
    public int getWorkEndHour() { return workEndHour; }
    public void setWorkEndHour(int hour) { this.workEndHour = hour; }
    
    // 生活提醒时间 Getter/Setter
    public int getBreakfastHour() { return breakfastHour; }
    public void setBreakfastTime(int hour, int minute) { 
        this.breakfastHour = hour; 
        this.breakfastMinute = minute;
        if (breakfastReminderEnabled) startBreakfastReminder();
    }
    
    public int getLunchHour() { return lunchHour; }
    public void setLunchTime(int hour, int minute) { 
        this.lunchHour = hour; 
        this.lunchMinute = minute;
        if (lunchReminderEnabled) startLunchReminder();
    }
    
    public int getDinnerHour() { return dinnerHour; }
    public void setDinnerTime(int hour, int minute) { 
        this.dinnerHour = hour; 
        this.dinnerMinute = minute;
        if (dinnerReminderEnabled) startDinnerReminder();
    }
    
    public int getSleepHour() { return sleepHour; }
    public void setSleepTime(int hour, int minute) { 
        this.sleepHour = hour; 
        this.sleepMinute = minute;
        if (sleepReminderEnabled) startSleepReminder();
    }
    
    public int getWakeUpHour() { return wakeUpHour; }
    public void setWakeUpTime(int hour, int minute) { 
        this.wakeUpHour = hour; 
        this.wakeUpMinute = minute;
        if (wakeUpReminderEnabled) startWakeUpReminder();
    }
}
