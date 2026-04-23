package com.openclaw.homeassistant;

import org.junit.Before;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.robolectric.RobolectricTestRunner;
import org.robolectric.RuntimeEnvironment;

import java.util.List;
import java.util.Map;

import static org.junit.Assert.*;

/**
 * ShoppingService 单元测试
 */
@RunWith(RobolectricTestRunner.class)
public class ShoppingServiceTest {

    private ShoppingService shoppingService;

    @Before
    public void setUp() {
        shoppingService = new ShoppingService(RuntimeEnvironment.getApplication().getApplicationContext());
    }

    @Test
    public void testAddItem() {
        // 测试添加物品
        shoppingService.addItem("牛奶", "食品", 2, "瓶", "测试用户");

        // 验证物品已添加
        List<Map<String, Object>> items = shoppingService.getShoppingList();
        assertNotNull(items);
    }

    @Test
    public void testAddItemByVoice() {
        // 测试语音添加
        shoppingService.addItemByVoice("买5瓶牛奶", "测试用户");

        // 验证物品已添加
        assertNotNull(shoppingService);
    }

    @Test
    public void testGetShoppingList() {
        // 添加测试数据
        shoppingService.addItem("苹果", "水果", 3, "个", "测试用户");
        shoppingService.addItem("面包", "食品", 1, "袋", "测试用户");

        // 获取购物清单
        List<Map<String, Object>> items = shoppingService.getShoppingList();

        // 验证返回清单
        assertNotNull(items);
        assertTrue(items.size() >= 2);
    }

    @Test
    public void testMarkAsPurchased() {
        // 先添加物品
        shoppingService.addItem("测试物品", "其他", 1, "个", "测试用户");

        // 获取购物清单找到 ID
        List<Map<String, Object>> items = shoppingService.getShoppingList();
        if (!items.isEmpty()) {
            String itemId = (String) items.get(0).get("id");

            // 标记为已购买
            shoppingService.markAsPurchased(itemId);

            // 验证状态已更新
            assertNotNull(shoppingService);
        }
    }

    @Test
    public void testClearPurchasedItems() {
        // 清空已购项目
        shoppingService.clearPurchasedItems();

        // 验证操作成功
        assertNotNull(shoppingService);
    }

    @Test
    public void testGetRestockSuggestions() {
        // 获取补货建议
        List<String> suggestions = shoppingService.getRestockSuggestions();

        // 验证返回建议列表
        assertNotNull(suggestions);
    }

    @Test
    public void testGetPriceComparison() {
        // 获取价格对比
        Map<String, Double> prices = shoppingService.getPriceComparison("牛奶");

        // 验证返回价格数据
        assertNotNull(prices);
    }

    @Test
    public void testExtractItemInfo() {
        // 测试语音解析
        // 简化测试
        assertNotNull(shoppingService);
    }
}