#!/usr/bin/env python3
"""
Termux 语音助手节点客户�?v2
通过 HTTP API 与主服务通信，语�?I/O 通过 Termux 工具实现

功能:
    - 轮询主服务命令队�?(poll)
    - 录音: termux-microphone-record
    - 播放: termux-media-player
    - TTS: 调用 CosyVoice API 生成音频
    - STT: 调用 Whisper API 识别音频

用法:
    python3 termux_voice_client.py --server http://192.168.1.11:8000 --node-id termux_voice_01
"""

import os
import sys
import json
import time
import wave
import uuid
import argparse
import subprocess
import urllib.request
import urllib.error
from datetime import datetime

# ============== 配置 ==============
DEFAULT_SERVER = "http://192.168.1.11:8000"
DEFAULT_NODE_ID = "termux_voice_01"
POLL_INTERVAL = 5  # �?
RECORD_DURATION = 5  # 录音时长（秒�?
AUDIO_FILE = "/data/data/com.termux/files/home/voice_input.wav"
TTS_FILE = "/data/data/com.termux/files/home/tts_output.wav"
API_BASE = "https://www.finna.com.cn/v1"

# ============== Termux 工具封装 ==============

def exec_cmd(cmd, timeout=30):
    """执行本地命令"""
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {"stdout": r.stdout, "stderr": r.stderr, "rc": r.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "timeout", "rc": -1}


def record_audio(duration=RECORD_DURATION, output=AUDIO_FILE):
    """录音"""
    # 停止之前的录音（如果还在跑）
    exec_cmd("pkill -f termux-microphone-record || true")
    time.sleep(0.5)

    # 开始录�?
    r = exec_cmd(f"termux-microphone-record -f {output} -l {duration}")
    if r["rc"] != 0:
        return False, f"录音失败: {r['stderr']}"

    # 等待录音完成
    time.sleep(duration + 1)

    # 检查文�?
    if not os.path.exists(output):
        return False, "录音文件不存�?

    size = os.path.getsize(output)
    if size < 1000:
        return False, f"录音文件太小: {size} bytes"

    return True, output


def play_audio(filepath):
    """播放音频"""
    r = exec_cmd(f"termux-media-player play {filepath}")
    return r["rc"] == 0


def stop_audio():
    """停止播放"""
    exec_cmd("termux-media-player stop")


# ============== API 调用 ==============

def call_cosyvoice_tts(text, output_file=TTS_FILE, voice="zh-CN-XiaoxiaoNeural"):
    """调用 CosyVoice TTS API 生成音频"""
    api_key = "app-BqyKsTO4Om3JGoPCTkJX080J"  # CosyVoice API key

    url = f"{API_BASE}/audio/speech"

    # 构�?OpenAI TTS compatible request
    payload = json.dumps({
        "model": "FunAudioLLM/CosyVoice2-0.5B",
        "input": text,
        "voice": voice,
        "response_format": "wav",
        "speed": 1.0
    }).encode("utf-8")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=30) as response:
            audio_data = response.read()
            with open(output_file, "wb") as f:
                f.write(audio_data)
            return True, output_file
    except Exception as e:
        return False, str(e)


