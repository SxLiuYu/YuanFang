package com.openclaw.homeassistant;

import android.content.Context;
import android.text.TextUtils;
import android.util.Log;
import java.io.IOException;
import okhttp3.*;
import org.json.JSONObject;
import org.json.JSONArray;

/**
 * OpenClaw API 客户端
 * 支持动态配置服务器地址和 API Key
 * 安全性：使用 SecureConfig 管理敏感信息
 */
public class OpenClawApiClient {
    
    private static final String TAG = "OpenClawClient";
    
    private String baseUrl;
    private String apiKey;
    private final SecureConfig secureConfig;
    
    private final OkHttpClient client;
    private final MediaType JSON = MediaType.get("application/json; charset=utf-8");
    
    /**
     * 推荐构造函数 - 使用安全配置
     */
    public OpenClawApiClient(Context context) {
        this.secureConfig = SecureConfig.getInstance(context);
        this.baseUrl = secureConfig.getChatServerUrl();
        this.apiKey = secureConfig.getApiKey();
        this.client = new OkHttpClient.Builder()
            .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
            .readTimeout(60, java.util.concurrent.TimeUnit.SECONDS)
            .writeTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
            .build();
    }
    
    /**
     * 自定义配置
     */
    public OpenClawApiClient(Context context, String baseUrl, String apiKey) {
        this.secureConfig = SecureConfig.getInstance(context);
        this.baseUrl = !TextUtils.isEmpty(baseUrl) ? baseUrl : secureConfig.getChatServerUrl();
        this.apiKey = !TextUtils.isEmpty(apiKey) ? apiKey : secureConfig.getApiKey();
        this.client = new OkHttpClient.Builder()
            .connectTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
            .readTimeout(60, java.util.concurrent.TimeUnit.SECONDS)
            .writeTimeout(30, java.util.concurrent.TimeUnit.SECONDS)
            .build();
    }
    
    /**
     * 更新配置
     */
    public void updateConfig(String newBaseUrl, String newApiKey) {
        if (!TextUtils.isEmpty(newBaseUrl)) {
            this.baseUrl = newBaseUrl;
        }
        if (!TextUtils.isEmpty(newApiKey)) {
            this.apiKey = newApiKey;
        }
    }
    
    /**
     * 刷新安全配置
     */
    public void refreshConfig() {
        this.baseUrl = secureConfig.getChatServerUrl();
        this.apiKey = secureConfig.getApiKey();
    }
    
    /**
     * 健康检查
     */
    public interface HealthCallback {
        void onSuccess(String message);
        void onError(String error);
    }
    
    public void health(HealthCallback callback) {
        Request request = new Request.Builder()
            .url(baseUrl + "/health")
            .addHeader("Authorization", "Bearer " + apiKey)
            .get()
            .build();
        
        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                callback.onError("网络错误：" + e.getMessage());
            }
            
