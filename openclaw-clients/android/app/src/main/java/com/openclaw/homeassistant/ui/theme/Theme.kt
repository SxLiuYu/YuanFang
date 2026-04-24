package com.openclaw.homeassistant.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable

private val DarkColorScheme = darkColorScheme(
    primary = DeepSeaPrimary,
    onPrimary = DeepSeaTextPrimary,
    primaryContainer = DeepSeaSurfaceVariant,
    onPrimaryContainer = DeepSeaTextPrimary,
    secondary = DeepSeaSecondary,
    onSecondary = DeepSeaTextPrimary,
    secondaryContainer = DeepSeaSurfaceVariant,
    onSecondaryContainer = DeepSeaTextPrimary,
    tertiary = DeepSeaTertiary,
    onTertiary = DeepSeaTextPrimary,
    tertiaryContainer = DeepSeaSurfaceVariant,
    onTertiaryContainer = DeepSeaTextPrimary,
    background = DeepSeaBackground,
    onBackground = DeepSeaTextPrimary,
    surface = DeepSeaSurface,
    onSurface = DeepSeaTextPrimary,
    surfaceVariant = DeepSeaSurfaceVariant,
    onSurfaceVariant = DeepSeaTextSecondary,
    error = DeepSeaError,
    onError = DeepSeaTextPrimary,
    outline = DeepSeaDivider,
    outlineVariant = DeepSeaDivider
)

@Composable
fun OpenClawTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = DarkColorScheme,
        typography = DeepSeaTypography,
        content = content
    )
}