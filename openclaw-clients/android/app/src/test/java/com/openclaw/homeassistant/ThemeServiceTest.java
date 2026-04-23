package com.openclaw.homeassistant;

import android.content.Context;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.mockito.Mock;
import org.mockito.MockitoAnnotations;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;

import static org.junit.Assert.*;

/**
 * ThemeService 单元测试
 */
@RunWith(RobolectricTestRunner.class)
public class ThemeServiceTest {

    private ThemeService themeService;
    private Context context;

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        context = RuntimeEnvironment.getApplication().getApplicationContext();
        themeService = new ThemeService(context);
    }

    @Test
    public void testServiceNotNull() {
        assertNotNull("服务不应为空", themeService);
    }

    @Test
    public void testGetCurrentTheme() {
        // 测试获取当前主题
        String theme = themeService.getCurrentTheme();
        assertNotNull("主题不应为空", theme);
    }

    @Test
    public void testSetTheme() {
        // 测试设置主题
        boolean result = themeService.setTheme("dark");
        assertTrue("设置主题应成功", result);
    }

    @Test
    public void testGetAvailableThemes() {
        // 测试获取可用主题列表
        assertNotNull("主题列表不应为空", themeService.getAvailableThemes());
    }

    @Test
    public void testIsDarkMode() {
        // 测试是否暗色模式
        themeService.setTheme("dark");
        assertTrue("应为暗色模式", themeService.isDarkMode());
    }

    @Test
    public void testSetAutoTheme() {
        // 测试设置自动主题
        boolean result = themeService.setAutoTheme(true);
        assertTrue("设置自动主题应成功", result);
    }

    @Test
    public void testGetAccentColor() {
        // 测试获取强调色
        int color = themeService.getAccentColor();
        assertNotNull("强调色不应为空", color);
    }

    @Test
    public void testSetAccentColor() {
        // 测试设置强调色
        boolean result = themeService.setAccentColor("#FF5722");
        assertTrue("设置强调色应成功", result);
    }
}