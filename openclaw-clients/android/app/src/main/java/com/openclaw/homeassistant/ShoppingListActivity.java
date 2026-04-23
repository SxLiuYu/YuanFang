package com.openclaw.homeassistant;

import android.app.AlertDialog;
import android.content.Intent;
import android.os.Bundle;
import android.speech.RecognizerIntent;
import android.util.Log;
import android.view.View;
import android.widget.EditText;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * 智能购物清单界面
 */
public class ShoppingListActivity extends AppCompatActivity implements ShoppingService.ShoppingListener {

    private static final String TAG = "ShoppingListActivity";
    private static final int VOICE_REQUEST_CODE = 1002;

    private ShoppingService shoppingService;
    private TextView txtRestockSuggestions;
    private RecyclerView recyclerShoppingList;

    private ShoppingListAdapter adapter;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_shopping_list);
        
        // 初始化服务
        shoppingService = new ShoppingService(this);
        ShoppingService.setListener(this);
        
        // 绑定 UI 组件
        bindViews();
        
        // 设置按钮
        setupButtons();
        
        // 加载数据
        loadData();
    }
    
    private void bindViews() {
        txtRestockSuggestions = findViewById(R.id.txt_restock_suggestions);
        recyclerShoppingList = findViewById(R.id.recycler_shopping_list);
        
        // 设置 RecyclerView
        recyclerShoppingList.setLayoutManager(new LinearLayoutManager(this));
        adapter = new ShoppingListAdapter();
        recyclerShoppingList.setAdapter(adapter);
    }
    
    private void setupButtons() {
        // 语音添加
        findViewById(R.id.btn_voice_add).setOnClickListener(v -> {
            startVoiceRecognition();
        });

        // 添加物品
        findViewById(R.id.btn_add_item).setOnClickListener(v -> {
            showAddItemDialog();
        });

        // 清空已购
        findViewById(R.id.btn_clear_purchased).setOnClickListener(v -> {
            shoppingService.clearPurchasedItems();
            showToast("已清空已购项目");
            loadData();
        });

        // 价格对比
        findViewById(R.id.btn_price_compare).setOnClickListener(v -> {
            showPriceCompareDialog();
        });
    }

    /**
     * 启动语音识别
     */
    private void startVoiceRecognition() {
        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.CHINA);
        intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "请说出要买的物品，如：买两瓶牛奶");
        try {
            startActivityForResult(intent, VOICE_REQUEST_CODE);
        } catch (Exception e) {
            showToast("语音识别不可用");
            Log.e(TAG, "语音识别启动失败", e);
        }
    }

    /**
     * 显示添加物品对话框
     */
    private void showAddItemDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        View dialogView = getLayoutInflater().inflate(R.layout.dialog_add_shopping_item, null);
        builder.setView(dialogView);
        AlertDialog dialog = builder.create();

        EditText edtItemName = dialogView.findViewById(R.id.edt_item_name);
        EditText edtQuantity = dialogView.findViewById(R.id.edt_quantity);
        EditText edtUnit = dialogView.findViewById(R.id.edt_unit);

        // 取消按钮
        dialogView.findViewById(R.id.btn_cancel).setOnClickListener(v -> dialog.dismiss());

        // 确认按钮
        dialogView.findViewById(R.id.btn_confirm).setOnClickListener(v -> {
            String itemName = edtItemName.getText().toString().trim();
            if (itemName.isEmpty()) {
                showToast("请输入物品名称");
                return;
            }

            String quantityStr = edtQuantity.getText().toString().trim();
            int quantity = quantityStr.isEmpty() ? 1 : Integer.parseInt(quantityStr);

            String unit = edtUnit.getText().toString().trim();
            if (unit.isEmpty()) unit = "个";

            shoppingService.addItem(itemName, "日用品", quantity, unit, "我");
            showToast("已添加：" + itemName);
            dialog.dismiss();
            loadData();
        });

        dialog.show();
    }

    /**
     * 显示价格对比对话框
     */
    private void showPriceCompareDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("价格对比");

        // 获取购物清单中的物品
        List<Map<String, Object>> items = shoppingService.getShoppingList();
        if (items.isEmpty()) {
            builder.setMessage("购物清单为空，请先添加物品");
            builder.setPositiveButton("确定", null);
            builder.show();
            return;
        }

        // 创建物品选择列表
        String[] itemNames = new String[items.size()];
        for (int i = 0; i < items.size(); i++) {
            itemNames[i] = (String) items.get(i).get("item_name");
        }

        builder.setItems(itemNames, (dialog, which) -> {
            String selectedItem = itemNames[which];
            showPriceComparison(selectedItem);
        });

        builder.setNegativeButton("取消", null);
        builder.show();
    }

    /**
     * 显示物品价格对比
     */
    private void showPriceComparison(String itemName) {
        Map<String, Double> prices = shoppingService.getPriceComparison(itemName);

        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle(itemName + " - 价格对比");

        if (prices.isEmpty()) {
            builder.setMessage("暂无价格数据");
        } else {
            StringBuilder sb = new StringBuilder();
            sb.append("各平台价格：\n\n");
            for (Map.Entry<String, Double> entry : prices.entrySet()) {
                sb.append(String.format("%s: ¥%.2f\n", entry.getKey(), entry.getValue()));
            }
            sb.append("\n建议：选择价格最低的平台购买");

            // 找出最低价
            String cheapestPlatform = null;
            double lowestPrice = Double.MAX_VALUE;
            for (Map.Entry<String, Double> entry : prices.entrySet()) {
                if (entry.getValue() < lowestPrice) {
                    lowestPrice = entry.getValue();
                    cheapestPlatform = entry.getKey();
                }
            }
            if (cheapestPlatform != null) {
                sb.append(String.format("\n最便宜：%s (¥%.2f)", cheapestPlatform, lowestPrice));
            }

            builder.setMessage(sb.toString());
        }

        builder.setPositiveButton("确定", null);
        builder.show();
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == VOICE_REQUEST_CODE && resultCode == RESULT_OK && data != null) {
            ArrayList<String> results = data.getStringArrayListExtra(RecognizerIntent.EXTRA_RESULTS);
            if (results != null && !results.isEmpty()) {
                processVoiceInput(results.get(0));
            }
        }
    }

    /**
     * 处理语音输入
     * 支持格式：买两瓶牛奶、买5个苹果
     */
    private void processVoiceInput(String voiceText) {
        Log.d(TAG, "语音输入：" + voiceText);

        // 解析数量
        Pattern quantityPattern = Pattern.compile("(\\d+)");
        Matcher matcher = quantityPattern.matcher(voiceText);
        int quantity = 1;
        if (matcher.find()) {
            quantity = Integer.parseInt(matcher.group(1));
        }

        // 解析单位
        String unit = "个";
        if (voiceText.contains("瓶")) unit = "瓶";
        else if (voiceText.contains("袋")) unit = "袋";
        else if (voiceText.contains("盒")) unit = "盒";
        else if (voiceText.contains("斤")) unit = "斤";
        else if (voiceText.contains("包")) unit = "包";

        // 解析物品名称（移除数字、单位、"买"等词）
        String itemName = voiceText
                .replaceAll("\\d+", "")
                .replace("买", "")
                .replace("瓶", "")
                .replace("袋", "")
                .replace("盒", "")
                .replace("斤", "")
                .replace("包", "")
                .replace("个", "")
                .trim();

        if (!itemName.isEmpty()) {
            shoppingService.addItem(itemName, "日用品", quantity, unit, "我");
            showToast(String.format("已添加：%d%s %s", quantity, unit, itemName));
            loadData();
        } else {
            showToast("未能识别物品名称，请重试");
        }
    }
    
    private void loadData() {
        // 加载购物清单
        List<Map<String, Object>> items = shoppingService.getShoppingList();
        // adapter.setItems(items);
        
        // 加载补货建议
        List<String> suggestions = shoppingService.getRestockSuggestions();
        if (suggestions.isEmpty()) {
            txtRestockSuggestions.setText("暂无补货建议");
        } else {
            StringBuilder sb = new StringBuilder();
            for (String item : suggestions) {
                sb.append(item).append("\n");
            }
            txtRestockSuggestions.setText(sb.toString());
        }
    }
    
    @Override
    public void onItemAdded(String itemName, double estimatedPrice) {
        runOnUiThread(() -> {
            showToast(String.format("已添加 %s (约 ¥%.2f)", itemName, estimatedPrice));
            loadData();
        });
    }
    
    @Override
    public void onLowStockWarning(String itemName, int daysSinceLastPurchase) {
        runOnUiThread(() -> {
            showToast(String.format("⚠️ %s 可能快用完了（%d 天未购买）", itemName, daysSinceLastPurchase));
        });
    }
    
    @Override
    public void onPriceDrop(String itemName, double oldPrice, double newPrice) {
        runOnUiThread(() -> {
            showToast(String.format("💰 %s 降价了！¥%.2f → ¥%.2f", itemName, oldPrice, newPrice));
        });
    }
    
    private void showToast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        ShoppingService.setListener(null);
    }
}
