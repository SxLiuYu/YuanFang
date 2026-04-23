package com.openclaw.homeassistant;

import android.content.Context;
import android.content.Intent;
import android.net.Uri;
import android.provider.AlarmClock;
import android.provider.CalendarContract;
import android.provider.MediaStore;
import android.provider.Settings;
import android.util.Log;

import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * 快捷指令服务
 * 根据用户意图执行快捷操作
 */
public class QuickActions {
    
    private static final String TAG = "QuickActions";
    private final Context context;
    
    public QuickActions(Context context) {
        this.context = context.getApplicationContext();
    }
    
    /**
     * 执行快捷指令
     * @return 执行结果
     */
    public String execute(String intent, Map<String, String> params) {
        try {
            switch (intent.toLowerCase()) {
                case "set_reminder":
                    return setReminder(params);
                case "set_alarm":
                    return setAlarm(params);
                case "get_weather":
                    return getWeather(params);
                case "create_calendar_event":
                    return createCalendarEvent(params);
                case "open_app":
                    return openApp(params);
                case "make_call":
                    return makeCall(params);
                case "send_message":
                    return sendMessage(params);
                case "play_music":
                    return playMusic(params);
                case "set_timer":
                    return setTimer(params);
                case "search_web":
                    return searchWeb(params);
                default:
                    return "暂不支持该指令";
            }
        } catch (Exception e) {
            Log.e(TAG, "执行指令失败", e);
            return "执行失败：" + e.getMessage();
        }
    }
    
    /**
     * 设置提醒
     */
    private String setReminder(Map<String, String> params) {
        String title = params.getOrDefault("title", "提醒");
        String time = params.getOrDefault("time", "");
        
        try {
            Intent intent = new Intent(AlarmClock.ACTION_SET_ALARM);
            intent.putExtra(AlarmClock.EXTRA_MESSAGE, title);
            
            if (!time.isEmpty()) {
                // 解析时间
                String[] parts = time.split(":");
                if (parts.length >= 2) {
                    int hour = Integer.parseInt(parts[0]);
                    int minute = Integer.parseInt(parts[1]);
                    intent.putExtra(AlarmClock.EXTRA_HOUR, hour);
                    intent.putExtra(AlarmClock.EXTRA_MINUTES, minute);
                }
            }
            
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(intent);
            
            return "✅ 已创建提醒：" + title + (time.isEmpty() ? "" : " " + time);
        } catch (Exception e) {
            return "❌ 创建提醒失败：" + e.getMessage();
        }
    }
    
    /**
     * 设置闹钟
     */
    private String setAlarm(Map<String, String> params) {
        String time = params.getOrDefault("time", "");
        
        try {
            Intent intent = new Intent(AlarmClock.ACTION_SET_ALARM);
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            
            if (!time.isEmpty()) {
                String[] parts = time.split(":");
                if (parts.length >= 2) {
                    int hour = Integer.parseInt(parts[0]);
                    int minute = Integer.parseInt(parts[1]);
                    intent.putExtra(AlarmClock.EXTRA_HOUR, hour);
                    intent.putExtra(AlarmClock.EXTRA_MINUTES, minute);
                }
            }
            
            context.startActivity(intent);
            return "✅ 闹钟已设置：" + time;
        } catch (Exception e) {
            return "❌ 设置闹钟失败";
        }
    }
    
    /**
     * 获取天气（调用 AI 服务）
     */
    private String getWeather(Map<String, String> params) {
        String location = params.getOrDefault("location", "北京");
        // 天气信息需要调用外部 API，这里返回提示
        return "🌤️ 正在查询 " + location + " 的天气...";
    }
    
    /**
     * 创建日历事件
     */
    private String createCalendarEvent(Map<String, String> params) {
        String title = params.getOrDefault("title", "日程");
        String description = params.getOrDefault("description", "");
        
        try {
            Intent intent = new Intent(Intent.ACTION_INSERT);
            intent.setData(CalendarContract.Events.CONTENT_URI);
            intent.putExtra(CalendarContract.Events.TITLE, title);
            intent.putExtra(CalendarContract.Events.DESCRIPTION, description);
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            
            context.startActivity(intent);
            return "✅ 已打开日历，请确认创建：" + title;
        } catch (Exception e) {
            return "❌ 创建日程失败";
        }
    }
    
    /**
     * 打开应用
     */
    private String openApp(Map<String, String> params) {
        String appName = params.getOrDefault("app", "");
        
        // 这里需要根据应用名查找包名，简化版本直接返回提示
        return "📱 正在打开 " + appName + "...";
    }
    
    /**
     * 拨打电话
     */
    private String makeCall(Map<String, String> params) {
        String phoneNumber = params.getOrDefault("phone", "");
        
        if (phoneNumber.isEmpty()) {
            return "❌ 请提供电话号码";
        }
        
        try {
            Intent intent = new Intent(Intent.ACTION_DIAL);
            intent.setData(Uri.parse("tel:" + phoneNumber));
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(intent);
            return "📞 正在拨打：" + phoneNumber;
        } catch (Exception e) {
            return "❌ 拨打电话失败";
        }
    }
    
