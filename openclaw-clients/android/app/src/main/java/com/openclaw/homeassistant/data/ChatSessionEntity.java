package com.openclaw.homeassistant.data;

import androidx.room.Entity;
import androidx.room.Index;
import androidx.room.PrimaryKey;
import androidx.annotation.NonNull;

@Entity(
    tableName = "chat_sessions",
    indices = {
        @Index(value = "timestamp")
    }
)
public class ChatSessionEntity {
    
    @PrimaryKey
    @NonNull
    public String id;
    
    public String preview;
    public long timestamp;
    public int messageCount;
    
    public ChatSessionEntity() {}
    
    public ChatSessionEntity(String id, String preview) {
        this.id = id;
        this.preview = preview;
        this.timestamp = System.currentTimeMillis();
        this.messageCount = 0;
    }
}