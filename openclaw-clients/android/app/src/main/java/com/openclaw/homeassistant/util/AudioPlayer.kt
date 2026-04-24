package com.openclaw.homeassistant.util

import android.media.AudioTrack
import android.media.AudioFormat

class AudioPlayer {
    private var audioTrack: AudioTrack? = null

    fun play(audioBytes: ByteArray) {
        stop()
        val sampleRate = 16000
        val bufferSize = AudioTrack.getMinBufferSize(
            sampleRate, AudioFormat.CHANNEL_OUT_MONO, AudioFormat.ENCODING_PCM_16BIT
        )
        audioTrack = AudioTrack(
            android.media.AudioManager.STREAM_MUSIC,
            sampleRate, AudioFormat.CHANNEL_OUT_MONO,
            AudioFormat.ENCODING_PCM_16BIT, maxOf(bufferSize, audioBytes.size),
            AudioTrack.MODE_STREAM
        )
        audioTrack?.play()
        audioTrack?.write(audioBytes, 0, audioBytes.size)
    }

    fun flush() {
        audioTrack?.flush()
    }

    fun stop() {
        audioTrack?.let {
            try {
                it.flush()
                it.stop()
                it.release()
            } catch (e: Exception) {
                // Ignore cleanup errors
            }
        }
        audioTrack = null
    }
    
    fun release() {
        // 完全释放资源，供ViewModel onCleared调用
        stop()
    }
}