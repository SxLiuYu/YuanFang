package com.openclaw.homeassistant;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import java.text.SimpleDateFormat;
import java.util.*;

/**
 * 能源图表服务
 * 生成图表数据供 MPAndroidChart 使用
 */
public class EnergyChartService {
    
    private static final String TAG = "EnergyChartService";
    private static final String PREFS_NAME = "energy_management";
    
    private Context context;
    private SharedPreferences prefs;
    
    public EnergyChartService(Context context) {
        this.context = context;
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }
    
    // ========== 数据模型 ==========
    
    public static class TrendData {
        public String date;
        public float[] kwhValues = new float[24];
        public float totalKwh;
        public float totalCost;
        public int peakHour;
    }
    
    public static class WeeklyTrendData {
        public String[] labels = new String[7];
        public float[] kwhValues = new float[7];
        public float totalKwh;
        public float totalCost;
        public float avgDailyKwh;
    }
    
    public static class MonthlyTrendData {
        public String[] labels;
        public float[] kwhValues;
        public float totalKwh;
        public float totalCost;
        public float avgDailyKwh;
    }
    
    public static class DistributionData {
        public String[] labels;
        public float[] values;
        public float totalKwh;
    }
    
    // ========== 回调接口 ==========
    
    public interface DailyTrendCallback {
        void onTrendData(TrendData data);
        void onError(String error);
    }
    
    public interface WeeklyTrendCallback {
        void onTrendData(WeeklyTrendData data);
        void onError(String error);
    }
    
    public interface MonthlyTrendCallback {
        void onTrendData(MonthlyTrendData data);
        void onError(String error);
    }
    
    public interface DistributionCallback {
        void onDistributionData(DistributionData data);
        void onError(String error);
    }
    
    // ========== 图表数据生成 ==========
    
