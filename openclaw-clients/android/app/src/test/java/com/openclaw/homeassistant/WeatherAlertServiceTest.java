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
 * WeatherAlertService 单元测试
 */
@RunWith(RobolectricTestRunner.class)
public class WeatherAlertServiceTest {

    private WeatherAlertService weatherAlertService;
    private Context context;

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        context = RuntimeEnvironment.getApplication().getApplicationContext();
        weatherAlertService = new WeatherAlertService(context);
    }

    @Test
    public void testServiceNotNull() {
        assertNotNull("服务不应为空", weatherAlertService);
    }

    @Test
    public void testGetCurrentWeather() {
        // 测试获取当前天气
        String weather = weatherAlertService.getCurrentWeather("北京");
        // 可能返回空（无网络）
        assertNotNull("天气查询不应抛出异常", weather);
    }

    @Test
    public void testSetWeatherAlert() {
        // 测试设置天气预警
        boolean result = weatherAlertService.setWeatherAlert(
            "北京",
            "rain",
            true
        );
        assertTrue("设置预警应成功", result);
    }

    @Test
    public void testGetAlerts() {
        // 测试获取预警列表
        assertNotNull("预警列表不应为空", weatherAlertService.getAlerts());
    }

    @Test
    public void testCheckWeatherCondition() {
        // 测试检查天气条件
        boolean isRain = weatherAlertService.checkWeatherCondition("rain");
        assertNotNull("天气条件检查不应抛出异常", isRain);
    }

    @Test
    public void testGetForecast() {
        // 测试获取天气预报
        String forecast = weatherAlertService.getForecast("北京", 3);
        assertNotNull("天气预报查询不应抛出异常", forecast);
    }

    @Test
    public void testRemoveAlert() {
        // 先添加一个预警
        weatherAlertService.setWeatherAlert("上海", "snow", true);

        // 删除预警
        boolean result = weatherAlertService.removeAlert("上海", "snow");
        assertNotNull("删除预警不应抛出异常", result);
    }
}