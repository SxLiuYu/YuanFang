#!/usr/bin/env python3
"""
Termux Voice Interactive Client
手机录音 → 上传到 Mac Mini MLX 语音管线 → 接收语音回复 → 手机播放

管线:
  手机麦克风 → (上传) → Mac Mini Flask /api/mlx-voice/pipeline
               → mlx_whisper (STT) → Gemma 4B (LLM) → Kokoro TTS
               → (返回音频) → 手机 termux-media-player 播放
"""
import os
import sys
import json
import time
import uuid
import base64
import argparse
import subprocess
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime

# ============== 配置 ==============
DEFAULT_SERVER = "http://192.168.1.3:8000"
AUDIO_FILE = "/data/data/com.termux/files/home/voice_input.wav"
TTS_FILE = "/data/data/com.termux/files/home/tts_output.wav"
RECORD_DURATION = 5  # 录音秒数
VOICE = "af_heart"  # Kokoro 声音

# ============== 工具函数 ==============

def exec_cmd(cmd, timeout=30):
    """执行本地命令"""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {"stdout": r.stdout.strip(), "stderr": r.stderr.strip(), "rc": r.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "timeout", "rc": -1}


def record_audio(duration=RECORD_DURATION, output=AUDIO_FILE):
    """
    录音 - 使用 termux-microphone-record
    返回: (成功标志, 文件路径或错误信息)
    """
    # 停止之前的录音
    exec_cmd("pkill -f termux-microphone-record || true")
    time.sleep(0.3)

    # 开始录音（后台）
    r = exec_cmd(f"termux-microphone-record -f {output} -l {duration} -d", timeout=5)
    if r["rc"] != 0:
        return False, f"录音启动失败: {r['stderr']}"

    # 等待录音完成
    wait_time = duration + 2
    time.sleep(wait_time)

    # 停止录音
    exec_cmd("pkill -f termux-microphone-record || true")
    time.sleep(0.5)

    # 检查文件
    if not os.path.exists(output):
        return False, "录音文件不存在"

    size = os.path.getsize(output)
    if size < 1000:
        return False, f"录音文件太小: {size} bytes"

    return True, output


def play_audio(filepath):
    """播放音频 - termux-media-player"""
    r = exec_cmd(f"termux-media-player play {filepath}", timeout=10)
    return r["rc"] == 0


def stop_audio():
    """停止播放"""
    exec_cmd("termux-media-player stop", timeout=5)


# ============== API 调用 ==============

def upload_and_process(audio_path, server_url, voice=VOICE):
    """
    上传音频到 MLX Voice 管线，获取语音回复
    返回: (成功标志, TTS音频文件路径 或 错误信息)
    """
    if not os.path.exists(audio_path):
        return False, f"音频文件不存在: {audio_path}"

    try:
        # 读取音频文件
        with open(audio_path, "rb") as f:
            audio_data = f.read()

        # 构建 multipart form-data
        boundary = "----WebKitFormBoundary" + uuid.uuid4().hex[:16]
        
        body = b""
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(audio_path)}"\r\n'.encode()
        body += b"Content-Type: audio/wav\r\n\r\n"
        body += audio_data
        body += f"\r\n--{boundary}\r\n".encode()
        
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="voice"\r\n\r\n'.encode()
        body += f"{voice}\r\n".encode()
        body += f"--{boundary}--\r\n".encode()

        url = f"{server_url}/api/mlx-voice/pipeline"
        headers = {
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 上传音频到 MLX 管线...")
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode("utf-8"))

        if not result.get("success"):
            return False, f"管线失败: {result.get('error', 'unknown')}"

        # 保存返回的音频
        if result.get("audio_data"):
            audio_b64 = result["audio_data"]
            audio_bytes = base64.b64decode(audio_b64)
            with open(TTS_FILE, "wb") as f:
                f.write(audio_bytes)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 收到回复音频: {len(audio_bytes)} bytes")
            return True, TTS_FILE
        
        return False, "没有收到音频数据"

    except urllib.error.HTTPError as e:
        return False, f"HTTP 错误: {e.code} {e.reason}"
    except urllib.error.URLError as e:
        return False, f"网络错误: {e.reason}"
    except Exception as e:
        return False, f"错误: {str(e)}"


def simple_chat(message, server_url):
    """
    纯文字对话（不需要录音）
    """
    try:
        payload = json.dumps({
            "message": message,
            "model": "gemma-4-E4B-it-4bit",
            "max_tokens": 256,
            "temperature": 0.7,
        }).encode("utf-8")

        headers = {"Content-Type": "application/json"}
        req = urllib.request.Request(
            f"{server_url}/api/mlx-voice/chat",
            data=payload,
            headers=headers,
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        
        if result.get("success"):
            return True, result["response"]
        return False, result.get("error", "unknown")
    except Exception as e:
        return False, str(e)


# ============== 交互模式 ==============

def interactive_mode(server_url):
    """交互式语音对话"""
    print("=" * 50)
    print("Termux Voice Interactive - 交互式语音对话")
    print(f"服务器: {server_url}")
    print("按 Ctrl+C 退出")
    print("=" * 50)
    
    print("\n📍 语音模式已启动")
    print(f"   每次说话录音 {RECORD_DURATION} 秒")
    print("-" * 50)

    try:
        while True:
            print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 🎤 开始录音 ({RECORD_DURATION}s)...")
            
            ok, msg = record_audio()
            if not ok:
                print(f"❌ 录音失败: {msg}")
                time.sleep(1)
                continue

            print(f"✅ 录音完成: {msg}")
            
            # 上传到 MLX 管线
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🤖 等待 MLX 处理...")
            ok, msg = upload_and_process(AUDIO_FILE, server_url)
            
            if not ok:
                print(f"❌ 处理失败: {msg}")
                continue

            # 播放 TTS 音频
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔊 播放回复...")
            played = play_audio(msg)
            if played:
                print(f"✅ 播放完成")
            else:
                print(f"❌ 播放失败")

    except KeyboardInterrupt:
        print("\n\n退出...")
        stop_audio()


def text_mode(server_url, message):
    """文字对话模式"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 💬 发送: {message}")
    ok, resp = simple_chat(message, server_url)
    if ok:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🤖 回复: {resp}")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 错误: {resp}")


# ============== 主入口 ==============

def main():
    parser = argparse.ArgumentParser(description="Termux Voice Interactive Client")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="Flask 服务器地址")
    parser.add_argument("--duration", type=int, default=RECORD_DURATION, help="录音时长(秒)")
    parser.add_argument("--voice", default=VOICE, help="TTS 声音 (默认: af_heart)")
    parser.add_argument("--text", type=str, help="文字模式: 直接发送文字并获取回复")
    args = parser.parse_args()

    global RECORD_DURATION, VOICE
    RECORD_DURATION = args.duration
    VOICE = args.voice

    if args.text:
        text_mode(args.server, args.text)
    else:
        interactive_mode(args.server)


if __name__ == "__main__":
    main()
