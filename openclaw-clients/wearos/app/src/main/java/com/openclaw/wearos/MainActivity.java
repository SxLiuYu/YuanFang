package com.openclaw.wearos;

import android.Manifest;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.view.View;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.IOException;
import java.util.ArrayList;
import java.util.Locale;

import okhttp3.Call;
import okhttp3.Callback;
import okhttp3.MediaType;
import okhttp3.OkHttpClient;
import okhttp3.Request;
import okhttp3.RequestBody;
import okhttp3.Response;

public class MainActivity extends AppCompatActivity {
    
    private static final String PREF_API_KEY = "dashscope_api_key";
    private static final String DEFAULT_API_KEY = "";
    
    private TextView tvStatus;
    private TextView tvResponse;
    private Button btnVoice;
    
    private SpeechRecognizer speechRecognizer;
    private OkHttpClient httpClient;
    private Handler mainHandler;
    private boolean isListening = false;
    
    private final ActivityResultLauncher<String> permissionLauncher =
        registerForActivityResult(new ActivityResultContracts.RequestPermission(), isGranted -> {
            if (isGranted) {
                startListening();
            } else {
                Toast.makeText(this, "需要麦克风权限", Toast.LENGTH_SHORT).show();
            }
        });

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        tvStatus = findViewById(R.id.tvStatus);
        tvResponse = findViewById(R.id.tvResponse);
        btnVoice = findViewById(R.id.btnVoice);
        
        httpClient = new OkHttpClient();
        mainHandler = new Handler(Looper.getMainLooper());
        
        setupSpeechRecognizer();
        setupListeners();
        
