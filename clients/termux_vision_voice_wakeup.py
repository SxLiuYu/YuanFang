#!/usr/bin/env python3
"""
Termux Vision + Voice + WakeWord — 贾维斯离线唤醒版
- openwakeword 离线唤醒 "贾维斯" / "你好贾维斯"
- 唤醒后自动录音+拍照 → 上传Mac → 获取回复 → 播放 + 红外控制
- 支持后台持续监听，不需要手动触发

要求:
- 手机Termux安装openwakeword（或使用openwakeword轻量模型）
- pip install openwakeword pyaudio
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
import wave

DEFAULT_SERVER = "http://192.168.1.3:8000"
AUDIO_FILE = "/data/data/com.termux/files/home/voice_input.wav"
IMAGE_FILE = "/data/data/com.termux/files/home/camera_photo.jpg"
RECORD_DURATION = 6
WAKE_WORD = "贾维斯"
THRESHOLD = 0.5  # 唤醒阈值

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

def check_wakeword_available():
    """检查openwakeword是否可用"""
    r = exec_cmd("python3 -c 'import openwakeword' 2>/dev/null")
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

def record_after_wakeup(duration=RECORD_DURATION, output=AUDIO_FILE):
    """唤醒后录音"""
    exec_cmd("pkill -f termux-microphone-record || true")
    time.sleep(0.3)
    r = exec_cmd(f"termux-microphone-record -f {output} -l {duration} -d", timeout=5)
    if r["rc"] != 0:
        return False, f"录音失败: {r['stderr']}"
    print(f"🎤 录音中... ({duration}s)")
    time.sleep(duration + 2)
    exec_cmd("pkill -f termux-microphone-record || true")
    time.sleep(0.5)
    if not os.path.exists(output):
        return False, "音频文件不存在"
    if os.path.getsize(output) < 1000:
        return False, f"文件太小 ({os.path.getsize(output)} bytes)"
    print(f"✅ 录音完成: {os.path.getsize(output)} bytes")
    return True, output

def infrared_transmit(frequency, pattern):
    """发射红外信号"""
    cmd = f"termux-infrared-transmit -f {frequency} {pattern}"
    r = exec_cmd(cmd, timeout=10)
    return r["rc"] == 0, r["stderr"]

def vibrate(duration=100):
    """振动反馈，表示唤醒成功"""
    exec_cmd(f"termux-vibrate -d {duration} -f")

def beep():
    """提示音，表示可以说话了"""
    exec_cmd("termux-media-player play /system/media/audio/ui/KeypressStandard.ogg 2>/dev/null || true")

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

def vision_voice_interact(audio_path, image_path, server_url, node_id="termux_wakeup", max_tokens=384, enable_vision=True):
    """完整视觉语音交互，含返回结果处理"""
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

        body += f'Content-Disposition: form-data; name="max_tokens"\r\n\r\n'.encode()
        body += f"{max_tokens}\r\n".encode()
        body += f"--{boundary}--\r\n".encode()

        endpoint = f"{server_url}/api/voice/vision-voice/pipeline"
        req = urllib.request.Request(
            endpoint,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST"
        )

        print(f"[{datetime.now().strftime('%H:%M:%S')}] 🧠 处理中...")
        with urllib.request.urlopen(req, timeout=240) as resp:
            result = json.loads(resp.read().decode("utf-8"))

        if not result.get("success"):
            return False, "", result.get("error", "处理失败"), 0

        user_text = result.get("text", "")
        assistant_text = result.get("response", "")
        audio_b64 = result.get("audio_data", "")
        thinking = result.get("thinking", "")
        infrared = result.get("infrared", None)
        latency_ms = int((time.time() - start) * 1000)

        # 如果有红外控制指令，执行
        infrared_ok = False
        if infrared and check_infrared_available():
            freq = infrared.get("frequency", 38000)
            pattern = infrared.get("pattern", "")
            if pattern:
                print(f"📶 发送红外信号: {freq} Hz")
                ok, err = infrared_transmit(freq, pattern)
                infrared_ok = ok
                if ok:
                    assistant_text += "\n[红外已发送 ✅]"
                else:
                    assistant_text += f"\n[红外发送失败 ❌: {err}]"

        # 播放语音回复
        if audio_b64:
            audio_bytes = base64.b64decode(audio_b64)
            wav_path = "/data/data/com.termux/files/home/response.wav"
            with open(wav_path, "wb") as f:
                f.write(audio_bytes)
            print(f"🔊 播放回复...")
            subprocess.run(["termux-media-player", "play", wav_path], timeout=60, capture_output=True)
        else:
            print(f"🔊 TTS朗读: {assistant_text[:80]}...")
            tts_speak(assistant_text)

        # 记入日志
        log_conversation(server_url, node_id, user_text, assistant_text, latency_ms)

        if thinking:
            print(f"[思考] {thinking[:80]}...")

        return True, user_text, assistant_text, latency_ms

    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")[:200]
        return False, "", f"HTTP {e.code}: {err}", 0
    except urllib.error.URLError as e:
        return False, "", f"网络错误: {e.reason}", 0
    except Exception as e:
        return False, "", f"错误: {str(e)}", 0

def run_wakeword_listening(server_url, enable_vision=True, threshold=THRESHOLD):
    """运行离线唤醒监听循环"""
    try:
        import pyaudio
        from openwakeword.model import Model
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("\n请先安装依赖:\n")
        print("  pkg install python-pyaudio")
        print("  pip install openwakeword")
        print("\n下载模型:")
        print("  可以从 https://github.com/dscripka/openWakeWord/releases 下载预训练模型")
        print("  或用: openwakeword download 贾维斯")
        return False

    # 加载唤醒词模型
    # 默认使用预训练的alexa模型，你需要替换成你训练的"贾维斯"模型
    model_path = "/data/data/com.termux/files/home/jiasi_justin.onnx"
    if not os.path.exists(model_path):
        print(f"⚠️  未找到自定义模型 {model_path}")
        print("使用默认预训练 'alexa' 模型测试... 说 'alexa' 唤醒")
        # 下载默认模型
        exec_cmd("cd && wget -O alexa.onnx https://github.com/dscripka/openwakeword/releases/download/v0.1.0/alexa-verb-alexa-nocrowd-v3.onnx")
        model_path = "alexa.onnx"

    print(f"🧠 加载唤醒词模型: {model_path}")
    owwModel = Model(model_path)

    # 配置音频输入
    CHUNK = 1280
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000

    p = pyaudio.PyAudio()
    stream = p.open(
        format=FORMAT,
        channels=CHANNELS,
        rate=RATE,
        input=True,
        frames_per_buffer=CHUNK
    )

    print("\n" + "=" * 60)
    print("🎧 贾维斯离线唤醒监听已启动")
    print(f"   阈值: {threshold}")
    print(f"   视觉: {'开启' if enable_vision else '关闭'}")
    print(f"   服务器: {server_url}")
    ir_available = check_infrared_available()
    print(f"   红外: {'✅ 可用' if ir_available else '❌ 不可用'}")
    print("\n请说唤醒词...")
    print("=" * 60 + "\n")

    try:
        while True:
            audio_chunk = stream.read(CHUNK, exception_on_overflow=False)
            prediction = owwModel.predict(audio_chunk)

            # 获取最高得分
            max_score = max(prediction.values())
            if max_score > threshold:
                wake_word = max(prediction, key=prediction.get)
                print(f"\n⚡ 唤醒! (得分: {max_score:.4f}, 词: {wake_word})")
                vibrate(150)
                beep()
                time.sleep(0.5)

                # 拍照（如果开视觉）
                photo_ok = False
                if enable_vision:
                    print("📸 拍照...")
                    photo_ok, img = take_photo()
                    if not photo_ok:
                        print(f"  ❌ {img}")

                # 录音
                ok, msg = record_after_wakeup()
                if not ok:
                    print(f"  ❌ {msg}")
                    time.sleep(1)
                    continue

                # 交互
                ok, user_txt, resp, latency = vision_voice_interact(
                    AUDIO_FILE, IMAGE_FILE, server_url, enable_vision=enable_vision
                )
                if not ok:
                    print(f"  ❌ {resp}")
                    continue

                print(f"  ✅ 完成 ({latency}ms)")
                print(f"  你说: {user_txt}")
                print(f"  贾维斯: {resp[:150]}{'...' if len(resp) > 150 else ''}")
                print("\n🧠 继续监听唤醒词...\n")
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n👋 停止监听")
        stream.stop_stream()
        stream.close()
        p.terminate()
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Termux Vision + Voice + WakeWord")
    parser.add_argument("--server", default=DEFAULT_SERVER, help="服务器地址")
    parser.add_argument("--duration", type=int, default=RECORD_DURATION, help="唤醒后录音时长")
    parser.add_argument("--no-vision", action="store_true", help="禁用视觉模式")
    parser.add_argument("--threshold", type=float, default=THRESHOLD, help="唤醒阈值")
    parser.add_argument("--model", default="", help="唤醒词模型路径")
    args = parser.parse_args()

    RECORD_DURATION = args.duration
    if args.model:
        WAKE_WORD_MODEL = args.model

    print("=" * 60)
    print("🤖 贾维斯 — 离线唤醒 视觉语音助手")
    print("   唤醒词: " + WAKE_WORD)
    print("   阈值: " + str(args.threshold))
    print("=" * 60)

    # 检查依赖
    if not check_wakeword_available():
        print("\n❌ openwakeword 未安装，请先在Termux安装:")
        print("   pkg install python-pyaudio")
        print("   pip install openwakeword")
        print("\n然后下载训练好的'贾维斯'唤醒词模型到 ~/jiasi_justin.onnx")
        exit(1)

    # 开始监听
    run_wakeword_listening(args.server, enable_vision=not args.no_vision, threshold=args.threshold)
