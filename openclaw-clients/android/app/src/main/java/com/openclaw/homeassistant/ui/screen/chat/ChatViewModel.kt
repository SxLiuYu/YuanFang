package com.openclaw.homeassistant.ui.screen.chat

import androidx.lifecycle.SavedStateHandle
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.openclaw.homeassistant.domain.model.ChatMessage
import com.openclaw.homeassistant.domain.model.PersonalityState
import com.openclaw.homeassistant.domain.repository.ChatRepository
import com.openclaw.homeassistant.domain.repository.PersonalityRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class ChatViewModel @Inject constructor(
    private val chatRepository: ChatRepository,
    private val personalityRepository: PersonalityRepository,
    savedStateHandle: SavedStateHandle
) : ViewModel() {

    private val _messages = MutableStateFlow<List<ChatMessage>>(emptyList())
    val messages = _messages.asStateFlow()

    private val _inputText = MutableStateFlow("")
    val inputText = _inputText.asStateFlow()

    private val _isLoading = MutableStateFlow(false)
    val isLoading = _isLoading.asStateFlow()

    private val _personalityState = MutableStateFlow<PersonalityState?>(null)
    val personalityState = _personalityState.asStateFlow()

    private var currentSessionId = savedStateHandle.get<String>("sessionId") ?: "default"
    private var messageCollectionJob: Job? = null

    init {
        viewModelScope.launch {
            try {
                _personalityState.value = personalityRepository.getStatus()
            } catch (e: Exception) {
                _personalityState.value = PersonalityState()
            }
        }
        collectMessages(currentSessionId)
    }

    private fun collectMessages(sessionId: String) {
        messageCollectionJob?.cancel()
        messageCollectionJob = viewModelScope.launch {
            chatRepository.getMessages(sessionId).collect { msgs ->
                _messages.value = msgs
            }
        }
    }

    fun updateInput(text: String) {
        _inputText.value = text
    }

    fun sendMessage() {
        val text = _inputText.value
        if (text.isBlank()) return
        _inputText.value = ""
        _isLoading.value = true

        viewModelScope.launch {
            try {
                chatRepository.sendMessage(currentSessionId, text)
            } catch (e: Exception) {
                _messages.value = _messages.value + ChatMessage(
                    sessionId = currentSessionId,
                    role = "system",
                    content = "发送失败: ${e.message}",
                    timestamp = System.currentTimeMillis()
                )
            } finally {
                _isLoading.value = false
            }
        }
    }

    fun createNewSession() {
        viewModelScope.launch {
            val session = chatRepository.createSession("新会话 ${System.currentTimeMillis()}")
            currentSessionId = session.id
            collectMessages(currentSessionId)
        }
    }
}