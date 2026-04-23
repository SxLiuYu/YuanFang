package com.openclaw.homeassistant;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Intent;
import android.os.Build;
import android.os.IBinder;
import android.util.Log;

import androidx.annotation.Nullable;
import androidx.core.app.NotificationCompat;

/**
 * 自动化后台服务
 * 保持自动化引擎在后台运行
 */
public class AutomationService extends Service {
    
    private static final String TAG = "AutomationService";
    private static final String NOTIFICATION_CHANNEL_ID = "automation_service";
    private static final int NOTIFICATION_ID = 1001;
    
    public static final String ACTION_START = "com.openclaw.action.START_AUTOMATION";
    public static final String ACTION_STOP = "com.openclaw.action.STOP_AUTOMATION";
    
    private AutomationEngine automationEngine;
    private ConfigManager configManager;
    private DashScopeService dashScopeService;
    
    @Override
    public void onCreate() {
        super.onCreate();
        Log.d(TAG, "服务创建");
        
        createNotificationChannel();
        
        configManager = new ConfigManager(this);
        dashScopeService = new DashScopeService(this);
        automationEngine = new AutomationEngine(this, configManager, dashScopeService);
    }
    
    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent == null) {
            return START_STICKY;
        }
        
        String action = intent.getAction();
        
        if (ACTION_START.equals(action)) {
            Log.d(TAG, "启动自动化服务");
            startForeground(NOTIFICATION_ID, createNotification());
            automationEngine.start();
        } else if (ACTION_STOP.equals(action)) {
            Log.d(TAG, "停止自动化服务");
            stopSelf();
        }
        
        return START_STICKY;
    }
    
    @Nullable
    @Override
    public IBinder onBind(Intent intent) {
        return null;
    }
    
    @Override
    public void onDestroy() {
        Log.d(TAG, "服务销毁");
        
        if (automationEngine != null) {
            automationEngine.stop();
        }
        
        super.onDestroy();
    }
    
    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                NOTIFICATION_CHANNEL_ID,
                "自动化服务",
                NotificationManager.IMPORTANCE_LOW
            );
            channel.setDescription("自动化引擎后台运行通知");
            channel.setShowBadge(false);
            
            NotificationManager manager = getSystemService(NotificationManager.class);
            if (manager != null) {
                manager.createNotificationChannel(channel);
            }
        }
    }
    
    private Notification createNotification() {
        Intent notificationIntent = new Intent(this, MainActivity.class);
        PendingIntent pendingIntent = PendingIntent.getActivity(
            this, 0, notificationIntent,
            PendingIntent.FLAG_IMMUTABLE
        );
        
        return new NotificationCompat.Builder(this, NOTIFICATION_CHANNEL_ID)
            .setContentTitle("OpenClaw 自动化")
            .setContentText("自动化引擎运行中")
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentIntent(pendingIntent)
            .setOngoing(true)
            .setPriority(NotificationCompat.PRIORITY_LOW)
            .build();
    }
}
