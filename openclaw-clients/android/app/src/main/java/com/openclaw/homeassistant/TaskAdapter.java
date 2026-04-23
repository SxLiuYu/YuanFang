package com.openclaw.homeassistant;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * 家庭任务列表适配器
 */
public class TaskAdapter extends RecyclerView.Adapter<TaskAdapter.TaskViewHolder> {
    
    private List<Map<String, Object>> tasks = new ArrayList<>();
    private OnTaskClickListener listener;
    
    public interface OnTaskClickListener {
        void onTaskClick(Map<String, Object> task);
    }
    
    public TaskAdapter() {
        this.listener = null;
    }
    
    public TaskAdapter(OnTaskClickListener listener) {
        this.listener = listener;
    }
    
    public void setTasks(List<Map<String, Object>> tasks) {
        this.tasks = tasks;
        notifyDataSetChanged();
    }
    
    @NonNull
    @Override
    public TaskViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(android.R.layout.simple_list_item_2, parent, false);
        return new TaskViewHolder(view);
    }
    
    @Override
    public void onBindViewHolder(@NonNull TaskViewHolder holder, int position) {
        Map<String, Object> task = tasks.get(position);
        String title = (String) task.get("title");
        String assignee = (String) task.get("assignee");
        
        holder.txtTitle.setText(title);
        holder.txtAssignee.setText(assignee != null ? assignee : "");
        
        holder.itemView.setOnClickListener(v -> {
            if (listener != null) {
                listener.onTaskClick(task);
            }
        });
    }
    
    @Override
    public int getItemCount() {
        return tasks.size();
    }
    
    static class TaskViewHolder extends RecyclerView.ViewHolder {
        TextView txtTitle;
        TextView txtAssignee;
        
        TaskViewHolder(View itemView) {
            super(itemView);
            txtTitle = itemView.findViewById(android.R.id.text1);
            txtAssignee = itemView.findViewById(android.R.id.text2);
        }
    }
}
