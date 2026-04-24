package com.openclaw.homeassistant.di

import com.openclaw.homeassistant.data.repository.ChatRepositoryImpl
import com.openclaw.homeassistant.data.repository.HomeRepositoryImpl
import com.openclaw.homeassistant.data.repository.VoiceRepositoryImpl
import com.openclaw.homeassistant.data.repository.MemoryRepositoryImpl
import com.openclaw.homeassistant.data.repository.PersonalityRepositoryImpl
import com.openclaw.homeassistant.data.repository.SkillsRepositoryImpl
import com.openclaw.homeassistant.data.repository.RulesRepositoryImpl
import com.openclaw.homeassistant.data.repository.DeviceRepositoryImpl
import com.openclaw.homeassistant.domain.repository.ChatRepository
import com.openclaw.homeassistant.domain.repository.HomeRepository
import com.openclaw.homeassistant.domain.repository.VoiceRepository
import com.openclaw.homeassistant.domain.repository.MemoryRepository
import com.openclaw.homeassistant.domain.repository.PersonalityRepository
import com.openclaw.homeassistant.domain.repository.SkillsRepository
import com.openclaw.homeassistant.domain.repository.RulesRepository
import com.openclaw.homeassistant.domain.repository.DeviceRepository
import dagger.Binds
import dagger.Module
import dagger.hilt.InstallIn
import dagger.hilt.components.SingletonComponent

@Module
@InstallIn(SingletonComponent::class)
abstract class RepositoryModule {

    @Binds
    abstract fun bindChatRepository(impl: ChatRepositoryImpl): ChatRepository

    @Binds
    abstract fun bindHomeRepository(impl: HomeRepositoryImpl): HomeRepository

    @Binds
    abstract fun bindVoiceRepository(impl: VoiceRepositoryImpl): VoiceRepository

    @Binds
    abstract fun bindMemoryRepository(impl: MemoryRepositoryImpl): MemoryRepository

    @Binds
    abstract fun bindPersonalityRepository(impl: PersonalityRepositoryImpl): PersonalityRepository

    @Binds
    abstract fun bindSkillsRepository(impl: SkillsRepositoryImpl): SkillsRepository

    @Binds
    abstract fun bindRulesRepository(impl: RulesRepositoryImpl): RulesRepository

    @Binds
    abstract fun bindDeviceRepository(impl: DeviceRepositoryImpl): DeviceRepository
}