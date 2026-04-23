#!/usr/bin/env python3
"""
Termux Voice Client — 停顿时自动触发（VAD）
手机持续听 → 检测到说话 → 检测到停顿 → 自动发送处理

比唤醒词更自然：不用每次喊名字，说完话停一下就行。
"""
import os
import json
import time
import uuid
import struct
import subprocess
import urllib.request
import urllib.error
import argparse
from datetime import datetime

DEFAULT_SERVER = "http://192.168.1.3:8000"
AUDIO_FILE = "/data/data/com.termux/files/home/voice_input.wav"
SILENCE_THRESHOLD = 1500   # 静音能量阈值
SPEECH_THRESHOLD = 5000    # 语音能量阈值（提高减少误触发）
CHUNK_DURATION = 0.1       # 每块录音 100ms
CHUNKS_BEFORE_SEND = 40    # 约4秒音频后发送
CHUNKS_AFTER_SPEECH = 15   # 检测到语音后，再等1.5秒确保说完
SILENCE_CHUNKS_TO_TRIGGER = 25  # 连续25个静音块（约2.5秒）= 说完了
MIN_SPEECH_CHUNKS = 5      # 最少需要多少个语音块才触发（过滤噪音）

def exec_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {"stdout": r.stdout.strip(), "stderr": r.stderr.strip(), "rc": r.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "timeout", "rc": -1}

def record_chunk(output, duration=CHUNK_DURATION):
    """录一小块音频（100ms）"""
    exec_cmd("pkill -f termux-microphone-record || true")
    time.sleep(0.02)
    r = exec_cmd(f"termux-microphone-record -f {output} -l {int(duration * 1000)} -d", timeout=3)
    time.sleep(duration + 0.1)
    exec_cmd("pkill -f termux-microphone-record || true")
    time.sleep(0.02)

def get_audio_energy(audio_file):
    """计算音频能量"""
    try:
        with open(audio_file, "rb") as f:
            data = f.read()
        if len(data) <= 44:
            return 0
        pcm = data[44:]
        samples = struct.unpack_from(f"<{len(pcm)//2}h", pcm)
        return max(abs(s) for s in samples) if samples else 0
    except:
        return 0

def tts_speak(text):
    if len(text) > 300:
        text = text[:300] + "..."
    text = text.replace('\\', '\\\\').replace('"', '\\"')
    r = exec_cmd(f'termux-tts speak "{text}"', timeout=30)
    return r["rc"] == 0

def log_conversation(server_url, user_text, assistant_text, latency_ms):
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
    except:
        pass

def send_to_pipeline(audio_path, server_url, max_tokens=128):
    """发送音频到 MLX pipeline"""
    try:
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        boundary = "----WebKitFormBoundary" + uuid.uuid4().hex[:16]
        body = b""
        body += f"--{boundary}\r\n".encode()
        body += b'Content-Disposition: form-data; name="file"; filename="voice.wav"\r\n'
        body += b"Content-Type: audio/wav\r\n\r\n"
        body += audio_data
        body += f"\r\n--{boundary}\r\n".encode()
        body += b'Content-Disposition: form-data; name="max_tokens"\r\n\r\n'
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

def vad_loop(server_url):
    """VAD 主循环 — 检测语音+停顿自动触发"""
    print("=" * 50)
    print("🦞 元芳  — 停顿时自动触发")
    print(f"   服务器: {server_url}")
    print("   说话后停顿约2秒自动处理")
    print("   Ctrl+C 退出")
    print("=" * 50)

    tmp_chunk = "/data/data/com.termux/files/home/vad_chunk.wav"
    silence_count = 0
    speech_count = 0
    chunks_stored = []
    was_speaking = False
    cooldown = 0  # 处理完后的冷却期

    try:
        while True:
            if cooldown > 0:
                cooldown -= 1
                time.sleep(0.1)
                continue

            # 录一小块
            record_chunk(tmp_chunk)
            energy = get_audio_energy(tmp_chunk)

            is_speech = energy > SPEECH_THRESHOLD
            is_silence = energy < SILENCE_THRESHOLD

            if is_speech:
                speech_count += 1
                silence_count = 0
                # 收集语音块
                with open(tmp_chunk, "rb") as f:
                    chunks_stored.append(f.read())
                # 限制最大长度
                if len(chunks_stored) > CHUNKS_BEFORE_SEND:
                    chunks_stored.pop(0)
                was_speaking = True

            elif is_silence:
                silence_count += 1
                if was_speaking and speech_count >= MIN_SPEECH_CHUNKS:
                    # 说话后出现静音 = 可能的停顿
                    with open(tmp_chunk, "rb") as f:
                        chunks_stored.append(f.read())
                    if silence_count >= SILENCE_CHUNKS_TO_TRIGGER:
                        # 停顿够长，触发处理
                        speech_count = 0
                        was_speaking = False
                        if chunks_stored:
                            # 保存完整录音
                            full_audio = b"".join(chunks_stored)
                            # WAV header from first chunk
                            if len(full_audio) > 44:
                                with open(AUDIO_FILE, "wb") as f:
                                    f.write(full_audio)
                                chunks_stored = []

                                print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🎤 检测到说话！处理中...")
                                
                                start = time.time()
                                result = send_to_pipeline(AUDIO_FILE, server_url)
                                latency_ms = int((time.time() - start) * 1000)

                                if result.get("success"):
                                    resp = result.get("response", "")
                                    print(f"  🤖 {resp[:60]}...")
                                    print(f"  🔊 朗读...")
                                    tts_speak(resp)
                                    log_conversation(server_url, result.get("text", ""), resp, latency_ms)
                                    cooldown = 20  # 2秒冷却
                                else:
                                    print(f"  ❌ {result.get('error', '处理失败')}")
                                    cooldown = 10
                elif was_speaking and silence_count >= 5:
                    # 还没到触发点，继续等
                    pass
                else:
                    # 真正在静音，重置
                    if not was_speaking:
                        chunks_stored = []
                        silence_count = 0
                        speech_count = 0
            else:
                # 中间能量，视为语音延续
                if was_speaking:
                    with open(tmp_chunk, "rb") as f:
                        chunks_stored.append(f.read())
                    silence_count = 0

    except KeyboardInterrupt:
        print("\n\n退出...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="🦞 元芳 Voice Client — VAD自动触发")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="服务器地址")
    parser.add_argument("--speech-threshold", type=int, default=SPEECH_THRESHOLD, 
                        help=f"语音能量阈值 (默认: {SPEECH_THRESHOLD}, 越大越难触发，减少误识别)")
    parser.add_argument("--silence-threshold", type=int, default=SILENCE_THRESHOLD,
                        help=f"静音能量阈值 (默认: {SILENCE_THRESHOLD})")
    parser.add_argument("--silence-trigger", type=int, default=SILENCE_CHUNKS_TO_TRIGGER,
                        help=f"静音多少块触发 (每块0.1s，默认: {SILENCE_CHUNKS_TO_TRIGGER})")
    parser.add_argument("--min-speech", type=int, default=MIN_SPEECH_CHUNKS,
                        help=f"最少语音块数触发 (默认: {MIN_SPEECH_CHUNKS})")
    args = parser.parse_args()
    
    # 覆盖参数
    SPEECH_THRESHOLD = args.speech_threshold
    SILENCE_THRESHOLD = args.silence_threshold
    SILENCE_CHUNKS_TO_TRIGGER = args.silence_trigger
    MIN_SPEECH_CHUNKS = args.min_speech
    
    vad_loop(args.server)
