package com.openclaw.homeassistant.data.local.db

import android.content.Context
import androidx.room.Database
import androidx.room.Room
import androidx.room.RoomDatabase
import androidx.room.TypeConverters
import com.openclaw.homeassistant.data.local.db.dao.ChatSessionDao
import com.openclaw.homeassistant.data.local.db.dao.MessageDao
import com.openclaw.homeassistant.data.local.db.dao.DeviceDao
import com.openclaw.homeassistant.data.local.db.dao.AutomationRuleDao
import com.openclaw.homeassistant.data.local.db.entity.MessageEntity
import com.openclaw.homeassistant.data.local.db.entity.ChatSessionEntity
import com.openclaw.homeassistant.data.local.db.entity.DeviceEntity
import com.openclaw.homeassistant.data.local.db.entity.AutomationRuleEntity
import dagger.hilt.android.qualifiers.ApplicationContext

@Database(
    entities = [MessageEntity::class, ChatSessionEntity::class, DeviceEntity::class, AutomationRuleEntity::class],
    version = 1,
    exportSchema = false
)
@TypeConverters(Converters::class)
abstract class AppDatabase : RoomDatabase() {
    abstract fun messageDao(): MessageDao
    abstract fun chatSessionDao(): ChatSessionDao
    abstract fun deviceDao(): DeviceDao
    abstract fun automationRuleDao(): AutomationRuleDao

    companion object {
        @Volatile
        private var INSTANCE: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase {
            return INSTANCE ?: synchronized(this) {
                val instance = Room.databaseBuilder(
                    context.applicationContext,
                    AppDatabase::class.java,
                    "openclaw_database"
                )
                    .fallbackToDestructiveMigration()
                    .build()
                INSTANCE = instance
                instance
            }
        }
    }
}

class Converters {
    private val gson = com.google.gson.Gson()

    @androidx.room.TypeConverter
    fun fromStringList(value: List<String>?): String = gson.toJson(value)

    @androidx.room.TypeConverter
    fun toStringList(value: String?): List<String> =
        gson.fromJson(value, object : com.google.gson.reflect.TypeToken<List<String>>() {}.type)
            ?: emptyList()
}