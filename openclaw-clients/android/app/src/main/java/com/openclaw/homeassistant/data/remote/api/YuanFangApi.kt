package com.openclaw.homeassistant.data.remote.api

import com.openclaw.homeassistant.data.remote.dto.*
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.*

interface YuanFangApi {

    @POST("/api/chat")
    suspend fun chat(@Body request: ChatRequest): ChatResponse

    @POST("/api/v1/chat/completions")
    suspend fun chatCompletions(@Body request: OpenAIChatRequest): OpenAIChatResponse

    @GET("/api/v1/models")
    suspend fun getModels(): ModelsResponse

    @Multipart
    @POST("/api/voice/pipeline")
    suspend fun voicePipeline(
        @Part audio: MultipartBody.Part,
        @Part("system_prompt") prompt: RequestBody?
    ): VoicePipelineResponse

    @Multipart
    @POST("/api/voice/stt")
    suspend fun voiceStt(@Part audio: MultipartBody.Part): SttResponse

    @POST("/api/voice/tts")
    suspend fun voiceTts(@Body request: TtsRequest): Response<okhttp3.ResponseBody>

    @POST("/api/voice/chat")
    suspend fun voiceChat(@Body request: VoiceChatRequest): VoiceChatResponse

    @Multipart
    @POST("/api/voice/vision-voice/pipeline")
    suspend fun visionVoicePipeline(
        @Part audio: MultipartBody.Part,
        @Part("image") image: RequestBody?,
        @Part("max_tokens") maxTokens: RequestBody?,
        @Part("use_tools") useTools: RequestBody?
    ): VoicePipelineResponse

    @Multipart
    @POST("/api/voice/fast")
    suspend fun voiceFast(
        @Part file: MultipartBody.Part,
        @Part("max_tokens") maxTokens: RequestBody?
    ): VoicePipelineResponse

    @GET("/api/voice/health")
    suspend fun voiceHealth(): VoiceHealthResponse

    @GET("/api/ha/ping")
    suspend fun haPing(): HaPingResponse

    @GET("/api/ha/states")
    suspend fun haStates(@Query("domain") domain: String?): List<HaEntityStateDto>

    @GET("/api/ha/state/{entityId}")
    suspend fun haState(@Path("entityId") entityId: String): HaEntityStateDto

    @POST("/api/ha/control")
    suspend fun haControl(@Body request: HaControlRequest): HaControlResponse

    @POST("/api/ha/light")
    suspend fun haLight(@Body request: HaLightRequest): HaLightResponse

    @POST("/api/ha/climate")
    suspend fun haClimate(@Body request: HaClimateRequest): HaClimateResponse

    @GET("/api/ha/scenes")
    suspend fun haScenes(): List<HaSceneDto>

    @POST("/api/ha/scene/activate")
    suspend fun haSceneActivate(@Body request: SceneActivateRequest): SceneActivateResponse

    @GET("/api/mqtt/status")
    suspend fun mqttStatus(): MqttStatusResponse

    @GET("/api/mqtt/devices")
    suspend fun mqttDevices(): MqttDevicesResponse

    @POST("/api/mqtt/control")
    suspend fun mqttControl(@Body request: MqttControlRequest): MqttControlResponse

    @GET("/api/switchbot/status")
    suspend fun switchbotStatus(): SwitchBotStatusResponse

    @GET("/api/switchbot/devices")
    suspend fun switchbotDevices(): SwitchBotDevicesResponse

    @POST("/api/switchbot/control")
    suspend fun switchbotControl(@Body request: SwitchBotControlRequest): SwitchBotControlResponse

    @GET("/api/frigate/status")
    suspend fun frigateStatus(): FrigateStatusResponse

    @GET("/api/frigate/events")
    suspend fun frigateEvents(
        @Query("label") label: String?,
        @Query("minutes") minutes: Int?,
        @Query("limit") limit: Int?
    ): FrigateEventsResponse

    @GET("/api/frigate/summary")
    suspend fun frigateSummary(@Query("minutes") minutes: Int?): FrigateSummaryResponse

    @GET("/api/memory/search")
    suspend fun memorySearch(@Query("q") query: String, @Query("top_k") topK: Int?): List<MemorySearchResultDto>

    @POST("/api/memory/scene/snapshot")
    suspend fun memorySnapshot(@Body request: SnapshotRequest): SnapshotResponse