    /**
     * 发送短信
     */
    private String sendMessage(Map<String, String> params) {
        String phoneNumber = params.getOrDefault("phone", "");
        String message = params.getOrDefault("message", "");
        
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setData(Uri.parse("sms:" + phoneNumber));
            intent.putExtra("sms_body", message);
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(intent);
            return "💬 已打开短信，发送给：" + phoneNumber;
        } catch (Exception e) {
            return "❌ 发送短信失败";
        }
    }
    
    /**
     * 播放音乐
     */
    private String playMusic(Map<String, String> params) {
        String song = params.getOrDefault("song", "");
        
        try {
            Intent intent = new Intent(Intent.ACTION_VIEW);
            intent.setDataAndType(Uri.parse("file://"), "audio/*");
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(intent);
            return "🎵 正在播放：" + (song.isEmpty() ? "音乐" : song);
        } catch (Exception e) {
            return "❌ 播放音乐失败";
        }
    }
    
    /**
     * 设置计时器
     */
    private String setTimer(Map<String, String> params) {
        String minutes = params.getOrDefault("minutes", "1");
        
        try {
            Intent intent = new Intent(AlarmClock.ACTION_SET_TIMER);
            intent.putExtra(AlarmClock.EXTRA_LENGTH, Integer.parseInt(minutes) * 60);
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(intent);
            return "⏱️ 计时器已设置：" + minutes + "分钟";
        } catch (Exception e) {
            return "❌ 设置计时器失败";
        }
    }
    
    /**
     * 搜索网页
     */
    private String searchWeb(Map<String, String> params) {
        String query = params.getOrDefault("query", "");
        
        if (query.isEmpty()) {
            return "❌ 请提供搜索内容";
        }
        
        try {
            Intent intent = new Intent(Intent.ACTION_WEB_SEARCH);
            intent.putExtra("query", query);
            intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
            context.startActivity(intent);
            return "🔍 正在搜索：" + query;
        } catch (Exception e) {
            return "❌ 搜索失败";
        }
    }
    
    /**
     * 从用户输入中识别意图
     */
    public static class IntentRecognizer {
        
        private static final Map<String, String[]> INTENT_KEYWORDS = new HashMap<>();
        
        static {
            INTENT_KEYWORDS.put("set_reminder", new String[]{"提醒", "记得", "别忘了", "提示我"});
            INTENT_KEYWORDS.put("set_alarm", new String[]{"闹钟", "叫醒我", "起床"});
            INTENT_KEYWORDS.put("get_weather", new String[]{"天气", "下雨", "温度", "几度"});
            INTENT_KEYWORDS.put("create_calendar_event", new String[]{"日程", "会议", "约会", "安排"});
            INTENT_KEYWORDS.put("make_call", new String[]{"打电话", "拨打", "联系"});
            INTENT_KEYWORDS.put("send_message", new String[]{"发短信", "发消息", "微信"});
            INTENT_KEYWORDS.put("play_music", new String[]{"播放音乐", "听歌", "唱歌"});
            INTENT_KEYWORDS.put("set_timer", new String[]{"计时", "倒计时", "分钟后"});
            INTENT_KEYWORDS.put("search_web", new String[]{"搜索", "查一下", "百度", "谷歌"});
        }
        
        /**
         * 识别用户意图
         */
        public static IntentMatch match(String query) {
            query = query.toLowerCase();
            
            for (Map.Entry<String, String[]> entry : INTENT_KEYWORDS.entrySet()) {
                for (String keyword : entry.getValue()) {
                    if (query.contains(keyword.toLowerCase())) {
                        // 提取参数
                        Map<String, String> params = extractParams(query, entry.getKey());
                        return new IntentMatch(entry.getKey(), params);
                    }
                }
            }
            
            return new IntentMatch("chat", new HashMap<>());
        }
        
        /**
         * 提取参数
         */
        private static Map<String, String> extractParams(String query, String intent) {
            Map<String, String> params = new HashMap<>();
            
            switch (intent) {
                case "set_reminder":
                case "set_alarm":
                    // 提取时间
                    if (query.matches(".*\\d{1,2}:\\d{2}.*")) {
                        String[] parts = query.split(":");
                        for (String part : parts) {
                            if (part.matches(".*\\d{1,2}$")) {
                                String time = part.replaceAll("[^0-9:]", "");
                                if (time.contains(":")) {
                                    params.put("time", time);
                                }
                            }
                        }
                    }
                    // 提取提醒内容
                    params.put("title", query.replaceAll(".*(提醒我 | 记得 | 别忘了).*", "").trim());
                    break;
                    
                case "get_weather":
                    // 提取地点
                    if (query.contains("北京")) params.put("location", "北京");
                    else if (query.contains("上海")) params.put("location", "上海");
                    else if (query.contains("广州")) params.put("location", "广州");
                    else if (query.contains("深圳")) params.put("location", "深圳");
                    else params.put("location", "本地");
                    break;
                    
                case "make_call":
                case "send_message":
                    // 提取电话号码
                    if (query.matches(".*\\d{11}.*")) {
                        params.put("phone", query.replaceAll("[^0-9]", ""));
                    }
                    break;
            }
            
            return params;
        }
    }
    
    /**
     * 意图匹配结果
     */
    public static class IntentMatch {
        public final String intent;
        public final Map<String, String> params;
        
        public IntentMatch(String intent, Map<String, String> params) {
            this.intent = intent;
            this.params = params;
        }
        
        public boolean isAction() {
            return !"chat".equals(intent);
        }
    }
}
