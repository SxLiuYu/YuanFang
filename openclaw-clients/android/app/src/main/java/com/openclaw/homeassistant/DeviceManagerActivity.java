package com.openclaw.homeassistant;

import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

/**
 * 设备管理界面
 * 查看设备状态、令牌、重新认证等
 */
public class DeviceManagerActivity extends AppCompatActivity {
    
    private TextView textDeviceId;
    private TextView textDeviceName;
    private TextView textDeviceModel;
    private TextView textAuthToken;
    private TextView textAuthStatus;
    private Button btnReauth;
    private Button btnLogout;
    private Button btnRefresh;
    
    private DeviceAuthService authService;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_device_manager);
        
        authService = OpenClawApplication.getInstance().getAuthService();
        
        initViews();
        loadDeviceInfo();
        setupListeners();
    }
    
    private void initViews() {
        textDeviceId = findViewById(R.id.textDeviceId);
        textDeviceName = findViewById(R.id.textDeviceName);
        textDeviceModel = findViewById(R.id.textDeviceModel);
        textAuthToken = findViewById(R.id.textAuthToken);
        textAuthStatus = findViewById(R.id.textAuthStatus);
        btnReauth = findViewById(R.id.btnReauth);
        btnLogout = findViewById(R.id.btnLogout);
        btnRefresh = findViewById(R.id.btnRefresh);
    }
    
    private void loadDeviceInfo() {
        String deviceId = authService.getDeviceId();
        String deviceName = getDeviceName();
        String deviceModel = android.os.Build.BRAND + " " + android.os.Build.MODEL;
        String token = authService.getToken();
        boolean confirmed = authService.isConfirmed();
        
        textDeviceId.setText("设备 ID: " + (deviceId != null ? deviceId : "未知"));
        textDeviceName.setText("设备名称：" + deviceName);
        textDeviceModel.setText("设备型号：" + deviceModel);
        
        if (token != null) {
            String maskedToken = token.substring(0, 8) + "..." + token.substring(token.length() - 8);
            textAuthToken.setText("认证令牌：" + maskedToken);
        } else {
            textAuthToken.setText("认证令牌：未获取");
        }
        
        textAuthStatus.setText("认证状态：" + (confirmed ? "✅ 已确认" : "❌ 未确认"));
        
        // 按钮状态：未确认时也需要能操作
        btnReauth.setEnabled(true);
        btnLogout.setEnabled(true);
        
        // 未确认时显示提示
        if (!confirmed) {
            Toast.makeText(this, "设备未确认，请查看飞书获取确认码", Toast.LENGTH_LONG).show();
        }
    }
    
    private void setupListeners() {
        // 刷新按钮
        btnRefresh.setOnClickListener(v -> loadDeviceInfo());
        
        // 重新认证按钮
        btnReauth.setOnClickListener(v -> {
            new AlertDialog.Builder(this)
                .setTitle("重新认证")
                .setMessage("确定要重新认证设备吗？当前令牌将失效。")
                .setPositiveButton("确定", (dialog, which) -> {
                    authService.logout();
                    authService.registerOrLogin();
                    Toast.makeText(this, "正在重新认证，请查看飞书...", Toast.LENGTH_SHORT).show();
                    // 跳转到确认界面
                    Intent intent = new Intent(DeviceManagerActivity.this, DeviceConfirmActivity.class);
                    intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
                    startActivity(intent);
                    finish();
                })
                .setNegativeButton("取消", null)
                .show();
        });
        
        // 退出登录按钮
        btnLogout.setOnClickListener(v -> {
            new AlertDialog.Builder(this)
                .setTitle("退出登录")
                .setMessage("确定要退出登录吗？所有服务将停止。")
                .setPositiveButton("确定", (dialog, which) -> {
                    OpenClawApplication.getInstance().logout();
                    Toast.makeText(this, "已退出登录，请查看飞书确认码", Toast.LENGTH_SHORT).show();
                    // 跳转到确认界面
                    Intent intent = new Intent(DeviceManagerActivity.this, DeviceConfirmActivity.class);
                    intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
                    startActivity(intent);
                    finish();
                })
                .setNegativeButton("取消", null)
                .show();
        });
    }
    
    private String getDeviceName() {
        android.content.SharedPreferences prefs = getSharedPreferences("device_auth", MODE_PRIVATE);
        return prefs.getString("device_name", "未命名设备");
    }
    
    @Override
    protected void onResume() {
        super.onResume();
        loadDeviceInfo();
    }
}
