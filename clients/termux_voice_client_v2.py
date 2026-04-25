#!/usr/bin/env python3
"""
Termux Voice Client v2 — MLX 快速管线
手机录音 → Mac Mini (STT+LLM) → Android TTS 朗读 → 记入 Memory

用法:
    python3 termux_voice_client_v2.py --server http://192.168.1.3:8000
"""
import os
import json
import time
import uuid
import argparse
import subprocess
import urllib.request
import urllib.error
from datetime import datetime

DEFAULT_SERVER = "http://192.168.1.3:8000"
AUDIO_FILE = "/data/data/com.termux/files/home/voice_input.wav"
RECORD_DURATION = 5

def exec_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {"stdout": r.stdout.strip(), "stderr": r.stderr.strip(), "rc": r.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "timeout", "rc": -1}

def record_audio(duration=RECORD_DURATION, output=AUDIO_FILE):
    exec_cmd("pkill -f termux-microphone-record || true")
    time.sleep(0.3)
    r = exec_cmd(f"termux-microphone-record -f {output} -l {duration} -d", timeout=5)
    if r["rc"] != 0:
        return False, f"录音失败: {r['stderr']}"
    time.sleep(duration + 2)
    exec_cmd("pkill -f termux-microphone-record || true")
    time.sleep(0.5)
    if not os.path.exists(output):
        return False, "文件不存在"
    if os.path.getsize(output) < 1000:
        return False, f"文件太小"
    return True, output

def tts_speak(text):
    """Android 系统 TTS 朗读"""
    if len(text) > 300:
        text = text[:300] + "..."
    # escape double quotes
    text = text.replace('\\', '\\\\').replace('"', '\\"')
    r = exec_cmd(f'termux-tts speak "{text}"', timeout=30)
    return r["rc"] == 0

def log_conversation(server_url, node_id, user_text, assistant_text, latency_ms):
    """记入 memory"""
    try:
        payload = json.dumps({
            "node": node_id,
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
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}

def voice_interact(audio_path, server_url, node_id="termux_vivo_x9s", max_tokens=128):
    """
    完整交互: 录音 → STT → LLM → TTS → memory
    返回: (成功, 用户文字, 助手回复)
    """
    start = time.time()
    if not os.path.exists(audio_path):
        return False, "", "音频文件不存在", 0

    try:
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        boundary = "----WebKitFormBoundary" + uuid.uuid4().hex[:16]
        body = b""
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="file"; filename="voice.wav"\r\n'.encode()
        body += b"Content-Type: audio/wav\r\n\r\n"
        body += audio_data
        body += f"\r\n--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="max_tokens"\r\n\r\n'.encode()
        body += f"{max_tokens}\r\n".encode()
        body += f"--{boundary}--\r\n".encode()

        req = urllib.request.Request(
            f"{server_url}/api/voice/mlx-voice/pipeline",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST"
        )

        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎤 识别...")
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        if not result.get("success"):
            return False, "", result.get("error", "处理失败"), 0

        user_text = result.get("text", "")
        assistant_text = result.get("response", "")
        audio_b64 = result.get("audio_data", "")
        latency_ms = int((time.time() - start) * 1000)

        # 优先用返回的 TTS 音频，其次用 Android TTS
        if audio_b64:
            import base64
            audio_bytes = base64.b64decode(audio_b64)
            wav_path = "/data/data/com.termux/files/home/response.wav"
            with open(wav_path, "wb") as f:
                f.write(audio_bytes)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔊 播放音频...")
            subprocess.run(["termux-media-player", "play", wav_path], timeout=30, capture_output=True)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔊 朗读: {assistant_text[:50]}...")
            tts_ok = tts_speak(assistant_text)

        # 记入 memory
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 💾 记入 memory...")
        log_conversation(server_url, node_id, user_text, assistant_text, latency_ms)

        return True, user_text, assistant_text, latency_ms

    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")[:200]
        return False, "", f"HTTP {e.code}: {err}", 0
    except urllib.error.URLError as e:
        return False, "", f"网络错误: {e.reason}", 0
    except Exception as e:
        return False, "", f"错误: {str(e)}", 0

def interactive_mode(server_url):
    print("=" * 50)
    print("🦞 Termux Voice v2 — 语音交互")
    print(f"   服务器: {server_url}")
    print(f"   Pipeline: Whisper → llama-omni (MiniCPM-o 4.5) → macOS say")
    print(f"   延迟: ~10-20s | TTS: Mac Mini 本地生成")
    print("=" * 50)
    
    try:
        while True:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🎤 录音 ({RECORD_DURATION}s)...")
            ok, msg = record_audio()
            if not ok:
                print(f"  ❌ {msg}")
                time.sleep(1)
                continue

            ok, user_txt, resp, latency = voice_interact(AUDIO_FILE, server_url)
            if not ok:
                print(f"  ❌ {resp}")
                continue

            print(f"  ✅ 回复 ({latency}ms): {resp[:60]}...")
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n退出...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Termux Voice Client v2")
    parser.add_argument("--server", default=DEFAULT_SERVER)
    parser.add_argument("--duration", type=int, default=RECORD_DURATION)
    args = parser.parse_args()
    RECORD_DURATION = args.duration
    interactive_mode(args.server)
