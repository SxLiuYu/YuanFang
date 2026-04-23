package com.openclaw.homeassistant;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import androidx.annotation.NonNull;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.IOException;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class OpenClawApiClient {

    private static final String TAG = "OpenClawApi";
    private static final int CONNECT_TIMEOUT = 15;
    private static final int READ_TIMEOUT = 120;

    private String baseUrl;
    private String apiKey;
    private OkHttpClient client;

    public interface ChatCallback {
        void onSuccess(String reply);
        void onError(String error);
    }

    public interface HealthCallback {
        void onSuccess(String status);
        void onError(String error);
    }

    public interface GetHistoryCallback {
        void onSuccess(JSONArray history);
        void onError(String error);
    }

    public interface WeatherCallback {
        void onSuccess(String weather);
        void onError(String error);
    }

    public interface VoiceCallback {
        void onSuccess(String text);
        void onError(String error);
    }

    public interface VoiceChatCallback {
        void onSuccess(String text, byte[] ttsAudio);
        void onError(String error);
    }

    public interface VideoChatCallback {
        void onSuccess(String text, byte[] ttsAudio);
        void onError(String error);
    }

    public OpenClawApiClient(Context context) {
        // 从 SharedPreferences 读取配置
        SharedPreferences prefs = context.getSharedPreferences("openclaw_config", Context.MODE_PRIVATE);
        this.baseUrl = prefs.getString("api_base_url", "http://192.168.1.3:8000");
        this.apiKey = prefs.getString("api_key", "");

        Log.d(TAG, "Initialized with baseUrl: " + baseUrl);

        client = new OkHttpClient.Builder()
                .connectTimeout(CONNECT_TIMEOUT, java.util.concurrent.TimeUnit.SECONDS)
                .readTimeout(READ_TIMEOUT, java.util.concurrent.TimeUnit.SECONDS)
                .build();
    }

    public void updateConfig(String newBaseUrl, String newApiKey) {
        this.baseUrl = newBaseUrl;
        this.apiKey = newApiKey;
        Log.d(TAG, "Config updated: " + baseUrl);
    }

    /**
     * 简单对话，不保存历史（向前兼容）
     */
    public void chat(String message, ChatCallback callback) {
        Log.d(TAG, "Sending chat: " + message);

        JSONObject json = new JSONObject();
        try {
            json.put("message", message);
        } catch (JSONException e) {
            callback.onError("JSON error: " + e.getMessage());
            return;
        }

        MediaType JSON = MediaType.parse("application/json; charset=utf-8");
        RequestBody body = RequestBody.create(json.toString(), JSON);
        Request request = new Request.Builder()
                .url(baseUrl + "/api/chat")
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
                    JSONObject result = new JSONObject(response.body().string());
                    String reply = result.getString("response");
                    callback.onSuccess(reply);
                } catch (Exception e) {
                    callback.onError("解析错误：" + e.getMessage());
                }
            }
        });
    }

    /**
     * 带对话历史的聊天
     */
    public void chatWithHistory(JSONArray history, ChatCallback callback) {
        Log.d(TAG, "Sending chat with history, messages: " + history.length());

        JSONObject json = new JSONObject();
        try {
            json.put("messages", history);
        } catch (JSONException e) {
            callback.onError("JSON error: " + e.getMessage());
            return;
        }

        MediaType JSON = MediaType.parse("application/json; charset=utf-8");
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
                    JSONObject result = new JSONObject(response.body().string());
                    String reply = result.getJSONArray("choices")
                            .getJSONObject(0)
                            .getJSONObject("message")
                            .getString("content");
                    callback.onSuccess(reply);
                } catch (Exception e) {
                    callback.onError("解析错误：" + e.getMessage());
                }
            }
        });
    }

    /**
     * 健康检查
     */
    public void health(HealthCallback callback) {
        Request request = new Request.Builder()
                .url(baseUrl + "/health")
                .addHeader("Authorization", "Bearer " + apiKey)
                .get()
                .build();

        client.newCall(request).enqueue(new Callback() {
            @Override
            public void onFailure(Call call, IOException e) {
                callback.onError("连接失败：" + e.getMessage());
            }

            @Override
            public void onResponse(Call call, Response response) throws IOException {
                if (response.isSuccessful()) {
                    callback.onSuccess(response.body().string());
                } else {
                    callback.onError("状态码：" + response.code());
                }
            }
        });
    }

    /**
     * 语音识别上传接口
     * 上传 WAV 音频文件，返回识别文本
     */
    public void speechToText(File audioFile, VoiceCallback callback) {
        MediaType MEDIA_TYPE_WAV = MediaType.parse("audio/wav");

        MultipartBody.Builder builder = new MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("audio", audioFile.getName(),
                        RequestBody.create(audioFile, MEDIA_TYPE_WAV));

        RequestBody requestBody = builder.build();
        Request request = new Request.Builder()
                .url(baseUrl + "/api/voice/stt")
                .addHeader("Authorization", "Bearer " + apiKey)
                .post(requestBody)
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
                    JSONObject result = new JSONObject(response.body().string());
                    String text = result.getString("text");
                    callback.onSuccess(text);
                } catch (Exception e) {
                    callback.onError("解析错误：" + e.getMessage());
                }
            }
        });
    }

    /**
     * 语音对话：上传语音，直接返回 TTS 音频（完整 pipeline: STT→LLM→TTS）
     */
    public void voiceChat(File audioFile, JSONArray history, VoiceChatCallback callback) {
        MediaType MEDIA_TYPE_WAV = MediaType.parse("audio/wav");

        MultipartBody.Builder builder = new MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("audio", audioFile.getName(),
                        RequestBody.create(audioFile, MEDIA_TYPE_WAV));

        RequestBody requestBody = builder.build();
        Request request = new Request.Builder()
                .url(baseUrl + "/api/voice/pipeline")
                .addHeader("Authorization", "Bearer " + apiKey)
                .post(requestBody)
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
                    // Response is JSON with base64 encoded audio
                    String bodyStr = response.body().string();
                    JSONObject result = new JSONObject(bodyStr);
                    String text = result.getString("text");
                    String audioBase64 = result.getString("audio_data");
                    byte[] ttsAudio = android.util.Base64.decode(audioBase64, android.util.Base64.DEFAULT);
                    callback.onSuccess(text, ttsAudio);
                } catch (Exception e) {
                    callback.onError("解析错误：" + e.getMessage());
                }
            }
        });
    }

    public void getWeather(WeatherCallback callback) {
        Request request = new Request.Builder()
                .url(baseUrl + "/api/weather")
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

    /**
     * 视频对话：上传语音音频 + 当前画面 JPEG，返回文字回答 + TTS 音频
     * 完整 pipeline: STT → VLM+LLM → TTS
     */
    public void videoChat(File audioFile, byte[] imageBytes, VideoChatCallback callback) {
        MediaType MEDIA_TYPE_WAV = MediaType.parse("audio/wav");
        MediaType MEDIA_TYPE_JPEG = MediaType.parse("image/jpeg");

        MultipartBody.Builder builder = new MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("audio", "audio.wav",
                        RequestBody.create(audioFile, MEDIA_TYPE_WAV))
                .addFormDataPart("image", "frame.jpg",
                        RequestBody.create(imageBytes, MEDIA_TYPE_JPEG));

        RequestBody requestBody = builder.build();
        Request request = new Request.Builder()
                .url(baseUrl + "/api/video/chat")
                .addHeader("Authorization", "Bearer " + apiKey)
                .post(requestBody)
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
                    // Response is JSON with text + base64 encoded TTS audio
                    String bodyStr = response.body().string();
                    JSONObject result = new JSONObject(bodyStr);
                    String text = result.getString("text");
                    String audioBase64 = result.getString("audio_data");
                    byte[] ttsAudio = android.util.Base64.decode(audioBase64, android.util.Base64.DEFAULT);
                    callback.onSuccess(text, ttsAudio);
                } catch (Exception e) {
                    callback.onError("解析错误：" + e.getMessage());
                }
            }
        });
    }
}