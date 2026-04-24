package com.openclaw.homeassistant.data.remote.dto

import com.google.gson.annotations.SerializedName

data class ChatRequest(
    val message: String,
    val voice_mode: Boolean = false
)

data class ChatResponse(
    val response: String,
    val skill_used: String?,
    val emotion: String = "neutral",
    val metadata: MetadataDto?
)

data class MetadataDto(
    val mode: String,
    val skill_result: Map<String, Any>?
)

data class ChatStreamInitResponse(
    val status: String,
    val response: String?,
    val skill_used: String?,
    val done: Boolean = false
)

data class OpenAIChatRequest(
    val model: String? = null,
    val messages: List<OpenAIMessageDto>,
    val stream: Boolean = false,
    val temperature: Double = 0.7,
    val max_tokens: Int = 1000
)

data class OpenAIMessageDto(
    val role: String,
    val content: String
)

data class OpenAIChatResponse(
    val id: String,
    @SerializedName("object")
    val objectType: String,
    val created: Long,
    val model: String,
    val choices: List<OpenAIChoiceDto>,
    val usage: OpenAIUsageDto?
)

data class OpenAIChoiceDto(
    val index: Int,
    val message: OpenAIMessageDto,
    val finish_reason: String
)

data class OpenAIUsageDto(
    val prompt_tokens: Int,
    val completion_tokens: Int,
    val total_tokens: Int
)

data class ModelsResponse(
    @SerializedName("object")
    val objectType: String,
    val data: List<ModelDto>
)

data class ModelDto(
    val id: String,
    @SerializedName("object")
    val objectType: String
)

data class VoicePipelineResponse(
    val success: Boolean,
    val text: String = "",
    val response: String = "",
    val audio_data: String? = null,
    val source: String = "llm",
    val thinking: String? = null,
    val infrared: InfraredDto? = null,
    val error: String? = null
)

data class InfraredDto(
    val device: String = "",
    val frequency: Int = 38000,
    val pattern: String = "",
    val action: String = ""
)

data class SttResponse(
    val success: Boolean,
    val text: String = "",
    val error: String? = null
)

data class TtsRequest(
    val text: String
)

data class VoiceChatRequest(
    val message: String,
    val system_prompt: String? = null
)

data class VoiceChatResponse(
    val success: Boolean,
    val response: String = ""
)

data class VoiceHealthResponse(
    val status: String,
    val services: Map<String, String>?
)

data class HaPingResponse(
    val connected: Boolean
)

data class HaEntityStateDto(
    val entity_id: String,
    val state: String,
    val attributes: Map<String, Any> = emptyMap(),
    val last_changed: String? = null,
    val last_updated: String? = null
)

data class HaControlRequest(
    val entity_id: String,
    val action: String = "on"
)

data class HaControlResponse(
    val success: Boolean = true,
    val result: Any? = null
)

data class HaLightRequest(
    val entity_id: String,
    val brightness: Int? = null,
    val color_temp: Int? = null,
    val rgb_color: List<Int>? = null
)

data class HaLightResponse(
    val success: Boolean = true,
    val result: Any? = null
)

data class HaClimateRequest(
    val entity_id: String,
    val temperature: Double,
    val hvac_mode: String? = null
)

data class HaClimateResponse(
    val success: Boolean = true,
    val result: Any? = null
)

data class HaSceneDto(
    val entity_id: String,
    val name: String? = null,
    val state: String? = null
)

data class SceneActivateRequest(
    val entity_id: String
)

data class SceneActivateResponse(
    val success: Boolean = true,
    val result: Any? = null
)

data class MqttStatusResponse(
    val connected: Boolean,
    val devices: Int
)

data class MqttDevicesResponse(
    val devices: List<MqttDeviceDto>
)

data class MqttDeviceDto(
    val device_id: String,
    val name: String,
    val state: String? = null,
    val type: String? = null
)

data class MqttControlRequest(
    val device_id: String,
    val action: String,
    val value: String? = null
)

