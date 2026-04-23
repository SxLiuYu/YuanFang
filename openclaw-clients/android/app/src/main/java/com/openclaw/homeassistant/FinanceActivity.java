package com.openclaw.homeassistant;

import android.app.AlertDialog;
import android.content.Intent;
import android.os.Bundle;
import android.speech.RecognizerIntent;
import android.util.Log;
import android.view.View;
import android.widget.ArrayAdapter;
import android.widget.EditText;
import android.widget.Spinner;
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
 * 家庭账本界面
 */
public class FinanceActivity extends AppCompatActivity implements FinanceService.FinanceListener {

    private static final String TAG = "FinanceActivity";
    private static final int VOICE_REQUEST_CODE = 1001;

    private FinanceService financeService;
    private TextView txtMonthIncome;
    private TextView txtMonthExpense;
    private TextView txtCategoryStats;
    private RecyclerView recyclerTransactions;

    private TransactionAdapter transactionAdapter;
    private List<FinanceService.Transaction> transactions = new ArrayList<>();

    // 支出分类
    private static final String[] EXPENSE_CATEGORIES = {"餐饮", "购物", "交通", "娱乐", "医疗", "教育", "住房", "其他"};
    // 收入分类
    private static final String[] INCOME_CATEGORIES = {"工资", "奖金", "投资", "兼职", "其他"};
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_finance);
        
        // 初始化服务
        financeService = new FinanceService(this);
        FinanceService.setListener(this);
        
        // 绑定 UI 组件
        bindViews();
        
        // 设置按钮
        setupButtons();
        
        // 加载数据
        loadData();
    }
    
    private void bindViews() {
        txtMonthIncome = findViewById(R.id.txt_month_income);
        txtMonthExpense = findViewById(R.id.txt_month_expense);
        txtCategoryStats = findViewById(R.id.txt_category_stats);
        recyclerTransactions = findViewById(R.id.recycler_transactions);
        
        // 设置 RecyclerView
        recyclerTransactions.setLayoutManager(new LinearLayoutManager(this));
        transactionAdapter = new TransactionAdapter();
        recyclerTransactions.setAdapter(transactionAdapter);
    }
    
    private void setupButtons() {
        // 语音记账
        findViewById(R.id.btn_voice_input).setOnClickListener(v -> {
            startVoiceRecognition();
        });

        // 添加交易
        findViewById(R.id.btn_add_transaction).setOnClickListener(v -> {
            showAddTransactionDialog();
        });
    }

    /**
     * 启动语音识别
     */
    private void startVoiceRecognition() {
        Intent intent = new Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE_MODEL, RecognizerIntent.LANGUAGE_MODEL_FREE_FORM);
        intent.putExtra(RecognizerIntent.EXTRA_LANGUAGE, Locale.CHINA);
        intent.putExtra(RecognizerIntent.EXTRA_PROMPT, "请说出金额和分类，如：花了50块钱吃饭");
        try {
            startActivityForResult(intent, VOICE_REQUEST_CODE);
        } catch (Exception e) {
            showToast("语音识别不可用");
            Log.e(TAG, "语音识别启动失败", e);
        }
    }

    /**
     * 显示添加交易对话框
     */
    private void showAddTransactionDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        View dialogView = getLayoutInflater().inflate(R.layout.dialog_add_transaction, null);
        builder.setView(dialogView);
        AlertDialog dialog = builder.create();

        EditText edtAmount = dialogView.findViewById(R.id.edt_amount);
        Spinner spinnerType = dialogView.findViewById(R.id.spinner_type);
        Spinner spinnerCategory = dialogView.findViewById(R.id.spinner_category);
        EditText edtNote = dialogView.findViewById(R.id.edt_note);

        // 设置类型选择
        ArrayAdapter<String> typeAdapter = new ArrayAdapter<>(this,
                android.R.layout.simple_spinner_item, new String[]{"支出", "收入"});
        spinnerType.setAdapter(typeAdapter);

        // 设置分类选择
        spinnerType.setOnItemSelectedListener(new android.widget.AdapterView.OnItemSelectedListener() {
            @Override
            public void onItemSelected(android.widget.AdapterView<?> parent, View view, int position, long id) {
                String[] categories = position == 0 ? EXPENSE_CATEGORIES : INCOME_CATEGORIES;
                ArrayAdapter<String> categoryAdapter = new ArrayAdapter<>(FinanceActivity.this,
                        android.R.layout.simple_spinner_item, categories);
                spinnerCategory.setAdapter(categoryAdapter);
            }

            @Override
            public void onNothingSelected(android.widget.AdapterView<?> parent) {}
        });

        // 取消按钮
        dialogView.findViewById(R.id.btn_cancel).setOnClickListener(v -> dialog.dismiss());

        // 确认按钮
        dialogView.findViewById(R.id.btn_confirm).setOnClickListener(v -> {
            String amountStr = edtAmount.getText().toString().trim();
            if (amountStr.isEmpty()) {
                showToast("请输入金额");
                return;
            }

            try {
                double amount = Double.parseDouble(amountStr);
                String type = spinnerType.getSelectedItemPosition() == 0 ? "expense" : "income";
                String category = spinnerCategory.getSelectedItem().toString();
                String note = edtNote.getText().toString().trim();

                financeService.addTransaction(amount, type, category, null, note, "我");
                showToast("添加成功");
                dialog.dismiss();
                loadData();
            } catch (NumberFormatException e) {
                showToast("请输入有效金额");
            }
        });

        dialog.show();
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
     * 支持格式：花了50块钱吃饭、收入5000工资
     */
    private void processVoiceInput(String voiceText) {
        Log.d(TAG, "语音输入：" + voiceText);

        // 解析金额
        Pattern amountPattern = Pattern.compile("(\\d+(?:\\.\\d+)?)");
        Matcher matcher = amountPattern.matcher(voiceText);
        double amount = 0;
        if (matcher.find()) {
            amount = Double.parseDouble(matcher.group(1));
        }

        // 判断类型
        String type = "expense";
        if (voiceText.contains("收入") || voiceText.contains("赚") || voiceText.contains("工资")) {
            type = "income";
        }

        // 解析分类
        String category = guessCategory(voiceText);

        if (amount > 0) {
            financeService.addTransactionByVoice(voiceText, "我");
            showToast(String.format("已记录：%s %.2f 元 - %s",
                    type.equals("expense") ? "支出" : "收入", amount, category));
            loadData();
        } else {
            showToast("未能识别金额，请重试");
        }
    }

    /**
     * 根据语音文本猜测分类
     */
    private String guessCategory(String text) {
        if (text.contains("吃饭") || text.contains("餐") || text.contains("外卖")) return "餐饮";
        if (text.contains("买") || text.contains("购物")) return "购物";
        if (text.contains("打车") || text.contains("地铁") || text.contains("公交")) return "交通";
        if (text.contains("电影") || text.contains("游戏")) return "娱乐";
        if (text.contains("医院") || text.contains("药")) return "医疗";
        if (text.contains("工资") || text.contains("薪水")) return "工资";
        if (text.contains("奖金")) return "奖金";
        return "其他";
    }
    
    private void loadData() {
        // 加载月度统计
        Map<String, Double> stats = financeService.getMonthStats(null);
        
        double totalIncome = 0; // TODO: 从数据库加载
        double totalExpense = 0;
        for (Double value : stats.values()) {
            totalExpense += value;
        }
        
        txtMonthIncome.setText(String.format("收入\n¥%.2f", totalIncome));
        txtMonthExpense.setText(String.format("支出\n¥%.2f", totalExpense));
        
        // 分类统计
        StringBuilder sb = new StringBuilder();
        for (Map.Entry<String, Double> entry : stats.entrySet()) {
            sb.append(entry.getKey()).append(": ¥").append(String.format("%.2f", entry.getValue())).append("\n");
        }
        txtCategoryStats.setText(sb.length() > 0 ? sb.toString() : "暂无数据");
        
        // 加载交易记录
        // transactionAdapter.setTransactions(...);
    }
    
    @Override
    public void onBudgetWarning(String category, double budget, double spent) {
        runOnUiThread(() -> {
            showToast(String.format("⚠️ %s 预算预警：已花 %.2f，预算 %.2f", category, spent, budget));
        });
    }
    
    @Override
    public void onTransactionAdded(FinanceService.Transaction transaction) {
        runOnUiThread(() -> {
            Log.d(TAG, "添加交易：" + transaction.category + " " + transaction.amount);
            loadData();
        });
    }
    
    private void showToast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        FinanceService.setListener(null);
    }
}
