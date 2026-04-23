package com.openclaw.homeassistant;

import android.Manifest;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.content.pm.PackageManager;
import android.location.Address;
import android.location.Geocoder;
import android.location.Location;
import android.location.LocationManager;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.os.BatteryManager;
import android.os.Build;
import android.os.Environment;
import android.os.StatFs;
import android.provider.ContactsContract;
import android.database.Cursor;

import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * 扩展设备数据读取器
 * 功能：位置、网络、设备信息、联系人、存储等
 */
public class ExtendedDeviceReader {
    
    private final Context context;
    
    public ExtendedDeviceReader(Context context) {
        this.context = context;
    }
    
    /**
     * 获取当前位置
     */
    public String getLocation() {
        try {
            LocationManager locationManager = (LocationManager) 
                context.getSystemService(Context.LOCATION_SERVICE);
            
            if (locationManager == null) {
                return "位置服务不可用";
            }
            
            // 检查权限
            if (androidx.core.content.ContextCompat.checkSelfPermission(
                    context, Manifest.permission.ACCESS_FINE_LOCATION) 
                    != PackageManager.PERMISSION_GRANTED) {
                return "⚠️ 需要位置权限 (设置→应用→权限)";
            }
            
            // 检查 GPS 是否启用
            if (!locationManager.isProviderEnabled(LocationManager.GPS_PROVIDER)) {
                return "⚠️ GPS 未启用，请打开位置服务";
            }
            
            // 获取最后已知位置
            Location location = null;
            try {
                location = locationManager.getLastKnownLocation(LocationManager.GPS_PROVIDER);
            } catch (Exception e) {
                // GPS 失败，尝试网络定位
            }
            
            if (location == null) {
                try {
                    location = locationManager.getLastKnownLocation(LocationManager.NETWORK_PROVIDER);
                } catch (Exception e) {
                    return "无法获取位置，请检查网络连接";
                }
            }
            
            if (location != null) {
                double lat = location.getLatitude();
                double lon = location.getLongitude();
                
                // 反向地理编码
                try {
                    Geocoder geocoder = new Geocoder(context, Locale.CHINA);
                    List<Address> addresses = geocoder.getFromLocation(lat, lon, 1);
                    if (addresses != null && !addresses.isEmpty()) {
                        Address addr = addresses.get(0);
                        StringBuilder sb = new StringBuilder();
                        if (addr.getCountryName() != null) sb.append(addr.getCountryName());
                        if (addr.getAdminArea() != null) sb.append(addr.getAdminArea());
                        if (addr.getLocality() != null) sb.append(addr.getLocality());
                        if (addr.getThoroughfare() != null) sb.append(addr.getThoroughfare());
                        return sb.toString();
                    }
                } catch (Exception e) {
                    // 地理编码失败
                }
                
                return String.format("纬度：%.4f, 经度：%.4f", lat, lon);
            }
            
            return "无法获取位置";
        } catch (Exception e) {
            return "位置获取失败：" + e.getMessage();
        }
    }
    
    /**
     * 获取网络状态
     */
    public String getNetworkStatus() {
        ConnectivityManager cm = (ConnectivityManager) 
            context.getSystemService(Context.CONNECTIVITY_SERVICE);
        
        if (cm == null) {
            return "网络服务不可用";
        }
        
        NetworkInfo activeNetwork = cm.getActiveNetworkInfo();
        
        if (activeNetwork == null || !activeNetwork.isConnected()) {
            return "❌ 未连接网络";
        }
        
        StringBuilder sb = new StringBuilder();
        sb.append("✅ 网络已连接\n");
        sb.append("类型：").append(activeNetwork.getTypeName()).append("\n");
        sb.append("子类型：").append(activeNetwork.getSubtypeName());
        
        return sb.toString();
    }
    
    /**
     * 获取 WiFi 信息
     */
    public String getWifiInfo() {
        WifiManager wifiManager = (WifiManager) 
            context.getApplicationContext().getSystemService(Context.WIFI_SERVICE);
        
        if (wifiManager == null || !wifiManager.isWifiEnabled()) {
            return "WiFi 未开启";
        }
        
        WifiInfo wifiInfo = wifiManager.getConnectionInfo();
        if (wifiInfo == null) {
            return "未连接 WiFi";
        }
        
        String ssid = wifiInfo.getSSID();
        if (ssid.startsWith("\"") && ssid.endsWith("\"")) {
            ssid = ssid.substring(1, ssid.length() - 1);
        }
        
        int rssi = wifiInfo.getRssi();
        String signalStrength;
        if (rssi >= -50) signalStrength = "极好";
        else if (rssi >= -60) signalStrength = "良好";
        else if (rssi >= -70) signalStrength = "一般";
        else signalStrength = "较差";
        
        return String.format("📶 %s\n信号：%s (%d dBm)", ssid, signalStrength, rssi);
    }
    
    /**
     * 获取设备信息
     */
    public String getDeviceInfo() {
        StringBuilder sb = new StringBuilder();
        
        sb.append("📱 设备型号：").append(Build.MODEL).append("\n");
        sb.append("🏭 品牌：").append(Build.MANUFACTURER).append("\n");
        sb.append("🤖 Android 版本：").append(Build.VERSION.RELEASE);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            sb.append(" (API ").append(Build.VERSION.SDK_INT).append(")");
        }
        sb.append("\n");
        
        // 屏幕信息
        android.util.DisplayMetrics metrics = context.getResources().getDisplayMetrics();
        sb.append("📺 屏幕：").append(metrics.widthPixels)
          .append("x").append(metrics.heightPixels)
          .append(" (").append((int)(metrics.density * 160)).append(" DPI)\n");
        
