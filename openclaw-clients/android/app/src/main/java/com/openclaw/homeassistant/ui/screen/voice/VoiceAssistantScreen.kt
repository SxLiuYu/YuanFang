package com.openclaw.homeassistant.ui.screen.voice

import androidx.compose.animation.*
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.scale
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavHostController
import com.openclaw.homeassistant.ui.theme.*

@Composable
fun VoiceAssistantScreen(
    navController: NavHostController,
    viewModel: VoiceViewModel = hiltViewModel()
) {
    val isListening by viewModel.isListening.collectAsState()
    val transcribedText by viewModel.transcribedText.collectAsState()
    val aiResponse by viewModel.aiResponse.collectAsState()
    val hasInfrared by viewModel.hasInfrared.collectAsState()
    val infraredInfo by viewModel.infraredInfo.collectAsState()

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.Center,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text("元芳语音助手", style = MaterialTheme.typography.headlineMedium, color = DeepSeaAccent)

        Spacer(modifier = Modifier.height(32.dp))

        AnimatedContent(targetState = isListening, transitionSpec = { fadeIn() togetherWith fadeOut() }) { listening ->
            Box(
                modifier = Modifier.size(120.dp),
                contentAlignment = Alignment.Center
            ) {
if (isListening) {
                    Surface(
                        modifier = Modifier.fillMaxSize().scale(1.1f),
                        shape = CircleShape,
                        color = DeepSeaAccentWarm
                    ) {}
                }
                Surface(
                    modifier = Modifier.size(if (listening) 100.dp else 80.dp),
                    shape = CircleShape,
                    color = if (listening) DeepSeaAccentWarm else DeepSeaPrimary,
                    onClick = { viewModel.toggleListening() }
                ) {
                    Box(contentAlignment = Alignment.Center) {
                        Text(
                            if (listening) "🛑" else "🎙",
                            style = MaterialTheme.typography.headlineLarge,
                            color = DeepSeaTextPrimary
                        )
                    }
                }
            }
        }

        if (isListening) {
            Text("正在聆听...", style = MaterialTheme.typography.bodyMedium, color = DeepSeaAccent)
        }

        Spacer(modifier = Modifier.height(24.dp))

        if (transcribedText.isNotEmpty()) {
            Card(
                modifier = Modifier.fillMaxWidth(),
                colors = CardDefaults.cardColors(containerColor = DeepSeaCard)
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text("你说:", style = MaterialTheme.typography.labelMedium, color = DeepSeaTextMuted)
                    Text(transcribedText, style = MaterialTheme.typography.bodyLarge, color = DeepSeaTextPrimary)
                }
            }
        }

        if (aiResponse.isNotEmpty()) {
            Card(
                modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                colors = CardDefaults.cardColors(containerColor = DeepSeaSurfaceVariant)
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text("元芳:", style = MaterialTheme.typography.labelMedium, color = DeepSeaAccent)
                    Text(aiResponse, style = MaterialTheme.typography.bodyLarge, color = DeepSeaTextPrimary)
                }
            }
        }

        if (hasInfrared) {
            Card(
                modifier = Modifier.fillMaxWidth().padding(top = 8.dp),
                colors = CardDefaults.cardColors(containerColor = DeepSeaWarning.copy(alpha = 0.2f))
            ) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text("红外指令:", style = MaterialTheme.typography.labelMedium, color = DeepSeaAccentWarm)
                    Text(infraredInfo, style = MaterialTheme.typography.bodyMedium, color = DeepSeaAccentWarm)
                }
            }
        }
    }
}