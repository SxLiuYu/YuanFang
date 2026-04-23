package com.openclaw.homeassistant;
import android.util.Log;

import android.graphics.Color;
import android.os.Bundle;
import android.view.View;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;
import androidx.cardview.widget.CardView;

import org.json.JSONObject;

import java.util.List;

/**
 * 健康档案管理界面
 * 支持体重、血压、血糖、运动记录和健康报告
 */
public class HealthProfileActivity extends AppCompatActivity {

    private static final String TAG = "HealthProfileActivity";

    // UI 组件
    private TextView txtMemberName;
    private TextView txtHeight;
    private TextView txtBloodType;
    private CardView cardWeight;
    private CardView cardBloodPressure;
    private CardView cardBloodGlucose;
    private CardView cardExercise;
    private CardView cardMedication;
    private CardView cardHealthReport;

    // 数据显示
    private TextView txtLatestWeight;
    private TextView txtLatestBMI;
    private TextView txtLatestBP;
    private TextView txtBPStatus;
    private TextView txtLatestGlucose;
    private TextView txtGlucoseStatus;
    private TextView txtExerciseSummary;

    // 服务
    private HealthProfileService healthService;

    // 当前档案
    private long currentProfileId = -1;
    private JSONObject currentProfile;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_health_profile);

        healthService = new HealthProfileService(this);

        initViews();
        setupListeners();
        loadOrCreateProfile();
    }

    private void initViews() {
        txtMemberName = findViewById(R.id.txt_member_name);
        txtHeight = findViewById(R.id.txt_height);
        txtBloodType = findViewById(R.id.txt_blood_type);

        cardWeight = findViewById(R.id.card_weight);
        cardBloodPressure = findViewById(R.id.card_blood_pressure);
        cardBloodGlucose = findViewById(R.id.card_blood_glucose);
        cardExercise = findViewById(R.id.card_exercise);
        cardMedication = findViewById(R.id.card_medication);
        cardHealthReport = findViewById(R.id.card_health_report);

        txtLatestWeight = findViewById(R.id.txt_latest_weight);
        txtLatestBMI = findViewById(R.id.txt_latest_bmi);
        txtLatestBP = findViewById(R.id.txt_latest_bp);
        txtBPStatus = findViewById(R.id.txt_bp_status);
        txtLatestGlucose = findViewById(R.id.txt_latest_glucose);
        txtGlucoseStatus = findViewById(R.id.txt_glucose_status);
        txtExerciseSummary = findViewById(R.id.txt_exercise_summary);
    }

    private void setupListeners() {
        // 记录体重
        cardWeight.setOnClickListener(v -> showWeightDialog());

        // 记录血压
        cardBloodPressure.setOnClickListener(v -> showBloodPressureDialog());

        // 记录血糖
        cardBloodGlucose.setOnClickListener(v -> showBloodGlucoseDialog());

        // 记录运动
        cardExercise.setOnClickListener(v -> showExerciseDialog());

        // 用药管理
        cardMedication.setOnClickListener(v -> showMedicationDialog());

        // 健康报告
        cardHealthReport.setOnClickListener(v -> showHealthReport());
    }

    /**
     * 加载或创建健康档案
     */
    private void loadOrCreateProfile() {
        List<JSONObject> profiles = healthService.getProfiles();

        if (profiles.isEmpty()) {
            // 创建默认档案
            showCreateProfileDialog();
        } else {
            // 加载第一个档案
            currentProfile = profiles.get(0);
            try {
                currentProfileId = currentProfile.getLong("profile_id");
                updateProfileDisplay();
                loadLatestData();
            } catch (Exception e) {
                Log.e(TAG, "获取档案ID失败", e);
            }
        }
    }

    /**
     * 显示创建档案对话框
     */
    private void showCreateProfileDialog() {
        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("创建健康档案");

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(50, 40, 50, 10);

        final EditText etName = new EditText(this);
        etName.setHint("姓名");
        layout.addView(etName);

        final EditText etHeight = new EditText(this);
        etHeight.setHint("身高(cm)");
        etHeight.setInputType(android.text.InputType.TYPE_CLASS_NUMBER);
        layout.addView(etHeight);

        builder.setView(layout);

        builder.setPositiveButton("创建", (dialog, which) -> {
            String name = etName.getText().toString().trim();
            String heightStr = etHeight.getText().toString().trim();

            if (!name.isEmpty() && !heightStr.isEmpty()) {
                double height = Double.parseDouble(heightStr);
                currentProfileId = healthService.createProfile(name, "unknown", null, height, null);

                // 重新加载档案
                loadOrCreateProfile();
                Toast.makeText(this, "档案创建成功", Toast.LENGTH_SHORT).show();
            } else {
                Toast.makeText(this, "请填写完整信息", Toast.LENGTH_SHORT).show();
            }
        });

        builder.setNegativeButton("取消", null);
        builder.show();
    }

    /**
     * 更新档案显示
     */
    private void updateProfileDisplay() {
        if (currentProfile == null) return;

        try {
            txtMemberName.setText(currentProfile.getString("member_name"));
            txtHeight.setText(currentProfile.optDouble("height", 0) + " cm");
            txtBloodType.setText(currentProfile.optString("blood_type", "未知"));
} catch (Exception e) {
                Log.e(TAG, "获取档案ID失败", e);
            }
        }

    /**
     * 加载最新数据
     */
    private void loadLatestData() {
        if (currentProfileId < 0) return;

        // 加载最新体重
        List<JSONObject> weights = healthService.getWeightHistory(currentProfileId, 30);
        if (!weights.isEmpty()) {
            try {
                JSONObject latest = weights.get(0);
                txtLatestWeight.setText(latest.getDouble("weight") + " kg");
                txtLatestBMI.setText("BMI: " + latest.getDouble("bmi"));
            } catch (Exception e) {
                Log.e(TAG, "显示最新体重失败", e);
            }
        }

        // 加载最新血压
        List<JSONObject> bps = healthService.getBloodPressureHistory(currentProfileId, 30);
        if (!bps.isEmpty()) {
            try {
                JSONObject latest = bps.get(0);
                txtLatestBP.setText(latest.getInt("systolic") + "/" + latest.getInt("diastolic") + " mmHg");

                JSONObject status = latest.getJSONObject("status");
                txtBPStatus.setText(status.getString("message"));
                txtBPStatus.setTextColor(getColorByStatus(status.getString("color")));
            } catch (Exception e) {
                Log.e(TAG, "显示血压失败", e);
            }
        }

        // 加载运动汇总
        List<JSONObject> exercises = healthService.getExerciseHistory(currentProfileId, 7);
        int totalCalories = 0;
        int totalDuration = 0;
        for (JSONObject ex : exercises) {
            try {
                totalCalories += ex.getInt("calories");
                totalDuration += ex.getInt("duration_minutes");
            } catch (Exception e) {
                Log.e(TAG, "计算运动汇总失败", e);
            }
        }
        txtExerciseSummary.setText("本周: " + exercises.size() + "次运动, " + totalCalories + "千卡, " + totalDuration + "分钟");
    }

    /**
     * 显示记录体重对话框
     */
    private void showWeightDialog() {
        if (currentProfileId < 0) {
            Toast.makeText(this, "请先创建健康档案", Toast.LENGTH_SHORT).show();
            return;
        }

        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("记录体重");

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(50, 40, 50, 10);

        final EditText etWeight = new EditText(this);
        etWeight.setHint("体重(kg)");
        etWeight.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
        layout.addView(etWeight);

        final EditText etNote = new EditText(this);
        etNote.setHint("备注(可选)");
        layout.addView(etNote);

        builder.setView(layout);

        builder.setPositiveButton("保存", (dialog, which) -> {
            String weightStr = etWeight.getText().toString().trim();
            String note = etNote.getText().toString().trim();

            if (!weightStr.isEmpty()) {
                double weight = Double.parseDouble(weightStr);
                healthService.recordWeight(currentProfileId, weight, note);
                Toast.makeText(this, "体重记录成功", Toast.LENGTH_SHORT).show();
                loadLatestData();
            }
        });

        builder.setNegativeButton("取消", null);
        builder.show();
    }

    /**
     * 显示记录血压对话框
     */
    private void showBloodPressureDialog() {
        if (currentProfileId < 0) {
            Toast.makeText(this, "请先创建健康档案", Toast.LENGTH_SHORT).show();
            return;
        }

        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("记录血压");

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(50, 40, 50, 10);

        final EditText etSystolic = new EditText(this);
        etSystolic.setHint("收缩压(高压)");
        etSystolic.setInputType(android.text.InputType.TYPE_CLASS_NUMBER);
        layout.addView(etSystolic);

        final EditText etDiastolic = new EditText(this);
        etDiastolic.setHint("舒张压(低压)");
        etDiastolic.setInputType(android.text.InputType.TYPE_CLASS_NUMBER);
        layout.addView(etDiastolic);

        final EditText etPulse = new EditText(this);
        etPulse.setHint("脉搏(可选)");
        etPulse.setInputType(android.text.InputType.TYPE_CLASS_NUMBER);
        layout.addView(etPulse);

        builder.setView(layout);

        builder.setPositiveButton("保存", (dialog, which) -> {
            String sysStr = etSystolic.getText().toString().trim();
            String diaStr = etDiastolic.getText().toString().trim();
            String pulseStr = etPulse.getText().toString().trim();

            if (!sysStr.isEmpty() && !diaStr.isEmpty()) {
                int systolic = Integer.parseInt(sysStr);
                int diastolic = Integer.parseInt(diaStr);
                Integer pulse = pulseStr.isEmpty() ? null : Integer.parseInt(pulseStr);

                healthService.recordBloodPressure(currentProfileId, systolic, diastolic, pulse, "");
                Toast.makeText(this, "血压记录成功", Toast.LENGTH_SHORT).show();
                loadLatestData();
            }
        });

        builder.setNegativeButton("取消", null);
        builder.show();
    }

    /**
     * 显示记录血糖对话框
     */
    private void showBloodGlucoseDialog() {
        if (currentProfileId < 0) {
            Toast.makeText(this, "请先创建健康档案", Toast.LENGTH_SHORT).show();
            return;
        }

        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("记录血糖");

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(50, 40, 50, 10);

        final EditText etGlucose = new EditText(this);
        etGlucose.setHint("血糖值(mmol/L)");
        etGlucose.setInputType(android.text.InputType.TYPE_CLASS_NUMBER | android.text.InputType.TYPE_NUMBER_FLAG_DECIMAL);
        layout.addView(etGlucose);

        final String[] measureTypes = {"空腹", "餐前", "餐后", "随机"};
        builder.setSingleChoiceItems(measureTypes, 0, null);

        builder.setView(layout);

        builder.setPositiveButton("保存", (dialog, which) -> {
            String glucoseStr = etGlucose.getText().toString().trim();

            if (!glucoseStr.isEmpty()) {
                double glucose = Double.parseDouble(glucoseStr);
                int selectedPosition = ((AlertDialog) dialog).getListView().getCheckedItemPosition();
                String measureType = new String[]{"fasting", "before_meal", "after_meal", "random"}[selectedPosition];

                healthService.recordBloodGlucose(currentProfileId, glucose, measureType, "");
                Toast.makeText(this, "血糖记录成功", Toast.LENGTH_SHORT).show();
                loadLatestData();
            }
        });

        builder.setNegativeButton("取消", null);
        builder.show();
    }

    /**
     * 显示记录运动对话框
     */
    private void showExerciseDialog() {
        if (currentProfileId < 0) {
            Toast.makeText(this, "请先创建健康档案", Toast.LENGTH_SHORT).show();
            return;
        }

        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("记录运动");

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(50, 40, 50, 10);

        final String[] exerciseTypes = {"散步", "跑步", "游泳", "骑行", "瑜伽", "篮球", "羽毛球", "健身"};
        builder.setSingleChoiceItems(exerciseTypes, 0, null);

        final EditText etDuration = new EditText(this);
        etDuration.setHint("时长(分钟)");
        etDuration.setInputType(android.text.InputType.TYPE_CLASS_NUMBER);
        layout.addView(etDuration);

        builder.setView(layout);

        builder.setPositiveButton("保存", (dialog, which) -> {
            String durationStr = etDuration.getText().toString().trim();

            if (!durationStr.isEmpty()) {
                int duration = Integer.parseInt(durationStr);
                int selectedPosition = ((AlertDialog) dialog).getListView().getCheckedItemPosition();
                String[] typeKeys = {"walking", "running", "swimming", "cycling", "yoga", "basketball", "badminton", "gym"};
                String exerciseType = typeKeys[selectedPosition];

                healthService.recordExercise(currentProfileId, exerciseType, duration, null, null, "");
                Toast.makeText(this, "运动记录成功", Toast.LENGTH_SHORT).show();
                loadLatestData();
            }
        });

        builder.setNegativeButton("取消", null);
        builder.show();
    }

    /**
     * 显示用药管理对话框
     */
    private void showMedicationDialog() {
        if (currentProfileId < 0) {
            Toast.makeText(this, "请先创建健康档案", Toast.LENGTH_SHORT).show();
            return;
        }

        AlertDialog.Builder builder = new AlertDialog.Builder(this);
        builder.setTitle("用药管理");

        LinearLayout layout = new LinearLayout(this);
        layout.setOrientation(LinearLayout.VERTICAL);
        layout.setPadding(50, 40, 50, 10);

        final EditText etName = new EditText(this);
        etName.setHint("药品名称");
        layout.addView(etName);

        final EditText etDosage = new EditText(this);
        etDosage.setHint("剂量(如: 1片)");
        layout.addView(etDosage);

        final EditText etFrequency = new EditText(this);
        etFrequency.setHint("频次(如: 每日3次)");
        layout.addView(etFrequency);

        builder.setView(layout);

        builder.setPositiveButton("添加", (dialog, which) -> {
            String name = etName.getText().toString().trim();
            String dosage = etDosage.getText().toString().trim();
            String frequency = etFrequency.getText().toString().trim();

            if (!name.isEmpty()) {
                healthService.addMedication(currentProfileId, name, dosage, frequency, null, "");
                Toast.makeText(this, "用药记录添加成功", Toast.LENGTH_SHORT).show();
            }
        });

        builder.setNegativeButton("取消", null);
        builder.setNeutralButton("查看列表", (dialog, which) -> {
            List<JSONObject> meds = healthService.getMedications(currentProfileId);
            StringBuilder sb = new StringBuilder();
            for (JSONObject med : meds) {
                try {
                    sb.append(med.getString("medication_name"))
                            .append(" - ").append(med.getString("dosage"))
                            .append(" - ").append(med.getString("frequency"))
                            .append("\n");
} catch (Exception e) {
                Log.e(TAG, "构建用药列表失败", e);
            }
        }
            new AlertDialog.Builder(this)
                    .setTitle("用药列表")
                    .setMessage(sb.length() > 0 ? sb.toString() : "暂无用药记录")
                    .setPositiveButton("确定", null)
                    .show();
        });
        builder.show();
    }

    /**
     * 显示健康报告
     */
    private void showHealthReport() {
        if (currentProfileId < 0) {
            Toast.makeText(this, "请先创建健康档案", Toast.LENGTH_SHORT).show();
            return;
        }

        StringBuilder report = new StringBuilder();
        report.append("=== 健康报告 ===\n\n");

        // 体重分析
        List<JSONObject> weights = healthService.getWeightHistory(currentProfileId, 30);
        if (!weights.isEmpty()) {
            try {
                JSONObject latest = weights.get(0);
                report.append("【体重】\n");
                report.append("最新: ").append(latest.getDouble("weight")).append(" kg\n");
                report.append("BMI: ").append(latest.getDouble("bmi")).append("\n\n");
            } catch (Exception e) {
                Log.e(TAG, "构建体重报告失败", e);
            }
        }

        // 血压分析
        List<JSONObject> bps = healthService.getBloodPressureHistory(currentProfileId, 30);
        if (!bps.isEmpty()) {
            try {
                JSONObject latest = bps.get(0);
                report.append("【血压】\n");
                report.append("最新: ").append(latest.getInt("systolic")).append("/")
                        .append(latest.getInt("diastolic")).append(" mmHg\n");
                JSONObject status = latest.getJSONObject("status");
                report.append("状态: ").append(status.getString("message")).append("\n\n");
            } catch (Exception e) {
                Log.e(TAG, "构建血压报告失败", e);
            }
        }

        // 运动分析
        List<JSONObject> exercises = healthService.getExerciseHistory(currentProfileId, 7);
        report.append("【运动(本周)】\n");
        report.append("次数: ").append(exercises.size()).append(" 次\n");

        int totalCalories = 0;
        for (JSONObject ex : exercises) {
            try {
                totalCalories += ex.getInt("calories");
            } catch (Exception e) {
                Log.e(TAG, "计算卡路里失败", e);
            }
        }
        report.append("消耗: ").append(totalCalories).append(" 千卡\n\n");

        // 健康建议
        report.append("【健康建议】\n");
        report.append("• 保持规律作息，每天睡眠7-8小时\n");
        report.append("• 每周运动3-5次，每次30分钟以上\n");
        report.append("• 定期监测血压、血糖等指标\n");

        new AlertDialog.Builder(this)
                .setTitle("健康报告")
                .setMessage(report.toString())
                .setPositiveButton("确定", null)
                .show();
    }

    /**
     * 根据状态获取颜色
     */
    private int getColorByStatus(String color) {
        switch (color) {
            case "green":
                return Color.parseColor("#4CAF50");
            case "yellow":
                return Color.parseColor("#FFC107");
            case "red":
                return Color.parseColor("#F44336");
            case "blue":
                return Color.parseColor("#2196F3");
            default:
                return Color.GRAY;
        }
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        if (healthService != null) {
            healthService.close();
        }
    }
}