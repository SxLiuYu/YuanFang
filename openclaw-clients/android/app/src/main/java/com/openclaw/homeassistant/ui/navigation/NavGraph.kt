package com.openclaw.homeassistant.ui.navigation

import androidx.compose.runtime.Composable
import androidx.navigation.NavHostController
import androidx.navigation.compose.NavHost
import androidx.navigation.compose.composable
import com.openclaw.homeassistant.ui.screen.chat.ChatScreen
import com.openclaw.homeassistant.ui.screen.home.HomeDashboardScreen
import com.openclaw.homeassistant.ui.screen.voice.VoiceAssistantScreen
import com.openclaw.homeassistant.ui.screen.memory.MemoryScreen
import com.openclaw.homeassistant.ui.screen.personality.PersonalityScreen
import com.openclaw.homeassistant.ui.screen.skills.SkillsScreen
import com.openclaw.homeassistant.ui.screen.automation.AutomationScreen
import com.openclaw.homeassistant.ui.screen.settings.SettingsScreen
import com.openclaw.homeassistant.ui.main.HomeScreen

@Composable
fun NavGraph(navController: NavHostController) {
    NavHost(navController = navController, startDestination = Route.Home.route) {
        composable(Route.Home.route) {
            HomeScreen(navController = navController)
        }
        composable(Route.Chat.route) {
            ChatScreen(navController = navController)
        }
        composable(Route.ChatSession.route) { backStackEntry ->
            val sessionId = backStackEntry.arguments?.getString("sessionId") ?: "default"
            ChatScreen(navController = navController, sessionId = sessionId)
        }
        composable(Route.Voice.route) {
            VoiceAssistantScreen(navController = navController)
        }
        composable(Route.HomeDashboard.route) {
            HomeDashboardScreen(navController = navController)
        }
        composable(Route.Personality.route) {
            PersonalityScreen(navController = navController)
        }
        composable(Route.Memory.route) {
            MemoryScreen(navController = navController)
        }
        composable(Route.Skills.route) {
            SkillsScreen(navController = navController)
        }
        composable(Route.Automation.route) {
            AutomationScreen(navController = navController)
        }
        composable(Route.Settings.route) {
            SettingsScreen(navController = navController)
        }
    }
}