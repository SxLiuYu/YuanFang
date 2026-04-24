package com.openclaw.homeassistant.di

import android.content.Context
import com.openclaw.homeassistant.BuildConfig
import com.openclaw.homeassistant.data.local.prefs.SecureConfig
import com.openclaw.homeassistant.data.remote.api.YuanFangApi
import com.openclaw.homeassistant.data.remote.api.JarvisApi
import com.openclaw.homeassistant.data.remote.socket.YuanFangSocketClient
import com.openclaw.homeassistant.data.local.db.AppDatabase
import com.openclaw.homeassistant.data.local.db.dao.ChatSessionDao
import com.openclaw.homeassistant.data.local.db.dao.MessageDao
import com.openclaw.homeassistant.data.local.db.dao.DeviceDao
import com.openclaw.homeassistant.data.local.db.dao.AutomationRuleDao
import dagger.Module
import dagger.Provides
import dagger.hilt.InstallIn
import dagger.hilt.android.qualifiers.ApplicationContext
import dagger.hilt.components.SingletonComponent
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import retrofit2.converter.scalars.ScalarsConverterFactory
import java.util.concurrent.TimeUnit
import javax.inject.Qualifier
import javax.inject.Singleton

@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class YuanFangRetrofit

@Qualifier
@Retention(AnnotationRetention.BINARY)
annotation class JarvisRetrofit

@Module
@InstallIn(SingletonComponent::class)
object AppModule {

    @Provides
    @Singleton
    fun provideOkHttpClient(secureConfig: SecureConfig): OkHttpClient {
        return OkHttpClient.Builder()
            .connectTimeout(30, TimeUnit.SECONDS)
            .readTimeout(60, TimeUnit.SECONDS)
            .writeTimeout(30, TimeUnit.SECONDS)
            .addInterceptor(HttpLoggingInterceptor().apply {
                level = if (BuildConfig.DEBUG) HttpLoggingInterceptor.Level.BODY else HttpLoggingInterceptor.Level.NONE
            })
            .addInterceptor { chain ->
                val request = chain.request()
                val token = secureConfig.deviceToken
                val builder = request.newBuilder()
                if (token.isNotEmpty()) {
                    builder.header("Authorization", "Bearer $token")
                }
                chain.proceed(builder.build())
            }
            .build()
    }

    @Provides
    @Singleton
    @YuanFangRetrofit
    fun provideYuanFangRetrofit(okHttpClient: OkHttpClient, secureConfig: SecureConfig): Retrofit {
        return Retrofit.Builder()
            .baseUrl(secureConfig.yuanfangUrl)
            .client(okHttpClient)
            .addConverterFactory(ScalarsConverterFactory.create())
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    @Provides
    @Singleton
    @JarvisRetrofit
    fun provideJarvisRetrofit(okHttpClient: OkHttpClient, secureConfig: SecureConfig): Retrofit {
        return Retrofit.Builder()
            .baseUrl(secureConfig.jarvisUrl)
            .client(okHttpClient)
            .addConverterFactory(ScalarsConverterFactory.create())
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }

    @Provides
    @Singleton
    fun provideYuanFangApi(@YuanFangRetrofit retrofit: Retrofit): YuanFangApi {
        return retrofit.create(YuanFangApi::class.java)
    }

    @Provides
    @Singleton
    fun provideJarvisApi(@JarvisRetrofit retrofit: Retrofit): JarvisApi {
        return retrofit.create(JarvisApi::class.java)
    }

    @Provides
    @Singleton
    fun provideAppDatabase(@ApplicationContext context: Context): AppDatabase {
        return AppDatabase.getInstance(context)
    }

    @Provides
    fun provideChatSessionDao(db: AppDatabase): ChatSessionDao = db.chatSessionDao()

    @Provides
    fun provideMessageDao(db: AppDatabase): MessageDao = db.messageDao()

    @Provides
    fun provideDeviceDao(db: AppDatabase): DeviceDao = db.deviceDao()

    @Provides
    fun provideAutomationRuleDao(db: AppDatabase): AutomationRuleDao = db.automationRuleDao()
}