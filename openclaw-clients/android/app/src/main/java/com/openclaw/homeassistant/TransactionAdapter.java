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
 * 家庭账本交易记录适配器
 */
public class TransactionAdapter extends RecyclerView.Adapter<TransactionAdapter.TransactionViewHolder> {
    
    private List<Map<String, Object>> transactions = new ArrayList<>();
    
    public void setTransactions(List<Map<String, Object>> transactions) {
        this.transactions = transactions;
        notifyDataSetChanged();
    }
    
    @NonNull
    @Override
    public TransactionViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(android.R.layout.simple_list_item_2, parent, false);
        return new TransactionViewHolder(view);
    }
    
    @Override
    public void onBindViewHolder(@NonNull TransactionViewHolder holder, int position) {
        Map<String, Object> transaction = transactions.get(position);
        String description = (String) transaction.get("description");
        Double amount = (Double) transaction.get("amount");
        
        holder.txtDescription.setText(description);
        holder.txtAmount.setText(String.format("¥%.2f", amount));
    }
    
    @Override
    public int getItemCount() {
        return transactions.size();
    }
    
    static class TransactionViewHolder extends RecyclerView.ViewHolder {
        TextView txtDescription;
        TextView txtAmount;
        
        TransactionViewHolder(View itemView) {
            super(itemView);
            txtDescription = itemView.findViewById(android.R.id.text1);
            txtAmount = itemView.findViewById(android.R.id.text2);
        }
    }
}
