#!/usr/bin/env python3
"""
Termux Voice Client — Silero VAD 高精度自动触发
手机持续听 → AI检测语音 → 检测到停顿 → 自动发送处理

Silero VAD 基于深度学习，比简单能量阈值误识别少很多，适合噪音环境。

依赖:
    pip install onnxruntime numpy

下载模型:
    wget https://github.com/k2-fsa/sherpa-onnx/releases/download/asf-models/silero_vad.onnx -P ~/

用法:
    python3 termux_voice_wake_silero.py --server http://192.168.1.3:8000 --model ~/silero_vad.onnx
"""
import os
import json
import time
import uuid
import struct
import argparse
import subprocess
import urllib.request
import urllib.error
from datetime import datetime

import numpy as np

DEFAULT_SERVER = "http://192.168.1.3:8000"
AUDIO_FILE = "/data/data/com.termux/files/home/voice_input.wav"
SAMPLE_RATE = 16000  # Silero VAD requirement
CHUNK_DURATION = 0.096  # 96ms 推荐块大小
THRESHOLD = 0.5  # 检测阈值，>0.5认为是语音
MIN_SPEECH_DURATION = 0.3  # 最短语音长度(秒)，过滤噪音
MAX_SPEECH_DURATION = 15.0  # 最长语音长度
SILENCE_DURATION_TO_END = 1.0  # 静音多久后结束(秒)

def exec_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {"stdout": r.stdout.strip(), "stderr": r.stderr.strip(), "rc": r.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "timeout", "rc": -1}

def is_termux():
    return "com.termux" in os.getenv("PREFIX", "") or os.path.exists("/data/data/com.termux")

def open_audio_stream():
    """Open continuous raw PCM stream on Termux"""
    if is_termux():
        # Use arecord on Termux
        cmd = [
            "arecord",
            "-r", str(SAMPLE_RATE),
            "-c", "1",
            "-f", "S16_LE",
            "-t", "raw",
        ]
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=1024
        )
        return proc
    else:
        # For testing on PC
        try:
            import sounddevice as sd
            return sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16")
        except ImportError:
            raise RuntimeError("Need sounddevice on PC or arecord on Termux")

def read_chunk(proc, chunk_size):
    """Read a chunk of PCM data"""
    if is_termux():
        # proc is subprocess.Popen
        bytes_needed = chunk_size * 2  # 2 bytes per sample
        data = proc.stdout.read(bytes_needed)
        if len(data) < bytes_needed:
            return None
        return np.frombuffer(data, dtype=np.int16)
    else:
        # proc is sounddevice InputStream
        import sounddevice as sd
        data, overflow = proc.read(chunk_size)
        if overflow:
            print("⚠️  Audio overflow", file=sys.stderr)
        return (data * 32768).astype(np.int16)

class SileroVAD:
    """Silero VAD ONNX inference wrapper"""
    def __init__(self, model_path, threshold=0.5):
        import onnxruntime
        self.threshold = threshold
        self.session = onnxruntime.InferenceSession(
            model_path,
            providers=['CPUExecutionProvider']
        )
        self.sample_rate = SAMPLE_RATE
        self.reset_state()

    def reset_state(self):
        """Reset hidden state for new utterance"""
        self.h = np.zeros((2, 1, 64), dtype=np.float32)
        self.c = np.zeros((2, 1, 64), dtype=np.float32)

    def __call__(self, audio_chunk):
        """
        audio_chunk: np.ndarray[int16] shape (chunk_size,)
        returns: probability (0~1) that this chunk is speech
        """
        # Convert to float32 in [-1, 1]
        audio_float = audio_chunk.astype(np.float32) / 32768.0
        # Reshape for model input
        input_name = self.session.get_inputs()[0].name
        h_name = self.session.get_inputs()[1].name
        c_name = self.session.get_inputs()[2].name
        sr_name = self.session.get_inputs()[3].name

        inputs = {
            input_name: audio_float[None, :],
            h_name: self.h,
            c_name: self.c,
            sr_name: np.array([self.sample_rate], dtype=np.int64)
        }

        output, h_new, c_new = self.session.run(None, inputs)
        self.h = h_new
        self.c = c_new
        return output[0][0]

