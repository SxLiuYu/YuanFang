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
 * 自动化规则适配器
 */
public class RulesAdapter extends RecyclerView.Adapter<RulesAdapter.RulesViewHolder> {
    
    private List<Map<String, Object>> rules = new ArrayList<>();
    private OnRuleClickListener listener;
    
    public interface OnRuleClickListener {
        void onRuleClick(Map<String, Object> rule);
    }
    
    public RulesAdapter() {
        this.listener = null;
    }
    
    public RulesAdapter(OnRuleClickListener listener) {
        this.listener = listener;
    }
    
    public void setRules(List<Map<String, Object>> rules) {
        this.rules = rules;
        notifyDataSetChanged();
    }
    
    @NonNull
    @Override
    public RulesViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(android.R.layout.simple_list_item_2, parent, false);
        return new RulesViewHolder(view);
    }
    
    @Override
    public void onBindViewHolder(@NonNull RulesViewHolder holder, int position) {
        Map<String, Object> rule = rules.get(position);
        String name = (String) rule.get("name");
        String description = (String) rule.get("description");
        
        holder.txtName.setText(name);
        holder.txtDescription.setText(description != null ? description : "");
        
        holder.itemView.setOnClickListener(v -> {
            if (listener != null) {
                listener.onRuleClick(rule);
            }
        });
    }
    
    @Override
    public int getItemCount() {
        return rules.size();
    }
    
    static class RulesViewHolder extends RecyclerView.ViewHolder {
        TextView txtName;
        TextView txtDescription;
        
        RulesViewHolder(View itemView) {
            super(itemView);
            txtName = itemView.findViewById(android.R.id.text1);
            txtDescription = itemView.findViewById(android.R.id.text2);
        }
    }
}
