package com.openclaw.homeassistant;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * 设备注册与认证服务
 * - 首次启动时注册设备
 * - 等待用户飞书确认
 * - 保存永久信任令牌
 */
public class DeviceAuthService {
    
    private static final String TAG = "DeviceAuthService";
    private static final String PREFS_NAME = "device_auth";
    
    private final SecureConfig secureConfig;
    
    // 认证状态
    private final Context context;
    private final SharedPreferences prefs;
    private String deviceId;
    private String deviceToken;
    private boolean isConfirmed;
    private String currentTempId;  // 当前待确认的临时 ID
    
    public interface AuthListener {
        void onAuthSuccess(String token);
        void onAuthPending(String tempId);
        void onAuthFailed(String error);
    }
    
    private AuthListener listener;
    
    public DeviceAuthService(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        this.secureConfig = SecureConfig.getInstance(context);
        
        // 加载设备 ID
        this.deviceId = prefs.getString("device_id", null);
        if (this.deviceId == null) {
            this.deviceId = android.provider.Settings.Secure.getString(
                context.getContentResolver(),
                android.provider.Settings.Secure.ANDROID_ID
            );
            if (this.deviceId == null || this.deviceId.equals("9774d56d682e549c")) {
                this.deviceId = java.util.UUID.randomUUID().toString();
            }
            prefs.edit().putString("device_id", this.deviceId).apply();
        }
        
        // 加载令牌
        this.deviceToken = prefs.getString("device_token", null);
        this.isConfirmed = prefs.getBoolean("device_confirmed", false);
        
        Log.d(TAG, "设备初始化：" + deviceId + " (已确认：" + isConfirmed + ")");
    }
    
    public void setListener(AuthListener listener) {
        this.listener = listener;
    }
    
    /**
     * 检查认证状态
     */
    public boolean isConfirmed() {
        return isConfirmed;
    }
    
    /**
     * 获取设备令牌
     */
    public String getToken() {
        return deviceToken;
    }
    
    /**
     * 注册或登录设备
     */
    public void registerOrLogin() {
        ThreadPoolManager.getInstance().execute(() -> {
            try {
                JSONObject requestData = new JSONObject();
                requestData.put("device_id", deviceId);
                requestData.put("device_name", getDeviceName());
                requestData.put("device_model", android.os.Build.BRAND + " " + android.os.Build.MODEL);
                
                URL url = new URL(secureConfig.getServerUrl() + "/device/register");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setConnectTimeout(10000);
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                
                try (OutputStream os = conn.getOutputStream()) {
                    os.write(requestData.toString().getBytes("utf-8"));
                }
                
                int status = conn.getResponseCode();
                try (BufferedReader br = new BufferedReader(
                        new InputStreamReader(conn.getInputStream(), "utf-8"))) {
                    StringBuilder response = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null) {
                        response.append(line);
                    }
                    
                    JSONObject responseJson = new JSONObject(response.toString());
                    
                    if (responseJson.optBoolean("confirmed")) {
                        // 设备已确认，保存令牌
                        String token = responseJson.getString("token");
                        prefs.edit()
                            .putString("device_token", token)
                            .putBoolean("device_confirmed", true)
                            .apply();
                        
                        this.deviceToken = token;
                        this.isConfirmed = true;
                        
                        Log.d(TAG, "设备已确认");
                        if (listener != null) {
                            listener.onAuthSuccess(token);
                        }
                        
                    } else if ("pending".equals(responseJson.optString("status"))) {
                        // 等待确认
                        String tempId = responseJson.getString("temp_id");
                        this.currentTempId = tempId;  // 保存临时 ID
                        Log.d(TAG, "等待用户确认，temp_id: " + tempId);
                        if (listener != null) {
                            listener.onAuthPending(tempId);
                        }
                    }
                }
                
                conn.disconnect();
                
            } catch (Exception e) {
                Log.e(TAG, "注册失败", e);
                if (listener != null) {
                    listener.onAuthFailed(e.getMessage());
                }
            }
        });
    }
    
    /**
     * 确认设备（用户输入确认码后调用）
     */
    public void confirmDevice(String tempId, String confirmCode) {
        ThreadPoolManager.getInstance().execute(() -> {
            try {
                JSONObject requestData = new JSONObject();
                requestData.put("temp_id", tempId);
                requestData.put("confirm_code", confirmCode.toUpperCase());
                
                URL url = new URL(secureConfig.getServerUrl() + "/device/confirm");
                HttpURLConnection conn = (HttpURLConnection) url.openConnection();
                conn.setRequestMethod("POST");
                conn.setConnectTimeout(10000);
                conn.setRequestProperty("Content-Type", "application/json");
                conn.setDoOutput(true);
                
                try (OutputStream os = conn.getOutputStream()) {
                    os.write(requestData.toString().getBytes("utf-8"));
                }
                
                int status = conn.getResponseCode();
                try (BufferedReader br = new BufferedReader(
                        new InputStreamReader(conn.getInputStream(), "utf-8"))) {
                    StringBuilder response = new StringBuilder();
                    String line;
                    while ((line = br.readLine()) != null) {
                        response.append(line);
                    }
                    
                    JSONObject responseJson = new JSONObject(response.toString());
                    
                    if (responseJson.optBoolean("confirmed")) {
                        String token = responseJson.getString("token");
                        prefs.edit()
                            .putString("device_token", token)
                            .putBoolean("device_confirmed", true)
                            .apply();
                        
                        this.deviceToken = token;
                        this.isConfirmed = true;
                        
                        Log.d(TAG, "设备确认成功");
                        if (listener != null) {
                            listener.onAuthSuccess(token);
                        }
                    }
                }
                
                conn.disconnect();
                
            } catch (Exception e) {
                Log.e(TAG, "确认失败", e);
                if (listener != null) {
                    listener.onAuthFailed(e.getMessage());
                }
            }
        });
    }
    
    /**
     * 获取设备名称
     */
    private String getDeviceName() {
        String savedName = prefs.getString("device_name", null);
        if (savedName != null) {
            return savedName;
        }
        
        String defaultName = android.os.Build.BRAND + " " + android.os.Build.MODEL;
        prefs.edit().putString("device_name", defaultName).apply();
        return defaultName;
    }
    
    /**
     * 设置设备名称
     */
    public void setDeviceName(String name) {
        prefs.edit().putString("device_name", name).apply();
    }
    
    /**
     * 获取设备 ID
     */
    public String getDeviceId() {
        return deviceId;
    }
    
    /**
     * 获取当前临时 ID（用于确认界面）
     */
    public String getCurrentTempId() {
        return currentTempId;
    }
    
    /**
     * 退出登录（清除令牌）
     */
    public void logout() {
        prefs.edit()
            .remove("device_token")
            .remove("device_confirmed")
            .apply();
        this.deviceToken = null;
        this.isConfirmed = false;
        this.currentTempId = null;
        Log.d(TAG, "已退出登录");
    }
}
