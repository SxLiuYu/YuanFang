package com.openclaw.homeassistant;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 主题服务
 * 支持多套主题皮肤切换
 */
public class ThemeService {
    
    private static final String TAG = "ThemeService";
    private static final String PREFS_NAME = "theme_settings";
    
    private final Context context;
    private final SharedPreferences prefs;
    
    // 预设主题
    public enum ThemeType {
        LIGHT,          // 明亮主题
        DARK,           // 深色主题
        BLUE,           // 蓝色主题
        GREEN,          // 绿色主题
        PURPLE,         // 紫色主题
        CUSTOM          // 自定义主题
    }
    
    private static ThemeService instance;
    private ThemeType currentTheme;
    
    private ThemeService(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        loadCurrentTheme();
    }
    
    public static synchronized ThemeService getInstance(Context context) {
        if (instance == null) {
            instance = new ThemeService(context.getApplicationContext());
        }
        return instance;
    }
    
    /**
     * 获取所有可用主题
     */
    public List<ThemeInfo> getAvailableThemes() {
        List<ThemeInfo> themes = new ArrayList<>();
        
        themes.add(new ThemeInfo(ThemeType.LIGHT, "明亮", "#FFFFFF", "#000000", "#2196F3"));
        themes.add(new ThemeInfo(ThemeType.DARK, "深色", "#121212", "#FFFFFF", "#BB86FC"));
        themes.add(new ThemeInfo(ThemeType.BLUE, "蓝色", "#E3F2FD", "#0D47A1", "#2196F3"));
        themes.add(new ThemeInfo(ThemeType.GREEN, "绿色", "#E8F5E9", "#1B5E20", "#4CAF50"));
        themes.add(new ThemeInfo(ThemeType.PURPLE, "紫色", "#F3E5F5", "#4A148C", "#9C27B0"));
        
        // 加载自定义主题
        String customJson = prefs.getString("custom_theme", null);
        if (customJson != null) {
            try {
                JSONObject json = new JSONObject(customJson);
                themes.add(new ThemeInfo(
                    ThemeType.CUSTOM,
                    json.optString("name", "自定义"),
                    json.optString("background", "#FFFFFF"),
                    json.optString("text", "#000000"),
                    json.optString("accent", "#2196F3")
                ));
            } catch (Exception e) {
                Log.e(TAG, "加载自定义主题失败", e);
            }
        }
        
        return themes;
    }
    
    /**
     * 应用主题
     */
    public void applyTheme(ThemeType theme) {
        currentTheme = theme;
        prefs.edit().putString("current_theme", theme.name()).apply();
        Log.d(TAG, "应用主题：" + theme);
    }
    
    /**
     * 获取当前主题
     */
    public ThemeType getCurrentTheme() {
        return currentTheme;
    }
    
