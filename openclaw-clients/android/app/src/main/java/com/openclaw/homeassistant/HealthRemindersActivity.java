package com.openclaw.homeassistant;

import android.os.Bundle;
import android.widget.SeekBar;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;

/**
 * 健康提醒设置 Activity
 */
public class HealthRemindersActivity extends AppCompatActivity 
    implements HealthReminderService.HealthReminderListener {
    
    private HealthReminderService healthService;
    
    // UI 组件
    private Switch switchSit;
    private Switch switchWater;
    private Switch switchEye;
    private SeekBar seekSit;
    private SeekBar seekWater;
    private SeekBar seekEye;
    private TextView tvSitInterval;
    private TextView tvWaterInterval;
    private TextView tvEyeInterval;
    private TextView tvWorkHours;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_health_reminders);
        
        healthService = new HealthReminderService(this);
        HealthReminderService.setListener(this);
        
        initViews();
        loadSettings();
        setupListeners();
        
        // 启动提醒
        healthService.startAllReminders();
    }
    
    private void initViews() {
        switchSit = findViewById(R.id.switchSit);
        switchWater = findViewById(R.id.switchWater);
        switchEye = findViewById(R.id.switchEye);
        seekSit = findViewById(R.id.seekSit);
        seekWater = findViewById(R.id.seekWater);
        seekEye = findViewById(R.id.seekEye);
        tvSitInterval = findViewById(R.id.tvSitInterval);
        tvWaterInterval = findViewById(R.id.tvWaterInterval);
        tvEyeInterval = findViewById(R.id.tvEyeInterval);
        tvWorkHours = findViewById(R.id.tvWorkHours);
    }
    
    private void loadSettings() {
        switchSit.setChecked(healthService.isSitReminderEnabled());
        switchWater.setChecked(healthService.isWaterReminderEnabled());
        switchEye.setChecked(healthService.isEyeReminderEnabled());
        
        seekSit.setProgress(healthService.getSitInterval());
        seekWater.setProgress(healthService.getWaterInterval());
        seekEye.setProgress(healthService.getEyeInterval());
        
        updateIntervalTexts();
        updateWorkHoursText();
    }
    
    private void setupListeners() {
        // 久坐提醒
        switchSit.setOnCheckedChangeListener((buttonView, isChecked) -> {
            healthService.setSitReminderEnabled(isChecked);
            Toast.makeText(this, isChecked ? "久坐提醒已启用" : "久坐提醒已禁用", Toast.LENGTH_SHORT).show();
        });
        
        seekSit.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                healthService.setSitInterval(progress);
                tvSitInterval.setText(progress + " 分钟");
            }
            @Override public void onStartTrackingTouch(SeekBar seekBar) {}
            @Override public void onStopTrackingTouch(SeekBar seekBar) {
                healthService.saveSettings();
            }
        });
        
        // 喝水提醒
        switchWater.setOnCheckedChangeListener((buttonView, isChecked) -> {
            healthService.setWaterReminderEnabled(isChecked);
            Toast.makeText(this, isChecked ? "喝水提醒已启用" : "喝水提醒已禁用", Toast.LENGTH_SHORT).show();
        });
        
        seekWater.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                healthService.setWaterInterval(progress);
                tvWaterInterval.setText(progress + " 分钟");
            }
            @Override public void onStartTrackingTouch(SeekBar seekBar) {}
            @Override public void onStopTrackingTouch(SeekBar seekBar) {
                healthService.saveSettings();
            }
        });
        
        // 眼保健提醒
        switchEye.setOnCheckedChangeListener((buttonView, isChecked) -> {
            healthService.setEyeReminderEnabled(isChecked);
            Toast.makeText(this, isChecked ? "眼保健提醒已启用" : "眼保健提醒已禁用", Toast.LENGTH_SHORT).show();
        });
        
        seekEye.setOnSeekBarChangeListener(new SeekBar.OnSeekBarChangeListener() {
            @Override public void onProgressChanged(SeekBar seekBar, int progress, boolean fromUser) {
                healthService.setEyeInterval(progress);
                tvEyeInterval.setText(progress + " 分钟");
            }
            @Override public void onStartTrackingTouch(SeekBar seekBar) {}
            @Override public void onStopTrackingTouch(SeekBar seekBar) {
                healthService.saveSettings();
            }
        });
    }
    
    private void updateIntervalTexts() {
        tvSitInterval.setText(healthService.getSitInterval() + " 分钟");
        tvWaterInterval.setText(healthService.getWaterInterval() + " 分钟");
        tvEyeInterval.setText(healthService.getEyeInterval() + " 分钟");
    }
    
    private void updateWorkHoursText() {
        tvWorkHours.setText(String.format("%02d:00 - %02d:00", 
            healthService.getWorkStartHour(), healthService.getWorkEndHour()));
    }
    
    // ============== 提醒触发回调 ==============
    
    @Override
    public void onSitReminder() {
        runOnUiThread(() -> {
            Toast.makeText(this, "💺 久坐提醒：起来活动一下吧！", Toast.LENGTH_LONG).show();
            
            // 发送通知
            NotificationHelper.sendHealthNotification(this, 
                "💺 久坐提醒", 
                "已经坐了 1 小时，起来活动活动吧~");
        });
    }
    
    @Override
    public void onWaterReminder() {
        runOnUiThread(() -> {
            Toast.makeText(this, "💧 喝水提醒：该喝水了！", Toast.LENGTH_LONG).show();
            
            NotificationHelper.sendHealthNotification(this,
                "💧 喝水提醒",
                "记得多喝水，保持身体健康~");
        });
    }
    
    @Override
    public void onEyeReminder() {
        runOnUiThread(() -> {
            Toast.makeText(this, "👁️ 眼保健提醒：让眼睛休息一下吧！", Toast.LENGTH_LONG).show();
            
            NotificationHelper.sendHealthNotification(this,
                "👁️ 眼保健提醒",
                "看看远方，做做眼保健操~");
        });
    }
    
    // 生活提醒
    @Override
    public void onBreakfastReminder() {
        runOnUiThread(() -> {
            Toast.makeText(this, "🍳 早餐提醒：该吃早餐了！", Toast.LENGTH_LONG).show();
            NotificationHelper.sendHealthNotification(this,
                "🍳 早餐提醒",
                "记得吃营养丰富的早餐，开启美好的一天~");
        });
    }
    
    @Override
    public void onLunchReminder() {
        runOnUiThread(() -> {
            Toast.makeText(this, "🍱 午餐提醒：该吃午餐了！", Toast.LENGTH_LONG).show();
            NotificationHelper.sendHealthNotification(this,
                "🍱 午餐提醒",
                "好好吃饭，下午才有精神~");
        });
    }
    
    @Override
    public void onDinnerReminder() {
        runOnUiThread(() -> {
            Toast.makeText(this, "🍲 晚餐提醒：该吃晚餐了！", Toast.LENGTH_LONG).show();
            NotificationHelper.sendHealthNotification(this,
                "🍲 晚餐提醒",
                "晚餐别吃太饱，清淡一点更健康~");
        });
    }
    
    @Override
    public void onSleepReminder() {
        runOnUiThread(() -> {
            Toast.makeText(this, "🌙 睡觉提醒：该准备睡觉了！", Toast.LENGTH_LONG).show();
            NotificationHelper.sendHealthNotification(this,
                "🌙 睡觉提醒",
                "别熬夜，早睡早起身体好~");
        });
    }
    
    @Override
    public void onWakeUpReminder() {
        runOnUiThread(() -> {
            Toast.makeText(this, "☀️ 起床提醒：早上好！", Toast.LENGTH_LONG).show();
            NotificationHelper.sendHealthNotification(this,
                "☀️ 起床提醒",
                "新的一天开始了，加油！");
        });
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        // 保持服务运行，不销毁
    }
}
