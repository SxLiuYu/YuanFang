package com.openclaw.homeassistant;

import android.Manifest;
import android.content.Context;
import android.content.pm.PackageManager;
import android.media.AudioFormat;
import android.media.AudioRecord;
import android.media.MediaRecorder;
import android.os.Environment;
import android.util.Log;

import androidx.core.app.ActivityCompat;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

/**
 * 语音录音工具类
 * 支持 VAD（语音活动检测）通过能量阈值
 * 输出 16kHz 16-bit 单声道 WAV 格式，兼容服务端要求
 */
public class VoiceRecorder {
    private static final String TAG = "VoiceRecorder";

    // 音频参数 - 服务端要求 16kHz 16-bit 单声道
    public static final int SAMPLE_RATE = 16000;
    public static final int CHANNEL_CONFIG = AudioFormat.CHANNEL_IN_MONO;
    public static final int AUDIO_FORMAT = AudioFormat.ENCODING_PCM_16BIT;
    public static final int BUFFER_SIZE = AudioRecord.getMinBufferSize(
            SAMPLE_RATE, CHANNEL_CONFIG, AUDIO_FORMAT);

    // VAD 参数
    private static final float ENERGY_THRESHOLD = 0.0003f;  // 能量阈值
    private static final int SILENCE_FRAMES = 30;  // 多少帧静音后停止录音 (~0.3秒)
    private static final int MAX_SPEECH_SECONDS = 30;  // 最大录音时长
    private static final int MIN_SPEECH_FRAMES = 10;  // 最小语音帧数 (~0.1秒)

    private Context context;
    private AudioRecord audioRecord;
    private boolean isRecording = false;
    private boolean isSpeaking = false;
    private int silenceCount = 0;
    private int speechFrames = 0;
    private short[] buffer;
    private byte[] pcmData;
    private int pcmOffset = 0;

    // 回调接口
    public interface VoiceRecorderCallback {
        void onSpeechStart();  // 检测到说话开始
        void onSpeechEnd(String wavFilePath);  // 说话结束，返回 WAV 文件路径
        void onError(String error);  // 出错
    }

    public VoiceRecorder(Context context) {
        this.context = context;
        this.buffer = new short[BUFFER_SIZE / 2];  // 16-bit = 2 bytes per sample
    }

