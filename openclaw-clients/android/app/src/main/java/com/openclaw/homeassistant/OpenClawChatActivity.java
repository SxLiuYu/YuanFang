package com.openclaw.homeassistant;
import android.util.Log;

import android.os.Bundle;
import android.view.Menu;
import android.view.MenuItem;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;
import android.widget.ScrollView;
import android.widget.LinearLayout;
import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.List;

/**
 * OpenClaw AI 对话界面
 * 支持多轮对话上下文、会话管理
 */
public class OpenClawChatActivity extends AppCompatActivity {

    private static final String TAG = "OpenClawChat";

    // UI 组件
    private Toolbar toolbar;
    private EditText messageInput;
    private TextView chatDisplay;
    private ScrollView scrollView;
    private LinearLayout chatContainer;
    private Button sendButton;
    private TextView txtSessionInfo;

    // 服务
    private OpenClawApiClient apiClient;
    private ConversationHistoryService historyService;

    // 状态
    private boolean isProcessing = false;

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
        chatContainer = findViewById(R.id.chatContainer);
        scrollView = findViewById(R.id.scrollView);
        txtSessionInfo = findViewById(R.id.txt_session_info);

        // 显示当前会话信息
        updateSessionInfo();
    }

    private void setupListeners() {
        // 发送按钮
        sendButton.setOnClickListener(v -> sendMessage());

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
            addMessage("🦞 你好！我是你的 AI 助手。我可以记住我们的对话，有什么可以帮你的？", false);
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
     * 发送消息
     */
    private void sendMessage() {
        if (isProcessing) {
            Toast.makeText(this, "正在处理中...", Toast.LENGTH_SHORT).show();
            return;
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
     * 添加消息到界面
     */
    private void addMessageToView(String message, boolean isUserMessage, boolean animate) {
        TextView messageView = new TextView(this);
        messageView.setText(message);
        messageView.setTextSize(16);
        messageView.setPadding(32, 24, 32, 24);
        int maxWidth = (int) (getResources().getDisplayMetrics().widthPixels * 0.8f);
        messageView.setMaxWidth(maxWidth);

        // 设置样式
        if (isUserMessage) {
            messageView.setBackgroundResource(R.drawable.bg_message_user);
            messageView.setTextColor(getResources().getColor(android.R.color.white));
        } else {
            messageView.setBackgroundResource(R.drawable.bg_message_ai);
            messageView.setTextColor(getResources().getColor(android.R.color.black));
        }

        // 设置对齐
        LinearLayout.LayoutParams params = new LinearLayout.LayoutParams(
                LinearLayout.LayoutParams.WRAP_CONTENT,
                LinearLayout.LayoutParams.WRAP_CONTENT
        );
        params.gravity = isUserMessage ? android.view.Gravity.END : android.view.Gravity.START;
        params.setMargins(0, 8, 0, 8);
        messageView.setLayoutParams(params);

        chatContainer.addView(messageView);

        // 滚动到底部
        scrollView.post(() -> scrollView.fullScroll(ScrollView.FOCUS_DOWN));

        // 动画效果
        if (animate) {
            messageView.setAlpha(0f);
            messageView.animate().alpha(1f).setDuration(200).start();
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
                addMessage("🦞 新会话已创建，有什么可以帮你的？", false);
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
    }
}