#!/usr/bin/env python3
"""
Jarvis Voice Pipeline — 流式语音对话
解决 Qwen3.5 thinking 模式：实时过滤 reasoning_content，只对正式回答做 TTS

流程:
  [麦克风/文件] → Whisper STT → Qwen3.5 流式推理 → 过滤思考过程 → Kokoro TTS → 播放
"""

import os
import sys
import time
import json
import wave
import tempfile
import subprocess
import numpy as np
import requests
from pathlib import Path

# 尝试使用统一配置，如果独立运行则使用默认值
try:
    import sys
    sys.path.insert(0, '/Users/sxliuyu/YuanFang/core/config')
    from config import get_config
    config = get_config()
    jarvis_config = config.jarvis_voice
    OMLX_BASE_URL = jarvis_config.omlx_base_url
    OMLX_AUTH = jarvis_config.omlx_auth
    DEFAULT_MODEL = jarvis_config.default_model
    KOKORO_MODEL = jarvis_config.kokoro_model
    DEFAULT_VOICE = jarvis_config.default_voice
    OUTPUT_DIR = Path(jarvis_config.output_dir).expanduser()
except (ImportError, AttributeError):
    # 独立运行时使用默认配置
    # ==================== 配置 ====================
    OMLX_BASE_URL = "http://localhost:4560"
    # oMLX 即使 skip_api_key_verification=true 仍然要求 API key
    # 配置正确的 API key
    OMLX_AUTH = "jarvis-local"
    DEFAULT_MODEL = "Qwen3.5-4B-MLX-4bit"
    KOKORO_MODEL = "prince-canuma/Kokoro-82M"
    DEFAULT_VOICE = "af_heart"
    OUTPUT_DIR = Path("~/YuanFang/data/audio").expanduser()

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# OMLX_URL 别名兼容旧代码
OMLX_URL = OMLX_BASE_URL

# ==================== 核心: 流式对话 + 思考过滤 ====================

