package com.openclaw.homeassistant.data.repository

import com.openclaw.homeassistant.data.local.db.dao.DeviceDao
import com.openclaw.homeassistant.data.local.db.entity.DeviceEntity
import com.openclaw.homeassistant.data.remote.api.YuanFangApi
import com.openclaw.homeassistant.data.remote.dto.*
import com.openclaw.homeassistant.domain.model.DeviceState
import com.openclaw.homeassistant.domain.repository.HomeRepository
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.map
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class HomeRepositoryImpl @Inject constructor(
    private val yuanFangApi: YuanFangApi,
    private val deviceDao: DeviceDao
) : HomeRepository {

    override suspend fun checkHaConnection(): Boolean {
        return try {
            yuanFangApi.haPing().connected
        } catch (e: Exception) {
            false
        }
    }

    override suspend fun getDeviceStates(domain: String?): List<DeviceState> {
        val states = yuanFangApi.haStates(domain)
        return states.map { it.toDomain() }
    }

    override suspend fun controlDevice(entityId: String, action: String): Boolean {
        return try {
            yuanFangApi.haControl(HaControlRequest(entity_id = entityId, action = action)).success
        } catch (e: Exception) {
            false
        }
    }

    override suspend fun controlLight(entityId: String, brightness: Int?, colorTemp: Int?, rgbColor: List<Int>?): Boolean {
        return try {
            yuanFangApi.haLight(HaLightRequest(entity_id = entityId, brightness = brightness, color_temp = colorTemp, rgb_color = rgbColor)).success
        } catch (e: Exception) {
            false
        }
    }

    override suspend fun controlClimate(entityId: String, temperature: Double, hvacMode: String?): Boolean {
        return try {
            yuanFangApi.haClimate(HaClimateRequest(entity_id = entityId, temperature = temperature, hvac_mode = hvacMode)).success
        } catch (e: Exception) {
            false
        }
    }

    override suspend fun getScenes(): List<DeviceState> {
        return yuanFangApi.haScenes().map { DeviceState(entityId = it.entity_id, name = it.name ?: it.entity_id, domain = "scene", state = it.state ?: "unknown") }
    }

    override suspend fun activateScene(entityId: String): Boolean {
        return try {
            yuanFangApi.haSceneActivate(SceneActivateRequest(entity_id = entityId)).success
        } catch (e: Exception) {
            false
        }
    }

    override fun getLocalDevices(): Flow<List<DeviceState>> {
        return deviceDao.getAll().map { entities -> entities.map { it.toDomain() } }
    }

    override fun getFavoriteDevices(): Flow<List<DeviceState>> {
        return deviceDao.getFavorites().map { entities -> entities.map { it.toDomain() } }
    }

    override fun getRooms(): Flow<List<String>> {
        return deviceDao.getRooms()
    }

    override suspend fun refreshDevices() {
        val remoteStates = getDeviceStates(null)
        val entities = remoteStates.map { state ->
            DeviceEntity(
                entityId = state.entityId,
                name = state.name,
                platform = state.platform,
                domain = state.domain,
                room = state.room,
                state = state.state,
                attributesJson = com.google.gson.Gson().toJson(state.attributes),
                lastUpdated = state.lastUpdated
            )
        }
        deviceDao.insertAll(entities)
    }

    override suspend fun setFavorite(entityId: String, favorite: Boolean) {
        val device = deviceDao.getById(entityId)
        if (device != null) {
            deviceDao.update(device.copy(isFavorite = favorite))
        }
    }

    private fun HaEntityStateDto.toDomain(): DeviceState {
        val friendlyName = attributes["friendly_name"]?.toString() ?: entity_id
        val domainStr = entity_id.split(".").firstOrNull() ?: "unknown"
        val roomStr = attributes["area"]?.toString() ?: ""
        return DeviceState(
            entityId = entity_id, name = friendlyName, domain = domainStr,
            platform = "ha", room = roomStr, state = state,
            attributes = attributes
        )
    }

    private fun DeviceEntity.toDomain() = DeviceState(
        entityId = entityId, name = name, domain = domain,
        platform = platform, room = room, state = state,
        isFavorite = isFavorite, lastUpdated = lastUpdated,
        attributes = try { com.google.gson.Gson().fromJson(attributesJson, Map::class.java) as Map<String, Any> } catch (e: Exception) { emptyMap() }
    )
}