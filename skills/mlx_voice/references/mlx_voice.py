# references/mlx_voice.py
"""
MLX Voice Pipeline — 本地语音交互管线
Mac Mini M4 (MLX) + Gemma 4B + Whisper + Kokoro TTS

管线流程:
  语音输入 → mlx_whisper (STT) → OMLX Server (Gemma LLM) → mlx_audio (Kokoro TTS) → 语音输出
"""
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# ==================== 配置 ====================

OMLX_BASE_URL = "http://localhost:8080"
OMLX_AUTH = "Bearer omlx"
DEFAULT_MODEL = "gemma-4-E4B-it-4bit"

# 模型路径
KOKORO_MODEL_PATH = "prince-canuma/Kokoro-82M"
DEFAULT_VOICE = "af_heart"  # 女性温暖声音

# 输出目录
OUTPUT_DIR = Path("~/YuanFang/data/audio").expanduser()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ==================== STT — mlx_whisper ====================

def transcribe(audio_path: str) -> str:
    """
    语音转文字 (mlx_whisper)
    
    Args:
        audio_path: 音频文件路径 (wav/mp3/m4a)
    
    Returns:
        识别出的文字
    """
    try:
        import mlx_whisper
    except ImportError:
        raise RuntimeError(
            "mlx_whisper 未安装。请运行:\n"
            "  ~/.venv-omlx/bin/pip install mlx-whisper"
        )
    
    logger.info(f"[MLX Voice] 转写中: {audio_path}")
    result = mlx_whisper.transcribe(audio_path)
    text = result.get("text", "").strip()
    logger.info(f"[MLX Voice] 转写结果: {text}")
    return text


# ==================== LLM — OMLX Server (Gemma 4B) ====================

def chat(
    message: str,
    system_prompt: str = "你是一个有帮助的AI助手。请用中文回复。",
    model: str = DEFAULT_MODEL,
    max_tokens: int = 512,
    temperature: float = 0.7,
) -> str:
    """
    通过 OMLX Server 调用 Gemma 4B 进行对话
    
    Args:
        message: 用户消息
        system_prompt: 系统提示词
        model: 模型名称
        max_tokens: 最大生成token数
        temperature: 温度参数
    
    Returns:
        LLM 生成的回复
    """
    import requests
    
    url = f"{OMLX_BASE_URL}/v1/chat/completions"
    headers = {
        "Authorization": OMLX_AUTH,
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    
    logger.info(f"[MLX Voice] LLM 推理中... (model={model})")
    response = requests.post(url, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    
    result = response.json()
    reply = result["choices"][0]["message"]["content"].strip()
    logger.info(f"[MLX Voice] LLM 回复: {reply[:100]}...")
    return reply


# ==================== TTS — mlx_audio (Kokoro) ====================

def speak(
    text: str,
    voice: str = DEFAULT_VOICE,
    output_file: Optional[str] = None,
) -> str:
    """
    文字转语音 (Kokoro TTS)
    
    Args:
        text: 要朗读的文字
        voice: 声音名称 (af_heart, bf_heart, etc.)
        output_file: 输出文件路径 (默认生成时间戳文件名)
    
    Returns:
        生成的音频文件路径
    """
    try:
        from mlx_audio.tts.generate import generate_audio
    except ImportError:
        raise RuntimeError(
            "mlx_audio 未安装。请运行:\n"
            "  ~/.venv-omlx/bin/pip install mlx-audio"
        )
    
    if not output_file:
        import time
        output_file = str(OUTPUT_DIR / f"response_{int(time.time())}.wav")
    
    logger.info(f"[MLX Voice] TTS 生成中... (voice={voice})")
    generate_audio(
        text=text,
        model_path=KOKORO_MODEL_PATH,
        voice=voice,
        file_prefix=output_file.replace(".wav", ""),
        audio_format="wav",
    )
    
    actual_file = f"{output_file.replace('.wav', '')}.wav"
    logger.info(f"[MLX Voice] 语音已生成: {actual_file}")
    return actual_file


# ==================== 完整管线 ====================

def voice_pipeline(
    audio_path: str,
    system_prompt: str = "你是一个有帮助的AI助手。请用中文回复。",
    use_tts: bool = True,
    voice: str = DEFAULT_VOICE,
) -> dict:
    """
    完整 MLX 语音管线
    
    Args:
        audio_path: 音频文件路径
        system_prompt: 系统提示词
        use_tts: 是否生成语音回复
        voice: TTS 声音
    
    Returns:
        {
            "text": 用户语音转写的文字,
            "response": LLM 回复,
            "audio_file": 生成的语音文件路径 (如果有),
            "success": 是否成功
        }
    """
    result = {
        "success": False,
        "text": "",
        "response": "",
        "audio_file": None,
        "error": None,
    }
    
    try:
        # Step 1: STT
        result["text"] = transcribe(audio_path)
        
        # Step 2: LLM
        result["response"] = chat(result["text"], system_prompt=system_prompt)
        
        # Step 3: TTS (可选)
        if use_tts:
            result["audio_file"] = speak(result["response"], voice=voice)
        
        result["success"] = True
        
    except Exception as e:
        logger.error(f"[MLX Voice] 管线错误: {e}")
        result["error"] = str(e)
    
    return result


# ==================== 健康检查 ====================

def health_check() -> dict:
    """
    检查 MLX 语音管线各组件状态
    """
    import requests
    
    status = {
        "omlx_server": False,
        "mlx_whisper": False,
        "mlx_audio": False,
    }
    
    # OMLX Server
    try:
        resp = requests.get(f"{OMLX_BASE_URL}/health", timeout=5)
        status["omlx_server"] = resp.status_code == 200
    except Exception:
        pass
    
    # mlx_whisper
    try:
        import mlx_whisper
        status["mlx_whisper"] = True
    except ImportError:
        pass
    
    # mlx_audio
    try:
        from mlx_audio.tts.generate import generate_audio
        status["mlx_audio"] = True
    except ImportError:
        pass
    
    return status


# ==================== CLI 入口 ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="MLX Voice 触手")
    parser.add_argument("audio", help="音频文件路径")
    parser.add_argument("--no-tts", action="store_true", help="禁用 TTS")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="TTS 声音")
    args = parser.parse_args()
    
    print(f"[MLX Voice] 音频文件: {args.audio}")
    
    # 健康检查
    print("\n=== 组件状态 ===")
    for component, ok in health_check().items():
        print(f"  {component}: {'✅' if ok else '❌'}")
    
    # 执行管线
    print("\n=== 执行语音管线 ===")
    result = voice_pipeline(args.audio, use_tts=not args.no_tts, voice=args.voice)
    
    if result["success"]:
        print(f"\n✅ 成功!")
        print(f"  用户: {result['text']}")
        print(f"  助手: {result['response']}")
        if result["audio_file"]:
            print(f"  语音: {result['audio_file']}")
    else:
        print(f"\n❌ 失败: {result['error']}")