    /**
     * 检查录音权限
     */
    public boolean hasRecordPermission() {
        return ActivityCompat.checkSelfPermission(context,
                Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED;
    }

    /**
     * 开始录音（后台线程）
     */
    public void startRecording(VoiceRecorderCallback callback) {
        if (isRecording) {
            Log.w(TAG, "Already recording");
            return;
        }

        if (!hasRecordPermission()) {
            callback.onError("没有录音权限");
            return;
        }

        // 初始化 AudioRecord
        try {
            audioRecord = new AudioRecord(
                    MediaRecorder.AudioSource.MIC,
                    SAMPLE_RATE,
                    CHANNEL_CONFIG,
                    AUDIO_FORMAT,
                    BUFFER_SIZE * 2
            );

            if (audioRecord.getState() != AudioRecord.STATE_INITIALIZED) {
                callback.onError("AudioRecord 初始化失败");
                return;
            }
        } catch (Exception e) {
            Log.e(TAG, "Failed to init AudioRecord", e);
            callback.onError("初始化失败: " + e.getMessage());
            return;
        }

        // 重置状态
        isRecording = true;
        isSpeaking = false;
        silenceCount = 0;
        speechFrames = 0;
        pcmOffset = 0;
        int maxSamples = SAMPLE_RATE * MAX_SPEECH_SECONDS;
        pcmData = new byte[maxSamples * 2];  // 16-bit = 2 bytes

        Log.d(TAG, "Started recording, buffer size: " + BUFFER_SIZE);

        // 开始录音
        audioRecord.startRecording();

        // 录音线程
        Thread recordingThread = new Thread(() -> {
            processRecording(callback);
        }, "VoiceRecorderThread");
        recordingThread.start();
    }

    /**
     * 停止录音
     */
    public void stopRecording() {
        isRecording = false;
        if (audioRecord != null) {
            try {
                if (audioRecord.getState() == AudioRecord.STATE_INITIALIZED) {
                    audioRecord.stop();
                }
                audioRecord.release();
            } catch (Exception e) {
                Log.e(TAG, "Error stopping recording", e);
            } finally {
                audioRecord = null;
            }
        }
        Log.d(TAG, "Stopped recording");
    }

    /**
     * 处理录音和 VAD 检测
     */
    private void processRecording(VoiceRecorderCallback callback) {
        while (isRecording) {
            int framesRead = audioRecord.read(buffer, 0, buffer.length);

            if (framesRead < 0) {
                Log.e(TAG, "Error reading audio: " + framesRead);
                continue;
            }

            // 计算当前帧能量
            float energy = calculateEnergy(buffer, framesRead);

            // VAD 逻辑
            boolean isCurrentSpeech = energy > ENERGY_THRESHOLD;

            if (isCurrentSpeech) {
                silenceCount = 0;
                speechFrames++;

                if (!isSpeaking && speechFrames > MIN_SPEECH_FRAMES) {
                    isSpeaking = true;
                    Log.d(TAG, "Speech started, energy: " + energy);
                    context.getMainLooper().getHandler().post(() -> {
                        callback.onSpeechStart();
                    });
                }
            } else {
                if (isSpeaking) {
                    silenceCount++;
                    if (silenceCount > SILENCE_FRAMES) {
                        // 静音足够长时间，停止录音
                        Log.d(TAG, "Speech ended, silence frames: " + silenceCount);
                        isRecording = false;
                    }
                }
            }

            // 将 PCM 数据存入缓冲区
            for (int i = 0; i < framesRead; i++) {
                short sample = buffer[i];
                pcmData[pcmOffset++] = (byte) (sample & 0xFF);
                pcmData[pcmOffset++] = (byte) ((sample >> 8) & 0xFF);
            }

            // 超过最大时长，停止
            if (pcmOffset >= pcmData.length) {
                isRecording = false;
                Log.d(TAG, "Reached max recording duration");
                break;
            }
        }

        // 录音结束，保存 WAV 文件
        String wavPath = savePcmToWav();
        if (wavPath != null && pcmOffset > 1000 && isSpeaking) {
            // 有有效语音
            context.getMainLooper().getHandler().post(() -> {
                callback.onSpeechEnd(wavPath);
            });
        } else if (pcmOffset > 0 && isSpeaking) {
            // 录音太短或没有语音
            context.getMainLooper().getHandler().post(() -> {
                callback.onError("录音太短，请重新说话");
            });
        }

        // 清理
        stopRecording();
    }

    /**
     * 计算帧能量（均方根）
     */
    private float calculateEnergy(short[] buffer, int length) {
        double sum = 0;
        for (int i = 0; i < length; i++) {
            float normalized = buffer[i] / 32768.0f;
            sum += normalized * normalized;
        }
        return (float) Math.sqrt(sum / length);
    }

    /**
     * 将 PCM 数据保存为 WAV 文件
     */
    private String savePcmToWav() {
        if (pcmOffset <= 0) {
            Log.w(TAG, "No PCM data to save");
            return null;
        }

        try {
            // 创建输出文件
            File outputDir = context.getExternalFilesDir(Environment.DIRECTORY_MUSIC);
            if (outputDir == null) {
                outputDir = context.getFilesDir();
            }
            File wavFile = new File(outputDir, "openclaw_voice_" + System.currentTimeMillis() + ".wav");

            FileOutputStream fos = new FileOutputStream(wavFile);

            // WAV header
            writeWavHeader(fos, pcmOffset, SAMPLE_RATE, 1, 16);

            // 写入 PCM 数据
            fos.write(pcmData, 0, pcmOffset);
            fos.close();

            Log.d(TAG, "Saved WAV to: " + wavFile.getAbsolutePath() + ", size: " + wavFile.length());
            return wavFile.getAbsolutePath();

        } catch (IOException e) {
            Log.e(TAG, "Failed to save WAV", e);
            return null;
        }
    }

    /**
     * 写入 WAV 文件头
     */
    private void writeWavHeader(FileOutputStream fos, int pcmLength, int sampleRate, int channels, int bitsPerSample) throws IOException {
        int byteRate = sampleRate * channels * bitsPerSample / 8;
        int totalDataLen = pcmLength;
        int totalLength = totalDataLen + 44;

        // RIFF chunk
        writeString(fos, "RIFF");
        writeInt(fos, totalLength - 8);
        writeString(fos, "WAVE");

        // fmt chunk
        writeString(fos, "fmt ");
        writeInt(fos, 16);  // PCM
        writeShort(fos, (short) 1);  // linear PCM
        writeShort(fos, (short) channels);
        writeInt(fos, sampleRate);
        writeInt(fos, byteRate);
        writeShort(fos, (short) (channels * bitsPerSample / 8));
        writeShort(fos, (short) bitsPerSample);

        // data chunk
        writeString(fos, "data");
        writeInt(fos, totalDataLen);
    }

    private void writeString(FileOutputStream fos, String s) throws IOException {
        fos.write(s.getBytes());
    }

    private void writeInt(FileOutputStream fos, int value) throws IOException {
        fos.write(value & 0xFF);
        fos.write((value >> 8) & 0xFF);
        fos.write((value >> 16) & 0xFF);
        fos.write((value >> 24) & 0xFF);
    }

    private void writeShort(FileOutputStream fos, short value) throws IOException {
        fos.write(value & 0xFF);
        fos.write((value >> 8) & 0xFF);
    }

    public boolean isRecording() {
        return isRecording;
    }

    /**
     * 删除临时文件
     */
    public static void deleteFile(String filePath) {
        if (filePath != null) {
            try {
                new File(filePath).delete();
            } catch (Exception e) {
                // ignore
            }
        }
    }
}