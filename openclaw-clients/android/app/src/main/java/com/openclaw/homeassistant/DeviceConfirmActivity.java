package com.openclaw.homeassistant;

import android.app.AlertDialog;
import android.content.Intent;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

/**
 * 设备确认界面
 * 用户输入飞书消息中的确认码完成设备登录
 */
public class DeviceConfirmActivity extends AppCompatActivity {
    
    private TextView textTempId;
    private EditText inputConfirmCode;
    private Button btnConfirm;
    private Button btnResend;
    
    private String tempId;
    private DeviceAuthService authService;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_device_confirm);
        
        // 初始化视图
        textTempId = findViewById(R.id.textTempId);
        inputConfirmCode = findViewById(R.id.inputConfirmCode);
        btnConfirm = findViewById(R.id.btnConfirm);
        btnResend = findViewById(R.id.btnResend);
        
        // 获取认证服务
        try {
            authService = OpenClawApplication.getInstance().getAuthService();
        } catch (Exception e) {
            Toast.makeText(this, "服务初始化中，请稍候...", Toast.LENGTH_SHORT).show();
            finish();
            return;
        }
        
        // 从认证服务获取临时 ID
        if (authService != null) {
            tempId = authService.getCurrentTempId();
        }
        
        // 设置监听器
        authService.setListener(new DeviceAuthService.AuthListener() {
            @Override
            public void onAuthSuccess(String token) {
                // 已经认证成功，直接跳转
                runOnUiThread(() -> {
                    Toast.makeText(DeviceConfirmActivity.this, 
                        "设备已确认", Toast.LENGTH_SHORT).show();
                    Intent intent = new Intent(DeviceConfirmActivity.this, MainActivity.class);
                    intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TASK);
                    startActivity(intent);
                    finish();
                });
            }
            
            @Override
            public void onAuthPending(String newTempId) {
                tempId = newTempId;
                runOnUiThread(() -> {
                    textTempId.setText("临时 ID: " + tempId);
                    btnConfirm.setEnabled(true);
                    Toast.makeText(DeviceConfirmActivity.this, 
                        "请查看飞书消息获取确认码", Toast.LENGTH_LONG).show();
                });
            }
            
            @Override
            public void onAuthFailed(String error) {
                runOnUiThread(() -> {
                    textTempId.setText("获取失败，请重试");
                    btnConfirm.setEnabled(false);
                    btnResend.setEnabled(true);
                });
            }
        });
        
        // 如果还没有 tempId，触发注册
        if (tempId == null) {
            textTempId.setText("正在获取确认信息...");
            btnConfirm.setEnabled(false);
            authService.registerOrLogin();
        } else {
            textTempId.setText("临时 ID: " + tempId);
            btnConfirm.setEnabled(true);
        }
        
        // 确认按钮点击
        btnConfirm.setOnClickListener(v -> {
            String code = inputConfirmCode.getText().toString().trim().toUpperCase();
            if (code.length() != 6) {
                Toast.makeText(this, "请输入 6 位确认码", Toast.LENGTH_SHORT).show();
                return;
            }
            
            btnConfirm.setEnabled(false);
            btnConfirm.setText("确认中...");
            
            // 调用确认接口
            if (authService != null && tempId != null) {
                authService.confirmDevice(tempId, code);
            }
        });
        
        // 重新发送按钮
        btnResend.setOnClickListener(v -> {
            btnConfirm.setEnabled(true);
            if (authService != null) {
                authService.registerOrLogin();
                Toast.makeText(this, "已重新发送确认请求", Toast.LENGTH_SHORT).show();
            }
        });
    }
    
    @Override
    protected void onSaveInstanceState(Bundle outState) {
        super.onSaveInstanceState(outState);
        if (tempId != null) {
            outState.putString("temp_id", tempId);
        }
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        // 清除监听器，防止内存泄漏
        if (authService != null) {
            authService.setListener(null);
        }
    }
}
