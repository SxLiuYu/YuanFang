package com.openclaw.homeassistant;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.AccessibilityServiceInfo;
import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;
import android.view.accessibility.AccessibilityEvent;

import java.util.ArrayList;
import java.util.List;

/**
 * 应用启动触发服务 (使用无障碍服务)
 * 功能：打开特定 App 时触发自动化
 */
public class AppLaunchTriggerService extends AccessibilityService {
    
    private static final String TAG = "AppLaunchTriggerService";
    private static final String PREFS_NAME = "app_triggers";
    
    private static AppLaunchTriggerService instance;
    private SharedPreferences prefs;
    private String lastPackageName = null;
    
    public interface AppLaunchListener {
        void onAppLaunched(String packageName, String appName);
    }
    
    private static AppLaunchListener listener;
    
    public static void setListener(AppLaunchListener listener) {
        AppLaunchTriggerService.listener = listener;
    }
    
    @Override
    public void onServiceConnected() {
        super.onServiceConnected();
        instance = this;
        prefs = getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        
        AccessibilityServiceInfo info = new AccessibilityServiceInfo();
        info.eventTypes = AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED;
        info.feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC;
        info.flags = AccessibilityServiceInfo.DEFAULT;
        setServiceInfo(info);
        
        Log.d(TAG, "无障碍服务已连接");
    }
    
    @Override
    public void onAccessibilityEvent(AccessibilityEvent event) {
        if (event.getEventType() == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) {
            String packageName = (String) event.getPackageName();
            
            if (packageName != null && !packageName.equals(lastPackageName)) {
                lastPackageName = packageName;
                handleAppLaunch(packageName);
            }
        }
    }
    
    @Override
    public void onInterrupt() {
        Log.w(TAG, "无障碍服务中断");
    }
    
    /**
     * 处理应用启动
     */
    private void handleAppLaunch(String packageName) {
        // 检查是否绑定了动作
        String actionId = prefs.getString("app_" + packageName, null);
        
        if (actionId != null) {
            Log.d(TAG, "应用启动触发：" + packageName + " → " + actionId);
            
            if (listener != null) {
                listener.onAppLaunched(packageName, getAppName(packageName));
            }
            
            // 触发自动化动作
            triggerAction(packageName, actionId);
        }
    }
    
    /**
     * 触发绑定动作
     */
    private void triggerAction(String packageName, String actionId) {
        // 集成到自动化引擎
        NotificationHelper.sendHealthNotification(this,
            "📱 应用启动触发",
            "打开 " + getAppName(packageName) + "，执行动作：" + actionId);
    }
    
    /**
     * 获取应用名称
     */
    private String getAppName(String packageName) {
        try {
            return getPackageManager()
                .getApplicationLabel(
                    getPackageManager().getApplicationInfo(packageName, 0))
                .toString();
        } catch (Exception e) {
            return packageName;
        }
    }
    
    /**
     * 绑定应用到动作
     */
    public void bindAppToAction(String packageName, String actionId) {
        prefs.edit().putString("app_" + packageName, actionId).apply();
        Log.d(TAG, "应用绑定：" + packageName + " → " + actionId);
    }
    
    /**
     * 解绑应用
     */
    public void unbindApp(String packageName) {
        prefs.edit().remove("app_" + packageName).apply();
        Log.d(TAG, "应用解绑：" + packageName);
    }
    
    /**
     * 获取已绑定的应用列表
     */
    public List<String> getBoundApps() {
        List<String> apps = new ArrayList<>();
        for (String key : prefs.getAll().keySet()) {
            if (key.startsWith("app_")) {
                apps.add(key.substring(4));
            }
        }
        return apps;
    }
    
    /**
     * 检查服务是否运行
     */
    public static boolean isRunning() {
        return instance != null;
    }
    
    /**
     * 获取实例
     */
    public static AppLaunchTriggerService getInstance() {
        return instance;
    }
}
