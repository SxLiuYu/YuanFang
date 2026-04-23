package com.openclaw.homeassistant;

import android.content.Context;
import android.content.SharedPreferences;
import android.util.Log;

import org.json.JSONArray;
import org.json.JSONObject;

import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * 家庭账本服务
 * 支持收支记录、预算管理、智能报表
 */
public class FinanceService {
    
    private static final String TAG = "FinanceService";
    private static final String PREFS_NAME = "family_finance";
    
    private final Context context;
    private final SharedPreferences prefs;
    private final SimpleDateFormat dateFormat;
    private final SimpleDateFormat monthFormat;
    
    public interface FinanceListener {
        void onBudgetWarning(String category, double budget, double spent);
        void onTransactionAdded(Transaction transaction);
    }
    
    private static FinanceListener listener;
    
    public FinanceService(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        this.dateFormat = new SimpleDateFormat("yyyy-MM-dd", Locale.CHINA);
        this.monthFormat = new SimpleDateFormat("yyyy-MM", Locale.CHINA);
    }
    
    public static void setListener(FinanceListener listener) {
        FinanceService.listener = listener;
    }
    
    /**
     * 添加交易记录
     */
    public void addTransaction(double amount, String type, String category, 
                              String subcategory, String note, String recordedBy) {
        Log.d(TAG, "添加交易：" + type + " " + amount + " - " + category);
        
        try {
            JSONObject transaction = new JSONObject();
            transaction.put("id", generateId());
            transaction.put("amount", amount);
            transaction.put("type", type);  // income or expense
            transaction.put("category", category);
            transaction.put("subcategory", subcategory != null ? subcategory : "");
            transaction.put("note", note != null ? note : "");
            transaction.put("recorded_by", recordedBy);
            transaction.put("recorded_at", dateFormat.format(new Date()));
            
            // 保存到本地存储（简化实现，实际应使用 Room DB）
            String key = "txn_" + transaction.getString("id");
            prefs.edit().putString(key, transaction.toString()).apply();
            
            // 检查预算
            if ("expense".equals(type)) {
                checkBudget(category, amount);
            }
            
            // 通知监听器
            if (listener != null) {
                listener.onTransactionAdded(new Transaction(transaction));
            }
            
        } catch (Exception e) {
            Log.e(TAG, "添加交易失败", e);
        }
    }
    
    /**
     * AI 语音记账（调用 AI 识别）
     */
    public void addTransactionByVoice(String voiceText, String recordedBy) {
        Log.d(TAG, "语音记账：" + voiceText);
        
        // 调用 AI 解析语音内容
        // 示例："今天花了 50 块钱吃饭"
        // AI 应返回：{amount: 50, type: expense, category: 餐饮}
        
        // 这里简化处理，实际应调用 DashScope API
        parseAndAddTransaction(voiceText, recordedBy);
    }
    
    private void parseAndAddTransaction(String text, String recordedBy) {
        // 简单的关键词匹配（实际应使用 AI）
        double amount = extractAmount(text);
        String category = categorizeByText(text);
        
        if (amount > 0) {
            addTransaction(amount, "expense", category, null, text, recordedBy);
        }
    }
    
    private double extractAmount(String text) {
        // 提取金额（简化实现）
        if (text.contains("块") || text.contains("元")) {
            try {
                String[] parts = text.split("[块元]");
                if (parts.length > 0) {
                    return Double.parseDouble(parts[0].replaceAll("[^0-9.]", ""));
                }
            } catch (Exception e) {
                // ignore
            }
        }
        return 0;
    }
    
    private String categorizeByText(String text) {
        if (text.contains("饭") || text.contains("吃") || text.contains("餐")) {
            return "餐饮";
        } else if (text.contains("车") || text.contains("交通") || text.contains("地铁")) {
            return "交通";
        } else if (text.contains("买") || text.contains("购") || text.contains("物")) {
            return "购物";
        } else if (text.contains("玩") || text.contains("娱乐") || text.contains("电影")) {
            return "娱乐";
        } else if (text.contains("药") || text.contains("病") || text.contains("医院")) {
            return "医疗";
        }
        return "其他";
    }
    
    /**
     * 设置预算
     */
    public void setBudget(String category, double amount, String period) {
        try {
            JSONObject budget = new JSONObject();
            budget.put("category", category);
            budget.put("amount", amount);
            budget.put("period", period);  // monthly or yearly
            budget.put("start_date", dateFormat.format(new Date()));
            
            String key = "budget_" + category + "_" + period;
            prefs.edit().putString(key, budget.toString()).apply();
            
            Log.d(TAG, "预算设置成功：" + category + " - " + amount);
        } catch (Exception e) {
            Log.e(TAG, "预算设置失败", e);
        }
    }
    
