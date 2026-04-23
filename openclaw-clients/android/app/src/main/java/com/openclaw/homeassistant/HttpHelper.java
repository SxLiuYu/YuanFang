package com.openclaw.homeassistant;

import android.util.Log;

import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.HttpURLConnection;
import java.net.URL;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * HTTP 工具类
 * 统一管理 HTTP 请求，减少重复代码
 */
public class HttpHelper {
    
    private static final String TAG = "HttpHelper";
    private static final int DEFAULT_TIMEOUT = 10000;
    private static final ExecutorService executor = Executors.newCachedThreadPool();
    
    public interface ResponseCallback {
        void onSuccess(String response);
        void onError(String error);
    }
    
    public interface JsonCallback {
        void onSuccess(JSONObject response);
        void onError(String error);
    }
    
    public static class RequestBuilder {
        private String url;
        private String method = "GET";
        private String body;
        private Map<String, String> headers = new HashMap<>();
        private int timeout = DEFAULT_TIMEOUT;
        
        public RequestBuilder url(String url) {
            this.url = url;
            return this;
        }
        
        public RequestBuilder method(String method) {
            this.method = method;
            return this;
        }
        
        public RequestBuilder body(String body) {
            this.body = body;
            return this;
        }
        
        public RequestBuilder header(String key, String value) {
            this.headers.put(key, value);
            return this;
        }
        
        public RequestBuilder authorization(String token) {
            return header("Authorization", "Bearer " + token);
        }
        
        public RequestBuilder contentType(String contentType) {
            return header("Content-Type", contentType);
        }
        
        public RequestBuilder timeout(int timeout) {
            this.timeout = timeout;
            return this;
        }
        
        public String execute() throws Exception {
            return HttpHelper.execute(this);
        }
        
        public void executeAsync(ResponseCallback callback) {
            HttpHelper.executeAsync(this, callback);
        }
        
        public void executeJsonAsync(JsonCallback callback) {
            HttpHelper.executeJsonAsync(this, callback);
        }
    }
    
    public static RequestBuilder builder() {
        return new RequestBuilder();
    }
    
    /**
     * 异步 GET 请求
     */
    public static void get(String url, ResponseCallback callback) {
        executor.execute(() -> {
            try {
                String response = doGet(url);
                callback.onSuccess(response);
            } catch (Exception e) {
                Log.e(TAG, "GET 请求失败: " + url, e);
                callback.onError(e.getMessage());
            }
        });
    }
    
    /**
     * 异步 GET 请求（返回 JSON）
     */
    public static void getJson(String url, JsonCallback callback) {
        executor.execute(() -> {
            try {
                String response = doGet(url);
                callback.onSuccess(new JSONObject(response));
            } catch (Exception e) {
                Log.e(TAG, "GET 请求失败: " + url, e);
                callback.onError(e.getMessage());
            }
        });
    }
    
    /**
     * 异步 POST 请求
     */
    public static void post(String url, String body, ResponseCallback callback) {
        executor.execute(() -> {
            try {
                String response = doPost(url, body);
                callback.onSuccess(response);
            } catch (Exception e) {
                Log.e(TAG, "POST 请求失败: " + url, e);
                callback.onError(e.getMessage());
            }
        });
    }
    
    /**
     * 异步 POST 请求（返回 JSON）
     */
    public static void postJson(String url, JSONObject data, JsonCallback callback) {
        executor.execute(() -> {
            try {
                String response = doPost(url, data.toString());
                callback.onSuccess(new JSONObject(response));
            } catch (Exception e) {
                Log.e(TAG, "POST 请求失败: " + url, e);
                callback.onError(e.getMessage());
            }
        });
    }
    
