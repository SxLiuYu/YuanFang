package com.openclaw.homeassistant;
import android.util.Log;

import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.sqlite.SQLiteDatabase;
import android.database.sqlite.SQLiteOpenHelper;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;

/**
 * 对话历史管理服务
 * 支持多轮对话上下文、多会话管理、历史持久化
 */
public class ConversationHistoryService {

    private static final String TAG = "ConversationHistory";
    private static final String DB_NAME = "conversation_history.db";
    private static final int DB_VERSION = 1;

    // 配置
    private static final int MAX_HISTORY_MESSAGES = 20;  // 最大历史消息数
    private static final int MAX_CONTEXT_TOKENS = 4000;  // 最大上下文token数（约）

    private DatabaseHelper dbHelper;
    private Context context;

    // 当前会话
    private long currentSessionId = -1;
    private String currentSessionName = "默认会话";

    public ConversationHistoryService(Context context) {
        this.context = context;
        this.dbHelper = new DatabaseHelper(context);
        initDefaultSession();
    }

    /**
     * 数据库帮助类
     */
    private static class DatabaseHelper extends SQLiteOpenHelper {

        public DatabaseHelper(Context context) {
            super(context, DB_NAME, null, DB_VERSION);
        }

        @Override
        public void onCreate(SQLiteDatabase db) {
            // 会话表
            db.execSQL("CREATE TABLE IF NOT EXISTS conversation_sessions (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                    "session_name TEXT, " +
                    "created_at INTEGER, " +
                    "updated_at INTEGER, " +
                    "message_count INTEGER DEFAULT 0)");

            // 消息表
            db.execSQL("CREATE TABLE IF NOT EXISTS conversation_messages (" +
                    "id INTEGER PRIMARY KEY AUTOINCREMENT, " +
                    "session_id INTEGER, " +
                    "role TEXT, " +
                    "content TEXT, " +
                    "token_count INTEGER DEFAULT 0, " +
                    "created_at INTEGER, " +
                    "FOREIGN KEY (session_id) REFERENCES conversation_sessions(id))");

            // 创建索引
            db.execSQL("CREATE INDEX IF NOT EXISTS idx_messages_session ON conversation_messages(session_id)");
            db.execSQL("CREATE INDEX IF NOT EXISTS idx_sessions_updated ON conversation_sessions(updated_at)");
        }

        @Override
        public void onUpgrade(SQLiteDatabase db, int oldVersion, int newVersion) {
            db.execSQL("DROP TABLE IF EXISTS conversation_messages");
            db.execSQL("DROP TABLE IF EXISTS conversation_sessions");
            onCreate(db);
        }
    }

    /**
     * 初始化默认会话
     */
    private void initDefaultSession() {
        SQLiteDatabase db = dbHelper.getReadableDatabase();
        Cursor cursor = db.query("conversation_sessions", null, null, null, null, null, "updated_at DESC", "1");

        if (cursor.moveToFirst()) {
            currentSessionId = cursor.getLong(cursor.getColumnIndexOrThrow("id"));
            currentSessionName = cursor.getString(cursor.getColumnIndexOrThrow("session_name"));
        } else {
            // 创建默认会话
            createNewSession("默认会话");
        }

        cursor.close();
        db.close();
    }

    // ========== 会话管理 ==========

    /**
     * 创建新会话
     */
    public long createNewSession(String sessionName) {
        SQLiteDatabase db = dbHelper.getWritableDatabase();
        ContentValues values = new ContentValues();
        values.put("session_name", sessionName);
        values.put("created_at", System.currentTimeMillis());
        values.put("updated_at", System.currentTimeMillis());
        values.put("message_count", 0);

        currentSessionId = db.insert("conversation_sessions", null, values);
        currentSessionName = sessionName;
        db.close();

        return currentSessionId;
    }

    /**
     * 获取所有会话
     */
    public List<JSONObject> getAllSessions() {
        List<JSONObject> sessions = new ArrayList<>();
        SQLiteDatabase db = dbHelper.getReadableDatabase();

        Cursor cursor = db.query("conversation_sessions", null, null, null, null, null, "updated_at DESC");

        while (cursor.moveToNext()) {
            JSONObject session = new JSONObject();
            try {
                session.put("session_id", cursor.getLong(cursor.getColumnIndexOrThrow("id")));
                session.put("session_name", cursor.getString(cursor.getColumnIndexOrThrow("session_name")));
                session.put("created_at", cursor.getLong(cursor.getColumnIndexOrThrow("created_at")));
                session.put("updated_at", cursor.getLong(cursor.getColumnIndexOrThrow("updated_at")));
                session.put("message_count", cursor.getInt(cursor.getColumnIndexOrThrow("message_count")));
            } catch (Exception e) {
                Log.e(TAG, "构建会话JSON失败", e);
            }
            sessions.add(session);
        }

        cursor.close();
        db.close();
        return sessions;
    }

