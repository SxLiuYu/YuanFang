package com.openclaw.homeassistant;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.CheckBox;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;

/**
 * 购物清单适配器
 */
public class ShoppingListAdapter extends RecyclerView.Adapter<ShoppingListAdapter.ShoppingListViewHolder> {
    
    private List<Map<String, Object>> items = new ArrayList<>();
    private OnItemClickListener listener;
    
    public interface OnItemClickListener {
        void onItemCheck(Map<String, Object> item, boolean isChecked);
    }
    
    public ShoppingListAdapter() {
        this.listener = null;
    }
    
    public ShoppingListAdapter(OnItemClickListener listener) {
        this.listener = listener;
    }
    
    public void setItems(List<Map<String, Object>> items) {
        this.items = items;
        notifyDataSetChanged();
    }
    
    @NonNull
    @Override
    public ShoppingListViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(android.R.layout.simple_list_item_multiple_choice, parent, false);
        return new ShoppingListViewHolder(view);
    }
    
    @Override
    public void onBindViewHolder(@NonNull ShoppingListViewHolder holder, int position) {
        Map<String, Object> item = items.get(position);
        String name = (String) item.get("name");
        Boolean checked = (Boolean) item.get("checked");
        
        holder.txtName.setText(name);
        holder.checkBox.setChecked(checked != null && checked);
        
        holder.checkBox.setOnCheckedChangeListener((buttonView, isChecked) -> {
            if (listener != null) {
                listener.onItemCheck(item, isChecked);
            }
        });
    }
    
    @Override
    public int getItemCount() {
        return items.size();
    }
    
    static class ShoppingListViewHolder extends RecyclerView.ViewHolder {
        TextView txtName;
        CheckBox checkBox;
        
        ShoppingListViewHolder(View itemView) {
            super(itemView);
            txtName = itemView.findViewById(android.R.id.text1);
            checkBox = itemView.findViewById(android.R.id.checkbox);
        }
    }
}
