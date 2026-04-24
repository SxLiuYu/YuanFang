package com.openclaw.homeassistant.data.remote.api

import com.openclaw.homeassistant.data.remote.dto.*
import retrofit2.http.*

interface JarvisApi {

    @GET("/health")
    suspend fun health(): JarvisHealthResponse

    @GET("/api/status")
    suspend fun status(): JarvisStatusResponse

    @POST("/api/chat")
    suspend fun chat(@Query("message") message: String, @Query("user_id") userId: String?): JarvisChatResponse

    @POST("/api/nlu/understand")
    suspend fun nluUnderstand(@Query("question") question: String, @Query("context") context: String?): NluResponse

    @POST("/api/knowledge/search")
    suspend fun knowledgeSearch(@Query("query") query: String, @Query("limit") limit: Int?): KnowledgeSearchResponse

    @POST("/api/voice/speak")
    suspend fun voiceSpeak(@Query("text") text: String, @Query("voice_id") voiceId: String?): JarvisTtsResponse

    @POST("/api/voice/listen")
    suspend fun voiceListen(@Query("text") text: String): JarvisAsrResponse

    @POST("/api/execute")
    suspend fun execute(@Query("command") command: String, @Query("context") context: String?): JarvisExecuteResponse
}