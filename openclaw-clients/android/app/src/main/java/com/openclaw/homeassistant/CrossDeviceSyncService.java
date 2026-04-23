package com.openclaw.homeassistant;

import android.content.Context;
import android.content.SharedPreferences;
import android.os.Build;
import android.provider.Settings;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CopyOnWriteArrayList;

import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.Response;
import okhttp3.WebSocket;
import okhttp3.WebSocketListener;

/**
 * 跨设备协同服务
 * 功能：设备发现、实时通信、数据同步、消息传递
 */
public class CrossDeviceSyncService {

    private static final String TAG = "CrossDeviceSync";

    // 配置
    private static final String PREFS_NAME = "cross_device_sync";
    private static final int SYNC_VERSION = 1;

    // 服务端地址
    private String serverUrl;
    private String wsUrl;

    // 上下文
    private final Context context;
    private final SharedPreferences prefs;

    // 设备信息
    private final String deviceId;
    private final String deviceName;
    private final String deviceType;
    private String userId;
    private String familyId;

    // WebSocket
    private OkHttpClient okHttpClient;
    private WebSocket webSocket;
    private boolean isConnected = false;

    // 监听器
    private final List<DeviceSyncListener> listeners = new CopyOnWriteArrayList<>();

    // 数据同步状态
    private final Map<String, Long> lastSyncTimes = new ConcurrentHashMap<>();
    private final Map<String, Integer> dataVersions = new ConcurrentHashMap<>();

    // 设备缓存
    private final Map<String, DeviceInfo> onlineDevices = new ConcurrentHashMap<>();

    // 同步数据类型
    public static final String DATA_CONVERSATION = "conversation";
    public static final String DATA_TASKS = "tasks";
    public static final String DATA_HEALTH = "health";
    public static final String DATA_SHOPPING = "shopping";
    public static final String DATA_SETTINGS = "settings";

    /**
     * 设备同步监听器
     */
    public interface DeviceSyncListener {
        default void onConnected() {}
        default void onDisconnected() {}
        default void onDeviceOnline(DeviceInfo device) {}
        default void onDeviceOffline(String deviceId) {}
        default void onDataSynced(String dataType, JSONObject data) {}
        default void onDataConflict(String dataType, JSONObject localData, JSONObject remoteData) {}
        default void onMessageReceived(String fromDevice, String type, JSONObject payload) {}
        default void onError(String error) {}
    }

    public CrossDeviceSyncService(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);

        // 初始化设备信息
        this.deviceId = getOrCreateDeviceId();
        this.deviceName = getDeviceName();
        this.deviceType = getDeviceType();
        this.userId = prefs.getString("user_id", null);
        this.familyId = prefs.getString("family_id", null);

        // 初始化 HTTP 客户端
        this.okHttpClient = new OkHttpClient.Builder()
                .pingInterval(java.time.Duration.ofSeconds(30))
                .build();

