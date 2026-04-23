package com.openclaw.homeassistant;

import android.content.Context;
import android.media.AudioAttributes;
import android.media.MediaPlayer;
import android.net.Uri;
import android.util.Log;

import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;

/**
 * 音频播放器
 * 用于播放服务端返回的 TTS 音频
 */
public class AudioPlayer {
    private static final String TAG = "AudioPlayer";

    private MediaPlayer mediaPlayer;
    private Context context;
    private boolean isPlaying = false;

    public interface PlaybackCallback {
        void onPlaybackComplete();
        void onPlaybackError(String error);
    }

    public AudioPlayer(Context context) {
        this.context = context;
    }

    /**
     * 播放 WAV 音频文件
     */
    public void playWav(byte[] audioData, PlaybackCallback callback) {
        stop();

        try {
            // 保存到临时文件
            File tempDir = context.getExternalFilesDir(null);
            if (tempDir == null) {
                tempDir = context.getCacheDir();
            }
            File tempFile = new File(tempDir, "tts_response_" + System.currentTimeMillis() + ".wav");

            FileOutputStream fos = new FileOutputStream(tempFile);
            fos.write(audioData);
            fos.close();

            mediaPlayer = new MediaPlayer();
            mediaPlayer.setAudioAttributes(
                    new AudioAttributes.Builder()
                            .setContentType(AudioAttributes.CONTENT_TYPE_MUSIC)
                            .setUsage(AudioAttributes.USAGE_MEDIA)
                            .build()
            );

            mediaPlayer.setDataSource(context, Uri.fromFile(tempFile));
            mediaPlayer.prepareAsync();

            mediaPlayer.setOnPreparedListener(mp -> {
                Log.d(TAG, "Audio prepared, starting playback");
                mp.start();
                isPlaying = true;
            });

            mediaPlayer.setOnCompletionListener(mp -> {
                Log.d(TAG, "Playback completed");
                isPlaying = false;
                tempFile.delete();
                if (callback != null) {
                    callback.onPlaybackComplete();
                }
            });

            mediaPlayer.setOnErrorListener((mp, what, extra) -> {
                Log.e(TAG, "Playback error: " + what + ", " + extra);
                isPlaying = false;
                tempFile.delete();
                if (callback != null) {
                    callback.onPlaybackError("播放错误: " + what);
                }
                return true;
            });

        } catch (IOException e) {
            Log.e(TAG, "Failed to play audio", e);
            if (callback != null) {
                callback.onPlaybackError("播放失败: " + e.getMessage());
            }
        }
    }

    /**
     * 停止播放
     */
    public void stop() {
        if (mediaPlayer != null) {
            try {
                if (isPlaying) {
                    mediaPlayer.stop();
                }
                mediaPlayer.release();
            } catch (Exception e) {
                Log.e(TAG, "Error stopping playback", e);
            } finally {
                mediaPlayer = null;
                isPlaying = false;
            }
        }
    }

    /**
     * 打断当前播放（用于说话打断功能）
     */
    public void interrupt() {
        stop();
    }

    public boolean isPlaying() {
        return isPlaying && mediaPlayer != null;
    }
}