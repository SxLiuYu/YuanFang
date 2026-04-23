package com.openclaw.homeassistant;

import android.graphics.Color;
import android.os.Bundle;
import androidx.appcompat.app.AppCompatActivity;
import android.view.View;
import android.widget.*;

import com.github.mikephil.charting.charts.LineChart;
import com.github.mikephil.charting.charts.PieChart;
import com.github.mikephil.charting.charts.BarChart;
import com.github.mikephil.charting.data.*;
import com.github.mikephil.charting.components.*;
import com.github.mikephil.charting.formatter.ValueFormatter;

import java.util.*;

/**
 * 能源图表 Activity
 * 功能：
 * - 用电趋势折线图（日/周/月）
 * - 设备占比饼图
 * - 电费对比柱状图
 */
public class EnergyChartActivity extends AppCompatActivity {
    
    private EnergyChartService chartService;
    
    // 图表组件
    private LineChart lineChartTrend;
    private PieChart pieChartDistribution;
    private BarChart barChartCost;
    
    // 切换按钮
    private ToggleButton toggleDaily;
    private ToggleButton toggleWeekly;
    private ToggleButton toggleMonthly;
    
    // 统计文本
    private TextView textTotalKwh;
    private TextView textTotalCost;
    private TextView textPeakHour;
    private TextView textAvgDaily;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_energy_chart);
        
        chartService = new EnergyChartService(this);
        
        initViews();
        setupCharts();
        setupListeners();
        
        // 默认加载每日数据
        loadDailyData();
    }
    
    private void initViews() {
        lineChartTrend = findViewById(R.id.line_chart_trend);
        pieChartDistribution = findViewById(R.id.pie_chart_distribution);
        barChartCost = findViewById(R.id.bar_chart_cost);
        
        toggleDaily = findViewById(R.id.toggle_daily);
        toggleWeekly = findViewById(R.id.toggle_weekly);
        toggleMonthly = findViewById(R.id.toggle_monthly);
        
        textTotalKwh = findViewById(R.id.text_total_kwh);
        textTotalCost = findViewById(R.id.text_total_cost);
        textPeakHour = findViewById(R.id.text_peak_hour);
        textAvgDaily = findViewById(R.id.text_avg_daily);
    }
    
    private void setupCharts() {
        // 折线图配置
        setupLineChart();
        
        // 饼图配置
        setupPieChart();
        
        // 柱状图配置
        setupBarChart();
    }
    
    private void setupLineChart() {
        lineChartTrend.getDescription().setEnabled(false);
        lineChartTrend.setDrawGridBackground(false);
        lineChartTrend.setTouchEnabled(true);
        lineChartTrend.setDragEnabled(true);
        lineChartTrend.setScaleEnabled(true);
        lineChartTrend.setPinchZoom(true);
        
        // X 轴
        XAxis xAxis = lineChartTrend.getXAxis();
        xAxis.setPosition(XAxis.XAxisPosition.BOTTOM);
        xAxis.setDrawGridLines(false);
        xAxis.setGranularity(1f);
        xAxis.setLabelCount(24, true);
        xAxis.setValueFormatter(new ValueFormatter() {
            @Override
            public String getFormattedValue(float value) {
                return String.format("%02d:00", (int) value);
            }
        });
        
        // 左 Y 轴
        com.github.mikephil.charting.components.YAxis leftAxis = lineChartTrend.getAxisLeft();
        leftAxis.setDrawGridLines(true);
        leftAxis.setGridColor(Color.LTGRAY);
        
        // 右 Y 轴
        lineChartTrend.getAxisRight().setEnabled(false);
        
        // 图例
        Legend legend = lineChartTrend.getLegend();
        legend.setEnabled(true);
        legend.setVerticalAlignment(Legend.LegendVerticalAlignment.TOP);
        legend.setHorizontalAlignment(Legend.LegendHorizontalAlignment.RIGHT);
    }
    
    private void setupPieChart() {
        pieChartDistribution.getDescription().setEnabled(false);
        pieChartDistribution.setDrawHoleEnabled(true);
        pieChartDistribution.setHoleRadius(40f);
        pieChartDistribution.setTransparentCircleRadius(45f);
        pieChartDistribution.setUsePercentValues(true);
        
        // 中心文本
        pieChartDistribution.setDrawCenterText(true);
        pieChartDistribution.setCenterText("设备占比");
        pieChartDistribution.setCenterTextSize(14f);
        
        // 图例
        Legend legend = pieChartDistribution.getLegend();
        legend.setVerticalAlignment(Legend.LegendVerticalAlignment.BOTTOM);
        legend.setHorizontalAlignment(Legend.LegendHorizontalAlignment.CENTER);
    }
    
    private void setupBarChart() {
        barChartCost.getDescription().setEnabled(false);
        barChartCost.setDrawGridBackground(false);
        barChartCost.setFitBars(true);
        
        // X 轴
        XAxis xAxis = barChartCost.getXAxis();
        xAxis.setPosition(XAxis.XAxisPosition.BOTTOM);
        xAxis.setDrawGridLines(false);
        xAxis.setGranularity(1f);
        
        // Y 轴
        com.github.mikephil.charting.components.YAxis leftAxis = barChartCost.getAxisLeft();
        leftAxis.setDrawGridLines(true);
        leftAxis.setGridColor(Color.LTGRAY);
        
        barChartCost.getAxisRight().setEnabled(false);
    }
    
    private void setupListeners() {
        toggleDaily.setOnCheckedChangeListener((buttonView, isChecked) -> {
            if (isChecked) {
                toggleWeekly.setChecked(false);
                toggleMonthly.setChecked(false);
                loadDailyData();
            }
        });
        
        toggleWeekly.setOnCheckedChangeListener((buttonView, isChecked) -> {
            if (isChecked) {
                toggleDaily.setChecked(false);
                toggleMonthly.setChecked(false);
                loadWeeklyData();
            }
        });
        
        toggleMonthly.setOnCheckedChangeListener((buttonView, isChecked) -> {
            if (isChecked) {
                toggleDaily.setChecked(false);
                toggleWeekly.setChecked(false);
                loadMonthlyData();
            }
        });
    }
    
    private void loadDailyData() {
        chartService.getDailyTrendData(null, new EnergyChartService.DailyTrendCallback() {
            @Override
            public void onTrendData(EnergyChartService.TrendData data) {
                // 设置折线图
                setLineChartData(data);
                
                // 更新统计
                textTotalKwh.setText(String.format("总用电：%.2f 度", data.totalKwh));
                textTotalCost.setText(String.format("总电费：¥%.2f", data.totalCost));
                textPeakHour.setText(String.format("高峰时段：%02d:00", data.peakHour));
            }
            
            @Override
            public void onError(String error) {
                Toast.makeText(EnergyChartActivity.this, "加载失败：" + error, Toast.LENGTH_SHORT).show();
            }
        });
        
        chartService.getDeviceDistributionData(null, new EnergyChartService.DistributionCallback() {
            @Override
            public void onDistributionData(EnergyChartService.DistributionData data) {
                setPieChartData(data);
            }
            
            @Override
            public void onError(String error) {
                // 忽略错误
            }
        });
    }
    
    private void loadWeeklyData() {
        chartService.getWeeklyTrendData(null, new EnergyChartService.WeeklyTrendCallback() {
            @Override
            public void onTrendData(EnergyChartService.WeeklyTrendData data) {
                setBarChartWeeklyData(data);
                textAvgDaily.setText(String.format("日均用电：%.2f 度", data.avgDailyKwh));
            }
            
            @Override
            public void onError(String error) {
                Toast.makeText(EnergyChartActivity.this, "加载失败：" + error, Toast.LENGTH_SHORT).show();
            }
        });
    }
    
    private void loadMonthlyData() {
        chartService.getMonthlyTrendData(0, 0, new EnergyChartService.MonthlyTrendCallback() {
            @Override
            public void onTrendData(EnergyChartService.MonthlyTrendData data) {
                setBarChartMonthlyData(data);
                textAvgDaily.setText(String.format("日均用电：%.2f 度", data.avgDailyKwh));
            }
            
            @Override
            public void onError(String error) {
                Toast.makeText(EnergyChartActivity.this, "加载失败：" + error, Toast.LENGTH_SHORT).show();
            }
        });
    }
    
    private void setLineChartData(EnergyChartService.TrendData data) {
        List<Entry> entries = new ArrayList<>();
        for (int i = 0; i < data.kwhValues.length; i++) {
            entries.add(new Entry(i, data.kwhValues[i]));
        }
        
        LineDataSet dataSet = new LineDataSet(entries, "用电量 (度)");
        dataSet.setColor(Color.parseColor("#4CAF50"));
        dataSet.setCircleColor(Color.parseColor("#4CAF50"));
        dataSet.setLineWidth(2f);
        dataSet.setCircleRadius(3f);
        dataSet.setDrawFilled(true);
        dataSet.setFillColor(Color.parseColor("#81C784"));
        
        LineData lineData = new LineData(dataSet);
        lineChartTrend.setData(lineData);
        lineChartTrend.invalidate();
    }
    
    private void setPieChartData(EnergyChartService.DistributionData data) {
        List<PieEntry> entries = new ArrayList<>();
        for (int i = 0; i < data.labels.length; i++) {
            entries.add(new PieEntry(data.values[i], data.labels[i]));
        }
        
        PieDataSet dataSet = new PieDataSet(entries, "设备用电分布");
        dataSet.setColors(
            Color.parseColor("#FF6384"),
            Color.parseColor("#36A2EB"),
            Color.parseColor("#FFCE56"),
            Color.parseColor("#4BC0C0"),
            Color.parseColor("#9966FF"),
            Color.parseColor("#FF9F40")
        );
        dataSet.setValueTextSize(12f);
        
        PieData pieData = new PieData(dataSet);
        pieChartDistribution.setData(pieData);
        pieChartDistribution.invalidate();
    }
    
    private void setBarChartWeeklyData(EnergyChartService.WeeklyTrendData data) {
        List<BarEntry> entries = new ArrayList<>();
        for (int i = 0; i < data.kwhValues.length; i++) {
            entries.add(new BarEntry(i, data.kwhValues[i]));
        }
        
        BarDataSet dataSet = new BarDataSet(entries, "用电量 (度)");
        dataSet.setColor(Color.parseColor("#4CAF50"));
        dataSet.setValueTextSize(12f);
        
        BarData barData = new BarData(dataSet);
        barData.setBarWidth(0.8f);
        
        barChartCost.setData(barData);
        barChartCost.getXAxis().setValueFormatter(new ValueFormatter() {
            @Override
            public String getFormattedValue(float value) {
                return data.labels[(int) value];
            }
        });
        barChartCost.invalidate();
    }
    
    private void setBarChartMonthlyData(EnergyChartService.MonthlyTrendData data) {
        List<BarEntry> entries = new ArrayList<>();
        for (int i = 0; i < data.kwhValues.length; i++) {
            entries.add(new BarEntry(i, data.kwhValues[i]));
        }
        
        BarDataSet dataSet = new BarDataSet(entries, "用电量 (度)");
        dataSet.setColor(Color.parseColor("#2196F3"));
        dataSet.setValueTextSize(10f);
        
        BarData barData = new BarData(dataSet);
        barData.setBarWidth(0.8f);
        
        barChartCost.setData(barData);
        barChartCost.getXAxis().setValueFormatter(new ValueFormatter() {
            @Override
            public String getFormattedValue(float value) {
                String label = data.labels[(int) value];
                return label.isEmpty() ? "" : label;
            }
        });
        barChartCost.getXAxis().setLabelRotationAngle(45);
        barChartCost.invalidate();
    }
}
