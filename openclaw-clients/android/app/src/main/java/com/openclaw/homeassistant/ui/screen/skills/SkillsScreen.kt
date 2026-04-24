package com.openclaw.homeassistant.ui.screen.skills

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavHostController
import com.openclaw.homeassistant.domain.model.Skill
import com.openclaw.homeassistant.domain.repository.SkillsRepository
import com.openclaw.homeassistant.ui.theme.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SkillsScreen(navController: NavHostController, viewModel: SkillsViewModel = hiltViewModel()) {
    val skills by viewModel.skills.collectAsState()

    Scaffold(topBar = { TopAppBar(title = { Text("技能工具", color = DeepSeaAccent) }, colors = TopAppBarDefaults.topAppBarColors(containerColor = DeepSeaSurface)) }) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilledTonalButton(onClick = { viewModel.refresh() }, colors = ButtonDefaults.filledTonalButtonColors(containerColor = DeepSeaAccent, contentColor = DeepSeaBackground)) { Text("刷新") }
                FilledTonalButton(onClick = { viewModel.registerNewSkill() }, colors = ButtonDefaults.filledTonalButtonColors(containerColor = DeepSeaSurfaceVariant)) { Text("+ 创建新技能") }
            }
            LazyColumn(modifier = Modifier.fillMaxSize().weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(skills) { skill ->
                    SkillCard(skill)
                }
            }
        }
    }
}

@Composable
fun SkillCard(skill: Skill) {
    Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = DeepSeaCard)) {
        Column(modifier = Modifier.padding(12.dp)) {
            Text(skill.name, style = MaterialTheme.typography.titleMedium, color = DeepSeaAccent)
            if (skill.description != null) Text(skill.description, style = MaterialTheme.typography.bodyMedium, color = DeepSeaTextSecondary, maxLines = 2)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                if (skill.category != null) Text(skill.category, style = MaterialTheme.typography.labelSmall, color = DeepSeaTextMuted)
                if (skill.qualityScore != null) Text("评分: ${skill.qualityScore}", style = MaterialTheme.typography.labelSmall, color = DeepSeaAccent)
            }
        }
    }
}

@HiltViewModel
class SkillsViewModel @Inject constructor(private val repo: SkillsRepository) : ViewModel() {
    private val _skills = MutableStateFlow<List<Skill>>(emptyList())
    val skills = _skills.asStateFlow()

    init { refresh() }

    fun refresh() { viewModelScope.launch { try { _skills.value = repo.getSkills(null) } catch (_: Exception) {} } }
    fun registerNewSkill() { viewModelScope.launch { try { repo.registerSkill("新技能_${System.currentTimeMillis()}", null, "general", null); refresh() } catch (_: Exception) {} } }
}