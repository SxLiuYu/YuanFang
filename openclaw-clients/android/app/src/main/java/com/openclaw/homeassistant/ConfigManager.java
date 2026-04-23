package com.openclaw.homeassistant;

import android.content.Context;

import org.json.JSONArray;
import org.json.JSONObject;

/**
 * ConfigManager - 配置管理类的包装器
 * 委托给SecureConfig实现所有功能
 */
public class ConfigManager {
    
    private static ConfigManager instance;
    private final SecureConfig secureConfig;
    private final Context context;
    
    public ConfigManager(Context context) {
        this.context = context.getApplicationContext();
        this.secureConfig = SecureConfig.getInstance(this.context);
    }
    
    public static synchronized ConfigManager getInstance(Context context) {
        if (instance == null) {
            instance = new ConfigManager(context.getApplicationContext());
        }
        return instance;
    }
    
    // 委托方法
    public void setApiKey(String apiKey) { secureConfig.setApiKey(apiKey); }
    public String getApiKey() { return secureConfig.getApiKey(); }
    public void setDeviceToken(String token) { secureConfig.setDeviceToken(token); }
    public String getDeviceToken() { return secureConfig.getDeviceToken(); }
    public boolean hasDeviceToken() { return secureConfig.hasDeviceToken(); }
    public String getDeviceId() { return secureConfig.getDeviceId(); }
    public void setServerUrl(String url) { secureConfig.setServerUrl(url); }
    public String getServerUrl() { return secureConfig.getServerUrl(); }
    public void setChatServerUrl(String url) { secureConfig.setChatServerUrl(url); }
    public String getChatServerUrl() { return secureConfig.getChatServerUrl(); }
    public void setString(String key, String value) { secureConfig.setString(key, value); }
    public String getString(String key, String defaultValue) { return secureConfig.getString(key, defaultValue); }
    public void setInt(String key, int value) { secureConfig.setInt(key, value); }
    public int getInt(String key, int defaultValue) { return secureConfig.getInt(key, defaultValue); }
    public void setBoolean(String key, boolean value) { secureConfig.setBoolean(key, value); }
    public boolean getBoolean(String key, boolean defaultValue) { return secureConfig.getBoolean(key, defaultValue); }
    public void setDashScopeApiKey(String apiKey) { secureConfig.setDashScopeApiKey(apiKey); }
    public String getDashScopeApiKey() { return secureConfig.getDashScopeApiKey(); }
    public boolean isDashScopeConfigured() { return secureConfig.isDashScopeConfigured(); }
    public void setFamilyServiceUrl(String url) { secureConfig.setFamilyServiceUrl(url); }
    public String getFamilyServiceUrl() { return secureConfig.getFamilyServiceUrl(); }
    public void setFeishuWebhook(String webhook) { secureConfig.setFeishuWebhook(webhook); }
    public String getFeishuWebhook() { return secureConfig.getFeishuWebhook(); }
    public boolean isConfigured() { return secureConfig.isConfigured(); }
    public void clear(String key) { secureConfig.clear(key); }
    public JSONObject getConfig() { return secureConfig.getConfig(); }
    public void saveConfig() { secureConfig.saveConfig(); }
    public JSONArray getAutomationRules() { return secureConfig.getAutomationRules(); }
    public boolean isAutomationEnabled() { return secureConfig.isAutomationEnabled(); }
    
    public JSONArray createDefaultAutomationRules() {
        JSONArray rules = new JSONArray();
        try {
            JSONObject morningRule = new JSONObject();
            morningRule.put("id", "morning_report");
            morningRule.put("name", "早安播报");
            morningRule.put("enabled", true);
            morningRule.put("trigger", "time:07:00");
            morningRule.put("actions", new JSONArray().put("weather_report").put("schedule_reminder"));
            rules.put(morningRule);
            
            JSONObject eveningRule = new JSONObject();
            eveningRule.put("id", "evening_summary");
            eveningRule.put("name", "晚安总结");
            eveningRule.put("enabled", true);
            eveningRule.put("trigger", "time:22:00");
            eveningRule.put("actions", new JSONArray().put("daily_summary").put("tomorrow_preview"));
            rules.put(eveningRule);
        } catch (Exception e) {
            e.printStackTrace();
        }
        return rules;
    }
}