    /**
     * 切换会话
     */
    public void switchSession(long sessionId) {
        SQLiteDatabase db = dbHelper.getReadableDatabase();
        Cursor cursor = db.query("conversation_sessions", null, "id = ?",
                new String[]{String.valueOf(sessionId)}, null, null, null);

        if (cursor.moveToFirst()) {
            currentSessionId = sessionId;
            currentSessionName = cursor.getString(cursor.getColumnIndexOrThrow("session_name"));
        }

        cursor.close();
        db.close();
    }

    /**
     * 删除会话及其消息
     */
    public void deleteSession(long sessionId) {
        SQLiteDatabase db = dbHelper.getWritableDatabase();

        // 删除消息
        db.delete("conversation_messages", "session_id = ?",
                new String[]{String.valueOf(sessionId)});

        // 删除会话
        db.delete("conversation_sessions", "id = ?",
                new String[]{String.valueOf(sessionId)});

        db.close();

        // 如果删除的是当前会话，切换到其他会话
        if (sessionId == currentSessionId) {
            initDefaultSession();
        }
    }

    // ========== 消息管理 ==========

    /**
     * 添加用户消息
     */
    public long addUserMessage(String content) {
        return addMessage("user", content);
    }

    /**
     * 添加AI消息
     */
    public long addAssistantMessage(String content) {
        return addMessage("assistant", content);
    }

    /**
     * 添加系统消息
     */
    public long addSystemMessage(String content) {
        return addMessage("system", content);
    }

    /**
     * 添加消息
     */
    private long addMessage(String role, String content) {
        if (currentSessionId < 0) {
            createNewSession("默认会话");
        }

        SQLiteDatabase db = dbHelper.getWritableDatabase();

        // 估算token数（粗略：中文约1.5字符/token，英文约4字符/token）
        int tokenCount = estimateTokens(content);

        ContentValues values = new ContentValues();
        values.put("session_id", currentSessionId);
        values.put("role", role);
        values.put("content", content);
        values.put("token_count", tokenCount);
        values.put("created_at", System.currentTimeMillis());

        long id = db.insert("conversation_messages", null, values);

        // 更新会话时间和消息数
        updateSessionStats(db);

        db.close();
        return id;
    }

    /**
     * 获取对话历史（用于API调用）
     */
    public JSONArray getConversationHistory() {
        return getConversationHistory(MAX_HISTORY_MESSAGES);
    }

    /**
     * 获取对话历史
     * @param maxMessages 最大消息数
     */
    public JSONArray getConversationHistory(int maxMessages) {
        JSONArray messages = new JSONArray();
        SQLiteDatabase db = dbHelper.getReadableDatabase();

        // 先添加系统提示
        JSONObject systemMessage = new JSONObject();
        try {
            systemMessage.put("role", "system");
            systemMessage.put("content", "你是一个智能家庭助手，请理解用户的语音指令并提供相应的帮助。" +
                    "你可以帮助用户控制智能家居、管理家庭任务、记录健康数据、查询天气新闻等。" +
                    "请用简洁友好的方式回复。");
            messages.put(systemMessage);
        } catch (Exception e) {
            Log.e(TAG, "构建系统消息失败", e);
        }

        // 获取历史消息（按时间升序）
        Cursor cursor = db.query("conversation_messages", null,
                "session_id = ?", new String[]{String.valueOf(currentSessionId)},
                null, null, "created_at DESC", String.valueOf(maxMessages));

        // 反向读取（从旧到新）
        List<JSONObject> tempMessages = new ArrayList<>();
        while (cursor.moveToNext()) {
            JSONObject msg = new JSONObject();
            try {
                msg.put("role", cursor.getString(cursor.getColumnIndexOrThrow("role")));
                msg.put("content", cursor.getString(cursor.getColumnIndexOrThrow("content")));
            } catch (Exception e) {
                Log.e(TAG, "构建消息JSON失败", e);
            }
            tempMessages.add(msg);
        }

        // 添加到JSONArray（从旧到新）
        for (int i = tempMessages.size() - 1; i >= 0; i--) {
            messages.put(tempMessages.get(i));
        }

        cursor.close();
        db.close();

        return messages;
    }

