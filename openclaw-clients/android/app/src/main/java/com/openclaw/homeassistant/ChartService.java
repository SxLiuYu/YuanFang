package com.openclaw.homeassistant;

import android.content.Context;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.graphics.Color;
import android.util.Base64;
import android.util.Log;

import com.github.mikephil.charting.charts.BarChart;
import com.github.mikephil.charting.charts.LineChart;
import com.github.mikephil.charting.charts.PieChart;
import com.github.mikephil.charting.components.Legend;
import com.github.mikephil.charting.components.XAxis;
import com.github.mikephil.charting.data.BarData;
import com.github.mikephil.charting.data.BarDataSet;
import com.github.mikephil.charting.data.BarEntry;
import com.github.mikephil.charting.data.Entry;
import com.github.mikephil.charting.data.LineData;
import com.github.mikephil.charting.data.LineDataSet;
import com.github.mikephil.charting.data.PieEntry;
import com.github.mikephil.charting.utils.ColorTemplate;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 数据可视化服务
 * 集成 MPAndroidChart 图表库
 */
public class ChartService {
    
    private static final String TAG = "ChartService";
    private final Context context;
    
    public ChartService(Context context) {
        this.context = context.getApplicationContext();
    }
    
    /**
     * 生成支出饼图数据
     */
    public List<PieEntry> generateExpensePieData(Map<String, Double> stats) {
        List<PieEntry> entries = new ArrayList<>();
        
        for (Map.Entry<String, Double> entry : stats.entrySet()) {
            entries.add(new PieEntry(entry.getValue().floatValue(), entry.getKey()));
        }
        
        return entries;
    }
    
    /**
     * 生成收支趋势数据
     */
    public LineData generateTrendLineData(List<Map<String, Object>> trendData) {
        LineDataSet incomeSet = new LineDataSet(createLineEntries(trendData, "income"), "收入");
        incomeSet.setColor(Color.GREEN);
        incomeSet.setLineWidth(2f);
        
        LineDataSet expenseSet = new LineDataSet(createLineEntries(trendData, "expense"), "支出");
        expenseSet.setColor(Color.RED);
        expenseSet.setLineWidth(2f);
        
        LineDataSet balanceSet = new LineDataSet(createLineEntries(trendData, "balance"), "结余");
        balanceSet.setColor(Color.BLUE);
        balanceSet.setLineWidth(2f);
        balanceSet.enableDashedLine(10f, 10f, 0f);
        
        return new LineData(incomeSet, expenseSet, balanceSet);
    }
    
    /**
     * 生成分类柱状图数据
     */
    public BarData generateCategoryBarData(Map<String, Double> stats) {
        List<BarEntry> entries = new ArrayList<>();
        int index = 0;
        
        for (Map.Entry<String, Double> entry : stats.entrySet()) {
            entries.add(new BarEntry(index++, entry.getValue().floatValue()));
        }
        
        BarDataSet dataSet = new BarDataSet(entries, "支出");
        dataSet.setColors(ColorTemplate.MATERIAL_COLORS);
        
        return new BarData(dataSet);
    }
    
    /**
     * 生成积分排行榜数据
     */
    public BarData generateLeaderboardData(List<Map<String, Object>> leaderboard) {
        List<BarEntry> entries = new ArrayList<>();
        
        for (int i = 0; i < leaderboard.size(); i++) {
            Map<String, Object> entry = leaderboard.get(i);
            entries.add(new BarEntry(i, ((Number)entry.get("points")).floatValue()));
        }
        
        BarDataSet dataSet = new BarDataSet(entries, "积分");
        dataSet.setColors(ColorTemplate.VORDIPLOM_COLORS);
        
        return new BarData(dataSet);
    }
    
    /**
     * 从 Base64 加载图表图片
     */
    public Bitmap loadChartFromBase64(String base64String) {
        try {
            // 移除 data:image/png;base64, 前缀
            String pureBase64 = base64String.split(",")[1];
            byte[] decodedBytes = Base64.decode(pureBase64, Base64.DEFAULT);
            
            Bitmap bitmap = BitmapFactory.decodeByteArray(decodedBytes, 0, decodedBytes.length);
            Log.d(TAG, "图表加载成功：" + bitmap.getWidth() + "x" + bitmap.getHeight());
            
            return bitmap;
        } catch (Exception e) {
            Log.e(TAG, "图表加载失败", e);
            return null;
        }
    }
    
    // ========== 工具方法 ==========
    
    private List<Entry> createLineEntries(List<Map<String, Object>> trendData, String key) {
        List<Entry> entries = new ArrayList<>();
        
        for (int i = 0; i < trendData.size(); i++) {
            Map<String, Object> data = trendData.get(i);
            entries.add(new Entry(i, ((Number)data.get(key)).floatValue()));
        }
        
        return entries;
    }
    
    // ========== 图表配置 ==========
    
    /**
     * 配置饼图
     */
    public static void configurePieChart(PieChart pieChart) {
        pieChart.setUsePercentValues(true);
        pieChart.getDescription().setEnabled(false);
        pieChart.setExtraOffsets(5, 10, 5, 5);
        pieChart.setDragDecelerationFrictionCoef(0.95f);
        pieChart.setDrawHoleEnabled(true);
        pieChart.setHoleColor(Color.WHITE);
        pieChart.setTransparentCircleRadius(61f);
        
        // 图例配置
        Legend legend = pieChart.getLegend();
        legend.setVerticalAlignment(Legend.LegendVerticalAlignment.TOP);
        legend.setHorizontalAlignment(Legend.LegendHorizontalAlignment.RIGHT);
        legend.setOrientation(Legend.LegendOrientation.VERTICAL);
        legend.setDrawInside(false);
    }
    
    /**
     * 配置折线图
     */
    public static void configureLineChart(LineChart lineChart) {
        lineChart.getDescription().setEnabled(false);
        lineChart.setTouchEnabled(true);
        lineChart.setDragEnabled(true);
        lineChart.setScaleEnabled(true);
        lineChart.setPinchZoom(true);
        
        // X 轴配置
        XAxis xAxis = lineChart.getXAxis();
        xAxis.setPosition(XAxis.XAxisPosition.BOTTOM);
        xAxis.setGranularity(1f);
        xAxis.setGranularityEnabled(true);
        
        // Y 轴配置
        lineChart.getAxisLeft().setGranularity(100f);
        lineChart.getAxisRight().setEnabled(false);
    }
    
    /**
     * 配置柱状图
     */
    public static void configureBarChart(BarChart barChart) {
        barChart.getDescription().setEnabled(false);
        barChart.setFitBars(true);
        barChart.setDrawBarShadow(false);
        barChart.setDrawGridBackground(false);
        
        // 图例配置
        barChart.getLegend().setEnabled(true);
        barChart.getAxisRight().setEnabled(false);
    }
}
