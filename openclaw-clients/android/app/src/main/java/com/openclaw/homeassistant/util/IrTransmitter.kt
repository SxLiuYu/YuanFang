package com.openclaw.homeassistant.util

import android.content.Context
import android.hardware.ConsumerIrManager
import com.openclaw.homeassistant.domain.model.InfraredCommand

class IrTransmitter(context: Context) {
    private val irManager: ConsumerIrManager? = context.getSystemService(Context.CONSUMER_IR_SERVICE) as? ConsumerIrManager

    fun transmit(command: InfraredCommand) {
        if (irManager == null || !irManager.hasIrEmitter()) return
        val pattern = hexPatternToIntArray(command.pattern)
        if (pattern.isNotEmpty()) {
            irManager.transmit(command.frequency, pattern)
        }
    }

    fun hasIrEmitter(): Boolean = irManager?.hasIrEmitter() == true

    private fun hexPatternToIntArray(hexString: String): IntArray {
        if (hexString.isEmpty()) return IntArray(0)
        val cleaned = hexString.replace(" ", "").replace("0x", "").lowercase()
        if (cleaned.isEmpty() || cleaned.length % 4 != 0) return IntArray(0)
        // 每个 pattern 间隔是 16-bit (两个字节)，所以每次读取 4 个十六进制字符
        val result = IntArray(cleaned.length / 4)
        for (i in result.indices) {
            val wordStr = cleaned.substring(i * 4, i * 4 + 4)
            try {
                result[i] = wordStr.toInt(16)
            } catch (e: NumberFormatException) {
                return IntArray(0)
            }
        }
        return result
    }
}