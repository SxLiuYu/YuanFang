package com.openclaw.homeassistant.ui.screen.memory

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import androidx.navigation.NavHostController
import com.openclaw.homeassistant.domain.model.MemoryEntry
import com.openclaw.homeassistant.domain.repository.MemoryRepository
import com.openclaw.homeassistant.ui.theme.*
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun MemoryScreen(navController: NavHostController, viewModel: MemoryViewModel = hiltViewModel()) {
    val searchQuery by viewModel.searchQuery.collectAsState()
    val results by viewModel.results.collectAsState()

    Scaffold(topBar = { TopAppBar(title = { Text("记忆搜索", color = DeepSeaAccent) }, colors = TopAppBarDefaults.topAppBarColors(containerColor = DeepSeaSurface)) }) { padding ->
        Column(modifier = Modifier.fillMaxSize().padding(padding).padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            OutlinedTextField(value = searchQuery, onValueChange = { viewModel.updateQuery(it) }, modifier = Modifier.fillMaxWidth(), placeholder = { Text("搜索记忆...", color = DeepSeaTextMuted) }, shape = RoundedCornerShape(24.dp), colors = OutlinedTextFieldDefaults.colors(focusedBorderColor = DeepSeaAccent, unfocusedBorderColor = DeepSeaDivider, focusedContainerColor = DeepSeaSurfaceVariant, unfocusedContainerColor = DeepSeaSurfaceVariant, cursorColor = DeepSeaAccent, focusedTextColor = DeepSeaTextPrimary))
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                FilledTonalButton(onClick = { viewModel.search() }, colors = ButtonDefaults.filledTonalButtonColors(containerColor = DeepSeaAccent, contentColor = DeepSeaBackground)) { Text("搜索") }
                FilledTonalButton(onClick = { viewModel.createSnapshot() }, colors = ButtonDefaults.filledTonalButtonColors(containerColor = DeepSeaSurfaceVariant)) { Text("创建快照") }
            }
            LazyColumn(modifier = Modifier.fillMaxSize().weight(1f), verticalArrangement = Arrangement.spacedBy(8.dp)) {
                items(results) { entry ->
                    MemoryCard(entry)
                }
            }
        }
    }
}

@Composable
fun MemoryCard(entry: MemoryEntry) {
    Card(modifier = Modifier.fillMaxWidth(), colors = CardDefaults.cardColors(containerColor = DeepSeaCard)) {
        Column(modifier = Modifier.padding(12.dp)) {
            Text(entry.text, style = MaterialTheme.typography.bodyMedium, color = DeepSeaTextPrimary, maxLines = 3)
            Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Text("相似度: ${(entry.score * 100).toInt()}%", style = MaterialTheme.typography.labelSmall, color = DeepSeaAccent)
                if (entry.timestamp != null) Text(entry.timestamp, style = MaterialTheme.typography.labelSmall, color = DeepSeaTextMuted)
            }
        }
    }
}

@HiltViewModel
class MemoryViewModel @Inject constructor(private val repo: MemoryRepository) : ViewModel() {
    private val _searchQuery = MutableStateFlow("")
    val searchQuery = _searchQuery.asStateFlow()
    private val _results = MutableStateFlow<List<MemoryEntry>>(emptyList())
    val results = _results.asStateFlow()

    fun updateQuery(q: String) { _searchQuery.value = q }
    fun search() { viewModelScope.launch { try { _results.value = repo.search(_searchQuery.value, 10) } catch (_: Exception) {} } }
    fun createSnapshot() { viewModelScope.launch { try { repo.createSnapshot(null, null) } catch (_: Exception) {} } }
}