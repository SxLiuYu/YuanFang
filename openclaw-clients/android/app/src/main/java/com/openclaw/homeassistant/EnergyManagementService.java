package com.openclaw.homeassistant;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * 家庭能源管理服务
 * 功能：
 * - 设备用电监控
 * - 电费统计与分析
 * - 节能建议生成
 * - 用电报告（日报/周报/月报）
 */
public class EnergyManagementService {
    
    private static final String TAG = "EnergyManagement";
    private static final String PREFS_NAME = "energy_management";
    
    private Context context;
    private SharedPreferences prefs;
    private OpenClawApiClient apiClient;
    
    // 设备功率参考值（瓦特）
    private Map<String, Integer> devicePowerReference;
    
    // 电价（元/度）
    private double electricityRate = 0.4887; // 北京居民电价
    
    public EnergyManagementService(Context context) {
        this.context = context;
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        this.apiClient = new OpenClawApiClient(context);
        initDevicePowerReference();
    }
    
    private void initDevicePowerReference() {
        devicePowerReference = new HashMap<>();
        devicePowerReference.put("light", 10);
        devicePowerReference.put("空调", 1500);
        devicePowerReference.put("air_conditioner", 1500);
        devicePowerReference.put("tv", 150);
        devicePowerReference.put("电视", 150);
        devicePowerReference.put("refrigerator", 200);
        devicePowerReference.put("冰箱", 200);
        devicePowerReference.put("washing_machine", 500);
        devicePowerReference.put("洗衣机", 500);
        devicePowerReference.put("microwave", 1000);
        devicePowerReference.put("微波炉", 1000);
        devicePowerReference.put("electric_kettle", 1800);
        devicePowerReference.put("电水壶", 1800);
        devicePowerReference.put("computer", 300);
        devicePowerReference.put("电脑", 300);
        devicePowerReference.put("router", 10);
        devicePowerReference.put("路由器", 10);
        devicePowerReference.put("heater", 2000);
        devicePowerReference.put("电暖器", 2000);
        devicePowerReference.put("fan", 50);
        devicePowerReference.put("风扇", 50);
        devicePowerReference.put("water_heater", 3000);
        devicePowerReference.put("热水器", 3000);
    }
    
    /**
     * 记录设备用电
     */
    public interface RecordCallback {
        void onSuccess(Map<String, Object> result);
        void onError(String error);
    }
    
