package com.openclaw.homeassistant.data.repository

import com.openclaw.homeassistant.data.local.db.dao.ChatSessionDao
import com.openclaw.homeassistant.data.local.db.dao.MessageDao
import com.openclaw.homeassistant.data.local.db.entity.ChatSessionEntity
import com.openclaw.homeassistant.data.local.db.entity.MessageEntity
import com.openclaw.homeassistant.data.remote.api.YuanFangApi
import com.openclaw.homeassistant.data.remote.dto.ChatRequest
import com.openclaw.homeassistant.data.remote.dto.OpenAIChatRequest
import com.openclaw.homeassistant.data.remote.dto.OpenAIMessageDto
import com.openclaw.homeassistant.data.remote.socket.YuanFangSocketClient
import com.openclaw.homeassistant.domain.model.ChatMessage
import com.openclaw.homeassistant.domain.model.ChatSession
import com.openclaw.homeassistant.domain.repository.ChatRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.first
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class ChatRepositoryImpl @Inject constructor(
    private val yuanFangApi: YuanFangApi,
    private val socketClient: YuanFangSocketClient,
    private val messageDao: MessageDao,
    private val chatSessionDao: ChatSessionDao
) : ChatRepository {

    private val _currentSessionId = MutableStateFlow("default")
    override val currentSessionId: String get() = _currentSessionId.value

    override fun getMessages(sessionId: String): Flow<List<ChatMessage>> {
        return messageDao.getBySession(sessionId).map { entities ->
            entities.map { it.toDomain() }
        }
    }

    override suspend fun sendMessage(sessionId: String, message: String): ChatMessage {
        val userMsg = MessageEntity(
            sessionId = sessionId,
            role = "user",
            content = message,
            timestamp = System.currentTimeMillis()
        )
        messageDao.insert(userMsg)

        val request = ChatRequest(message = message)
        val response = yuanFangApi.chat(request)

        val aiMsg = MessageEntity(
            sessionId = sessionId,
            role = "assistant",
            content = response.response,
            emotion = response.emotion,
            source = response.metadata?.mode ?: "llm",
            skillUsed = response.skill_used,
            timestamp = System.currentTimeMillis()
        )
        messageDao.insert(aiMsg)

        chatSessionDao.updateStats(
            sessionId,
            System.currentTimeMillis(),
            messageDao.getCount(sessionId),
            response.response.take(50)
        )

        return aiMsg.toDomain()
    }

    override suspend fun sendStreamMessage(sessionId: String, message: String): Flow<String> {
        val userMsg = MessageEntity(
            sessionId = sessionId,
            role = "user",
            content = message,
            timestamp = System.currentTimeMillis()
        )
        messageDao.insert(userMsg)

        socketClient.connect()
        yuanFangApi.chatStream(ChatRequest(message = message))

        return socketClient.chatChunks
    }

    override suspend fun sendOpenAIChat(messages: List<Pair<String, String>>, model: String?): ChatMessage {
        val sessionId = _currentSessionId.value

        val openAIMessages = messages.map { (role, content) ->
            OpenAIMessageDto(role = role, content = content)
        }
        val request = OpenAIChatRequest(messages = openAIMessages, model = model)
        val response = yuanFangApi.chatCompletions(request)

        val content = response.choices.firstOrNull()?.message?.content ?: ""
        val aiMsg = MessageEntity(
            sessionId = sessionId,
            role = "assistant",
            content = content,
            timestamp = System.currentTimeMillis()
        )
        messageDao.insert(aiMsg)

        return aiMsg.toDomain()
    }

    override fun getSessions(): Flow<List<ChatSession>> {
        return chatSessionDao.getAll().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    override suspend fun createSession(name: String): ChatSession {
        val id = "session_${System.currentTimeMillis()}"
        val entity = ChatSessionEntity(id = id, name = name)
        chatSessionDao.insert(entity)
        _currentSessionId.value = id
        return entity.toDomain()
    }

    override suspend fun switchSession(sessionId: String) {
        _currentSessionId.value = sessionId
    }

    override suspend fun deleteSession(sessionId: String) {
        messageDao.deleteBySession(sessionId)
        val session = chatSessionDao.getById(sessionId)
        if (session != null) chatSessionDao.delete(session)
    }

    override suspend fun clearSessionHistory(sessionId: String) {
        messageDao.deleteBySession(sessionId)
    }

    private fun MessageEntity.toDomain() = ChatMessage(
        id = id, sessionId = sessionId, role = role, content = content,
        timestamp = timestamp, emotion = emotion, source = source,
        skillUsed = skillUsed
    )

    private fun ChatSessionEntity.toDomain() = ChatSession(
        id = id, name = name, preview = preview, createdAt = createdAt,
        updatedAt = updatedAt, messageCount = messageCount, personalityMood = personalityMood
    )
}