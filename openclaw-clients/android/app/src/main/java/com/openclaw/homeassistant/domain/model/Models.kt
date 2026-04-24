package com.openclaw.homeassistant.domain.model

data class ChatMessage(
    val id: Long = 0,
    val sessionId: String,
    val role: String,
    val content: String,
    val timestamp: Long = System.currentTimeMillis(),
    val emotion: String = "neutral",
    val source: String = "llm",
    val skillUsed: String? = null,
    val isStreaming: Boolean = false
)

data class ChatSession(
    val id: String,
    val name: String = "默认会话",
    val preview: String = "",
    val createdAt: Long = System.currentTimeMillis(),
    val updatedAt: Long = System.currentTimeMillis(),
    val messageCount: Int = 0,
    val personalityMood: String = "calm"
)

data class DeviceState(
    val entityId: String,
    val name: String,
    val domain: String,
    val platform: String = "ha",
    val room: String = "",
    val state: String = "unknown",
    val attributes: Map<String, Any> = emptyMap(),
    val isFavorite: Boolean = false,
    val lastUpdated: Long = System.currentTimeMillis()
)

data class PersonalityState(
    val name: String = "元芳",
    val mood: String = "calm",
    val energy: Double = 0.8,
    val stress: Double = 0.2,
    val traits: PersonalityTraits = PersonalityTraits(),
    val evolutionCount: Int = 0,
    val lastUpdated: String? = null
)

data class PersonalityTraits(
    val curiosity: Double = 0.85,
    val loyalty: Double = 0.90,
    val playfulness: Double = 0.60,
    val caution: Double = 0.70,
    val initiative: Double = 0.75
)

data class MemoryEntry(
    val id: String,
    val text: String,
    val score: Double,
    val timestamp: String? = null
)

data class AutomationRule(
    val id: String,
    val name: String,
    val enabled: Boolean = true,
    val condition: RuleCondition,
    val actions: List<RuleAction>,
    val priority: Int = 0,
    val lastTriggeredAt: Long? = null,
    val triggerCount: Int = 0
)

data class RuleCondition(
    val triggerType: String,
    val entityId: String? = null,
    val time: String? = null,
    val days: List<String>? = null,
    val levelBelow: Double? = null,
    val state: String? = null
)

data class RuleAction(
    val type: String,
    val text: String? = null,
    val template: String? = null,
    val title: String? = null,
    val message: String? = null,
    val packageName: String? = null,
    val entityId: String? = null,
    val action: String? = null
)

data class Skill(
    val id: String,
    val name: String,
    val description: String?,
    val category: String?,
    val triggerPatterns: List<String>?,
    val qualityScore: Double?
)

data class InfraredCommand(
    val device: String,
    val frequency: Int,
    val pattern: String,
    val action: String
)

data class VoiceResult(
    val transcribedText: String,
    val aiResponse: String,
    val audioData: String?,
    val source: String,
    val infrared: InfraredCommand?,
    val success: Boolean
)

data class FrigateEvent(
    val id: String,
    val camera: String,
    val label: String,
    val startTime: Double,
    val endTime: Double?,
    val thumbnail: String?,
    val hasClip: Boolean = false
)

data class NotificationItem(
    val id: String?,
    val type: String?,
    val message: String?,
    val timestamp: String?
)

enum class Mood(val label: String) {
    CALM("平静"),
    HAPPY("开心"),
    CURIOUS("好奇"),
    FOCUSED("专注"),
    TIRED("疲惫")
}