        tvResponse.setText("你好！\n点击麦克风\n对我说话");
    }
    
    private void setupSpeechRecognizer() {
        if (SpeechRecognizer.isRecognitionAvailable(this)) {
            speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this);
            speechRecognizer.setRecognitionListener(new RecognitionListener() {
                @Override
                public void onReadyForSpeech(Bundle params) {
                    updateStatus("正在听...");
                }

                @Override
                public void onBeginningOfSpeech() {}

                @Override
                public void onRmsChanged(float rmsdB) {}

                @Override
                public void onBufferReceived(byte[] buffer) {}

                @Override
                public void onEndOfSpeech() {
                    isListening = false;
                    updateStatus("处理中...");
                }

                @Override
                public void onError(int error) {
                    isListening = false;
                    updateStatus("点击说话");
                    String errorText = getErrorText(error);
                    mainHandler.post(() -> Toast.makeText(MainActivity.this, errorText, Toast.LENGTH_SHORT).show());
                }

                @Override
                public void onResults(Bundle results) {
                    ArrayList<String> matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                    if (matches != null && !matches.isEmpty()) {
                        String text = matches.get(0);
                        sendToAI(text);
                    }
                    isListening = false;
                    updateStatus("点击说话");
                }

                @Override
                public void onPartialResults(Bundle partialResults) {}

                @Override
                public void onEvent(int eventType, Bundle params) {}
            });
        }
    }
    
    private void setupListeners() {
        btnVoice.setOnClickListener(v -> {
            if (isListening) {
                stopListening();
            } else {
                checkPermissionAndStart();
            }
        });
    }
    
    private void checkPermissionAndStart() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                == PackageManager.PERMISSION_GRANTED) {
            startListening();
        } else {
            permissionLauncher.launch(Manifest.permission.RECORD_AUDIO);
        }
    }
    
    private void startListening() {
        if (speechRecognizer != null) {
            Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
            intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.CHINESE);
            intent.putExtra(RecognizerIntent.EXTRA_MAX_RESULTS, 1);
            
            try {
                speechRecognizer.startListening(intent);
                isListening = true;
                btnVoice.setText("⏹️");
            } catch (Exception e) {
                Toast.makeText(this, "语音识别启动失败", Toast.LENGTH_SHORT).show();
            }
        }
    }
    
    private void stopListening() {
        if (speechRecognizer != null) {
            speechRecognizer.stopListening();
            isListening = false;
            btnVoice.setText("🎤");
            updateStatus("点击说话");
        }
    }
    
    private void sendToAI(String text) {
        updateStatus("思考中...");
        
        String apiKey = getSharedPreferences("prefs", MODE_PRIVATE)
            .getString(PREF_API_KEY, DEFAULT_API_KEY);
        
        if (apiKey.isEmpty()) {
            tvResponse.setText("请先配置\nAPI 密钥");
            updateStatus("点击说话");
            return;
        }
        
        try {
            JSONObject requestBody = new JSONObject();
            requestBody.put("model", "qwen-max");
            
            JSONObject input = new JSONObject();
            JSONArray messages = new JSONArray();
            
            JSONObject systemMsg = new JSONObject();
            systemMsg.put("role", "system");
            systemMsg.put("content", "你是一个智能手表助手，请简洁回答。");
            messages.put(systemMsg);
            
            JSONObject userMsg = new JSONObject();
            userMsg.put("role", "user");
            userMsg.put("content", text);
            messages.put(userMsg);
            
            input.put("messages", messages);
            requestBody.put("input", input);
            
            JSONObject params = new JSONObject();
            params.put("temperature", 0.7);
            params.put("max_tokens", 200);
            requestBody.put("parameters", params);
            
            Request request = new Request.Builder()
                .url("https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation")
                .addHeader("Authorization", "Bearer " + apiKey)
                .addHeader("Content-Type", "application/json")
                .post(RequestBody.create(
                    requestBody.toString(),
                    MediaType.parse("application/json")
                ))
                .build();
            
            httpClient.newCall(request).enqueue(new Callback() {
                @Override
                public void onFailure(Call call, IOException e) {
                    mainHandler.post(() -> {
                        tvResponse.setText("请求失败\n" + e.getMessage());
                        updateStatus("点击说话");
                    });
                }

                @Override
                public void onResponse(Call call, Response response) throws IOException {
                    try {
                        String responseBody = response.body().string();
                        if (response.isSuccessful()) {
                            JSONObject jsonResponse = new JSONObject(responseBody);
                            String content = jsonResponse
                                .getJSONObject("output")
                                .getJSONArray("choices")
                                .getJSONObject(0)
                                .getString("message")
                                .getString("content");
                            
                            mainHandler.post(() -> {
                                tvResponse.setText(content);
                                updateStatus("点击说话");
                            });
                        } else {
                            mainHandler.post(() -> {
                                tvResponse.setText("API 错误\n" + response.code());
                                updateStatus("点击说话");
                            });
                        }
                    } catch (Exception e) {
                        mainHandler.post(() -> {
                            tvResponse.setText("解析失败\n" + e.getMessage());
                            updateStatus("点击说话");
                        });
                    }
                }
            });
        } catch (Exception e) {
            tvResponse.setText("请求构建失败");
            updateStatus("点击说话");
        }
    }
    
    private void updateStatus(String status) {
        mainHandler.post(() -> tvStatus.setText(status));
    }
    
    private String getErrorText(int errorCode) {
        switch (errorCode) {
            case SpeechRecognizer.ERROR_AUDIO_RECORDING: return "录音错误";
            case SpeechRecognizer.ERROR_CLIENT: return "客户端错误";
            case SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS: return "权限不足";
            case SpeechRecognizer.ERROR_NETWORK: return "网络错误";
            case SpeechRecognizer.ERROR_NETWORK_TIMEOUT: return "网络超时";
            case SpeechRecognizer.ERROR_NO_MATCH: return "无法识别";
            case SpeechRecognizer.ERROR_RECOGNIZER_BUSY: return "识别器忙碌";
            case SpeechRecognizer.ERROR_SERVER: return "服务器错误";
            case SpeechRecognizer.ERROR_SPEECH_TIMEOUT: return "语音超时";
            default: return "未知错误";
        }
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (speechRecognizer != null) {
            speechRecognizer.destroy();
        }
    }
}
