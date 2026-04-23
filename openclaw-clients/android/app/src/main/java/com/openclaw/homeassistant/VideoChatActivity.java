package com.openclaw.homeassistant;

import android.Manifest;
import android.content.pm.PackageManager;
import android.graphics.Bitmap;
import android.graphics.BitmapFactory;
import android.util.Log;
import android.view.MenuItem;
import android.view.View;
import android.widget.Button;
import android.widget.ImageButton;
import android.widget.TextView;
import android.widget.Toast;

import androidx.annotation.NonNull;
import androidx.appcompat.app.AppCompatActivity;
import androidx.appcompat.widget.Toolbar;
import androidx.camera.core.Camera;
import androidx.camera.core.CameraSelector;
import androidx.camera.core.ImageCapture;
import androidx.camera.core.ImageCaptureException;
import androidx.camera.core.Preview;
import androidx.camera.lifecycle.ProcessCameraProvider;
import androidx.camera.view.PreviewView;
import androidx.core.app.ActivityCompat;
import androidx.core.content.ContextCompat;

import android.os.Bundle;

import com.google.common.util.concurrent.ListenableFuture;

import java.io.ByteArrayOutputStream;
import java.io.File;
import java.nio.ByteBuffer;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.Executor;
import java.util.concurrent.Executors;

import okhttp3.MediaType;
import okhttp3.MultipartBody;
import okhttp3.RequestBody;

/**
 * 视频对话界面
 * 支持：
 * 1. 实时摄像头预览
 * 2. 按住说话 + 采集当前帧
 * 3. 发送图像+语音到服务器
 * 4. 服务器返回文字回答 + TTS 音频
 * 5. 播放语音回答
 */
public class VideoChatActivity extends AppCompatActivity {

    private static final String TAG = "VideoChat";
    private static final int REQUEST_CAMERA_PERMISSION = 2001;
    private static final int REQUEST_RECORD_PERMISSION = 2002;

    private PreviewView previewView;
    private TextView tvStatus;
    private TextView tvReply;
    private TextView tvHint;
    private Button btnSwitchCamera;
    private Button btnCapture;
    private ImageButton btnVideoTalk;

    // CameraX
    private ProcessCameraProvider cameraProvider;
    private ImageCapture imageCapture;
    private Executor cameraExecutor;
    private CameraSelector cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA;

    // 语音录制
    private VoiceRecorder voiceRecorder;
    private AudioPlayer audioPlayer;
    private OpenClawApiClient apiClient;

