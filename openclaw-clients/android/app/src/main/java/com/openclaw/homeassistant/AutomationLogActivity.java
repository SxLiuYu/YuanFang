package com.openclaw.homeassistant;

import android.os.Bundle;
import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.ArrayAdapter;
import android.widget.Button;
import android.widget.ListView;
import android.widget.TextView;

import androidx.appcompat.app.AlertDialog;
import androidx.appcompat.app.AppCompatActivity;

import java.util.ArrayList;
import java.util.List;

/**
 * 自动化日志查看 Activity
 */
public class AutomationLogActivity extends AppCompatActivity {
    
    private ListView listView;
    private LogsAdapter adapter;
    private List<AutomationLogger.LogEntry> logList;
    private AutomationLogger logger;
    private TextView tvEmpty;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_automation_log);
        
        logger = new AutomationLogger(this);
        
        initViews();
        loadLogs();
    }
    
    private void initViews() {
        listView = findViewById(R.id.listView);
        tvEmpty = findViewById(R.id.tvEmpty);
        Button btnClear = findViewById(R.id.btnClear);
        Button btnRefresh = findViewById(R.id.btnRefresh);
        
        logList = new ArrayList<>();
        adapter = new LogsAdapter();
        listView.setAdapter(adapter);
        
        btnClear.setOnClickListener(v -> showClearConfirm());
        btnRefresh.setOnClickListener(v -> loadLogs());
    }
    
    private void loadLogs() {
        logList.clear();
        logList.addAll(logger.getLogs());
        adapter.notifyDataSetChanged();
        
        if (logList.isEmpty()) {
            tvEmpty.setVisibility(View.VISIBLE);
            listView.setVisibility(View.GONE);
        } else {
            tvEmpty.setVisibility(View.GONE);
            listView.setVisibility(View.VISIBLE);
        }
    }
    
    private void showClearConfirm() {
        new AlertDialog.Builder(this)
            .setTitle("确认清空")
            .setMessage("确定要清空所有自动化日志吗？此操作不可恢复。")
            .setPositiveButton("清空", (dialog, which) -> {
                logger.clearLogs();
                loadLogs();
            })
            .setNegativeButton("取消", null)
            .show();
    }
    
    class LogsAdapter extends ArrayAdapter<AutomationLogger.LogEntry> {
        LogsAdapter() {
            super(AutomationLogActivity.this, 0, logList);
        }
        
        @Override
        public View getView(int position, View convertView, ViewGroup parent) {
            if (convertView == null) {
                convertView = LayoutInflater.from(AutomationLogActivity.this)
                    .inflate(R.layout.item_log, parent, false);
            }
            
            AutomationLogger.LogEntry entry = logList.get(position);
            
            TextView tvTime = convertView.findViewById(R.id.tvTime);
            TextView tvTitle = convertView.findViewById(R.id.tvTitle);
            TextView tvDetails = convertView.findViewById(R.id.tvDetails);
            
            tvTime.setText(entry.getFormattedTime());
            tvTitle.setText(entry.getDisplayText());
            tvDetails.setText(entry.details != null ? entry.details : "");
            
            return convertView;
        }
    }
}
