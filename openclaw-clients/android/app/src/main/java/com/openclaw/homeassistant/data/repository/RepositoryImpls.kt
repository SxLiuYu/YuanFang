package com.openclaw.homeassistant.data.repository

import com.openclaw.homeassistant.data.remote.api.YuanFangApi
import com.openclaw.homeassistant.data.remote.dto.*
import com.openclaw.homeassistant.domain.model.MemoryEntry
import com.openclaw.homeassistant.domain.repository.MemoryRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class MemoryRepositoryImpl @Inject constructor(
    private val yuanFangApi: YuanFangApi
) : MemoryRepository {

    override suspend fun search(query: String, topK: Int): List<MemoryEntry> {
        return yuanFangApi.memorySearch(query, topK).map { dto ->
            MemoryEntry(id = dto.id, text = dto.text, score = dto.score, timestamp = dto.timestamp)
        }
    }

    override suspend fun createSnapshot(sceneType: String?, note: String?): Boolean {
        val response = yuanFangApi.memorySnapshot(SnapshotRequest(scene_type = sceneType, note = note))
        return response.success
    }

    override suspend fun getEmotionalMemory(emotion: String?, topK: Int): List<MemoryEntry> {
        val response = yuanFangApi.memoryEmotional(emotion, topK)
        return response.memories?.map { dto ->
            MemoryEntry(id = dto.id, text = dto.text, score = dto.score, timestamp = dto.timestamp)
        } ?: emptyList()
    }

    override suspend fun getSceneMemory(type: String?, n: Int): List<MemoryEntry> {
        val response = yuanFangApi.memoryScene(type, n)
        return response.scenes?.mapNotNull { scene ->
            val id = scene["id"]?.toString() ?: return null
            val text = scene["text"]?.toString() ?: return null
            val score = (scene["score"] as? Number)?.toDouble() ?: 0.0
            MemoryEntry(id = id, text = text, score = score, timestamp = scene["timestamp"]?.toString())
        } ?: emptyList()
    }

    override suspend fun getMemoryReport(): Map<String, Any> {
        val response = yuanFangApi.memoryReport()
        return response.report ?: emptyMap()
    }
}

@Singleton
class PersonalityRepositoryImpl @Inject constructor(
    private val yuanFangApi: YuanFangApi
) : com.openclaw.homeassistant.domain.repository.PersonalityRepository {

    override suspend fun getStatus(): com.openclaw.homeassistant.domain.model.PersonalityState {
        val dto = yuanFangApi.personalityStatus()
        return com.openclaw.homeassistant.domain.model.PersonalityState(
            name = dto.name, mood = dto.mood, energy = dto.energy, stress = dto.stress,
            traits = com.openclaw.homeassistant.domain.model.PersonalityTraits(
                curiosity = dto.traits.curiosity, loyalty = dto.traits.loyalty,
                playfulness = dto.traits.playfulness, caution = dto.traits.caution,
                initiative = dto.traits.initiative
            ),
            evolutionCount = dto.evolution_count, lastUpdated = dto.last_updated
        )
    }

    override suspend fun updateMood(mood: String, energyDelta: Double, stressDelta: Double): com.openclaw.homeassistant.domain.model.PersonalityState {
        val response = yuanFangApi.updateMood(MoodUpdateRequest(mood = mood, energy_delta = energyDelta, stress_delta = stressDelta))
        return getStatus()
    }

    override suspend fun driftMood(): String {
        val response = yuanFangApi.driftMood()
        return response.new_mood
    }
}

@Singleton
class SkillsRepositoryImpl @Inject constructor(
    private val yuanFangApi: YuanFangApi
) : com.openclaw.homeassistant.domain.repository.SkillsRepository {

    override suspend fun getSkills(category: String?): List<com.openclaw.homeassistant.domain.model.Skill> {
        return yuanFangApi.getSkills(category).skills.map { dto ->
            com.openclaw.homeassistant.domain.model.Skill(
                id = dto.id, name = dto.name, description = dto.description,
                category = dto.category, triggerPatterns = dto.trigger_patterns,
                qualityScore = dto.quality_score
            )
        }
    }

    override suspend fun registerSkill(name: String, description: String?, category: String, triggerPatterns: List<String>?): String {
        val response = yuanFangApi.registerSkill(SkillRegisterRequest(name = name, description = description, category = category, trigger_patterns = triggerPatterns))
        return response.skill_id ?: ""
    }

    override suspend fun executeSkillSandbox(commands: List<Map<String, String>>): List<Map<String, Any>> {
        val response = yuanFangApi.executeSkillSandbox(SkillExecuteRequest(commands = commands))
        return response.results
    }

    override suspend fun getSkillsReport(): Map<String, Any> {
        val response = yuanFangApi.skillsReport()
        return response.report ?: emptyMap()
    }
}

