package com.openclaw.homeassistant;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

/**
 * 任务提醒接收器
 * 接收定时提醒并发送通知
 */
public class TaskReminderReceiver extends BroadcastReceiver {

    private static final String TAG = "TaskReminderReceiver";

    @Override
    public void onReceive(Context context, Intent intent) {
        String taskId = intent.getStringExtra("task_id");
        String taskName = intent.getStringExtra("task_name");

        Log.d(TAG, "收到任务提醒：" + taskName);

        // 发送通知
        NotificationHelper.sendHealthNotification(
                context,
                "📋 任务提醒",
                "别忘了完成：" + taskName
        );
    }
}