def tts_speak(text):
    """Android 系统 TTS 朗读"""
    if len(text) > 300:
        text = text[:300] + "..."
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    r = exec_cmd(f'termux-tts speak "{text}"', timeout=30)
    return r["rc"] == 0

def log_conversation(server_url, user_text, assistant_text, latency_ms):
    """记入 memory"""
    try:
        payload = json.dumps({
            "node": "termux_vivo_x9s",
            "user_text": user_text,
            "assistant_text": assistant_text,
            "latency_ms": latency_ms,
        }).encode("utf-8")
        req = urllib.request.Request(
            f"{server_url}/api/conversation/log",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10):
            pass
    except Exception:
        pass

def send_to_pipeline(audio_pcm, server_url, max_tokens=128):
    """
    Send PCM audio (int16) to MLX pipeline
    First save as WAV then send
    """
    # Save as WAV
    with open(AUDIO_FILE, "wb") as f:
        # WAV header
        f.write(b"RIFF")
        f.write((36 + len(audio_pcm) * 2).to_bytes(4, "little"))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write((16).to_bytes(4, "little"))
        f.write((1).to_bytes(2, "little"))  # PCM
        f.write((1).to_bytes(2, "little"))  # 1 channel
        f.write((SAMPLE_RATE).to_bytes(4, "little"))
        f.write((SAMPLE_RATE * 2).to_bytes(4, "little"))
        f.write((2).to_bytes(2, "little"))  # block align
        f.write((16).to_bytes(2, "little"))  # bits per sample
        f.write(b"data")
        f.write((len(audio_pcm) * 2).to_bytes(4, "little"))
        # Write samples
        for sample in audio_pcm:
            f.write(sample.to_bytes(2, "little", signed=True))

    # Send multipart form
    try:
        with open(AUDIO_FILE, "rb") as f:
            audio_data = f.read()

        boundary = "----WebKitFormBoundary" + uuid.uuid4().hex[:16]
        body = b""
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="file"; filename="voice.wav"\r\n'.encode()
        body += b"Content-Type: audio/wav\r\n\r\n".encode()
        body += audio_data
        body += f"\r\n--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="max_tokens"\r\n\r\n'.encode()
        body += f"{max_tokens}\r\n".encode()
        body += f"--{boundary}--\r\n".encode()

        req = urllib.request.Request(
            f"{server_url}/api/mlx-voice/fast",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        return {"success": False, "error": str(e)}

def vad_loop(server_url, model_path, threshold=0.5, min_speech=0.3, max_speech=15.0, silence_end=1.0):
    """Silero VAD 主循环"""
    print("=" * 60)
    print("🦞 元芳 — Silero VAD 高精度自动触发")
    print(f"   服务器: {server_url}")
    print(f"   模型: {model_path}")
    print(f"   阈值: {threshold} | 最短语音: {min_speech}s | 静音结束: {silence_end}s")
    print(f"   AI检测语音，说话后自动识别停顿处理")
    print(f"   Ctrl+C 退出")
    print("=" * 60)

    # Initialize VAD
    print(f"🔄 加载 Silero VAD 模型...")
    vad = SileroVAD(model_path, threshold)

    # Open audio stream
    print(f"🎙️ 打开音频流，开始监听...")
    stream = open_audio_stream()

    chunk_size = int(SAMPLE_RATE * CHUNK_DURATION)  # samples per chunk
    min_speech_chunks = int(min_speech / CHUNK_DURATION)
    silence_chunks_end = int(silence_end / CHUNK_DURATION)
    max_speech_chunks = int(max_speech / CHUNK_DURATION)

    # State
    speech_buffer = []
    in_speech = False
    silence_chunks = 0
    cooldown = 0

    try:
        while True:
            if cooldown > 0:
                cooldown -= 1
                time.sleep(CHUNK_DURATION)
                continue

            # Read chunk
            chunk = read_chunk(stream, chunk_size)
            if chunk is None:
                time.sleep(0.01)
                continue

            # VAD inference
            prob = vad(chunk)
            is_speech = prob > threshold

            # Debug output
            if is_speech:
                print("●", end="", flush=True)
            else:
                if in_speech:
                    print("◦", end="", flush=True)

            if is_speech:
                if not in_speech:
                    # Start of speech
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 👋 检测到语音开始...")
                    vad.reset_state()
                    in_speech = True
                    speech_buffer = []
                speech_buffer.extend(chunk.tolist())
                silence_chunks = 0
            else:
                if in_speech:
                    silence_chunks += 1
                    # Continue buffering while waiting more silence
                    speech_buffer.extend(chunk.tolist())

                    # Check if enough silence to end
                    if silence_chunks >= silence_chunks_end or len(speech_buffer) >= max_speech_chunks:
                        # End of speech
                        total_duration = len(speech_buffer) * CHUNK_DURATION
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🎤 语音结束，时长: {total_duration:.1f}s")

                        # Filter too short
                        if len(speech_buffer) < min_speech_chunks:
                            print(f"  ⚠️  语音太短 ({len(speech_buffer)} chunks)，丢弃")
                            in_speech = False
                            speech_buffer = []
                            vad.reset_state()
                            cooldown = 10
                            continue

                        # Process
                        speech_pcm = np.array(speech_buffer, dtype=np.int16)

                        start_time = time.time()
                        print(f"  🚀 发送处理中...")
                        result = send_to_pipeline(speech_pcm, server_url)
                        latency_ms = int((time.time() - start_time) * 1000)

                        if result.get("success"):
                            resp = result.get("response", "")
                            user_text = result.get("text", "")
                            print(f"  🤖 回复 ({latency_ms}ms): {resp[:60]}...")
                            print(f"  🔊 朗读...")
                            if is_termux():
                                tts_speak(resp)
                            log_conversation(server_url, user_text, resp, latency_ms)
                            cooldown = 20  # ~2s cooling
                        else:
                            print(f"  ❌ 失败: {result.get('error', 'unknown error')}")
                            cooldown = 10

                        # Reset for next utterance
                        in_speech = False
                        speech_buffer = []
                        vad.reset_state()

    except KeyboardInterrupt:
        print("\n\n👋 退出...")
    finally:
        if is_termux() and stream is not None:
            stream.terminate()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🦞 元芳 — Silero VAD 高精度自动触发")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="服务器地址")
    parser.add_argument("--model", default="/data/data/com.termux/files/home/silero_vad.onnx",
                        help="Silero VAD ONNX 模型路径")
    parser.add_argument("--threshold", type=float, default=THRESHOLD,
                        help=f"检测阈值 0~1 (默认 {THRESHOLD}, 越大越严格)")
    parser.add_argument("--min-speech", type=float, default=MIN_SPEECH_DURATION,
                        help=f"最短语音长度秒 (默认 {MIN_SPEECH_DURATION})")
    parser.add_argument("--max-speech", type=float, default=MAX_SPEECH_DURATION,
                        help=f"最长语音长度秒 (默认 {MAX_SPEECH_DURATION})")
    parser.add_argument("--silence-end", type=float, default=SILENCE_DURATION_TO_END,
                        help=f"静音多久后结束秒 (默认 {SILENCE_DURATION_TO_END})")
    args = parser.parse_args()

    vad_loop(
        args.server,
        args.model,
        threshold=args.threshold,
        min_speech=args.min_speech,
        max_speech=args.max_speech,
        silence_end=args.silence_end
    )
