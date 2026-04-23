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
 * NewsService 单元测试
 */
@RunWith(RobolectricTestRunner.class)
public class NewsServiceTest {

    private NewsService newsService;
    private Context context;

    @Before
    public void setUp() {
        MockitoAnnotations.initMocks(this);
        context = RuntimeEnvironment.getApplication().getApplicationContext();
        newsService = new NewsService(context);
    }

    @Test
    public void testServiceNotNull() {
        assertNotNull("服务不应为空", newsService);
    }

    @Test
    public void testGetHeadlines() {
        // 测试获取头条新闻
        assertNotNull("新闻列表不应为空", newsService.getHeadlines());
    }

    @Test
    public void testGetNewsByCategory() {
        // 测试按类别获取新闻
        assertNotNull("科技新闻列表不应为空", newsService.getNewsByCategory("tech"));
        assertNotNull("娱乐新闻列表不应为空", newsService.getNewsByCategory("entertainment"));
    }

    @Test
    public void testSearchNews() {
        // 测试搜索新闻
        assertNotNull("搜索结果不应为空", newsService.searchNews("AI"));
    }

    @Test
    public void testGetNewsDetail() {
        // 测试获取新闻详情
        String detail = newsService.getNewsDetail("test_news_id");
        // 可能返回空（新闻不存在）
        assertNotNull("新闻详情查询不应抛出异常", detail);
    }

    @Test
    public void testSetNewsSource() {
        // 测试设置新闻源
        boolean result = newsService.setNewsSource("sina", true);
        assertTrue("设置新闻源应成功", result);
    }

    @Test
    public void testGetSources() {
        // 测试获取新闻源列表
        assertNotNull("新闻源列表不应为空", newsService.getSources());
    }
}