            @Override
            public void onResponse(Call call, Response response) throws IOException {
                try {
                    String responseBody = response.body().string();
                    JSONObject result = new JSONObject(responseBody);
                    if ("ok".equals(result.getString("status"))) {
                        callback.onSuccess("服务器正常");
                    } else {
                        callback.onError("服务器异常");
                    }
                } catch (Exception e) {
                    callback.onError("解析错误：" + e.getMessage());
                }
            }
        });
    }
    
    /**
     * 单轮聊天对话
     */
    public interface ChatCallback {
        void onSuccess(String reply);
        void onError(String error);
    }

    public void chat(String message, ChatCallback callback) {
        JSONArray messages = new JSONArray();
        try {
            JSONObject userMsg = new JSONObject();
            userMsg.put("role", "user");
            userMsg.put("content", message);
            messages.put(userMsg);
        } catch (Exception e) {
            Log.e(TAG, "构建消息失败", e);
        }

        chatWithHistory(messages, callback);
    }

    /**
     * 多轮对话（带历史）
     */
    public void chatWithHistory(JSONArray messages, ChatCallback callback) {
        JSONObject json = new JSONObject();
        try {
            json.put("model", "qwen3.5-plus");
            json.put("messages", messages);
            json.put("temperature", 0.7);
            json.put("max_tokens", 1000);
        } catch (Exception e) {
            Log.e(TAG, "构建请求失败", e);
            callback.onError("构建请求失败：" + e.getMessage());
            return;
        }

        RequestBody body = RequestBody.create(json.toString(), JSON);
        Request request = new Request.Builder()
            .url(baseUrl + "/v1/chat/completions")
            .addHeader("Authorization", "Bearer " + apiKey)
            .addHeader("Content-Type", "application/json")
            .post(body)
            .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                callback.onError("网络错误：" + e.getMessage());
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                try {
                    String responseBody = response.body().string();
                    if (!response.isSuccessful()) {
                        callback.onError("服务器错误：" + response.code());
                        return;
                    }
                    JSONObject result = new JSONObject(responseBody);
                    JSONArray choices = result.getJSONArray("choices");
                    JSONObject choice = choices.getJSONObject(0);
                    JSONObject msg = choice.getJSONObject("message");
                    String reply = msg.getString("content");
                    callback.onSuccess(reply);
                } catch (Exception e) {
                    callback.onError("解析错误：" + e.getMessage());
                }
            }
        });
    }

    /**
     * 流式对话（用于打字效果）
     */
    public interface StreamCallback {
        void onToken(String token);
        void onComplete(String fullReply);
        void onError(String error);
    }

    public void chatStream(JSONArray messages, StreamCallback callback) {
        JSONObject json = new JSONObject();
        try {
            json.put("model", "qwen3.5-plus");
            json.put("messages", messages);
            json.put("stream", true);
            json.put("temperature", 0.7);
            json.put("max_tokens", 1000);
        } catch (Exception e) {
            Log.e(TAG, "构建请求失败", e);
            callback.onError("构建请求失败：" + e.getMessage());
            return;
        }

        RequestBody body = RequestBody.create(json.toString(), JSON);
        Request request = new Request.Builder()
            .url(baseUrl + "/v1/chat/completions")
            .addHeader("Authorization", "Bearer " + apiKey)
            .addHeader("Content-Type", "application/json")
            .post(body)
            .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                callback.onError("网络错误：" + e.getMessage());
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                try {
                    if (!response.isSuccessful()) {
                        callback.onError("服务器错误：" + response.code());
                        return;
                    }

                    StringBuilder fullReply = new StringBuilder();
                    okio.BufferedSource source = response.body().source();

                    while (!source.exhausted()) {
                        String line = source.readUtf8Line();
                        if (line != null && line.startsWith("data: ")) {
                            String data = line.substring(6);
                            if ("[DONE]".equals(data)) {
                                break;
                            }
                            JSONObject chunk = new JSONObject(data);
                            JSONArray choices = chunk.getJSONArray("choices");
                            if (choices.length() > 0) {
                                JSONObject delta = choices.getJSONObject(0).optJSONObject("delta");
                                if (delta != null && delta.has("content")) {
                                    String token = delta.getString("content");
                                    fullReply.append(token);
                                    callback.onToken(token);
                                }
                            }
                        }
                    }

                    callback.onComplete(fullReply.toString());
                } catch (Exception e) {
                    callback.onError("解析错误：" + e.getMessage());
                }
            }
        });
    }
    
    /**
     * 获取天气（异步）
     */
    public interface WeatherCallback {
        void onSuccess(String weather);
        void onError(String error);
    }
    
    public void getWeatherAsync(WeatherCallback callback) {
        Request request = new Request.Builder()
            .url(baseUrl + "/weather")
            .addHeader("Authorization", "Bearer " + apiKey)
            .get()
            .build();
        
        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                callback.onError("网络错误：" + e.getMessage());
            }
            
            @Override
            public void onResponse(Call call, Response response) throws IOException {
                try {
                    String weather = response.body().string();
                    callback.onSuccess(weather);
                } catch (Exception e) {
                    callback.onError("解析错误：" + e.getMessage());
                }
            }
        });
    }
}
