package com.openclaw.homeassistant;

/**
 * 统一的 API 回调接口
 * 替代多个重复的回调接口定义
 */
public interface ApiCallback<T> {
    
    void onSuccess(T result);
    
    void onError(AppException error);
    
    default void onProgress(String status) {}
    
    default void onComplete() {}
}