    /**
     * 同步 GET 请求
     */
    public static String doGet(String url) throws Exception {
        HttpURLConnection conn = null;
        try {
            conn = (HttpURLConnection) new URL(url).openConnection();
            conn.setRequestMethod("GET");
            conn.setConnectTimeout(DEFAULT_TIMEOUT);
            conn.setReadTimeout(DEFAULT_TIMEOUT);
            
            int responseCode = conn.getResponseCode();
            if (responseCode != 200) {
                throw new Exception("HTTP " + responseCode);
            }
            
            return readResponse(conn.getInputStream());
        } finally {
            if (conn != null) {
                conn.disconnect();
            }
        }
    }
    
    /**
     * 同步 POST 请求
     */
    public static String doPost(String url, String body) throws Exception {
        HttpURLConnection conn = null;
        try {
            conn = (HttpURLConnection) new URL(url).openConnection();
            conn.setRequestMethod("POST");
            conn.setConnectTimeout(DEFAULT_TIMEOUT);
            conn.setReadTimeout(DEFAULT_TIMEOUT);
            conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
            conn.setDoOutput(true);
            
            try (OutputStream os = conn.getOutputStream()) {
                os.write(body.getBytes(StandardCharsets.UTF_8));
            }
            
            int responseCode = conn.getResponseCode();
            if (responseCode != 200) {
                throw new Exception("HTTP " + responseCode);
            }
            
            return readResponse(conn.getInputStream());
        } finally {
            if (conn != null) {
                conn.disconnect();
            }
        }
    }
    
    /**
     * 读取响应
     */
    private static String readResponse(InputStream is) throws Exception {
        BufferedReader reader = new BufferedReader(new InputStreamReader(is, StandardCharsets.UTF_8));
        StringBuilder sb = new StringBuilder();
        String line;
        while ((line = reader.readLine()) != null) {
            sb.append(line);
        }
        reader.close();
        return sb.toString();
    }
    
    /**
     * 关闭线程池
     */
    public static void shutdown() {
        executor.shutdown();
    }
    
    /**
     * 执行请求（内部方法）
     */
    private static String execute(RequestBuilder builder) throws Exception {
        HttpURLConnection conn = null;
        try {
            conn = (HttpURLConnection) new URL(builder.url).openConnection();
            conn.setRequestMethod(builder.method);
            conn.setConnectTimeout(builder.timeout);
            conn.setReadTimeout(builder.timeout);
            
            // 设置请求头
            for (Map.Entry<String, String> header : builder.headers.entrySet()) {
                conn.setRequestProperty(header.getKey(), header.getValue());
            }
            
            // POST/PUT 请求体
            if (builder.body != null && ("POST".equals(builder.method) || "PUT".equals(builder.method))) {
                conn.setDoOutput(true);
                if (!builder.headers.containsKey("Content-Type")) {
                    conn.setRequestProperty("Content-Type", "application/json; charset=UTF-8");
                }
                try (OutputStream os = conn.getOutputStream()) {
                    os.write(builder.body.getBytes(StandardCharsets.UTF_8));
                }
            }
            
            int responseCode = conn.getResponseCode();
            if (responseCode < 200 || responseCode >= 300) {
                throw new Exception("HTTP " + responseCode);
            }
            
            return readResponse(conn.getInputStream());
        } finally {
            if (conn != null) {
                conn.disconnect();
            }
        }
    }
    
    /**
     * 异步执行请求
     */
    private static void executeAsync(RequestBuilder builder, ResponseCallback callback) {
        executor.execute(() -> {
            try {
                String response = execute(builder);
                callback.onSuccess(response);
            } catch (Exception e) {
                Log.e(TAG, "请求失败: " + builder.url, e);
                callback.onError(e.getMessage());
            }
        });
    }
    
    /**
     * 异步执行请求（返回 JSON）
     */
    private static void executeJsonAsync(RequestBuilder builder, JsonCallback callback) {
        executor.execute(() -> {
            try {
                String response = execute(builder);
                callback.onSuccess(new JSONObject(response));
            } catch (Exception e) {
                Log.e(TAG, "请求失败: " + builder.url, e);
                callback.onError(e.getMessage());
            }
        });
    }
}