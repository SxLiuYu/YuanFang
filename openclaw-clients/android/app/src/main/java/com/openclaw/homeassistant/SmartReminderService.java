package com.openclaw.homeassistant;

import android.content.Context;
import android.content.SharedPreferences;

import java.util.Map;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

/**
 * 智能提醒服务
 * 功能：根据用户习惯和场景智能触发提醒
 */
public class SmartReminderService {
    
    private static final String TAG = "SmartReminderService";
    private static final String PREFS_NAME = "smart_reminders";
    
    private final Context context;
    private final SharedPreferences prefs;
    
    public SmartReminderService(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }
    
    // ============== 智能场景检测 ==============
    
    /**
     * 检测是否应该提醒用户休息
     * 基于应用使用时间和时间段
     */
    public boolean shouldRemindRest() {
        long screenTime = getContinuousScreenTime();
        int hour = java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY);
        
        // 连续使用超过 1 小时，且不是深夜
        return screenTime > 60 * 60 * 1000 && hour > 6 && hour < 23;
    }
    
    /**
     * 检测是否应该提醒喝水
     */
    public boolean shouldRemindWater() {
        long lastWaterTime = prefs.getLong("last_water_time", 0);
        long now = System.currentTimeMillis();
        return (now - lastWaterTime) > 2 * 60 * 60 * 1000; // 2 小时没喝水
    }
    
    /**
     * 检测是否应该提醒吃饭
     */
    public boolean shouldRemindMeal() {
        int hour = java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY);
        long lastMealTime = prefs.getLong("last_meal_time", 0);
        long now = System.currentTimeMillis();
        
        // 早餐时间 7-9 点
        if (hour >= 7 && hour <= 9 && (now - lastMealTime) > 12 * 60 * 60 * 1000) {
            return true;
        }
        // 午餐时间 11-13 点
        if (hour >= 11 && hour <= 13 && (now - lastMealTime) > 4 * 60 * 60 * 1000) {
            return true;
        }
        // 晚餐时间 17-20 点
        if (hour >= 17 && hour <= 20 && (now - lastMealTime) > 5 * 60 * 60 * 1000) {
            return true;
        }
        return false;
    }
    
    /**
     * 检测是否应该提醒睡觉
     */
    public boolean shouldRemindSleep() {
        int hour = java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY);
        int minute = java.util.Calendar.getInstance().get(java.util.Calendar.MINUTE);
        
        // 晚上 10:30-11:30，且手机还在使用
        return (hour == 22 && minute >= 30) || (hour == 23 && minute <= 30);
    }
    
    /**
     * 检测低电量 - 临时实现
     */
    public boolean isLowBattery() {
        // TODO: 实现电量检测
        return false;
    }
    
    /**
     * 检测是否长时间未充电 - 临时实现
     */
    public boolean shouldRemindCharge() {
        // TODO: 实现充电检测
        return false;
    }
    
    // ============== 智能建议 ==============
    
    /**
     * 根据时间和场景生成智能建议
     */
    public String getSmartSuggestion() {
        int hour = java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY);
        StringBuilder suggestion = new StringBuilder();
        
        // 早晨建议
        if (hour >= 6 && hour <= 8) {
            suggestion.append("☀️ 早上好！今天天气不错，记得吃早餐。\n");
        }
        
        // 工作时段建议
        if (hour >= 9 && hour <= 11) {
            if (shouldRemindRest()) {
                suggestion.append("💺 工作很久了，起来活动一下吧。\n");
            }
        }
        
        // 午休建议
        if (hour >= 12 && hour <= 13) {
            suggestion.append("🍱 该吃午饭了，午休一下效率更高。\n");
        }
        
        // 下午建议
        if (hour >= 15 && hour <= 16) {
            if (shouldRemindWater()) {
                suggestion.append("💧 下午容易犯困，喝杯水提提神。\n");
            }
        }
        
        // 傍晚建议
        if (hour >= 17 && hour <= 18) {
            suggestion.append("🌆 快下班了，规划一下晚上的安排吧。\n");
        }
        
        // 晚上建议
        if (hour >= 20 && hour <= 21) {
            suggestion.append("📚 晚上适合学习或放松，别刷太多手机。\n");
        }
        
        // 睡前建议
        if (hour >= 22) {
            suggestion.append("🌙 时间不早了，准备休息吧，明天还要早起。\n");
        }
        
        return suggestion.toString();
    }
    
    // ============== 数据统计 ==============
    
    /**
     * 获取连续使用时间
     */
    public long getContinuousScreenTime() {
        DeviceDataReader reader = new DeviceDataReader(context);
        Map<String, Long> usage = reader.getAppUsageStats();
        
        if (usage == null) {
            return 0;
        }
        
        long total = 0;
        for (Long time : usage.values()) {
            total += time;
        }
        return total;
    }
    
    /**
     * 获取今日屏幕使用时间报告
     */
    public String getScreenTimeReport() {
        DeviceDataReader reader = new DeviceDataReader(context);
        String usage = reader.getFormattedAppUsage();
        
        long totalMinutes = getContinuousScreenTime() / 60000;
        int hours = (int)(totalMinutes / 60);
        int minutes = (int)(totalMinutes % 60);
        
        StringBuilder report = new StringBuilder();
        report.append("📊 今日屏幕使用时间报告\n\n");
        report.append("总时长：").append(hours).append("小时").append(minutes).append("分钟\n\n");
        
        if (hours > 6) {
            report.append("⚠️ 使用时间较长，建议适当休息。\n");
        } else if (hours > 4) {
            report.append("✅ 使用时间适中。\n");
        } else {
            report.append("👍 使用时间很健康！\n");
        }
        
        report.append("\n常用应用：\n").append(usage);
        
        return report.toString();
    }
    
    // ============== 记录行为 ==============
    
    /**
     * 记录用户吃饭时间
     */
    public void recordMeal() {
        prefs.edit().putLong("last_meal_time", System.currentTimeMillis()).apply();
    }
    
    /**
     * 记录用户喝水时间
     */
    public void recordWater() {
        prefs.edit().putLong("last_water_time", System.currentTimeMillis()).apply();
    }
    
    /**
     * 记录用户休息时间
     */
    public void recordRest() {
        prefs.edit().putLong("last_rest_time", System.currentTimeMillis()).apply();
    }
    
    // ============== 个性化学习 ==============
    
    /**
     * 学习用户作息习惯
     */
    public void learnUserHabit(String habitType, int hour) {
        String key = "habit_" + habitType + "_hour";
        int currentAvg = prefs.getInt(key, hour);
        int count = prefs.getInt("habit_" + habitType + "_count", 0);
        
        // 移动平均
        int newAvg = (currentAvg * count + hour) / (count + 1);
        
        prefs.edit()
            .putInt(key, newAvg)
            .putInt("habit_" + habitType + "_count", count + 1)
            .apply();
        
        Log.d(TAG, "学习用户习惯：" + habitType + " = " + newAvg);
    }
    
    /**
     * 获取用户习惯的作息时间
     */
    public int getUserHabitHour(String habitType) {
        return prefs.getInt("habit_" + habitType + "_hour", 0);
    }
}
