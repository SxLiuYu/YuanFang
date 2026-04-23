package com.openclaw.homeassistant;

import android.content.Context;
import android.util.Log;
import android.widget.Toast;

/**
 * 统一错误处理类
 */
public class ErrorHandler {
    
    private static final String TAG = "ErrorHandler";
    
    public enum ErrorCode {
        NETWORK_ERROR("网络连接失败"),
        SERVER_ERROR("服务器错误"),
        AUTH_ERROR("认证失败"),
        NOT_FOUND("资源不存在"),
        INVALID_INPUT("输入无效"),
        TIMEOUT("请求超时"),
        UNKNOWN("未知错误");
        
        private final String message;
        
        ErrorCode(String message) {
            this.message = message;
        }
        
        public String getMessage() {
            return message;
        }
    }
    
    public static class AppException extends Exception {
        private final ErrorCode code;
        private final String detailMessage;
        
        public AppException(ErrorCode code, String detailMessage) {
            super(detailMessage);
            this.code = code;
            this.detailMessage = detailMessage;
        }
        
        public AppException(ErrorCode code, String detailMessage, Throwable cause) {
            super(detailMessage, cause);
            this.code = code;
            this.detailMessage = detailMessage;
        }
        
        public ErrorCode getCode() {
            return code;
        }
        
        public String getUserMessage() {
            return code.getMessage() + (detailMessage != null ? ": " + detailMessage : "");
        }
    }
    
    /**
     * 处理异常
     */
    public static void handle(Context context, Exception e) {
        handle(context, e, true);
    }
    
    /**
     * 处理异常
     * @param context 上下文
     * @param e 异常
     * @param showToast 是否显示 Toast
     */
    public static void handle(Context context, Exception e, boolean showToast) {
        String message;
        
        if (e instanceof AppException) {
            AppException ae = (AppException) e;
            message = ae.getUserMessage();
            Log.e(TAG, "AppException [" + ae.getCode() + "]: " + ae.getMessage(), e);
        } else {
            message = "操作失败: " + e.getMessage();
            Log.e(TAG, "Unexpected error: " + e.getMessage(), e);
        }
        
        if (showToast && context != null) {
            Toast.makeText(context, message, Toast.LENGTH_SHORT).show();
        }
    }
    
    /**
     * 从 HTTP 状态码创建异常
     */
    public static AppException fromHttpCode(int code, String message) {
        if (code >= 500) {
            return new AppException(ErrorCode.SERVER_ERROR, message);
        } else if (code == 401 || code == 403) {
            return new AppException(ErrorCode.AUTH_ERROR, message);
        } else if (code == 404) {
            return new AppException(ErrorCode.NOT_FOUND, message);
        } else if (code >= 400) {
            return new AppException(ErrorCode.INVALID_INPUT, message);
        }
        return new AppException(ErrorCode.UNKNOWN, message);
    }
}