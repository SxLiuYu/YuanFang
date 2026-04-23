package com.openclaw.homeassistant;

import android.content.Context;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.*;
import java.net.*;
import java.util.*;

/**
 * AI 用电预测服务
 * 功能：
 * - 未来用电预测
 * - 月度电费预测
 * - 异常检测
 * - 智能节能建议
 */
public class AIEnergyPredictionService {
    
    private static final String TAG = "AIEnergyPrediction";
    
    private Context context;
    private SecureConfig secureConfig;
    
    public AIEnergyPredictionService(Context context) {
        this.context = context;
        this.secureConfig = SecureConfig.getInstance(context);
    }
    
    private String getApiBaseUrl() {
        return secureConfig.getServerUrl() + "/api/energy/ai";
    }
    
    // ========== 数据模型 ==========
    
    public static class PredictionResult {
        public boolean success;
        public String message;
        public List<DailyPrediction> predictions;
        public float totalKwh;
        public float totalCost;
        public float avgDailyKwh;
    }
    
    public static class DailyPrediction {
        public String date;
        public String weekday;
        public float predictedKwh;
        public float predictedCost;
        public float confidence;
    }
    
    public static class MonthlyPrediction {
        public String period;
        public float predictedKwh;
        public float predictedCost;
        public float lastMonthKwh;
        public float lastMonthCost;
        public float monthOverMonthChange;
        public String trend;
    }
    
    public static class AnomalyResult {
        public boolean success;
        public int anomaliesCount;
        public float meanDailyKwh;
        public List<Anomaly> anomalies;
        public List<String> recommendations;
    }
    
    public static class Anomaly {
        public String date;
        public float kwh;
        public float zScore;
        public String type;
        public float deviation;
        public String severity;
    }
    
    public static class Suggestion {
        public String type;
        public String priority;
        public String device;
        public String message;
        public float potentialSaving;
        public List<String> tips;
    }
    
    // ========== 回调接口 ==========
    
    public interface TrainCallback {
        void onTrainComplete(boolean success, String message);
        void onError(String error);
    }
    
    public interface PredictDailyCallback {
        void onPrediction(PredictionResult result);
        void onError(String error);
    }
    
    public interface PredictMonthlyCallback {
        void onPrediction(MonthlyPrediction prediction);
        void onError(String error);
    }
    
    public interface AnomalyCallback {
        void onAnomalyResult(AnomalyResult result);
        void onError(String error);
    }
    
    public interface SuggestionCallback {
        void onSuggestions(List<Suggestion> suggestions, float totalSaving);
        void onError(String error);
    }
    
    // ========== API 调用 ==========
    
