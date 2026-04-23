package com.openclaw.homeassistant;

import android.app.AlarmManager;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.content.IntentFilter;
import android.location.Location;
import android.os.BatteryManager;
import android.os.Build;
import android.os.PowerManager;
import android.speech.tts.TextToSpeech;
import android.util.Log;

import androidx.annotation.NonNull;
import androidx.core.app.NotificationCompat;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * 自动化引擎
 * 功能：
 * 1. 解析自动化规则
 * 2. 监听触发器（时间、电量、充电、GPS）
 * 3. 执行动作（TTS 播报、通知推送）
 * 4. 管理规则状态
 */
public class AutomationEngine {
    
    private static final String TAG = "AutomationEngine";
    private static final String NOTIFICATION_CHANNEL_ID = "automation_notifications";
    
    private final Context context;
    private final ConfigManager configManager;
    private final DashScopeService dashScopeService;
    private final NewsService newsService;
    private final AutomationLogger logger;
    private TextToSpeech textToSpeech;
    
    private List<AutomationRule> activeRules;
    private PowerManager.WakeLock wakeLock;
    private boolean isRunning = false;
    
    // 电量状态
    private int currentBatteryLevel = -1;
    private boolean isCharging = false;
    
    // 触发器广播接收器
    private BroadcastReceiver batteryReceiver;
    private BroadcastReceiver powerReceiver;
    private BroadcastReceiver timeReceiver;
    
    public AutomationEngine(Context context, ConfigManager configManager, DashScopeService dashScopeService) {
        this.context = context.getApplicationContext();
        this.configManager = configManager;
        this.dashScopeService = dashScopeService;
        this.newsService = new NewsService();
        this.logger = new AutomationLogger(context);
        this.activeRules = new ArrayList<>();
        
        initTTS();
        createNotificationChannel();
    }
    
    // ============== 初始化/启动/停止 ==============
    