    // 状态
    private boolean isRecording = false;
    private boolean isProcessing = false;
    private String currentWavPath = null;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_video_chat);

        // 初始化服务
        apiClient = new OpenClawApiClient(this);
        voiceRecorder = new VoiceRecorder(this);
        audioPlayer = new AudioPlayer(this);
        cameraExecutor = Executors.newSingleThreadExecutor();

        initViews();
        setupListeners();
        startCamera();
    }

    private void initViews() {
        Toolbar toolbar = findViewById(R.id.toolbar);
        setSupportActionBar(toolbar);
        if (getSupportActionBar() != null) {
            getSupportActionBar().setTitle("视频对话");
            getSupportActionBar().setDisplayHomeAsUpEnabled(true);
        }

        previewView = findViewById(R.id.previewView);
        tvStatus = findViewById(R.id.tvStatus);
        tvReply = findViewById(R.id.tvReply);
        tvHint = findViewById(R.id.tvHint);
        btnSwitchCamera = findViewById(R.id.btnSwitchCamera);
        btnCapture = findViewById(R.id.btnCapture);
        btnVideoTalk = findViewById(R.id.btnVideoTalk);
    }

    private void setupListeners() {
        // 切换摄像头
        btnSwitchCamera.setOnClickListener(v -> {
            if (cameraSelector == CameraSelector.DEFAULT_BACK_CAMERA) {
                cameraSelector = CameraSelector.DEFAULT_FRONT_CAMERA;
            } else {
                cameraSelector = CameraSelector.DEFAULT_BACK_CAMERA;
            }
            startCamera();
        });

        // 拍照提问（单张图片 + 文字输入模式）
        btnCapture.setOnClickListener(v -> captureImageAndAsk());

        // 按住说话视频对话
        btnVideoTalk.setOnTouchListener((v, event) -> {
            switch (event.getAction()) {
                case android.view.MotionEvent.ACTION_DOWN:
                    startVideoVoiceRecording();
                    return true;
                case android.view.MotionEvent.ACTION_UP:
                    stopVideoVoiceRecording();
                    return true;
                default:
                    return false;
            }
        });
    }

    private void startCamera() {
        ListenableFuture<ProcessCameraProvider> cameraProviderFuture =
                ProcessCameraProvider.getInstance(this);

        cameraProviderFuture.addListener(() -> {
            try {
                cameraProvider = cameraProviderFuture.get();

                Preview preview = new Preview.Builder().build();
                preview.setSurfaceProvider(previewView.getSurfaceProvider());

                imageCapture = new ImageCapture.Builder()
                        .setCaptureMode(ImageCapture.CAPTURE_MODE_MINIMIZE_LATENCY)
                        .build();

                cameraProvider.unbindAll();
                Camera camera = cameraProvider.bindToLifecycle(
                        this, cameraSelector, preview, imageCapture);

            } catch (ExecutionException | InterruptedException e) {
                Log.e(TAG, "相机启动失败", e);
                Toast.makeText(this, "相机启动失败: " + e.getMessage(), Toast.LENGTH_SHORT).show();
            }
        }, ContextCompat.getMainExecutor(this));

        // 检查权限
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.CAMERA)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.CAMERA},
                    REQUEST_CAMERA_PERMISSION);
        }
    }

    /**
     * 开始录音 + 显示状态
     */
    private void startVideoVoiceRecording() {
        // 检查权限
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.RECORD_AUDIO},
                    REQUEST_RECORD_PERMISSION);
            return;
        }

        if (audioPlayer.isPlaying()) {
            audioPlayer.interrupt();
        }

        isRecording = true;
        btnVideoTalk.setBackgroundColor(getResources().getColor(android.R.color.holo_red_dark));
        tvStatus.setText("🔴 正在录音 + 准备采集画面...");

        // 开始录音
        voiceRecorder.startRecording(new VoiceRecorder.VoiceRecorderCallback() {
            @Override
            public void onSpeechStart() {
                Log.d(TAG, "Speech started");
            }

            @Override
            public void onSpeechEnd(String wavFilePath) {
                Log.d(TAG, "Speech ended: " + wavFilePath);
                runOnUiThread(() -> {
                    currentWavPath = wavFilePath;
                    processVideoVoiceRequest();
                });
            }

            @Override
            public void onError(String error) {
                Log.e(TAG, "Recording error: " + error);
                runOnUiThread(() -> {
                    Toast.makeText(VideoChatActivity.this, error, Toast.LENGTH_SHORT).show();
                    stopVideoVoiceRecording();
                });
            }
        });
    }

    private void stopVideoVoiceRecording() {
        if (isRecording) {
            voiceRecorder.stopRecording();
            isRecording = false;
            btnVideoTalk.setBackgroundResource(R.drawable.bg_voice_button);
            tvStatus.setText("📹 正在处理...");
        }
    }

    /**
     * 处理视频对话请求：采集当前帧 + 发送音频+图片到服务器
     */
    private void processVideoVoiceRequest() {
        stopVideoVoiceRecording();

        if (imageCapture == null || currentWavPath == null) {
            Toast.makeText(this, "采集失败，请重试", Toast.LENGTH_SHORT).show();
            return;
        }

        File audioFile = new File(currentWavPath);
        if (!audioFile.exists() || audioFile.length() < 1000) {
            Toast.makeText(this, "录音无效，请重试", Toast.LENGTH_SHORT).show();
            return;
        }

        isProcessing = true;
        setButtonsEnabled(false);

        // 捕获当前帧
        imageCapture.takePicture(cameraExecutor, new ImageCapture.OnImageCapturedCallback() {
            @Override
            public void onCaptureSuccess(@NonNull androidx.camera.core.ImageProxy image) {
                Log.d(TAG, "Image captured: " + image.getWidth() + "x" + image.getHeight());

                // 转换为压缩的 JPEG
                Bitmap bitmap = imageToBitmap(image);
                byte[] imageBytes = bitmapToJpeg(bitmap, 80);
                image.close();

                // 发送到服务器
                sendVideoChatRequest(audioFile, imageBytes);

                if (bitmap != null && !bitmap.isRecycled()) {
                    bitmap.recycle();
                }
            }

            @Override
            public void onError(@NonNull ImageCaptureException exception) {
                Log.e(TAG, "Image capture failed", exception);
                runOnUiThread(() -> {
                    Toast.makeText(VideoChatActivity.this,
                            "拍照失败: " + exception.getMessage(), Toast.LENGTH_SHORT).show();
                    isProcessing = false;
                    setButtonsEnabled(true);
                    tvStatus.setText("📹 就绪，按住说话开始视频对话");
                });
            }
        });
    }

    /**
     * 拍照提问 - 单张图片 + 语音
     */
    private void captureImageAndAsk() {
        if (isProcessing) {
            Toast.makeText(this, "正在处理中，请稍候", Toast.LENGTH_SHORT).show();
            return;
        }

        // 检查录音权限
        if (ContextCompat.checkSelfPermission(this, Manifest.permission.RECORD_AUDIO)
                != PackageManager.PERMISSION_GRANTED) {
            ActivityCompat.requestPermissions(this,
                    new String[]{Manifest.permission.RECORD_AUDIO},
                    REQUEST_RECORD_PERMISSION);
            return;
        }

        isProcessing = true;
        setButtonsEnabled(false);
        tvStatus.setText("📸 正在拍照...");

        imageCapture.takePicture(cameraExecutor, new ImageCapture.OnImageCapturedCallback() {
            @Override
            public void onCaptureSuccess(@NonNull androidx.camera.core.ImageProxy image) {
                Log.d(TAG, "Image captured for ask");
                Bitmap bitmap = imageToBitmap(image);
                byte[] imageBytes = bitmapToJpeg(bitmap, 85);
                image.close();

                // 开始录音，提示用户说话
                runOnUiThread(() -> {
                    Toast.makeText(VideoChatActivity.this, "请说出你的问题", Toast.LENGTH_SHORT).show();
                    startVoiceForImage(imageBytes);
                });

                if (bitmap != null && !bitmap.isRecycled()) {
                    bitmap.recycle();
                }
            }

            @Override
            public void onError(@NonNull ImageCaptureException exception) {
                Log.e(TAG, "Capture failed", exception);
                runOnUiThread(() -> {
                    Toast.makeText(VideoChatActivity.this, "拍照失败", Toast.LENGTH_SHORT).show();
                    isProcessing = false;
                    setButtonsEnabled(true);
                    tvStatus.setText("📹 就绪");
                });
            }
        });
    }

    private void startVoiceForImage(byte[] imageBytes) {
        voiceRecorder.startRecording(new VoiceRecorder.VoiceRecorderCallback() {
            @Override
            public void onSpeechStart() {}

            @Override
            public void onSpeechEnd(String wavFilePath) {
                File audioFile = new File(wavFilePath);
                runOnUiThread(() -> {
                    sendImageVoiceRequest(audioFile, imageBytes);
                    VoiceRecorder.deleteFile(wavFilePath);
                });
            }

            @Override
            public void onError(String error) {
                runOnUiThread(() -> {
                    Toast.makeText(VideoChatActivity.this, error, Toast.LENGTH_SHORT).show();
                    isProcessing = false;
                    setButtonsEnabled(true);
                });
            }
        });
    }

    /**
     * 发送视频聊天请求（图片 + 音频）
     */
    private void sendVideoChatRequest(File audioFile, byte[] imageBytes) {
        apiClient.videoChat(audioFile, imageBytes, new OpenClawApiClient.VideoChatCallback() {
            @Override
            public void onSuccess(String text, byte[] ttsAudio) {
                runOnUiThread(() -> {
                    tvReply.setText(text);
                    isProcessing = false;
                    setButtonsEnabled(true);
                    tvStatus.setText("✅ " + text);

                    // 播放 TTS
                    if (ttsAudio != null && ttsAudio.length > 0) {
                        audioPlayer.playWav(ttsAudio, new AudioPlayer.PlaybackCallback() {
                            @Override
                            public void onPlaybackComplete() {
                                Log.d(TAG, "TTS playback complete");
                                runOnUiThread(() -> tvStatus.setText("📹 就绪，按住说话开始视频对话"));
                            }

                            @Override
                            public void onPlaybackError(String error) {
                                runOnUiThread(() -> {
                                    Toast.makeText(VideoChatActivity.this, error, Toast.LENGTH_SHORT).show();
                                    tvStatus.setText("📹 就绪，按住说话开始视频对话");
                                });
                            }
                        });
                    } else {
                        tvStatus.setText("📹 就绪，按住说话开始视频对话");
                    }

                    // 删除临时文件
                    if (currentWavPath != null) {
                        VoiceRecorder.deleteFile(currentWavPath);
                        currentWavPath = null;
                    }
                });
            }

            @Override
            public void onError(String error) {
                runOnUiThread(() -> {
                    Toast.makeText(VideoChatActivity.this, error, Toast.LENGTH_SHORT).show();
                    tvReply.setText("错误: " + error);
                    isProcessing = false;
                    setButtonsEnabled(true);
                    tvStatus.setText("❌ " + error);
                    if (currentWavPath != null) {
                        VoiceRecorder.deleteFile(currentWavPath);
                        currentWavPath = null;
                    }
                });
            }
        });
    }

    /**
     * 发送图片+语音请求（拍照提问模式）
     */
    private void sendImageVoiceRequest(File audioFile, byte[] imageBytes) {
        sendVideoChatRequest(audioFile, imageBytes);
    }

    /**
     * ImageProxy 转 Bitmap
     */
    private Bitmap imageToBitmap(androidx.camera.core.ImageProxy image) {
        ByteBuffer buffer = image.getPlanes()[0].getBuffer();
        byte[] bytes = new byte[buffer.capacity()];
        buffer.get(bytes);
        return BitmapFactory.decodeByteArray(bytes, 0, bytes.length);
    }

    /**
     * Bitmap 压缩为 JPEG 字节数组
     */
    private byte[] bitmapToJpeg(Bitmap bitmap, int quality) {
        ByteArrayOutputStream outputStream = new ByteArrayOutputStream();
        bitmap.compress(Bitmap.CompressFormat.JPEG, quality, outputStream);
        return outputStream.toByteArray();
    }

    private void setButtonsEnabled(boolean enabled) {
        btnSwitchCamera.setEnabled(enabled);
        btnCapture.setEnabled(enabled);
        btnVideoTalk.setEnabled(enabled);
    }

    @Override
    public void onRequestPermissionsResult(int requestCode, @NonNull String[] permissions,
                                           @NonNull int[] grantResults) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);
        if (requestCode == REQUEST_CAMERA_PERMISSION) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startCamera();
            } else {
                Toast.makeText(this, "需要相机权限才能使用视频对话", Toast.LENGTH_SHORT).show();
            }
        } else if (requestCode == REQUEST_RECORD_PERMISSION) {
            if (grantResults.length > 0 && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startVideoVoiceRecording();
            } else {
                Toast.makeText(this, "需要录音权限才能使用语音提问", Toast.LENGTH_SHORT).show();
            }
        }
    }

    @Override
    public boolean onOptionsItemSelected(MenuItem item) {
        if (item.getItemId() == android.R.id.home) {
            finish();
            return true;
        }
        return super.onOptionsItemSelected(item);
    }

    @Override
    protected void onDestroy() {
        super.onDestroy();
        cameraExecutor.shutdown();
        if (audioPlayer != null) {
            audioPlayer.release();
        }
    }
}