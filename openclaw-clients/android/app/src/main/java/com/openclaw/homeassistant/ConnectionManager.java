package com.openclaw.homeassistant;

import android.content.Context;
import android.content.SharedPreferences;
import okhttp3.*;
import org.json.JSONObject;
import java.util.concurrent.TimeUnit;

public class ConnectionManager {
    private static final String SERVER_URL_PREFERENCE = "control_server_url";
    private static final String DEFAULT_URL = "ws://localhost:8080/ws";
    
    private final SharedPreferences preferences;
    private OkHttpClient client;
    private WebSocket webSocket;
    private boolean isConnected = false;
    
    public interface ConnectionListener {
        void onConnected();
        void onDisconnected(String reason);
        void onMessageReceived(String message);
        void onError(String error);
    }
    
    private ConnectionListener listener;
    
    public ConnectionManager(Context context) {
        this.preferences = context.getSharedPreferences("OpenClawPrefs", Context.MODE_PRIVATE);
        this.client = new OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build();
    }
    
    public void setConnectionListener(ConnectionListener listener) {
        this.listener = listener;
    }
    
    public void connect() {
        String serverUrl = preferences.getString(SERVER_URL_PREFERENCE, DEFAULT_URL);
        
        Request request = new Request.Builder()
            .url(serverUrl)
            .build();
        
        webSocket = client.newWebSocket(request, new WebSocketListener() {
            @Override
            public void onOpen(WebSocket webSocket, Response response) {
                isConnected = true;
                if (listener != null) {
                    listener.onConnected();
                }
            }
            
            @Override
            public void onMessage(WebSocket webSocket, String text) {
                if (listener != null) {
                    listener.onMessageReceived(text);
                }
            }
            
            @Override
            public void onClosing(WebSocket webSocket, int code, String reason) {
                webSocket.close(1000, null);
                isConnected = false;
                if (listener != null) {
                    listener.onDisconnected(reason);
                }
            }
            
            @Override
            public void onFailure(WebSocket webSocket, Throwable t, Response response) {
                isConnected = false;
                if (listener != null) {
                    listener.onError("连接失败: " + t.getMessage());
                }
            }
        });
    }
    
    public void disconnect() {
        if (webSocket != null) {
            webSocket.close(1000, "正常关闭");
            isConnected = false;
        }
    }
    
    public void sendMessage(String type, String query, String response) {
        if (webSocket != null && isConnected) {
            try {
                JSONObject message = new JSONObject();
                message.put("type", type);
                message.put("query", query);
                message.put("response", response);
                message.put("timestamp", System.currentTimeMillis());
                
                webSocket.send(message.toString());
            } catch (Exception e) {
                if (listener != null) {
                    listener.onError("发送消息失败: " + e.getMessage());
                }
            }
        } else {
            if (listener != null) {
                listener.onError("未连接到控制服务器");
            }
        }
    }
    
    public boolean isConnected() {
        return isConnected;
    }
    
    public void saveServerUrl(String url) {
        preferences.edit().putString(SERVER_URL_PREFERENCE, url).apply();
    }
}