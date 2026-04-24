package com.openclaw.homeassistant.ui.screen.automation

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavHostController
import com.openclaw.homeassistant.domain.model.AutomationRule
import com.openclaw.homeassistant.domain.model.RuleCondition
import com.openclaw.homeassistant.domain.model.RuleAction
import com.openclaw.homeassistant.domain.repository.RulesRepository
import com.openclaw.homeassistant.ui.theme.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.Job
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AutomationScreen(navController: NavHostController, viewModel: AutomationViewModel = hiltViewModel()) {
    val rules by viewModel.rules.collectAsState()

    Scaffold(topBar = { TopAppBar(title = { Text("自动化", color = DeepSeaAccent) }, colors = TopAppBarDefaults.topAppBarColors(containerColor = DeepSeaSurface)) }) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilledTonalButton(onClick = { viewModel.syncRules() }, colors = ButtonDefaults.filledTonalButtonColors(containerColor = DeepSeaAccent, contentColor = DeepSeaBackground)) { Text("同步规则") }
                FilledTonalButton(onClick = { viewModel.addRule() }, colors = ButtonDefaults.filledTonalButtonColors(containerColor = DeepSeaSurfaceVariant)) { Text("+ 新规则") }
            }
            LazyColumn(modifier = Modifier.fillMaxSize().weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(rules) { rule ->
                    RuleCard(rule, onToggle = { viewModel.toggleRule(rule) })
                }
            }
        }
    }
}

@Composable
fun RuleCard(rule: AutomationRule, onToggle: () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = DeepSeaCard)) {
        Row(modifier = Modifier.fillMaxWidth().padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
            Column(modifier = Modifier.weight(1f)) {
                Text(rule.name, style = MaterialTheme.typography.titleMedium, color = DeepSeaTextPrimary)
                Text("触发: ${rule.condition.triggerType}", style = MaterialTheme.typography.bodySmall, color = DeepSeaTextMuted)
                if (rule.triggerCount > 0) Text("已触发 ${rule.triggerCount} 次", style = MaterialTheme.typography.labelSmall, color = DeepSeaAccent)
            }
            Switch(checked = rule.enabled, onCheckedChange = { onToggle() }, colors = SwitchDefaults.colors(checkedTrackColor = DeepSeaSuccess, uncheckedTrackColor = DeepSeaDivider))
        }
    }
}

@HiltViewModel
class AutomationViewModel @Inject constructor(private val repo: RulesRepository) : ViewModel() {
    private val _rules = MutableStateFlow<List<AutomationRule>>(emptyList())
    val rules = _rules.asStateFlow()
    private var rulesCollectionJob: Job? = null

    init { syncRules() }

    private fun collectRules() {
        rulesCollectionJob?.cancel()
        rulesCollectionJob = viewModelScope.launch {
            repo.getLocalRules().collect { _rules.value = it }
        }
    }

    fun syncRules() {
        viewModelScope.launch {
            try {
                repo.syncRules()
                collectRules()
            } catch (_: Exception) { }
        }
    }

    fun addRule() {
        viewModelScope.launch {
            try {
                repo.addRule(AutomationRule(
                    id = "rule_${System.currentTimeMillis()}",
                    name = "新规则",
                    condition = RuleCondition(triggerType = "time"),
                    actions = listOf(RuleAction(type = "notify"))
                )
                syncRules()
            } catch (_: Exception) { }
        }
    }

    fun toggleRule(rule: AutomationRule) {
        viewModelScope.launch {
            try {
                if (rule.enabled) repo.disableRule(rule.id) else repo.enableRule(rule.id)
                syncRules()
            } catch (_: Exception) { }
        }
    }
}