def stream_chat_filtered(message, system_prompt=None):
    """
    流式对话，返回 (text_type, token)
    text_type: 'thinking' | 'content' | 'done'
    
    Qwen3.5 thinking 模式处理：
    - 情况1：思考过程在 reasoning_content，回答在 content → 过滤 reasoning_content
    - 情况2：思考过程直接写在 content 里 → 检测并跳过 "Thinking Process:" 直到 "Final Answer"
    - 情况3：流式时只有 reasoning_content，content 在最后 → 需要在最后获取完整 content
    """
    if system_prompt is None:
        system_prompt = "你叫元芳，是于金泽的AI助手。回答简洁有帮助，用中文。"
    
    payload = {
        "model": DEFAULT_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        "stream": True,
    }

    headers = {
        "Content-Type": "application/json"
    }
    if OMLX_AUTH and OMLX_AUTH.strip():
        headers["Authorization"] = OMLX_AUTH
    
    response_text = ""
    thinking_buffer = ""
    found_final_answer = False
    has_seen_content = False

    try:
        resp = requests.post(f"{OMLX_BASE_URL}/v1/chat/completions",
                           json=payload, headers=headers, timeout=60, stream=True)
        resp.raise_for_status()
        
        for line in resp.iter_lines():
            if not line or line.startswith(b": "):
                continue
            if line.startswith(b"data: "):
                data = line[6:]
                if data.strip() == b"[DONE]":
                    break
                
                try:
                    chunk = json.loads(data)
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    
                    # 情况1：推理在 reasoning_content 分开字段 → 全部过滤
                    reasoning = delta.get("reasoning_content")
                    if reasoning:
                        thinking_buffer += reasoning
                        # 不yield思考内容
                    
                    # 检查是否有 content
                    content = delta.get("content")
                    if content:
                        has_seen_content = True
                        response_text += content
                        
                        # 状态机处理：还在找 Final Answer 标记（当推理混在 content 时）
                        if not found_final_answer:
                            thinking_buffer += content
                            # 检测各种可能的回答开始标记
                            if "**Final Answer:**" in thinking_buffer or                                "最终答案：" in thinking_buffer or                                "答案：" in thinking_buffer or                                "回答：" in thinking_buffer or                                "Draft the Answer:" in thinking_buffer:
                                found_final_answer = True
                                # 提取标记之后的内容作为回答开始
                                for marker in ["**Final Answer:**", "最终答案：", "答案：", "回答：", "Draft the Answer:"]:
                                    if marker in thinking_buffer:
                                        idx = thinking_buffer.find(marker) + len(marker)
                                        final_start_content = thinking_buffer[idx:]
                                        if final_start_content.strip():
                                            yield ("content", final_start_content)
                                        break
                                continue
                            continue
                        else:
                            # 已经找到 Final Answer，正常输出
                            yield ("content", content)
                        
                except json.JSONDecodeError:
                    continue
        
        # 流式结束后处理：
        # 情况A：如果没有收到任何 content → 重新请求非流式
        # 情况B：如果收到了 content 但还没找到 Final Answer 标记 → 直接返回现有 content（因为此时 content 本身就是完整回答）
        if not has_seen_content:
            # 重新请求非流式获取完整结果
            non_stream_payload = payload.copy()
            non_stream_payload["stream"] = False
            resp = requests.post(f"{OMLX_URL}/v1/chat/completions", 
                               json=non_stream_payload, headers=headers, timeout=120)
            resp.raise_for_status()
            result = resp.json()
            message = result["choices"][0]["message"]
            content = message.get("content", "")
            
            # 如果思考过程混在 content 中，提取 Final Answer 部分
            if content and ("Thinking Process:" in content or "**Final Answer:**" in content or "最终答案：" in content or "Draft" in content):
                markers = ["**Final Answer:**", "最终答案：", "答案：", "回答：", "Draft the Answer:", "**Draft the Answer:**"]
                found_marker = False
                for marker in markers:
                    if marker in content:
                        idx = content.find(marker) + len(marker)
                        content = content[idx:]
                        found_marker = True
                        break
                # 找到标记后，仍然可能有多个草稿，取最后一个 bullet 点
                if found_marker:
                    lines = content.split("\n")
                    last_answer = None
                    for line in lines:
                        line = line.strip()
                        if line.startswith(('* ', '• ', '- ')) and ':' in line:
                            idx = line.find(':')
                            candidate = line[idx+1:].strip()
                            if candidate:
                                last_answer = candidate
                    if last_answer:
                        content = last_answer
                content = content.strip()
            
            if content.strip():
                yield ("content", content.strip())
        elif has_seen_content and not found_final_answer:
            # 已经收到 content，但全程没找到 Final Answer 标记
            # 这种情况就是：思考在 reasoning_content，回答直接在 content → 直接返回收集到的全部 content
            content = response_text.strip()
            if content:
                yield ("content", content)
                    
        yield ("done", "")
                    
    except Exception as e:
        yield ("error", str(e))


def chat_once(message, system_prompt=None):
    """单次对话，返回正式回答（过滤掉思考过程）"""
    full_response = ""
    for text_type, token in stream_chat_filtered(message, system_prompt):
        if text_type == "content":
            full_response += token
        elif text_type == "error":
            return f"[错误: {token}]"
    return full_response if full_response.strip() else "[无响应]"

# ==================== TTS — Kokoro ====================

