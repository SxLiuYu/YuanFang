package com.openclaw.homeassistant;

import android.os.Bundle;
import android.util.Log;
import android.widget.Button;
import android.widget.TextView;
import android.widget.Toast;

import androidx.appcompat.app.AppCompatActivity;
import androidx.recyclerview.widget.LinearLayoutManager;
import androidx.recyclerview.widget.RecyclerView;

import java.util.List;
import java.util.Map;

/**
 * 家庭任务板界面
 */
public class FamilyTasksActivity extends AppCompatActivity implements TaskService.TaskListener {
    
    private static final String TAG = "FamilyTasksActivity";
    
    private TaskService taskService;
    private TextView txtLeaderboard;
    private RecyclerView recyclerPendingTasks;
    private RecyclerView recyclerCompletedTasks;
    
    private TaskAdapter pendingTaskAdapter;
    private TaskAdapter completedTaskAdapter;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_family_tasks);
        
        // 初始化服务
        taskService = new TaskService(this);
        TaskService.setListener(this);
        
        // 绑定 UI 组件
        bindViews();
        
        // 设置按钮
        setupButtons();
        
        // 加载数据
        loadData();
    }
    
    private void bindViews() {
        txtLeaderboard = findViewById(R.id.txt_leaderboard);
        recyclerPendingTasks = findViewById(R.id.recycler_pending_tasks);
        recyclerCompletedTasks = findViewById(R.id.recycler_completed_tasks);
        
        // 设置 RecyclerView
        recyclerPendingTasks.setLayoutManager(new LinearLayoutManager(this));
        recyclerCompletedTasks.setLayoutManager(new LinearLayoutManager(this));
        pendingTaskAdapter = new TaskAdapter();
        completedTaskAdapter = new TaskAdapter();
        recyclerPendingTasks.setAdapter(pendingTaskAdapter);
        recyclerCompletedTasks.setAdapter(completedTaskAdapter);
    }
    
    private void setupButtons() {
        // 创建任务
        findViewById(R.id.btn_create_task).setOnClickListener(v -> {
            // TODO: 打开创建任务对话框
            showToast("创建任务功能开发中");
        });
    }
    
    private void loadData() {
        // 加载排行榜
        List<Map<String, Object>> leaderboard = taskService.getLeaderboard();
        StringBuilder sb = new StringBuilder();
        for (int i = 0; i < leaderboard.size(); i++) {
            Map<String, Object> entry = leaderboard.get(i);
            sb.append(i + 1).append(". ").append(entry.get("name"))
              .append(" - ").append(entry.get("points")).append("分\n");
        }
        txtLeaderboard.setText(sb.length() > 0 ? sb.toString() : "暂无数据");
        
        // 加载待办任务
        List<Map<String, Object>> pendingTasks = taskService.getPendingTasks();
        // pendingTaskAdapter.setTasks(pendingTasks);
        
        // 加载已完成任务
        // List<Map<String, Object>> completedTasks = taskService.getCompletedTasks();
        // completedTaskAdapter.setTasks(completedTasks);
    }
    
    @Override
    public void onTaskCompleted(String taskName, String memberName, int points) {
        runOnUiThread(() -> {
            showToast(String.format("✅ %s 完成了 %s，获得 %d 积分", memberName, taskName, points));
            loadData();
        });
    }
    
    @Override
    public void onPointsUpdated(String memberName, int totalPoints) {
        runOnUiThread(() -> {
            Log.d(TAG, memberName + " 积分更新：" + totalPoints);
            loadData();
        });
    }
    
    private void showToast(String message) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show();
    }
    
    @Override
    protected void onDestroy() {
        super.onDestroy();
        TaskService.setListener(null);
    }
}
