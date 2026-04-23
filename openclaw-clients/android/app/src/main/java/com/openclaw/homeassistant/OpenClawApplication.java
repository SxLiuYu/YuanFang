package com.openclaw.homeassistant;

import android.app.Application;
import android.content.Context;
import android.util.Log;

/**
 * OpenClaw 应用主类
 * 初始化并管理所有服务
 */
public class OpenClawApplication extends Application {
    
    private static final String TAG = "OpenClawApp";
    
    // 服务实例
    private DeviceAuthService authService;
    private TaskService taskService;
    private DeviceDataService deviceDataService;
    
    // 单例
    private static OpenClawApplication instance;
    
    public static OpenClawApplication getInstance() {
        return instance;
    }
    
    @Override
    public void onCreate() {
        super.onCreate();
        instance = this;
        
        Log.d(TAG, "OpenClaw 应用启动");
        
        // 1. 初始化设备认证服务
        initAuthService();
        
        // 2. 初始化任务服务（依赖认证）
        initTaskService();
        
        // 3. 初始化设备数据服务
        initDeviceDataService();
        
        Log.d(TAG, "所有服务初始化完成");
    }
    
    /**
     * 初始化设备认证服务
     */
    private void initAuthService() {
        authService = new DeviceAuthService(this);
        authService.setListener(new DeviceAuthService.AuthListener() {
            @Override
            public void onAuthSuccess(String token) {
                Log.d(TAG, "设备认证成功，token: " + token.substring(0, 8) + "...");
                // 认证成功后启动其他服务
                startAllServices();
            }
            
            @Override
            public void onAuthPending(String tempId) {
                Log.d(TAG, "等待用户确认，temp_id: " + tempId);
                // 可以在这里发送本地通知提醒用户
                NotificationHelper.showAuthNotification(
                    OpenClawApplication.this,
                    tempId,
                    "请查看飞书消息并输入确认码完成设备登录"
                );
            }
            
            @Override
            public void onAuthFailed(String error) {
                Log.e(TAG, "设备认证失败：" + error);
                // 1 分钟后重试
                authService.registerOrLogin();
            }
        });
        
        // 启动认证
        authService.registerOrLogin();
    }
    
    /**
     * 初始化任务服务
     */
    private void initTaskService() {
        taskService = new TaskService(this);
        taskService.setListener(new TaskService.TaskListener() {
            @Override
            public void onTaskCompleted(String taskName, String memberName, int points) {
                Log.d(TAG, "任务完成：" + taskName + " - " + memberName + " 获得 " + points + " 分");
            }
            
            @Override
            public void onPointsUpdated(String memberName, int totalPoints) {
                Log.d(TAG, "积分更新：" + memberName + " - " + totalPoints + " 分");
            }
        });
    }
    
    /**
     * 初始化设备数据服务
     */
    private void initDeviceDataService() {
        deviceDataService = new DeviceDataService(this);
    }
    
    /**
     * 启动所有服务
     */
    private void startAllServices() {
        // 启动任务服务（每 5 分钟拉取任务）
        if (taskService != null && !taskService.isRunning()) {
            taskService.start();
            Log.d(TAG, "任务服务已启动");
        }
        
        // 启动设备数据服务（每 30 分钟上传数据）
        if (deviceDataService != null && !deviceDataService.isRunning()) {
            deviceDataService.start();
            Log.d(TAG, "设备数据服务已启动");
        }
    }
    
    /**
     * 获取设备认证服务
     */
    public DeviceAuthService getAuthService() {
        return authService;
    }
    
    /**
     * 获取任务服务
     */
    public TaskService getTaskService() {
        return taskService;
    }
    
    /**
     * 获取设备数据服务
     */
    public DeviceDataService getDeviceDataService() {
        return deviceDataService;
    }
    
    /**
     * 检查设备是否已认证
     */
    public boolean isDeviceConfirmed() {
        return authService != null && authService.isConfirmed();
    }
    
    /**
     * 获取设备令牌
     */
    public String getDeviceToken() {
        return authService != null ? authService.getToken() : null;
    }
    
    /**
     * 重新认证设备
     */
    public void reAuthenticate() {
        if (authService != null) {
            authService.registerOrLogin();
        }
    }
    
    /**
     * 退出登录
     */
    public void logout() {
        // 停止所有服务
        if (taskService != null) {
            taskService.stop();
        }
        if (deviceDataService != null) {
            deviceDataService.stop();
        }
        
        // 清除认证信息
        if (authService != null) {
            authService.logout();
        }
        
        Log.d(TAG, "已退出登录");
        
        // 重新认证
        reAuthenticate();
    }
    
    @Override
    public void onTerminate() {
        super.onTerminate();
        
        // 清理服务
        if (taskService != null) {
            taskService.stop();
        }
        if (deviceDataService != null) {
            deviceDataService.stop();
        }
        
        Log.d(TAG, "应用已终止");
    }
}
