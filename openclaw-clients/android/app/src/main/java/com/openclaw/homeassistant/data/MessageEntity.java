package com.openclaw.homeassistant.data;

import androidx.room.Entity;
import androidx.room.Index;
import androidx.room.PrimaryKey;

@Entity(
    tableName = "messages",
    indices = {
        @Index(value = "sessionId"),
        @Index(value = "timestamp")
    }
)
public class MessageEntity {
    
    @PrimaryKey(autoGenerate = true)
    public long id;
    
    public String sessionId;
    public String role;
    public String content;
    public long timestamp;
    
    public MessageEntity() {}
    
    public MessageEntity(String sessionId, String role, String content) {
        this.sessionId = sessionId;
        this.role = role;
        this.content = content;
        this.timestamp = System.currentTimeMillis();
    }
}