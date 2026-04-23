package com.openclaw.homeassistant.data;

import androidx.room.Dao;
import androidx.room.Insert;
import androidx.room.Query;
import androidx.room.Delete;

import java.util.List;

@Dao
public interface MessageDao {
    
    @Insert
    long insert(MessageEntity message);
    
    @Query("SELECT * FROM messages WHERE sessionId = :sessionId ORDER BY timestamp ASC")
    List<MessageEntity> getMessagesBySession(String sessionId);
    
    @Query("SELECT * FROM messages WHERE sessionId = :sessionId ORDER BY timestamp DESC LIMIT :limit")
    List<MessageEntity> getRecentMessages(String sessionId, int limit);
    
    @Query("SELECT * FROM messages WHERE sessionId = :sessionId ORDER BY timestamp ASC LIMIT :offset, :limit")
    List<MessageEntity> getMessagesPaged(String sessionId, int offset, int limit);
    
    @Query("SELECT COUNT(*) FROM messages WHERE sessionId = :sessionId")
    int getMessageCount(String sessionId);
    
    @Query("DELETE FROM messages WHERE sessionId = :sessionId")
    void deleteBySession(String sessionId);
    
    @Query("DELETE FROM messages WHERE timestamp < :beforeTimestamp")
    int deleteOldMessages(long beforeTimestamp);
    
    @Query("DELETE FROM messages")
    void deleteAll();
    
    @Insert
    void insertSession(ChatSessionEntity session);
    
    @Query("SELECT * FROM chat_sessions ORDER BY timestamp DESC")
    List<ChatSessionEntity> getAllSessions();
    
    @Query("SELECT * FROM chat_sessions ORDER BY timestamp DESC LIMIT :limit")
    List<ChatSessionEntity> getRecentSessions(int limit);
    
    @Query("UPDATE chat_sessions SET preview = :preview, messageCount = messageCount + 1, timestamp = :timestamp WHERE id = :sessionId")
    void updateSession(String sessionId, String preview, long timestamp);
    
    @Delete
    void deleteSession(ChatSessionEntity session);
    
    @Query("DELETE FROM chat_sessions WHERE id = :sessionId")
    void deleteSessionById(String sessionId);
    
    @Query("DELETE FROM chat_sessions")
    void deleteAllSessions();
}