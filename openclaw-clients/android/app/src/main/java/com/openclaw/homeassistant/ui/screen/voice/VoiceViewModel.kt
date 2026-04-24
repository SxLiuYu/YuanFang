package com.openclaw.homeassistant.ui.screen.voice

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.openclaw.homeassistant.domain.repository.VoiceRepository
import com.openclaw.homeassistant.util.AudioRecorder
import com.openclaw.homeassistant.util.AudioPlayer
import com.openclaw.homeassistant.util.IrTransmitter
import dagger.hilt.android.lifecycle.HiltViewModel
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class VoiceViewModel @Inject constructor(
    private val voiceRepository: VoiceRepository,
    @ApplicationContext private val context: Context
) : ViewModel() {

    private val _isListening = MutableStateFlow(false)
    val isListening = _isListening.asStateFlow()

    private val _transcribedText = MutableStateFlow("")
    val transcribedText = _transcribedText.asStateFlow()

    private val _aiResponse = MutableStateFlow("")
    val aiResponse = _aiResponse.asStateFlow()

    private val _hasInfrared = MutableStateFlow(false)
    val hasInfrared = _hasInfrared.asStateFlow()

    private val _infraredInfo = MutableStateFlow("")
    val infraredInfo = _infraredInfo.asStateFlow()

    private val _isProcessing = MutableStateFlow(false)
    val isProcessing = _isProcessing.asStateFlow()

    private val audioRecorder = AudioRecorder()
    private val audioPlayer = AudioPlayer()
    private val irTransmitter = IrTransmitter(context)

    fun toggleListening() {
        if (_isListening.value) {
            stopListening()
        } else {
            startListening()
        }
    }

    private fun startListening() {
        // 用户开始说话，停止任何正在播放的回答
        audioPlayer.stop()
        _isListening.value = true
        _transcribedText.value = ""
        _aiResponse.value = ""
        _hasInfrared.value = false
        _infraredInfo.value = ""
        audioRecorder.startRecording()
    }

    private fun stopListening() {
        _isListening.value = false
        val audioBytes = audioRecorder.stopRecording()
        if (audioBytes != null && audioBytes.isNotEmpty()) {
            processVoice(audioBytes)
        } else {
            audioRecorder.cancel()
        }
    }

    private fun processVoice(audioBytes: ByteArray) {
        _isProcessing.value = true
        viewModelScope.launch {
            try {
                val result = voiceRepository.processVoicePipeline(audioBytes, null)
                _transcribedText.value = result.transcribedText
                _aiResponse.value = result.aiResponse

                if (result.audioData != null) {
                    val audioBytes = android.util.Base64.decode(result.audioData, android.util.Base64.DEFAULT)
                    audioPlayer.play(audioBytes)
                }

                if (result.infrared != null) {
                    _hasInfrared.value = true
                    _infraredInfo.value = "${result.infrared.device} - ${result.infrared.action}"
                    irTransmitter.transmit(result.infrared)
                }
            } catch (e: Exception) {
                _aiResponse.value = "处理失败: ${e.message}"
            } finally {
                _isProcessing.value = false
            }
        }
    }

    override fun onCleared() {
        super.onCleared()
        audioPlayer.stop()
        audioPlayer.release()
        if (_isListening.value) {
            audioRecorder.cancel()
        }
    }
}