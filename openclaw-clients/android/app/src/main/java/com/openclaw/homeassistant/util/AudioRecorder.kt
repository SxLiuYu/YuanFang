package com.openclaw.homeassistant.util

import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder
import java.util.concurrent.CountDownLatch
import java.util.concurrent.atomic.AtomicBoolean

class AudioRecorder {
    private var audioRecord: AudioRecord? = null
    private val isRecording = AtomicBoolean(false)
    private var recordedBytes: ByteArray = ByteArray(0)
    private val bufferSize = AudioRecord.getMinBufferSize(
        16000, AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT
    )

    fun startRecording() {
        if (isRecording.get()) return
        // 确保之前的录音已经停止
        stopRecording()
        
        recordedBytes = ByteArray(0)
        audioRecord = AudioRecord(
            MediaRecorder.AudioSource.MIC, 16000,
            AudioFormat.CHANNEL_IN_MONO, AudioFormat.ENCODING_PCM_16BIT,
            bufferSize * 2
        )
        
        if (audioRecord?.state != AudioRecord.STATE_INITIALIZED) {
            audioRecord = null
            return
        }
        
        audioRecord?.startRecording()
        isRecording.set(true)

        Thread {
            val buffer = ByteArray(bufferSize)
            val outputStream = java.io.ByteArrayOutputStream()
            while (isRecording.get()) {
                val read = audioRecord?.read(buffer, 0, buffer.size) ?: 0
                if (read > 0) outputStream.write(buffer, 0, read)
            }
            recordedBytes = outputStream.toByteArray()
            outputStream.close()
        }.start()
    }

    fun stopRecording(): ByteArray? {
        if (!isRecording.get()) return null
        isRecording.set(false)
        val result = recordedBytes.takeIf { it.isNotEmpty() }
        try {
            audioRecord?.stop()
            audioRecord?.release()
        } catch (e: Exception) {
            // Ignore
        } finally {
            audioRecord = null
        }
        return result
    }
    
    fun cancel() {
        isRecording.set(false)
        try {
            audioRecord?.stop()
            audioRecord?.release()
        } catch (e: Exception) {
            // Ignore
        } finally {
            audioRecord = null
            recordedBytes = ByteArray(0)
        }
    }
}