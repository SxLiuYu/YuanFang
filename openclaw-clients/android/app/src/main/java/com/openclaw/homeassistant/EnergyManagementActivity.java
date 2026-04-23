package com.openclaw.homeassistant;

import android.app.AlertDialog;
import android.os.Bundle;
import android.view.View;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;
import java.util.*;

/**
 * 能源管理 Activity
 * 功能：
 * - 记录设备用电
 * - 查看用电报告
 * - 节能建议
 * - 节能目标
 */
public class EnergyManagementActivity extends AppCompatActivity {
    
    private EnergyManagementService energyService;
    
    // UI 组件
    private Spinner spinnerDevice;
    private EditText editHours;
    private EditText editPower;
    private Button btnRecord;
    private TextView textTodayUsage;
    private TextView textTodayCost;
    private TextView textMonthlyUsage;
    private Button btnViewReport;
    private Button btnSuggestions;
    private Button btnSetGoal;
    private ListView listDevices;
    private ListView listSuggestions;
    
    private String[] deviceNames = {
        "客厅空调", "卧室空调", "电视", "冰箱", "洗衣机",
        "微波炉", "电水壶", "电脑", "路由器", "电暖器",
        "风扇", "热水器", "LED 灯", "其他"
    };
    
    private Map<String, Integer> devicePowerMap;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_energy_management);
        
        initDevicePowerMap();
        initViews();
        setupListeners();
        loadTodayData();
    }
    
    private void initDevicePowerMap() {
        devicePowerMap = new HashMap<>();
        devicePowerMap.put("客厅空调", 1500);
        devicePowerMap.put("卧室空调", 1500);
        devicePowerMap.put("电视", 150);
        devicePowerMap.put("冰箱", 200);
        devicePowerMap.put("洗衣机", 500);
        devicePowerMap.put("微波炉", 1000);
        devicePowerMap.put("电水壶", 1800);
        devicePowerMap.put("电脑", 300);
        devicePowerMap.put("路由器", 10);
        devicePowerMap.put("电暖器", 2000);
        devicePowerMap.put("风扇", 50);
        devicePowerMap.put("热水器", 3000);
        devicePowerMap.put("LED 灯", 10);
        devicePowerMap.put("其他", 100);
    }
    
    private void initViews() {
        spinnerDevice = findViewById(R.id.spinner_device);
        editHours = findViewById(R.id.edit_hours);
        editPower = findViewById(R.id.edit_power);
        btnRecord = findViewById(R.id.btn_record);
        textTodayUsage = findViewById(R.id.text_today_usage);
        textTodayCost = findViewById(R.id.text_today_cost);
        textMonthlyUsage = findViewById(R.id.text_monthly_usage);
        btnViewReport = findViewById(R.id.btn_view_report);
        btnSuggestions = findViewById(R.id.btn_suggestions);
        btnSetGoal = findViewById(R.id.btn_set_goal);
        listDevices = findViewById(R.id.list_devices);
        listSuggestions = findViewById(R.id.list_suggestions);
        
        // 设置设备下拉框
        ArrayAdapter<String> adapter = new ArrayAdapter<>(
            this, 
            android.R.layout.simple_spinner_item, 
            deviceNames
        );
        adapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinnerDevice.setAdapter(adapter);
        
        energyService = new EnergyManagementService(this);
    }
    
    private void setupListeners() {
        // 设备选择变化时自动填充功率
        spinnerDevice.setOnItemSelectedListener(new AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(AdapterView<?> parent, View view, int position, long id) {
                String deviceName = deviceNames[position];
                Integer power = devicePowerMap.get(deviceName);
                if (power != null) {
                    editPower.setText(String.valueOf(power));
                }
            }
            
            @Override
            public void onNothingSelected(AdapterView<?> parent) {}
        });
        
        // 记录用电按钮
        btnRecord.setOnClickListener(v -> recordEnergyUsage());
        
        // 查看报告按钮
        btnViewReport.setOnClickListener(v -> viewReport());
        
        // 节能建议按钮
        btnSuggestions.setOnClickListener(v -> showSuggestions());
        
        // 设置目标按钮
        btnSetGoal.setOnClickListener(v -> setEnergyGoal());
    }
    
    private void recordEnergyUsage() {
        String deviceName = spinnerDevice.getSelectedItem().toString();
        String hoursStr = editHours.getText().toString();
        String powerStr = editPower.getText().toString();
        
        if (hoursStr.isEmpty()) {
            Toast.makeText(this, "请输入使用时长", Toast.LENGTH_SHORT).show();
            return;
        }
        
        double hours = Double.parseDouble(hoursStr);
        double power = powerStr.isEmpty() ? devicePowerMap.get(deviceName) : Double.parseDouble(powerStr);
        
        energyService.quickRecord(deviceName, hours, new EnergyManagementService.RecordCallback() {
            @Override
            public void onSuccess(Map<String, Object> result) {
                double energyKwh = (Double) result.get("energy_kwh");
                double cost = (Double) result.get("cost");
                
                Toast.makeText(
                    EnergyManagementActivity.this,
                    "记录成功：" + String.format("%.2f", energyKwh) + "度，" + 
                    String.format("%.2f", cost) + "元",
                    Toast.LENGTH_SHORT
                ).show();
                
                loadTodayData();
            }
            
            @Override
            public void onError(String error) {
                Toast.makeText(EnergyManagementActivity.this, "记录失败：" + error, Toast.LENGTH_SHORT).show();
            }
        });
    }
    
    private void loadTodayData() {
        energyService.getDailyReport(null, new EnergyManagementService.DailyReportCallback() {
            @Override
            public void onReport(Map<String, Object> report) {
                double totalKwh = (Double) report.get("total_kwh");
                double totalCost = (Double) report.get("cost");
                
                textTodayUsage.setText(String.format("今日用电：%.2f 度", totalKwh));
                textTodayCost.setText(String.format("今日电费：¥%.2f", totalCost));
                
                // 加载月度数据
                Map<String, Object> monthly = energyService.getMonthlyTotal();
                double monthlyKwh = (Double) monthly.get("total_kwh");
                double monthlyCost = (Double) monthly.get("total_cost");
                
                textMonthlyUsage.setText(String.format(
                    "本月累计：%.2f 度 (¥%.2f)",
                    monthlyKwh, monthlyCost
                ));
            }
            
            @Override
            public void onError(String error) {
                textTodayUsage.setText("今日用电：--");
                textTodayCost.setText("今日电费：--");
            }
        });
    }
    
    private void viewReport() {
        energyService.getDailyReport(null, new EnergyManagementService.DailyReportCallback() {
            @Override
            public void onReport(Map<String, Object> report) {
                List<Map<String, Object>> devices = (List<Map<String, Object>>) report.get("devices");
                
                List<String> deviceList = new ArrayList<>();
                for (Map<String, Object> device : devices) {
                    String name = (String) device.get("name");
                    double kwh = (Double) device.get("kwh");
                    double cost = (Double) device.get("cost");
                    deviceList.add(String.format("%s: %.2f度 (¥%.2f)", name, kwh, cost));
                }
                
                ArrayAdapter<String> adapter = new ArrayAdapter<>(
                    EnergyManagementActivity.this,
                    android.R.layout.simple_list_item_1,
                    deviceList
                );
                listDevices.setAdapter(adapter);
                
                Toast.makeText(EnergyManagementActivity.this, "已加载设备用电明细", Toast.LENGTH_SHORT).show();
            }
            
            @Override
            public void onError(String error) {
                Toast.makeText(EnergyManagementActivity.this, "加载失败：" + error, Toast.LENGTH_SHORT).show();
            }
        });
    }
    
    private void showSuggestions() {
        List<Map<String, Object>> suggestions = energyService.getEnergySavingSuggestions();
        
        List<String> suggestionList = new ArrayList<>();
        for (Map<String, Object> suggestion : suggestions) {
            String message = (String) suggestion.get("message");
            Double saving = (Double) suggestion.get("potential_saving");
            
            if (saving != null && saving > 0) {
                suggestionList.add(String.format("💡 %s (预计省¥%.2f)", message, saving));
            } else {
                suggestionList.add("💡 " + message);
            }
        }
        
        ArrayAdapter<String> adapter = new ArrayAdapter<>(
            this,
            android.R.layout.simple_list_item_1,
            suggestionList
        );
        listSuggestions.setAdapter(adapter);
    }
    
    private void setEnergyGoal() {
        // 简单弹窗设置目标
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("设置节能目标");
        
        final EditText input = new EditText(this);
        input.setHint("目标用电量（度）");
        input.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | 
                          android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
        builder.setView(input);
        
        builder.setPositiveButton("确定", (dialog, which) -> {
            String targetStr = input.getText().toString();
            if (!targetStr.isEmpty()) {
                double targetKwh = Double.parseDouble(targetStr);
                boolean success = energyService.setEnergySavingGoal(
                    "月度节能目标",
                    targetKwh,
                    "monthly"
                );
                
                if (success) {
                    Toast.makeText(this, "目标设置成功", Toast.LENGTH_SHORT).show();
                }
            }
        });
        
        builder.setNegativeButton("取消", null);
        builder.show();
    }
}
