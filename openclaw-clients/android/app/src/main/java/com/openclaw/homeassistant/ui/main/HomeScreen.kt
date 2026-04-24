package com.openclaw.homeassistant.ui.main

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavHostController
import com.openclaw.homeassistant.ui.navigation.Route
import com.openclaw.homeassistant.ui.theme.*

data class FeatureCard(
    val title: String,
    val icon: String,
    val route: Route,
    val description: String
)

val featureCards = listOf(
    FeatureCard("AI 对话", "💬", Route.Chat, "与元芳智能对话"),
    FeatureCard("语音助手", "🎙", Route.Voice, "语音唤醒与交互"),
    FeatureCard("智能家居", "🏠", Route.HomeDashboard, "控制家中设备"),
    FeatureCard("性格状态", "🧠", Route.Personality, "元芳的心情与特质"),
    FeatureCard("记忆搜索", "🔍", Route.Memory, "搜索过往记忆"),
    FeatureCard("技能工具", "⚡", Route.Skills, "查看与创建技能"),
    FeatureCard("自动化", "⚙", Route.Automation, "规则与自动执行"),
    FeatureCard("设置", "🔧", Route.Settings, "服务器与配置")
)

@Composable
fun HomeScreen(
    navController: NavHostController,
    viewModel: HomeViewModel = hiltViewModel()
) {
    val personalityState by viewModel.personalityState.collectAsState()
    val isConnected by viewModel.isConnected.collectAsState()

    Column(
        modifier = Modifier.fillMaxSize().padding(16.dp),
        verticalArrangement = Arrangement.spacedBy(12.dp)
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = "元芳 · 智能家居",
                style = MaterialTheme.typography.headlineLarge,
                color = DeepSeaAccent
            )
            if (personalityState != null) {
                AssistChip(
                    onClick = { navController.navigate(Route.Personality.route) },
                    label = { Text(personalityState!!.mood, color = MoodCalm) },
                    modifier = Modifier.height(36.dp)
                )
            }
        }

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp),
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(
                text = if (isConnected) "已连接" else "未连接",
                style = MaterialTheme.typography.bodySmall,
                color = if (isConnected) DeepSeaSuccess else DeepSeaWarning
            )
            if (personalityState != null) {
                Text(
                    text = "能量: ${(personalityState!!.energy * 100).toInt()}%",
                    style = MaterialTheme.typography.bodySmall,
                    color = DeepSeaTextMuted
                )
            }
        }

        LazyVerticalGrid(
            columns = GridCells.Fixed(2),
            modifier = Modifier.fillMaxWidth().weight(1f),
            horizontalArrangement = Arrangement.spacedBy(12.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp)
        ) {
            items(featureCards) { card ->
                FeatureCardItem(card = card, onClick = {
                    navController.navigate(card.route.route)
                })
            }
        }

        FilledTonalButton(
            onClick = { navController.navigate(Route.Voice.route) },
            modifier = Modifier.fillMaxWidth().height(56.dp),
            colors = ButtonDefaults.filledTonalButtonColors(
                containerColor = DeepSeaAccent,
                contentColor = DeepSeaBackground
            )
        ) {
            Text("🎙 语音助手", style = MaterialTheme.typography.titleMedium)
        }
    }
}

@Composable
fun FeatureCardItem(card: FeatureCard, onClick: () -> Unit) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth().height(100.dp),
        colors = CardDefaults.cardColors(containerColor = DeepSeaCard),
        shape = CardDefaults.shape
    ) {
        Column(
            modifier = Modifier.fillMaxSize().padding(12.dp),
            verticalArrangement = Arrangement.Center,
            horizontalAlignment = Alignment.Start
        ) {
            Text(text = "${card.icon} ${card.title}", style = MaterialTheme.typography.titleMedium, color = DeepSeaTextPrimary)
            Text(text = card.description, style = MaterialTheme.typography.bodySmall, color = DeepSeaTextMuted)
        }
    }
}