package com.openclaw.homeassistant.ui.screen.chat

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.alpha
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.navigation.NavHostController
import com.openclaw.homeassistant.domain.model.ChatMessage
import com.openclaw.homeassistant.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun ChatScreen(
    navController: NavHostController,
    sessionId: String = "default",
    viewModel: ChatViewModel = hiltViewModel()
) {
    val messages by viewModel.messages.collectAsState()
    val inputText by viewModel.inputText.collectAsState()
    val isLoading by viewModel.isLoading.collectAsState()
    val personalityState by viewModel.personalityState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Row(verticalAlignment = Alignment.CenterVertically) {
                        Text("元芳对话", color = DeepSeaAccent)
                        if (personalityState != null) {
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(
                                text = personalityState!!.mood,
                                style = MaterialTheme.typography.labelSmall,
                                color = MoodCalm,
                                modifier = Modifier.alpha(0.7f)
                            )
                        }
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = DeepSeaSurface,
                    titleContentColor = DeepSeaTextPrimary
                ),
                actions = {
                    IconButton(onClick = { viewModel.createNewSession() }) {
                        Text("+", color = DeepSeaAccent)
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier.fillMaxSize().padding(padding)
        ) {
            LazyColumn(
                modifier = Modifier.fillMaxSize().weight(1f).padding(horizontal = 12.dp),
                verticalArrangement = Arrangement.spacedBy(8.dp),
                reverseLayout = false
            ) {
                items(messages, key = { it.id }) { message ->
                    ChatBubble(message = message)
                }
                if (isLoading) {
                    item {
                        Row(
                            modifier = Modifier.fillMaxWidth().padding(8.dp),
                            horizontalArrangement = Arrangement.Start
                        ) {
                            Text("元芳正在思考...", style = MaterialTheme.typography.bodyMedium, color = DeepSeaAccent)
                        }
                    }
                }
            }

            Row(
                modifier = Modifier.fillMaxWidth().padding(12.dp),
                horizontalArrangement = Arrangement.spacedBy(8.dp),
                verticalAlignment = Alignment.CenterVertically
            ) {
                OutlinedTextField(
                    value = inputText,
                    onValueChange = { viewModel.updateInput(it) },
                    modifier = Modifier.weight(1f),
                    placeholder = { Text("输入消息...", color = DeepSeaTextMuted) },
                    shape = RoundedCornerShape(24.dp),
                    colors = OutlinedTextFieldDefaults.colors(
                        focusedBorderColor = DeepSeaAccent,
                        unfocusedBorderColor = DeepSeaDivider,
                        focusedContainerColor = DeepSeaSurfaceVariant,
                        unfocusedContainerColor = DeepSeaSurfaceVariant,
                        cursorColor = DeepSeaAccent,
                        focusedTextColor = DeepSeaTextPrimary,
                        unfocusedTextColor = DeepSeaTextPrimary
                    ),
                    maxLines = 3
                )
                FilledTonalButton(
                    onClick = { viewModel.sendMessage() },
                    enabled = inputText.isNotBlank() && !isLoading,
                    modifier = Modifier.height(48.dp),
                    colors = ButtonDefaults.filledTonalButtonColors(
                        containerColor = DeepSeaAccent,
                        contentColor = DeepSeaBackground
                    )
                ) {
                    Text("发送")
                }
            }
        }
    }
}

@Composable
fun ChatBubble(message: ChatMessage) {
    val isUser = message.role == "user"
    val alignment = if (isUser) Alignment.End else Alignment.Start
    val bgColor = if (isUser) DeepSeaPrimary else DeepSeaCard
    val textColor = if (isUser) DeepSeaTextPrimary else DeepSeaTextPrimary

    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = if (isUser) Arrangement.End else Arrangement.Start
    ) {
        Card(
            modifier = Modifier.fillMaxWidth(0.85f),
            colors = CardDefaults.cardColors(containerColor = bgColor),
            shape = RoundedCornerShape(
                topStart = if (isUser) 16.dp else 4.dp,
                topEnd = if (isUser) 4.dp else 16.dp,
                bottomStart = 16.dp,
                bottomEnd = 16.dp
            )
        ) {
            Column(modifier = Modifier.padding(12.dp)) {
                Text(text = message.content, style = MaterialTheme.typography.bodyLarge, color = textColor)
                if (!isUser && message.skillUsed != null) {
                    Text(
                        text = "技能: ${message.skillUsed}",
                        style = MaterialTheme.typography.labelSmall,
                        color = DeepSeaTextMuted,
                        modifier = Modifier.alpha(0.6f)
                    )
                }
            }
        }
    }
}