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
 * 智能家居设备列表适配器
 */
public class DeviceListAdapter extends RecyclerView.Adapter<DeviceListAdapter.DeviceViewHolder> {
    
    private List<Map<String, Object>> devices = new ArrayList<>();
    private OnDeviceClickListener listener;
    
    public interface OnDeviceClickListener {
        void onDeviceClick(Map<String, Object> device);
    }
    
    public DeviceListAdapter() {
        this.listener = null;
    }
    
    public DeviceListAdapter(OnDeviceClickListener listener) {
        this.listener = listener;
    }
    
    public void setDevices(List<Map<String, Object>> devices) {
        this.devices = devices;
        notifyDataSetChanged();
    }
    
    @NonNull
    @Override
    public DeviceViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View view = LayoutInflater.from(parent.getContext())
                .inflate(android.R.layout.simple_list_item_2, parent, false);
        return new DeviceViewHolder(view);
    }
    
    @Override
    public void onBindViewHolder(@NonNull DeviceViewHolder holder, int position) {
        Map<String, Object> device = devices.get(position);
        String name = (String) device.get("name");
        String status = (String) device.get("status");
        
        holder.txtName.setText(name);
        holder.txtStatus.setText(status);
        
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
    
    static class DeviceViewHolder extends RecyclerView.ViewHolder {
        TextView txtName;
        TextView txtStatus;
        
        DeviceViewHolder(View itemView) {
            super(itemView);
            txtName = itemView.findViewById(android.R.id.text1);
            txtStatus = itemView.findViewById(android.R.id.text2);
        }
    }
}
