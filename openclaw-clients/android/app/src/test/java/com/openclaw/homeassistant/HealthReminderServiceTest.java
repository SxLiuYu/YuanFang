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
 * HealthReminderService 单元测试
 */
@RunWith(RobolectricTestRunner.class)
public class HealthReminderServiceTest {

    private HealthReminderService healthReminderService;
    private Context context;

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        context = RuntimeEnvironment.getApplication().getApplicationContext();
        healthReminderService = new HealthReminderService(context);
    }

    @Test
    public void testServiceNotNull() {
        assertNotNull("服务不应为空", healthReminderService);
    }

    @Test
    public void testAddReminder() {
        // 测试添加健康提醒
        long reminderId = healthReminderService.addReminder(
            "喝水提醒",
            "请喝水",
            30, // 每30分钟
            "09:00-22:00"
        );

        assertTrue("提醒ID应大于0", reminderId > 0);
    }

    @Test
    public void testGetReminders() {
        // 测试获取提醒列表
        assertNotNull("提醒列表不应为空", healthReminderService.getReminders());
    }

    @Test
    public void testDeleteReminder() {
        // 先添加一个提醒
        long reminderId = healthReminderService.addReminder(
            "测试提醒",
            "测试内容",
            60,
            "08:00-20:00"
        );

        // 删除提醒
        boolean result = healthReminderService.deleteReminder(reminderId);
        assertTrue("删除应成功", result);
    }

    @Test
    public void testUpdateReminder() {
        // 先添加一个提醒
        long reminderId = healthReminderService.addReminder(
            "原提醒",
            "原内容",
            60,
            "08:00-20:00"
        );

        // 更新提醒
        boolean result = healthReminderService.updateReminder(
            reminderId,
            "新提醒",
            "新内容",
            30,
            "09:00-21:00"
        );

        assertTrue("更新应成功", result);
    }

    @Test
    public void testToggleReminder() {
        // 先添加一个提醒
        long reminderId = healthReminderService.addReminder(
            "开关测试",
            "测试内容",
            60,
            "08:00-20:00"
        );

        // 切换状态
        boolean result = healthReminderService.toggleReminder(reminderId, false);
        assertTrue("切换状态应成功", result);
    }
}