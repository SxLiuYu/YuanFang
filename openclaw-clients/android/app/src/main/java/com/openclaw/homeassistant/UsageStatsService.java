package com.openclaw.homeassistant;

import android.content.Context;
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
 * 使用统计服务
 * 功能：统计规则触发次数/时间分布
 */
public class UsageStatsService {
    
    private static final String TAG = "UsageStatsService";
    private static final String PREFS_NAME = "usage_stats";
    
    private final Context context;
    private final SharedPreferences prefs;
    private final SimpleDateFormat dateFormat;
    private final SimpleDateFormat hourFormat;
    
    public UsageStatsService(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        this.dateFormat = new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault());
        this.hourFormat = new SimpleDateFormat("HH", Locale.getDefault());
    }
    
    /**
     * 记录规则触发
     */
    public synchronized void recordTrigger(String ruleId, String ruleName) {
        try {
            String today = dateFormat.format(new Date());
            String hour = hourFormat.format(new Date());
            
            // 今日统计
            String todayKey = "today_" + today;
            int todayCount = prefs.getInt(todayKey, 0);
            prefs.edit().putInt(todayKey, todayCount + 1).apply();
            
            // 规则统计
            String ruleKey = "rule_" + ruleId;
            int ruleCount = prefs.getInt(ruleKey, 0);
            prefs.edit().putInt(ruleKey, ruleCount + 1).apply();
            
            // 小时分布
            String hourKey = "hour_" + hour;
            int hourCount = prefs.getInt(hourKey, 0);
            prefs.edit().putInt(hourKey, hourCount + 1).apply();
            
            // 最近 7 天统计
            recordDailyStats(today, ruleId, ruleName);
            
            Log.d(TAG, "记录触发：" + ruleName + " (今日：" + (todayCount + 1) + ")");
            
        } catch (Exception e) {
            Log.e(TAG, "记录统计失败", e);
        }
    }
    
    /**
     * 记录每日统计
     */
    private void recordDailyStats(String date, String ruleId, String ruleName) {
        try {
            String dailyKey = "daily_" + date;
            String dailyJson = prefs.getString(dailyKey, "{}");
            JSONObject daily = new JSONObject(dailyJson);
            
            JSONObject ruleStats = daily.optJSONObject(ruleId);
            if (ruleStats == null) {
                ruleStats = new JSONObject();
                ruleStats.put("name", ruleName);
                ruleStats.put("count", 0);
            }
            
            ruleStats.put("count", ruleStats.getInt("count") + 1);
            daily.put(ruleId, ruleStats);
            
            prefs.edit().putString(dailyKey, daily.toString()).apply();
            
        } catch (Exception e) {
            Log.e(TAG, "记录每日统计失败", e);
        }
    }
    
    /**
     * 获取今日触发次数
     */
    public int getTodayCount() {
        String today = dateFormat.format(new Date());
        return prefs.getInt("today_" + today, 0);
    }
    
    /**
     * 获取规则总触发次数
     */
    public int getRuleCount(String ruleId) {
        return prefs.getInt("rule_" + ruleId, 0);
    }
    
    /**
     * 获取小时分布
     */
    public Map<Integer, Integer> getHourlyDistribution() {
        Map<Integer, Integer> distribution = new HashMap<>();
        
        for (int hour = 0; hour < 24; hour++) {
            String hourKey = "hour_" + String.format(Locale.getDefault(), "%02d", hour);
            int count = prefs.getInt(hourKey, 0);
            if (count > 0) {
                distribution.put(hour, count);
            }
        }
        
        return distribution;
    }
    
    /**
     * 获取最近 7 天统计
     */
    public List<DailyStats> getLast7DaysStats() {
        List<DailyStats> stats = new ArrayList<>();
        
        Calendar calendar = Calendar.getInstance();
        for (int i = 6; i >= 0; i--) {
            calendar.add(Calendar.DAY_OF_YEAR, -i);
            String date = dateFormat.format(calendar.getTime());
            
            String dailyKey = "daily_" + date;
            String dailyJson = prefs.getString(dailyKey, "{}");
            
            DailyStats dailyStats = new DailyStats();
            dailyStats.date = date;
            dailyStats.rules = new ArrayList<>();
            
            try {
                JSONObject daily = new JSONObject(dailyJson);
                JSONArray keys = daily.names();
                if (keys != null) {
                    for (int j = 0; j < keys.length(); j++) {
                        String ruleId = keys.getString(j);
                        JSONObject ruleStats = daily.getJSONObject(ruleId);
                        
                        RuleStats ruleStat = new RuleStats();
                        ruleStat.ruleId = ruleId;
                        ruleStat.ruleName = ruleStats.optString("name", ruleId);
                        ruleStat.count = ruleStats.getInt("count");
                        
                        dailyStats.rules.add(ruleStat);
                    }
                }
            } catch (Exception e) {
                // 忽略解析错误
            }
            
            stats.add(dailyStats);
        }
        
        return stats;
    }
    
    /**
     * 清空统计
     */
    public void clearStats() {
        prefs.edit().clear().apply();
        Log.d(TAG, "统计已清空");
    }
    
    /**
     * 每日统计
     */
    public static class DailyStats {
        public String date;
        public List<RuleStats> rules;
    }
    
    /**
     * 规则统计
     */
    public static class RuleStats {
        public String ruleId;
        public String ruleName;
        public int count;
    }
}
