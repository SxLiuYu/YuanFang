#!/data/data/com.termux/files/usr/bin/python3
"""
Jarvis Phone Client V3 — 手机端语音交互 + VAD 检测 + 说话打断
循环: VAD 检测语音 → 录制 → 上传 Mac Mini → STT+LLM+TTS → 播放回复
支持: 说话打断TTS播放，自动检测语音起止

Usage:
    python3 jarvis_phone_vad.py [--server http://192.168.1.3:8000]
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
from typing import Optional, List

import numpy as np

DEFAULT_SERVER = "http://192.168.1.3:8000"
AUDIO_FILE = "/data/data/com.termux/files/home/jarvis_input.wav"
RESPONSE_FILE = "/data/data/com.termux/files/home/jarvis_response.wav"
NODE_ID = "jarvis_phone_hisense"

# VAD 配置
SAMPLE_RATE = 16000
CHUNK_MS = 30
CHUNK_SIZE = int(SAMPLE_RATE * CHUNK_MS / 1000)
SPEECH_THRESHOLD = 0.5
SILENCE_THRESHOLD = 1.0  # 静音多少秒后认为结束
MIN_SPEECH_MS = 100  # 最小语音长度ms
MAX_SPEECH_SEC = 15  # 最大语音长度s


def exec_cmd(cmd: str, timeout: int = 30) -> dict:
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return {"stdout": r.stdout.strip(), "stderr": r.stderr.strip(), "rc": r.returncode}
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "timeout", "rc": -1}


def stop_tts_playback() -> None:
    """停止正在播放的TTS"""
    exec_cmd("pkill -f termux-media-player || true")
    exec_cmd("pkill -f termux-tts-speak || true")


def tts_speak(text: str) -> bool:
    """Android 系统 TTS 朗读"""
    if len(text) > 400:
        text = text[:400] + "..."
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    r = exec_cmd(f'termux-tts-speak "{text}"', timeout=30)
    return r["rc"] == 0


def play_audio(path: str) -> bool:
    """播放音频文件"""
    # 使用 termux-media-player 播放
    r = exec_cmd(f"termux-media-player play {path}", timeout=30)
    return r["rc"] == 0


def voice_interact(audio_path: str, server_url: str, max_tokens: int = 256) -> tuple[bool, str, str, int]:
    """
    完整交互: 上传音频 → STT → LLM → TTS → 播放
    返回: (成功, 用户文字, 助手回复, 延迟ms)
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

        print(f"[{now()}] 🧠 服务器处理中...")
        sys.stdout.flush()
        with urllib.request.urlopen(req, timeout=180) as resp:
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
            print(f"[{now()}] 🔊 播放音频回复...")
            sys.stdout.flush()
            play_audio(RESPONSE_FILE)
        else:
            print(f"[{now()}] 🔊 系统TTS朗读: {assistant_text[:60]}...")
            sys.stdout.flush()
            tts_speak(assistant_text)

        return True, user_text, assistant_text, latency_ms

    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")[:300]
        return False, "", f"HTTP {e.code}: {err}", 0
    except urllib.error.URLError as e:
        return False, "", f"网络错误: {e.reason}", 0
    except Exception as e:
        return False, "", f"错误: {str(e)}", 0


def now() -> str:
    return datetime.now().strftime("%H:%M:%S")


def get_audio_chunk() -> Optional[np.ndarray]:
    """获取一小块音频用于VAD检测 (从live recording)"""
    # 由于 Termux 不支持流录音，我们采用短分段录音方式
    # termux-microphone-record 输出 MP4/AAC，用 pydub 直接读取
    tmp_dir = os.path.expanduser("~/tmp")
    os.makedirs(tmp_dir, exist_ok=True)
    tmp_m4a = os.path.join(tmp_dir, "chunk.m4a")
    # 每次录制大约 1秒（CHUNK_MS=30，所以总共 60ms 语音，但termux需要至少1秒）
    duration_sec = 1

    # 清理旧文件和旧进程
    exec_cmd("pkill -f termux-microphone-record || true")
    exec_cmd("termux-microphone-record -q > /dev/null 2>&1 || true")
    if os.path.exists(tmp_m4a):
        os.unlink(tmp_m4a)

    # 开始录制，用nohup放后台避免卡住SSH
    r = exec_cmd(f"nohup termux-microphone-record -f {tmp_m4a} -l {duration_sec} > /dev/null 2>&1 &", timeout=10)
    # 等待录制完成
    time.sleep(duration_sec + 0.3)
    # 主动停止录制，确保退出
    exec_cmd("termux-microphone-record -q > /dev/null 2>&1 || true")
    # 杀掉残留进程
    exec_cmd("pkill -f termux-microphone-record || true")
    if r["rc"] != 0:
        return None
    # 等待录制完成
    time.sleep(duration_sec + 0.3)
    # 杀掉残留进程
    exec_cmd("pkill -f termux-microphone-record || true")

    if not os.path.exists(tmp_m4a) or os.path.getsize(tmp_m4a) < 100:
        return None

    # 使用 pydub 直接读取 m4a 并转换为 numpy 数组
    try:
        from pydub import AudioSegment
        audio = AudioSegment.from_file(tmp_m4a, format="m4a")
        # 转换为单声道
        audio = audio.set_channels(1)
        # 重采样到目标采样率
        audio = audio.set_frame_rate(SAMPLE_RATE)
        # 转换为 float32 numpy 数组
        samples = np.array(audio.get_array_of_samples()).astype(np.float32) / 32768.0
        # 清理
        os.unlink(tmp_m4a)
        return samples
    except Exception as e:
        print(f"[DEBUG] pydub read error: {e}")
        sys.stdout.flush()
        if os.path.exists(tmp_m4a):
            os.unlink(tmp_m4a)
        return None


