package com.openclaw.homeassistant;

import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.nfc.NfcAdapter;
import android.nfc.Tag;
import android.nfc.tech.Ndef;
import android.nfc.tech.NdefFormatable;
import android.os.Parcelable;
import android.util.Log;

import java.nio.charset.StandardCharsets;

/**
 * NFC 触发服务
 * 功能：刷 NFC 标签触发自动化
 */
public class NfcTriggerService {
    
    private static final String TAG = "NfcTriggerService";
    private static final String PREFS_NAME = "nfc_triggers";
    private static final String NFC_MIME_TYPE = "text/plain";
    
    private final Context context;
    private final SharedPreferences prefs;
    private final NfcAdapter nfcAdapter;
    
    public interface NfcTriggerListener {
        void onNfcTagScanned(String tagId, String action);
    }
    
    private static NfcTriggerListener listener;
    
    public NfcTriggerService(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE);
        this.nfcAdapter = NfcAdapter.getDefaultAdapter(context);
    }
    
    public static void setListener(NfcTriggerListener listener) {
        NfcTriggerService.listener = listener;
    }
    
    /**
     * 检查 NFC 是否可用
     */
    public boolean isNfcAvailable() {
        return nfcAdapter != null && nfcAdapter.isEnabled();
    }
    
    /**
     * 处理 NFC 标签
     */
    public void handleIntent(Intent intent) {
        String action = intent.getAction();
        
        if (NfcAdapter.ACTION_TAG_DISCOVERED.equals(action) ||
            NfcAdapter.ACTION_TECH_DISCOVERED.equals(action) ||
            NfcAdapter.ACTION_NDEF_DISCOVERED.equals(action)) {
            
            Tag tag = intent.getParcelableExtra(NfcAdapter.EXTRA_TAG);
            if (tag != null) {
                String tagId = bytesToHexString(tag.getId());
                Log.d(TAG, "NFC 标签扫描：" + tagId);
                
                // 获取绑定的动作
                String actionId = prefs.getString("nfc_" + tagId, null);
                if (actionId != null) {
                    triggerAction(tagId, actionId);
                } else {
                    // 未绑定动作，提示用户配置
                    Log.d(TAG, "NFC 标签未绑定动作");
                }
                
                if (listener != null) {
                    listener.onNfcTagScanned(tagId, actionId);
                }
            }
        }
    }
    
    /**
     * 绑定 NFC 标签到动作
     */
    public void bindTagToAction(String tagId, String actionId) {
        prefs.edit().putString("nfc_" + tagId, actionId).apply();
        Log.d(TAG, "NFC 标签绑定：" + tagId + " → " + actionId);
    }
    
    /**
     * 解绑 NFC 标签
     */
    public void unbindTag(String tagId) {
        prefs.edit().remove("nfc_" + tagId).apply();
        Log.d(TAG, "NFC 标签解绑：" + tagId);
    }
    
    /**
     * 触发绑定动作
     */
    private void triggerAction(String tagId, String actionId) {
        Log.d(TAG, "触发 NFC 动作：" + actionId);
        
        // 这里可以集成到自动化引擎
        // 暂时发送通知
        NotificationHelper.sendHealthNotification(context,
            "📱 NFC 触发",
            "扫描到 NFC 标签，执行动作：" + actionId);
    }
    
    /**
     * 写入 NFC 标签
     */
    public boolean writeNfcTag(Tag tag, String text) {
        try {
            Ndef ndef = Ndef.get(tag);
            if (ndef != null) {
                // 已有 NDEF 格式
                ndef.connect();
                if (!ndef.isWritable()) {
                    ndef.close();
                    return false;
                }
                
                android.nfc.NdefMessage message = new android.nfc.NdefMessage(
                    new android.nfc.NdefRecord[] {
                        createTextRecord(text)
                    }
                );
                
                ndef.writeNdefMessage(message);
                ndef.close();
                return true;
                
            } else {
                // 需要格式化
                NdefFormatable formatable = NdefFormatable.get(tag);
                if (formatable != null) {
                    formatable.connect();
                    android.nfc.NdefMessage message = new android.nfc.NdefMessage(
                        new android.nfc.NdefRecord[] {
                            createTextRecord(text)
                        }
                    );
                    formatable.format(message);
                    formatable.close();
                    return true;
                }
            }
        } catch (Exception e) {
            Log.e(TAG, "写入 NFC 失败", e);
        }
        return false;
    }
    
    /**
     * 创建文本记录
     */
    private android.nfc.NdefRecord createTextRecord(String text) {
        byte[] textBytes = text.getBytes(StandardCharsets.UTF_8);
        byte[] langBytes = "en".getBytes(StandardCharsets.US_ASCII);
        
        byte[] data = new byte[1 + langBytes.length + textBytes.length];
        data[0] = (byte) (langBytes.length & 0x1F);
        System.arraycopy(langBytes, 0, data, 1, langBytes.length);
        System.arraycopy(textBytes, 0, data, 1 + langBytes.length, textBytes.length);
        
        return new android.nfc.NdefRecord(
            android.nfc.NdefRecord.TNF_WELL_KNOWN,
            android.nfc.NdefRecord.RTD_TEXT,
            new byte[0],
            data
        );
    }
    
    /**
     * 字节数组转十六进制字符串
     */
    private String bytesToHexString(byte[] bytes) {
        StringBuilder sb = new StringBuilder();
        for (byte b : bytes) {
            sb.append(String.format("%02X", b));
        }
        return sb.toString();
    }
    
    /**
     * 获取已绑定的 NFC 标签数量
     */
    public int getBoundTagsCount() {
        return prefs.getAll().size();
    }
}