    /**
     * 检查预算
     */
    private void checkBudget(String category, double amount) {
        String key = "budget_" + category + "_monthly";
        String budgetStr = prefs.getString(key, null);
        
        if (budgetStr != null) {
            try {
                JSONObject budget = new JSONObject(budgetStr);
                double budgetAmount = budget.getDouble("amount");
                
                // 计算本月已花费
                double spent = getMonthTotal(category, "expense");
                
                if (spent >= budgetAmount * 0.8) {
                    // 预算使用超过 80%，发出警告
                    if (listener != null) {
                        listener.onBudgetWarning(category, budgetAmount, spent);
                    }
                    
                    NotificationHelper.sendHealthNotification(
                        context,
                        "💰 预算预警",
                        category + " 本月已花费 " + spent + " 元，预算 " + budgetAmount + " 元"
                    );
                }
            } catch (Exception e) {
                Log.e(TAG, "预算检查失败", e);
            }
        }
    }
    
    /**
     * 获取月度统计
     */
    public Map<String, Double> getMonthStats(String month) {
        Map<String, Double> stats = new HashMap<>();
        
        // 统计各分类支出
        String[] categories = {"餐饮", "交通", "购物", "娱乐", "医疗", "教育", "其他"};
        for (String category : categories) {
            double total = getMonthTotal(category, "expense");
            stats.put(category, total);
        }
        
        return stats;
    }
    
    /**
     * 获取月度总计
     */
    public double getMonthTotal(String category, String type) {
        double total = 0;
        String currentMonth = monthFormat.format(new Date());
        
        // 遍历所有交易记录（简化实现，实际应从数据库查询）
        Map<String, ?> all = prefs.getAll();
        for (Map.Entry<String, ?> entry : all.entrySet()) {
            if (entry.getKey().startsWith("txn_")) {
                try {
                    JSONObject txn = new JSONObject(entry.getValue().toString());
                    String date = txn.getString("recorded_at");
                    String txnType = txn.getString("type");
                    String txnCategory = txn.getString("category");
                    
                    if (date.startsWith(currentMonth) && 
                        txnType.equals(type) && 
                        txnCategory.equals(category)) {
                        total += txn.getDouble("amount");
                    }
                } catch (Exception e) {
                    // ignore
                }
            }
        }
        
        return total;
    }
    
    /**
     * 获取收支趋势（最近 6 个月）
     */
    public List<Map<String, Object>> getTrendData() {
        List<Map<String, Object>> trend = new ArrayList<>();
        
        Calendar calendar = Calendar.getInstance();
        for (int i = 5; i >= 0; i--) {
            calendar.add(Calendar.MONTH, -i);
            String month = monthFormat.format(calendar.getTime());
            
            double income = getTotalByMonth(month, "income");
            double expense = getTotalByMonth(month, "expense");
            
            Map<String, Object> data = new HashMap<>();
            data.put("month", month);
            data.put("income", income);
            data.put("expense", expense);
            data.put("balance", income - expense);
            
            trend.add(data);
        }
        
        return trend;
    }
    
    private double getTotalByMonth(String month, String type) {
        double total = 0;
        
        Map<String, ?> all = prefs.getAll();
        for (Map.Entry<String, ?> entry : all.entrySet()) {
            if (entry.getKey().startsWith("txn_")) {
                try {
                    JSONObject txn = new JSONObject(entry.getValue().toString());
                    String date = txn.getString("recorded_at");
                    String txnType = txn.getString("type");
                    
                    if (date.startsWith(month) && txnType.equals(type)) {
                        total += txn.getDouble("amount");
                    }
                } catch (Exception e) {
                    // ignore
                }
            }
        }
        
        return total;
    }
    
    /**
     * 生成唯一 ID
     */
    private String generateId() {
        return String.valueOf(System.currentTimeMillis());
    }
    
    // ========== 交易记录类 ==========
    
    public static class Transaction {
        public String id;
        public double amount;
        public String type;
        public String category;
        public String subcategory;
        public String note;
        public String recordedBy;
        public String recordedAt;
        
        public Transaction(JSONObject json) throws Exception {
            this.id = json.getString("id");
            this.amount = json.getDouble("amount");
            this.type = json.getString("type");
            this.category = json.getString("category");
            this.subcategory = json.optString("subcategory");
            this.note = json.optString("note");
            this.recordedBy = json.getString("recorded_by");
            this.recordedAt = json.getString("recorded_at");
        }
    }
}