    public void recordEnergyUsage(String deviceId, String deviceName, 
                                  double powerWatts, double usageHours,
                                  String room, String notes,
                                  RecordCallback callback) {
        ThreadPoolManager.getInstance().execute(() -> {
            try {
                // 计算用电量和费用
                double energyKwh = (powerWatts * usageHours) / 1000.0;
                double cost = energyKwh * electricityRate;
                
                // 调用后端 API
                Map<String, Object> params = new HashMap<>();
                params.put("device_id", deviceId);
                params.put("device_name", deviceName);
                params.put("power_watts", powerWatts);
                params.put("usage_hours", usageHours);
                params.put("room", room);
                params.put("notes", notes);
                
                // 保存到本地
                saveLocalRecord(deviceId, deviceName, powerWatts, usageHours, energyKwh, cost, room);
                
                Map<String, Object> result = new HashMap<>();
                result.put("success", true);
                result.put("energy_kwh", Math.round(energyKwh * 1000.0) / 1000.0);
                result.put("cost", Math.round(cost * 100.0) / 100.0);
                
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onSuccess(result));
                }
                
                Log.d(TAG, "记录用电：" + deviceName + " " + energyKwh + "度 " + cost + "元");
                
            } catch (Exception e) {
                Log.e(TAG, "记录用电失败", e);
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onError(e.getMessage()));
                }
            }
        });
    }
    
    /**
     * 快速记录（根据设备名自动匹配功率）
     */
    public void quickRecord(String deviceName, double usageHours, RecordCallback callback) {
        Integer powerWatts = getPowerByDeviceName(deviceName);
        if (powerWatts == null) {
            powerWatts = 100; // 默认 100W
        }
        
        recordEnergyUsage(
            "manual_" + System.currentTimeMillis(),
            deviceName,
            powerWatts,
            usageHours,
            null,
            null,
            callback
        );
    }
    
    private Integer getPowerByDeviceName(String deviceName) {
        String lowerName = deviceName.toLowerCase();
        for (Map.Entry<String, Integer> entry : devicePowerReference.entrySet()) {
            if (lowerName.contains(entry.getKey())) {
                return entry.getValue();
            }
        }
        return null;
    }
    
    private void saveLocalRecord(String deviceId, String deviceName, double powerWatts,
                                 double usageHours, double energyKwh, double cost, String room) {
        SharedPreferences.Editor editor = prefs.edit();
        
        // 获取今日记录数
        String today = new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(new Date());
        int count = prefs.getInt("record_count_" + today, 0);
        
        // 保存记录
        String key = "record_" + today + "_" + count;
        JSONObject record = new JSONObject();
        try {
            record.put("device_id", deviceId);
            record.put("device_name", deviceName);
            record.put("power_watts", powerWatts);
            record.put("usage_hours", usageHours);
            record.put("energy_kwh", energyKwh);
            record.put("cost", cost);
            record.put("room", room != null ? room : "");
            record.put("timestamp", System.currentTimeMillis());
            
            editor.putString(key, record.toString());
            editor.putInt("record_count_" + today, count + 1);
            
            // 更新今日总计
            double totalKwh = prefs.getFloat("total_kwh_" + today, 0);
            double totalCost = prefs.getFloat("total_cost_" + today, 0);
            editor.putFloat("total_kwh_" + today, (float) (totalKwh + energyKwh));
            editor.putFloat("total_cost_" + today, (float) (totalCost + cost));
            
            editor.apply();
        } catch (Exception e) {
            Log.e(TAG, "保存本地记录失败", e);
        }
    }
    
    /**
     * 获取每日用电报告
     */
    public interface DailyReportCallback {
        void onReport(Map<String, Object> report);
        void onError(String error);
    }
    
    public void getDailyReport(String date, DailyReportCallback callback) {
        if (date == null) {
            date = new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(new Date());
        }
        
        final String finalDate = date;
        
        ThreadPoolManager.getInstance().execute(() -> {
            try {
                Map<String, Object> report = new HashMap<>();
                report.put("date", finalDate);
                report.put("total_kwh", prefs.getFloat("total_kwh_" + finalDate, 0));
                report.put("total_cost", prefs.getFloat("total_cost_" + finalDate, 0));
                report.put("device_count", prefs.getInt("record_count_" + finalDate, 0));
                
                // 获取设备明细
                List<Map<String, Object>> devices = new ArrayList<>();
                int count = prefs.getInt("record_count_" + finalDate, 0);
                
                for (int i = 0; i < count; i++) {
                    String key = "record_" + finalDate + "_" + i;
                    String json = prefs.getString(key, null);
                    if (json != null) {
                        JSONObject record = new JSONObject(json);
                        Map<String, Object> device = new HashMap<>();
                        device.put("name", record.getString("device_name"));
                        device.put("kwh", record.getDouble("energy_kwh"));
                        device.put("cost", record.getDouble("cost"));
                        device.put("room", record.optString("room", ""));
                        devices.add(device);
                    }
                }
                
                report.put("devices", devices);
                report.put("success", true);
                
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onReport(report));
                }
                
            } catch (Exception e) {
                Log.e(TAG, "获取日报失败", e);
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onError(e.getMessage()));
                }
            }
        });
    }
    
    /**
     * 获取节能建议
     */
    public List<Map<String, Object>> getEnergySavingSuggestions() {
        List<Map<String, Object>> suggestions = new ArrayList<>();
        
        // 分析高耗电设备
        String today = new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(new Date());
        int count = prefs.getInt("record_count_" + today, 0);
        
        Map<String, Double> deviceUsage = new HashMap<>();
        
        for (int i = 0; i < count; i++) {
            String key = "record_" + today + "_" + i;
            String json = prefs.getString(key, null);
            if (json != null) {
                try {
                    JSONObject record = new JSONObject(json);
                    String name = record.getString("device_name");
                    double kwh = record.getDouble("energy_kwh");
                    
                    deviceUsage.put(name, deviceUsage.getOrDefault(name, 0.0) + kwh);
                } catch (Exception e) {
                    Log.e(TAG, "分析设备用电失败", e);
                }
            }
        }
        
        // 生成建议
        for (Map.Entry<String, Double> entry : deviceUsage.entrySet()) {
            String deviceName = entry.getKey();
            double kwh = entry.getValue();
            
            Integer power = getPowerByDeviceName(deviceName);
            if (power != null && power > 1500) {
                Map<String, Object> suggestion = new HashMap<>();
                suggestion.put("type", "high_power");
                suggestion.put("device", deviceName);
                suggestion.put("message", deviceName + "是大功率设备（" + power + "W），建议合理使用");
                suggestion.put("potential_saving", Math.round(kwh * 0.1 * electricityRate * 100.0) / 100.0);
                suggestions.add(suggestion);
            }
        }
        
        // 通用建议
        Map<String, Object> standbySuggestion = new HashMap<>();
        standbySuggestion.put("type", "standby");
        standbySuggestion.put("message", "不用的电器建议拔掉插头，待机能耗约占家庭用电的 5-10%");
        standbySuggestion.put("potential_saving", 5.0);
        suggestions.add(standbySuggestion);
        
        return suggestions;
    }
    
    /**
     * 设置节能目标
     */
    public boolean setEnergySavingGoal(String goalName, double targetKwh, String period) {
        SharedPreferences.Editor editor = prefs.edit();
        
        editor.putString("goal_name", goalName);
        editor.putFloat("goal_target_kwh", (float) targetKwh);
        editor.putFloat("goal_target_cost", (float) (targetKwh * electricityRate));
        editor.putString("goal_period", period);
        editor.putLong("goal_start_date", System.currentTimeMillis());
        editor.putFloat("goal_current_kwh", 0);
        editor.putBoolean("goal_active", true);
        
        return editor.commit();
    }
    
    /**
     * 获取节能目标进度
     */
    public Map<String, Object> getGoalProgress() {
        Map<String, Object> progress = new HashMap<>();
        
        if (!prefs.getBoolean("goal_active", false)) {
            progress.put("success", false);
            progress.put("message", "无活跃节能目标");
            return progress;
        }
        
        String goalName = prefs.getString("goal_name", "节能目标");
        float targetKwh = prefs.getFloat("goal_target_kwh", 0);
        float targetCost = prefs.getFloat("goal_target_cost", 0);
        long startDate = prefs.getLong("goal_start_date", 0);
        
        // 计算当前进度
        String today = new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(new Date());
        float currentKwh = prefs.getFloat("total_kwh_" + today, 0);
        
        // 简单起见，这里只计算今日，实际应该从 startDate 累计
        progress.put("success", true);
        progress.put("goal_name", goalName);
        progress.put("target_kwh", targetKwh);
        progress.put("target_cost", targetCost);
        progress.put("current_kwh", currentKwh);
        progress.put("progress", targetKwh > 0 ? (currentKwh / targetKwh * 100) : 0);
        
        return progress;
    }
    
    /**
     * 清除本地记录
     */
    public void clearRecords(String date) {
        SharedPreferences.Editor editor = prefs.edit();
        editor.remove("record_count_" + date);
        editor.remove("total_kwh_" + date);
        editor.remove("total_cost_" + date);
        editor.apply();
    }
    
    /**
     * 获取本月累计用电
     */
    public Map<String, Object> getMonthlyTotal() {
        Map<String, Object> result = new HashMap<>();
        
        double totalKwh = 0;
        double totalCost = 0;
        int days = 0;
        
        SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault());
        Date now = new Date();
        
        // 简单计算当月已记录的天数
        for (int i = 0; i < 31; i++) {
            Date date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
            String dateStr = sdf.format(date);
            
            float dayKwh = prefs.getFloat("total_kwh_" + dateStr, 0);
            if (dayKwh > 0) {
                totalKwh += dayKwh;
                totalCost += prefs.getFloat("total_cost_" + dateStr, 0);
                days++;
            }
        }
        
        result.put("total_kwh", Math.round(totalKwh * 100.0) / 100.0);
        result.put("total_cost", Math.round(totalCost * 100.0) / 100.0);
        result.put("days", days);
        result.put("avg_daily_kwh", days > 0 ? Math.round((totalKwh / days) * 100.0) / 100.0 : 0);
        
        return result;
    }
}
