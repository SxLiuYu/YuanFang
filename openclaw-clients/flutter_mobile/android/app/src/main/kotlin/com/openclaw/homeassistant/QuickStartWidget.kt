package com.openclaw.homeassistant

import android.app.PendingIntent
import android.appwidget.AppWidgetManager
import android.appwidget.AppWidgetProvider
import android.content.Context
import android.content.Intent
import android.net.Uri
import android.widget.RemoteViews
import android.content.SharedPreferences

class QuickStartWidget : AppWidgetProvider() {
    
    companion object {
        const val ACTION_QUICK_ACCOUNTING = "com.openclaw.homeassistant.QUICK_ACCOUNTING"
        const val ACTION_OPEN_APP = "com.openclaw.homeassistant.OPEN_APP"
        const val ACTION_REFRESH = "com.openclaw.homeassistant.REFRESH"
        
        private const val PREFS_NAME = "QuickStartWidgetPrefs"
        private const val PREF_PREFIX_KEY = "widget_"
    }
    
    override fun onUpdate(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetIds: IntArray
    ) {
        for (appWidgetId in appWidgetIds) {
            updateAppWidget(context, appWidgetManager, appWidgetId)
        }
    }
    
    override fun onReceive(context: Context, intent: Intent) {
        super.onReceive(context, intent)
        
        when (intent.action) {
            ACTION_QUICK_ACCOUNTING -> {
                openQuickAccounting(context)
            }
            ACTION_OPEN_APP -> {
                openApp(context)
            }
            ACTION_REFRESH -> {
                val appWidgetId = intent.getIntExtra(
                    AppWidgetManager.EXTRA_APPWIDGET_ID,
                    AppWidgetManager.INVALID_APPWIDGET_ID
                )
                if (appWidgetId != AppWidgetManager.INVALID_APPWIDGET_ID) {
                    updateAppWidget(
                        context,
                        AppWidgetManager.getInstance(context),
                        appWidgetId
                    )
                }
            }
        }
    }
    
    private fun updateAppWidget(
        context: Context,
        appWidgetManager: AppWidgetManager,
        appWidgetId: Int
    ) {
        val views = RemoteViews(context.packageName, R.layout.quick_start_widget)
        
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val steps = prefs.getInt("${PREF_PREFIX_KEY}steps_$appWidgetId", 0)
        val todos = prefs.getInt("${PREF_PREFIX_KEY}todos_$appWidgetId", 0)
        
        views.setTextViewText(R.id.text_steps, "$steps 步")
        views.setTextViewText(R.id.text_todos, "$todos 项")
        
        val openAppIntent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        val openAppPendingIntent = PendingIntent.getActivity(
            context, 0, openAppIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.widget_root, openAppPendingIntent)
        
        val accountingIntent = Intent(context, QuickStartWidget::class.java).apply {
            action = ACTION_QUICK_ACCOUNTING
        }
        val accountingPendingIntent = PendingIntent.getBroadcast(
            context, 1, accountingIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.btn_quick_accounting, accountingPendingIntent)
        
        val refreshIntent = Intent(context, QuickStartWidget::class.java).apply {
            action = ACTION_REFRESH
            putExtra(AppWidgetManager.EXTRA_APPWIDGET_ID, appWidgetId)
        }
        val refreshPendingIntent = PendingIntent.getBroadcast(
            context, 2, refreshIntent,
            PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE
        )
        views.setOnClickPendingIntent(R.id.btn_refresh, refreshPendingIntent)
        
        appWidgetManager.updateAppWidget(appWidgetId, views)
    }
    
    private fun openQuickAccounting(context: Context) {
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            putExtra("action", "quick_accounting")
            data = Uri.parse("openclaw://accounting/quick")
        }
        context.startActivity(intent)
    }
    
    private fun openApp(context: Context) {
        val intent = Intent(context, MainActivity::class.java).apply {
            flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
        }
        context.startActivity(intent)
    }
    
    override fun onDeleted(context: Context, appWidgetIds: IntArray) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val editor = prefs.edit()
        for (appWidgetId in appWidgetIds) {
            editor.remove("${PREF_PREFIX_KEY}steps_$appWidgetId")
            editor.remove("${PREF_PREFIX_KEY}todos_$appWidgetId")
        }
        editor.apply()
    }
    
    fun updateWidgetData(
        context: Context,
        steps: Int,
        todos: Int
    ) {
        val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
        val editor = prefs.edit()
        
        val appWidgetManager = AppWidgetManager.getInstance(context)
        val appWidgetIds = appWidgetManager.getAppWidgetIds(
            android.content.ComponentName(context, QuickStartWidget::class.java)
        )
        
        for (appWidgetId in appWidgetIds) {
            editor.putInt("${PREF_PREFIX_KEY}steps_$appWidgetId", steps)
            editor.putInt("${PREF_PREFIX_KEY}todos_$appWidgetId", todos)
        }
        editor.apply()
        
        onUpdate(context, appWidgetManager, appWidgetIds)
    }
}