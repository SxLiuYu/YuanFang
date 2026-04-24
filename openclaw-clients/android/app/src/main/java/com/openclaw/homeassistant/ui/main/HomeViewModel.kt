package com.openclaw.homeassistant.ui.main

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.openclaw.homeassistant.data.remote.socket.YuanFangSocketClient
import com.openclaw.homeassistant.domain.model.PersonalityState
import com.openclaw.homeassistant.domain.repository.PersonalityRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class HomeViewModel @Inject constructor(
    private val personalityRepository: PersonalityRepository,
    private val socketClient: YuanFangSocketClient
) : ViewModel() {

    private val _personalityState = MutableStateFlow<PersonalityState?>(null)
    val personalityState = _personalityState.asStateFlow()

    private val _isConnected = MutableStateFlow(false)
    val isConnected = _isConnected.asStateFlow()

    init {
        viewModelScope.launch {
            socketClient.connect()
            socketClient.connectionState.collect { connected ->
                _isConnected.value = connected
            }
        }
        viewModelScope.launch {
            try {
                _personalityState.value = personalityRepository.getStatus()
            } catch (e: Exception) {
                _personalityState.value = PersonalityState()
            }
        }
    }

    override fun onCleared() {
        super.onCleared()
        socketClient.disconnect()
    }
}