    /**
     * 获取主题颜色
     */
    public Map<String, String> getThemeColors(ThemeType theme) {
        Map<String, String> colors = new HashMap<>();
        
        switch (theme) {
            case LIGHT:
                colors.put("background", "#FFFFFF");
                colors.put("surface", "#F5F5F5");
                colors.put("primary", "#2196F3");
                colors.put("onPrimary", "#FFFFFF");
                colors.put("secondary", "#03DAC6");
                colors.put("onSecondary", "#000000");
                colors.put("text", "#000000");
                colors.put("onBackground", "#000000");
                break;
                
            case DARK:
                colors.put("background", "#121212");
                colors.put("surface", "#1E1E1E");
                colors.put("primary", "#BB86FC");
                colors.put("onPrimary", "#000000");
                colors.put("secondary", "#03DAC6");
                colors.put("onSecondary", "#000000");
                colors.put("text", "#FFFFFF");
                colors.put("onBackground", "#FFFFFF");
                break;
                
            case BLUE:
                colors.put("background", "#E3F2FD");
                colors.put("surface", "#BBDEFB");
                colors.put("primary", "#2196F3");
                colors.put("onPrimary", "#FFFFFF");
                colors.put("secondary", "#64B5F6");
                colors.put("onSecondary", "#000000");
                colors.put("text", "#0D47A1");
                colors.put("onBackground", "#0D47A1");
                break;
                
            case GREEN:
                colors.put("background", "#E8F5E9");
                colors.put("surface", "#C8E6C9");
                colors.put("primary", "#4CAF50");
                colors.put("onPrimary", "#FFFFFF");
                colors.put("secondary", "#81C784");
                colors.put("onSecondary", "#000000");
                colors.put("text", "#1B5E20");
                colors.put("onBackground", "#1B5E20");
                break;
                
            case PURPLE:
                colors.put("background", "#F3E5F5");
                colors.put("surface", "#E1BEE7");
                colors.put("primary", "#9C27B0");
                colors.put("onPrimary", "#FFFFFF");
                colors.put("secondary", "#BA68C8");
                colors.put("onSecondary", "#000000");
                colors.put("text", "#4A148C");
                colors.put("onBackground", "#4A148C");
                break;
                
            case CUSTOM:
                // 加载自定义颜色
                String customJson = prefs.getString("custom_theme", null);
                if (customJson != null) {
                    try {
                        JSONObject json = new JSONObject(customJson);
                        colors.put("background", json.optString("background", "#FFFFFF"));
                        colors.put("surface", json.optString("surface", "#F5F5F5"));
                        colors.put("primary", json.optString("primary", "#2196F3"));
                        colors.put("onPrimary", json.optString("onPrimary", "#FFFFFF"));
                        colors.put("secondary", json.optString("secondary", "#03DAC6"));
                        colors.put("onSecondary", json.optString("onSecondary", "#000000"));
                        colors.put("text", json.optString("text", "#000000"));
                        colors.put("onBackground", json.optString("onBackground", "#000000"));
                    } catch (Exception e) {
                        Log.e(TAG, "加载自定义颜色失败", e);
                    }
                }
                break;
        }
        
        return colors;
    }
    
    /**
     * 保存自定义主题
     */
    public void saveCustomTheme(String name, Map<String, String> colors) {
        try {
            JSONObject json = new JSONObject();
            json.put("name", name);
            for (Map.Entry<String, String> entry : colors.entrySet()) {
                json.put(entry.getKey(), entry.getValue());
            }
            
            prefs.edit().putString("custom_theme", json.toString()).apply();
            Log.d(TAG, "保存自定义主题：" + name);
        } catch (Exception e) {
            Log.e(TAG, "保存自定义主题失败", e);
        }
    }
    
    /**
     * 删除自定义主题
     */
    public void deleteCustomTheme() {
        prefs.edit().remove("custom_theme").apply();
        Log.d(TAG, "删除自定义主题");
    }
    
    /**
     * 根据时间自动切换主题
     */
    public void autoThemeByTime() {
        int hour = java.util.Calendar.getInstance().get(java.util.Calendar.HOUR_OF_DAY);
        
        if (hour >= 6 && hour < 18) {
            // 白天使用明亮主题
            applyTheme(ThemeType.LIGHT);
        } else {
            // 晚上使用深色主题
            applyTheme(ThemeType.DARK);
        }
        
        Log.d(TAG, "根据时间自动切换主题：" + (hour >= 6 && hour < 18 ? "明亮" : "深色"));
    }
    
    /**
     * 加载当前主题
     */
    private void loadCurrentTheme() {
        String themeName = prefs.getString("current_theme", ThemeType.LIGHT.name());
        try {
            currentTheme = ThemeType.valueOf(themeName);
        } catch (Exception e) {
            currentTheme = ThemeType.LIGHT;
        }
    }
    
    // ========== 主题信息类 ==========
    
    public static class ThemeInfo {
        public ThemeType type;
        public String name;
        public String backgroundColor;
        public String textColor;
        public String accentColor;
        
        public ThemeInfo(ThemeType type, String name, String bg, String text, String accent) {
            this.type = type;
            this.name = name;
            this.backgroundColor = bg;
            this.textColor = text;
            this.accentColor = accent;
        }
    }
}
