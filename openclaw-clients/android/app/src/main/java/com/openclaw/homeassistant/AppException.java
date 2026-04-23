package com.openclaw.homeassistant;

/**
 * 应用自定义异常
 * 统一错误码定义和用户友好提示
 */
public class AppException extends Exception {
    
    public static final int CODE_NETWORK_ERROR = 1001;
    public static final int CODE_SERVER_ERROR = 1002;
    public static final int CODE_PARSE_ERROR = 1003;
    public static final int CODE_TIMEOUT = 1004;
    public static final int CODE_AUTH_ERROR = 1005;
    public static final int CODE_PERMISSION_DENIED = 1006;
    public static final int CODE_UNKNOWN = 1999;
    
    private final int code;
    private final String userMessage;
    
    public AppException(int code, String message) {
        super(message);
        this.code = code;
        this.userMessage = getUserFriendlyMessage(code, message);
    }
    
    public AppException(int code, String message, Throwable cause) {
        super(message, cause);
        this.code = code;
        this.userMessage = getUserFriendlyMessage(code, message);
    }
    
    public int getCode() {
        return code;
    }
    
    public String getUserMessage() {
        return userMessage;
    }
    
    private String getUserFriendlyMessage(int code, String technicalMessage) {
        switch (code) {
            case CODE_NETWORK_ERROR:
                return "网络连接失败，请检查网络设置";
            case CODE_SERVER_ERROR:
                return "服务器暂时无法响应，请稍后重试";
            case CODE_PARSE_ERROR:
                return "数据解析失败";
            case CODE_TIMEOUT:
                return "请求超时，请检查网络连接";
            case CODE_AUTH_ERROR:
                return "认证失败，请重新登录";
            case CODE_PERMISSION_DENIED:
                return "权限不足，请在设置中开启相关权限";
            default:
                return technicalMessage != null ? technicalMessage : "操作失败";
        }
    }
    
    public static AppException networkError(String message) {
        return new AppException(CODE_NETWORK_ERROR, message);
    }
    
    public static AppException networkError(Throwable cause) {
        return new AppException(CODE_NETWORK_ERROR, cause.getMessage(), cause);
    }
    
    public static AppException serverError(int statusCode) {
        return new AppException(CODE_SERVER_ERROR, "服务器错误: " + statusCode);
    }
    
    public static AppException parseError(String message) {
        return new AppException(CODE_PARSE_ERROR, message);
    }
    
    public static AppException timeout() {
        return new AppException(CODE_TIMEOUT, "请求超时");
    }
    
    public static AppException authError() {
        return new AppException(CODE_AUTH_ERROR, "认证失败");
    }
    
    public static AppException unknown(String message) {
        return new AppException(CODE_UNKNOWN, message);
    }
}