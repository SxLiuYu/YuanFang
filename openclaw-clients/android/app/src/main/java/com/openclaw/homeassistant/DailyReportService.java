package com.openclaw.homeassistant;

import android.content.Context;
import android.content.SharedPreferences;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

/**
 * 每日报告服务
 * 功能：生成用户每日生活报告
 */
public class DailyReportService {
    
    private static final String PREFS_NAME = "daily_report";
    private final Context context;
    private final SharedPreferences prefs;
    private final SimpleDateFormat dateFormat;
    
    public DailyReportService(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        this.dateFormat = new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault());
    }
    
    /**
     * 生成今日报告
     */
    public String generateTodayReport() {
        StringBuilder report = new StringBuilder();
        String today = dateFormat.format(new Date());
        
        report.append("📅 ").append(today).append(" 每日报告\n\n");
        
        // 睡眠情况
        report.append(generateSleepReport());
        
        // 饮食情况
        report.append(generateMealReport());
        
        // 屏幕使用时间
        report.append(generateScreenTimeReport());
        
        // 健康提醒统计
        report.append(generateHealthStats());
        
        // AI 建议
        report.append(generateAISuggestion());
        
        return report.toString();
    }
    
    /**
     * 睡眠报告
     */
    private String generateSleepReport() {
        int sleepHour = prefs.getInt("sleep_hour_" + dateFormat.format(new Date()), 0);
        int wakeHour = prefs.getInt("wakeup_hour_" + dateFormat.format(new Date()), 0);
        
        StringBuilder sb = new StringBuilder();
        sb.append("😴 睡眠情况\n");
        sb.append("━━━━━━━━━━━━━━━━\n");
        
        if (sleepHour > 0 && wakeHour > 0) {
            int duration = wakeHour - sleepHour;
            if (duration < 0) duration += 24;
            sb.append("入睡时间：").append(String.format("%02d:00", sleepHour)).append("\n");
            sb.append("起床时间：").append(String.format("%02d:00", wakeHour)).append("\n");
            sb.append("睡眠时长：").append(duration).append("小时\n");
            
            if (duration >= 7 && duration <= 9) {
                sb.append("评价：✅ 睡眠质量良好\n");
            } else if (duration < 6) {
                sb.append("评价：⚠️ 睡眠不足，今晚早点休息\n");
            } else {
                sb.append("评价：⚠️ 睡得有点多\n");
            }
        } else {
            sb.append("数据不足，请记得记录作息时间\n");
        }
        
        sb.append("\n");
        return sb.toString();
    }
    
    /**
     * 饮食报告
     */
    private String generateMealReport() {
        boolean breakfast = prefs.getBoolean("breakfast_" + dateFormat.format(new Date()), false);
        boolean lunch = prefs.getBoolean("lunch_" + dateFormat.format(new Date()), false);
        boolean dinner = prefs.getBoolean("dinner_" + dateFormat.format(new Date()), false);
        
        StringBuilder sb = new StringBuilder();
        sb.append("🍱 饮食情况\n");
        sb.append("━━━━━━━━━━━━━━━━\n");
        
        int mealCount = 0;
        if (breakfast) mealCount++;
        if (lunch) mealCount++;
        if (dinner) mealCount++;
        
        sb.append("早餐：").append(breakfast ? "✅" : "❌").append("\n");
        sb.append("午餐：").append(lunch ? "✅" : "❌").append("\n");
        sb.append("晚餐：").append(dinner ? "✅" : "❌").append("\n");
        sb.append("总计：").append(mealCount).append("/3 餐\n");
        
        if (mealCount == 3) {
            sb.append("评价：✅ 饮食规律\n");
        } else if (mealCount >= 2) {
            sb.append("评价：👍 基本正常\n");
        } else {
            sb.append("评价：⚠️ 饮食不规律，注意身体\n");
        }
        
        sb.append("\n");
        return sb.toString();
    }
    
    /**
     * 屏幕使用时间报告
     */
    private String generateScreenTimeReport() {
        DeviceDataReader reader = new DeviceDataReader(context);
        String usage = reader.getFormattedAppUsage();
        
        StringBuilder sb = new StringBuilder();
        sb.append("📱 屏幕使用\n");
        sb.append("━━━━━━━━━━━━━━━━\n");
        sb.append(usage.isEmpty() ? "数据不足" : usage);
        sb.append("\n\n");
        return sb.toString();
    }
    
    /**
     * 健康提醒统计
     */
    private String generateHealthStats() {
        int waterCount = prefs.getInt("water_count_" + dateFormat.format(new Date()), 0);
        int restCount = prefs.getInt("rest_count_" + dateFormat.format(new Date()), 0);
        
        StringBuilder sb = new StringBuilder();
        sb.append("💪 健康提醒\n");
        sb.append("━━━━━━━━━━━━━━━━\n");
        sb.append("喝水提醒：").append(waterCount).append("次\n");
        sb.append("休息提醒：").append(restCount).append("次\n");
        sb.append("\n");
        return sb.toString();
    }
    
    /**
     * AI 建议
     */
    private String generateAISuggestion() {
        StringBuilder sb = new StringBuilder();
        sb.append("🤖 AI 小建议\n");
        sb.append("━━━━━━━━━━━━━━━━\n");
        
        // 根据数据生成建议
        boolean breakfast = prefs.getBoolean("breakfast_" + dateFormat.format(new Date()), false);
        int waterCount = prefs.getInt("water_count_" + dateFormat.format(new Date()), 0);
        
        if (!breakfast) {
            sb.append("• 明天记得吃早餐哦\n");
        }
        if (waterCount < 4) {
            sb.append("• 喝水有点少，明天多喝点水\n");
        }
        
        sb.append("• 继续保持好习惯！\n");
        
        return sb.toString();
    }
    
    // ============== 记录数据 ==============
    
    public void recordSleep(int hour) {
        prefs.edit().putInt("sleep_hour_" + dateFormat.format(new Date()), hour).apply();
    }
    
    public void recordWakeUp(int hour) {
        prefs.edit().putInt("wakeup_hour_" + dateFormat.format(new Date()), hour).apply();
    }
    
    public void recordBreakfast() {
        prefs.edit().putBoolean("breakfast_" + dateFormat.format(new Date()), true).apply();
    }
    
    public void recordLunch() {
        prefs.edit().putBoolean("lunch_" + dateFormat.format(new Date()), true).apply();
    }
    
    public void recordDinner() {
        prefs.edit().putBoolean("dinner_" + dateFormat.format(new Date()), true).apply();
    }
    
    public void recordWater() {
        String key = "water_count_" + dateFormat.format(new Date());
        int count = prefs.getInt(key, 0);
        prefs.edit().putInt(key, count + 1).apply();
    }
    
    public void recordRest() {
        String key = "rest_count_" + dateFormat.format(new Date());
        int count = prefs.getInt(key, 0);
        prefs.edit().putInt(key, count + 1).apply();
    }
    
    /**
     * 获取连续记录天数
     */
    public int getStreakDays() {
        int streak = prefs.getInt("streak_days", 0);
        String lastDate = prefs.getString("last_report_date", "");
        String today = dateFormat.format(new Date());
        
        if (!today.equals(lastDate)) {
            // 检查是否是昨天
            // 简化处理，直接返回当前连续天数
        }
        
        return streak;
    }
}
