package com.openclaw.homeassistant;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.net.ConnectivityManager;
import android.net.NetworkInfo;
import android.net.wifi.WifiInfo;
import android.net.wifi.WifiManager;
import android.util.Log;

/**
 * 网络连接状态监听器
 * 功能：WiFi 连接/断开触发
 */
public class ConnectivityReceiver extends BroadcastReceiver {
    
    private static final String TAG = "ConnectivityReceiver";
    private static ConnectivityListener listener;
    
    public interface ConnectivityListener {
        void onWifiConnected(String ssid);
        void onWifiDisconnected();
        void onMobileDataConnected();
        void onMobileDataDisconnected();
    }
    
    public static void setListener(ConnectivityListener listener) {
        ConnectivityReceiver.listener = listener;
    }
    
    @Override
    public void onReceive(Context context, Intent intent) {
        String action = intent.getAction();
        
        if (ConnectivityManager.CONNECTIVITY_ACTION.equals(action)) {
            checkNetworkStatus(context);
        }
    }
    
    private void checkNetworkStatus(Context context) {
        ConnectivityManager cm = (ConnectivityManager) 
            context.getSystemService(Context.CONNECTIVITY_SERVICE);
        if (cm == null) return;
        
        NetworkInfo wifiInfo = cm.getNetworkInfo(ConnectivityManager.TYPE_WIFI);
        NetworkInfo mobileInfo = cm.getNetworkInfo(ConnectivityManager.TYPE_MOBILE);
        
        if (wifiInfo != null && wifiInfo.isConnected()) {
            // WiFi 已连接
            WifiManager wifiManager = (WifiManager) context.getApplicationContext()
                .getSystemService(Context.WIFI_SERVICE);
            if (wifiManager != null) {
                WifiInfo wifiInfo2 = wifiManager.getConnectionInfo();
                String ssid = wifiInfo2 != null ? wifiInfo2.getSSID() : "未知";
                if (ssid != null && ssid.startsWith("\"") && ssid.endsWith("\"")) {
                    ssid = ssid.substring(1, ssid.length() - 1);
                }
                
                Log.d(TAG, "WiFi 已连接：" + ssid);
                if (listener != null) {
                    listener.onWifiConnected(ssid);
                }
            }
        } else {
            // WiFi 已断开
            Log.d(TAG, "WiFi 已断开");
            if (listener != null) {
                listener.onWifiDisconnected();
            }
        }
        
        if (mobileInfo != null && mobileInfo.isConnected()) {
            Log.d(TAG, "移动数据已连接");
            if (listener != null) {
                listener.onMobileDataConnected();
            }
        } else {
            Log.d(TAG, "移动数据已断开");
            if (listener != null) {
                listener.onMobileDataDisconnected();
            }
        }
    }
}