    /**
     * 获取对话历史（带token限制）
     */
    public JSONArray getConversationHistoryWithTokenLimit() {
        JSONArray messages = new JSONArray();
        SQLiteDatabase db = dbHelper.getReadableDatabase();

        // 系统提示
        JSONObject systemMessage = new JSONObject();
        try {
            systemMessage.put("role", "system");
            systemMessage.put("content", "你是一个智能家庭助手，请理解用户的语音指令并提供相应的帮助。");
            messages.put(systemMessage);
        } catch (Exception e) {
            Log.e(TAG, "构建系统消息失败", e);
        }

        // 获取消息并计算token
        Cursor cursor = db.query("conversation_messages", null,
                "session_id = ?", new String[]{String.valueOf(currentSessionId)},
                null, null, "created_at DESC");

        List<JSONObject> tempMessages = new ArrayList<>();
        int totalTokens = 0;

        while (cursor.moveToNext() && totalTokens < MAX_CONTEXT_TOKENS) {
            String role = cursor.getString(cursor.getColumnIndexOrThrow("role"));
            String content = cursor.getString(cursor.getColumnIndexOrThrow("content"));
            int tokens = cursor.getInt(cursor.getColumnIndexOrThrow("token_count"));

            if (totalTokens + tokens <= MAX_CONTEXT_TOKENS) {
                JSONObject msg = new JSONObject();
                try {
                    msg.put("role", role);
                    msg.put("content", content);
                } catch (Exception e) {
                    Log.e(TAG, "构建消息JSON失败", e);
                }
                tempMessages.add(msg);
                totalTokens += tokens;
            } else {
                break;
            }
        }

        cursor.close();
        db.close();

        // 从旧到新添加
        for (int i = tempMessages.size() - 1; i >= 0; i--) {
            messages.put(tempMessages.get(i));
        }

        return messages;
    }

    /**
     * 获取消息列表（用于显示）
     */
    public List<JSONObject> getMessagesForDisplay(int limit) {
        List<JSONObject> messages = new ArrayList<>();
        SQLiteDatabase db = dbHelper.getReadableDatabase();

        Cursor cursor = db.query("conversation_messages", null,
                "session_id = ?", new String[]{String.valueOf(currentSessionId)},
                null, null, "created_at DESC", String.valueOf(limit));

        while (cursor.moveToNext()) {
            JSONObject msg = new JSONObject();
            try {
                msg.put("message_id", cursor.getLong(cursor.getColumnIndexOrThrow("id")));
                msg.put("role", cursor.getString(cursor.getColumnIndexOrThrow("role")));
                msg.put("content", cursor.getString(cursor.getColumnIndexOrThrow("content")));
                msg.put("created_at", cursor.getLong(cursor.getColumnIndexOrThrow("created_at")));
            } catch (Exception e) {
                Log.e(TAG, "构建显示消息JSON失败", e);
            }
            messages.add(msg);
        }

        cursor.close();
        db.close();
        return messages;
    }

    /**
     * 清空当前会话历史
     */
    public void clearCurrentSessionHistory() {
        SQLiteDatabase db = dbHelper.getWritableDatabase();
        db.delete("conversation_messages", "session_id = ?",
                new String[]{String.valueOf(currentSessionId)});

        // 重置消息计数
        ContentValues values = new ContentValues();
        values.put("message_count", 0);
        values.put("updated_at", System.currentTimeMillis());
        db.update("conversation_sessions", values, "id = ?",
                new String[]{String.valueOf(currentSessionId)});

        db.close();
    }

    /**
     * 获取当前会话ID
     */
    public long getCurrentSessionId() {
        return currentSessionId;
    }

    /**
     * 获取当前会话名称
     */
    public String getCurrentSessionName() {
        return currentSessionName;
    }

    /**
     * 更新会话统计
     */
    private void updateSessionStats(SQLiteDatabase db) {
        // 获取消息数
        Cursor cursor = db.rawQuery(
                "SELECT COUNT(*) FROM conversation_messages WHERE session_id = ?",
                new String[]{String.valueOf(currentSessionId)});

        int count = 0;
        if (cursor.moveToFirst()) {
            count = cursor.getInt(0);
        }
        cursor.close();

        // 更新会话
        ContentValues values = new ContentValues();
        values.put("updated_at", System.currentTimeMillis());
        values.put("message_count", count);
        db.update("conversation_sessions", values, "id = ?",
                new String[]{String.valueOf(currentSessionId)});
    }

    /**
     * 估算token数
     */
    private int estimateTokens(String text) {
        if (text == null || text.isEmpty()) return 0;

        // 粗略估算：中文字符约1.5字符/token，英文约4字符/token
        int chineseChars = 0;
        int otherChars = 0;

        for (char c : text.toCharArray()) {
            if (Character.UnicodeScript.of(c) == Character.UnicodeScript.HAN) {
                chineseChars++;
            } else {
                otherChars++;
            }
        }

        return (int) Math.ceil(chineseChars / 1.5 + otherChars / 4.0);
    }

    /**
     * 关闭数据库
     */
    public void close() {
        if (dbHelper != null) {
            dbHelper.close();
        }
    }
}