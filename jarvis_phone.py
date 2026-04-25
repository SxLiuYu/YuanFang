#!/data/data/com.termux/files/usr/bin/python3
"""
Jarvis Phone Client — 手机端语音交互
循环: 录音 → 上传 Mac Mini → STT+LLM+TTS → 播放回复

Usage:
    python3 jarvis_phone.py [--server http://192.168.1.3:8000] [--duration 5]
"""
import os
import sys
import json
import time
import uuid
import argparse
import subprocess
import urllib.request
import urllib.error
from datetime import datetime

DEFAULT_SERVER = "http://192.168.1.3:8000"
AUDIO_FILE = "/data/data/com.termux/files/home/jarvis_input.wav"
RESPONSE_FILE = "/data/data/com.termux/files/home/jarvis_response.wav"
RECORD_DURATION = 5
NODE_ID = "jarvis_phone_vivo"

def exec_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {"stdout": r.stdout.strip(), "stderr": r.stderr.strip(), "rc": r.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "timeout", "rc": -1}

def record_audio(duration=RECORD_DURATION, output=AUDIO_FILE):
    """录音"""
    exec_cmd("pkill -f termux-microphone-record || true")
    time.sleep(0.3)
    r = exec_cmd(f"termux-microphone-record -f {output} -l {duration} -d", timeout=5)
    if r["rc"] != 0:
        return False, f"录音启动失败: {r['stderr']}"
    # 等待录制完成
    time.sleep(duration + 1.5)
    exec_cmd("pkill -f termux-microphone-record || true")
    time.sleep(0.5)
    if not os.path.exists(output):
        return False, "录音文件不存在"
    if os.path.getsize(output) < 1000:
        return False, f"录音文件太小 ({os.path.getsize(output)} bytes)"
    return True, output

def tts_speak(text):
    """Android 系统 TTS 朗读"""
    if len(text) > 400:
        text = text[:400] + "..."
    text = text.replace('\\', '\\\\').replace('"', '\\"')
    r = exec_cmd(f'termux-tts-speak "{text}"', timeout=30)
    return r["rc"] == 0

def play_audio(path):
    """播放音频文件"""
    r = exec_cmd(f"termux-media-player play {path}", timeout=30)
    return r["rc"] == 0

def voice_interact(audio_path, server_url, max_tokens=256):
    """
    完整交互: 上传音频 → STT → LLM → TTS → 播放
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

        print(f"[{now()}] 🧠 处理中...")
        with urllib.request.urlopen(req, timeout=90) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        if not result.get("success"):
            return False, "", result.get("error", "处理失败"), 0

        user_text = result.get("text", "")
        assistant_text = result.get("response", "")
        audio_b64 = result.get("audio_data", "")
        latency_ms = int((time.time() - start) * 1000)

        # 播放回复
        if audio_b64:
            import base64
            audio_bytes = base64.b64decode(audio_b64)
            with open(RESPONSE_FILE, "wb") as f:
                f.write(audio_bytes)
            print(f"[{now()}] 🔊 播放音频...")
            play_audio(RESPONSE_FILE)
        else:
            print(f"[{now()}] 🔊 朗读: {assistant_text[:60]}...")
            tts_speak(assistant_text)

        return True, user_text, assistant_text, latency_ms

    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")[:300]
        return False, "", f"HTTP {e.code}: {err}", 0
    except urllib.error.URLError as e:
        return False, "", f"网络错误: {e.reason}", 0
    except Exception as e:
        return False, "", f"错误: {str(e)}", 0

def now():
    return datetime.now().strftime("%H:%M:%S")

def main_loop(server_url, duration):
    print("=" * 50)
    print("🎙️ JARVIS Phone Client — 语音交互")
    print(f"   服务器: {server_url}")
    print(f"   录音时长: {duration}s")
    print(f"   节点: {NODE_ID}")
    print("   按 Ctrl+C 退出")
    print("=" * 50)

    # 首次启动提示
    tts_speak("贾维斯已启动，请说话")

    try:
        while True:
            print(f"\n[{now()}] 🎤 录音 ({duration}s)...")
            ok, msg = record_audio(duration=duration)
            if not ok:
                print(f"  ❌ {msg}")
                time.sleep(1)
                continue

            ok, user_txt, resp, latency = voice_interact(AUDIO_FILE, server_url)
            if not ok:
                print(f"  ❌ {resp}")
                tts_speak("处理失败，请重试")
                continue

            print(f"  👤 你说: {user_txt}")
            print(f"  🤖 回复 ({latency}ms): {resp[:80]}...")
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n退出...")
        tts_speak("再见")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jarvis Phone Client")
    parser.add_argument("--server", default=DEFAULT_SERVER)
    parser.add_argument("--duration", type=int, default=RECORD_DURATION)
    args = parser.parse_args()
    main_loop(args.server, args.duration)
