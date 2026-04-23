package com.openclaw.homeassistant;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * 健康提醒广播接收器
 */
public class HealthReminderReceiver extends BroadcastReceiver {
    
    private static final String TAG = "HealthReminderReceiver";
    
    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        
        Log.d(TAG, "收到健康提醒：" + action);
        
        if (action == null) return;
        
        HealthReminderService service = new HealthReminderService(context);
        
        switch (action) {
            case "SIT_REMINDER":
                service.triggerSitReminder();
                service.startSitReminder();
                break;
                
            case "WATER_REMINDER":
                service.triggerWaterReminder();
                service.startWaterReminder();
                break;
                
            case "EYE_REMINDER":
                service.triggerEyeReminder();
                service.startEyeReminder();
                break;
            
            // 生活提醒
            case "BREAKFAST_REMINDER":
                service.triggerBreakfastReminder();
                service.startBreakfastReminder();
                break;
                
            case "LUNCH_REMINDER":
                service.triggerLunchReminder();
                service.startLunchReminder();
                break;
                
            case "DINNER_REMINDER":
                service.triggerDinnerReminder();
                service.startDinnerReminder();
                break;
                
            case "SLEEP_REMINDER":
                service.triggerSleepReminder();
                service.startSleepReminder();
                break;
                
            case "WAKEUP_REMINDER":
                service.triggerWakeUpReminder();
                service.startWakeUpReminder();
                break;
        }
    }
}
