package com.openclaw.homeassistant.data.local.db.dao

import androidx.room.*
import com.openclaw.homeassistant.data.local.db.entity.MessageEntity
import kotlinx.coroutines.flow.Flow

@Dao
interface MessageDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(message: MessageEntity): Long

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(messages: List<MessageEntity>)

    @Query("SELECT * FROM messages WHERE sessionId = :sessionId ORDER BY timestamp ASC")
    fun getBySession(sessionId: String): Flow<List<MessageEntity>>

    @Query("SELECT * FROM messages WHERE sessionId = :sessionId ORDER BY timestamp ASC LIMIT :limit")
    suspend fun getBySessionLimit(sessionId: String, limit: Int): List<MessageEntity>

    @Query("SELECT * FROM messages ORDER BY timestamp DESC LIMIT :limit")
    suspend fun getRecent(limit: Int): List<MessageEntity>

    @Query("SELECT COUNT(*) FROM messages WHERE sessionId = :sessionId")
    suspend fun getCount(sessionId: String): Int

    @Query("DELETE FROM messages WHERE sessionId = :sessionId")
    suspend fun deleteBySession(sessionId: String)

    @Query("DELETE FROM messages WHERE timestamp < :cutoff AND sessionId != :currentSessionId")
    suspend fun deleteOldMessages(cutoff: Long, currentSessionId: String): Int

    @Query("SELECT SUM(tokenCount) FROM messages WHERE sessionId = :sessionId")
    suspend fun getTotalTokens(sessionId: String): Int?
}

@Dao
interface ChatSessionDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(session: com.openclaw.homeassistant.data.local.db.entity.ChatSessionEntity)

    @Query("SELECT * FROM chat_sessions ORDER BY updatedAt DESC")
    fun getAll(): Flow<List<com.openclaw.homeassistant.data.local.db.entity.ChatSessionEntity>>

    @Query("SELECT * FROM chat_sessions WHERE id = :id")
    suspend fun getById(id: String): com.openclaw.homeassistant.data.local.db.entity.ChatSessionEntity?

    @Query("UPDATE chat_sessions SET updatedAt = :timestamp, messageCount = :count, preview = :preview WHERE id = :id")
    suspend fun updateStats(id: String, timestamp: Long, count: Int, preview: String)

    @Update
    suspend fun update(session: com.openclaw.homeassistant.data.local.db.entity.ChatSessionEntity)

    @Delete
    suspend fun delete(session: com.openclaw.homeassistant.data.local.db.entity.ChatSessionEntity)
}

@Dao
interface DeviceDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(device: com.openclaw.homeassistant.data.local.db.entity.DeviceEntity)

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertAll(devices: List<com.openclaw.homeassistant.data.local.db.entity.DeviceEntity>)

    @Query("SELECT * FROM devices ORDER BY room, name")
    fun getAll(): Flow<List<com.openclaw.homeassistant.data.local.db.entity.DeviceEntity>>

    @Query("SELECT * FROM devices WHERE entityId = :id")
    suspend fun getById(id: String): com.openclaw.homeassistant.data.local.db.entity.DeviceEntity?

    @Query("SELECT * FROM devices WHERE room = :room")
    fun getByRoom(room: String): Flow<List<com.openclaw.homeassistant.data.local.db.entity.DeviceEntity>>

    @Query("SELECT * FROM devices WHERE domain = :domain")
    fun getByDomain(domain: String): Flow<List<com.openclaw.homeassistant.data.local.db.entity.DeviceEntity>>

    @Query("SELECT * FROM devices WHERE isFavorite = 1")
    fun getFavorites(): Flow<List<com.openclaw.homeassistant.data.local.db.entity.DeviceEntity>>

    @Query("SELECT DISTINCT room FROM devices ORDER BY room")
    fun getRooms(): Flow<List<String>>

    @Update
    suspend fun update(device: com.openclaw.homeassistant.data.local.db.entity.DeviceEntity)

    @Delete
    suspend fun delete(device: com.openclaw.homeassistant.data.local.db.entity.DeviceEntity)

    @Query("DELETE FROM devices")
    suspend fun deleteAll()
}

@Dao
interface AutomationRuleDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(rule: com.openclaw.homeassistant.data.local.db.entity.AutomationRuleEntity)

    @Query("SELECT * FROM automation_rules ORDER BY priority DESC")
    fun getAll(): Flow<List<com.openclaw.homeassistant.data.local.db.entity.AutomationRuleEntity>>

    @Query("SELECT * FROM automation_rules WHERE enabled = 1 ORDER BY priority DESC")
    fun getEnabled(): Flow<List<com.openclaw.homeassistant.data.local.db.entity.AutomationRuleEntity>>

    @Query("SELECT * FROM automation_rules WHERE id = :id")
    suspend fun getById(id: String): com.openclaw.homeassistant.data.local.db.entity.AutomationRuleEntity?

    @Update
    suspend fun update(rule: com.openclaw.homeassistant.data.local.db.entity.AutomationRuleEntity)

    @Delete
    suspend fun delete(rule: com.openclaw.homeassistant.data.local.db.entity.AutomationRuleEntity)

    @Query("UPDATE automation_rules SET enabled = :enabled WHERE id = :id")
    suspend fun setEnabled(id: String, enabled: Boolean)

    @Query("UPDATE automation_rules SET lastTriggeredAt = :timestamp, triggerCount = triggerCount + 1 WHERE id = :id")
    suspend fun recordTrigger(id: String, timestamp: Long)
}