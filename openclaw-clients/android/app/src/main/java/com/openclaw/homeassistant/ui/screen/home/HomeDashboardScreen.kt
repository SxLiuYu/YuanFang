package com.openclaw.homeassistant.ui.screen.home

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavHostController
import com.openclaw.homeassistant.domain.model.DeviceState
import com.openclaw.homeassistant.domain.repository.HomeRepository
import com.openclaw.homeassistant.ui.theme.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeDashboardScreen(
    navController: NavHostController,
    viewModel: HomeDashboardViewModel = hiltViewModel()
) {
    val devices by viewModel.devices.collectAsState()
    val scenes by viewModel.scenes.collectAsState()
    val isConnected by viewModel.isConnected.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("智能家居", color = DeepSeaAccent) },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = DeepSeaSurface)
            )
        }
    ) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding).padding(12.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(if (isConnected) "HA 已连接" else "HA 未连接", style = MaterialTheme.typography.bodySmall, color = if (isConnected) DeepSeaSuccess else DeepSeaWarning)
                TextButton(onClick = { viewModel.refreshDevices() }) { Text("刷新", color = DeepSeaAccent) }
            }

            Row(modifier = Modifier.fillMaxWidth().padding(vertical = 8.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                scenes.forEach { scene ->
                    FilledTonalButton(
                        onClick = { viewModel.activateScene(scene.entityId) },
                        modifier = Modifier.height(40.dp),
                        colors = ButtonDefaults.filledTonalButtonColors(containerColor = DeepSeaSurfaceVariant)
                    ) { Text(scene.name, style = MaterialTheme.typography.labelMedium) }
                }
            }

            LazyVerticalGrid(
                columns = GridCells.Fixed(2),
                modifier = Modifier.fillMaxSize().weight(1f),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp)
            ) {
                items(devices) { device ->
                    DeviceCard(device = device, onToggle = { viewModel.toggleDevice(device) })
                }
            }
        }
    }
}

@Composable
fun DeviceCard(device: DeviceState, onToggle: () -> Unit) {
    val stateColor = when (device.state) {
        "on" -> DeepSeaSuccess
        "off" -> DeepSeaTextMuted
        else -> DeepSeaWarning
    }
    Card(
        modifier = Modifier.fillMaxWidth().height(80.dp),
        colors = CardDefaults.cardColors(containerColor = DeepSeaCard),
        onClick = onToggle
    ) {
        Row(modifier = Modifier.fillMaxSize().padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Column(modifier = Modifier.weight(1f)) {
                Text(device.name, style = MaterialTheme.typography.titleMedium, color = DeepSeaTextPrimary, maxLines = 1)
                Text("${device.domain} · ${device.room}", style = MaterialTheme.typography.bodySmall, color = DeepSeaTextMuted, maxLines = 1)
            }
            Text(device.state, style = MaterialTheme.typography.labelLarge, color = stateColor)
        }
    }
}

@HiltViewModel
class HomeDashboardViewModel @Inject constructor(
    private val homeRepository: HomeRepository
) : ViewModel() {

    private val _devices = MutableStateFlow<List<DeviceState>>(emptyList())
    val devices = _devices.asStateFlow()

    private val _scenes = MutableStateFlow<List<DeviceState>>(emptyList())
    val scenes = _scenes.asStateFlow()

    private val _isConnected = MutableStateFlow(false)
    val isConnected = _isConnected.asStateFlow()

    init {
        viewModelScope.launch {
            homeRepository.getLocalDevices().collect { _devices.value = it }
        }
        refreshDevices()
    }

    fun refreshDevices() {
        viewModelScope.launch {
            try {
                _isConnected.value = homeRepository.checkHaConnection()
                homeRepository.refreshDevices()
                _scenes.value = homeRepository.getScenes()
            } catch (e: Exception) {
                _isConnected.value = false
            }
        }
    }

    fun toggleDevice(device: DeviceState) {
        viewModelScope.launch {
            val action = if (device.state == "on") "off" else "on"
            homeRepository.controlDevice(device.entityId, action)
            refreshDevices()
        }
    }

    fun activateScene(entityId: String) {
        viewModelScope.launch {
            homeRepository.activateScene(entityId)
        }
    }
}