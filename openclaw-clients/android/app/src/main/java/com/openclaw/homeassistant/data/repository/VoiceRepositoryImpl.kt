package com.openclaw.homeassistant.data.repository

import android.util.Base64
import com.openclaw.homeassistant.data.remote.api.YuanFangApi
import com.openclaw.homeassistant.data.remote.dto.*
import com.openclaw.homeassistant.data.remote.socket.YuanFangSocketClient
import com.openclaw.homeassistant.domain.model.InfraredCommand
import com.openclaw.homeassistant.domain.model.VoiceResult
import com.openclaw.homeassistant.domain.repository.VoiceRepository
import kotlinx.coroutines.flow.Flow
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import java.io.File
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class VoiceRepositoryImpl @Inject constructor(
    private val yuanFangApi: YuanFangApi,
    private val socketClient: YuanFangSocketClient
) : VoiceRepository {

    override suspend fun processVoicePipeline(audioBytes: ByteArray, systemPrompt: String?): VoiceResult {
        var audioFile: File? = null
        try {
            audioFile = File.createTempFile("voice_", ".wav")
            audioFile.writeBytes(audioBytes)

            val audioPart = MultipartBody.Part.createFormData(
                "audio", audioFile.name,
                audioFile.asRequestBody("audio/wav".toMediaTypeOrNull())
            )

            val promptPart = systemPrompt?.toRequestBody("text/plain".toMediaTypeOrNull())

            val response = yuanFangApi.voicePipeline(audioPart, promptPart)

            val infrared = response.infrared?.let { ir ->
                InfraredCommand(device = ir.device, frequency = ir.frequency, pattern = ir.pattern, action = ir.action)
            }

            return VoiceResult(
                transcribedText = response.text,
                aiResponse = response.response,
                audioData = response.audio_data,
                source = response.source,
                infrared = infrared,
                success = response.success
            )
        } finally {
            audioFile?.delete()
        }
    }

    override suspend fun recognizeSpeech(audioBytes: ByteArray): String {
        var audioFile: File? = null
        try {
            audioFile = File.createTempFile("stt_", ".wav")
            audioFile.writeBytes(audioBytes)

            val audioPart = MultipartBody.Part.createFormData(
                "audio", audioFile.name,
                audioFile.asRequestBody("audio/wav".toMediaTypeOrNull())
            )

            val response = yuanFangApi.voiceStt(audioPart)
            return if (response.success) response.text else ""
        } finally {
            audioFile?.delete()
        }
    }

    override suspend fun synthesizeSpeech(text: String): ByteArray? {
        return try {
            val response = yuanFangApi.voiceTts(TtsRequest(text = text))
            if (response.isSuccessful) response.body()?.bytes() else null
        } catch (e: Exception) {
            null
        }
    }

    override suspend fun textChat(message: String, systemPrompt: String?): String {
        return try {
            val request = VoiceChatRequest(message = message, system_prompt = systemPrompt)
            val response = yuanFangApi.voiceChat(request)
            if (response.success) response.response else ""
        } catch (e: Exception) {
            ""
        }
    }

    override suspend fun processVisionVoice(audioBytes: ByteArray, imageBase64: String?): VoiceResult {
        var audioFile: File? = null
        try {
            audioFile = File.createTempFile("voice_", ".wav")
            audioFile.writeBytes(audioBytes)

            val audioPart = MultipartBody.Part.createFormData(
                "audio", audioFile.name,
                audioFile.asRequestBody("audio/wav".toMediaTypeOrNull())
            )

            val imagePart = imageBase64?.toRequestBody("text/plain".toMediaTypeOrNull())

            val maxTokensPart = "256".toRequestBody("text/plain".toMediaTypeOrNull())
            val useToolsPart = "true".toRequestBody("text/plain".toMediaTypeOrNull())

            val response = yuanFangApi.visionVoicePipeline(audioPart, imagePart, maxTokensPart, useToolsPart)

            val infrared = response.infrared?.let { ir ->
                InfraredCommand(device = ir.device, frequency = ir.frequency, pattern = ir.pattern, action = ir.action)
            }

            return VoiceResult(
                transcribedText = response.text,
                aiResponse = response.response,
                audioData = response.audio_data,
                source = response.source,
                infrared = infrared,
                success = response.success
            )
        } finally {
            audioFile?.delete()
        }
    }

    override val streamChunks: Flow<String> = socketClient.chatChunks
    override val streamDone: Flow<String> = socketClient.chatDone
}