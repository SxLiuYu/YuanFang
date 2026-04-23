package com.openclaw.homeassistant;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.BatteryManager;
import android.content.Intent;
import android.content.IntentFilter;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.provider.Settings;
import android.util.Log;

import org.json.JSONObject;

/**
 * 设备数据上传服务
 * 定时上传设备数据到 OpenClaw 服务器（带鉴权）
 */
public class DeviceDataService {
    
    private static final String TAG = "DeviceDataService";
    private static final String PREFS_NAME = "device_data";
    private static final long UPLOAD_INTERVAL = 30 * 60 * 1000;  // 30 分钟
    
    private final Context context;
    private final SharedPreferences prefs;
    private final SecureConfig secureConfig;
    private Thread uploadThread;
    private boolean isRunning = false;
    
    public DeviceDataService(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        this.secureConfig = SecureConfig.getInstance(context);
    }
    
    /**
     * 启动定时上传
     */
    public void start() {
        if (isRunning) {
            Log.w(TAG, "已在运行中");
            return;
        }
        
        isRunning = true;
        uploadThread = new Thread(() -> {
            while (isRunning) {
                try {
                    // 立即上传一次
                    uploadDeviceData();
                    
                    // 等待下次上传
                    Thread.sleep(UPLOAD_INTERVAL);
                } catch (InterruptedException e) {
                    Log.w(TAG, "上传线程被中断");
                    break;
                } catch (Exception e) {
                    Log.e(TAG, "上传失败", e);
                    try {
                        Thread.sleep(60000);  // 失败后等待 1 分钟重试
                    } catch (InterruptedException ie) {
                        break;
                    }
                }
            }
        });
        uploadThread.start();
        Log.d(TAG, "定时上传已启动，间隔：" + (UPLOAD_INTERVAL / 60000) + "分钟");
    }
    
    /**
     * 停止定时上传
     */
    public void stop() {
        isRunning = false;
        if (uploadThread != null) {
            uploadThread.interrupt();
            uploadThread = null;
        }
        Log.d(TAG, "定时上传已停止");
    }
    
    /**
     * 立即上传设备数据
     */
    public void uploadDeviceData() {
        try {
            JSONObject data = buildDeviceData();
            boolean success = sendToDeviceServer(data);
            
            if (success) {
                Log.d(TAG, "设备数据上传成功");
                // 保存最后上传时间
                prefs.edit().putLong("last_upload", System.currentTimeMillis()).apply();
            } else {
                Log.e(TAG, "设备数据上传失败");
            }
        } catch (Exception e) {
            Log.e(TAG, "上传异常", e);
        }
    }
    
    /**
     * 构建设备数据 JSON
     */
    private JSONObject buildDeviceData() throws Exception {
        JSONObject data = new JSONObject();
        
        // 设备 ID
        String deviceId = Settings.Secure.getString(
            context.getContentResolver(),
            Settings.Secure.ANDROID_ID
        );
        data.put("device_id", deviceId != null ? deviceId : "unknown");
        
        // 电池信息
        JSONObject battery = new JSONObject();
        IntentFilter ifilter = new IntentFilter(Intent.ACTION_BATTERY_CHANGED);
        Intent batteryStatus = context.registerReceiver(null, ifilter);
        if (batteryStatus != null) {
            int level = batteryStatus.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
            int scale = batteryStatus.getIntExtra(BatteryManager.EXTRA_SCALE, -1);
            int batteryPct = (level >= 0 && scale > 0) ? (int) ((level / (float) scale) * 100) : 100;
            int status = batteryStatus.getIntExtra(BatteryManager.EXTRA_STATUS, -1);
            boolean isCharging = (status == BatteryManager.BATTERY_STATUS_CHARGING || 
                                 status == BatteryManager.BATTERY_STATUS_FULL);
            
            battery.put("level", batteryPct);
            battery.put("charging", isCharging);
        } else {
            battery.put("level", 100);
            battery.put("charging", false);
        }
        data.put("battery", battery);
        
        // 步数（需要从传感器或健康服务获取，这里暂时设为 0）
        // TODO: 集成 Google Fit 或华为运动健康
        data.put("steps", 0);
        
        // 网络状态
        JSONObject network = new JSONObject();
        ConnectivityManager cm = (ConnectivityManager) context.getSystemService(Context.CONNECTIVITY_SERVICE);
        NetworkInfo activeNetwork = cm != null ? cm.getActiveNetworkInfo() : null;
        if (activeNetwork != null && activeNetwork.isConnected()) {
            network.put("type", activeNetwork.getTypeName());
            network.put("connected", true);
        } else {
            network.put("type", "none");
            network.put("connected", false);
        }
        data.put("network", network);
        
        // 额外信息
        data.put("timestamp", System.currentTimeMillis());
        data.put("android_version", android.os.Build.VERSION.RELEASE);
        data.put("device_model", android.os.Build.BRAND + " " + android.os.Build.MODEL);
        
        return data;
    }
    
    /**
     * 发送到设备服务器
     */
    private boolean sendToDeviceServer(JSONObject data) {
        try {
            String serverUrl = secureConfig.getServerUrl();
            String apiKey = secureConfig.getApiKey();
            
            String response = HttpHelper.builder()
                .url(serverUrl + "/device-data")
                .method("POST")
                .body(data.toString())
                .authorization(apiKey)
                .header("User-Agent", "OpenClaw-Android/1.0")
                .execute();
            
            Log.d(TAG, "服务器响应：" + response);
            return true;
            
        } catch (Exception e) {
            Log.e(TAG, "发送失败", e);
            return false;
        }
    }
    
    /**
     * 获取最后上传时间
     */
    public long getLastUploadTime() {
        return prefs.getLong("last_upload", 0);
    }
    
    /**
     * 获取上传状态
     */
    public boolean isRunning() {
        return isRunning;
    }
}
