package com.openclaw.homeassistant.ui.screen.settings

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavHostController
import com.openclaw.homeassistant.data.local.prefs.SecureConfig
import com.openclaw.homeassistant.domain.repository.DeviceRepository
import com.openclaw.homeassistant.ui.theme.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(navController: NavHostController, viewModel: SettingsViewModel = hiltViewModel()) {
    val yuanfangUrl by viewModel.yuanfangUrl.collectAsState()
    val jarvisUrl by viewModel.jarvisUrl.collectAsState()
    val defaultModel by viewModel.defaultModel.collectAsState()
    val isDeviceConfirmed by viewModel.isDeviceConfirmed.collectAsState()

    Scaffold(topBar = { TopAppBar(title = { Text("设置", color = DeepSeaAccent) }, colors = TopAppBarDefaults.topAppBarColors(containerColor = DeepSeaSurface)) }) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding).padding(16.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            Text("服务器配置", style = MaterialTheme.typography.titleMedium, color = DeepSeaTextPrimary)
            OutlinedTextField(value = yuanfangUrl, onValueChange = { viewModel.updateYuanfangUrl(it) }, modifier = Modifier.fillMaxWidth(), label = { Text("YuanFang 服务器 URL") }, colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = DeepSeaAccent, unfocusedBorderColor = DeepSeaDivider, focusedTextColor = DeepSeaTextPrimary))
            OutlinedTextField(value = jarvisUrl, onValueChange = { viewModel.updateJarvisUrl(it) }, modifier = Modifier.fillMaxWidth(), label = { Text("Jarvis 服务器 URL") }, colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = DeepSeaAccent, unfocusedBorderColor = DeepSeaDivider, focusedTextColor = DeepSeaTextPrimary))
            OutlinedTextField(value = defaultModel, onValueChange = { viewModel.updateDefaultModel(it) }, modifier = Modifier.fillMaxWidth(), label = { Text("默认模型") }, colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = DeepSeaAccent, unfocusedBorderColor = DeepSeaDivider, focusedTextColor = DeepSeaTextPrimary))

            Text("设备状态", style = MaterialTheme.typography.titleMedium, color = DeepSeaTextPrimary)
            Text(if (isDeviceConfirmed) "设备已认证" else "设备未认证", style = MaterialTheme.typography.bodyMedium, color = if (isDeviceConfirmed) DeepSeaSuccess else DeepSeaWarning)
            if (!isDeviceConfirmed) {
                FilledTonalButton(onClick = { viewModel.confirmDevice() }, colors = ButtonDefaults.filledTonalButtonColors(containerColor = DeepSeaAccent, contentColor = DeepSeaBackground)) { Text("认证设备") }
            }

            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilledTonalButton(onClick = { viewModel.save() }, colors = ButtonDefaults.filledTonalButtonColors(containerColor = DeepSeaSuccess)) { Text("保存") }
                OutlinedButton(onClick = { viewModel.logout() }, colors = ButtonDefaults.outlinedButtonColors(contentColor = DeepSeaError)) { Text("退出登录") }
            }
        }
    }
}

@HiltViewModel
class SettingsViewModel @Inject constructor(
    private val secureConfig: SecureConfig,
    private val deviceRepo: DeviceRepository
) : ViewModel() {
    private val _yuanfangUrl = MutableStateFlow(secureConfig.yuanfangUrl)
    val yuanfangUrl = _yuanfangUrl.asStateFlow()
    private val _jarvisUrl = MutableStateFlow(secureConfig.jarvisUrl)
    val jarvisUrl = _jarvisUrl.asStateFlow()
    private val _defaultModel = MutableStateFlow(secureConfig.defaultModel)
    val defaultModel = _defaultModel.asStateFlow()
    private val _isDeviceConfirmed = MutableStateFlow(secureConfig.isDeviceConfirmed)
    val isDeviceConfirmed = _isDeviceConfirmed.asStateFlow()

    fun updateYuanfangUrl(url: String) { _yuanfangUrl.value = url }
    fun updateJarvisUrl(url: String) { _jarvisUrl.value = url }
    fun updateDefaultModel(model: String) { _defaultModel.value = model }
    fun save() { secureConfig.yuanfangUrl = _yuanfangUrl.value; secureConfig.jarvisUrl = _jarvisUrl.value; secureConfig.defaultModel = _defaultModel.value }
    fun logout() { viewModelScope.launch { deviceRepo.logout(); _isDeviceConfirmed.value = false } }
    fun confirmDevice() { viewModelScope.launch { deviceRepo.confirmDevice("", ""); _isDeviceConfirmed.value = true } }
}