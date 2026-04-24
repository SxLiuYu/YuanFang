package com.openclaw.homeassistant.data.remote.socket

import com.openclaw.homeassistant.data.local.prefs.SecureConfig
import com.openclaw.homeassistant.data.remote.dto.InfraredDto
import com.openclaw.homeassistant.data.remote.dto.VoicePipelineResponse
import kotlinx.coroutines.channels.Channel
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.MutableSharedFlow
import kotlinx.coroutines.flow.asSharedFlow
import io.socket.client.IO
import io.socket.client.Socket
import io.socket.emitter.Emitter
import okhttp3.OkHttpClient
import org.json.JSONObject
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class YuanFangSocketClient @Inject constructor(
    private val okHttpClient: OkHttpClient,
    private val secureConfig: SecureConfig
) {
    private var socket: Socket? = null

    private val _chatChunks = MutableSharedFlow<String>(extraBufferCapacity = 64)
    val chatChunks: Flow<String> = _chatChunks.asSharedFlow()

    private val _chatDone = MutableSharedFlow<String>(extraBufferCapacity = 16)
    val chatDone: Flow<String> = _chatDone.asSharedFlow()

    private val _chatErrors = MutableSharedFlow<String>(extraBufferCapacity = 16)
    val chatErrors: Flow<String> = _chatErrors.asSharedFlow()

    private val _voiceResults = MutableSharedFlow<VoicePipelineResponse>(extraBufferCapacity = 16)
    val voiceResults: Flow<VoicePipelineResponse> = _voiceResults.asSharedFlow()

    private val _notifications = MutableSharedFlow<JSONObject>(extraBufferCapacity = 16)
    val notifications: Flow<JSONObject> = _notifications.asSharedFlow()

    private val _sensorRealtime = MutableSharedFlow<JSONObject>(extraBufferCapacity = 16)
    val sensorRealtime: Flow<JSONObject> = _sensorRealtime.asSharedFlow()

    private val _sceneUpdate = MutableSharedFlow<JSONObject>(extraBufferCapacity = 16)
    val sceneUpdate: Flow<JSONObject> = _sceneUpdate.asSharedFlow()

    private val _commands = MutableSharedFlow<JSONObject>(extraBufferCapacity = 16)
    val commands: Flow<JSONObject> = _commands.asSharedFlow()

    private val _connectionState = MutableSharedFlow<Boolean>(extraBufferCapacity = 1)
    val connectionState: Flow<Boolean> = _connectionState.asSharedFlow()

    fun connect() {
        if (socket != null && socket?.connected() == true) return

        val url = secureConfig.yuanfangUrl
        val options = IO.Options()
        options.transports = arrayOf("websocket")
        options.reconnection = true
        options.reconnectionAttempts = Int.MAX_VALUE
        options.reconnectionDelay = 5000
        options.timeout = 10000

        val token = secureConfig.deviceToken
        if (token.isNotEmpty()) {
            val auth = JSONObject().put("token", token)
            options.auth = mapOf("token" to token)
        }

        socket = IO.socket(url, options)

        socket?.on(Socket.EVENT_CONNECT, Emitter.Listener {
            _connectionState.tryEmit(true)
        })

        socket?.on(Socket.EVENT_DISCONNECT, Emitter.Listener {
            _connectionState.tryEmit(false)
        })

        socket?.on(Socket.EVENT_CONNECT_ERROR, Emitter.Listener { args ->
            _chatErrors.tryEmit(args?.firstOrNull()?.toString() ?: "Connection error")
        })

        socket?.on("chat_chunk", Emitter.Listener { args ->
            val json = args?.firstOrNull() as? JSONObject
            val content = json?.optString("content", "") ?: ""
            if (content.isNotEmpty()) {
                _chatChunks.tryEmit(content)
            }
        })

        socket?.on("chat_done", Emitter.Listener { args ->
            val json = args?.firstOrNull() as? JSONObject
            val emotion = json?.optString("emotion", "neutral") ?: "neutral"
            _chatDone.tryEmit(emotion)
        })

        socket?.on("chat_error", Emitter.Listener { args ->
            val json = args?.firstOrNull() as? JSONObject
            val error = json?.optString("error", "Unknown error") ?: "Unknown error"
            _chatErrors.tryEmit(error)
        })

        socket?.on("voice_result", Emitter.Listener { args ->
            val json = args?.firstOrNull() as? JSONObject
            if (json != null) {
                val infraredJson = json.optJSONObject("infrared")
                val infrared = if (infraredJson != null) InfraredDto(
                    device = infraredJson.optString("device", ""),
                    frequency = infraredJson.optInt("frequency", 0),
                    pattern = infraredJson.optString("pattern", ""),
                    action = infraredJson.optString("action", "")
                ) else null

                val result = VoicePipelineResponse(
                    success = json.optBoolean("success", true),
                    text = json.optString("text", ""),
                    response = json.optString("response", ""),
                    audio_data = json.optString("audio_data", null),
                    source = json.optString("source", "llm"),
                    infrared = infrared,
                    error = json.optString("error", null)
                )
                _voiceResults.tryEmit(result)
            }
        })

        socket?.on("notification", Emitter.Listener { args ->
            val json = args?.firstOrNull() as? JSONObject
            if (json != null) {
                _notifications.tryEmit(json)
            }
        })

        socket?.on("sensor_realtime", Emitter.Listener { args ->
            val json = args?.firstOrNull() as? JSONObject
            if (json != null) {
                _sensorRealtime.tryEmit(json)
            }
        })

        socket?.on("scene_update", Emitter.Listener { args ->
            val json = args?.firstOrNull() as? JSONObject
            if (json != null) {
                _sceneUpdate.tryEmit(json)
            }
        })

        socket?.on("command", Emitter.Listener { args ->
            val json = args?.firstOrNull() as? JSONObject
            if (json != null) {
                _commands.tryEmit(json)
            }
        })

        socket?.on("chat_message", Emitter.Listener { args ->
            val json = args?.firstOrNull() as? JSONObject
            if (json != null) {
                _notifications.tryEmit(json)
            }
        })

        socket?.connect()
    }

    fun disconnect() {
        socket?.disconnect()
        socket?.off()
        socket = null
    }

    fun sendVoiceInput(audioData: ByteArray) {
        val json = JSONObject()
        json.put("audio", android.util.Base64.encodeToString(audioData, android.util.Base64.NO_WRAP))
        socket?.emit("voice_input", json)
    }

    fun sendMessage(message: String) {
        socket?.emit("message", JSONObject().put("text", message))
    }

    fun sendPing() {
        socket?.emit("ping")
    }

    fun registerNode(nodeId: String, deviceInfo: JSONObject) {
        val json = JSONObject()
        json.put("type", "register")
        json.put("node_id", nodeId)
        json.put("device", deviceInfo)
        socket?.emit("register", json)
    }

    fun sendSensorUpdate(sensorData: JSONObject) {
        socket?.emit("sensor_update", sensorData)
    }

    fun sendWakeRegister(nodeId: String, platform: String) {
        val json = JSONObject()
        json.put("type", "wake_register")
        json.put("node_id", nodeId)
        json.put("platform", platform)
        socket?.emit("wake_register", json)
    }

    fun isConnected(): Boolean = socket?.connected() == true
}