def upload_and_transcribe(audio_file, server_url):
    """上传音频到主服务进行 Whisper 识别"""
    try:
        import urllib.parse

        with open(audio_file, "rb") as f:
            audio_data = f.read()

        # 构�?multipart form
        boundary = "----WebKitFormBoundary" + uuid.uuid4().hex[:16]
        body = b""
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="file"; filename="{os.path.basename(audio_file)}"\r\n'.encode()
        body += b"Content-Type: audio/wav\r\n\r\n"
        body += audio_data
        body += f"\r\n--{boundary}--\r\n".encode()

        url = f"{server_url}/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer app-BqyKsTO4Om3JGoPCTkJX080J",
            "Content-Type": f"multipart/form-data; boundary={boundary}"
        }

        req = urllib.request.Request(url, data=body, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
            return True, result.get("text", "")
    except Exception as e:
        return False, str(e)


# ============== 命令队列 ==============

def poll_commands(server_url, node_id):
    """轮询待执行命�?""
    try:
        url = f"{server_url}/api/commands/pending/{node_id}"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"轮询失败: {e}")
        return []


def report_result(server_url, node_id, command_id, success, result):
    """上报命令结果"""
    try:
        url = f"{server_url}/api/commands/complete"
        payload = json.dumps({
            "node_id": node_id,
            "command_id": command_id,
            "success": success,
            "result": result
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"上报失败: {e}")
        return None


# ============== 命令执行 ==============

def execute_command(cmd, server_url, node_id):
    """执行单个命令"""
    action = cmd.get("action", "")
    params = cmd.get("params", {})
    command_id = cmd.get("id", "")

    print(f"\n执行命令 [{command_id}]: {action}")

    if action == "voice_listen":
        # 语音监听：录�?-> 上传识别 -> 返回文字
        duration = params.get("duration", RECORD_DURATION)
        print(f"  录音 {duration} �?..")
        ok, msg = record_audio(duration=duration)
        if not ok:
            report_result(server_url, node_id, command_id, False, {"error": msg})
            return

        print(f"  上传并识�?..")
        ok, text = upload_and_transcribe(AUDIO_FILE, server_url)
        if ok:
            print(f"  识别结果: {text}")
            report_result(server_url, node_id, command_id, True, {"text": text})
        else:
            print(f"  识别失败: {text}")
            report_result(server_url, node_id, command_id, False, {"error": text})

    elif action == "tts_speak":
        # TTS 播报：生成音�?-> 播放
        text = params.get("text", "")
        print(f"  TTS: {text}")
        ok, msg = call_cosyvoice_tts(text)
        if ok:
            print(f"  播放...")
            play_audio(msg)
            report_result(server_url, node_id, command_id, True, {"played": True})
        else:
            print(f"  TTS 失败: {msg}")
            report_result(server_url, node_id, command_id, False, {"error": msg})

    elif action == "play_audio":
        # 播放指定音频文件
        filepath = params.get("filepath", TTS_FILE)
        print(f"  播放: {filepath}")
        ok = play_audio(filepath)
        report_result(server_url, node_id, command_id, ok, {"played": ok})

    elif action == "stop_audio":
        stop_audio()
        report_result(server_url, node_id, command_id, True, {"stopped": True})

    elif action == "status":
        # 状态查�?
        r = exec_cmd("termux-battery-status 2>/dev/null || echo '{}'")
        battery = r.get("stdout", "").strip()
        info_r = exec_cmd("termux-media-player info 2>/dev/null || echo 'not playing'")
        report_result(server_url, node_id, command_id, True, {
            "node": node_id,
            "battery": battery,
            "player": info_r.get("stdout", "").strip(),
            "time": datetime.now().isoformat()
        })

    else:
        report_result(server_url, node_id, command_id, False, {"error": f"未知动作: {action}"})


# ============== 主循�?==============

def main():
    parser = argparse.ArgumentParser(description="Termux 语音助手节点 v2")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="主服务地址")
    parser.add_argument("--node-id", default=DEFAULT_NODE_ID, help="节点ID")
    parser.add_argument("--poll-interval", type=int, default=POLL_INTERVAL, help="轮询间隔(�?")
    args = parser.parse_args()

    print("=" * 50)
    print("Termux 语音助手节点 v2")
    print(f"主服�? {args.server}")
    print(f"节点ID: {args.node_id}")
    print(f"轮询间隔: {args.poll_interval}�?)
    print("=" * 50)

    while True:
        try:
            commands = poll_commands(args.server, args.node_id)
            if commands:
                print(f"\n收到 {len(commands)} 个命�?")
                for cmd in commands:
                    execute_command(cmd, args.server, args.node_id)
            else:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 等待命令...", end="\r")

            time.sleep(args.poll_interval)

        except KeyboardInterrupt:
            print("\n退�?..")
            break
        except Exception as e:
            print(f"\n错误: {e}")
            time.sleep(args.poll_interval)


if __name__ == "__main__":
    main()

