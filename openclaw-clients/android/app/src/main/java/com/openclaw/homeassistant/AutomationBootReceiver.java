package com.openclaw.homeassistant;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * 开机启动接收器
 * 设备启动后自动启动自动化引擎
 */
public class AutomationBootReceiver extends BroadcastReceiver {
    
    private static final String TAG = "AutomationBootReceiver";
    
    @Override
    public void onReceive(Context context, Intent intent) {
        if (Intent.ACTION_BOOT_COMPLETED.equals(intent.getAction()) ||
            "android.intent.action.QUICKBOOT_POWERON".equals(intent.getAction())) {
            
            Log.d(TAG, "设备启动完成，检查自动化配置");
            
            // 检查自动化是否启用
            ConfigManager configManager = new ConfigManager(context);
            if (configManager.isAutomationEnabled()) {
                Log.d(TAG, "自动化已启用，启动引擎");
                
                // 启动自动化服务（后台）
                Intent serviceIntent = new Intent(context, AutomationService.class);
                serviceIntent.setAction(AutomationService.ACTION_START);
                
                if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.O) {
                    context.startForegroundService(serviceIntent);
                } else {
                    context.startService(serviceIntent);
                }
            } else {
                Log.d(TAG, "自动化未启用，跳过");
            }
        }
    }
}
