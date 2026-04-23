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
 * 自动化日志适配器
 */
public class LogsAdapter extends RecyclerView.Adapter<LogsAdapter.LogsViewHolder> {
    
    private List<Map<String, Object>> logs = new ArrayList<>();
    
    public LogsAdapter() {
    }
    
    public void setLogs(List<Map<String, Object>> logs) {
        this.logs = logs;
        notifyDataSetChanged();
    }
    
    @NonNull
    @Override
    public LogsViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(android.R.layout.simple_list_item_2, parent, false);
        return new LogsViewHolder(view);
    }
    
    @Override
    public void onBindViewHolder(@NonNull LogsViewHolder holder, int position) {
        Map<String, Object> log = logs.get(position);
        String message = (String) log.get("message");
        String timestamp = (String) log.get("timestamp");
        
        holder.txtMessage.setText(message);
        holder.txtTimestamp.setText(timestamp);
    }
    
    @Override
    public int getItemCount() {
        return logs.size();
    }
    
    static class LogsViewHolder extends RecyclerView.ViewHolder {
        TextView txtMessage;
        TextView txtTimestamp;
        
        LogsViewHolder(View itemView) {
            super(itemView);
            txtMessage = itemView.findViewById(android.R.id.text1);
            txtTimestamp = itemView.findViewById(android.R.id.text2);
        }
    }
}
