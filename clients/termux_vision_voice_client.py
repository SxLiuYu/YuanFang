#!/usr/bin/env python3
"""
Termux Vision + Voice Client — 贾维斯视频对话智能助手
手机：录音 + 拍照 → Mac Mini (Whisper + Qwen3-VL + Kokoro TTS) → Android 播放回复
支持红外发射控制家电（需要手机自带红外 + Termux:API）

用法:
    python3 termux_vision_voice_client.py --server http://192.168.1.3:8000
    python3 termux_vision_voice_client.py --server http://192.168.1.3:8000 --no-vision  # 仅语音模式
"""
import os
import json
import time
import uuid
import argparse
import subprocess
import urllib.request
import urllib.error
import base64
from datetime import datetime

DEFAULT_SERVER = "http://192.168.1.3:8000"
AUDIO_FILE = "/data/data/com.termux/files/home/voice_input.wav"
IMAGE_FILE = "/data/data/com.termux/files/home/camera_photo.jpg"
RECORD_DURATION = 5

def exec_cmd(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {"stdout": r.stdout.strip(), "stderr": r.stderr.strip(), "rc": r.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "timeout", "rc": -1}

def check_infrared_available():
    """检查红外是否可用"""
    r = exec_cmd("which termux-infrared-frequencies")
    return r["rc"] == 0

def take_photo(output=IMAGE_FILE):
    """使用Termux摄像头拍照"""
    if output != os.path.abspath(output):
        output = os.path.abspath(output)
    r = exec_cmd(f"termux-camera-photo {output}", timeout=10)
    if r["rc"] != 0:
        return False, f"拍照失败: {r['stderr']}"
    time.sleep(1)
    if not os.path.exists(output):
        return False, "照片文件不存在"
    if os.path.getsize(output) < 1000:
        return False, f"照片太小 ({os.path.getsize(output)} bytes)"
    return True, output

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
        return False, "音频文件不存在"
    if os.path.getsize(output) < 1000:
        return False, f"文件太小 ({os.path.getsize(output)} bytes)"
    return True, output

def infrared_transmit(frequency, pattern):
    """发射红外信号"""
    cmd = f"termux-infrared-transmit -f {frequency} {pattern}"
    r = exec_cmd(cmd, timeout=10)
    return r["rc"] == 0, r["stderr"]

def list_infrared_frequencies():
    """列出支持的红外频率"""
    r = exec_cmd("termux-infrared-frequencies")
    return r["stdout"]

def tts_speak(text):
    """Android 系统 TTS 朗读"""
    if len(text) > 300:
        text = text[:300] + "..."
    text = text.replace("\\", "\\\\").replace("\"", "\\\"")
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

def vision_voice_interact(audio_path, image_path, server_url, node_id="termux_vision", max_tokens=256, enable_vision=True):
    """
    完整视觉语音交互: 录音+照片 → STT+VL → TTS → memory
    返回: (成功, 用户文字, 助手回复)
    """
    start = time.time()
    if not os.path.exists(audio_path):
        return False, "", "音频文件不存在", 0

    try:
        boundary = "----WebKitFormBoundary" + uuid.uuid4().hex[:16]
        body = b""

        # 上传音频
        with open(audio_path, "rb") as f:
            audio_data = f.read()
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="audio"; filename="voice.wav"\r\n'.encode()
        body += b"Content-Type: audio/wav\r\n\r\n"
        body += audio_data
        body += f"\r\n--{boundary}\r\n".encode()

        # 上传图片（如果启用视觉）
        image_b64 = ""
        if enable_vision and os.path.exists(image_path):
            with open(image_path, "rb") as f:
                image_bytes = f.read()
                image_b64 = base64.b64encode(image_bytes).decode("utf-8")
            body += f'Content-Disposition: form-data; name="image"\r\n\r\n'.encode()
            body += f"{image_b64}\r\n".encode()
            body += f"--{boundary}\r\n".encode()

        # max_tokens 参数
        body += f'Content-Disposition: form-data; name="max_tokens"\r\n\r\n'.encode()
        body += f"{max_tokens}\r\n".encode()
        body += f"--{boundary}--\r\n".encode()

        endpoint = f"{server_url}/api/vision-voice/pipeline"
        req = urllib.request.Request(
            endpoint,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST"
        )

        vision_tag = "视觉+语音" if enable_vision else "纯语音"
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎤 处理{vision_tag}...")
        with urllib.request.urlopen(req, timeout=180) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        if not result.get("success"):
            return False, "", result.get("error", "处理失败"), 0

        user_text = result.get("text", "")
        assistant_text = result.get("response", "")
        audio_b64 = result.get("audio_data", "")
        thinking = result.get("thinking", "")
        latency_ms = int((time.time() - start) * 1000)

        # 如果有红外控制指令，直接执行
        infrared = result.get("infrared", None)
        if infrared and check_infrared_available():
            freq = infrared.get("frequency", 38000)
            pattern = infrared.get("pattern", "")
            if pattern:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📶 发送红外信号...")
                ok, err = infrared_transmit(freq, pattern)
                if ok:
                    assistant_text += "\n[红外已发送]"
                else:
                    assistant_text += f"\n[红外发送失败: {err}]"

        # 播放语音回复
        if audio_b64:
            audio_bytes = base64.b64decode(audio_b64)
            wav_path = "/data/data/com.termux/files/home/response.wav"
            with open(wav_path, "wb") as f:
                f.write(audio_bytes)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔊 播放音频...")
            subprocess.run(["termux-media-player", "play", wav_path], timeout=60, capture_output=True)
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔊 朗读: {assistant_text[:80]}...")
            tts_speak(assistant_text)

        # 记入 conversation memory
        log_conversation(server_url, node_id, user_text, assistant_text, latency_ms)

        if thinking:
            print(f"[思考] {thinking[:100]}...")

        return True, user_text, assistant_text, latency_ms

    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")[:200]
        return False, "", f"HTTP {e.code}: {err}", 0
    except urllib.error.URLError as e:
        return False, "", f"网络错误: {e.reason}", 0
    except Exception as e:
        return False, "", f"错误: {str(e)}", 0

def interactive_mode(server_url, enable_vision=True):
    print("=" * 60)
    print("🤖 贾维斯 — Termux 视觉语音助手")
    print(f"   服务器: {server_url}")
    print(f"   视觉模式: {'开启' if enable_vision else '关闭'}")
    print(f"   Pipeline: 手机拍照+录音 → Mac Whisper → Qwen3-VL → Kokoro TTS")
    ir_available = check_infrared_available()
    print(f"   红外控制: {'✅ 可用' if ir_available else '❌ 不可用（需要手机带红外+Termux:API）'}")
    if ir_available:
        freqs = list_infrared_frequencies()
        print(f"   支持频率: {freqs}")
    print("=" * 60)
    print("\n操作说明:")
    print(" - 每次录音自动拍照（如果开启视觉）")
    print(" - 按 Ctrl+C 退出")
    print(" - 说：'贾维斯，这是什么' → 识别物体")
    print(" - 说：'贾维斯，打开电视' → 识别+红外控制")
    print()

    try:
        while True:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🎤 录音 ({RECORD_DURATION}s)...")
            if enable_vision:
                print("  📸 拍照中...")
                ok, img = take_photo()
                if not ok:
                    print(f"  ❌ {img}")
                    time.sleep(1)
                    continue
                print(f"  ✅ 拍照完成: {os.path.getsize(img)} bytes")

            ok, msg = record_audio()
            if not ok:
                print(f"  ❌ {msg}")
                time.sleep(1)
                continue

            ok, user_txt, resp, latency = vision_voice_interact(
                AUDIO_FILE, IMAGE_FILE, server_url, enable_vision=enable_vision
            )
            if not ok:
                print(f"  ❌ {resp}")
                continue

            print(f"  ✅ 完成 ({latency}ms)")
            print(f"  你说: {user_txt}")
            print(f"  贾维斯: {resp[:150]}{'...' if len(resp) > 150 else ''}")
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n\n👋 退出...")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Termux Vision + Voice Client")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="服务器地址")
    parser.add_argument("--duration", type=int, default=RECORD_DURATION, help="录音时长")
    parser.add_argument("--no-vision", action="store_true", help="禁用视觉模式，仅语音")
    args = parser.parse_args()
    RECORD_DURATION = args.duration
    interactive_mode(args.server, enable_vision=not args.no_vision)
