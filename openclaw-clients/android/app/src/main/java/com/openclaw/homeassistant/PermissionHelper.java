package com.openclaw.homeassistant;

import android.app.Activity;
import android.app.AlarmManager;
import android.content.Context;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.PowerManager;
import android.provider.Settings;

import androidx.activity.result.ActivityResultLauncher;
import androidx.appcompat.app.AlertDialog;
import androidx.core.content.ContextCompat;

/**
 * 权限辅助工具
 * 处理 Android 12+ 的特殊权限请求
 */
public class PermissionHelper {
    
    /**
     * 检查并请求精确闹钟权限 (Android 12+)
     */
    public static void checkAndRequestAlarmPermission(Activity activity, ActivityResultLauncher<String> launcher) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            AlarmManager alarmManager = (AlarmManager) activity.getSystemService(Context.ALARM_SERVICE);
            if (alarmManager != null && !alarmManager.canScheduleExactAlarms()) {
                new AlertDialog.Builder(activity)
                    .setTitle("需要精确闹钟权限")
                    .setMessage("自动化场景需要精确闹钟权限才能按时触发。是否前往设置页面授权？")
                    .setPositiveButton("去设置", (dialog, which) -> {
                        Intent intent = new Intent(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM);
                        intent.setData(Uri.parse("package:" + activity.getPackageName()));
                        launcher.launch(Settings.ACTION_REQUEST_SCHEDULE_EXACT_ALARM);
                    })
                    .setNegativeButton("稍后", null)
                    .show();
            }
        }
    }
    
    /**
     * 检查是否有精确闹钟权限
     */
    public static boolean hasAlarmPermission(Context context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
            AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
            return alarmManager != null && alarmManager.canScheduleExactAlarms();
        }
        return true;
    }
    
    /**
     * 检查并请求忽略电池优化权限
     */
    public static void checkAndRequestBatteryOptimization(Activity activity) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            PowerManager powerManager = (PowerManager) activity.getSystemService(Context.POWER_SERVICE);
            if (powerManager != null && !powerManager.isIgnoringBatteryOptimizations(activity.getPackageName())) {
                new AlertDialog.Builder(activity)
                    .setTitle("电池优化设置")
                    .setMessage("为确保自动化服务稳定运行，建议将本应用加入电池优化白名单。")
                    .setPositiveButton("去设置", (dialog, which) -> {
                        Intent intent = new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS);
                        intent.setData(Uri.parse("package:" + activity.getPackageName()));
                        activity.startActivity(intent);
                    })
                    .setNegativeButton("取消", null)
                    .show();
            }
        }
    }
    
    /**
     * 检查通知权限 (Android 13+)
     */
    public static boolean hasNotificationPermission(Context context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            return ContextCompat.checkSelfPermission(context, android.Manifest.permission.POST_NOTIFICATIONS)
                    == PackageManager.PERMISSION_GRANTED;
        }
        return true;
    }
}
