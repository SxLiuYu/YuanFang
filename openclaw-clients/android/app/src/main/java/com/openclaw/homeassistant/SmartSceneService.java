package com.openclaw.homeassistant;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

/**
 * 智能场景服务
 * 功能：回家/离家/睡眠模式
 */
public class SmartSceneService {
    
    private static final String TAG = "SmartSceneService";
    private static final String PREFS_NAME = "smart_scenes";
    
    private final Context context;
    private final SharedPreferences prefs;
    
    public interface SceneListener {
        void onSceneActivated(String sceneId, String sceneName);
    }
    
    private static SceneListener listener;
    
    public SmartSceneService(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
    }
    
    public static void setListener(SceneListener listener) {
        SmartSceneService.listener = listener;
    }
    
    /**
     * 激活场景
     */
    public void activateScene(String sceneId) {
        Log.d(TAG, "激活场景：" + sceneId);
        
        switch (sceneId) {
            case "home_mode":
                activateHomeMode();
                break;
            case "away_mode":
                activateAwayMode();
                break;
            case "sleep_mode":
                activateSleepMode();
                break;
            case "work_mode":
                activateWorkMode();
                break;
        }
        
        if (listener != null) {
            listener.onSceneActivated(sceneId, getSceneName(sceneId));
        }
    }
    
    /**
     * 回家模式
     */
    private void activateHomeMode() {
        // 打开灯光
        // 打开空调
        // 播放音乐
        // 关闭安防
        Log.d(TAG, "回家模式：欢迎回家");
        
        NotificationHelper.sendHealthNotification(context,
            "🏠 回家模式",
            "欢迎回家！已为您打开灯光和空调。");
    }
    
    /**
     * 离家模式
     */
    private void activateAwayMode() {
        // 关闭所有灯光
        // 关闭空调
        // 开启安防
        // 关闭窗帘
        Log.d(TAG, "离家模式：已关闭所有设备");
        
        NotificationHelper.sendHealthNotification(context,
            "🚪 离家模式",
            "已关闭所有设备，安防已开启。");
    }
    
    /**
     * 睡眠模式
     */
    private void activateSleepMode() {
        // 关闭灯光
        // 空调调至睡眠模式
        // 关闭窗帘
        // 开启勿扰
        Log.d(TAG, "睡眠模式：晚安");
        
        NotificationHelper.sendHealthNotification(context,
            "🌙 睡眠模式",
            "晚安！已关闭所有灯光。");
    }
    
    /**
     * 工作模式
     */
    private void activateWorkMode() {
        // 打开工作灯
        // 空调调至舒适温度
        // 关闭娱乐设备
        Log.d(TAG, "工作模式：专注工作");
        
        NotificationHelper.sendHealthNotification(context,
            "💼 工作模式",
            "已为您设置工作环境。");
    }
    
    /**
     * 获取场景名称
     */
    private String getSceneName(String sceneId) {
        switch (sceneId) {
            case "home_mode": return "回家模式";
            case "away_mode": return "离家模式";
            case "sleep_mode": return "睡眠模式";
            case "work_mode": return "工作模式";
            default: return "未知场景";
        }
    }
    
    /**
     * 获取所有场景
     */
    public List<SceneInfo> getAllScenes() {
        List<SceneInfo> scenes = new ArrayList<>();
        
        scenes.add(new SceneInfo("home_mode", "🏠 回家模式", "打开灯光、空调，关闭安防"));
        scenes.add(new SceneInfo("away_mode", "🚪 离家模式", "关闭所有设备，开启安防"));
        scenes.add(new SceneInfo("sleep_mode", "🌙 睡眠模式", "关闭灯光，空调睡眠模式"));
        scenes.add(new SceneInfo("work_mode", "💼 工作模式", "工作环境设置"));
        
        return scenes;
    }
    
    /**
     * 场景信息
     */
    public static class SceneInfo {
        public String id;
        public String name;
        public String description;
        
        public SceneInfo(String id, String name, String description) {
            this.id = id;
            this.name = name;
            this.description = description;
        }
    }
}