    /**
     * 训练 AI 预测模型
     */
    public void trainModel(int days, TrainCallback callback) {
        ThreadPoolManager.getInstance().execute(() -> {
            try {
                JSONObject response = sendPostRequest(getApiBaseUrl() + "/train", 
                    new JSONObject().put("days", days));
                
                boolean success = response.getBoolean("success");
                String message = response.optString("message", "");
                
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onTrainComplete(success, message));
                }
                
            } catch (Exception e) {
                Log.e(TAG, "训练模型失败", e);
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onError(e.getMessage()));
                }
            }
        });
    }
    
    /**
     * 预测未来每日用电
     */
    public void predictDailyUsage(int days, PredictDailyCallback callback) {
        ThreadPoolManager.getInstance().execute(() -> {
            try {
                JSONObject response = sendGetRequest(getApiBaseUrl() + "/predict-daily?days=" + days);
                
                PredictionResult result = new PredictionResult();
                result.success = response.getBoolean("success");
                result.totalKwh = (float) response.getDouble("total_kwh");
                result.totalCost = (float) response.getDouble("total_cost");
                result.avgDailyKwh = (float) response.getDouble("avg_daily_kwh");
                
                result.predictions = new ArrayList<>();
                JSONArray predictionsArray = response.getJSONArray("predictions");
                for (int i = 0; i < predictionsArray.length(); i++) {
                    JSONObject pred = predictionsArray.getJSONObject(i);
                    DailyPrediction dp = new DailyPrediction();
                    dp.date = pred.getString("date");
                    dp.weekday = pred.getString("weekday");
                    dp.predictedKwh = (float) pred.getDouble("predicted_kwh");
                    dp.predictedCost = (float) pred.getDouble("predicted_cost");
                    dp.confidence = (float) pred.getDouble("confidence");
                    result.predictions.add(dp);
                }
                
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onPrediction(result));
                }
                
            } catch (Exception e) {
                Log.e(TAG, "预测失败", e);
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onError(e.getMessage()));
                }
            }
        });
    }
    
    /**
     * 预测月度电费
     */
    public void predictMonthlyBill(Integer month, Integer year, PredictMonthlyCallback callback) {
        String url = getApiBaseUrl() + "/predict-monthly?";
        if (month != null) url += "month=" + month + "&";
        if (year != null) url += "year=" + year;
        
        final String finalUrl = url;
        
        ThreadPoolManager.getInstance().execute(() -> {
            try {
                JSONObject response = sendGetRequest(finalUrl);
                
                MonthlyPrediction prediction = new MonthlyPrediction();
                prediction.period = response.getString("period");
                prediction.predictedKwh = (float) response.getDouble("predicted_kwh");
                prediction.predictedCost = (float) response.getDouble("predicted_cost");
                prediction.lastMonthKwh = (float) response.getDouble("last_month_kwh");
                prediction.lastMonthCost = (float) response.getDouble("last_month_cost");
                prediction.monthOverMonthChange = (float) response.getDouble("month_over_month_change");
                prediction.trend = response.getString("trend");
                
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onPrediction(prediction));
                }
                
            } catch (Exception e) {
                Log.e(TAG, "月度预测失败", e);
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onError(e.getMessage()));
                }
            }
        });
    }
    
    /**
     * 检测异常用电
     */
    public void detectAnomalies(int days, AnomalyCallback callback) {
        ThreadPoolManager.getInstance().execute(() -> {
            try {
                JSONObject response = sendGetRequest(getApiBaseUrl() + "/anomalies?days=" + days);
                
                AnomalyResult result = new AnomalyResult();
                result.success = response.getBoolean("success");
                result.anomaliesCount = response.getInt("anomalies_count");
                result.meanDailyKwh = (float) response.getDouble("mean_daily_kwh");
                
                result.anomalies = new ArrayList<>();
                if (response.has("anomalies")) {
                    JSONArray anomaliesArray = response.getJSONArray("anomalies");
                    for (int i = 0; i < anomaliesArray.length(); i++) {
                        JSONObject anomaly = anomaliesArray.getJSONObject(i);
                        Anomaly a = new Anomaly();
                        a.date = anomaly.getString("date");
                        a.kwh = (float) anomaly.getDouble("kwh");
                        a.zScore = (float) anomaly.getDouble("z_score");
                        a.type = anomaly.getString("type");
                        a.deviation = (float) anomaly.getDouble("deviation");
                        a.severity = anomaly.getString("severity");
                        result.anomalies.add(a);
                    }
                }
                
                result.recommendations = new ArrayList<>();
                if (response.has("recommendations")) {
                    JSONArray recArray = response.getJSONArray("recommendations");
                    for (int i = 0; i < recArray.length(); i++) {
                        result.recommendations.add(recArray.getString(i));
                    }
                }
                
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onAnomalyResult(result));
                }
                
            } catch (Exception e) {
                Log.e(TAG, "异常检测失败", e);
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onError(e.getMessage()));
                }
            }
        });
    }
    
    /**
     * 获取 AI 智能建议
     */
    public void getSmartSuggestions(SuggestionCallback callback) {
        ThreadPoolManager.getInstance().execute(() -> {
            try {
                JSONObject response = sendGetRequest(getApiBaseUrl() + "/suggestions");
                
                List<Suggestion> suggestions = new ArrayList<>();
                JSONArray suggestionsArray = response.getJSONArray("suggestions");
                
                for (int i = 0; i < suggestionsArray.length(); i++) {
                    JSONObject sug = suggestionsArray.getJSONObject(i);
                    Suggestion s = new Suggestion();
                    s.type = sug.optString("type", "");
                    s.priority = sug.optString("priority", "medium");
                    s.device = sug.optString("device", "");
                    s.message = sug.getString("message");
                    s.potentialSaving = (float) sug.optDouble("potential_saving", 0);
                    
                    if (sug.has("tips")) {
                        s.tips = new ArrayList<>();
                        JSONArray tipsArray = sug.getJSONArray("tips");
                        for (int j = 0; j < tipsArray.length(); j++) {
                            s.tips.add(tipsArray.getString(j));
                        }
                    }
                    
                    suggestions.add(s);
                }
                
                float totalSaving = (float) response.getDouble("total_potential_saving");
                
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onSuggestions(suggestions, totalSaving));
                }
                
            } catch (Exception e) {
                Log.e(TAG, "获取建议失败", e);
                if (callback != null) {
                    android.os.Handler mainHandler = new android.os.Handler(context.getMainLooper());
                    mainHandler.post(() -> callback.onError(e.getMessage()));
                }
            }
        });
    }
    
    // ========== HTTP 工具方法 ==========
    
    private JSONObject sendGetRequest(String urlString) throws Exception {
        URL url = new URL(urlString);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("GET");
        conn.setConnectTimeout(10000);
        conn.setReadTimeout(10000);
        
        int responseCode = conn.getResponseCode();
        if (responseCode != 200) {
            throw new Exception("HTTP error: " + responseCode);
        }
        
        BufferedReader reader = new BufferedReader(
            new InputStreamReader(conn.getInputStream(), "UTF-8"));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            sb.append(line);
        }
        reader.close();
        
        return new JSONObject(sb.toString());
    }
    
    private JSONObject sendPostRequest(String urlString, JSONObject data) throws Exception {
        URL url = new URL(urlString);
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setConnectTimeout(10000);
        conn.setReadTimeout(10000);
        conn.setRequestProperty("Content-Type", "application/json");
        conn.setDoOutput(true);
        
        OutputStream os = conn.getOutputStream();
        os.write(data.toString().getBytes("UTF-8"));
        os.flush();
        os.close();
        
        int responseCode = conn.getResponseCode();
        if (responseCode != 200) {
            throw new Exception("HTTP error: " + responseCode);
        }
        
        BufferedReader reader = new BufferedReader(
            new InputStreamReader(conn.getInputStream(), "UTF-8"));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            sb.append(line);
        }
        reader.close();
        
        return new JSONObject(sb.toString());
    }
}
