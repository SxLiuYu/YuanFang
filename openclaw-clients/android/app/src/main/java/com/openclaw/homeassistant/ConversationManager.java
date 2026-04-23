package com.openclaw.homeassistant;

import android.content.Context;
import android.util.Log;

import com.openclaw.homeassistant.data.ChatSessionEntity;
import com.openclaw.homeassistant.data.ConversationDatabase;
import com.openclaw.homeassistant.data.MessageDao;
import com.openclaw.homeassistant.data.MessageEntity;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

/**
 * 对话管理器 - 使用 SQLite 存储多轮对话上下文和历史记录
 * 性能优化：异步数据库操作，支持分页查询
 */
public class ConversationManager {
    private static final String TAG = "ConversationManager";
    private static final int MAX_CONTEXT_SIZE = 20;
    private static final int MAX_HISTORY_SIZE = 50;
    private static final String DEFAULT_SESSION = "default";
    
    private final ConversationDatabase database;
    private final MessageDao messageDao;
    private final ExecutorService executor;
    
    private String currentSessionId = DEFAULT_SESSION;
    private List<Message> cachedContext;
    
    public static class Message {
        public String role;
        public String content;
        public long timestamp;
        
        public Message(String role, String content) {
            this.role = role;
            this.content = content;
            this.timestamp = System.currentTimeMillis();
        }
        
        public Message(String role, String content, long timestamp) {
            this.role = role;
            this.content = content;
            this.timestamp = timestamp;
        }
    }
    
    public static class ChatSession {
        public String id;
        public String preview;
        public long timestamp;
        public int messageCount;
        
        public ChatSession(ChatSessionEntity entity) {
            this.id = entity.id;
            this.preview = entity.preview;
            this.timestamp = entity.timestamp;
            this.messageCount = entity.messageCount;
        }
    }
    
    public interface DataCallback<T> {
        void onData(T data);
    }
    
    public ConversationManager(Context context) {
        this.database = ConversationDatabase.getInstance(context);
        this.messageDao = database.messageDao();
        this.executor = Executors.newSingleThreadExecutor();
        this.cachedContext = new ArrayList<>();
        loadContextAsync();
    }
    
    private void loadContextAsync() {
        executor.execute(() -> {
            try {
                List<MessageEntity> entities = messageDao.getRecentMessages(currentSessionId, MAX_CONTEXT_SIZE);
                cachedContext.clear();
                for (MessageEntity entity : entities) {
                    cachedContext.add(new Message(entity.role, entity.content, entity.timestamp));
                }
                Log.d(TAG, "加载上下文: " + cachedContext.size() + " 条消息");
            } catch (Exception e) {
                Log.e(TAG, "加载上下文失败", e);
            }
        });
    }
    
    public void addMessage(String role, String content) {
        Message message = new Message(role, content);
        cachedContext.add(message);
        
        if (cachedContext.size() > MAX_CONTEXT_SIZE) {
            cachedContext = cachedContext.subList(
                cachedContext.size() - MAX_CONTEXT_SIZE,
                cachedContext.size()
            );
        }
        
        executor.execute(() -> {
            try {
                MessageEntity entity = new MessageEntity(currentSessionId, role, content);
                messageDao.insert(entity);
                
                String preview = content.length() > 50 ? content.substring(0, 50) + "..." : content;
                messageDao.updateSession(currentSessionId, preview, System.currentTimeMillis());
                Log.d(TAG, "消息已保存: " + role);
            } catch (Exception e) {
                Log.e(TAG, "保存消息失败", e);
            }
        });
    }
    
    public List<Message> getContext() {
        return new ArrayList<>(cachedContext);
    }
    
    public void getContextAsync(DataCallback<List<Message>> callback) {
        executor.execute(() -> {
            try {
                List<MessageEntity> entities = messageDao.getRecentMessages(currentSessionId, MAX_CONTEXT_SIZE);
                List<Message> messages = new ArrayList<>();
                for (MessageEntity entity : entities) {
                    messages.add(new Message(entity.role, entity.content, entity.timestamp));
                }
                callback.onData(messages);
            } catch (Exception e) {
                Log.e(TAG, "获取上下文失败", e);
                callback.onData(new ArrayList<>());
            }
        });
    }
    
    public JSONArray getRecentMessages(int maxMessages) {
        JSONArray result = new JSONArray();
        try {
            int start = Math.max(0, cachedContext.size() - maxMessages);
            for (int i = start; i < cachedContext.size(); i++) {
                Message msg = cachedContext.get(i);
                JSONObject obj = new JSONObject();
                obj.put("role", msg.role);
                obj.put("content", msg.content);
                result.put(obj);
            }
        } catch (Exception e) {
            Log.e(TAG, "构建消息数组失败", e);
        }
        return result;
    }
    
    public void clearContext() {
        cachedContext.clear();
        executor.execute(() -> {
            try {
                messageDao.deleteBySession(currentSessionId);
                Log.d(TAG, "上下文已清除");
            } catch (Exception e) {
                Log.e(TAG, "清除上下文失败", e);
            }
        });
    }
    
    public void createNewSession(String sessionId) {
        this.currentSessionId = sessionId;
        this.cachedContext.clear();
        
        executor.execute(() -> {
            try {
                ChatSessionEntity session = new ChatSessionEntity(sessionId, "新对话");
                messageDao.insertSession(session);
                loadContextAsync();
                Log.d(TAG, "新会话已创建: " + sessionId);
            } catch (Exception e) {
                Log.e(TAG, "创建会话失败", e);
            }
        });
    }
    
    public void loadSession(String sessionId) {
        this.currentSessionId = sessionId;
        loadContextAsync();
    }
    
    public void getSessionsAsync(DataCallback<List<ChatSession>> callback) {
        executor.execute(() -> {
            try {
                List<ChatSessionEntity> entities = messageDao.getRecentSessions(MAX_HISTORY_SIZE);
                List<ChatSession> sessions = new ArrayList<>();
                for (ChatSessionEntity entity : entities) {
                    sessions.add(new ChatSession(entity));
                }
                callback.onData(sessions);
            } catch (Exception e) {
                Log.e(TAG, "获取会话列表失败", e);
                callback.onData(new ArrayList<>());
            }
        });
    }
    
    public void deleteSession(String sessionId) {
        executor.execute(() -> {
            try {
                messageDao.deleteBySession(sessionId);
                messageDao.deleteSessionById(sessionId);
                Log.d(TAG, "会话已删除: " + sessionId);
            } catch (Exception e) {
                Log.e(TAG, "删除会话失败", e);
            }
        });
    }
    
    public void cleanupOldData(long beforeTimestamp) {
        executor.execute(() -> {
            try {
                int deleted = messageDao.deleteOldMessages(beforeTimestamp);
                Log.d(TAG, "清理旧数据: " + deleted + " 条");
            } catch (Exception e) {
                Log.e(TAG, "清理数据失败", e);
            }
        });
    }
    
    public void close() {
        executor.shutdown();
        ConversationDatabase.destroyInstance();
    }
}