    private void initTTS() {
        textToSpeech = new TextToSpeech(context, status -> {
            if (status == TextToSpeech.SUCCESS) {
                textToSpeech.setLanguage(Locale.CHINESE);
                Log.d(TAG, "TTS 初始化成功");
            }
        });
    }
    
    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                NOTIFICATION_CHANNEL_ID,
                "自动化通知",
                NotificationManager.IMPORTANCE_DEFAULT
            );
            channel.setDescription("自动化场景触发的通知");
            
            NotificationManager manager = context.getSystemService(NotificationManager.class);
            if (manager != null) {
                manager.createNotificationChannel(channel);
            }
        }
    }
    
    /**
     * 启动自动化引擎
     */
    public void start() {
        if (isRunning) {
            Log.w(TAG, "自动化引擎已在运行");
            return;
        }
        
        Log.d(TAG, "启动自动化引擎");
        isRunning = true;
        
        // 加载规则
        loadRules();
        
        // 注册广播接收器
        registerReceivers();
        
        // 调度时间触发器
        scheduleTimeTriggers();
    }
    
    /**
     * 停止自动化引擎
     */
    public void stop() {
        if (!isRunning) return;
        
        Log.d(TAG, "停止自动化引擎");
        isRunning = false;
        
        // 注销广播接收器
        unregisterReceivers();
        
        // 取消所有调度的闹钟
        cancelAllAlarms();
        
        // 清空规则
        activeRules.clear();
    }
    
    // ============== 规则管理 ==============
    
    /**
     * 从配置加载规则
     */
    private void loadRules() {
        activeRules.clear();
        
        JSONArray rules = configManager.getAutomationRules();
        if (rules == null) {
            Log.d(TAG, "没有自动化规则");
            return;
        }
        
        for (int i = 0; i < rules.length(); i++) {
            try {
                JSONObject ruleJson = rules.getJSONObject(i);
                if (ruleJson.optBoolean("enabled", true)) {
                    AutomationRule rule = AutomationRule.fromJson(ruleJson);
                    if (rule != null) {
                        activeRules.add(rule);
                        Log.d(TAG, "加载规则：" + rule.name);
                    }
                }
            } catch (JSONException e) {
                Log.e(TAG, "解析规则失败", e);
            }
        }
        
        Log.d(TAG, "共加载 " + activeRules.size() + " 条规则");
    }
    
    /**
     * 重新加载规则（配置变更时调用）
     */
    public void reloadRules() {
        Log.d(TAG, "重新加载规则");
        stop();
        start();
    }
    
    // ============== 广播接收器 ==============
    
    private void registerReceivers() {
        // 电量变化
        batteryReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                if (Intent.ACTION_BATTERY_CHANGED.equals(intent.getAction())) {
                    int level = intent.getIntExtra(BatteryManager.EXTRA_LEVEL, -1);
                    int scale = intent.getIntExtra(BatteryManager.EXTRA_SCALE, -1);
                    int batteryPct = (int) ((level / (float) scale) * 100);
                    
                    int status = intent.getIntExtra(BatteryManager.EXTRA_STATUS, -1);
                    boolean charging = status == BatteryManager.BATTERY_STATUS_CHARGING ||
                                      status == BatteryManager.BATTERY_STATUS_FULL;
                    
                    onBatteryChanged(batteryPct, charging);
                }
            }
        };
        context.registerReceiver(batteryReceiver, new IntentFilter(Intent.ACTION_BATTERY_CHANGED));
        
        // 充电状态变化
        powerReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                if (Intent.ACTION_POWER_CONNECTED.equals(intent.getAction())) {
                    onPowerStateChanged(true);
                } else if (Intent.ACTION_POWER_DISCONNECTED.equals(intent.getAction())) {
                    onPowerStateChanged(false);
                }
            }
        };
        IntentFilter powerFilter = new IntentFilter();
        powerFilter.addAction(Intent.ACTION_POWER_CONNECTED);
        powerFilter.addAction(Intent.ACTION_POWER_DISCONNECTED);
        context.registerReceiver(powerReceiver, powerFilter);
        
        // 时间触发器（每分钟检查）
        timeReceiver = new BroadcastReceiver() {
            @Override
            public void onReceive(Context context, Intent intent) {
                onTimeTick();
            }
        };
        IntentFilter timeFilter = new IntentFilter("com.openclaw.TIME_TICK");
        context.registerReceiver(timeReceiver, timeFilter);
    }
    
    private void unregisterReceivers() {
        try {
            if (batteryReceiver != null) context.unregisterReceiver(batteryReceiver);
            if (powerReceiver != null) context.unregisterReceiver(powerReceiver);
            if (timeReceiver != null) context.unregisterReceiver(timeReceiver);
        } catch (Exception e) {
            Log.e(TAG, "注销接收器失败", e);
        }
    }
    
    // ============== 触发器处理 ==============
    
    private void onBatteryChanged(int batteryLevel, boolean charging) {
        Log.d(TAG, "电量变化：" + batteryLevel + "%, 充电：" + charging);
        
        currentBatteryLevel = batteryLevel;
        isCharging = charging;
        
        for (AutomationRule rule : activeRules) {
            if (rule.checkBatteryTrigger(batteryLevel, charging)) {
                Log.d(TAG, "触发规则：" + rule.name + " (电量)");
                executeRule(rule);
            }
        }
    }
    
    private void onPowerStateChanged(boolean plugged) {
        Log.d(TAG, "电源状态变化：" + (plugged ? "已连接" : "已断开"));
        
        isCharging = plugged;
        
        for (AutomationRule rule : activeRules) {
            if (rule.checkPowerTrigger(plugged)) {
                Log.d(TAG, "触发规则：" + rule.name + " (电源)");
                executeRule(rule);
            }
        }
    }
    
    private void onTimeTick() {
        Calendar now = Calendar.getInstance();
        int hour = now.get(Calendar.HOUR_OF_DAY);
        int minute = now.get(Calendar.MINUTE);
        int dayOfWeek = now.get(Calendar.DAY_OF_WEEK) - 1; // 0=周日
        
        String currentTime = String.format(Locale.getDefault(), "%02d:%02d", hour, minute);
        
        for (AutomationRule rule : activeRules) {
            if (rule.checkTimeTrigger(currentTime, dayOfWeek)) {
                Log.d(TAG, "触发规则：" + rule.name + " (时间：" + currentTime + ")");
                executeRule(rule);
            }
        }
    }
    
    // ============== 闹钟调度 ==============
    
    private void scheduleTimeTriggers() {
        AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (alarmManager == null) return;
        
        for (AutomationRule rule : activeRules) {
            for (Trigger trigger : rule.triggers) {
                if ("time".equals(trigger.type)) {
                    scheduleAlarm(alarmManager, rule.id, trigger.time);
                }
            }
        }
    }
    
    private void scheduleAlarm(AlarmManager alarmManager, String ruleId, String time) {
        try {
            String[] parts = time.split(":");
            int hour = Integer.parseInt(parts[0]);
            int minute = Integer.parseInt(parts[1]);
            
            Calendar calendar = Calendar.getInstance();
            calendar.set(Calendar.HOUR_OF_DAY, hour);
            calendar.set(Calendar.MINUTE, minute);
            calendar.set(Calendar.SECOND, 0);
            
            // 如果时间已过，设置为明天
            if (calendar.getTimeInMillis() <= System.currentTimeMillis()) {
                calendar.add(Calendar.DAY_OF_YEAR, 1);
            }
            
            Intent intent = new Intent("com.openclaw.TIME_TICK");
            intent.putExtra("rule_id", ruleId);
            PendingIntent pendingIntent = PendingIntent.getBroadcast(
                context, ruleId.hashCode(), intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
            );
            
            // 每天重复
            alarmManager.setRepeating(
                AlarmManager.RTC_WAKEUP,
                calendar.getTimeInMillis(),
                AlarmManager.INTERVAL_DAY,
                pendingIntent
            );
            
            Log.d(TAG, "调度闹钟：" + ruleId + " " + time);
            
        } catch (Exception e) {
            Log.e(TAG, "调度闹钟失败", e);
        }
    }
    
    private void cancelAllAlarms() {
        AlarmManager alarmManager = (AlarmManager) context.getSystemService(Context.ALARM_SERVICE);
        if (alarmManager == null) return;
        
        for (AutomationRule rule : activeRules) {
            Intent intent = new Intent("com.openclaw.TIME_TICK");
            PendingIntent pendingIntent = PendingIntent.getBroadcast(
                context, rule.id.hashCode(), intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
            );
            alarmManager.cancel(pendingIntent);
        }
    }
    
    // ============== 动作执行 ==============
    
    private void executeRule(AutomationRule rule) {
        Log.d(TAG, "执行规则：" + rule.name);
        
        // 记录触发日志
        logger.logTrigger(rule.id, rule.name, "auto");
        
        // 获取 WakeLock 防止休眠
        acquireWakeLock();
        
        for (Action action : rule.actions) {
            executeAction(action, rule.id);
        }
        
        releaseWakeLock();
    }
    
    private void executeAction(Action action, String ruleId) {
        Log.d(TAG, "执行动作：" + action.type);
        
        // 记录动作日志
        logger.logAction(ruleId, action.type, action.title != null ? action.title : "");
        
        switch (action.type) {
            case "speak":
                executeSpeak(action);
                break;
            case "notify":
                executeNotify(action, ruleId);
                break;
            case "launch":
                executeLaunch(action);
                break;
        }
    }
    
    private void executeSpeak(Action action) {
        String text = action.text;
        
        // 如果是模板，生成内容
        if (action.template != null) {
            text = generateTemplateContent(action.template);
        }
        
        if (text != null && textToSpeech != null) {
            textToSpeech.speak(text, TextToSpeech.QUEUE_FLUSH, null, null);
            Log.d(TAG, "TTS 播报：" + text);
        }
    }
    
    private void executeNotify(Action action, String ruleId) {
        NotificationManager manager = (NotificationManager) 
            context.getSystemService(Context.NOTIFICATION_SERVICE);
        if (manager == null) return;
        
        String title = action.title;
        String message = action.message != null ? action.message : "";
        
        // 创建点击 Intent
        Intent clickIntent = new Intent(context, SettingsActivity.class);
        clickIntent.putExtra("rule_id", ruleId);
        clickIntent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        
        PendingIntent pendingIntent = PendingIntent.getActivity(
            context, ruleId.hashCode(), clickIntent,
            PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );
        
        NotificationCompat.Builder builder = new NotificationCompat.Builder(context, NOTIFICATION_CHANNEL_ID)
            .setSmallIcon(android.R.drawable.ic_dialog_info)
            .setContentTitle(title)
            .setContentText(message)
            .setPriority(NotificationCompat.PRIORITY_DEFAULT)
            .setAutoCancel(true)
            .setContentIntent(pendingIntent);
        
        manager.notify(ruleId.hashCode(), builder.build());
        Log.d(TAG, "发送通知：" + title);
    }
    
    private void executeLaunch(Action action) {
        try {
            Intent intent = context.getPackageManager().getLaunchIntentForPackage(action.packageName);
            if (intent != null) {
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                context.startActivity(intent);
                Log.d(TAG, "启动应用：" + action.packageName);
            }
        } catch (Exception e) {
            Log.e(TAG, "启动应用失败", e);
        }
    }
    
    private String generateTemplateContent(String template) {
        switch (template) {
            case "weather_commute":
                return getWeatherAndCommute();
            case "tomorrow_weather":
                return getTomorrowWeather();
            case "news_brief":
                return getNewsBrief();
            default:
                return null;
        }
    }
    
    /**
     * 获取简要资讯 (天气 +AI+ 财经)
     */
    private String getNewsBrief() {
        try {
            JSONObject weather = fetchWeather();
            String weatherText = weather != null ? 
                weather.optString("weather", "晴") + "，温度" + weather.optInt("temp", 20) + "度" : 
                "天气信息获取失败";
            
            String aiNews = newsService.getAINewsBrief();
            String financeNews = newsService.getFinanceNewsBrief();
            
            return String.format("早上好！北京今天%s。AI 动态：%s。财经：%s。", 
                weatherText, aiNews, financeNews);
            
        } catch (Exception e) {
            Log.e(TAG, "获取资讯失败", e);
            return "早上好！最新资讯获取失败，请稍后重试。";
        }
    }
    
    /**
     * 获取实时天气 + 通勤建议
     */
    private String getWeatherAndCommute() {
        try {
            JSONObject weather = fetchWeather();
            if (weather == null) {
                return "早上好！天气信息获取失败，请注意查看实时天气。";
            }
            
            String weatherText = weather.optString("weather", "晴");
            int temp = weather.optInt("temp", 20);
            String commuteAdvice = getCommuteAdvice(weatherText, temp);
            
            return String.format("早上好！北京今天%s，温度%d度。%s", weatherText, temp, commuteAdvice);
            
        } catch (Exception e) {
            Log.e(TAG, "获取天气失败", e);
            return "早上好！今天天气不错，通勤路上请注意安全。";
        }
    }
    
    /**
     * 获取明日天气
     */
    private String getTomorrowWeather() {
        try {
            JSONObject weather = fetchWeather();
            if (weather == null) {
                return "明天天气信息获取失败，建议查看天气预报。";
            }
            
            String weatherText = weather.optString("weather", "晴");
            int temp = weather.optInt("temp", 20);
            
            return String.format("明天预计%s，温度%d度左右。", weatherText, temp);
            
        } catch (Exception e) {
            Log.e(TAG, "获取天气失败", e);
            return "明天天气晴朗，温度适宜。";
        }
    }
    
    /**
     * 从 wttr.in 获取天气
     */
    private JSONObject fetchWeather() {
        try {
            URL url = new URL("http://wttr.in/Beijing?format=j1");
            HttpURLConnection conn = (HttpURLConnection) url.openConnection();
            conn.setConnectTimeout(5000);
            conn.setReadTimeout(5000);
            conn.setRequestMethod("GET");
            
            BufferedReader reader = new BufferedReader(
                new InputStreamReader(conn.getInputStream()));
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line);
            }
            reader.close();
            conn.disconnect();
            
            JSONObject json = new JSONObject(sb.toString());
            JSONArray currentCondition = json.getJSONArray("current_condition");
            JSONObject current = currentCondition.getJSONObject(0);
            
            JSONArray weatherDesc = current.getJSONObject("weatherDesc").getJSONArray("weatherDesc");
            String weatherEn = weatherDesc.getJSONObject(0).getString("value");
            
            JSONObject result = new JSONObject();
            result.put("weather", mapWeatherDesc(weatherEn));
            result.put("temp", current.getInt("temp_C"));
            result.put("feels_like", current.getInt("FeelsLikeC"));
            result.put("humidity", current.getInt("humidity"));
            
            return result;
            
        } catch (Exception e) {
            Log.e(TAG, "获取天气失败", e);
            return null;
        }
    }
    
    /**
     * 天气描述映射
     */
    private String mapWeatherDesc(String enDesc) {
        if (enDesc.contains("Sunny") || enDesc.contains("Clear")) return "晴";
        if (enDesc.contains("Cloudy") || enDesc.contains("Overcast")) return "阴";
        if (enDesc.contains("rain")) return "雨";
        if (enDesc.contains("snow")) return "雪";
        if (enDesc.contains("Mist") || enDesc.contains("Fog")) return "雾";
        return "晴";
    }
    
    /**
     * 生成通勤建议
     */
    private String getCommuteAdvice(String weather, int temp) {
        StringBuilder advice = new StringBuilder();
        
        if (weather.contains("雨")) {
            advice.append("携带雨具，路面湿滑注意安全。");
        } else if (weather.contains("雪")) {
            advice.append("路面可能结冰，提前出门防滑。");
        } else if (weather.contains("雾")) {
            advice.append("能见度低，注意交通安全。");
        } else {
            advice.append("天气良好，适合出行。");
        }
        
        if (temp < 5) {
            advice.append("气温较低，注意保暖。");
        } else if (temp > 30) {
            advice.append("高温天气，注意防暑。");
        }
        
        return advice.toString();
    }
    
    // ============== WakeLock ==============
    
    private void acquireWakeLock() {
        if (wakeLock == null) {
            PowerManager powerManager = (PowerManager) context.getSystemService(Context.POWER_SERVICE);
            wakeLock = powerManager.newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "openclaw:automation");
        }
        if (!wakeLock.isHeld()) {
            wakeLock.acquire(10 * 60 * 1000L); // 最多 10 分钟
        }
    }
    
    private void releaseWakeLock() {
        if (wakeLock != null && wakeLock.isHeld()) {
            wakeLock.release();
        }
    }
    
    // ============== 内部类 ==============
    
    /**
     * 自动化规则
     */
    static class AutomationRule {
        String id;
        String name;
        boolean enabled;
        List<Trigger> triggers;
        List<Action> actions;
        
        static AutomationRule fromJson(JSONObject json) {
            try {
                AutomationRule rule = new AutomationRule();
                rule.id = json.getString("id");
                rule.name = json.getString("name");
                rule.enabled = json.optBoolean("enabled", true);
                
                rule.triggers = new ArrayList<>();
                JSONArray triggersJson = json.getJSONArray("triggers");
                for (int i = 0; i < triggersJson.length(); i++) {
                    Trigger trigger = Trigger.fromJson(triggersJson.getJSONObject(i));
                    if (trigger != null) rule.triggers.add(trigger);
                }
                
                rule.actions = new ArrayList<>();
                JSONArray actionsJson = json.getJSONArray("actions");
                for (int i = 0; i < actionsJson.length(); i++) {
                    Action action = Action.fromJson(actionsJson.getJSONObject(i));
                    if (action != null) rule.actions.add(action);
                }
                
                return rule;
                
            } catch (JSONException e) {
                Log.e(TAG, "解析规则失败", e);
                return null;
            }
        }
        
        boolean checkTimeTrigger(String currentTime, int dayOfWeek) {
            for (Trigger trigger : triggers) {
                if ("time".equals(trigger.type) && currentTime.equals(trigger.time)) {
                    // 检查星期（如果指定了）
                    if (trigger.days != null && !trigger.days.contains(dayOfWeek)) {
                        continue;
                    }
                    return true;
                }
            }
            return false;
        }
        
        boolean checkBatteryTrigger(int batteryLevel, boolean charging) {
            for (Trigger trigger : triggers) {
                if ("battery".equals(trigger.type)) {
                    if (batteryLevel <= trigger.levelBelow) {
                        return true;
                    }
                }
            }
            return false;
        }
        
        boolean checkPowerTrigger(boolean plugged) {
            for (Trigger trigger : triggers) {
                if ("power".equals(trigger.type)) {
                    if ("plugged".equals(trigger.state) && plugged) return true;
                    if ("unplugged".equals(trigger.state) && !plugged) return true;
                }
            }
            return false;
        }
    }
    
    /**
     * 触发器
     */
    static class Trigger {
        String type;
        String time;
        List<Integer> days;
        int levelBelow;
        String state;
        
        static Trigger fromJson(JSONObject json) {
            try {
                Trigger trigger = new Trigger();
                trigger.type = json.getString("type");
                
                switch (trigger.type) {
                    case "time":
                        trigger.time = json.getString("time");
                        if (json.has("days")) {
                            trigger.days = new ArrayList<>();
                            JSONArray daysJson = json.getJSONArray("days");
                            for (int i = 0; i < daysJson.length(); i++) {
                                trigger.days.add(daysJson.getInt(i));
                            }
                        }
                        break;
                    case "battery":
                        trigger.levelBelow = json.getInt("level_below");
                        break;
                    case "power":
                        trigger.state = json.getString("state");
                        break;
                }
                
                return trigger;
                
            } catch (JSONException e) {
                Log.e(TAG, "解析触发器失败", e);
                return null;
            }
        }
    }
    
    /**
     * 动作
     */
    static class Action {
        String type;
        String text;
        String template;
        String title;
        String message;
        String packageName;
        
        static Action fromJson(JSONObject json) {
            try {
                Action action = new Action();
                action.type = json.getString("type");
                
                switch (action.type) {
                    case "speak":
                        action.text = json.optString("text");
                        action.template = json.optString("template");
                        break;
                    case "notify":
                        action.title = json.getString("title");
                        action.message = json.optString("message");
                        break;
                    case "launch":
                        action.packageName = json.getString("package");
                        break;
                }
                
                return action;
                
            } catch (JSONException e) {
                Log.e(TAG, "解析动作失败", e);
                return null;
            }
        }
    }
}