        Log.d(TAG, "跨设备协同服务初始化: " + deviceName + " (" + deviceId + ")");
    }

    // ========== 设备管理 ==========

    /**
     * 获取或创建设备ID
     */
    private String getOrCreateDeviceId() {
        String id = prefs.getString("device_id", null);
        if (id == null) {
            id = Settings.Secure.getString(context.getContentResolver(), Settings.Secure.ANDROID_ID);
            if (id == null || id.equals("9774d56d682e549c")) {
                id = UUID.randomUUID().toString();
            }
            prefs.edit().putString("device_id", id).apply();
        }
        return id;
    }

    /**
     * 获取设备名称
     */
    private String getDeviceName() {
        String name = prefs.getString("device_name", null);
        if (name == null) {
            name = Build.BRAND + " " + Build.MODEL;
            prefs.edit().putString("device_name", name).apply();
        }
        return name;
    }

    /**
     * 获取设备类型
     */
    private String getDeviceType() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT_WATCH) {
            if (context.getPackageManager().hasSystemFeature("android.hardware.type.watch")) {
                return "watch";
            }
            if (context.getPackageManager().hasSystemFeature("android.hardware.type.tv")) {
                return "tv";
            }
        }
        return "phone";
    }

    /**
     * 设置服务器地址
     */
    public void setServerUrl(String url) {
        this.serverUrl = url;
        this.wsUrl = url.replace("http://", "ws://").replace("https://", "wss://");
        if (!this.wsUrl.endsWith("/")) {
            this.wsUrl += "/";
        }
        this.wsUrl += "ws";
    }

    /**
     * 设置用户信息
     */
    public void setUserInfo(String userId, String familyId) {
        this.userId = userId;
        this.familyId = familyId;
        prefs.edit()
                .putString("user_id", userId)
                .putString("family_id", familyId)
                .apply();
    }

    // ========== 连接管理 ==========

    /**
     * 连接到同步服务器
     */
    public void connect() {
        if (isConnected || wsUrl == null) {
            return;
        }

        Log.d(TAG, "连接到同步服务器: " + wsUrl);

        try {
            Request request = new Request.Builder()
                    .url(wsUrl)
                    .addHeader("X-Device-Id", deviceId)
                    .addHeader("X-Device-Name", deviceName)
                    .addHeader("X-Device-Type", deviceType)
                    .addHeader("X-User-Id", userId != null ? userId : "")
                    .addHeader("X-Family-Id", familyId != null ? familyId : "")
                    .build();

            webSocket = okHttpClient.newWebSocket(request, new WebSocketListener() {
                @Override
                public void onOpen(WebSocket webSocket, Response response) {
                    Log.d(TAG, "WebSocket 连接成功");
                    isConnected = true;
                    notifyConnected();

                    // 发送注册消息
                    sendRegistration();

                    // 请求初始同步
                    requestInitialSync();
                }

                @Override
                public void onMessage(WebSocket webSocket, String text) {
                    handleMessage(text);
                }

                @Override
                public void onFailure(WebSocket webSocket, Throwable t, Response response) {
                    Log.e(TAG, "WebSocket 连接失败", t);
                    isConnected = false;
                    notifyDisconnected();
                    scheduleReconnect();
                }

                @Override
                public void onClosing(WebSocket webSocket, int code, String reason) {
                    Log.d(TAG, "WebSocket 关闭: " + code + " - " + reason);
                }

                @Override
                public void onClosed(WebSocket webSocket, int code, String reason) {
                    Log.d(TAG, "WebSocket 已关闭");
                    isConnected = false;
                    notifyDisconnected();
                }
            });

        } catch (Exception e) {
            Log.e(TAG, "连接失败", e);
            notifyError("连接失败: " + e.getMessage());
        }
    }

    /**
     * 断开连接
     */
    public void disconnect() {
        if (webSocket != null) {
            webSocket.close(1000, "正常关闭");
            webSocket = null;
        }
        isConnected = false;
        notifyDisconnected();
    }

    /**
     * 重连
     */
    private void scheduleReconnect() {
        new android.os.Handler(android.os.Looper.getMainLooper()).postDelayed(() -> {
            if (!isConnected) {
                Log.d(TAG, "尝试重新连接...");
                connect();
            }
        }, 5000);
    }

    /**
     * 发送注册消息
     */
    private void sendRegistration() {
        try {
            JSONObject msg = new JSONObject();
            msg.put("type", "register");

            JSONObject deviceInfo = new JSONObject();
            deviceInfo.put("device_id", deviceId);
            deviceInfo.put("device_name", deviceName);
            deviceInfo.put("device_type", deviceType);
            deviceInfo.put("user_id", userId);
            deviceInfo.put("family_id", familyId);
            deviceInfo.put("app_version", getAppVersion());
            deviceInfo.put("os_version", Build.VERSION.RELEASE);
            msg.put("device", deviceInfo);

            sendMessage(msg);

        } catch (Exception e) {
            Log.e(TAG, "发送注册消息失败", e);
        }
    }

    // ========== 消息处理 ==========

    /**
     * 处理收到的消息
     */
    private void handleMessage(String text) {
        try {
            JSONObject msg = new JSONObject(text);
            String type = msg.getString("type");

            switch (type) {
                case "device_online":
                    handleDeviceOnline(msg);
                    break;
                case "device_offline":
                    handleDeviceOffline(msg);
                    break;
                case "sync_data":
                    handleSyncData(msg);
                    break;
                case "sync_request":
                    handleSyncRequest(msg);
                    break;
                case "device_message":
                    handleDeviceMessage(msg);
                    break;
                case "conflict":
                    handleConflict(msg);
                    break;
                case "pong":
                    // 心跳响应
                    break;
                default:
                    Log.d(TAG, "未知消息类型: " + type);
            }

        } catch (Exception e) {
            Log.e(TAG, "处理消息失败", e);
        }
    }

    /**
     * 处理设备上线
     */
    private void handleDeviceOnline(JSONObject msg) throws Exception {
        JSONObject device = msg.getJSONObject("device");
        DeviceInfo info = new DeviceInfo();
        info.deviceId = device.getString("device_id");
        info.deviceName = device.getString("device_name");
        info.deviceType = device.optString("device_type", "phone");
        info.status = "online";
        info.lastSeen = System.currentTimeMillis();

        onlineDevices.put(info.deviceId, info);
        notifyDeviceOnline(info);
    }

    /**
     * 处理设备离线
     */
    private void handleDeviceOffline(JSONObject msg) throws Exception {
        String offlineDeviceId = msg.getString("device_id");
        onlineDevices.remove(offlineDeviceId);
        notifyDeviceOffline(offlineDeviceId);
    }

    /**
     * 处理同步数据
     */
    private void handleSyncData(JSONObject msg) throws Exception {
        String dataType = msg.getString("data_type");
        JSONObject data = msg.getJSONObject("data");
        int version = msg.optInt("version", 1);
        String sourceDevice = msg.optString("source_device");

        // 检查版本
        int localVersion = dataVersions.getOrDefault(dataType, 0);
        if (version > localVersion) {
            // 更新本地数据
            dataVersions.put(dataType, version);
            lastSyncTimes.put(dataType, System.currentTimeMillis());
            notifyDataSynced(dataType, data);
        }
    }

    /**
     * 处理同步请求
     */
    private void handleSyncRequest(JSONObject msg) throws Exception {
        String dataType = msg.getString("data_type");
        String requestingDevice = msg.getString("requesting_device");

        // 发送该类型的最新数据
        JSONObject syncMsg = new JSONObject();
        syncMsg.put("type", "sync_data");
        syncMsg.put("data_type", dataType);
        syncMsg.put("target_device", requestingDevice);
        syncMsg.put("version", dataVersions.getOrDefault(dataType, 0));
        // 实际数据需要从各自的 Service 获取

        sendMessage(syncMsg);
    }

    /**
     * 处理设备间消息
     */
    private void handleDeviceMessage(JSONObject msg) throws Exception {
        String fromDevice = msg.getString("from_device");
        String msgType = msg.getString("message_type");
        JSONObject payload = msg.getJSONObject("payload");

        notifyMessageReceived(fromDevice, msgType, payload);
    }

    /**
     * 处理冲突
     */
    private void handleConflict(JSONObject msg) throws Exception {
        String dataType = msg.getString("data_type");
        JSONObject localData = msg.getJSONObject("local_data");
        JSONObject remoteData = msg.getJSONObject("remote_data");

        notifyDataConflict(dataType, localData, remoteData);
    }

    // ========== 数据同步 ==========

    /**
     * 请求初始同步
     */
    private void requestInitialSync() {
        try {
            JSONObject msg = new JSONObject();
            msg.put("type", "initial_sync");
            msg.put("data_types", new JSONArray()
                    .put(DATA_CONVERSATION)
                    .put(DATA_TASKS)
                    .put(DATA_HEALTH)
                    .put(DATA_SHOPPING));

            sendMessage(msg);

        } catch (Exception e) {
            Log.e(TAG, "请求初始同步失败", e);
        }
    }

    /**
     * 同步数据到其他设备
     */
    public void syncData(String dataType, JSONObject data) {
        if (!isConnected) return;

        try {
            int version = dataVersions.getOrDefault(dataType, 0) + 1;
            dataVersions.put(dataType, version);

            JSONObject msg = new JSONObject();
            msg.put("type", "sync_data");
            msg.put("data_type", dataType);
            msg.put("data", data);
            msg.put("version", version);
            msg.put("source_device", deviceId);
            msg.put("timestamp", System.currentTimeMillis());

            sendMessage(msg);
            lastSyncTimes.put(dataType, System.currentTimeMillis());

        } catch (Exception e) {
            Log.e(TAG, "同步数据失败", e);
        }
    }

    /**
     * 请求同步特定数据类型
     */
    public void requestDataSync(String dataType) {
        if (!isConnected) return;

        try {
            JSONObject msg = new JSONObject();
            msg.put("type", "sync_request");
            msg.put("data_type", dataType);

            sendMessage(msg);

        } catch (Exception e) {
            Log.e(TAG, "请求数据同步失败", e);
        }
    }

    // ========== 设备间通信 ==========

    /**
     * 发送消息到指定设备
     */
    public void sendToDevice(String targetDeviceId, String messageType, JSONObject payload) {
        if (!isConnected) return;

        try {
            JSONObject msg = new JSONObject();
            msg.put("type", "device_message");
            msg.put("target_device", targetDeviceId);
            msg.put("message_type", messageType);
            msg.put("payload", payload);
            msg.put("from_device", deviceId);

            sendMessage(msg);

        } catch (Exception e) {
            Log.e(TAG, "发送设备消息失败", e);
        }
    }

    /**
     * 广播消息到所有设备
     */
    public void broadcast(String messageType, JSONObject payload) {
        if (!isConnected) return;

        try {
            JSONObject msg = new JSONObject();
            msg.put("type", "broadcast");
            msg.put("message_type", messageType);
            msg.put("payload", payload);
            msg.put("from_device", deviceId);

            sendMessage(msg);

        } catch (Exception e) {
            Log.e(TAG, "广播消息失败", e);
        }
    }

    /**
     * 发送控制指令
     */
    public void sendControlCommand(String targetDeviceId, String command, JSONObject params) {
        try {
            JSONObject payload = new JSONObject();
            payload.put("command", command);
            payload.put("params", params);
            payload.put("timestamp", System.currentTimeMillis());

            sendToDevice(targetDeviceId, "control", payload);

        } catch (Exception e) {
            Log.e(TAG, "发送控制指令失败", e);
        }
    }

    // ========== 辅助方法 ==========

    /**
     * 发送消息
     */
    private void sendMessage(JSONObject msg) {
        if (webSocket != null && isConnected) {
            webSocket.send(msg.toString());
        }
    }

    /**
     * 获取应用版本
     */
    private String getAppVersion() {
        try {
            return context.getPackageManager()
                    .getPackageInfo(context.getPackageName(), 0)
                    .versionName;
        } catch (Exception e) {
            return "1.0";
        }
    }

    /**
     * 获取在线设备列表
     */
    public List<DeviceInfo> getOnlineDevices() {
        return new ArrayList<>(onlineDevices.values());
    }

    /**
     * 获取设备信息
     */
    public DeviceInfo getDeviceInfo(String deviceId) {
        return onlineDevices.get(deviceId);
    }

    /**
     * 是否已连接
     */
    public boolean isConnected() {
        return isConnected;
    }

    /**
     * 获取当前设备ID
     */
    public String getDeviceId() {
        return deviceId;
    }

    // ========== 监听器管理 ==========

    public void addListener(DeviceSyncListener listener) {
        listeners.add(listener);
    }

    public void removeListener(DeviceSyncListener listener) {
        listeners.remove(listener);
    }

    private void notifyConnected() {
        for (DeviceSyncListener listener : listeners) {
            listener.onConnected();
        }
    }

    private void notifyDisconnected() {
        for (DeviceSyncListener listener : listeners) {
            listener.onDisconnected();
        }
    }

    private void notifyDeviceOnline(DeviceInfo device) {
        for (DeviceSyncListener listener : listeners) {
            listener.onDeviceOnline(device);
        }
    }

    private void notifyDeviceOffline(String deviceId) {
        for (DeviceSyncListener listener : listeners) {
            listener.onDeviceOffline(deviceId);
        }
    }

    private void notifyDataSynced(String dataType, JSONObject data) {
        for (DeviceSyncListener listener : listeners) {
            listener.onDataSynced(dataType, data);
        }
    }

    private void notifyDataConflict(String dataType, JSONObject local, JSONObject remote) {
        for (DeviceSyncListener listener : listeners) {
            listener.onDataConflict(dataType, local, remote);
        }
    }

    private void notifyMessageReceived(String fromDevice, String type, JSONObject payload) {
        for (DeviceSyncListener listener : listeners) {
            listener.onMessageReceived(fromDevice, type, payload);
        }
    }

    private void notifyError(String error) {
        for (DeviceSyncListener listener : listeners) {
            listener.onError(error);
        }
    }

    /**
     * 设备信息类
     */
    public static class DeviceInfo {
        public String deviceId;
        public String deviceName;
        public String deviceType;
        public String status;
        public long lastSeen;
        public int battery;

        public boolean isOnline() {
            return "online".equals(status);
        }

        public String getLastSeenText() {
            long diff = System.currentTimeMillis() - lastSeen;
            if (diff < 60000) return "刚刚";
            if (diff < 3600000) return (diff / 60000) + "分钟前";
            if (diff < 86400000) return (diff / 3600000) + "小时前";
            return (diff / 86400000) + "天前";
        }
    }
}