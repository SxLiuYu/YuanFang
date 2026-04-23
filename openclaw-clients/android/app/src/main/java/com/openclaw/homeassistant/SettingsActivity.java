package com.openclaw.homeassistant;
import android.util.Log;

import android.content.SharedPreferences;
import android.os.Bundle;
import android.text.TextUtils;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.Spinner;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;

import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

/**
 * 设置界面 - 简化版
 * 只需配置 OpenClaw 服务器地址，由 OpenClaw 统一管理 AI 服务
 */
public class SettingsActivity extends AppCompatActivity {
    
    private static final String TAG = "SettingsActivity";
    
    private EditText etServerUrl;
    private EditText etApiKey;
    private Spinner spinnerContextLength;
    private TextView tvHint;
    private Button btnSave;
    private Button btnCancel;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_settings);
        
        initViews();
        loadSettings();
        setupListeners();
    }
    
    private void initViews() {
        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setTitle("");
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
        }
        
        etServerUrl = findViewById(R.id.etServerUrl);
        etApiKey = findViewById(R.id.etApiKey);
        spinnerContextLength = findViewById(R.id.spinnerContextLength);
        tvHint = findViewById(R.id.tvHint);
        btnSave = findViewById(R.id.btnSave);
        btnCancel = findViewById(R.id.btnCancel);
        
        // 设置上下文长度选项
        String[] contextOptions = {"最近 5 条", "最近 10 条", "最近 20 条"};
        ArrayAdapter<String> contextAdapter = new ArrayAdapter<>(this, 
            android.R.layout.simple_spinner_item, contextOptions);
        contextAdapter.setDropDownViewResource(android.R.layout.simple_spinner_dropdown_item);
        spinnerContextLength.setAdapter(contextAdapter);
        
        // 设置提示文字
        tvHint.setText("💡 家庭助手通过 OpenClaw 连接 AI 服务\nOpenClaw 会统一管理所有 AI 平台（智谱、阿里云等）\n只需填写服务器地址，其他配置在 OpenClaw 端完成");
    }
    
    private void loadSettings() {
        SharedPreferences prefs = getSharedPreferences("OpenClawPrefs", MODE_PRIVATE);
        
        String serverUrl = prefs.getString("server_url", "");
        String apiKey = prefs.getString("dashscope_api_key", "");
        int contextLength = prefs.getInt("context_length", 10);
        
        etServerUrl.setText(serverUrl);
        etApiKey.setText(apiKey);
        spinnerContextLength.setSelection(contextLength == 5 ? 0 : contextLength == 20 ? 2 : 1);
    }
    
    private void setupListeners() {
        btnSave.setOnClickListener(v -> saveSettings());
        btnCancel.setOnClickListener(v -> finish());
    }
    
    @Override
    public boolean onSupportNavigateUp() {
        onBackPressed();
        return true;
    }
    
    private void saveSettings() {
        String serverUrl = etServerUrl.getText().toString().trim();
        String apiKey = etApiKey.getText().toString().trim();
        int contextLength = spinnerContextLength.getSelectedItemPosition() == 0 ? 5 : 
                           spinnerContextLength.getSelectedItemPosition() == 2 ? 20 : 10;
        
        // 至少配置一个
        if (TextUtils.isEmpty(serverUrl) && TextUtils.isEmpty(apiKey)) {
            Toast.makeText(this, "⚠️ 请至少配置服务器地址或 API Key", Toast.LENGTH_SHORT).show();
            return;
        }
        
        SharedPreferences prefs = getSharedPreferences("OpenClawPrefs", MODE_PRIVATE);
        prefs.edit()
            .putString("server_url", serverUrl)
            .putString("dashscope_api_key", apiKey)
            .putInt("context_length", contextLength)
            .apply();
        
        // 同步到 ConfigManager
        try {
            ConfigManager configManager = new ConfigManager(this);
            JSONObject config = configManager.getConfig();
            if (config != null) {
                if (!TextUtils.isEmpty(serverUrl)) {
                    config.getJSONObject("core").put("server_url", serverUrl);
                }
                if (!TextUtils.isEmpty(apiKey)) {
                    config.getJSONObject("core").put("api_key", apiKey);
                }
                config.getJSONObject("core").put("context_length", contextLength);
                configManager.saveConfig();
            }
        } catch (Exception e) {
            Log.e(TAG, "保存配置失败", e);
        }
        
        String message = TextUtils.isEmpty(serverUrl) ? 
            "✅ API Key 已保存（使用直连模式）" : 
            "✅ 服务器地址已保存\n📍 " + serverUrl;
        Toast.makeText(this, message, Toast.LENGTH_LONG).show();
        finish();
    }
}
