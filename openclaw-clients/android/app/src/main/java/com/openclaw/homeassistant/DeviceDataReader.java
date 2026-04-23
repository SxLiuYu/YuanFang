package com.openclaw.homeassistant;

import android.app.usage.UsageEvents;
import android.app.usage.UsageStatsManager;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.BatteryManager;
import android.os.Build;
import android.provider.Settings;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 设备数据读取器
 * 功能：步数、应用使用时间、电池状态、网络状态等
 */
public class DeviceDataReader {
    
    private final Context context;
    
    public DeviceDataReader(Context context) {
        this.context = context;
    }
    
    /**
     * 读取今日步数（使用 Google Fit / Health Connect）
     * 注意：需要用户授权健康数据权限
     */
    public int getStepCount() {
        // 简化版本：返回 0，实际需要集成 Google Fit 或 Health Connect API
        // 完整实现需要：
        // 1. 添加 Google Fit 或 Health Connect SDK
        // 2. 请求 ACTIVITY_RECOGNITION 权限
        // 3. 查询步数数据
        return 0;
    }
    
    /**
     * 获取应用使用时间统计（过去 24 小时）
     */
    public Map<String, Long> getAppUsageStats() {
        UsageStatsManager usageStatsManager = (UsageStatsManager) 
            context.getSystemService(Context.USAGE_STATS_SERVICE);
        
        long currentTime = System.currentTimeMillis();
        long startTime = currentTime - 24 * 60 * 60 * 1000; // 24 小时前
        
        List<android.app.usage.UsageStats> stats = 
            usageStatsManager.queryUsageStats(UsageStatsManager.INTERVAL_DAILY, startTime, currentTime);
        
        Map<String, Long> usageMap = new HashMap<>();
        if (stats != null) {
            for (android.app.usage.UsageStats stat : stats) {
                String packageName = stat.getPackageName();
                long totalTime = stat.getTotalTimeInForeground();
                usageMap.put(packageName, totalTime);
            }
        }
        
        return usageMap;
    }
    
    /**
     * 获取应用使用时间（格式化字符串）
     */
    public String getFormattedAppUsage() {
        Map<String, Long> usageMap = getAppUsageStats();
        
        // 按使用时间排序
        List<Map.Entry<String, Long>> sorted = new ArrayList<>(usageMap.entrySet());
        sorted.sort((a, b) -> Long.compare(b.getValue(), a.getValue()));
        
        StringBuilder sb = new StringBuilder();
        int count = 0;
        for (Map.Entry<String, Long> entry : sorted) {
            if (count >= 5) break; // 只显示前 5 个
            
            long minutes = entry.getValue() / (1000 * 60);
            if (minutes < 1) continue; // 跳过少于 1 分钟的
            
            String appName = getAppName(entry.getKey());
            sb.append("• ").append(appName).append(": ")
              .append(formatTime(entry.getValue())).append("\n");
            count++;
        }
        
        return sb.length() > 0 ? sb.toString() : "无数据";
    }
    
    /**
     * 获取应用名称
     */
    private String getAppName(String packageName) {
        try {
            PackageManager pm = context.getPackageManager();
            return pm.getApplicationLabel(
                pm.getApplicationInfo(packageName, 0)).toString();
        } catch (Exception e) {
            return packageName;
        }
    }
    
    /**
     * 格式化时间（毫秒 → 小时/分钟）
     */
    private String formatTime(long millis) {
        long hours = millis / (1000 * 60 * 60);
        long minutes = (millis % (1000 * 60 * 60)) / (1000 * 60);
        
        if (hours > 0) {
            return hours + "小时" + minutes + "分钟";
        } else {
            return minutes + "分钟";
        }
    }
    
    /**
     * 获取屏幕使用时间（今天）
     */
    public String getScreenTime() {
        UsageStatsManager usageStatsManager = (UsageStatsManager) 
            context.getSystemService(Context.USAGE_STATS_SERVICE);
        
        long currentTime = System.currentTimeMillis();
        long startTime = currentTime - 24 * 60 * 60 * 1000;
        
        List<android.app.usage.UsageStats> stats = 
            usageStatsManager.queryUsageStats(UsageStatsManager.INTERVAL_DAILY, startTime, currentTime);
        
        long totalScreenTime = 0;
        if (stats != null) {
            for (android.app.usage.UsageStats stat : stats) {
                totalScreenTime += stat.getTotalTimeInForeground();
            }
        }
        
        long hours = totalScreenTime / (1000 * 60 * 60);
        long minutes = (totalScreenTime % (1000 * 60 * 60)) / (1000 * 60);
        
        return String.format("屏幕使用时间：%d 小时 %d 分钟", hours, minutes);
    }
    
    /**
     * 获取电池状态
     */
    public String getBatteryStatus() {
        IntentFilter ifilter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
        Intent batteryStatus = context.registerReceiver(null, ifilter);
        
        if (batteryStatus == null) {
            return "电池信息不可用";
        }
        
        int level = batteryStatus.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
        int scale = batteryStatus.getIntExtra(BatteryManager.EXTRA_SCALE, -1);
        int batteryPct = (int) ((level / (float) scale) * 100);
        
        int status = batteryStatus.getIntExtra(BatteryManager.EXTRA_STATUS, -1);
        boolean isCharging = status == BatteryManager.BATTERY_STATUS_CHARGING ||
                            status == BatteryManager.BATTERY_STATUS_FULL;
        
        return String.format("电量：%d%% (%s)", batteryPct, isCharging ? "充电中" : "放电中");
    }
    
    /**
     * 检查是否有 UsageStats 权限
     */
    public boolean hasUsageStatsPermission() {
        UsageStatsManager usageStatsManager = (UsageStatsManager) 
            context.getSystemService(Context.USAGE_STATS_SERVICE);
        
        long currentTime = System.currentTimeMillis();
        List<android.app.usage.UsageStats> stats = 
            usageStatsManager.queryUsageStats(UsageStatsManager.INTERVAL_DAILY, 
                currentTime - 1000 * 10, currentTime);
        
        return stats != null && !stats.isEmpty();
    }
    
    /**
     * 打开 UsageStats 权限设置
     */
    public void openUsageStatsSettings() {
        Intent intent = new Intent(Settings.ACTION_USAGE_ACCESS_SETTINGS);
        intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        context.startActivity(intent);
    }
    
    /**
     * 获取设备信息摘要
     */
    public String getDeviceSummary() {
        StringBuilder sb = new StringBuilder();
        
        // 电池
        sb.append("🔋 ").append(getBatteryStatus()).append("\n\n");
        
        // 屏幕使用时间
        sb.append("📱 ").append(getScreenTime()).append("\n\n");
        
        // 应用使用时间
        sb.append("📊 应用使用:\n").append(getFormattedAppUsage());
        
        return sb.toString();
    }
}