data class MqttControlResponse(
    val success: Boolean = true,
    val result: Any? = null
)

data class SwitchBotStatusResponse(
    val configured: Boolean,
    val devices: List<SwitchBotDeviceDto>? = null
)

data class SwitchBotDevicesResponse(
    val devices: List<SwitchBotDeviceDto>
)

data class SwitchBotDeviceDto(
    val device_id: String,
    val name: String,
    val type: String,
    val state: String? = null
)

data class SwitchBotControlRequest(
    val device_id: String,
    val action: String,
    val value: Int? = null
)

data class SwitchBotControlResponse(
    val success: Boolean = true,
    val result: Any? = null
)

data class FrigateStatusResponse(
    val configured: Boolean,
    val cameras: List<String>? = null
)

data class FrigateEventsResponse(
    val events: List<FrigateEventDto>
)

data class FrigateEventDto(
    val id: String,
    val camera: String,
    val label: String,
    val start_time: Double,
    val end_time: Double?,
    val thumbnail: String?,
    val has_clip: Boolean = false
)

data class FrigateSummaryResponse(
    val summary: Map<String, Any>
)

data class MemorySearchResultDto(
    val id: String,
    val text: String,
    val score: Double,
    val timestamp: String? = null
)

data class SnapshotRequest(
    val scene_type: String? = null,
    val note: String? = null
)

data class SnapshotResponse(
    val success: Boolean,
    val entry: Map<String, Any>? = null
)

data class EmotionalMemoryResponse(
    val memories: List<MemorySearchResultDto>? = null
)

data class MemoryReportResponse(
    val report: Map<String, Any>? = null
)

data class SceneMemoryResponse(
    val scenes: List<Map<String, Any>>? = null
)

data class PersonalityStatusDto(
    val name: String = "元芳",
    val mood: String = "calm",
    val energy: Double = 0.8,
    val stress: Double = 0.2,
    val traits: PersonalityTraitsDto = PersonalityTraitsDto(),
    val evolution_count: Int = 0,
    val last_updated: String? = null
)

data class PersonalityTraitsDto(
    val curiosity: Double = 0.85,
    val loyalty: Double = 0.90,
    val playfulness: Double = 0.60,
    val caution: Double = 0.70,
    val initiative: Double = 0.75
)

data class MoodUpdateRequest(
    val mood: String,
    val energy_delta: Double = 0.0,
    val stress_delta: Double = 0.0
)

data class MoodUpdateResponse(
    val success: Boolean,
    val status: PersonalityStatusDto? = null
)

data class MoodDriftResponse(
    val success: Boolean,
    val new_mood: String = "calm"
)

data class SkillsListResponse(
    val skills: List<SkillDto>
)

data class SkillDto(
    val id: String,
    val name: String,
    val description: String? = null,
    val category: String? = null,
    val trigger_patterns: List<String>? = null,
    val quality_score: Double? = null
)

data class SkillRegisterRequest(
    val name: String,
    val description: String? = null,
    val category: String = "general",
    val trigger_patterns: List<String>? = null,
    val ha_commands: List<Map<String, String>>? = null,
    val response_template: String? = null,
    val quality_score: Double = 5.0
)

data class SkillRegisterResponse(
    val success: Boolean,
    val skill_id: String? = null
)

data class SkillExecuteRequest(
    val commands: List<Map<String, String>>,
    val read_only: Boolean = false,
    val allowed_domains: List<String>? = null,
    val max_actions: Int = 5,
    val require_approval: Boolean = false
)

data class SkillExecuteResponse(
    val results: List<Map<String, Any>>,
    val permission: SkillPermissionDto? = null
)

data class SkillPermissionDto(
    val read_only: Boolean,
    val allowed_domains: List<String>
)

data class SkillsReportResponse(
    val report: Map<String, Any>? = null
)

data class RuleDto(
    val id: String,
    val name: String,
    val condition: Map<String, Any>? = null,
    val action: List<Map<String, Any>>? = null,
    val enabled: Boolean = true,
    val priority: Int = 0
)

