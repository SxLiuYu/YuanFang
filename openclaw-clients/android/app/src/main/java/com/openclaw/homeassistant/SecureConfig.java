package com.openclaw.homeassistant;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import androidx.security.crypto.EncryptedSharedPreferences;
import androidx.security.crypto.MasterKey;

import org.json.JSONObject;

import java.security.SecureRandom;
import java.util.Base64;

/**
 * 统一配置管理类
 * 使用 EncryptedSharedPreferences 加密存储敏感信息
 * 合并了原 ConfigManager 和 SecureConfig 的所有功能
 */
public class SecureConfig {
    
    private static final String TAG = "SecureConfig";
    private static final String PREFS_NAME = "openclaw_secure_config";
    private static final String REGULAR_PREFS_NAME = "openclaw_config";
    
    private static SecureConfig instance;
    private final SharedPreferences encryptedPrefs;
    private final SharedPreferences regularPrefs;
    private final Context context;
    
    public static final String KEY_API_KEY = "api_key";
    public static final String KEY_SERVER_URL = "server_url";
    public static final String KEY_CHAT_SERVER_URL = "chat_server_url";
    public static final String KEY_DEVICE_TOKEN = "device_token";
    public static final String KEY_DEVICE_ID = "device_id";
    
    public static final String KEY_DASHSCOPE_API_KEY = "dashscope_api_key";
    public static final String KEY_FAMILY_SERVICE_URL = "family_service_url";
    public static final String KEY_FEISHU_WEBHOOK = "feishu_webhook";
    
    public static final String DEFAULT_SERVER_URL = BuildConfig.DEFAULT_SERVER_URL;
    public static final String DEFAULT_CHAT_SERVER_URL = BuildConfig.DEFAULT_CHAT_SERVER_URL;
    public static final String DEFAULT_FAMILY_SERVICE_URL = "http://localhost:8082";
    
    private SecureConfig(Context context) {
        this.context = context.getApplicationContext();
        this.encryptedPrefs = createEncryptedPrefs();
        this.regularPrefs = context.getSharedPreferences("openclaw_config", Context.MODE_PRIVATE);
    }
    
    public static synchronized SecureConfig getInstance(Context context) {
        if (instance == null) {
            instance = new SecureConfig(context.getApplicationContext());
        }
        return instance;
    }
    
    private SharedPreferences createEncryptedPrefs() {
        try {
            MasterKey masterKey = new MasterKey.Builder(context)
                .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
                .build();
            
            return EncryptedSharedPreferences.create(
                context,
                PREFS_NAME,
                masterKey,
                EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
                EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
            );
        } catch (Exception e) {
            Log.e(TAG, "无法创建加密存储，使用普通存储", e);
            return context.getSharedPreferences(PREFS_NAME + "_fallback", Context.MODE_PRIVATE);
        }
    }
    
    // ========== 敏感信息存储（加密）==========
    
    public void setApiKey(String apiKey) {
        encryptedPrefs.edit().putString(KEY_API_KEY, apiKey).apply();
        Log.d(TAG, "API Key 已安全保存");
    }
    
    public String getApiKey() {
        return encryptedPrefs.getString(KEY_API_KEY, "");
    }
    
    public void setDeviceToken(String token) {
        encryptedPrefs.edit().putString(KEY_DEVICE_TOKEN, token).apply();
    }
    
    public String getDeviceToken() {
        return encryptedPrefs.getString(KEY_DEVICE_TOKEN, "");
    }
    
    public boolean hasDeviceToken() {
        String token = getDeviceToken();
        return token != null && !token.isEmpty();
    }
    
    public void setDeviceId(String deviceId) {
        encryptedPrefs.edit().putString(KEY_DEVICE_ID, deviceId).apply();
    }
    
    public String getDeviceId() {
        String id = encryptedPrefs.getString(KEY_DEVICE_ID, null);
        if (id == null) {
            id = generateDeviceId();
            setDeviceId(id);
        }
        return id;
    }
    
    // ========== 非敏感配置 ==========
    
    public void setServerUrl(String url) {
        regularPrefs.edit().putString(KEY_SERVER_URL, url).apply();
    }
    
    public String getServerUrl() {
        return regularPrefs.getString(KEY_SERVER_URL, DEFAULT_SERVER_URL);
    }
    
