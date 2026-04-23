package com.openclaw.homeassistant;
import android.util.Log;

import android.graphics.Color;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.cardview.widget.CardView;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;
import androidx.swiperefreshlayout.widget.SwipeRefreshLayout;

import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

/**
 * 跨设备协同界面
 * 显示在线设备列表、同步状态、设备间通信
 */
public class CrossDeviceActivity extends AppCompatActivity implements CrossDeviceSyncService.DeviceSyncListener {

    private static final String TAG = "CrossDeviceActivity";

    // UI 组件
    private Toolbar toolbar;
    private SwipeRefreshLayout swipeRefresh;
    private RecyclerView recyclerView;
    private TextView txtConnectionStatus;
    private TextView txtDeviceInfo;
    private LinearLayout layoutSyncStatus;
    private Button btnSyncAll;
    private Button btnSendCommand;

    // 服务
    private CrossDeviceSyncService syncService;

    // 设备列表适配器
    private DeviceAdapter deviceAdapter;
    private List<CrossDeviceSyncService.DeviceInfo> devices = new ArrayList<>();

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_cross_device);

        initViews();
        initSyncService();
        setupListeners();
    }

    private void initViews() {
        toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
            getSupportActionBar().setTitle("跨设备协同");
        }

        swipeRefresh = findViewById(R.id.swipe_refresh);
        recyclerView = findViewById(R.id.recycler_devices);
        txtConnectionStatus = findViewById(R.id.txt_connection_status);
        txtDeviceInfo = findViewById(R.id.txt_device_info);
        layoutSyncStatus = findViewById(R.id.layout_sync_status);
        btnSyncAll = findViewById(R.id.btn_sync_all);
        btnSendCommand = findViewById(R.id.btn_send_command);

        // 设置 RecyclerView
        recyclerView.setLayoutManager(new LinearLayoutManager(this));
        deviceAdapter = new DeviceAdapter();
        recyclerView.setAdapter(deviceAdapter);

        // 显示当前设备信息
        updateDeviceInfo();
    }

    private void initSyncService() {
        syncService = new CrossDeviceSyncService(this);
        syncService.addListener(this);

        // 配置服务器地址
        String serverUrl = getSharedPreferences("OpenClawPrefs", MODE_PRIVATE)
                .getString("server_url", SecureConfig.DEFAULT_SERVER_URL);
        syncService.setServerUrl(serverUrl);
    }

    private void setupListeners() {
        // 下拉刷新
        swipeRefresh.setOnRefreshListener(() -> {
            refreshDevices();
            swipeRefresh.setRefreshing(false);
        });

        // 同步所有数据
        btnSyncAll.setOnClickListener(v -> syncAllData());

        // 发送命令
        btnSendCommand.setOnClickListener(v -> showSendCommandDialog());

        // 连接/断开
        txtConnectionStatus.setOnClickListener(v -> {
            if (syncService.isConnected()) {
                syncService.disconnect();
            } else {
                syncService.connect();
            }
        });
    }

    /**
     * 更新设备信息显示
     */
    private void updateDeviceInfo() {
        String info = "本机: " + syncService.getDeviceId().substring(0, 8) + "...";
        txtDeviceInfo.setText(info);
    }

    /**
     * 刷新设备列表
     */
    private void refreshDevices() {
        devices.clear();
        devices.addAll(syncService.getOnlineDevices());
        deviceAdapter.notifyDataSetChanged();
        updateEmptyState();
    }

    /**
     * 同步所有数据
     */
    private void syncAllData() {
        if (!syncService.isConnected()) {
            Toast.makeText(this, "未连接到服务器", Toast.LENGTH_SHORT).show();
            return;
        }

        syncService.requestDataSync(CrossDeviceSyncService.DATA_CONVERSATION);
        syncService.requestDataSync(CrossDeviceSyncService.DATA_TASKS);
        syncService.requestDataSync(CrossDeviceSyncService.DATA_HEALTH);

        Toast.makeText(this, "同步请求已发送", Toast.LENGTH_SHORT).show();
    }

    /**
     * 显示发送命令对话框
     */
    private void showSendCommandDialog() {
        if (devices.isEmpty()) {
            Toast.makeText(this, "没有在线设备", Toast.LENGTH_SHORT).show();
            return;
        }

        String[] deviceNames = new String[devices.size()];
        for (int i = 0; i < devices.size(); i++) {
            deviceNames[i] = devices.get(i).deviceName;
        }

        new AlertDialog.Builder(this)
                .setTitle("选择目标设备")
                .setItems(deviceNames, (dialog, which) -> {
                    CrossDeviceSyncService.DeviceInfo device = devices.get(which);
                    showCommandInputDialog(device);
                })
                .show();
    }

    /**
     * 显示命令输入对话框
     */
    private void showCommandInputDialog(CrossDeviceSyncService.DeviceInfo device) {
        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(50, 40, 50, 10);

        final EditText etCommand = new EditText(this);
        etCommand.setHint("命令 (如: play_music, set_reminder)");
        layout.addView(etCommand);

        final EditText etParams = new EditText(this);
        etParams.setHint("参数 (JSON格式，可选)");
        layout.addView(etParams);

        new AlertDialog.Builder(this)
                .setTitle("发送命令到 " + device.deviceName)
                .setView(layout)
                .setPositiveButton("发送", (dialog, which) -> {
                    String command = etCommand.getText().toString().trim();
                    String paramsStr = etParams.getText().toString().trim();

                    if (command.isEmpty()) {
                        Toast.makeText(this, "请输入命令", Toast.LENGTH_SHORT).show();
                        return;
                    }

                    try {
                        JSONObject params = paramsStr.isEmpty() ? new JSONObject() : new JSONObject(paramsStr);
                        syncService.sendControlCommand(device.deviceId, command, params);
                        Toast.makeText(this, "命令已发送", Toast.LENGTH_SHORT).show();
                    } catch (Exception e) {
                        Toast.makeText(this, "参数格式错误", Toast.LENGTH_SHORT).show();
                    }
                })
                .setNegativeButton("取消", null)
                .show();
    }

    /**
     * 更新空状态
     */
    private void updateEmptyState() {
        TextView emptyView = findViewById(R.id.txt_empty);
        if (emptyView != null) {
            emptyView.setVisibility(devices.isEmpty() ? View.VISIBLE : View.GONE);
        }
    }

    // ========== DeviceSyncListener 实现 ==========

    @Override
    public void onConnected() {
        runOnUiThread(() -> {
            txtConnectionStatus.setText("● 已连接");
            txtConnectionStatus.setTextColor(Color.parseColor("#4CAF50"));
            Toast.makeText(this, "已连接到同步服务器", Toast.LENGTH_SHORT).show();
        });
    }

    @Override
    public void onDisconnected() {
        runOnUiThread(() -> {
            txtConnectionStatus.setText("○ 未连接");
            txtConnectionStatus.setTextColor(Color.parseColor("#F44336"));
        });
    }

    @Override
    public void onDeviceOnline(CrossDeviceSyncService.DeviceInfo device) {
        runOnUiThread(() -> {
            Toast.makeText(this, device.deviceName + " 上线了", Toast.LENGTH_SHORT).show();
            refreshDevices();
        });
    }

    @Override
    public void onDeviceOffline(String deviceId) {
        runOnUiThread(() -> {
            refreshDevices();
            Toast.makeText(this, "设备离线", Toast.LENGTH_SHORT).show();
        });
    }

    @Override
    public void onDataSynced(String dataType, JSONObject data) {
        runOnUiThread(() -> {
            String typeName = getTypeName(dataType);
            Toast.makeText(this, typeName + " 同步完成", Toast.LENGTH_SHORT).show();
            updateSyncStatus(dataType, true);
        });
    }

    @Override
    public void onDataConflict(String dataType, JSONObject localData, JSONObject remoteData) {
        runOnUiThread(() -> showConflictDialog(dataType, localData, remoteData));
    }

    @Override
    public void onMessageReceived(String fromDevice, String type, JSONObject payload) {
        runOnUiThread(() -> {
            CrossDeviceSyncService.DeviceInfo device = syncService.getDeviceInfo(fromDevice);
            String deviceName = device != null ? device.deviceName : fromDevice.substring(0, 8);

            new AlertDialog.Builder(this)
                    .setTitle("来自 " + deviceName)
                    .setMessage("类型: " + type + "\n内容: " + payload.toString())
                    .setPositiveButton("确定", null)
                    .show();
        });
    }

    @Override
    public void onError(String error) {
        runOnUiThread(() -> Toast.makeText(this, error, Toast.LENGTH_SHORT).show());
    }

    /**
     * 显示冲突解决对话框
     */
    private void showConflictDialog(String dataType, JSONObject local, JSONObject remote) {
        String typeName = getTypeName(dataType);

        new AlertDialog.Builder(this)
                .setTitle("数据冲突: " + typeName)
                .setMessage("检测到数据冲突，请选择保留哪个版本")
                .setPositiveButton("保留本地", (dialog, which) -> {
                    syncService.syncData(dataType, local);
                })
                .setNegativeButton("使用远程", (dialog, which) -> {
                    // 远程数据已更新，无需操作
                })
                .setNeutralButton("取消", null)
                .show();
    }

    /**
     * 更新同步状态
     */
    private void updateSyncStatus(String dataType, boolean success) {
        // 更新 UI 显示同步状态
        View statusView = layoutSyncStatus.findViewWithTag(dataType);
        if (statusView instanceof TextView) {
            ((TextView) statusView).setText(success ? "✓" : "✗");
        }
    }

    /**
     * 获取数据类型名称
     */
    private String getTypeName(String dataType) {
        switch (dataType) {
            case CrossDeviceSyncService.DATA_CONVERSATION: return "对话历史";
            case CrossDeviceSyncService.DATA_TASKS: return "任务列表";
            case CrossDeviceSyncService.DATA_HEALTH: return "健康数据";
            case CrossDeviceSyncService.DATA_SHOPPING: return "购物清单";
            case CrossDeviceSyncService.DATA_SETTINGS: return "设置";
            default: return dataType;
        }
    }

    // ========== 设备列表适配器 ==========

    private class DeviceAdapter extends RecyclerView.Adapter<DeviceAdapter.ViewHolder> {

        @Override
        public ViewHolder onCreateViewHolder(ViewGroup parent, int viewType) {
            View view = LayoutInflater.from(parent.getContext())
                    .inflate(R.layout.item_device, parent, false);
            return new ViewHolder(view);
        }

        @Override
        public void onBindViewHolder(ViewHolder holder, int position) {
            CrossDeviceSyncService.DeviceInfo device = devices.get(position);

            holder.txtDeviceName.setText(device.deviceName);
            holder.txtDeviceId.setText(device.deviceId.substring(0, 8) + "...");
            holder.txtDeviceType.setText(device.deviceType);

            // 在线状态
            if (device.isOnline()) {
                holder.imgStatus.setImageResource(R.drawable.ic_device_online);
                holder.cardView.setCardBackgroundColor(Color.parseColor("#E8F5E9"));
            } else {
                holder.imgStatus.setImageResource(R.drawable.ic_device_offline);
                holder.cardView.setCardBackgroundColor(Color.parseColor("#FAFAFA"));
            }

            // 点击发送消息
            holder.btnSend.setOnClickListener(v -> showSendMessageDialog(device));

            // 点击查看详情
            holder.cardView.setOnClickListener(v -> showDeviceDetailDialog(device));
        }

        @Override
        public int getItemCount() {
            return devices.size();
        }

        class ViewHolder extends RecyclerView.ViewHolder {
            CardView cardView;
            ImageView imgStatus;
            TextView txtDeviceName;
            TextView txtDeviceId;
            TextView txtDeviceType;
            Button btnSend;

            ViewHolder(View itemView) {
                super(itemView);
                cardView = itemView.findViewById(R.id.card_device);
                imgStatus = itemView.findViewById(R.id.img_status);
                txtDeviceName = itemView.findViewById(R.id.txt_device_name);
                txtDeviceId = itemView.findViewById(R.id.txt_device_id);
                txtDeviceType = itemView.findViewById(R.id.txt_device_type);
                btnSend = itemView.findViewById(R.id.btn_send);
            }
        }
    }

    /**
     * 显示发送消息对话框
     */
    private void showSendMessageDialog(CrossDeviceSyncService.DeviceInfo device) {
        EditText input = new EditText(this);
        input.setHint("输入消息内容");

        new AlertDialog.Builder(this)
                .setTitle("发送消息到 " + device.deviceName)
                .setView(input)
                .setPositiveButton("发送", (dialog, which) -> {
                    String message = input.getText().toString().trim();
                    if (!message.isEmpty()) {
                        try {
                            JSONObject payload = new JSONObject();
                            payload.put("message", message);
                            syncService.sendToDevice(device.deviceId, "text", payload);
                            Toast.makeText(this, "消息已发送", Toast.LENGTH_SHORT).show();
                        } catch (Exception e) {
                            Log.e(TAG, "发送消息失败", e);
                        }
                    }
                })
                .setNegativeButton("取消", null)
                .show();
    }

    /**
     * 显示设备详情对话框
     */
    private void showDeviceDetailDialog(CrossDeviceSyncService.DeviceInfo device) {
        StringBuilder info = new StringBuilder();
        info.append("设备名称: ").append(device.deviceName).append("\n");
        info.append("设备类型: ").append(device.deviceType).append("\n");
        info.append("设备ID: ").append(device.deviceId).append("\n");
        info.append("状态: ").append(device.isOnline() ? "在线" : "离线").append("\n");
        info.append("最后活跃: ").append(device.getLastSeenText());

        new AlertDialog.Builder(this)
                .setTitle("设备详情")
                .setMessage(info.toString())
                .setPositiveButton("确定", null)
                .show();
    }

    @Override
    protected void onResume() {
        super.onResume();
        // 自动连接
        if (!syncService.isConnected()) {
            syncService.connect();
        }
    }

    @Override
    protected void onPause() {
        super.onPause();
        // 保持后台连接
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (syncService != null) {
            syncService.removeListener(this);
            syncService.disconnect();
        }
    }

    @Override
    public boolean onSupportNavigateUp() {
        finish();
        return true;
    }
}