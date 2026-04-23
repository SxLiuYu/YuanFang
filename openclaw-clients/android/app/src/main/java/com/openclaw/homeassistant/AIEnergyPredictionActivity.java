package com.openclaw.homeassistant;

import android.os.Bundle;
import android.view.View;
import android.widget.*;
import androidx.appcompat.app.AppCompatActivity;
import androidx.cardview.widget.CardView;

import java.util.*;

/**
 * AI 用电预测 Activity
 * 功能：
 * - 未来 7 天用电预测
 * - 月度电费预测
 * - 异常用电检测
 * - AI 智能节能建议
 */
public class AIEnergyPredictionActivity extends AppCompatActivity {
    
    private AIEnergyPredictionService predictionService;
    
    // UI 组件
    private TextView textPredictionSummary;
    private TextView textMonthlyForecast;
    private TextView textAnomalyStatus;
    private ListView listPredictions;
    private ListView listSuggestions;
    private CardView cardPrediction;
    private CardView cardMonthly;
    private CardView cardAnomaly;
    private CardView cardSuggestions;
    private Button btnTrainModel;
    private ProgressBar progressLoading;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_ai_prediction);
        
        predictionService = new AIEnergyPredictionService(this);
        
        initViews();
        loadPredictions();
    }
    
    private void initViews() {
        textPredictionSummary = findViewById(R.id.text_prediction_summary);
        textMonthlyForecast = findViewById(R.id.text_monthly_forecast);
        textAnomalyStatus = findViewById(R.id.text_anomaly_status);
        listPredictions = findViewById(R.id.list_predictions);
        listSuggestions = findViewById(R.id.list_suggestions);
        cardPrediction = findViewById(R.id.card_prediction);
        cardMonthly = findViewById(R.id.card_monthly);
        cardAnomaly = findViewById(R.id.card_anomaly);
        cardSuggestions = findViewById(R.id.card_suggestions);
        btnTrainModel = findViewById(R.id.btn_train_model);
        progressLoading = findViewById(R.id.progress_loading);
        
        btnTrainModel.setOnClickListener(v -> trainModel());
    }
    
    private void loadPredictions() {
        progressLoading.setVisibility(View.VISIBLE);
        
        // 加载每日预测
        predictionService.predictDailyUsage(7, new AIEnergyPredictionService.PredictDailyCallback() {
            @Override
            public void onPrediction(AIEnergyPredictionService.PredictionResult result) {
                displayDailyPredictions(result);
                progressLoading.setVisibility(View.GONE);
            }
            
            @Override
            public void onError(String error) {
                Toast.makeText(AIEnergyPredictionActivity.this, "加载预测失败：" + error, Toast.LENGTH_SHORT).show();
                progressLoading.setVisibility(View.GONE);
            }
        });
        
        // 加载月度预测
        predictionService.predictMonthlyBill(null, null, new AIEnergyPredictionService.PredictMonthlyCallback() {
            @Override
            public void onPrediction(AIEnergyPredictionService.MonthlyPrediction prediction) {
                displayMonthlyPrediction(prediction);
            }
            
            @Override
            public void onError(String error) {
                // 忽略错误
            }
        });
        
        // 加载异常检测
        predictionService.detectAnomalies(7, new AIEnergyPredictionService.AnomalyCallback() {
            @Override
            public void onAnomalyResult(AIEnergyPredictionService.AnomalyResult result) {
                displayAnomalyResult(result);
            }
            
            @Override
            public void onError(String error) {
                // 忽略错误
            }
        });
        
        // 加载智能建议
        predictionService.getSmartSuggestions(new AIEnergyPredictionService.SuggestionCallback() {
            @Override
            public void onSuggestions(List<AIEnergyPredictionService.Suggestion> suggestions, float totalSaving) {
                displaySuggestions(suggestions, totalSaving);
            }
            
            @Override
            public void onError(String error) {
                // 忽略错误
            }
        });
    }
    
    private void displayDailyPredictions(AIEnergyPredictionService.PredictionResult result) {
        List<String> items = new ArrayList<>();
        
        for (AIEnergyPredictionService.DailyPrediction p : result.predictions) {
            String weekday = translateWeekday(p.weekday);
            items.add(String.format(
                "%s %s: %.2f度 ¥%.2f (可信度 %.0f%%)",
                p.date.substring(5), weekday, p.predictedKwh, p.predictedCost, p.confidence * 100
            ));
        }
        
        ArrayAdapter<String> adapter = new ArrayAdapter<>(
            this,
            android.R.layout.simple_list_item_1,
            items
        );
        listPredictions.setAdapter(adapter);
        
        textPredictionSummary.setText(String.format(
            "未来 7 天预计用电 %.1f 度，电费 ¥%.2f，日均 %.1f 度",
            result.totalKwh, result.totalCost, result.avgDailyKwh
        ));
    }
    
    private void displayMonthlyPrediction(AIEnergyPredictionService.MonthlyPrediction prediction) {
        String trendEmoji = "up".equals(prediction.trend) ? "📈" : "down".equals(prediction.trend) ? "📉" : "➡️";
        
        textMonthlyForecast.setText(String.format(
            "%s 预测电费：¥%.2f\n上月：¥%.2f 变化：%.1f%% %s",
            prediction.period, prediction.predictedCost, prediction.lastMonthCost,
            Math.abs(prediction.monthOverMonthChange), trendEmoji
        ));
    }
    
    private void displayAnomalyResult(AIEnergyPredictionService.AnomalyResult result) {
        if (result.anomaliesCount == 0) {
            textAnomalyStatus.setText("✅ 用电模式正常，无异常 detected");
        } else {
            String severity = result.anomalies.stream()
                .anyMatch(a -> "critical".equals(a.severity)) ? "⚠️" : "⚡";
            
            textAnomalyStatus.setText(String.format(
                "%s 发现 %d 个用电异常（平均 %.1f 度/天）",
                severity, result.anomaliesCount, result.meanDailyKwh
            ));
        }
    }
    
    private void displaySuggestions(List<AIEnergyPredictionService.Suggestion> suggestions, float totalSaving) {
        List<String> items = new ArrayList<>();
        
        for (AIEnergyPredictionService.Suggestion s : suggestions) {
            String priority = "high".equals(s.priority) ? "🔴" : "🟡";
            String saving = s.potentialSaving > 0 ? String.format(" (预计省¥%.2f)", s.potentialSaving) : "";
            
            items.add(priority + " " + s.message + saving);
            
            if (s.tips != null && !s.tips.isEmpty()) {
                for (String tip : s.tips) {
                    items.add("   💡 " + tip);
                }
            }
        }
        
        ArrayAdapter<String> adapter = new ArrayAdapter<>(
            this,
            android.R.layout.simple_list_item_1,
            items
        );
        listSuggestions.setAdapter(adapter);
    }
    
    private void trainModel() {
        progressLoading.setVisibility(View.VISIBLE);
        
        predictionService.trainModel(30, new AIEnergyPredictionService.TrainCallback() {
            @Override
            public void onTrainComplete(boolean success, String message) {
                progressLoading.setVisibility(View.GONE);
                Toast.makeText(
                    AIEnergyPredictionActivity.this,
                    success ? "模型训练完成：" + message : "训练失败：" + message,
                    Toast.LENGTH_SHORT
                ).show();
                
                if (success) {
                    loadPredictions();
                }
            }
            
            @Override
            public void onError(String error) {
                progressLoading.setVisibility(View.GONE);
                Toast.makeText(AIEnergyPredictionActivity.this, "训练失败：" + error, Toast.LENGTH_SHORT).show();
            }
        });
    }
    
    private String translateWeekday(String weekday) {
        Map<String, String> map = new HashMap<>();
        map.put("Monday", "周一");
        map.put("Tuesday", "周二");
        map.put("Wednesday", "周三");
        map.put("Thursday", "周四");
        map.put("Friday", "周五");
        map.put("Saturday", "周六");
        map.put("Sunday", "周日");
        return map.getOrDefault(weekday, weekday);
    }
}