        return sb.toString();
    }
    
    /**
     * 获取存储信息
     */
    public String getStorageInfo() {
        StringBuilder sb = new StringBuilder();
        
        // 内部存储
        File internalDir = Environment.getDataDirectory();
        StatFs internalStat = new StatFs(internalDir.getPath());
        long internalTotal = internalStat.getTotalBytes();
        long internalFree = internalStat.getFreeBytes();
        long internalUsed = internalTotal - internalFree;
        
        sb.append("💾 内部存储:\n");
        sb.append("  已用：").append(formatSize(internalUsed)).append("\n");
        sb.append("  可用：").append(formatSize(internalFree)).append("\n");
        sb.append("  总计：").append(formatSize(internalTotal)).append("\n\n");
        
        // 外部存储（SD 卡）
        if (Environment.isExternalStorageRemovable()) {
            File externalDir = Environment.getExternalStorageDirectory();
            StatFs externalStat = new StatFs(externalDir.getPath());
            long externalTotal = externalStat.getTotalBytes();
            long externalFree = externalStat.getFreeBytes();
            
            sb.append("📀 SD 卡:\n");
            sb.append("  已用：").append(formatSize(externalTotal - externalFree)).append("\n");
            sb.append("  可用：").append(formatSize(externalFree)).append("\n");
            sb.append("  总计：").append(formatSize(externalTotal));
        } else {
            sb.append("📀 无 SD 卡");
        }
        
        return sb.toString();
    }
    
    /**
     * 格式化存储大小
     */
    private String formatSize(long size) {
        if (size < 1024) return size + " B";
        if (size < 1024 * 1024) return (size / 1024) + " KB";
        if (size < 1024 * 1024 * 1024) return (size / (1024 * 1024)) + " MB";
        return String.format("%.2f GB", size / (1024.0 * 1024 * 1024));
    }
    
    /**
     * 查询联系人
     */
    public String searchContacts(String query) {
        if (query == null || query.isEmpty()) {
            return "请输入搜索关键词";
        }
        
        try {
            // 检查权限
            if (androidx.core.content.ContextCompat.checkSelfPermission(
                    context, Manifest.permission.READ_CONTACTS) 
                    != PackageManager.PERMISSION_GRANTED) {
                return "需要联系人权限";
            }
            
            Cursor cursor = context.getContentResolver().query(
                ContactsContract.Contacts.CONTENT_URI,
                null,
                ContactsContract.Contacts.DISPLAY_NAME + " LIKE ?",
                new String[]{"%" + query + "%"},
                ContactsContract.Contacts.DISPLAY_NAME + " ASC LIMIT 10"
            );
            
            if (cursor == null) {
                return "未找到联系人";
            }
            
            StringBuilder sb = new StringBuilder();
            int count = 0;
            int nameIndex = cursor.getColumnIndex(ContactsContract.Contacts.DISPLAY_NAME);
            
            while (cursor.moveToNext() && count < 10) {
                String name = cursor.getString(nameIndex);
                sb.append("• ").append(name).append("\n");
                count++;
            }
            
            cursor.close();
            
            if (count == 0) {
                return "未找到匹配的联系人";
            }
            
            return sb.toString();
        } catch (Exception e) {
            return "查询失败：" + e.getMessage();
        }
    }
    
    /**
     * 获取电池详细信息
     */
    public String getBatteryHealth() {
        Intent intent;
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.TIRAMISU) {
            intent = context.registerReceiver(null, 
                new IntentFilter(Intent.ACTION_BATTERY_CHANGED),
                Context.RECEIVER_NOT_EXPORTED);
        } else {
            intent = context.registerReceiver(null, 
                new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
        }
        
        if (intent == null) {
            return "电池信息不可用";
        }
        
        int level = intent.getIntExtra("level", 0);
        int scale = intent.getIntExtra("scale", 100);
        int health = intent.getIntExtra("health", 0);
        int voltage = intent.getIntExtra("voltage", 0);
        int temperature = intent.getIntExtra("temperature", 0);
        
        String healthStr;
        switch (health) {
            case 1: healthStr = "未知"; break;
            case 2: healthStr = "良好"; break;
            case 3: healthStr = "过热"; break;
            case 4: healthStr = "电压低"; break;
            case 5: healthStr = "电压高"; break;
            case 6: healthStr = "死亡"; break;
            default: healthStr = "未知";
        }
        
        return String.format(
            "电量：%d%%\n健康：%s\n电压：%d mV\n温度：%.1f°C",
            (level * 100) / scale, healthStr, voltage, temperature / 10.0
        );
    }
    
    /**
     * 获取 RAM 信息
     */
    public String getRamInfo() {
        android.app.ActivityManager.MemoryInfo mi = 
            new android.app.ActivityManager.MemoryInfo();
        android.app.ActivityManager activityManager = 
            (android.app.ActivityManager) context.getSystemService(
                Context.ACTIVITY_SERVICE);
        
        if (activityManager == null) {
            return "无法获取内存信息";
        }
        
        activityManager.getMemoryInfo(mi);
        
        long totalRam = mi.totalMem;
        long availRam = mi.availMem;
        long usedRam = totalRam - availRam;
        
        return String.format(
            "🧠 运行内存:\n  已用：%s\n  可用：%s\n  总计：%s",
            formatSize(usedRam), formatSize(availRam), formatSize(totalRam)
        );
    }
}