    public void setChatServerUrl(String url) {
        regularPrefs.edit().putString(KEY_CHAT_SERVER_URL, url).apply();
    }
    
    public String getChatServerUrl() {
        return regularPrefs.getString(KEY_CHAT_SERVER_URL, DEFAULT_CHAT_SERVER_URL);
    }
    
    // ========== 工具方法 ==========
    
    private String generateDeviceId() {
        SecureRandom random = new SecureRandom();
        byte[] bytes = new byte[8];
        random.nextBytes(bytes);
        return "android_" + Base64.getUrlEncoder().withoutPadding().encodeToString(bytes);
    }
    
    public boolean isConfigured() {
        return hasDeviceToken() || !getApiKey().isEmpty();
    }
    
    public void clearSensitiveData() {
        encryptedPrefs.edit().clear().apply();
        Log.d(TAG, "敏感数据已清除");
    }
    
    public void clearAll() {
        encryptedPrefs.edit().clear().apply();
        regularPrefs.edit().clear().apply();
        Log.d(TAG, "所有配置已清除");
    }
    
    public JSONObject toDeviceInfo() {
        try {
            JSONObject info = new JSONObject();
            info.put("device_id", getDeviceId());
            info.put("has_token", hasDeviceToken());
            info.put("server_url", getServerUrl());
            return info;
        } catch (Exception e) {
            return new JSONObject();
        }
    }
    
    // ========== 通用配置方法 ==========
    
    public void setString(String key, String value) {
        regularPrefs.edit().putString(key, value).apply();
    }
    
    public String getString(String key, String defaultValue) {
        return regularPrefs.getString(key, defaultValue);
    }
    
    public void setInt(String key, int value) {
        regularPrefs.edit().putInt(key, value).apply();
    }
    
    public int getInt(String key, int defaultValue) {
        return regularPrefs.getInt(key, defaultValue);
    }
    
    public void setBoolean(String key, boolean value) {
        regularPrefs.edit().putBoolean(key, value).apply();
    }
    
    public boolean getBoolean(String key, boolean defaultValue) {
        return regularPrefs.getBoolean(key, defaultValue);
    }
    
    // ========== 快捷方法（兼容 ConfigManager）==========
    
    public void setDashScopeApiKey(String apiKey) {
        encryptedPrefs.edit().putString(KEY_DASHSCOPE_API_KEY, apiKey).apply();
    }
    
    public String getDashScopeApiKey() {
        return encryptedPrefs.getString(KEY_DASHSCOPE_API_KEY, "");
    }
    
    public boolean isDashScopeConfigured() {
        String apiKey = getDashScopeApiKey();
        return apiKey != null && !apiKey.isEmpty() && apiKey.startsWith("sk-");
    }
    
    public void setFamilyServiceUrl(String url) {
        setString(KEY_FAMILY_SERVICE_URL, url);
    }
    
    public String getFamilyServiceUrl() {
        return getString(KEY_FAMILY_SERVICE_URL, DEFAULT_FAMILY_SERVICE_URL);
    }
    
    public void setFeishuWebhook(String webhook) {
        setString(KEY_FEISHU_WEBHOOK, webhook);
    }
    
    public String getFeishuWebhook() {
        return getString(KEY_FEISHU_WEBHOOK, "");
    }
    
    public void clear(String key) {
        regularPrefs.edit().remove(key).apply();
        encryptedPrefs.edit().remove(key).apply();
    }
    
    public String exportConfig() {
        StringBuilder sb = new StringBuilder();
        sb.append("服务器 URL: ").append(getServerUrl()).append("\n");
        sb.append("DashScope 配置: ").append(isDashScopeConfigured() ? "已配置" : "未配置").append("\n");
        sb.append("设备 Token: ").append(hasDeviceToken() ? "已获取" : "未获取").append("\n");
        return sb.toString();
    }
    
    public org.json.JSONObject getConfig() {
        return new org.json.JSONObject();
    }
    
    public void saveConfig() {
    }
    
    public org.json.JSONArray getAutomationRules() {
        return new org.json.JSONArray();
    }
    
    public boolean isAutomationEnabled() {
        return getBoolean("automation_enabled", false);
    }
}