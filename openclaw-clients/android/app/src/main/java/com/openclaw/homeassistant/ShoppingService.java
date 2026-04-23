package com.openclaw.homeassistant;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * 智能购物清单服务
 * 支持语音添加、价格对比、补货提醒
 */
public class ShoppingService {
    
    private static final String TAG = "ShoppingService";
    private static final String PREFS_NAME = "shopping_list";
    
    private final Context context;
    private final SharedPreferences prefs;
    private final SimpleDateFormat dateFormat;
    
    public interface ShoppingListener {
        void onItemAdded(String itemName, double estimatedPrice);
        void onLowStockWarning(String itemName, int daysSinceLastPurchase);
        void onPriceDrop(String itemName, double oldPrice, double newPrice);
    }
    
    private static ShoppingListener listener;
    
    public ShoppingService(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        this.dateFormat = new SimpleDateFormat("yyyy-MM-dd", Locale.CHINA);
    }
    
    public static void setListener(ShoppingListener listener) {
        ShoppingService.listener = listener;
    }
    
    /**
     * 添加购物项
     */
    public void addItem(String itemName, String category, int quantity, String unit, 
                       String addedBy) {
        Log.d(TAG, "添加购物项：" + itemName);
        
        try {
            JSONObject item = new JSONObject();
            item.put("id", generateId());
            item.put("name", itemName);
            item.put("category", category != null ? category : categorizeItem(itemName));
            item.put("quantity", quantity);
            item.put("unit", unit != null ? unit : "个");
            item.put("estimated_price", estimatePrice(itemName));
            item.put("is_purchased", false);
            item.put("added_by", addedBy);
            item.put("added_at", dateFormat.format(new Date()));
            
            String key = "item_" + item.getString("id");
            prefs.edit().putString(key, item.toString()).apply();
            
            // 通知监听器
            if (listener != null) {
                listener.onItemAdded(itemName, item.getDouble("estimated_price"));
            }
            
        } catch (Exception e) {
            Log.e(TAG, "添加购物项失败", e);
        }
    }
    
    /**
     * 语音添加（AI 识别）
     */
    public void addItemByVoice(String voiceText, String addedBy) {
        Log.d(TAG, "语音添加：" + voiceText);
        
        // AI 解析语音内容
        // 示例："买 5 瓶牛奶" -> {name: 牛奶，quantity: 5, unit: 瓶}
        
        parseAndAddItem(voiceText, addedBy);
    }
    
    private void parseAndAddItem(String text, String addedBy) {
        // 简单的关键词匹配（实际应使用 AI）
        String itemName = extractItemName(text);
        int quantity = extractQuantity(text);
        String unit = extractUnit(text);
        
        if (!itemName.isEmpty()) {
            addItem(itemName, null, quantity, unit, addedBy);
        }
    }
    
    private String extractItemName(String text) {
        // 提取商品名（简化实现）
        text = text.replace("买", "").replace("添加", "").replace("加入", "");
        text = text.replaceAll("[0-9]+", "").replaceAll("[瓶个盒袋斤公斤]", "");
        return text.trim();
    }
    
    private int extractQuantity(String text) {
        try {
            // 提取数字
            String[] parts = text.split("[^0-9]+");
            for (String part : parts) {
                if (!part.isEmpty()) {
                    return Integer.parseInt(part);
                }
            }
        } catch (Exception e) {
            // ignore
        }
        return 1;
    }
    
    private String extractUnit(String text) {
        if (text.contains("瓶")) return "瓶";
        if (text.contains("盒")) return "盒";
        if (text.contains("袋")) return "袋";
        if (text.contains("斤")) return "斤";
        if (text.contains("公斤")) return "公斤";
        return "个";
    }
    
    private String categorizeItem(String itemName) {
        if (itemName.contains("奶") || itemName.contains("蛋") || itemName.contains("肉") || 
            itemName.contains("菜") || itemName.contains("果")) {
            return "食品";
        } else if (itemName.contains("纸") || itemName.contains("洗") || itemName.contains("洁")) {
            return "日用";
        } else if (itemName.contains("电") || itemName.contains("器")) {
            return "家电";
        }
        return "其他";
    }
    
    private double estimatePrice(String itemName) {
        // 简化实现，返回模拟价格
        return Math.random() * 50 + 5;
    }
    
    /**
     * 标记为已购买
     */
    public void markAsPurchased(String itemId) {
        try {
            String key = "item_" + itemId;
            String itemStr = prefs.getString(key, null);
            
            if (itemStr != null) {
                JSONObject item = new JSONObject(itemStr);
                item.put("is_purchased", true);
                item.put("purchased_at", dateFormat.format(new Date()));
                
                prefs.edit().putString(key, item.toString()).apply();
                
                // 更新消耗统计
                updateConsumptionStats(item.getString("name"));
            }
        } catch (Exception e) {
            Log.e(TAG, "标记购买失败", e);
        }
    }
    
    /**
     * 更新消耗统计
     */
    private void updateConsumptionStats(String itemName) {
        try {
            String key = "consumption_" + itemName;
            String statsStr = prefs.getString(key, null);
            
            long now = System.currentTimeMillis();
            
            if (statsStr != null) {
                JSONObject stats = new JSONObject(statsStr);
                long lastPurchased = stats.getLong("last_purchased_at");
                int count = stats.getInt("purchase_count");
                
                // 计算平均购买间隔
                long daysBetween = (now - lastPurchased) / 86400000;
                int avgDays = (stats.getInt("avg_days") * count + (int)daysBetween) / (count + 1);
                
                stats.put("avg_days", avgDays);
                stats.put("purchase_count", count + 1);
                stats.put("last_purchased_at", now);
                
                prefs.edit().putString(key, stats.toString()).apply();
                
                // 检查是否需要补货提醒
                checkLowStock(itemName, avgDays);
            } else {
                // 首次记录
                JSONObject stats = new JSONObject();
                stats.put("item_name", itemName);
                stats.put("avg_days", 7);  // 默认 7 天
                stats.put("purchase_count", 1);
                stats.put("last_purchased_at", now);
                
                prefs.edit().putString(key, stats.toString()).apply();
            }
        } catch (Exception e) {
            Log.e(TAG, "更新消耗统计失败", e);
        }
    }
    