data class AddRuleRequest(
    val id: String,
    val name: String,
    val condition: Map<String, Any>,
    val action: List<Map<String, Any>>,
    val enabled: Boolean = true,
    val priority: Int = 0
)

data class RuleCheckRequest(
    val context: Map<String, Any>
)

data class RuleCheckResponse(
    val results: List<Map<String, Any>>
)

data class NotificationDto(
    val id: String? = null,
    val type: String? = null,
    val message: String? = null,
    val timestamp: String? = null
)

data class JarvisHealthResponse(
    val status: String,
    val jarvis: String? = null
)

data class JarvisStatusResponse(
    val status: String,
    val version: String? = null,
    val models: Map<String, Any>? = null,
    val voice_config: Map<String, Any>? = null,
    val redis_connected: Boolean? = null,
    val qdrant_connected: Boolean? = null
)

data class JarvisChatResponse(
    val status: String,
    val response: String? = null
)

data class NluResponse(
    val status: String,
    val intent: String? = null,
    val parameters: Map<String, Any>? = null,
    val confidence: Double? = null,
    val suggested_actions: List<String>? = null
)

data class KnowledgeSearchResponse(
    val status: String,
    val results: List<String>? = null,
    val count: Int? = null
)

data class JarvisTtsResponse(
    val status: String,
    val message: String? = null,
    val audio_url: String? = null
)

data class JarvisAsrResponse(
    val status: String,
    val recognized_text: String? = null,
    val message: String? = null
)

data class JarvisExecuteResponse(
    val status: String,
    val message: String? = null,
    val output: String? = null,
    val exit_code: Int? = null
)

data class HaSummaryResponse(
    val summary: Map<String, Any>? = null
)

data class KairosStatusResponse(
    val daemon: Map<String, Any>? = null,
    val dream: Map<String, Any>? = null,
    val tools: Map<String, Any>? = null
)

data class KairosObservationsResponse(
    val observations: List<Map<String, Any>>? = null
)

data class KairosAnomaliesResponse(
    val anomalies: List<Map<String, Any>>? = null
)

data class KairosEnvironmentResponse(
    val environment: Map<String, Any>? = null
)

data class KairosInsightsResponse(
    val insights: List<Map<String, Any>>? = null
)

data class HyperRunRequest(
    val task: String,
    val enable_evolution: Boolean = true
)

data class HyperRunResponse(
    val response: String? = null,
    val model: String? = null,
    val improvement: String? = null,
    val evolution_count: Int? = null,
    val timestamp: String? = null
)

data class HyperStatusResponse(
    val status: Map<String, Any>? = null
)

data class AgentCrewRequest(
    val task: String
)

data class AgentCrewResponse(
    val result: Map<String, Any>? = null
)

data class AgentCallRequest(
    val input: String
)

data class AgentCallResponse(
    val result: Map<String, Any>? = null
)

data class SkillAbstractRequest(
    val min_occurrences: Int = 3
)

data class SkillAbstractResponse(
    val analyzed: Int? = null,
    val new_skills: List<Map<String, Any>>? = null,
    val message: String? = null
)

data class SkillDeleteResponse(
    val success: Boolean = false
)

data class SkillMarketplaceResponse(
    val skills: List<SkillDto>? = null
)

data class SkillInstallRequest(
    val builtin_name: String? = null
)

data class SkillInstallResponse(
    val success: Boolean = false,
    val result: Map<String, Any>? = null
)

data class SendCommandRequest(
    val node_id: String,
    val action: String,
    val params: Map<String, Any>? = null
)

data class SendCommandResponse(
    val success: Boolean = false,
    val command_id: String? = null
)

data class PendingCommandDto(
    val command_id: String,
    val action: String,
    val params: Map<String, Any>? = null
)

data class CommandCompleteRequest(
    val node_id: String,
    val command_id: String,
    val success: Boolean,
    val result: Map<String, Any>? = null
)

data class CommandCompleteResponse(
    val success: Boolean = false
)