    @GET("/api/memory/emotional")
    suspend fun memoryEmotional(@Query("emotion") emotion: String?, @Query("top_k") topK: Int?): EmotionalMemoryResponse

    @GET("/api/memory/report")
    suspend fun memoryReport(): MemoryReportResponse

    @GET("/api/memory/scene")
    suspend fun memoryScene(@Query("type") type: String?, @Query("n") n: Int?): SceneMemoryResponse

    @GET("/api/personality/status")
    suspend fun personalityStatus(): PersonalityStatusDto

    @POST("/api/personality/mood")
    suspend fun updateMood(@Body request: MoodUpdateRequest): MoodUpdateResponse

    @POST("/api/personality/drift")
    suspend fun driftMood(): MoodDriftResponse

    @GET("/api/skills")
    suspend fun getSkills(@Query("category") category: String?): SkillsListResponse

    @POST("/api/skills/register")
    suspend fun registerSkill(@Body request: SkillRegisterRequest): SkillRegisterResponse

    @POST("/api/skills/sandbox/execute")
    suspend fun executeSkillSandbox(@Body request: SkillExecuteRequest): SkillExecuteResponse

    @GET("/api/skills/report")
    suspend fun skillsReport(): SkillsReportResponse

    @GET("/api/rules")
    suspend fun getRules(@Query("enabled") enabled: Boolean?): List<RuleDto>

    @POST("/api/rules")
    suspend fun addRule(@Body request: AddRuleRequest): RuleDto

    @DELETE("/api/rules/{ruleId}")
    suspend fun deleteRule(@Path("ruleId") ruleId: String)

    @POST("/api/rules/{ruleId}/enable")
    suspend fun enableRule(@Path("ruleId") ruleId: String): RuleDto

    @POST("/api/rules/{ruleId}/disable")
    suspend fun disableRule(@Path("ruleId") ruleId: String): RuleDto

    @POST("/api/rules/check")
    suspend fun checkRules(@Body request: RuleCheckRequest): RuleCheckResponse

    @GET("/api/notifications/recent")
    suspend fun recentNotifications(@Query("n") n: Int?): List<NotificationDto>

    @POST("/api/chat/stream")
    suspend fun chatStream(@Body request: ChatRequest): ChatStreamInitResponse

    @GET("/api/ha/summary")
    suspend fun haSummary(): HaSummaryResponse

    @GET("/api/kairos/status")
    suspend fun kairosStatus(): KairosStatusResponse

    @GET("/api/kairos/observations")
    suspend fun kairosObservations(@Query("n") n: Int?): KairosObservationsResponse

    @GET("/api/kairos/anomalies")
    suspend fun kairosAnomalies(@Query("n") n: Int?, @Query("severity") severity: String?): KairosAnomaliesResponse

    @GET("/api/kairos/environment")
    suspend fun kairosEnvironment(): KairosEnvironmentResponse

    @GET("/api/kairos/insights")
    suspend fun kairosInsights(): KairosInsightsResponse

    @POST("/api/hyper/run")
    suspend fun hyperRun(@Body request: HyperRunRequest): HyperRunResponse

    @GET("/api/hyper/status")
    suspend fun hyperStatus(): HyperStatusResponse

    @POST("/api/agent/crew")
    suspend fun agentCrew(@Body request: AgentCrewRequest): AgentCrewResponse

    @POST("/api/agent/{agentName}")
    suspend fun agentCall(@Path("agentName") agentName: String, @Body request: AgentCallRequest): AgentCallResponse

    @POST("/api/skills/abstract")
    suspend fun skillsAbstract(@Body request: SkillAbstractRequest): SkillAbstractResponse

    @DELETE("/api/skills/{skillId}")
    suspend fun deleteSkill(@Path("skillId") skillId: String): SkillDeleteResponse

    @GET("/api/skills/marketplace/available")
    suspend fun skillsMarketplaceAvailable(): SkillMarketplaceResponse

    @POST("/api/skills/marketplace/install")
    suspend fun skillsMarketplaceInstall(@Body request: SkillInstallRequest): SkillInstallResponse

    @POST("/api/commands/send")
    suspend fun sendCommand(@Body request: SendCommandRequest): SendCommandResponse

    @GET("/api/commands/pending/{nodeId}")
    suspend fun pendingCommands(@Path("nodeId") nodeId: String): List<PendingCommandDto>

    @POST("/api/commands/complete")
    suspend fun completeCommand(@Body request: CommandCompleteRequest): CommandCompleteResponse
}