@Singleton
class RulesRepositoryImpl @Inject constructor(
    private val yuanFangApi: YuanFangApi,
    private val automationRuleDao: com.openclaw.homeassistant.data.local.db.dao.AutomationRuleDao
) : com.openclaw.homeassistant.domain.repository.RulesRepository {

    override suspend fun getRules(enabled: Boolean?): List<com.openclaw.homeassistant.domain.model.AutomationRule> {
        return yuanFangApi.getRules(enabled).map { dto ->
            com.openclaw.homeassistant.domain.model.AutomationRule(
                id = dto.id, name = dto.name, enabled = dto.enabled, priority = dto.priority,
                condition = com.openclaw.homeassistant.domain.model.RuleCondition(
                    triggerType = dto.condition?.get("trigger_type")?.toString() ?: "time",
                    entityId = dto.condition?.get("entity_id")?.toString(),
                    time = dto.condition?.get("time")?.toString()
                ),
                actions = dto.action?.map { actionMap ->
                    com.openclaw.homeassistant.domain.model.RuleAction(
                        type = actionMap["type"]?.toString() ?: "notify",
                        text = actionMap["text"]?.toString(),
                        entityId = actionMap["entity_id"]?.toString(),
                        action = actionMap["action"]?.toString()
                    )
                } ?: emptyList()
            )
        }
    }

    override suspend fun addRule(rule: com.openclaw.homeassistant.domain.model.AutomationRule): com.openclaw.homeassistant.domain.model.AutomationRule {
        val request = AddRuleRequest(
            id = rule.id, name = rule.name, enabled = rule.enabled, priority = rule.priority,
            condition = mapOf("trigger_type" to rule.condition.triggerType, "entity_id" to (rule.condition.entityId ?: "")),
            action = rule.actions.map { mapOf("type" to it.type, "text" to (it.text ?: ""), "entity_id" to (it.entityId ?: "")) }
        )
        val dto = yuanFangApi.addRule(request)
        return rule
    }

    override suspend fun deleteRule(ruleId: String) {
        yuanFangApi.deleteRule(ruleId)
    }

    override suspend fun enableRule(ruleId: String) {
        yuanFangApi.enableRule(ruleId)
    }

    override suspend fun disableRule(ruleId: String) {
        yuanFangApi.disableRule(ruleId)
    }

    override suspend fun checkRules(context: Map<String, Any>): List<Map<String, Any>> {
        val response = yuanFangApi.checkRules(RuleCheckRequest(context = context))
        return response.results
    }

    override fun getLocalRules(): Flow<List<com.openclaw.homeassistant.domain.model.AutomationRule>> {
        return automationRuleDao.getAll().map { entities ->
            entities.map { it.toDomain() }
        }
    }

    override suspend fun syncRules() {
        val remoteRules = getRules(null)
        val gson = com.google.gson.Gson()
        val entities = remoteRules.map { rule ->
            com.openclaw.homeassistant.data.local.db.entity.AutomationRuleEntity(
                id = rule.id, name = rule.name, enabled = rule.enabled, priority = rule.priority,
                conditionJson = gson.toJson(rule.condition),
                actionJson = gson.toJson(rule.actions)
            )
        }
        entities.forEach { automationRuleDao.insert(it) }
    }

    private fun com.openclaw.homeassistant.data.local.db.entity.AutomationRuleEntity.toDomain(): com.openclaw.homeassistant.domain.model.AutomationRule {
        val gson = com.google.gson.Gson()
        val condition = gson.fromJson(conditionJson, com.openclaw.homeassistant.domain.model.RuleCondition::class.java)
        val actions = gson.fromJson(actionJson, Array<com.openclaw.homeassistant.domain.model.RuleAction>::class.java).toList()
        return com.openclaw.homeassistant.domain.model.AutomationRule(
            id = id, name = name, enabled = enabled, condition = condition,
            actions = actions, priority = priority, lastTriggeredAt = lastTriggeredAt,
            triggerCount = triggerCount
        )
    }
}

@Singleton
class DeviceRepositoryImpl @Inject constructor(
    private val secureConfig: com.openclaw.homeassistant.data.local.prefs.SecureConfig
) : com.openclaw.homeassistant.domain.repository.DeviceRepository {

    override suspend fun registerDevice(): String {
        return secureConfig.deviceId
    }

    override suspend fun confirmDevice(tempId: String, code: String): Boolean {
        secureConfig.isDeviceConfirmed = true
        return true
    }

    override suspend fun getDeviceInfo(): Map<String, Any> {
        return mapOf(
            "device_id" to secureConfig.deviceId,
            "has_token" to secureConfig.deviceToken.isNotEmpty(),
            "server_url" to secureConfig.yuanfangUrl
        )
    }

    override suspend fun logout() {
        secureConfig.clearSensitiveData()
        secureConfig.isDeviceConfirmed = false
    }

    override val isDeviceConfirmed: Boolean get() = secureConfig.isDeviceConfirmed
}