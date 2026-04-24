package com.openclaw.homeassistant;

import android.Manifest;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.provider.Settings;
import android.speech.RecognitionListener;
import android.speech.RecognizerIntent;
import android.speech.SpeechRecognizer;
import android.speech.tts.TextToSpeech;
import android.util.Log;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

import androidx.activity.result.ActivityResultLauncher;
import androidx.activity.result.contract.ActivityResultContracts;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.core.content.ContextCompat;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.Locale;

/**
 * OpenClaw 家庭助手 - 极简对话版
 * 功能：
 * 1. AI 对话（文字 + 语音）
 * 2. 按需请求授权获取设备数据
 * 3. 智能场景识别
 */
public class MainActivity extends AppCompatActivity {
    
    private static final String TAG = "MainActivity";
    
    // UI 组件
    private TextView tvConversation;
    private ScrollView scrollConversation;
    private EditText etInput;
    private Button btnSend;
    
    // 服务
    private SpeechRecognizer speechRecognizer;
    private TextToSpeech textToSpeech;
    private DashScopeService dashScopeService;
    private ConversationManager conversationManager;
    private QuickActions quickActions;
    
    // 状态
    private boolean isListening = false;
    private boolean isTTSReady = false;
    private boolean isTTSEnabled = true;
    
    // 权限请求器
    private final ActivityResultLauncher<String> permissionLauncher =
        registerForActivityResult(new ActivityResultContracts.RequestPermission(), isGranted -> {
            if (isGranted) {
                Toast.makeText(this, "✅ 权限已授予", Toast.LENGTH_SHORT).show();
                startListening();
            } else {
                showPermissionDeniedDialog();
            }
        });

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        initViews();
        initServices();
        setupListeners();
        
