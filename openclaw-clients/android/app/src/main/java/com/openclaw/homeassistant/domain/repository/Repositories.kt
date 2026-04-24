package com.openclaw.homeassistant.domain.repository

import com.openclaw.homeassistant.domain.model.*
import kotlinx.coroutines.flow.Flow

interface ChatRepository {
    fun getMessages(sessionId: String): Flow<List<ChatMessage>>
    suspend fun sendMessage(sessionId: String, message: String): ChatMessage
    suspend fun sendStreamMessage(sessionId: String, message: String): Flow<String>
    suspend fun sendOpenAIChat(messages: List<Pair<String, String>>, model: String?): ChatMessage
    fun getSessions(): Flow<List<ChatSession>>
    suspend fun createSession(name: String): ChatSession
    suspend fun switchSession(sessionId: String)
    suspend fun deleteSession(sessionId: String)
    suspend fun clearSessionHistory(sessionId: String)
    val currentSessionId: String
}

interface HomeRepository {
    suspend fun checkHaConnection(): Boolean
    suspend fun getDeviceStates(domain: String?): List<DeviceState>
    suspend fun controlDevice(entityId: String, action: String): Boolean
    suspend fun controlLight(entityId: String, brightness: Int?, colorTemp: Int?, rgbColor: List<Int>?): Boolean
    suspend fun controlClimate(entityId: String, temperature: Double, hvacMode: String?): Boolean
    suspend fun getScenes(): List<DeviceState>
    suspend fun activateScene(entityId: String): Boolean
    fun getLocalDevices(): Flow<List<DeviceState>>
    fun getFavoriteDevices(): Flow<List<DeviceState>>
    fun getRooms(): Flow<List<String>>
    suspend fun refreshDevices()
    suspend fun setFavorite(entityId: String, favorite: Boolean)
}

interface VoiceRepository {
    suspend fun processVoicePipeline(audioBytes: ByteArray, systemPrompt: String?): VoiceResult
    suspend fun recognizeSpeech(audioBytes: ByteArray): String
    suspend fun synthesizeSpeech(text: String): ByteArray?
    suspend fun textChat(message: String, systemPrompt: String?): String
    suspend fun processVisionVoice(audioBytes: ByteArray, imageBase64: String?): VoiceResult
    val streamChunks: Flow<String>
    val streamDone: Flow<String>
}

interface MemoryRepository {
    suspend fun search(query: String, topK: Int): List<MemoryEntry>
    suspend fun createSnapshot(sceneType: String?, note: String?): Boolean
    suspend fun getEmotionalMemory(emotion: String?, topK: Int): List<MemoryEntry>
    suspend fun getSceneMemory(type: String?, n: Int): List<MemoryEntry>
    suspend fun getMemoryReport(): Map<String, Any>
}

interface PersonalityRepository {
    suspend fun getStatus(): PersonalityState
    suspend fun updateMood(mood: String, energyDelta: Double, stressDelta: Double): PersonalityState
    suspend fun driftMood(): String
}

interface SkillsRepository {
    suspend fun getSkills(category: String?): List<Skill>
    suspend fun registerSkill(name: String, description: String?, category: String, triggerPatterns: List<String>?): String
    suspend fun executeSkillSandbox(commands: List<Map<String, String>>): List<Map<String, Any>>
    suspend fun getSkillsReport(): Map<String, Any>
}

interface RulesRepository {
    suspend fun getRules(enabled: Boolean?): List<AutomationRule>
    suspend fun addRule(rule: AutomationRule): AutomationRule
    suspend fun deleteRule(ruleId: String)
    suspend fun enableRule(ruleId: String)
    suspend fun disableRule(ruleId: String)
    suspend fun checkRules(context: Map<String, Any>): List<Map<String, Any>>
    fun getLocalRules(): Flow<List<AutomationRule>>
    suspend fun syncRules()
}

interface DeviceRepository {
    suspend fun registerDevice(): String
    suspend fun confirmDevice(tempId: String, code: String): Boolean
    suspend fun getDeviceInfo(): Map<String, Any>
    suspend fun logout()
    val isDeviceConfirmed: Boolean
}