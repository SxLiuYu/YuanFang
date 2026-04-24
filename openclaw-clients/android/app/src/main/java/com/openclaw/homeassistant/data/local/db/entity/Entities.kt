package com.openclaw.homeassistant.data.local.db.entity

import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey
import androidx.room.ForeignKey
import androidx.room.TypeConverter
import com.google.gson.Gson
import com.google.gson.reflect.TypeToken

@Entity(
    tableName = "messages",
    indices = [Index("sessionId"), Index("timestamp")]
)
data class MessageEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val sessionId: String,
    val role: String,
    val content: String,
    val tokenCount: Int = 0,
    val timestamp: Long = System.currentTimeMillis(),
    val emotion: String = "neutral",
    val source: String = "llm",
    val skillUsed: String? = null
)

@Entity(
    tableName = "chat_sessions",
    indices = [Index("updatedAt")]
)
data class ChatSessionEntity(
    @PrimaryKey val id: String,
    val name: String = "默认会话",
    val preview: String = "",
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis(),
    val messageCount: Int = 0,
    val personalityMood: String = "calm"
)

@Entity(
    tableName = "devices",
    indices = [Index("platform"), Index("room")]
)
data class DeviceEntity(
    @PrimaryKey val entityId: String,
    val name: String,
    val platform: String,
    val domain: String,
    val room: String = "",
    val state: String = "unknown",
    val attributesJson: String = "{}",
    val lastUpdated: Long = System.currentTimeMillis(),
    val isFavorite: Boolean = false
)

@Entity(tableName = "automation_rules")
data class AutomationRuleEntity(
    @PrimaryKey val id: String,
    val name: String,
    val enabled: Boolean = true,
    val conditionJson: String,
    val actionJson: String,
    val priority: Int = 0,
    val createdAt: Long = System.currentTimeMillis(),
    val lastTriggeredAt: Long? = null,
    val triggerCount: Int = 0
)