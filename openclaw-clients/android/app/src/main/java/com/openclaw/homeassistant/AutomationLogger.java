package com.openclaw.homeassistant;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/**
 * 自动化日志记录器
 * 功能：记录规则触发历史
 */
public class AutomationLogger {
    
    private static final String TAG = "AutomationLogger";
    private static final String PREFS_NAME = "automation_logs";
    private static final String KEY_LOGS = "logs";
    private static final int MAX_LOGS = 100;
    
    private final Context context;
    private final SimpleDateFormat dateFormat;
    
    public AutomationLogger(Context context) {
        this.context = context.getApplicationContext();
        this.dateFormat = new SimpleDateFormat("MM-dd HH:mm", Locale.getDefault());
    }
    
    /**
     * 记录规则触发
     */
    public void logTrigger(String ruleId, String ruleName, String triggerType) {
        try {
            JSONObject logEntry = new JSONObject();
            logEntry.put("timestamp", System.currentTimeMillis());
            logEntry.put("ruleId", ruleId);
            logEntry.put("ruleName", ruleName);
            logEntry.put("triggerType", triggerType);
            logEntry.put("action", "executed");
            
            saveLog(logEntry);
            
            Log.d(TAG, "记录触发：" + ruleName + " (" + triggerType + ")");
            
        } catch (Exception e) {
            Log.e(TAG, "记录日志失败", e);
        }
    }
    
    /**
     * 记录动作执行
     */
    public void logAction(String ruleId, String actionType, String details) {
        try {
            JSONObject logEntry = new JSONObject();
            logEntry.put("timestamp", System.currentTimeMillis());
            logEntry.put("ruleId", ruleId);
            logEntry.put("actionType", actionType);
            logEntry.put("details", details);
            
            saveLog(logEntry);
            
        } catch (Exception e) {
            Log.e(TAG, "记录动作失败", e);
        }
    }
    
    /**
     * 保存日志
     */
    private synchronized void saveLog(JSONObject logEntry) {
        try {
            SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
            String logsJson = prefs.getString(KEY_LOGS, "[]");
            JSONArray logs = new JSONArray(logsJson);
            
            // 添加到开头
            logs.put(0, logEntry);
            
            // 限制数量
            if (logs.length() > MAX_LOGS) {
                JSONArray newLogs = new JSONArray();
                for (int i = 0; i < MAX_LOGS; i++) {
                    newLogs.put(logs.getJSONObject(i));
                }
                logs = newLogs;
            }
            
            prefs.edit().putString(KEY_LOGS, logs.toString()).apply();
            
        } catch (Exception e) {
            Log.e(TAG, "保存日志失败", e);
        }
    }
    
    /**
     * 获取所有日志
     */
    public List<LogEntry> getLogs() {
        List<LogEntry> logs = new ArrayList<>();
        
        try {
            SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
            String logsJson = prefs.getString(KEY_LOGS, "[]");
            JSONArray logsArray = new JSONArray(logsJson);
            
            for (int i = 0; i < logsArray.length(); i++) {
                JSONObject obj = logsArray.getJSONObject(i);
                logs.add(LogEntry.fromJson(obj));
            }
            
        } catch (Exception e) {
            Log.e(TAG, "读取日志失败", e);
        }
        
        return logs;
    }
    
    /**
     * 清空日志
     */
    public void clearLogs() {
        SharedPreferences prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        prefs.edit().putString(KEY_LOGS, "[]").apply();
        Log.d(TAG, "日志已清空");
    }
    
    /**
     * 获取最近触发次数
     */
    public int getTriggerCount(String ruleId) {
        int count = 0;
        try {
            List<LogEntry> logs = getLogs();
            for (LogEntry log : logs) {
                if (ruleId.equals(log.ruleId)) {
                    count++;
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "统计触发次数失败", e);
        }
        return count;
    }
    
    /**
     * 日志条目
     */
    public static class LogEntry {
        public long timestamp;
        public String ruleId;
        public String ruleName;
        public String triggerType;
        public String actionType;
        public String details;
        public String action;
        
        public String getFormattedTime() {
            return new SimpleDateFormat("MM-dd HH:mm", Locale.getDefault())
                .format(new Date(timestamp));
        }
        
        public String getDisplayText() {
            if (ruleName != null) {
                return ruleName + " 触发 (" + triggerType + ")";
            } else if (actionType != null) {
                return "执行：" + actionType + " - " + details;
            }
            return "未知操作";
        }
        
        public static LogEntry fromJson(JSONObject json) {
            LogEntry entry = new LogEntry();
            entry.timestamp = json.optLong("timestamp", 0);
            entry.ruleId = json.optString("ruleId");
            entry.ruleName = json.optString("ruleName");
            entry.triggerType = json.optString("triggerType");
            entry.actionType = json.optString("actionType");
            entry.details = json.optString("details");
            entry.action = json.optString("action");
            return entry;
        }
    }
}
