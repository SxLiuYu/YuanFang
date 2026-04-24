package com.openclaw.homeassistant.ui.navigation

sealed class Route(val route: String) {
    object Home : Route("home")
    object Chat : Route("chat")
    object ChatSession : Route("chat/{sessionId}") {
        fun createRoute(sessionId: String) = "chat/$sessionId"
    }
    object Voice : Route("voice")
    object HomeDashboard : Route("home_dashboard")
    object DeviceDetail : Route("device_detail/{entityId}") {
        fun createRoute(entityId: String) = "device_detail/$entityId"
    }
    object Personality : Route("personality")
    object Memory : Route("memory")
    object Skills : Route("skills")
    object CreateTool : Route("create_tool")
    object Automation : Route("automation")
    object RuleDetail : Route("rule_detail/{ruleId}") {
        fun createRoute(ruleId: String) = "rule_detail/$ruleId"
    }
    object Settings : Route("settings")
    object Cooking : Route("cooking")
    object Health : Route("health")
    object Finance : Route("finance")
}