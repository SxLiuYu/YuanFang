package com.openclaw.homeassistant;

import android.Manifest;
import android.content.pm.PackageManager;
import android.util.Log;

import android.os.Bundle;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.ImageButton;
import android.widget.Toast;

import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;

import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.ScrollView;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.File;
import java.util.List;

/**
 * OpenClaw AI 对话界面
 * 支持多轮对话上下文、会话管理
 * 支持语音输入输出、说话打断
 */
public class OpenClawChatActivity extends AppCompatActivity {

    private static final String TAG = "OpenClawChat";

    // UI 组件
    private Toolbar toolbar;
    private EditText messageInput;
    private LinearLayout chatContainer;
    private ScrollView scrollView;
    private Button sendButton;
    private ImageButton voiceButton;
    private TextView txtSessionInfo;

    // 服务
    private OpenClawApiClient apiClient;
    private ConversationHistoryService historyService;

    // 语音组件
    private VoiceRecorder voiceRecorder;
    private AudioPlayer audioPlayer;

    // 状态
    private boolean isProcessing = false;
    private boolean isListening = false;
    private final int REQUEST_RECORD_PERMISSION = 1001;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_openclaw_chat);

        // 初始化服务
        apiClient = new OpenClawApiClient(this);
        historyService = new ConversationHistoryService(this);

        initViews();
        setupListeners();
        loadHistoryMessages();

        // 初始化语音组件
        voiceRecorder = new VoiceRecorder(this);
        audioPlayer = new AudioPlayer(this);
    }

    private void initViews() {
        toolbar = findViewById(R.id.toolbar);
        if (toolbar != null) {
            setSupportActionBar(toolbar);
            if (getSupportActionBar() != null) {
                getSupportActionBar().setDisplayHomeAsUpEnabled(true);
                getSupportActionBar().setTitle("AI 对话");
            }
        }

        messageInput = findViewById(R.id.messageInput);
        sendButton = findViewById(R.id.sendButton);
        voiceButton = findViewById(R.id.voiceButton);
        chatContainer = findViewById(R.id.chatContainer);
        scrollView = findViewById(R.id.scrollView);
        txtSessionInfo = findViewById(R.id.txt_session_info);

        // 显示当前会话信息
        updateSessionInfo();
    }

    private void setupListeners() {
        // 发送按钮
        sendButton.setOnClickListener(v -> sendMessage());

        // 语音按钮 - 切换录音状态，支持说话打断
        voiceButton.setOnClickListener(v -> {
            if (isListening) {
                // 停止录音
                stopVoiceRecording();
            } else {
                // 开始录音，如果正在播放TTS则打断
                if (audioPlayer.isPlaying()) {
                    audioPlayer.interrupt();
                }
                // 开始录音
                startVoiceRecording();
            }
        });

        // 回车发送
        messageInput.setOnEditorActionListener((v, actionId, event) -> {
            if (actionId == android.view.inputmethod.EditorInfo.IME_ACTION_SEND ||
                    (event != null && event.getKeyCode() == android.view.KeyEvent.KEYCODE_ENTER)) {
                sendMessage();
                return true;
            }
            return false;
        });
    }

    /**
     * 加载历史消息到界面
     */
    private void loadHistoryMessages() {
        List<JSONObject> messages = historyService.getMessagesForDisplay(50);

        // 清空当前显示
        chatContainer.removeAllViews();

        // 添加欢迎消息
        if (messages.isEmpty()) {
            addMessage("🦞 你好！我是你的 AI 助手。我可以记住我们的对话，长按麦克风说话，松开自动识别，随时可以打断我说话。", false);
        } else {
            // 加载历史消息
            for (int i = messages.size() - 1; i >= 0; i--) {
                try {
                    JSONObject msg = messages.get(i);
                    String role = msg.getString("role");
                    String content = msg.getString("content");
                    boolean isUser = "user".equals(role);
                    addMessageToView(content, isUser, false);
                } catch (Exception e) {
                    Log.e(TAG, "加载历史消息失败", e);
                }
            }

            // 添加分隔
            addMessage("─── 历史消息已加载 ───", false);
        }
    }

    /**
     * 发送文字消息
     */
    private void sendMessage() {
        if (isProcessing) {
            Toast.makeText(this, "正在处理中...", Toast.LENGTH_SHORT).show();
            return;
        }

        // 如果正在播放，打断
        if (audioPlayer.isPlaying()) {
            audioPlayer.interrupt();
        }

        String message = messageInput.getText().toString().trim();
        if (message.isEmpty()) {
            Toast.makeText(this, "请输入消息", Toast.LENGTH_SHORT).show();
            return;
        }

        // 显示用户消息
        addMessageToView(message, true, true);
        messageInput.setText("");
        isProcessing = true;
        sendButton.setEnabled(false);

        // 保存用户消息到历史
        historyService.addUserMessage(message);

        // 获取对话历史
        JSONArray conversationHistory = historyService.getConversationHistory();

        // 调用 API（带历史）
        apiClient.chatWithHistory(conversationHistory, new OpenClawApiClient.ChatCallback() {
            @Override
            public void onSuccess(String reply) {
                runOnUiThread(() -> {
                    addMessageToView(reply, false, true);
                    // 保存AI回复到历史
                    historyService.addAssistantMessage(reply);
                    isProcessing = false;
                    sendButton.setEnabled(true);
                });
            }

            @Override
            public void onError(String error) {
                runOnUiThread(() -> {
                    addMessageToView("⚠️ " + error, false, true);
                    Toast.makeText(OpenClawChatActivity.this, error, Toast.LENGTH_SHORT).show();
                    isProcessing = false;
                    sendButton.setEnabled(true);
                });
            }
        });
    }

    /**
     * 开始语音录制
     */
    private void startVoiceRecording() {
        // 检查权限
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.RECORD_AUDIO},
                    REQUEST_RECORD_PERMISSION);
            return;
        }

        startVoiceRecordingInternal();
    }

    private void startVoiceRecordingInternal() {
        isListening = true;
        // 录音时变为红色
        voiceButton.setBackgroundColor(getResources().getColor(android.R.color.holo_red_dark));
        addMessage("🎤 正在倾听...", false);

        voiceRecorder.startRecording(new VoiceRecorder.VoiceRecorderCallback() {
            @Override
            public void onSpeechStart() {
                Log.d(TAG, "Speech detected");
            }

            @Override
            public void onSpeechEnd(String wavFilePath) {
                Log.d(TAG, "Speech ended, file: " + wavFilePath);
                runOnUiThread(() -> {
                    processVoiceResult(wavFilePath);
                });
            }

            @Override
            public void onError(String error) {
                Log.e(TAG, "Recording error: " + error);
                runOnUiThread(() -> {
                    Toast.makeText(OpenClawChatActivity.this, error, Toast.LENGTH_SHORT).show();
                    stopVoiceRecording();
                });
            }
        });
    }

    /**
     * 停止语音录制
     */
    private void stopVoiceRecording() {
        voiceRecorder.stopRecording();
        isListening = false;
        // 恢复绿色
        voiceButton.setBackgroundResource(R.drawable.bg_voice_button);
    }

    /**
     * 处理录音结果，上传到服务端
     */
    private void processVoiceResult(String wavFilePath) {
        stopVoiceRecording();
        File audioFile = new File(wavFilePath);
        if (!audioFile.exists() || audioFile.length() < 1000) {
            Toast.makeText(this, "录音文件无效，请重试", Toast.LENGTH_SHORT).show();
            VoiceRecorder.deleteFile(wavFilePath);
            return;
        }

        isProcessing = true;

        JSONArray conversationHistory = historyService.getConversationHistory();

        apiClient.voiceChat(audioFile, conversationHistory, new OpenClawApiClient.VoiceChatCallback() {
            @Override
            public void onSuccess(String text, byte[] ttsAudio) {
                runOnUiThread(() -> {
                    // 显示用户语音转文字
                    addMessageToView(text, true, true);
                    historyService.addUserMessage(text);

                    isProcessing = false;

                    // 播放 TTS 音频
                    audioPlayer.playWav(ttsAudio, new AudioPlayer.PlaybackCallback() {
                        @Override
                        public void onPlaybackComplete() {
                            Log.d(TAG, "TTS playback complete");
                        }

                        @Override
                        public void onPlaybackError(String error) {
                            runOnUiThread(() -> {
                                Toast.makeText(OpenClawChatActivity.this, error, Toast.LENGTH_SHORT).show();
                            });
                        }
                    });
                });
            }

            @Override
            public void onError(String error) {
                runOnUiThread(() -> {
                    Toast.makeText(OpenClawChatActivity.this, error, Toast.LENGTH_SHORT).show();
                    isProcessing = false;
                });
            }
        });

        // 删除临时文件
        VoiceRecorder.deleteFile(wavFilePath);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, String[] permissions, int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_RECORD_PERMISSION) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startVoiceRecordingInternal();
            } else {
                Toast.makeText(this, "需要录音权限才能使用语音功能", Toast.LENGTH_SHORT).show();
            }
        }
    }

    /**
     * 添加消息到界面
     */
    private void addMessageToView(String message, boolean isUserMessage, boolean animate) {
        TextView messageView = new TextView(this);
        messageView.setText(message);
        messageView.setTextSize(15);
        messageView.setLineSpacing(4, 1.1f);
        messageView.setPadding(20, 14, 20, 14);
        int maxWidth = (int) (getResources().getDisplayMetrics().widthPixels * 0.78f);
        messageView.setMaxWidth(maxWidth);

        // 设置样式 - 豆包简约风格
        if (isUserMessage) {
            messageView.setBackgroundResource(R.drawable.bg_message_user);
            messageView.setTextColor(getResources().getColor(R.color.white));
        } else {
            messageView.setBackgroundResource(R.drawable.bg_message_ai);
            messageView.setTextColor(getResources().getColor(R.color.text_primary));
        }

        // 设置对齐 - 豆包风格：用户右对齐，AI左对齐
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.gravity = isUserMessage ? android.view.Gravity.END : android.view.Gravity.START;
        params.setMargins(4, 6, 4, 6);
        messageView.setLayoutParams(params);

        chatContainer.addView(messageView);

        // 滚动到底部
        scrollView.post(() -> scrollView.fullScroll(ScrollView.FOCUS_DOWN));

        // 动画效果
        if (animate) {
            messageView.setAlpha(0f);
            messageView.animate().alpha(1f).setDuration(150).start();
        }
    }

    /**
     * 添加消息（简化版）
     */
    private void addMessage(String message, boolean isUserMessage) {
        addMessageToView(message, isUserMessage, true);
    }

    /**
     * 更新会话信息显示
     */
    private void updateSessionInfo() {
        if (txtSessionInfo != null) {
            String sessionName = historyService.getCurrentSessionName();
            txtSessionInfo.setText("会话: " + sessionName);
        }
    }

    @Override
    public boolean onCreateOptionsMenu(Menu menu) {
        getMenuInflater().inflate(R.menu.chat_menu, menu);
        return true;
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        int id = item.getItemId();

        if (id == android.R.id.home) {
            finish();
            return true;
        } else if (id == R.id.action_new_session) {
            showNewSessionDialog();
            return true;
        } else if (id == R.id.action_switch_session) {
            showSwitchSessionDialog();
            return true;
        } else if (id == R.id.action_clear_history) {
            showClearHistoryDialog();
            return true;
        }

        return super.onOptionsItemSelected(item);
    }

    /**
     * 显示新建会话对话框
     */
    private void showNewSessionDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("新建会话");

        final EditText input = new EditText(this);
        input.setHint("会话名称");
        input.setText("新会话 " + (historyService.getAllSessions().size() + 1));
        builder.setView(input);

        builder.setPositiveButton("创建", (dialog, which) -> {
            String name = input.getText().toString().trim();
            if (!name.isEmpty()) {
                historyService.createNewSession(name);
                chatContainer.removeAllViews();
                addMessage("🦞 新会话已创建，长按麦克风说话，有什么可以帮你的？", false);
                updateSessionInfo();
            }
        });

        builder.setNegativeButton("取消", null);
        builder.show();
    }

    /**
     * 显示切换会话对话框
     */
    private void showSwitchSessionDialog() {
        List<JSONObject> sessions = historyService.getAllSessions();

        if (sessions.isEmpty()) {
            Toast.makeText(this, "没有其他会话", Toast.LENGTH_SHORT).show();
            return;
        }

        String[] sessionNames = new String[sessions.size()];
        for (int i = 0; i < sessions.size(); i++) {
            try {
                sessionNames[i] = sessions.get(i).getString("session_name") +
                        " (" + sessions.get(i).getInt("message_count") + "条消息)";
            } catch (Exception e) {
                sessionNames[i] = "未知会话";
            }
        }

        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("切换会话");
        builder.setItems(sessionNames, (dialog, which) -> {
            try {
                long sessionId = sessions.get(which).getLong("session_id");
                historyService.switchSession(sessionId);
                loadHistoryMessages();
                updateSessionInfo();
                Toast.makeText(this, "已切换到: " + sessionNames[which], Toast.LENGTH_SHORT).show();
            } catch (Exception e) {
                Log.e(TAG, "切换会话失败", e);
            }
        });

        builder.setNegativeButton("取消", null);
        builder.show();
    }

    /**
     * 显示清空历史对话框
     */
    private void showClearHistoryDialog() {
        new AlertDialog.Builder(this)
                .setTitle("清空历史")
                .setMessage("确定要清空当前会话的所有对话记录吗？")
                .setPositiveButton("清空", (dialog, which) -> {
                    historyService.clearCurrentSessionHistory();
                    chatContainer.removeAllViews();
                    addMessage("🦞 对话历史已清空，有什么可以帮你的？", false);
                })
                .setNegativeButton("取消", null)
                .show();
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (historyService != null) {
            historyService.close();
        }
        if (audioPlayer != null) {
            audioPlayer.stop();
        }
        if (voiceRecorder != null && voiceRecorder.isRecording()) {
            voiceRecorder.stopRecording();
        }
    }
}