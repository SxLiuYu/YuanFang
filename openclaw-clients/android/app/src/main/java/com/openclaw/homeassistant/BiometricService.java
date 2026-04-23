package com.openclaw.homeassistant;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.hardware.biometrics.BiometricManager;
import android.hardware.biometrics.BiometricPrompt;
import android.os.Build;
import android.os.CancellationSignal;
import android.util.Log;

import androidx.annotation.RequiresApi;
import androidx.core.content.ContextCompat;

/**
 * 生物识别服务
 * 支持指纹识别和面部识别
 */
public class BiometricService {
    
    private static final String TAG = "BiometricService";
    private final Context context;
    
    private CancellationSignal cancellationSignal;
    
    public interface BiometricListener {
        void onAuthenticationSucceeded();
        void onAuthenticationFailed();
        void onAuthenticationError(int errorCode, CharSequence errString);
    }
    
    public BiometricService(Context context) {
        this.context = context.getApplicationContext();
    }
    
    /**
     * 检查是否支持生物识别
     */
    public boolean isBiometricSupported() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            BiometricManager biometricManager = (BiometricManager) context.getSystemService(Context.BIOMETRIC_SERVICE);
            if (biometricManager != null) {
                int result = biometricManager.canAuthenticate();
                return result == BiometricManager.BIOMETRIC_SUCCESS;
            }
        }
        return false;
    }
    
    /**
     * 检查是否有 enrolled 的生物特征
     */
    public boolean hasEnrolledBiometrics() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            return context.checkSelfPermission(Manifest.permission.USE_BIOMETRIC) 
                    == PackageManager.PERMISSION_GRANTED;
        }
        return false;
    }
    
    /**
     * 显示生物识别对话框
     */
    @RequiresApi(api = Build.VERSION_CODES.P)
    public void showBiometricPrompt(String title, String subtitle, String description, 
                                    BiometricListener listener) {
        if (!isBiometricSupported()) {
            Log.e(TAG, "设备不支持生物识别");
            if (listener != null) {
                listener.onAuthenticationError(
                    android.hardware.biometrics.BiometricManager.BIOMETRIC_ERROR_NO_HARDWARE,
                    "设备不支持生物识别"
                );
            }
            return;
        }
        
        cancellationSignal = new CancellationSignal();
        
        BiometricPrompt prompt = new BiometricPrompt.Builder(context)
            .setTitle(title)
            .setSubtitle(subtitle)
            .setDescription(description)
            .setNegativeButton("取消", ContextCompat.getMainExecutor(context), 
                (dialogInterface, i) -> {
                    if (listener != null) {
                        listener.onAuthenticationFailed();
                    }
                })
            .build();
        
        prompt.authenticate(cancellationSignal, 
            ContextCompat.getMainExecutor(context),
            new BiometricPrompt.AuthenticationCallback() {
                @Override
                public void onAuthenticationSucceeded(BiometricPrompt.AuthenticationResult result) {
                    Log.d(TAG, "生物识别成功");
                    if (listener != null) {
                        listener.onAuthenticationSucceeded();
                    }
                }
                
                @Override
                public void onAuthenticationFailed() {
                    Log.d(TAG, "生物识别失败");
                    if (listener != null) {
                        listener.onAuthenticationFailed();
                    }
                }
                
                @Override
                public void onAuthenticationError(int errorCode, CharSequence errString) {
                    Log.e(TAG, "生物识别错误：" + errorCode + " - " + errString);
                    if (listener != null) {
                        listener.onAuthenticationError(errorCode, errString);
                    }
                }
            });
    }
    
    /**
     * 取消生物识别
     */
    public void cancel() {
        if (cancellationSignal != null && !cancellationSignal.isCanceled()) {
            cancellationSignal.cancel();
            Log.d(TAG, "取消生物识别");
        }
    }
    
    /**
     * 快速验证（用于支付等敏感操作）
     */
    @RequiresApi(api = Build.VERSION_CODES.P)
    public void quickVerify(String reason, BiometricListener listener) {
        showBiometricPrompt(
            "验证身份",
            "请验证您的身份以继续操作",
            reason,
            listener
        );
    }
    
    /**
     * 登录验证
     */
    @RequiresApi(api = Build.VERSION_CODES.P)
    public void login(BiometricListener listener) {
        showBiometricPrompt(
            "登录家庭助手",
            "使用生物识别快速登录",
            "请验证指纹或面部",
            listener
        );
    }
}
