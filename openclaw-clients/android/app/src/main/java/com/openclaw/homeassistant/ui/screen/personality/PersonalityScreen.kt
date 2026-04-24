package com.openclaw.homeassistant.ui.screen.personality

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavHostController
import com.openclaw.homeassistant.domain.model.PersonalityState
import com.openclaw.homeassistant.domain.repository.PersonalityRepository
import com.openclaw.homeassistant.ui.theme.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun PersonalityScreen(navController: NavHostController, viewModel: PersonalityViewModel = hiltViewModel()) {
    val state by viewModel.state.collectAsState()

    Scaffold(topBar = { TopAppBar(title = { Text("性格状态", color = DeepSeaAccent) }, colors = TopAppBarDefaults.topAppBarColors(containerColor = DeepSeaSurface)) }) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding).padding(16.dp).verticalScroll(rememberScrollState()), verticalArrangement = Arrangement.spacedBy(16.dp)) {
            if (state != null) {
                Text("${state!!.name} · ${state!!.mood}", style = MaterialTheme.typography.headlineMedium, color = DeepSeaAccent)
                Row(horizontalArrangement = Arrangement.spacedBy(16.dp)) {
                    ProgressCard("能量", state!!.energy, DeepSeaAccent)
                    ProgressCard("压力", state!!.stress, DeepSeaWarning)
                }
                Text("核心特质", style = MaterialTheme.typography.titleMedium, color = DeepSeaTextPrimary)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    TraitChip("好奇", state!!.traits.curiosity)
                    TraitChip("忠诚", state!!.traits.loyalty)
                    TraitChip("趣味", state!!.traits.playfulness)
                    TraitChip("谨慎", state!!.traits.caution)
                    TraitChip("主动", state!!.traits.initiative)
                }
                Text("进化次数: ${state!!.evolutionCount}", style = MaterialTheme.typography.bodyMedium, color = DeepSeaTextMuted)
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    FilledTonalButton(onClick = { viewModel.driftMood() }, colors = ButtonDefaults.filledTonalButtonColors(containerColor = DeepSeaSurfaceVariant)) { Text("随机漂移") }
                    FilledTonalButton(onClick = { viewModel.refresh() }, colors = ButtonDefaults.filledTonalButtonColors(containerColor = DeepSeaSurfaceVariant)) { Text("刷新") }
                }
            } else {
                Text("加载中...", color = DeepSeaTextMuted)
            }
        }
    }
}

@Composable
fun ProgressCard(label: String, value: Double, color: androidx.compose.ui.graphics.Color) {
    Card(modifier = Modifier.width(160.dp).height(60.dp), colors = CardDefaults.cardColors(containerColor = DeepSeaCard)) {
        Column(modifier = Modifier.padding(12.dp)) {
            Text(label, style = MaterialTheme.typography.labelSmall, color = DeepSeaTextMuted)
            LinearProgressIndicator(progress = { value.toFloat() }, modifier = Modifier.fillMaxWidth(), color = color, trackColor = DeepSeaDivider)
        }
    }
}

@Composable
fun TraitChip(name: String, value: Double) {
    AssistChip(onClick = {}, label = { Text("$name ${(value * 100).toInt()}%", style = MaterialTheme.typography.labelSmall) }, modifier = Modifier.height(32.dp))
}

@HiltViewModel
class PersonalityViewModel @Inject constructor(private val repo: PersonalityRepository) : ViewModel() {
    private val _state = MutableStateFlow<PersonalityState?>(null)
    val state = _state.asStateFlow()

    init { refresh() }

    fun refresh() { viewModelScope.launch { try { _state.value = repo.getStatus() } catch (e: Exception) { _state.value = PersonalityState() } } }
    fun driftMood() { viewModelScope.launch { try { repo.driftMood(); refresh() } catch (_: Exception) {} } }
}