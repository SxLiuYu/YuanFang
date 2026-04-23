package com.openclaw.homeassistant;

import android.app.AlertDialog;
import android.os.Bundle;
import android.util.Log;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 智能家居控制界面
 */
public class SmartHomeActivity extends AppCompatActivity implements SmartHomeService.DeviceListener {
    
    private static final String TAG = "SmartHomeActivity";
    
    private SmartHomeService smartHomeService;
    private RecyclerView recyclerDevices;
    private TextView txtEnergyStats;
    private Spinner spinnerRoom;
    
    private DeviceListAdapter deviceAdapter;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_smart_home);
        
        // 初始化服务
        smartHomeService = new SmartHomeService(this);
        SmartHomeService.setListener(this);
        
        // 绑定 UI 组件
        bindViews();
        
        // 设置场景按钮
        setupSceneButtons();
        
        // 加载设备列表
        loadDevices();
        
        // 加载能耗统计
        loadEnergyStats();
    }
    
    private void bindViews() {
        recyclerDevices = findViewById(R.id.recycler_devices);
        txtEnergyStats = findViewById(R.id.txt_energy_stats);
        spinnerRoom = findViewById(R.id.spinner_room);
        
        // 设置 RecyclerView
        recyclerDevices.setLayoutManager(new LinearLayoutManager(this));
        deviceAdapter = new DeviceListAdapter();
        recyclerDevices.setAdapter(deviceAdapter);
        
        // 房间选择
        setupRoomSpinner();
    }
    
    private void setupRoomSpinner() {
        // 房间列表
        String[] rooms = {"全部", "客厅", "卧室", "厨房", "卫生间", "阳台"};
        // 使用 ArrayAdapter 填充 Spinner
        // spinnerRoom.setAdapter(new ArrayAdapter<>(this, android.R.layout.simple_spinner_item, rooms));
    }
    
    private void setupSceneButtons() {
        // 回家模式
        findViewById(R.id.btn_home_mode).setOnClickListener(v -> {
            smartHomeService.executeScene("home_mode");
            showToast("已激活回家模式");
        });
        
        // 离家模式
        findViewById(R.id.btn_away_mode).setOnClickListener(v -> {
            smartHomeService.executeScene("away_mode");
            showToast("已激活离家模式");
        });
        
        // 睡眠模式
        findViewById(R.id.btn_sleep_mode).setOnClickListener(v -> {
            smartHomeService.executeScene("sleep_mode");
            showToast("已激活睡眠模式");
        });
        
        // 工作模式
        findViewById(R.id.btn_work_mode).setOnClickListener(v -> {
            smartHomeService.executeScene("work_mode");
            showToast("已激活工作模式");
        });
        
        // 添加设备
        findViewById(R.id.btn_add_device).setOnClickListener(v -> {
            showAddDeviceDialog();
        });
    }

    /**
     * 显示添加设备对话框
     */
    private void showAddDeviceDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        View dialogView = getLayoutInflater().inflate(R.layout.dialog_add_device, null);
        builder.setView(dialogView);
        AlertDialog dialog = builder.create();

        EditText edtDeviceName = dialogView.findViewById(R.id.edt_device_name);
        Spinner spinnerDeviceType = dialogView.findViewById(R.id.spinner_device_type);
        Spinner spinnerPlatform = dialogView.findViewById(R.id.spinner_platform);
        Spinner spinnerRoom = dialogView.findViewById(R.id.spinner_room);

        // 设备类型
        String[] deviceTypes = {"灯", "空调", "插座", "电视", "窗帘", "扫地机", "门锁", "其他"};
        spinnerDeviceType.setAdapter(new ArrayAdapter<>(this,
                android.R.layout.simple_spinner_item, deviceTypes));

        // 平台
        String[] platforms = {"米家", "涂鸦", "HomeKit", "天猫精灵", "其他"};
        spinnerPlatform.setAdapter(new ArrayAdapter<>(this,
                android.R.layout.simple_spinner_item, platforms));

        // 房间
        String[] rooms = {"客厅", "卧室", "厨房", "卫生间", "书房", "阳台", "其他"};
        spinnerRoom.setAdapter(new ArrayAdapter<>(this,
                android.R.layout.simple_spinner_item, rooms));

        // 取消按钮
        dialogView.findViewById(R.id.btn_cancel).setOnClickListener(v -> dialog.dismiss());

        // 确认按钮
        dialogView.findViewById(R.id.btn_confirm).setOnClickListener(v -> {
            String deviceName = edtDeviceName.getText().toString().trim();
            if (deviceName.isEmpty()) {
                showToast("请输入设备名称");
                return;
            }

            String deviceType = spinnerDeviceType.getSelectedItem().toString();
            String platform = spinnerPlatform.getSelectedItem().toString();
            String room = spinnerRoom.getSelectedItem().toString();

            // 生成设备 ID
            String deviceId = generateDeviceId(platform, deviceType);

            // 添加设备
            smartHomeService.addDevice(deviceId, deviceName, deviceType, platform.toLowerCase(), room);
            showToast("已添加设备：" + deviceName);
            dialog.dismiss();
            loadDevices();
        });

        dialog.show();
    }

    /**
     * 生成设备 ID
     */
    private String generateDeviceId(String platform, String type) {
        String prefix;
        switch (platform) {
            case "米家": prefix = "MI"; break;
            case "涂鸦": prefix = "TY"; break;
            case "HomeKit": prefix = "HK"; break;
            case "天猫精灵": prefix = "TM"; break;
            default: prefix = "OT"; break;
        }
        return prefix + "_" + System.currentTimeMillis();
    }
    
    private void loadDevices() {
        List<SmartHomeService.DeviceInfo> devices = smartHomeService.getAllDevices();
        
        // 转换为 Map 列表
        List<Map<String, Object>> deviceMaps = new ArrayList<>();
        for (SmartHomeService.DeviceInfo device : devices) {
            Map<String, Object> map = new HashMap<>();
            map.put("name", device.name);
            map.put("status", device.isOnline ? "在线" : "离线");
            map.put("type", device.type);
            map.put("room", device.room);
            deviceMaps.add(map);
        }
        
        deviceAdapter.setDevices(deviceMaps);
        
        if (devices.isEmpty()) {
            showToast("暂无设备，点击右上角添加");
        }
    }
    
    private void loadEnergyStats() {
        Map<String, Double> stats = smartHomeService.getEnergyStats("today");
        double total = 0;
        for (Double value : stats.values()) {
            total += value;
        }
        txtEnergyStats.setText(String.format("今日总耗电：%.2f kWh", total));
    }
    
    @Override
    public void onDeviceStatusChanged(String deviceId, boolean isOnline) {
        runOnUiThread(() -> {
            Log.d(TAG, "设备状态变化：" + deviceId + " - " + (isOnline ? "在线" : "离线"));
            // 更新设备列表
            loadDevices();
        });
    }
    
    @Override
    public void onSceneActivated(String sceneId, String sceneName) {
        runOnUiThread(() -> {
            showToast("场景已激活：" + sceneName);
        });
    }
    
    private void showToast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        SmartHomeService.setListener(null);
    }
}
