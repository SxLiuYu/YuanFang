package com.openclaw.homeassistant;

import android.app.TimePickerDialog;
import android.content.Intent;
import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.EditText;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ListView;
import android.widget.Spinner;
import android.widget.Switch;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;

import org.json.JSONArray;
import org.json.JSONObject;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/**
 * 自动化规则管理 Activity
 * 功能：
 * 1. 查看规则列表
 * 2. 添加/编辑规则
 * 3. 启用/禁用规则
 * 4. 删除规则
 */
public class AutomationRulesActivity extends AppCompatActivity {
    
    private ConfigManager configManager;
    private ListView listView;
    private RulesAdapter adapter;
    private List<RuleItem> ruleList;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_automation_rules);
        
        configManager = new ConfigManager(this);
        
        initViews();
        loadRules();
    }
    
    private void initViews() {
        listView = findViewById(R.id.listView);
        Button btnAddRule = findViewById(R.id.btnAddRule);
        
        ruleList = new ArrayList<>();
        adapter = new RulesAdapter();
        listView.setAdapter(adapter);
        
        btnAddRule.setOnClickListener(v -> showAddRuleDialog());
    }
    
    private void loadRules() {
        ruleList.clear();
        
        JSONArray rules = configManager.getAutomationRules();
        if (rules == null) {
            adapter.notifyDataSetChanged();
            return;
        }
        
        for (int i = 0; i < rules.length(); i++) {
            try {
                JSONObject rule = rules.getJSONObject(i);
                RuleItem item = new RuleItem();
                item.id = rule.getString("id");
                item.name = rule.getString("name");
                item.enabled = rule.optBoolean("enabled", true);
                item.json = rule;
                ruleList.add(item);
            } catch (Exception e) {
                // 跳过无效规则
            }
        }
        
        adapter.notifyDataSetChanged();
    }
    
    private void showAddRuleDialog() {
        View dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_add_rule, null);
        
        EditText etName = dialogView.findViewById(R.id.etName);
        Spinner spinnerType = dialogView.findViewById(R.id.spinnerType);
        EditText etTime = dialogView.findViewById(R.id.etTime);
        EditText etBatteryLevel = dialogView.findViewById(R.id.etBatteryLevel);
        
        new AlertDialog.Builder(this)
            .setTitle("添加自动化规则")
            .setView(dialogView)
            .setPositiveButton("保存", (dialog, which) -> {
                String name = etName.getText().toString();
                String type = spinnerType.getSelectedItem().toString();
                
                try {
                    JSONObject rule = new JSONObject();
                    rule.put("id", "rule_" + System.currentTimeMillis());
                    rule.put("name", name);
                    rule.put("enabled", true);
                    
                    JSONArray triggers = new JSONArray();
                    JSONObject trigger = new JSONObject();
                    
                    if (type.equals("时间触发")) {
                        String time = etTime.getText().toString();
                        if (time.isEmpty()) time = "07:00";
                        trigger.put("type", "time");
                        trigger.put("time", time);
                    } else if (type.equals("电量触发")) {
                        String level = etBatteryLevel.getText().toString();
                        int levelInt = level.isEmpty() ? 20 : Integer.parseInt(level);
                        trigger.put("type", "battery");
                        trigger.put("level_below", levelInt);
                    }
                    
                    triggers.put(trigger);
                    rule.put("triggers", triggers);
                    
                    // 默认动作：通知
                    JSONArray actions = new JSONArray();
                    JSONObject action = new JSONObject();
                    action.put("type", "notify");
                    action.put("title", name);
                    action.put("message", "规则触发");
                    actions.put(action);
                    rule.put("actions", actions);
                    
                    // 添加到配置
                    JSONArray existingRules = configManager.getAutomationRules();
                    if (existingRules == null) {
                        existingRules = new JSONArray();
                    }
                    existingRules.put(rule);
                    
                    JSONObject automation = new JSONObject();
                    automation.put("enabled", true);
                    automation.put("rules", existingRules);
                    
                    configManager.getConfig().put("automation", automation);
                    configManager.saveConfig();
                    
                    loadRules();
                    Toast.makeText(this, "规则已添加", Toast.LENGTH_SHORT).show();
                    
                } catch (Exception e) {
                    Toast.makeText(this, "保存失败：" + e.getMessage(), Toast.LENGTH_SHORT).show();
                }
            })
            .setNegativeButton("取消", null)
            .show();
    }
    
    private void showEditRuleDialog(RuleItem item) {
        View dialogView = LayoutInflater.from(this).inflate(R.layout.dialog_add_rule, null);
        
        EditText etName = dialogView.findViewById(R.id.etName);
        Spinner spinnerType = dialogView.findViewById(R.id.spinnerType);
        EditText etTime = dialogView.findViewById(R.id.etTime);
        EditText etBatteryLevel = dialogView.findViewById(R.id.etBatteryLevel);
        
        etName.setText(item.name);
        
        try {
            JSONArray triggers = item.json.getJSONArray("triggers");
            if (triggers.length() > 0) {
                JSONObject trigger = triggers.getJSONObject(0);
                String type = trigger.getString("type");
                
                if ("time".equals(type)) {
                    spinnerType.setSelection(0);
                    etTime.setText(trigger.getString("time"));
                } else if ("battery".equals(type)) {
                    spinnerType.setSelection(1);
                    etBatteryLevel.setText(String.valueOf(trigger.getInt("level_below")));
                }
            }
        } catch (Exception e) {
            // 忽略
        }
        
        new AlertDialog.Builder(this)
            .setTitle("编辑规则")
            .setView(dialogView)
            .setPositiveButton("保存", (dialog, which) -> {
                try {
                    item.name = etName.getText().toString();
                    item.json.put("name", item.name);
                    
                    // 更新配置
                    JSONArray rules = configManager.getAutomationRules();
                    for (int i = 0; i < rules.length(); i++) {
                        JSONObject rule = rules.getJSONObject(i);
                        if (rule.getString("id").equals(item.id)) {
                            rules.put(i, item.json);
                            break;
                        }
                    }
                    
                    JSONObject automation = configManager.getConfig().optJSONObject("automation");
                    if (automation != null) {
                        automation.put("rules", rules);
                        configManager.saveConfig();
                    }
                    
                    loadRules();
                    Toast.makeText(this, "规则已更新", Toast.LENGTH_SHORT).show();
                    
                } catch (Exception e) {
                    Toast.makeText(this, "保存失败", Toast.LENGTH_SHORT).show();
                }
            })
            .setNeutralButton("删除", (dialog, which) -> {
                deleteRule(item);
            })
            .setNegativeButton("取消", null)
            .show();
    }
    
    private void deleteRule(RuleItem item) {
        new AlertDialog.Builder(this)
            .setTitle("确认删除")
            .setMessage("确定要删除规则 \"" + item.name + "\" 吗？")
            .setPositiveButton("删除", (dialog, which) -> {
                try {
                    JSONArray rules = configManager.getAutomationRules();
                    JSONArray newRules = new JSONArray();
                    
                    for (int i = 0; i < rules.length(); i++) {
                        JSONObject rule = rules.getJSONObject(i);
                        if (!rule.getString("id").equals(item.id)) {
                            newRules.put(rule);
                        }
                    }
                    
                    JSONObject automation = configManager.getConfig().optJSONObject("automation");
                    if (automation != null) {
                        automation.put("rules", newRules);
                        configManager.saveConfig();
                    }
                    
                    loadRules();
                    Toast.makeText(this, "规则已删除", Toast.LENGTH_SHORT).show();
                    
                } catch (Exception e) {
                    Toast.makeText(this, "删除失败", Toast.LENGTH_SHORT).show();
                }
            })
            .setNegativeButton("取消", null)
            .show();
    }
    
    private void toggleRule(RuleItem item, boolean enabled) {
        try {
            item.enabled = enabled;
            item.json.put("enabled", enabled);
            
            JSONArray rules = configManager.getAutomationRules();
            for (int i = 0; i < rules.length(); i++) {
                JSONObject rule = rules.getJSONObject(i);
                if (rule.getString("id").equals(item.id)) {
                    rules.put(i, item.json);
                    break;
                }
            }
            
            JSONObject automation = configManager.getConfig().optJSONObject("automation");
            if (automation != null) {
                automation.put("rules", rules);
                configManager.saveConfig();
            }
            
            Toast.makeText(this, enabled ? "规则已启用" : "规则已禁用", Toast.LENGTH_SHORT).show();
            
        } catch (Exception e) {
            Toast.makeText(this, "操作失败", Toast.LENGTH_SHORT).show();
        }
    }
    
    class RuleItem {
        String id;
        String name;
        boolean enabled;
        JSONObject json;
    }
    
    class RulesAdapter extends ArrayAdapter<RuleItem> {
        RulesAdapter() {
            super(AutomationRulesActivity.this, 0, ruleList);
        }
        
        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            if (convertView == null) {
                convertView = LayoutInflater.from(AutomationRulesActivity.this)
                    .inflate(R.layout.item_rule, parent, false);
            }
            
            RuleItem item = ruleList.get(position);
            
            TextView tvName = convertView.findViewById(R.id.tvName);
            TextView tvStatus = convertView.findViewById(R.id.tvStatus);
            Switch switchEnabled = convertView.findViewById(R.id.switchEnabled);
            ImageView ivEdit = convertView.findViewById(R.id.ivEdit);
            
            tvName.setText(item.name);
            tvStatus.setText(item.enabled ? "已启用" : "已禁用");
            tvStatus.setTextColor(item.enabled ? 0xFF4CAF50 : 0xFF9E9E9E);
            
            switchEnabled.setChecked(item.enabled);
            switchEnabled.setOnCheckedChangeListener((buttonView, isChecked) -> {
                toggleRule(item, isChecked);
            });
            
            ivEdit.setOnClickListener(v -> {
                showEditRuleDialog(item);
            });
            
            return convertView;
        }
    }
}
