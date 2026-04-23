package com.openclaw.homeassistant;

import android.content.Context;
import android.text.TextUtils;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.IOException;
import java.util.concurrent.TimeUnit;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

/**
 * 统一的 AI 服务调用
 * 使用 SecureConfig 安全管理配置
 * 支持请求取消和统一错误处理
 */
public class DashScopeService {
    private static final String TAG = "DashScopeService";
    
    private final OkHttpClient client;
    private final SecureConfig secureConfig;
    private Call currentCall;
    
    private static final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    
    public DashScopeService(Context context) {
        this.secureConfig = SecureConfig.getInstance(context);
        this.client = new OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .build();
    }
    
    /**
     * 取消当前请求
     */
    public void cancelRequest() {
        if (currentCall != null && !currentCall.isCanceled()) {
            currentCall.cancel();
            Log.d(TAG, "请求已取消");
        }
    }
    
    /**
     * 处理查询 - 统一回调接口
     */
    public void processQuery(String query, ApiCallback<String> callback) {
        processViaOpenClaw(query, callback);
    }
    
    /**
     * 通过 OpenClaw 本地服务调用
     */
    private void processViaOpenClaw(String query, ApiCallback<String> callback) {
        String serverUrl = secureConfig.getServerUrl();
        String deviceToken = secureConfig.getDeviceToken();
        String apiKey = secureConfig.getApiKey();
        
        try {
            JSONObject requestBody = new JSONObject();
            requestBody.put("model", "qwen3.5-plus");
            
            JSONArray messages = new JSONArray();
            JSONObject systemMessage = new JSONObject();
            systemMessage.put("role", "system");
            systemMessage.put("content", "你是一个家庭助手，请理解用户的语音指令并提供相应的帮助。");
            messages.put(systemMessage);
            
            JSONObject userMessage = new JSONObject();
            userMessage.put("role", "user");
            userMessage.put("content", query);
            messages.put(userMessage);
            
            requestBody.put("messages", messages);
            
            String chatUrl = serverUrl.endsWith("/") ? serverUrl + "v1/chat/completions" : serverUrl + "/v1/chat/completions";
            Log.d(TAG, "请求 OpenClaw: " + chatUrl);
            
            Request.Builder requestBuilder = new Request.Builder()
                .url(chatUrl)
                .addHeader("Content-Type", "application/json")
                .post(RequestBody.create(requestBody.toString(), JSON));
            
            String authToken = !TextUtils.isEmpty(deviceToken) ? deviceToken : apiKey;
            if (!TextUtils.isEmpty(authToken)) {
                requestBuilder.addHeader("Authorization", "Bearer " + authToken);
            }
            
            currentCall = client.newCall(requestBuilder.build());
            
            currentCall.enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    if (call.isCanceled()) {
                        Log.d(TAG, "请求被取消");
                        return;
                    }
                    Log.e(TAG, "请求失败", e);
                    callback.onError(AppException.networkError(e));
                }
                
                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    handleResponse(response, callback);
                }
            });
        } catch (Exception e) {
            Log.e(TAG, "构建请求失败", e);
            callback.onError(AppException.unknown("构建请求失败: " + e.getMessage()));
        }
    }
    
    private void handleResponse(Response response, ApiCallback<String> callback) {
        try {
            String responseBody = response.body() != null ? response.body().string() : "";
            Log.d(TAG, "响应: " + responseBody.substring(0, Math.min(500, responseBody.length())));
            
            if (response.isSuccessful()) {
                JSONObject jsonResponse = new JSONObject(responseBody);
                JSONArray choices = jsonResponse.optJSONArray("choices");
                
                if (choices != null && choices.length() > 0) {
                    JSONObject choice = choices.getJSONObject(0);
                    JSONObject message = choice.getJSONObject("message");
                    String aiResponse = message.getString("content");
                    callback.onSuccess(aiResponse);
                } else {
                    callback.onError(AppException.parseError("服务器返回空响应"));
                }
            } else {
                String errorMsg = "服务器错误 (" + response.code() + ")";
                try {
                    JSONObject errorJson = new JSONObject(responseBody);
                    if (errorJson.has("error")) {
                        errorMsg += ": " + errorJson.optString("error");
                    }
                } catch (Exception ignored) {}
                
                if (response.code() == 401) {
                    callback.onError(AppException.authError());
                } else {
                    callback.onError(AppException.serverError(response.code()));
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "解析响应失败", e);
            callback.onError(AppException.parseError(e.getMessage()));
        } finally {
            if (response.body() != null) {
                response.body().close();
            }
        }
    }
    
    /**
     * 处理多轮对话 - 统一回调接口
     */
    public void processQueryWithMessages(JSONArray messages, ApiCallback<String> callback) {
        String serverUrl = secureConfig.getServerUrl();
        String deviceToken = secureConfig.getDeviceToken();
        String apiKey = secureConfig.getApiKey();
        
        try {
            JSONObject lastMessage = messages.getJSONObject(messages.length() - 1);
            String query = lastMessage.getString("content");
            
            JSONObject requestBody = new JSONObject();
            requestBody.put("message", query);
            requestBody.put("session", "homeassistant");
            requestBody.put("context", messages);
            
            String chatUrl = serverUrl.endsWith("/") ? serverUrl + "chat" : serverUrl + "/chat";
            
            Request.Builder requestBuilder = new Request.Builder()
                .url(chatUrl)
                .addHeader("Content-Type", "application/json")
                .post(RequestBody.create(requestBody.toString(), JSON));
            
            String authToken = !TextUtils.isEmpty(deviceToken) ? deviceToken : apiKey;
            if (!TextUtils.isEmpty(authToken)) {
                requestBuilder.addHeader("Authorization", "Bearer " + authToken);
            }
            
            currentCall = client.newCall(requestBuilder.build());
            
            currentCall.enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    if (call.isCanceled()) return;
                    callback.onError(AppException.networkError(e));
                }
                
                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    try {
                        String responseBody = response.body() != null ? response.body().string() : "";
                        if (response.isSuccessful()) {
                            JSONObject jsonResponse = new JSONObject(responseBody);
                            String aiResponse = jsonResponse.optString("reply", jsonResponse.toString());
                            callback.onSuccess(aiResponse);
                        } else {
                            callback.onError(AppException.serverError(response.code()));
                        }
                    } catch (Exception e) {
                        callback.onError(AppException.parseError(e.getMessage()));
                    } finally {
                        if (response.body() != null) {
                            response.body().close();
                        }
                    }
                }
            });
        } catch (Exception e) {
            callback.onError(AppException.unknown("构建请求失败: " + e.getMessage()));
        }
    }
    
    // ========== 兼容旧接口 ==========
    
    @Deprecated
    public interface ResponseCallback {
        void onSuccess(String response);
        void onError(String error);
    }
    
    @Deprecated
    public void processQuery(String query, ResponseCallback callback) {
        processQuery(query, new ApiCallback<String>() {
            @Override
            public void onSuccess(String result) {
                callback.onSuccess(result);
            }
            @Override
            public void onError(AppException error) {
                callback.onError(error.getUserMessage());
            }
        });
    }
    
    @Deprecated
    public interface SuccessCallback {
        void onSuccess(String response);
    }
    
    @Deprecated
    public interface ErrorCallback {
        void onError(String error);
    }
    
    @Deprecated
    public void processQueryWithMessages(JSONArray messages, 
                                         final SuccessCallback successCallback,
                                         final ErrorCallback errorCallback) {
        processQueryWithMessages(messages, new ApiCallback<String>() {
            @Override
            public void onSuccess(String result) {
                successCallback.onSuccess(result);
            }
            @Override
            public void onError(AppException error) {
                errorCallback.onError(error.getUserMessage());
            }
        });
    }
}