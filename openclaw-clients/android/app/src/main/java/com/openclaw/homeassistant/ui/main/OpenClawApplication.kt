package com.openclaw.homeassistant.ui.main

import android.app.Application
import dagger.hilt.android.HiltAndroidApp

@HiltAndroidApp
class OpenClawApplication : Application() {
    override fun onCreate() {
        super.onCreate()
    }
}