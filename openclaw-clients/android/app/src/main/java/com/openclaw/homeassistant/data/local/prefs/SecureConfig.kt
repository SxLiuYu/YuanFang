package com.openclaw.homeassistant.data.local.prefs

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import com.openclaw.homeassistant.BuildConfig
import dagger.hilt.android.qualifiers.ApplicationContext
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class SecureConfig @Inject constructor(@ApplicationContext private val context: Context) {

    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val encryptedPrefs: SharedPreferences = try {
        EncryptedSharedPreferences.create(
            context,
            "openclaw_secure_prefs",
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    } catch (e: Exception) {
        context.getSharedPreferences("openclaw_secure_prefs_fallback", Context.MODE_PRIVATE)
    }

    private val regularPrefs: SharedPreferences =
        context.getSharedPreferences("openclaw_regular_prefs", Context.MODE_PRIVATE)

    var apiKey: String
        get() = encryptedPrefs.getString("api_key", "") ?: ""
        set(value) = encryptedPrefs.edit().putString("api_key", value).apply()

    var deviceToken: String
        get() = encryptedPrefs.getString("device_token", "") ?: ""
        set(value) = encryptedPrefs.edit().putString("device_token", value).apply()

    var deviceId: String
        get() = encryptedPrefs.getString("device_id", "") ?: generateDeviceId()
        set(value) = encryptedPrefs.edit().putString("device_id", value).apply()

    var dashScopeApiKey: String
        get() = encryptedPrefs.getString("dashscope_api_key", "") ?: ""
        set(value) = encryptedPrefs.edit().putString("dashscope_api_key", value).apply()

    val isDashScopeConfigured: Boolean
        get() = dashScopeApiKey.isNotEmpty()

    var yuanfangUrl: String
        get() = regularPrefs.getString("yuanfang_url", BuildConfig.DEFAULT_YUANFANG_URL) ?: BuildConfig.DEFAULT_YUANFANG_URL
        set(value) = regularPrefs.edit().putString("yuanfang_url", value).apply()

    var jarvisUrl: String
        get() = regularPrefs.getString("jarvis_url", BuildConfig.DEFAULT_JARVIS_URL) ?: BuildConfig.DEFAULT_JARVIS_URL
        set(value) = regularPrefs.edit().putString("jarvis_url", value).apply()

    var openclawUrl: String
        get() = regularPrefs.getString("openclaw_url", BuildConfig.DEFAULT_OPENCLAW_URL) ?: BuildConfig.DEFAULT_OPENCLAW_URL
        set(value) = regularPrefs.edit().putString("openclaw_url", value).apply()

    var feishuWebhook: String
        get() = regularPrefs.getString("feishu_webhook", "") ?: ""
        set(value) = regularPrefs.edit().putString("feishu_webhook", value).apply()

    var familyServiceUrl: String
        get() = regularPrefs.getString("family_service_url", "") ?: ""
        set(value) = regularPrefs.edit().putString("family_service_url", value).apply()

    var username: String
        get() = regularPrefs.getString("username", "") ?: ""
        set(value) = regularPrefs.edit().putString("username", value).apply()

    var isConfigured: Boolean
        get() = deviceToken.isNotEmpty() || apiKey.isNotEmpty()

    var isDeviceConfirmed: Boolean
        get() = regularPrefs.getBoolean("device_confirmed", false)
        set(value) = regularPrefs.edit().putBoolean("device_confirmed", value).apply()

    var defaultModel: String
        get() = regularPrefs.getString("default_model", "Pro/deepseek-ai/DeepSeek-V3.1-Terminus") ?: "Pro/deepseek-ai/DeepSeek-V3.1-Terminus"
        set(value) = regularPrefs.edit().putString("default_model", value).apply()

    fun clearSensitiveData() {
        encryptedPrefs.edit().clear().apply()
    }

    fun clearAll() {
        encryptedPrefs.edit().clear().apply()
        regularPrefs.edit().clear().apply()
    }

    private fun generateDeviceId(): String {
        val bytes = java.security.SecureRandom().let { rnd ->
            ByteArray(8).also { rnd.nextBytes(it) }
        }
        val id = "android_" + android.util.Base64.encodeToString(bytes, android.util.Base64.URL_SAFE or android.util.Base64.NO_WRAP)
        deviceId = id
        return id
    }
}