def record_full_speech(output_path: str, max_duration: float = MAX_SPEECH_SEC) -> tuple[bool, float]:
    """使用VAD检测录音，直到静音结束"""
    print(f"[{now()}] 🎙️ 检测到语音，开始录音...")
    sys.stdout.flush()

    # 直接录最长时长，因为VAD已经检测到开始了
    # Termux API不支持流，分块慢慢录
    speech_chunks: List[np.ndarray] = []
    silence_start_time: Optional[float] = None
    speech_start = time.time()
    has_speech = False

    while time.time() - speech_start < max_duration:
        chunk = get_audio_chunk()
        if chunk is None:
            continue

        energy = np.abs(chunk).mean()
        # 计算能量判断是否有语音
        # 简单策略：能量超过阈值认为有语音
        if energy > 0.0002:  # 录音阶段静音检测阈值 - 再降低，更容易判定为静音
            has_speech = True
            silence_start_time = None
            speech_chunks.append(chunk)
        else:
            if has_speech:
                if silence_start_time is None:
                    silence_start_time = time.time()
                elif time.time() - silence_start_time >= SILENCE_THRESHOLD:
                    # 静音足够长时间，结束录音
                    break
                speech_chunks.append(chunk)
            else:
                # 还没语音，继续等
                continue

        # ========== 说话打断检测 ==========
        # 如果TTS正在播放，这里我们检测到用户说话，直接打断
        # 客户端无法直接知道服务器是否在播放，但用户说话必然是打断
        # 所以我们直接停止本地播放
        stop_tts_playback()

    if not speech_chunks:
        return False, 0.0

    # 合并所有块
    full_audio = np.concatenate(speech_chunks)

    # 保存为wav
    import wave
    n_frames = len(full_audio)
    with wave.open(output_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes((full_audio * 32768).astype(np.int16).tobytes())

    duration = time.time() - speech_start
    print(f"[{now()}] ✅ 录音完成，{duration:.1f}秒")
    sys.stdout.flush()
    return True, duration


def main_loop(server_url: str) -> None:
    print("=" * 60)
    print("🎙️ JARVIS Phone Client VAD — 语音交互")
    print(f"   服务器: {server_url}")
    print(f"   VAD 自动检测语音起止")
    print(f"   ✅ 支持说话打断TTS播放")
    print(f"   节点: {NODE_ID}")
    print(f"   按 Ctrl+C 退出")
    print("=" * 60)
    sys.stdout.flush()

    # 首次启动提示
    stop_tts_playback()
    print("[INFO] 播放启动提示音...")
    sys.stdout.flush()
    try:
        tts_speak("贾维斯已就绪，随时可以说话")
    except Exception:
        pass
    sys.stdout.flush()

    try:
        while True:
            # 等待语音开始 (通过能量检测)
            print(f"\n[{now()}] 👂 聆听中...")
            sys.stdout.flush()
            speech_detected = False
            while not speech_detected:
                chunk = get_audio_chunk()
                if chunk is None:
                    time.sleep(0.1)
                    continue

                energy = np.abs(chunk).mean()
                if energy > 0.0003:  # 检测到说话开始 - 适度调低更容易触发
                    speech_detected = True
                    break

                # 空闲时继续检查，看看是否有打断需要处理
                # 如果TTS正在播放并且检测到能量，打断它
                stop_tts_playback()

                time.sleep(0.05)
            sys.stdout.flush()

            # 开始录音完整语音
            ok, duration = record_full_speech(AUDIO_FILE)
            if not ok or duration < MIN_SPEECH_MS / 1000:
                print(f"  ⚠️ 录音太短，忽略")
                continue

            # 交互
            ok, user_txt, resp, latency = voice_interact(AUDIO_FILE, server_url)
            if not ok:
                print(f"  ❌ {resp}")
                sys.stdout.flush()
                tts_speak("处理失败，请重试")
                continue

            print(f"  👤 你说: {user_txt}")
            print(f"  🤖 回复 ({latency}ms): {resp[:80]}...")
            sys.stdout.flush()
            time.sleep(0.2)

    except KeyboardInterrupt:
        print("\n\n👋 退出...")
        sys.stdout.flush()
        stop_tts_playback()
        try:
            tts_speak("再见")
        except Exception:
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Jarvis Phone Client VAD")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="Server URL")
    args = parser.parse_args()
    main_loop(args.server)