    /**
     * 检查低库存
     */
    private void checkLowStock(String itemName, int avgDays) {
        // 如果距离上次购买已经超过平均间隔的 80%，发出提醒
        String key = "consumption_" + itemName;
        try {
            JSONObject stats = new JSONObject(prefs.getString(key, null));
            long lastPurchased = stats.getLong("last_purchased_at");
            long daysSince = (System.currentTimeMillis() - lastPurchased) / 86400000;
            
            if (daysSince >= avgDays * 0.8) {
                if (listener != null) {
                    listener.onLowStockWarning(itemName, (int)daysSince);
                }
                
                NotificationHelper.sendHealthNotification(
                    context,
                    "🛒 补货提醒",
                    itemName + " 可能快用完了（距离上次购买 " + daysSince + " 天）"
                );
            }
        } catch (Exception e) {
            // ignore
        }
    }
    
    /**
     * 获取价格对比（模拟实现）
     */
    public Map<String, Double> getPriceComparison(String itemName) {
        Map<String, Double> prices = new HashMap<>();
        
        // 模拟各平台价格（实际应调用电商平台 API）
        prices.put("京东", estimatePrice(itemName) * (0.9 + Math.random() * 0.2));
        prices.put("淘宝", estimatePrice(itemName) * (0.85 + Math.random() * 0.2));
        prices.put("拼多多", estimatePrice(itemName) * (0.8 + Math.random() * 0.15));
        prices.put("盒马", estimatePrice(itemName) * (0.95 + Math.random() * 0.1));
        
        // 记录价格历史
        recordPriceHistory(itemName, prices);
        
        return prices;
    }
    
    /**
     * 记录价格历史
     */
    private void recordPriceHistory(String itemName, Map<String, Double> prices) {
        try {
            JSONArray history = new JSONArray();
            
            for (Map.Entry<String, Double> entry : prices.entrySet()) {
                JSONObject priceRecord = new JSONObject();
                priceRecord.put("platform", entry.getKey());
                priceRecord.put("price", entry.getValue());
                priceRecord.put("recorded_at", dateFormat.format(new Date()));
                history.put(priceRecord);
            }
            
            String key = "price_history_" + itemName;
            prefs.edit().putString(key, history.toString()).apply();
        } catch (Exception e) {
            Log.e(TAG, "记录价格历史失败", e);
        }
    }
    
    /**
     * 获取待购清单
     */
    public List<Map<String, Object>> getShoppingList() {
        List<Map<String, Object>> items = new ArrayList<>();
        
        Map<String, ?> all = prefs.getAll();
        for (Map.Entry<String, ?> entry : all.entrySet()) {
            if (entry.getKey().startsWith("item_")) {
                try {
                    JSONObject item = new JSONObject(entry.getValue().toString());
                    if (!item.getBoolean("is_purchased")) {
                        Map<String, Object> itemData = new HashMap<>();
                        itemData.put("id", item.getString("id"));
                        itemData.put("name", item.getString("name"));
                        itemData.put("category", item.getString("category"));
                        itemData.put("quantity", item.getInt("quantity"));
                        itemData.put("unit", item.getString("unit"));
                        itemData.put("estimated_price", item.getDouble("estimated_price"));
                        items.add(itemData);
                    }
                } catch (Exception e) {
                    // ignore
                }
            }
        }
        
        return items;
    }
    
    /**
     * 获取智能补货建议
     */
    public List<String> getRestockSuggestions() {
        List<String> suggestions = new ArrayList<>();
        
        // 检查所有消耗品统计
        Map<String, ?> all = prefs.getAll();
        for (Map.Entry<String, ?> entry : all.entrySet()) {
            if (entry.getKey().startsWith("consumption_")) {
                try {
                    JSONObject stats = new JSONObject(entry.getValue().toString());
                    long lastPurchased = stats.getLong("last_purchased_at");
                    int avgDays = stats.getInt("avg_days");
                    long daysSince = (System.currentTimeMillis() - lastPurchased) / 86400000;
                    
                    if (daysSince >= avgDays * 0.8) {
                        suggestions.add(stats.getString("item_name"));
                    }
                } catch (Exception e) {
                    // ignore
                }
            }
        }
        
        return suggestions;
    }
    
    /**
     * 清空已购项目
     */
    public void clearPurchasedItems() {
        List<String> keysToRemove = new ArrayList<>();
        
        Map<String, ?> all = prefs.getAll();
        for (Map.Entry<String, ?> entry : all.entrySet()) {
            if (entry.getKey().startsWith("item_")) {
                try {
                    JSONObject item = new JSONObject(entry.getValue().toString());
                    if (item.getBoolean("is_purchased")) {
                        keysToRemove.add(entry.getKey());
                    }
                } catch (Exception e) {
                    // ignore
                }
            }
        }
        
        SharedPreferences.Editor editor = prefs.edit();
        for (String key : keysToRemove) {
            editor.remove(key);
        }
        editor.apply();
    }
    
    /**
     * 生成唯一 ID
     */
    private String generateId() {
        return String.valueOf(System.currentTimeMillis());
    }
}