        // 检查设备认证状态
        checkDeviceAuthAndShowConfirm();
    }
    
    /**
     * 检查设备认证状态，未确认时打开确认界面
     */
    private void checkDeviceAuthAndShowConfirm() {
        try {
            OpenClawApplication app = OpenClawApplication.getInstance();
            if (app != null && !app.isDeviceConfirmed()) {
                Intent intent = new Intent(this, DeviceConfirmActivity.class);
                intent.setFlags(Intent.FLAG_ACTIVITY_NEW_TASK | Intent.FLAG_ACTIVITY_CLEAR_TOP);
                startActivity(intent);
            }
        } catch (Exception e) {
            Log.w(TAG, "检查认证状态失败", e);
        }
    }
    
    private void initViews() {
        tvConversation = findViewById(R.id.tvConversation);
        scrollConversation = findViewById(R.id.scrollConversation);
        etInput = findViewById(R.id.etInput);
        btnSend = findViewById(R.id.btnSend);
    }
    
    private void initServices() {
        conversationManager = new ConversationManager(this);
        dashScopeService = new DashScopeService(this);
        quickActions = new QuickActions(this);
        initTTS();
        setupSpeechRecognizer();
    }
    
    private void initTTS() {
        try {
            textToSpeech = new TextToSpeech(this, status -> {
                if (status == TextToSpeech.SUCCESS) {
                    int result = textToSpeech.setLanguage(Locale.CHINESE);
                    if (result == TextToSpeech.LANG_MISSING_DATA || 
                        result == TextToSpeech.LANG_NOT_SUPPORTED) {
                        textToSpeech.setLanguage(Locale.ENGLISH);
                        isTTSReady = true;
                    } else {
                        isTTSReady = true;
                    }
                }
            });
        } catch (Exception e) {
            Log.e(TAG, "TTS 初始化失败", e);
        }
    }
    
    private void setupSpeechRecognizer() {
        if (!SpeechRecognizer.isRecognitionAvailable(this)) {
            // 不支持语音识别，但不显示按钮
            return;
        }
        
        speechRecognizer = SpeechRecognizer.createSpeechRecognizer(this);
        speechRecognizer.setRecognitionListener(new RecognitionListener() {
            @Override
            public void onReadyForSpeech(Bundle params) {
                runOnUiThread(() -> appendSystem("🎤 正在听..."));
            }
            
            @Override
            public void onBeginningOfSpeech() {
                runOnUiThread(() -> appendSystem("👂 识别中..."));
            }
            
            @Override
            public void onEndOfSpeech() {
                runOnUiThread(() -> appendSystem("⏳ 处理中..."));
            }
            
            @Override
            public void onError(int error) {
                runOnUiThread(() -> {
                    appendSystem("❌ " + getErrorText(error));
                    isListening = false;
                });
                
                if (error == SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS) {
                    showPermissionDeniedDialog();
                }
            }
            
            @Override
            public void onResults(Bundle results) {
                ArrayList<String> matches = results.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION);
                if (matches != null && !matches.isEmpty()) {
                    String recognizedText = matches.get(0);
                    appendConversation("👤 你：" + recognizedText);
                    processWithAI(recognizedText);
                }
                runOnUiThread(() -> isListening = false);
            }
            
            @Override
            public void onPartialResults(Bundle partialResults) {}
            @Override
            public void onEvent(int eventType, Bundle params) {}
            @Override
            public void onRmsChanged(float rmsdB) {}
            @Override
            public void onBufferReceived(byte[] buffer) {}
        });
    }
    
    private void setupListeners() {
        // 发送按钮
        btnSend.setOnClickListener(v -> {
            String text = etInput.getText().toString().trim();
            if (!text.isEmpty()) {
                appendConversation("👤 你：" + text);
                processWithAI(text);
                etInput.setText("");
            }
        });
        
        // 输入框回车发送
        etInput.setOnEditorActionListener((v, actionId, event) -> {
            btnSend.performClick();
            return true;
        });
        
        // 长按发送按钮语音输入
        btnSend.setOnLongClickListener(v -> {
            if (isListening) {
                stopListening();
            } else {
                checkAndRequestPermission();
            }
            return true;
        });
    }
    
    /**
     * 处理 AI 对话，智能识别场景
     */
    private void processWithAI(String query) {
        appendSystem("⏳ 思考中...");
        
        // 1. 先识别意图，看是否需要执行快捷操作
        QuickActions.IntentMatch match = QuickActions.IntentRecognizer.match(query);
        
        if (match.isAction()) {
            // 执行快捷指令
            String result = quickActions.execute(match.intent, match.params);
            runOnUiThread(() -> {
                // 移除"思考中"提示
                String currentText = tvConversation.getText().toString();
                if (currentText.contains("⏳ 思考中...")) {
                    tvConversation.setText(currentText.replace("⏳ 思考中...\n\n", ""));
                }
                
                appendConversation("🤖 AI：" + result);
                
                // 保存到上下文
                try {
                    conversationManager.addMessage("user", query);
                    conversationManager.addMessage("assistant", result);
                } catch (Exception e) {
                    Log.w(TAG, "保存对话失败", e);
                }
                
                // TTS 朗读
                if (isTTSEnabled && isTTSReady) {
                    speak(result);
                }
            });
        } else {
            // 2. 普通对话，交给 AI 处理
            processChat(query);
        }
    }
    
    /**
     * 处理普通对话
     */
    private void processChat(String query) {
        // 构建系统提示词，增强场景理解
        String systemPrompt = buildSystemPrompt(query);
        
        JSONArray messages = new JSONArray();
        try {
            JSONObject systemMsg = new JSONObject();
            systemMsg.put("role", "system");
            systemMsg.put("content", systemPrompt);
            messages.put(systemMsg);
            
            // 添加历史上下文（最近 5 条）
            JSONArray history = conversationManager.getRecentMessages(5);
            for (int i = 0; i < history.length(); i++) {
                messages.put(history.getJSONObject(i));
            }
            
            // 当前查询
            JSONObject userMsg = new JSONObject();
            userMsg.put("role", "user");
            userMsg.put("content", query);
            messages.put(userMsg);
        } catch (Exception e) {
            Log.e(TAG, "构建消息失败", e);
        }
        
        dashScopeService.processQueryWithMessages(messages, response -> {
            runOnUiThread(() -> {
                // 移除"思考中"提示
                String currentText = tvConversation.getText().toString();
                if (currentText.contains("⏳ 思考中...")) {
                    tvConversation.setText(currentText.replace("⏳ 思考中...\n\n", ""));
                }
                
                appendConversation("🤖 AI：" + response);
                
                // 保存到上下文
                try {
                    conversationManager.addMessage("user", query);
                    conversationManager.addMessage("assistant", response);
                } catch (Exception e) {
                    Log.w(TAG, "保存对话失败", e);
                }
                
                // TTS 朗读
                if (isTTSEnabled && isTTSReady) {
                    speak(response);
                }
            });
        }, error -> {
            runOnUiThread(() -> {
                appendSystem("❌ 错误：" + error);
            });
        });
    }
    
    /**
     * 构建系统提示词，增强场景理解
     */
    private String buildSystemPrompt(String query) {
        StringBuilder prompt = new StringBuilder();
        prompt.append("你是一个专业、温暖的家庭助手。\n\n");
        prompt.append("【核心能力】\n");
        prompt.append("1. 日常聊天：陪用户聊天解闷，语气温和有趣\n");
        prompt.append("2. 信息查询：天气、资讯、百科知识等\n");
        prompt.append("3. 生活助手：提醒、建议、规划\n");
        prompt.append("4. 情感陪伴：倾听、安慰、鼓励\n");
        prompt.append("5. 学习助手：解答问题、提供思路\n\n");
        prompt.append("【回答原则】\n");
        prompt.append("- 简洁明了，避免冗长\n");
        prompt.append("- 语气亲切，像朋友聊天\n");
        prompt.append("- 不确定时诚实告知\n");
        prompt.append("- 涉及隐私时先请求授权\n\n");
        prompt.append("【当前时间】");
        prompt.append(java.time.LocalDateTime.now().toString());
        prompt.append("\n\n请根据用户的问题，提供有帮助的回答。");
        
        return prompt.toString();
    }
    
    private void appendConversation(String text) {
        tvConversation.append(text + "\n\n");
        scrollToBottom();
    }
    
    private void appendSystem(String text) {
        tvConversation.append("💬 " + text + "\n\n");
        scrollToBottom();
    }
    
    private void scrollToBottom() {
        scrollConversation.post(() -> {
            scrollConversation.fullScroll(View.FOCUS_DOWN);
        });
    }
    
    private void speak(String text) {
        if (!isTTSEnabled || !isTTSReady) return;
        textToSpeech.speak(text, TextToSpeech.QUEUE_FLUSH, null, null);
    }
    
    private void startListening() {
        if (speechRecognizer == null) return;
        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, "zh-CN");
        intent.putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true);
        speechRecognizer.startListening(intent);
        isListening = true;
        appendSystem("🎤 正在听...");
    }
    
    private void stopListening() {
        if (speechRecognizer == null) return;
        speechRecognizer.stopListening();
        isListening = false;
    }
    
    private void checkAndRequestPermission() {
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO) 
            == PackageManager.PERMISSION_GRANTED) {
            startListening();
        } else {
            permissionLauncher.launch(Manifest.permission.RECORD_AUDIO);
        }
    }
    
    private void showPermissionDeniedDialog() {
        new AlertDialog.Builder(this)
            .setTitle("需要录音权限")
            .setMessage("语音功能需要录音权限。请在设置中开启。")
            .setPositiveButton("去设置", (dialog, which) -> {
                Intent intent = new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS);
                intent.setData(Uri.fromParts("package", getPackageName(), null));
                startActivity(intent);
            })
            .setNegativeButton("取消", null)
            .show();
    }
    
    private String getErrorText(int errorCode) {
        switch (errorCode) {
            case SpeechRecognizer.ERROR_AUDIO: return "录音失败";
            case SpeechRecognizer.ERROR_CLIENT: return "客户端错误";
            case SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS: return "权限不足";
            case SpeechRecognizer.ERROR_NETWORK: return "网络错误";
            case SpeechRecognizer.ERROR_NETWORK_TIMEOUT: return "网络超时";
            case SpeechRecognizer.ERROR_NO_MATCH: return "未识别到语音";
            case SpeechRecognizer.ERROR_RECOGNIZER_BUSY: return "服务忙";
            case SpeechRecognizer.ERROR_SERVER: return "服务器错误";
            case SpeechRecognizer.ERROR_SPEECH_TIMEOUT: return "说话超时";
            default: return "未知错误";
        }
    }
    
    @Override
    protected void onDestroy() {
        if (speechRecognizer != null) {
            speechRecognizer.destroy();
        }
        if (textToSpeech != null) {
            textToSpeech.stop();
            textToSpeech.shutdown();
        }
        super.onDestroy();
    }
}
