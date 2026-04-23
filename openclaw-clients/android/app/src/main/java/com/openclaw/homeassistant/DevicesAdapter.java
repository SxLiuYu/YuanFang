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
 * 设备列表适配器
 */
public class DevicesAdapter extends RecyclerView.Adapter<DevicesAdapter.DevicesViewHolder> {
    
    private List<Map<String, Object>> devices = new ArrayList<>();
    private OnDeviceClickListener listener;
    
    public interface OnDeviceClickListener {
        void onDeviceClick(Map<String, Object> device);
    }
    
    public DevicesAdapter() {
        this.listener = null;
    }
    
    public DevicesAdapter(OnDeviceClickListener listener) {
        this.listener = listener;
    }
    
    public void setDevices(List<Map<String, Object>> devices) {
        this.devices = devices;
        notifyDataSetChanged();
    }
    
    @NonNull
    @Override
    public DevicesViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(android.R.layout.simple_list_item_2, parent, false);
        return new DevicesViewHolder(view);
    }
    
    @Override
    public void onBindViewHolder(@NonNull DevicesViewHolder holder, int position) {
        Map<String, Object> device = devices.get(position);
        String name = (String) device.get("name");
        String type = (String) device.get("type");
        
        holder.txtName.setText(name);
        holder.txtType.setText(type);
        
        holder.itemView.setOnClickListener(v -> {
            if (listener != null) {
                listener.onDeviceClick(device);
            }
        });
    }
    
    @Override
    public int getItemCount() {
        return devices.size();
    }
    
    static class DevicesViewHolder extends RecyclerView.ViewHolder {
        TextView txtName;
        TextView txtType;
        
        DevicesViewHolder(View itemView) {
            super(itemView);
            txtName = itemView.findViewById(android.R.id.text1);
            txtType = itemView.findViewById(android.R.id.text2);
        }
    }
}