    /**
     * 获取每日用电趋势数据
     */
    public void getDailyTrendData(String date, DailyTrendCallback callback) {
        ThreadPoolManager.getInstance().execute(() -> {
            try {
                final String finalDate = (date == null) ? new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(new Date()) : date;
                
                TrendData data = new TrendData();
                data.date = finalDate;
                
                // 从 SharedPreferences 读取当日记录
                int count = prefs.getInt("record_count_" + finalDate, 0);
                float[] hourData = new float[24];
                
                for (int i = 0; i < count; i++) {
                    String key = "record_" + finalDate + "_" + i;
                    String json = prefs.getString(key, null);
                    if (json != null) {
                        org.json.JSONObject record = new org.json.JSONObject(json);
                        double kwh = record.getDouble("energy_kwh");
                        long timestamp = record.getLong("timestamp");
                        
                        Calendar cal = Calendar.getInstance();
                        cal.setTimeInMillis(timestamp);
                        int hour = cal.get(Calendar.HOUR_OF_DAY);
                        
                        hourData[hour] += kwh;
                        data.totalKwh += kwh;
                    }
                }
                
                // 复制到结果数组
                System.arraycopy(hourData, 0, data.kwhValues, 0, 24);
                data.totalCost = data.totalKwh * 0.4887f;
                
                // 找出高峰时段
                data.peakHour = 0;
                for (int h = 1; h < 24; h++) {
                    if (hourData[h] > hourData[data.peakHour]) {
                        data.peakHour = h;
                    }
                }
                
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onTrendData(data));
                }
                
            } catch (Exception e) {
                Log.e(TAG, "获取每日趋势失败", e);
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onError(e.getMessage()));
                }
            }
        });
    }
    
    /**
     * 获取每周用电趋势数据
     */
    public void getWeeklyTrendData(String endDateStr, WeeklyTrendCallback callback) {
        ThreadPoolManager.getInstance().execute(() -> {
            try {
                WeeklyTrendData data = new WeeklyTrendData();
                
                Calendar endCal = Calendar.getInstance();
                if (endDateStr != null) {
                    SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault());
                    endCal.setTime(sdf.parse(endDateStr));
                }
                
                Calendar startCal = (Calendar) endCal.clone();
                startCal.add(Calendar.DAY_OF_MONTH, -6);
                
                SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault());
                SimpleDateFormat labelFormat = new SimpleDateFormat("MM/dd", Locale.getDefault());
                
                for (int i = 0; i < 7; i++) {
                    Calendar current = (Calendar) startCal.clone();
                    current.add(Calendar.DAY_OF_MONTH, i);
                    String dateStr = sdf.format(current);
                    
                    data.labels[i] = labelFormat.format(current);
                    data.kwhValues[i] = prefs.getFloat("total_kwh_" + dateStr, 0);
                    data.totalKwh += data.kwhValues[i];
                }
                
                data.totalCost = data.totalKwh * 0.4887f;
                data.avgDailyKwh = data.totalKwh / 7;
                
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onTrendData(data));
                }
                
            } catch (Exception e) {
                Log.e(TAG, "获取每周趋势失败", e);
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onError(e.getMessage()));
                }
            }
        });
    }
    
    /**
     * 获取月度用电趋势数据
     */
    public void getMonthlyTrendData(int year, int month, MonthlyTrendCallback callback) {
        ThreadPoolManager.getInstance().execute(() -> {
            try {
                Calendar now = Calendar.getInstance();
                final int finalYear = (year == 0) ? now.get(Calendar.YEAR) : year;
                final int finalMonth = (month == 0) ? now.get(Calendar.MONTH) + 1 : month;
                
                Calendar startCal = Calendar.getInstance();
                startCal.set(finalYear, finalMonth - 1, 1);
                
                Calendar endCal = (Calendar) startCal.clone();
                endCal.add(Calendar.MONTH, 1);
                endCal.add(Calendar.DAY_OF_MONTH, -1);
                
                int daysInMonth = endCal.get(Calendar.DAY_OF_MONTH);
                
                MonthlyTrendData data = new MonthlyTrendData();
                data.labels = new String[daysInMonth];
                data.kwhValues = new float[daysInMonth];
                
                SimpleDateFormat sdf = new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault());
                SimpleDateFormat labelFormat = new SimpleDateFormat("MM/dd", Locale.getDefault());
                
                for (int i = 0; i < daysInMonth; i++) {
                    Calendar current = (Calendar) startCal.clone();
                    current.add(Calendar.DAY_OF_MONTH, i);
                    String dateStr = sdf.format(current);
                    
                    // 每 5 天显示一个标签
                    if (i % 5 == 0) {
                        data.labels[i] = labelFormat.format(current);
                    } else {
                        data.labels[i] = "";
                    }
                    
                    data.kwhValues[i] = prefs.getFloat("total_kwh_" + dateStr, 0);
                    data.totalKwh += data.kwhValues[i];
                }
                
                data.totalCost = data.totalKwh * 0.4887f;
                data.avgDailyKwh = data.totalKwh / daysInMonth;
                
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onTrendData(data));
                }
                
            } catch (Exception e) {
                Log.e(TAG, "获取月度趋势失败", e);
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onError(e.getMessage()));
                }
            }
        });
    }
    
    /**
     * 获取设备用电分布数据
     */
    public void getDeviceDistributionData(String date, DistributionCallback callback) {
        ThreadPoolManager.getInstance().execute(() -> {
            try {
                final String finalDate = (date == null) ? new SimpleDateFormat("yyyy-MM-dd", Locale.getDefault()).format(new Date()) : date;
                
                // 统计各设备用电量
                Map<String, Float> deviceUsage = new HashMap<>();
                int count = prefs.getInt("record_count_" + finalDate, 0);
                
                for (int i = 0; i < count; i++) {
                    String key = "record_" + finalDate + "_" + i;
                    String json = prefs.getString(key, null);
                    if (json != null) {
                        org.json.JSONObject record = new org.json.JSONObject(json);
                        String deviceName = record.getString("device_name");
                        float kwh = (float) record.getDouble("energy_kwh");
                        
                        deviceUsage.put(deviceName, deviceUsage.getOrDefault(deviceName, 0f) + kwh);
                    }
                }
                
                // 转换为数组
                DistributionData data = new DistributionData();
                int size = deviceUsage.size();
                data.labels = new String[size];
                data.values = new float[size];
                
                int i = 0;
                for (Map.Entry<String, Float> entry : deviceUsage.entrySet()) {
                    data.labels[i] = entry.getKey();
                    data.values[i] = entry.getValue();
                    data.totalKwh += data.values[i];
                    i++;
                }
                
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onDistributionData(data));
                }
                
            } catch (Exception e) {
                Log.e(TAG, "获取设备分布失败", e);
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onError(e.getMessage()));
                }
            }
        });
    }
}