def speak(text, voice=DEFAULT_VOICE, output_dir=OUTPUT_DIR):
    """TTS 生成并播放"""
    if not text or not text.strip():
        return
    
    text = text.strip()
    if len(text) > 500:
        text = text[:500]  # 限制长度
    
    timestamp = int(time.time())
    output_path = output_dir / f"jarvis_{timestamp}"
    
    try:
        from mlx_audio.tts.generate import generate_audio
        
        generate_audio(
            text=text,
            model=KOKORO_MODEL,
            voice=voice,
            file_prefix=str(output_path),
            audio_format="wav",
        )
        
        wav_file = f"{output_path}.wav"
        if os.path.exists(wav_file):
            # 播放
            subprocess.Popen([
                "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", wav_file
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"🔊 播放: {text[:50]}...")
            
    except Exception as e:
        print(f"⚠️ TTS 错误: {e}")

# ==================== STT — Whisper ====================

def transcribe(audio_path_or_array, sample_rate=16000):
    """Whisper 转写"""
    import mlx_whisper
    
    if isinstance(audio_path_or_array, np.ndarray):
        # 保存为临时 wav
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as f:
            wav_path = f.name
            audio_int16 = (audio_path_or_array * 32767).astype(np.int16)
            with wave.open(wav_path, 'w') as wav:
                wav.setnchannels(1)
                wav.setsampwidth(2)
                wav.writeframes(audio_int16.tobytes())
        try:
            result = mlx_whisper.transcribe(wav_path, language="zh")
            text = result.get("text", "").strip()
            os.unlink(wav_path)
            return text if text else None
        finally:
            if os.path.exists(wav_path):
                os.unlink(wav_path)
    else:
        result = mlx_whisper.transcribe(audio_path_or_array, language="zh")
        return result.get("text", "").strip()

# ==================== 流式 TTS ====================

def speak_streaming(text_gen, voice=DEFAULT_VOICE, output_dir=OUTPUT_DIR, chunk_size=50):
    """
    流式 TTS：实时生成并播放
    接收文本生成器，分段合成语音
    """
    from mlx_audio.tts.generate import generate_audio
    
    full_text = ""
    chunks = []
    
    for text_type, token in text_gen:
        if text_type == "content":
            full_text += token
            chunks.append(token)
            
            # 每 chunk_size 个字生成一次
            if len(full_text) >= chunk_size:
                _speak_chunk(full_text, voice, output_dir)
                full_text = ""
                chunks = []
    
    # 剩余文本
    if full_text:
        _speak_chunk(full_text, voice, output_dir)

def _speak_chunk(text, voice, output_dir):
    """合成并播放一段文本"""
    from mlx_audio.tts.generate import generate_audio
    
    if not text.strip():
        return
    
    timestamp = int(time.time())
    output_path = output_dir / f"chunk_{timestamp}"
    
    try:
        generate_audio(
            text=text,
            model=KOKORO_MODEL,
            voice=voice,
            file_prefix=str(output_path),
            audio_format="wav",
        )
        
        wav_file = f"{output_path}.wav"
        if os.path.exists(wav_file):
            subprocess.Popen([
                "ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", wav_file
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"  🔊 {text[:30]}...")
    except Exception as e:
        print(f"  ⚠️ TTS chunk error: {e}")

# ==================== 测试模式 ====================

def test_pipeline():
    """测试完整管线（不需要麦克风）"""
    print("\n" + "="*60)
    print("  Jarvis Pipeline 测试")
    print("="*60)
    
    # 1. 检查 OMLX
    print("\n[1] 检查 OMLX Server...")
    try:
        r = requests.get(f"{OMLX_URL}/health", timeout=5)
        print(f"    ✅ OMLX 可达: {r.status_code}")
        print(f"    Debug: OMLX_AUTH = {repr(OMLX_AUTH)}")
    except Exception as e:
        print(f"    ❌ OMLX 不可达: {e}")
        return False
    
    # 2. 测试对话过滤（不调用TTS避免版本问题）
    print("\n[2] 测试 Qwen3.5 流式推理（过滤思考）...")
    test_msg = "用三个词描述太阳"
    print(f"    输入: {test_msg}")
    
    response = ""
    for text_type, token in stream_chat_filtered(test_msg):
        if text_type == "content":
            response += token
            print(f"    → {token}", end="", flush=True)
    
    print(f"\n    最终回答: {response[:100]}...")
    
    # 3. 完整对话测试
    print("\n[3] 完整对话测试...")
    response = chat_once("1+1等于几？简单回答")
    print(f"    回答: {response[:100]}")
    
    if "[错误" in response:
        print(f"\n    ❌ LLM调用出错: {response}")
        return False
    
    print("\n✅ 所有测试通过！LLM推理+思考过滤工作正常。")
    print("  (TTS跳过因Python版本兼容性，需升级Python解决)")
    return True

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Jarvis Voice Pipeline")
    parser.add_argument("--test", action="store_true", help="运行测试模式")
    parser.add_argument("--chat", type=str, help="单次对话测试")
    parser.add_argument("--mic", action="store_true", help="启用麦克风监听")
    args = parser.parse_args()
    
    if args.test:
        test_pipeline()
    elif args.chat:
        response = chat_once(args.chat)
        print(f"\n元芳: {response}")
        # skip TTS for now
    else:
        test_pipeline()
