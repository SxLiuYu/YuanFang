#!/usr/bin/env python3
"""
手机端 VAD 监听 — 纯 Python + termux-microphone-record
无需 ffmpeg/sox，说完自动发，收到回复自动播放
"""
import os
import sys
import time
import wave
import audioop
import subprocess
import json
import uuid
import base64
import threading
from datetime import datetime

SERVER_URL = "http://192.168.1.3:8000"
# VAD 参数
SAMPLE_RATE = 16000
ENERGY_THRESHOLD = 400
MIN_SPEECH_SEC = 0.3   # 最少说话这么长时间才算有效
MAX_SILENCE_SEC = 1.2  # 说完后等待这么久没声音就发出去
REC_CHUNK_SEC = 0.05   # 每次录音块 50ms

TMP_DIR = "/data/data/com.termux/files/home"
RAW_AUDIO = f"{TMP_DIR}/vad_raw.wav"
SEND_AUDIO = f"{TMP_DIR}/vad_send.wav"
RESP_AUDIO = f"{TMP_DIR}/response.wav"


def record_chunk(seconds=5.0):
    """用 termux-microphone-record 录几秒，保存到 RAW_AUDIO"""
    try:
        proc = subprocess.run(
            ["termux-microphone-record", "-f", RAW_AUDIO, "-l", str(int(seconds * 1000))],
            timeout=seconds + 2,
            capture_output=True
        )
        return os.path.exists(RAW_AUDIO) and os.path.getsize(RAW_AUDIO) > 1000
    except Exception as e:
        return False


def analyze_and_send(filepath):
    """分析音频能量，有语音就发送"""
    try:
        with wave.open(filepath, 'rb') as wf:
            channels = wf.getnchannels()
            sample_width = wf.getsampwidth()
            framerate = wf.getframerate()
            nframes = wf.getnframes()
            audio_data = wf.readframes(nframes)
        
        # 分块分析能量
        chunk_size = int(framerate * REC_CHUNK_SEC) * sample_width
        total_chunks = len(audio_data) // chunk_size
        
        speech_frames = []
        for i in range(total_chunks):
            chunk = audio_data[i*chunk_size:(i+1)*chunk_size]
            try:
                energy = audioop.rms(chunk, sample_width)
            except:
                energy = 0
            if energy > ENERGY_THRESHOLD:
                speech_frames.append(chunk)
        
        speech_sec = len(speech_frames) * REC_CHUNK_SEC
        if speech_sec < MIN_SPEECH_SEC:
            return None
        
        # 保存有效语音
        with wave.open(SEND_AUDIO, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(SAMPLE_RATE)
            wf.writeframes(b''.join(speech_frames))
        
        # 发送
        return send_to_server(SEND_AUDIO)
        
    except Exception as e:
        return None


def send_to_server(filepath):
    """发送到 Mac Mini"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎤 发送中...")
    try:
        with open(filepath, 'rb') as f:
            audio_data = f.read()
        
        boundary = "----WebKitFormBoundary" + uuid.uuid4().hex[:16]
        body = b""
        body += f"--{boundary}\r\n".encode()
        body += f'Content-Disposition: form-data; name="file"; filename="voice.wav"\r\n'.encode()
        body += b"Content-Type: audio/wav\r\n\r\n"
        body += audio_data
        body += f"\r\n--{boundary}--\r\n".encode()
        
        req = urllib.request.Request(
            f"{SERVER_URL}/api/voice/mlx-voice/pipeline",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read().decode("utf-8"))
        
        if result.get("success"):
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ 处理成功")
            return result
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ {result.get('error')}")
            return None
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ 错误: {e}")
        return None


def play_audio(audio_b64):
    """播放 base64 音频"""
    try:
        audio_bytes = base64.b64decode(audio_b64)
        with open(RESP_AUDIO, 'wb') as f:
            f.write(audio_bytes)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔊 播放中...")
        subprocess.run(["termux-media-player", "play", RESP_AUDIO], 
                      timeout=60, capture_output=True)
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔊 播放完成")
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔊 播放失败: {e}")


def continuous_listen():
    """
    持续 VAD 监听：
    1. 短录音 → 分析能量
    2. 如果有语音 → 继续录音 MAX_SILENCE_SEC 秒
    3. 静音后 → 发送分析
    """
    print("=" * 50)
    print("🦞 持续监听模式 — 说完自动处理")
    print(f"   服务器: {SERVER_URL}")
    print(f"   能量阈值: {ENERGY_THRESHOLD}")
    print("   按 Ctrl+C 退出")
    print("=" * 50)
    
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 👂 开始监听...")
    
    silence_chunks = 0
    chunks_needed = int(MAX_SILENCE_SEC / REC_CHUNK_SEC)
    is_speech = False
    collected_frames = []
    
    while True:
        # 短录音 200ms
        ok = record_chunk(seconds=0.2)
        if not ok:
            time.sleep(0.1)
            continue
        
        try:
            with wave.open(RAW_AUDIO, 'rb') as wf:
                audio_data = wf.readframes(wf.getnframes())
                sample_width = wf.getsampwidth()
                energy = audioop.rms(audio_data[:512], sample_width) if len(audio_data) >= 512 else 0
        except:
            energy = 0
        
        if energy > ENERGY_THRESHOLD:
            if not is_speech:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎙️ 检测到说话...")
            is_speech = True
            silence_chunks = 0
            # 继续录音收集
            collected_frames.append(audio_data)
        else:
            if is_speech:
                silence_chunks += 1
                collected_frames.append(audio_data)
                if silence_chunks >= chunks_needed:
                    # 说完，发送
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 🔇 说完，发送 ({len(collected_frames)} 块)...")
                    
                    # 保存收集的音频
                    with wave.open(SEND_AUDIO, 'wb') as wf:
                        wf.setnchannels(1)
                        wf.setsampwidth(2)
                        wf.setframerate(SAMPLE_RATE)
                        wf.writeframes(b''.join(collected_frames))
                    
                    result = send_to_server(SEND_AUDIO)
                    if result and result.get('audio_data'):
                        play_audio(result['audio_data'])
                    
                    # 重置
                    collected_frames = []
                    silence_chunks = 0
                    is_speech = False
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] 👂 继续监听...")
        
        # 超时保护：超过 30s 强制发送
        if len(collected_frames) > 600:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏰ 超时，强制发送")
            with wave.open(SEND_AUDIO, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                wf.writeframes(b''.join(collected_frames))
            result = send_to_server(SEND_AUDIO)
            if result and result.get('audio_data'):
                play_audio(result['audio_data'])
            collected_frames = []
            silence_chunks = 0
            is_speech = False


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="VAD 持续监听")
    parser.add_argument("--server", default="http://192.168.1.3:8000")
    parser.add_argument("--threshold", type=int, default=400)
    args = parser.parse_args()
    
    SERVER_URL = args.server
    ENERGY_THRESHOLD = args.threshold
    
    try:
        continuous_listen()
    except KeyboardInterrupt:
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] 退出监听模式")
