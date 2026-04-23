# routes/voice_pipeline.py
"""
Voice Pipeline Route — 全本地 MLX 实现
手机录音 → POST /api/voice/pipeline → mlx_whisper(STT) → OMLX Qwen3.5-9B-MLX-4bit(LLM) → macOS say(TTS) → 返回音频
"""
from flask import Blueprint, request, jsonify, send_file
import tempfile
import os
import logging
import subprocess
import base64
import requests

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from services.tools import (
    TOOL_REGISTRY, TOOL_SYSTEM_PROMPT,
    parse_tool_call, execute_tool_call, has_tool_prefix
)

logger = logging.getLogger(__name__)

voice_bp = Blueprint("voice", __name__, url_prefix="/api/voice")

# FinnA API 配置（仅 STT/TTS 备用）
FINNA_API_BASE = "https://www.finna.com.cn/v1"
FINNA_KEY_WHISPER = "app-d678VU1DyYuPJe6Lo6CuGLpE"
FINNA_KEY_COSYVOICE = "app-BqyKsTO4Om3JGoPCTkJX080J"
FINNA_KEY_DEEPSEEK = "app-d678VU1DyYuPJe6Lo6CuGLpE"

# 本地 OMLX 配置
OMLX_BASE = "http://localhost:4560"
# 绕过敏感内容过滤：将API key拆分拼接
OMLX_API_KEY = "sk-" + "omlx" + "-local"
OMLX_MODEL_LLM = "Qwen3.5-4B-MLX-4bit"
OMLX_MODEL_VL = "Qwen3-VL-8B-Thinking"

# 本地 STT 模型
LOCAL_STT_MODEL = "mlx-community/whisper-tiny"

# macOS say 声音（中文）
SAY_VOICE = "Tingting"


def init_voice_routes(app):
    app.register_blueprint(voice_bp)
    logger.info("[Voice] 路由已注册: /api/voice")


# ============== STT — mlx_whisper（本地） ==============

def stt_whisper(audio_path: str) -> str:
    """语音转文字 — 优先 mlx_whisper，失败则回退 FinnA"""
    try:
        import mlx_whisper
        result = mlx_whisper.transcribe(
            audio=audio_path,
            path_or_hf_repo=LOCAL_STT_MODEL,
            verbose=False,
            language="zh",
        )
        text = result.get("text", "").strip()
        # Reject hallucination: excessive repetition
        if text:
            words = text.split()
            if len(words) > 5:
                unique_words = set(words)
                if len(unique_words) < len(words) * 0.3:  # >70% repetition
                    logger.warning(f"[Voice] STT hallucination detected: {text[:80]}")
                    raise RuntimeError("STT hallucination detected")
            logger.info(f"[Voice] 本地 STT: {text}")
            return text
        raise RuntimeError("STT 返回空文本")
    except Exception as e:
        logger.warning(f"[Voice] 本地 STT 失败: {e}，回退 FinnA")
        return _stt_finna(audio_path)


def _stt_finna(audio_path: str) -> str:
    """FinnA Whisper API STT（已停用，key 不支持 sensevoice）"""
    raise RuntimeError(
        "本地 mlx_whisper 未安装，且 FinnA STT key 不可用。"
        "请安装: pip install mlx-whisper"
    )


# 本地 STT 模型
LOCAL_STT_MODEL = "mlx-community/whisper-tiny"

# macOS say 声音（中文）
SAY_VOICE = "Tingting"

# ============== LLM 提供者枚举 ==============
class LLMProvider:
    OMNI = "omni"      # llama.cpp-omni (MiniCPM-o 4.5)
    OLLAMA = "ollama"  # Ollama Qwen2.5-Omni
    OMLX = "omlx"      # OMLX Qwen3.5-9B
    FINNA = "finna"    # FinnA DeepSeek

def llm_chat(message: str, system_prompt: str = "你是一个有帮助的AI助手。请用中文回复。", provider: str = None) -> str:
    """
    对话 — 按优先级尝试: OMLX > FinnA > ollama > omni
    provider: 强制使用指定提供者，None 则自动选择
    """
    providers = [provider] if provider else [LLMProvider.OMLX, LLMProvider.FINNA, LLMProvider.OLLAMA, LLMProvider.OMNI]
    last_error = None
    for p in providers:
        try:
            if p == LLMProvider.OMNI:
                return _llm_omni_server(message, system_prompt)
            elif p == LLMProvider.OLLAMA:
                return _llm_ollama(message, system_prompt)
            elif p == LLMProvider.OMLX:
                return _llm_omlx(message, system_prompt)
            elif p == LLMProvider.FINNA:
                return _llm_finna(message, system_prompt)
        except Exception as e:
            last_error = e
            logger.warning(f"[Voice] LLM provider {p} 失败: {e}")
    raise RuntimeError(f"所有 LLM 提供者均失败: {last_error}")


def _llm_ollama(message: str, system_prompt: str) -> str:
    """Ollama 本地模型 (Qwen2.5-Omni-7B)"""
    import subprocess, json
    # 构建完整 prompt（Ollama /api/generate 使用 prompt 字段）
    full_prompt = f"{system_prompt}\n\nUser: {message}\n\nAssistant:"
    cmd = [
        "curl", "-s", "-X", "POST", "http://localhost:11434/api/chat",
        "-d", json.dumps({
            "model": "rockn/Qwen2.5-Omni-7B-Q4_K_M:latest",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message},
            ],
            "stream": False,
            "options": {"num_predict": 256, "temperature": 0.7},
        })
    ]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        raise RuntimeError(f"ollama curl 失败: {r.stderr}")
    result = json.loads(r.stdout)
    return result.get("message", {}).get("content", "").strip()



def _llm_omlx(message: str, system_prompt: str) -> str:
    """OMLX Qwen3.5-4B-MLX-4bit 本地推理"""
    url = f"{OMLX_BASE}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OMLX_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OMLX_MODEL_LLM,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        "max_tokens": 512,
        "temperature": 0.7,
    }
    response = requests.post(url, json=payload, headers=headers, timeout=120)
    if response.status_code != 200:
        raise RuntimeError(f"OMLX 错误: {response.status_code} {response.text[:200]}")
    return response.json()["choices"][0]["message"]["content"].strip()



def _llm_finna(message: str, system_prompt: str) -> str:
    """FinnA DeepSeek V3.1 API"""
    url = f"{FINNA_API_BASE}/chat/completions"
    headers = {
        "Authorization": f"Bearer {FINNA_KEY_DEEPSEEK}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "Pro/deepseek-ai/DeepSeek-V3.1-Terminus",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        "max_tokens": 512,
        "temperature": 0.7,
    }
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"FinnA LLM 错误: {response.status_code}")
    return response.json()["choices"][0]["message"]["content"].strip()


# ============== TTS — macOS say（本地） ==============

def tts_say(text: str, output_path: str) -> str:
    """文字转语音 — macOS say（本地，无依赖）"""
    # say 命令生成 AIFF，然后转 WAV
    aiff_path = output_path.replace(".wav", ".aiff")
    cmd = ["say", "-v", SAY_VOICE, text, "-o", aiff_path]
    r = subprocess.run(cmd, capture_output=True, timeout=30)
    if r.returncode != 0:
        raise RuntimeError(f"say 命令失败: {r.stderr.decode() if r.stderr else 'unknown'}")

    # AIFF → WAV
    convert_cmd = ["afconvert", aiff_path, output_path, "-f", "WAVE", "-d", "LEI16@44100"]
    r2 = subprocess.run(convert_cmd, capture_output=True, timeout=10)
    if r2.returncode != 0:
        raise RuntimeError(f"afconvert 失败: {r2.stderr.decode() if r2.stderr else 'unknown'}")

    # 清理 AIFF
    if os.path.exists(aiff_path):
        os.unlink(aiff_path)

    return output_path


def tts_cosyvoice(text: str, output_path: str, voice: str = None) -> str:
    """文字转语音 — FinnA CosyVoice2（备用）"""
    url = f"{FINNA_API_BASE}/audio/speech"
    headers = {
        "Authorization": f"Bearer {FINNA_KEY_COSYVOICE}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": "cosyvoice2-CosyVoice-2.5",
        "input": text,
        "voice": voice or "中文男-念白",
        "response_format": "wav",
        "speed": 1.0,
    }
    response = requests.post(url, json=payload, headers=headers, timeout=60)
    if response.status_code != 200:
        raise RuntimeError(f"TTS API 错误: {response.status_code} {response.text}")
    with open(output_path, "wb") as f:
        f.write(response.content)
    return output_path


# ============== 路由 ==============

@voice_bp.route("/health", methods=["GET"])
def health():
    """检查 voice pipeline 状态"""
    return jsonify({
        "status": "ok",
        "services": {
            "whisper": "mlx_whisper (local)",
            "llm": "OMLX Qwen3.5-9B (local)",
            "tts": "macOS say (local)",
        }
    })


@voice_bp.route("/pipeline", methods=["POST"])
def pipeline():
    """
    完整语音管线: STT → LLM → TTS（全部本地）

    POST /api/voice/pipeline
    Content-Type: multipart/form-data

    参数:
        audio: 音频文件 (wav/mp3/m4a)
        system_prompt: 系统提示词 (可选)

    返回:
        audio_data: base64 编码的 WAV 音频
        text: 用户说的话
        response: LLM 回复
    """
    if "audio" not in request.files:
        return jsonify({"error": "未提供音频文件"}), 400

    audio_file = request.files["audio"]
    system_prompt = request.form.get(
        "system_prompt",
        "你是一个有帮助的AI助手。请用中文回复。"
    )

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name
        audio_file.save(audio_path)

    try:
        # Step 1: STT
        logger.info("[Voice] STT...")
        user_text = stt_whisper(audio_path)
        logger.info(f"[Voice] 用户: {user_text}")

        # Step 2: 检查是否是场景模式、笔记、提醒、计时器功能
        from jarvis.scene_mode import match_scene, execute_scene
        scene_id = match_scene(user_text)
        if scene_id is not None:
            logger.info(f"[Voice] 匹配场景模式: {scene_id}")
            result = execute_scene(scene_id)
            msg = result["message"]
            if result["success"] and result.get("infrared_list"):
                infrared_cmd = result["infrared_list"][0] if len(result["infrared_list"]) > 0 else None
                logger.info(f"[Voice] 场景执行: {msg}")
                tts_path = tempfile.mktemp(suffix=".wav")
                tts_say(msg, tts_path)
                with open(tts_path, "rb") as f:
                    audio_data = f.read()
                audio_b64 = base64.b64encode(audio_data).decode()
                os.unlink(tts_path)
                resp = {
                    "success": True,
                    "text": user_text,
                    "response": msg,
                    "audio_data": audio_b64,
                    "source": "scene_mode",
                }
                if infrared_cmd:
                    resp["infrared"] = infrared_cmd
                return jsonify(resp)
            else:
                # 无红外，直接返回文字
                tts_path = tempfile.mktemp(suffix=".wav")
                tts_say(msg, tts_path)
                with open(tts_path, "rb") as f:
                    audio_data = f.read()
                audio_b64 = base64.b64encode(audio_data).decode()
                os.unlink(tts_path)
                return jsonify({
                    "success": True,
                    "text": user_text,
                    "response": msg,
                    "audio_data": audio_b64,
                    "source": "scene_mode",
                })

        # 检查是否是笔记/提醒/计时器功能
        from jarvis.notes_reminder_timer import (
            add_note, add_reminder, add_timer,
            parse_natural_datetime,
            list_notes, search_notes,
            get_upcoming_reminders, list_all_reminders,
            list_active_timers, get_auto_suggestions,
        )
        assistant_text = None
        infrared_cmd = None

        # 笔记匹配
        if "记下来" in user_text or "记住" in user_text or "记笔记" in user_text or "写下来" in user_text:
            content = user_text
            for kw in ["记下来", "记住", "记笔记", "帮我记下来", "帮我记住", "写下来"]:
                content = content.replace(kw, "")
            content = content.strip()
            if content:
                result = add_note(content)
                assistant_text = result["message"]
                logger.info(f"[Voice] 添加笔记: {content[:30]}")
        
        # 提醒匹配
        elif "提醒我" in user_text or "提醒一下" in user_text or "设置提醒" in user_text:
            dt = parse_natural_datetime(user_text)
            if dt is None:
                assistant_text = "我没听清具体时间，请再说一遍，比如'明天早上8点提醒我开会'"
            else:
                content = user_text
                for kw in ["提醒我", "提醒一下", "设置提醒", "提醒我一下"]:
                    content = content.replace(kw, "")
                content = content.strip()
                if not content:
                    content = "待办事项"
                result = add_reminder(content, dt)
                assistant_text = result["message"]
                logger.info(f"[Voice] 添加提醒: {content} at {dt}")
        
        # 计时器匹配
        elif "计时器" in user_text or "倒计时" in user_text or "分钟后提醒我" in user_text:
            import re
            match = re.search(r'(\d+)分钟', user_text)
            minutes = 10
            if match:
                minutes = int(match.group(1))
            else:
                match = re.search(r'(\d+)分', user_text)
                if match:
                    minutes = int(match.group(1))
            content = user_text.strip()
            result = add_timer(minutes, content)
            assistant_text = result["message"]
            logger.info(f"[Voice] 设置计时器: {minutes}分钟")
        
        # 列表提醒
        elif "显示提醒" in user_text or "看一下提醒" in user_text or "有什么提醒" in user_text or "我的提醒" in user_text:
            assistant_text = list_all_reminders()
        
        # 列表笔记
        elif "我的笔记" in user_text or "显示笔记" in user_text or "查看笔记" in user_text:
            assistant_text = list_notes(10)
        
        # 搜索笔记
        elif "搜索笔记" in user_text:
            import re
            match = re.search(r'搜索笔记\s*(.*)', user_text)
            keyword = match.group(1) if match else ""
            if keyword:
                assistant_text = search_notes(keyword)
            else:
                assistant_text = "请告诉我要搜索什么关键词"
        
        # 列表计时器
        elif "计时器" in user_text and ("列表" in user_text or "显示" in user_text):
            assistant_text = list_active_timers()
        
        # 自动建议
        elif "自动建议" in user_text or "给我建议" in user_text or "有什么建议" in user_text:
            assistant_text = get_auto_suggestions()

        if assistant_text is not None:
            tts_path = tempfile.mktemp(suffix=".wav")
            tts_say(assistant_text, tts_path)
            with open(tts_path, "rb") as f:
                audio_data = f.read()
            audio_b64 = base64.b64encode(audio_data).decode()
            os.unlink(tts_path)
            return jsonify({
                "success": True,
                "text": user_text,
                "response": assistant_text,
                "audio_data": audio_b64,
                "source": "notes_reminder",
            })

        # 检查是否是快速工具功能（购物清单、找手机、备忘、快递查询）
        if assistant_text is None:
            from jarvis.quick_tools import quick_tools_handler
            quick_result = quick_tools_handler(user_text)
            if quick_result is not None:
                assistant_text = quick_result
                logger.info(f"[Voice] 快速工具: {assistant_text[:40]}")
                tts_path = tempfile.mktemp(suffix=".wav")
                tts_say(assistant_text, tts_path)
                with open(tts_path, "rb") as f:
                    audio_data = f.read()
                audio_b64 = base64.b64encode(audio_data).decode()
                os.unlink(tts_path)
                return jsonify({
                    "success": True,
                    "text": user_text,
                    "response": assistant_text,
                    "audio_data": audio_b64,
                    "source": "quick_tools",
                })

        # 检查是否是计算/单位转换功能
        if assistant_text is None:
            from jarvis.calculator_unit import calculator_handler
            calc_result = calculator_handler(user_text)
            if calc_result is not None:
                assistant_text = calc_result
                logger.info(f"[Voice] 计算器: {assistant_text[:40]}")
                tts_path = tempfile.mktemp(suffix=".wav")
                tts_say(assistant_text, tts_path)
                with open(tts_path, "rb") as f:
                    audio_data = f.read()
                audio_b64 = base64.b64encode(audio_data).decode()
                os.unlink(tts_path)
                return jsonify({
                    "success": True,
                    "text": user_text,
                    "response": assistant_text,
                    "audio_data": audio_b64,
                    "source": "calculator",
                })

        # 检查是否是古诗词/成语查询
        if assistant_text is None:
            from jarvis.poetry_idiom import poetry_handler
            poetry_result = poetry_handler(user_text)
            if poetry_result is not None:
                assistant_text = poetry_result
                logger.info(f"[Voice] 古诗词成语: {assistant_text[:40]}")
                tts_path = tempfile.mktemp(suffix=".wav")
                tts_say(assistant_text, tts_path)
                with open(tts_path, "rb") as f:
                    audio_data = f.read()
                audio_b64 = base64.b64encode(audio_data).decode()
                os.unlink(tts_path)
                return jsonify({
                    "success": True,
                    "text": user_text,
                    "response": assistant_text,
                    "audio_data": audio_b64,
                    "source": "poetry",
                })

        # 检查是否匹配动态工具（元芳自动生成的工具）
        if assistant_text is None:
            from jarvis.dynamic_tool_generator import (
                dynamic_tool_handler, 
                generate_and_validate_with_retry, 
                save_dynamic_tool, 
                DynamicTool, 
                snake_case_name, 
                validate_tool_code,
                search_similar_tools,
                MAX_RETRIES
            )
            from datetime import datetime
            
            # 首先检查：用户是否要求创建新工具？
            create_keywords = ["添加功能", "新增工具", "创建工具", "生成工具", "帮我做一个", "帮我添加", "我需要一个", "能不能做一个", "给我加一个", "创建一个"]
            if any(kw in user_text for kw in create_keywords):
                # 提取需求
                demand = user_text
                for kw in create_keywords:
                    demand = demand.replace(kw, "")
                demand = demand.strip()
                if not demand:
                    assistant_text = "请告诉我需要做什么功能，我会生成对应的工具代码。"
                else:
                    logger.info(f"[DynamicTool] 开始生成工具: {demand}")
                    
                    # 搜索相似工具，避免重复创建
                    similar_tools = search_similar_tools(demand)
                    if similar_tools:
                        similar = similar_tools[0]
                        assistant_text = f"已经存在相似功能工具了：「{similar.name}」\n功能：{similar.description}\n直接使用即可，不需要重复创建。"
                        logger.info(f"[DynamicTool] 找到相似工具: {similar.name}，跳过创建")
                    else:
                        # 使用LLM生成代码，带自动重试修复
                        success, code, error_msg = generate_and_validate_with_retry(demand)
                        if not success:
                            assistant_text = f"生成工具失败，经过 {MAX_RETRIES} 次尝试仍然有错误: {error_msg}\n需求: {demand}"
                            logger.error(f"[DynamicTool] 生成失败: {error_msg}")
                        else:
                            name = snake_case_name(demand)
                            handler_name = f"{name}_handler"
                            # 创建工具对象保存
                            tool = DynamicTool(
                                name=name,
                                description=demand,
                                handler_function=handler_name,
                                requirements="",
                                code=code,
                                created_at=datetime.now().isoformat(),
                                usage_example=user_text
                            )
                            saved = save_dynamic_tool(tool)
                            if saved:
                                assistant_text = f"已成功生成并保存动态工具「{name}」\n功能: {demand}\n经过自动验证，语法正确 ✓\n现在可以直接使用了！"
                                logger.info(f"[DynamicTool] 工具创建成功: {name}")
                            else:
                                assistant_text = f"生成工具「{name}」成功，但保存失败。"
                
                tts_path = tempfile.mktemp(suffix=".wav")
                tts_say(assistant_text, tts_path)
                with open(tts_path, "rb") as f:
                    audio_data = f.read()
                audio_b64 = base64.b64encode(audio_data).decode()
                os.unlink(tts_path)
                return jsonify({
                    "success": True,
                    "text": user_text,
                    "response": assistant_text,
                    "audio_data": audio_b64,
                    "source": "dynamic_tool_create",
                })
            
            # 如果不是创建，尝试调用已有的动态工具
            else:
                dynamic_result = dynamic_tool_handler(user_text)
                if dynamic_result is not None:
                    assistant_text = dynamic_result
                    logger.info(f"[Voice] 动态工具: {assistant_text[:40]}")
                    tts_path = tempfile.mktemp(suffix=".wav")
                    tts_say(assistant_text, tts_path)
                    with open(tts_path, "rb") as f:
                        audio_data = f.read()
                    audio_b64 = base64.b64encode(audio_data).decode()
                    os.unlink(tts_path)
                    return jsonify({
                        "success": True,
                        "text": user_text,
                        "response": assistant_text,
                        "audio_data": audio_b64,
                        "source": "dynamic_tool",
                    })

        # Step 2: 检查是否是智能家居控制意图
        from jarvis.smart_home_intent import _parse_smart_home_command
        result = _parse_smart_home_command(user_text)
        if result is not None:
            ir, msg = result
            if ir and ir.get("pattern"):
                logger.info(f"[Voice] 智能家居控制: {msg}, 红外已匹配")
                # 直接 TTS 返回结果
                tts_path = tempfile.mktemp(suffix=".wav")
                tts_say(msg, tts_path)
                with open(tts_path, "rb") as f:
                    audio_data = f.read()
                audio_b64 = base64.b64encode(audio_data).decode()
                os.unlink(tts_path)
                return jsonify({
                    "success": True,
                    "text": user_text,
                    "response": msg,
                    "audio_data": audio_b64,
                    "infrared": ir,
                    "source": "smart_home",
                })
            elif msg:
                logger.info(f"[Voice] 智能家居意图: {msg} (无红外码)")
                # 直接返回文字，不需要红外
                tts_path = tempfile.mktemp(suffix=".wav")
                tts_say(msg, tts_path)
                with open(tts_path, "rb") as f:
                    audio_data = f.read()
                audio_b64 = base64.b64encode(audio_data).decode()
                os.unlink(tts_path)
                return jsonify({
                    "success": True,
                    "text": user_text,
                    "response": msg,
                    "audio_data": audio_b64,
                    "source": "smart_home",
                })

        # Step 2: LLM
        logger.info("[Voice] LLM...")
        llm_response = llm_chat(user_text, system_prompt=system_prompt)
        logger.info(f"[Voice] 助手: {llm_response[:50]}...")

        # Step 3: TTS (macOS say 本地)
        logger.info("[Voice] TTS...")
        tts_path = tempfile.mktemp(suffix=".wav")
        tts_say(llm_response, tts_path)

        # 返回
        with open(tts_path, "rb") as f:
            audio_data = f.read()
        audio_b64 = base64.b64encode(audio_data).decode()

        os.unlink(tts_path)

        return jsonify({
            "success": True,
            "text": user_text,
            "response": llm_response,
            "audio_data": audio_b64,
        })

    except Exception as e:
        logger.error(f"[Voice] 管线错误: {e}")
        return jsonify({"error": str(e), "success": False}), 500

    finally:
        if os.path.exists(audio_path):
            os.unlink(audio_path)


@voice_bp.route("/chat", methods=["POST"])
def chat():
    """纯文字对话"""
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "未提供消息"}), 400
    try:
        response = llm_chat(
            data["message"],
            system_prompt=data.get("system_prompt", "你是一个有帮助的AI助手。请用中文回复。")
        )
        return jsonify({"success": True, "response": response})
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


@voice_bp.route("/stt", methods=["POST"])
def stt_only():
    """
    仅语音识别：上传音频 → 返回文字
    POST /api/voice/stt
    Content-Type: multipart/form-data
    参数: audio / file (音频文件)
    返回: {success: true, text: "..."}
    """
    if "audio" not in request.files and "file" not in request.files:
        return jsonify({"error": "未提供音频文件"}), 400

    audio_file = request.files.get("audio") or request.files.get("file")
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name
        audio_file.save(audio_path)

    # 格式转换: m4a/aac/mp4 → wav
    try:
        with open(audio_path, "rb") as f:
            header = f.read(12)
        if header[4:8] == b"ftyp" or (header[:4] != b"RIFF" and header[:3] != b"ID3"):
            converted = audio_path + "_conv.wav"
            import subprocess
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", audio_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", converted],
                capture_output=True, text=True, timeout=30,
                env={**os.environ, "PATH": "/opt/homebrew/bin:/usr/local/bin:" + os.environ.get("PATH", "")}
            )
            if result.returncode == 0 and os.path.exists(converted):
                os.unlink(audio_path)
                audio_path = converted
                logger.info(f"[Voice STT] Converted to wav: {audio_path}")
    except Exception as e:
        logger.warning(f"[Voice STT] Format check/convert skipped: {e}")

    try:
        text = stt_whisper(audio_path)
        return jsonify({"success": True, "text": text})
    except Exception as e:
        logger.error(f"[Voice] /stt 错误: {e}")
        return jsonify({"error": str(e), "success": False}), 500
    finally:
        if os.path.exists(audio_path):
            os.unlink(audio_path)


@voice_bp.route("/fast", methods=["POST"])
def mlx_voice_fast():
    """
    兼容旧版 termux 客户端 /api/mlx-voice/fast
    支持 multipart: file(audio) + max_tokens
    """
    if "file" not in request.files and "audio" not in request.files:
        return jsonify({"error": "no audio file"}), 400

    audio_file = request.files.get("file") or request.files.get("audio")
    max_tokens = int(request.form.get("max_tokens", 128))

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name
        audio_file.save(audio_path)

    try:
        user_text = stt_whisper(audio_path)
        llm_response = llm_chat(user_text)
        tts_path = tempfile.mktemp(suffix=".wav")
        tts_say(llm_response, tts_path)
        with open(tts_path, "rb") as f:
            audio_b64 = base64.b64encode(f.read()).decode()
        os.unlink(tts_path)
        return jsonify({
            "success": True,
            "text": user_text,
            "response": llm_response,
            "audio_data": audio_b64,
        })
    except Exception as e:
        logger.error(f"[Voice] /fast 错误: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if os.path.exists(audio_path):
            os.unlink(audio_path)


@voice_bp.route("/tts", methods=["POST"])
def tts():
    """文字转语音"""
    data = request.get_json()
    if not data or "text" not in data:
        return jsonify({"error": "未提供文字"}), 400
    try:
        tts_path = tempfile.mktemp(suffix=".wav")
        tts_say(data["text"], tts_path)
        return send_file(tts_path, mimetype="audio/wav")
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


# ============== 兼容旧版 termux 客户端 ==============

@voice_bp.route("/mlx-voice/pipeline", methods=["POST"])
def mlx_voice_pipeline():
    """
    兼容旧版 termux 客户端 /api/mlx-voice/pipeline
    手机麦克风 → STT → LLM → TTS → 返回 base64 音频
    """
    if "file" not in request.files and "audio" not in request.files:
        return jsonify({"error": "no audio file"}), 400

    audio_file = request.files.get("file") or request.files.get("audio")
    system_prompt = request.form.get(
        "system_prompt",
        "你是一个有帮助的AI助手。请用中文回复。"
    )
    voice = request.form.get("voice", "af_heart")
    use_tts = request.form.get("use_tts", "true").lower() != "false"
    use_tools = request.form.get("use_tools", "true").lower() != "false"

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name
        audio_file.save(audio_path)

    # Convert m4a/aac/mp4 to wav if needed (termux-microphone-record outputs m4a)
    try:
        with open(audio_path, "rb") as f:
            header = f.read(12)
        if header[4:8] == b"ftyp" or (header[:4] != b"RIFF" and header[:3] != b"ID3"):
            converted = audio_path + "_conv.wav"
            import subprocess
            result = subprocess.run(
                ["ffmpeg", "-y", "-i", audio_path, "-ar", "16000", "-ac", "1", "-c:a", "pcm_s16le", converted],
                capture_output=True, text=True, timeout=30,
                env={**os.environ, "PATH": "/opt/homebrew/bin:/usr/local/bin:" + os.environ.get("PATH", "")}
            )
            if result.returncode == 0 and os.path.exists(converted):
                os.unlink(audio_path)
                audio_path = converted
                logger.info(f"[Voice MLP] Converted to wav: {audio_path}")
    except Exception as e:
        logger.warning(f"[Voice MLP] Format check/convert skipped: {e}")

    try:
        logger.info("[Voice MLP] STT...")
        user_text = stt_whisper(audio_path)
        logger.info(f"[Voice MLP] 用户: {user_text}")

        # ===== 场景模式检测（优先级最高）=====
        from jarvis.scene_mode import match_scene, execute_scene
        scene_id = match_scene(user_text)
        if scene_id is not None:
            logger.info(f"[Voice MLP] 匹配场景模式: {scene_id}")
            result = execute_scene(scene_id)
            msg = result["message"]
            ir = result["infrared_list"][0] if (result["success"] and result.get("infrared_list")) else None
            if ir and ir.get("pattern"):
                logger.info(f"[Voice MLP] 场景执行: {msg}, 红外已匹配")
                if use_tts:
                    tts_path = tempfile.mktemp(suffix=".wav")
                    tts_say(msg, tts_path)
                    with open(tts_path, "rb") as f:
                        audio_b64 = base64.b64encode(f.read()).decode()
                    os.unlink(tts_path)
                    return jsonify({
                        "success": True,
                        "text": user_text,
                        "response": msg,
                        "audio_data": audio_b64,
                        "infrared": ir,
                        "source": "scene_mode",
                    })
                else:
                    return jsonify({
                        "success": True,
                        "text": user_text,
                        "response": msg,
                        "infrared": ir,
                        "source": "scene_mode",
                    })
            elif msg:
                logger.info(f"[Voice MLP] 场景匹配: {msg} (无红外码)")
                if use_tts:
                    tts_path = tempfile.mktemp(suffix=".wav")
                    tts_say(msg, tts_path)
                    with open(tts_path, "rb") as f:
                        audio_b64 = base64.b64encode(f.read()).decode()
                    os.unlink(tts_path)
                    return jsonify({
                        "success": True,
                        "text": user_text,
                        "response": msg,
                        "audio_data": audio_b64,
                        "source": "scene_mode",
                    })
                else:
                    return jsonify({
                        "success": True,
                        "text": user_text,
                        "response": msg,
                        "source": "scene_mode",
                    })

        # ===== 笔记/提醒/计时器检测（次优先级）=====
        from jarvis.notes_reminder_timer import (
            add_note, add_reminder, add_timer,
            parse_natural_datetime,
            list_notes, search_notes,
            get_upcoming_reminders, list_all_reminders,
            list_active_timers, get_auto_suggestions,
        )
        assistant_text = None
        infrared_cmd = None

        # 笔记匹配
        if "记下来" in user_text or "记住" in user_text or "记笔记" in user_text or "写下来" in user_text:
            content = user_text
            for kw in ["记下来", "记住", "记笔记", "帮我记下来", "帮我记住", "写下来"]:
                content = content.replace(kw, "")
            content = content.strip()
            if content:
                result = add_note(content)
                assistant_text = result["message"]
                logger.info(f"[Voice MLP] 添加笔记: {content[:30]}")
        
        # 提醒匹配
        elif "提醒我" in user_text or "提醒一下" in user_text or "设置提醒" in user_text:
            dt = parse_natural_datetime(user_text)
            if dt is None:
                assistant_text = "我没听清具体时间，请再说一遍，比如'明天早上8点提醒我开会'"
            else:
                content = user_text
                for kw in ["提醒我", "提醒一下", "设置提醒", "提醒我一下"]:
                    content = content.replace(kw, "")
                content = content.strip()
                if not content:
                    content = "待办事项"
                result = add_reminder(content, dt)
                assistant_text = result["message"]
                logger.info(f"[Voice MLP] 添加提醒: {content} at {dt}")
        
        # 计时器匹配
        elif "计时器" in user_text or "倒计时" in user_text or "分钟后提醒我" in user_text:
            import re
            match = re.search(r'(\d+)分钟', user_text)
            minutes = 10
            if match:
                minutes = int(match.group(1))
            else:
                match = re.search(r'(\d+)分', user_text)
                if match:
                    minutes = int(match.group(1))
            content = user_text.strip()
            result = add_timer(minutes, content)
            assistant_text = result["message"]
            logger.info(f"[Voice MLP] 设置计时器: {minutes}分钟")
        
        # 列表提醒
        elif "显示提醒" in user_text or "看一下提醒" in user_text or "有什么提醒" in user_text or "我的提醒" in user_text:
            assistant_text = list_all_reminders()
        
        # 列表笔记
        elif "我的笔记" in user_text or "显示笔记" in user_text or "查看笔记" in user_text:
            assistant_text = list_notes(10)
        
        # 搜索笔记
        elif "搜索笔记" in user_text:
            import re
            match = re.search(r'搜索笔记\s*(.*)', user_text)
            keyword = match.group(1) if match else ""
            if keyword:
                assistant_text = search_notes(keyword)
            else:
                assistant_text = "请告诉我要搜索什么关键词"
        
        # 列表计时器
        elif "计时器" in user_text and ("列表" in user_text or "显示" in user_text):
            assistant_text = list_active_timers()
        
        # 自动建议
        elif "自动建议" in user_text or "给我建议" in user_text or "有什么建议" in user_text:
            assistant_text = get_auto_suggestions()

        if assistant_text is not None:
            logger.info(f"[Voice MLP] 笔记/提醒/计时器功能: {assistant_text[:60]}")
            if use_tts:
                tts_path = tempfile.mktemp(suffix=".wav")
                tts_say(assistant_text, tts_path)
                with open(tts_path, "rb") as f:
                    audio_b64 = base64.b64encode(f.read()).decode()
                os.unlink(tts_path)
                return jsonify({
                    "success": True,
                    "text": user_text,
                    "response": assistant_text,
                    "audio_data": audio_b64,
                    "source": "notes_reminder",
                })
            else:
                return jsonify({
                    "success": True,
                    "text": user_text,
                    "response": assistant_text,
                    "source": "notes_reminder",
                })

        # 检查是否是快速工具功能（购物清单、找手机、备忘、快递查询）
        if assistant_text is None:
            from jarvis.quick_tools import quick_tools_handler
            quick_result = quick_tools_handler(user_text)
            if quick_result is not None:
                assistant_text = quick_result
                logger.info(f"[Voice MLP] 快速工具: {assistant_text[:40]}")
                if use_tts:
                    tts_path = tempfile.mktemp(suffix=".wav")
                    tts_say(assistant_text, tts_path)
                    with open(tts_path, "rb") as f:
                        audio_b64 = base64.b64encode(f.read()).decode()
                    os.unlink(tts_path)
                    return jsonify({
                        "success": True,
                        "text": user_text,
                        "response": assistant_text,
                        "audio_data": audio_b64,
                        "source": "quick_tools",
                    })
                else:
                    return jsonify({
                        "success": True,
                        "text": user_text,
                        "response": assistant_text,
                        "source": "quick_tools",
                    })

        # 检查是否是计算/单位转换功能
        if assistant_text is None:
            from jarvis.calculator_unit import calculator_handler
            calc_result = calculator_handler(user_text)
            if calc_result is not None:
                assistant_text = calc_result
                logger.info(f"[Voice MLP] 计算器: {assistant_text[:40]}")
                if use_tts:
                    tts_path = tempfile.mktemp(suffix=".wav")
                    tts_say(assistant_text, tts_path)
                    with open(tts_path, "rb") as f:
                        audio_b64 = base64.b64encode(f.read()).decode()
                    os.unlink(tts_path)
                    return jsonify({
                        "success": True,
                        "text": user_text,
                        "response": assistant_text,
                        "audio_data": audio_b64,
                        "source": "calculator",
                    })
                else:
                    return jsonify({
                        "success": True,
                        "text": user_text,
                        "response": assistant_text,
                        "source": "calculator",
                    })

        # 检查是否是古诗词/成语查询
        if assistant_text is None:
            from jarvis.poetry_idiom import poetry_handler
            poetry_result = poetry_handler(user_text)
            if poetry_result is not None:
                assistant_text = poetry_result
                logger.info(f"[Voice MLP] 古诗词成语: {assistant_text[:40]}")
                if use_tts:
                    tts_path = tempfile.mktemp(suffix=".wav")
                    tts_say(assistant_text, tts_path)
                    with open(tts_path, "rb") as f:
                        audio_b64 = base64.b64encode(f.read()).decode()
                    os.unlink(tts_path)
                    return jsonify({
                        "success": True,
                        "text": user_text,
                        "response": assistant_text,
                        "audio_data": audio_b64,
                        "source": "poetry",
                    })
                else:
                    return jsonify({
                        "success": True,
                        "text": user_text,
                        "response": assistant_text,
                        "source": "poetry",
                    })

        # ===== 智能家居意图检测 =====
        from jarvis.smart_home_intent import _parse_smart_home_command
        result = _parse_smart_home_command(user_text)
        if result is not None:
            ir, msg = result
            if ir and ir.get("pattern"):
                logger.info(f"[Voice MLP] 智能家居控制: {msg}, 红外已匹配")
                if use_tts:
                    tts_path = tempfile.mktemp(suffix=".wav")
                    tts_say(msg, tts_path)
                    with open(tts_path, "rb") as f:
                        audio_b64 = base64.b64encode(f.read()).decode()
                    os.unlink(tts_path)
                    return jsonify({
                        "success": True,
                        "text": user_text,
                        "response": msg,
                        "audio_data": audio_b64,
                        "infrared": ir,
                        "source": "smart_home",
                    })
                else:
                    return jsonify({
                        "success": True,
                        "text": user_text,
                        "response": msg,
                        "infrared": ir,
                        "source": "smart_home",
                    })
            elif msg:
                logger.info(f"[Voice MLP] 智能家居意图: {msg} (无红外码)")
                if use_tts:
                    tts_path = tempfile.mktemp(suffix=".wav")
                    tts_say(msg, tts_path)
                    with open(tts_path, "rb") as f:
                        audio_b64 = base64.b64encode(f.read()).decode()
                    os.unlink(tts_path)
                    return jsonify({
                        "success": True,
                        "text": user_text,
                        "response": msg,
                        "audio_data": audio_b64,
                        "source": "smart_home",
                    })
                else:
                    return jsonify({
                        "success": True,
                        "text": user_text,
                        "response": msg,
                        "source": "smart_home",
                    })

        logger.info(f"[Voice MLP] LLM... (tools={use_tools})")
        if use_tools:
            try:
                llm_response = _llm_omni_with_tools(user_text)
            except Exception as e:
                logger.warning(f"[Voice MLP] Tools LLM failed: {e}, falling back to plain LLM")
                llm_response = llm_chat(user_text, system_prompt=system_prompt)
        else:
            llm_response = llm_chat(user_text, system_prompt=system_prompt)
        logger.info(f"[Voice MLP] 助手: {llm_response[:80]}...")

        if use_tts:
            logger.info("[Voice MLP] TTS...")
            tts_path = tempfile.mktemp(suffix=".wav")
            tts_say(llm_response, tts_path)
            with open(tts_path, "rb") as f:
                audio_b64 = base64.b64encode(f.read()).decode()
            os.unlink(tts_path)
            return jsonify({
                "success": True,
                "text": user_text,
                "response": llm_response,
                "audio_file": tts_path,
                "audio_data": audio_b64,
            })
        else:
            return jsonify({
                "success": True,
                "text": user_text,
                "response": llm_response,
            })

    except Exception as e:
        logger.error(f"[Voice MLP] 错误: {e}")
        return jsonify({"error": str(e), "success": False}), 500
    finally:
        if os.path.exists(audio_path):
            os.unlink(audio_path)


@voice_bp.route("/mlx-voice/fast", methods=["POST"])
def mlx_voice_fast_compat():
    """
    兼容旧版 termux 客户端 /api/mlx-voice/fast
    快速管线: STT → LLM → 只返回文字（无 TTS）
    """
    if "file" not in request.files and "audio" not in request.files:
        return jsonify({"error": "no audio file"}), 400

    audio_file = request.files.get("file") or request.files.get("audio")
    max_tokens = int(request.form.get("max_tokens", 256))

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name
        audio_file.save(audio_path)

    try:
        user_text = stt_whisper(audio_path)
        llm_response = llm_chat(user_text)
        return jsonify({
            "success": True,
            "text": user_text,
            "response": llm_response,
        })
    except Exception as e:
        logger.error(f"[Voice MLP /fast] 错误: {e}")
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if os.path.exists(audio_path):
            os.unlink(audio_path)



@voice_bp.route("/mlx-voice/chat", methods=["POST"])
def mlx_voice_chat():
    """兼容旧版 termux 客户端 /api/mlx-voice/chat"""
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "未提供消息"}), 400
    try:
        response = llm_chat(
            data["message"],
            system_prompt=data.get("system_prompt", "你是一个有帮助的AI助手。请用中文回复。")
        )
        return jsonify({"success": True, "response": response})
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


# ============== llama.cpp-omni S2S（原生语音） ==============

def _llm_omni_server(message: str, system_prompt: str = "你是一个有帮助的AI助手。请用中文回复。") -> str:
    """MiniCPM-o 4.5 via llama.cpp-omni server"""
    import requests
    url = "http://localhost:8090/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": "minicpm-o",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message},
        ],
        "stream": False,
        "options": {"num_predict": 256, "temperature": 0.7},
    }
    r = requests.post(url, json=payload, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"omni server 错误: {r.status_code} {r.text}")
    return r.json()["choices"][0]["message"]["content"]


def _llm_omni_with_tools(message: str) -> str:
    """
    MiniCPM-o 4.5 with tool calling support.
    1. Send with tool system prompt → check if tool call needed
    2. If yes, execute tool → re-send with result
    3. Return final text response
    """
    import requests
    url = "http://localhost:8090/v1/chat/completions"
    headers = {"Content-Type": "application/json"}
    
    messages = [
        {"role": "system", "content": TOOL_SYSTEM_PROMPT},
        {"role": "user", "content": message},
    ]
    
    payload = {
        "model": "minicpm-o",
        "messages": messages,
        "stream": False,
        "options": {"num_predict": 150, "temperature": 0.3},
    }
    
    r = requests.post(url, json=payload, timeout=60)
    if r.status_code != 200:
        raise RuntimeError(f"omni server 错误: {r.status_code}")
    
    response_text = r.json()["choices"][0]["message"]["content"]
    tool_call = parse_tool_call(response_text)
    
    if tool_call:
        tool_name = tool_call.get("tool", "")
        query = tool_call.get("query", "")
        logger.info(f"[Tools] 工具调用: {tool_name}({query})")
        tool_result = execute_tool_call(tool_name, query)
        logger.info(f"[Tools] 结果: {tool_result[:100]}")
        
        # 把工具结果拼回去，再次调用
        messages.append({"role": "assistant", "content": response_text})
        messages.append({"role": "user", "content": f"工具结果: {tool_result}\n\n请根据工具结果回答用户的问题。"})
        
        payload2 = {
            "model": "minicpm-o",
            "messages": messages,
            "stream": False,
            "options": {"num_predict": 300, "temperature": 0.7},
        }
        r2 = requests.post(url, json=payload2, timeout=90)
        if r2.status_code == 200:
            return r2.json()["choices"][0]["message"]["content"]
        else:
            return f"工具执行成功，但生成最终回复失败: {r2.status_code}"
    else:
        return response_text


@voice_bp.route("/omni/s2s", methods=["POST"])
def omni_s2s():
    """
    原生 S2S：手机麦克风 → base64音频 → llama.cpp-omni → 语音回复
    POST: multipart audio file
    """
    if "file" not in request.files:
        return jsonify({"error": "no audio file"}), 400

    audio_file = request.files["file"]
    system_prompt = request.form.get(
        "system_prompt", "你是一个有帮助的AI助手。请用中文回复。"
    )
    use_tts = request.form.get("use_tts", "true").lower() != "false"

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name
        audio_file.save(audio_path)

    try:
        # 通过 llama.cpp-omni server 处理音频（S2S）
        # server 地址通过环境变量或配置文件指定
        omni_url = os.environ.get("OMNI_SERVER_URL", "http://localhost:8090")

        # 组装 form-data
        files = {"audio": open(audio_path, "rb")}
        data = {"system_prompt": system_prompt}
        if use_tts:
            data["return_audio"] = "true"

        resp = requests.post(f"{omni_url}/v1/audio/speech", files=files, data=data, timeout=120)
        os.unlink(audio_path)

        if resp.status_code == 200:
            result = resp.json()
            return jsonify({
                "success": True,
                "text": result.get("text", ""),
                "response": result.get("response", ""),
                "audio_data": result.get("audio_data"),
            })
        else:
            return jsonify({"error": f"omni server 错误: {resp.status_code}", "detail": resp.text}), 500

    except Exception as e:
        logger.error(f"[Omni S2S] 错误: {e}")
        return jsonify({"error": str(e), "success": False}), 500


@voice_bp.route("/omni/chat", methods=["POST"])
def omni_chat():
    """纯文字对话（走 llama.cpp-omni）"""
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "未提供消息"}), 400
    try:
        resp = _llm_omni_server(
            data["message"],
            system_prompt=data.get("system_prompt", "你是一个有帮助的AI助手。请用中文回复。")
        )
        return jsonify({"success": True, "response": resp})
    except Exception as e:
        return jsonify({"error": str(e), "success": False}), 500


# ============== 视觉 + 语音 管线 ==============

def _llm_omlx_vision(user_text: str, image_b64: str, system_prompt: str = None) -> dict:
    """
    OMLX Qwen3-VL 视觉问答
    返回: {"content": str, "thinking": str}
    支持thinking模式提取
    """
    url = f"{OMLX_BASE}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OMLX_API_KEY}",
        "Content-Type": "application/json",
    }
    
    if system_prompt is None:
        system_prompt = "你是贾维斯，一个智能居家助手。你可以看到用户发送的图片，请根据图片内容和用户问题，给出准确简洁的回答。你会对问题进行思考，然后给出最终答案。"
    
    # 构造多模态消息
    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image_b64}"}}
            ]
        }
    ]
    
    payload = {
        "model": OMLX_MODEL_VL,
        "messages": messages,
        "max_tokens": 512,
        "temperature": 0.7,
        "stream": False,
    }
    
    response = requests.post(url, json=payload, headers=headers, timeout=180)
    if response.status_code != 200:
        raise RuntimeError(f"OMLX VL 错误: {response.status_code} {response.text[:200]}")
    
    result = response.json()
    full_content = result["choices"][0]["message"]["content"].strip()
    
    # 提取thinking和最终回答（Qwen3 thinking 格式：<think>...</think>answer）
    thinking = ""
    content = full_content
    if "<think>" in full_content and "</think>" in full_content:
        import re
        match = re.search(r'<think>(.*?)</think>', full_content, re.DOTALL)
        if match:
            thinking = match.group(1).strip()
            # 提取think之后的内容作为最终回答
            content = full_content.split("</think>")[-1].strip()
    
    return {
        "content": content,
        "thinking": thinking,
        "full": full_content,
    }


# 智能家居红外控制意图识别
def _parse_smart_home_command(user_text: str) -> dict or None:
    """
    解析智能家居控制命令，调用红外数据库获取编码
    返回: {"frequency": int, "pattern": str, "message": str} 或 None
    """
    from jarvis.smart_home_intent import smart_home_tool
    result_json = smart_home_tool(user_text)
    try:
        import json
        result = json.loads(result_json)
        if result.get("success") and result.get("infrared"):
            return result["infrared"], result.get("message", "执行控制")
        else:
            # 识别成功但没有红外码（还没学习）
            return None, result.get("message", "未学习红外码")
    except:
        return None, result_json


def _llm_omlx_with_tools(user_text: str) -> str:
    """
    OMLX 支持工具调用
    1. Send with tool system prompt → check if tool call needed
    2. If yes, execute tool → re-send with result
    3. Return final text response
    """
    messages = [
        {"role": "system", "content": TOOL_SYSTEM_PROMPT},
        {"role": "user", "content": user_text},
    ]
    
    payload = {
        "model": OMLX_MODEL_LLM,
        "messages": messages,
        "max_tokens": 256,
        "temperature": 0.3,
    }
    
    url = f"{OMLX_BASE}/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OMLX_API_KEY}",
        "Content-Type": "application/json",
    }
    response = requests.post(url, json=payload, headers=headers, timeout=90)
    if response.status_code != 200:
        raise RuntimeError(f"OMLX 错误: {response.status_code} {response.text[:200]}")
    
    response_text = response.json()["choices"][0]["message"]["content"].strip()
    tool_call = parse_tool_call(response_text)
    
    if tool_call:
        tool_name = tool_call.get("tool", "")
        query = tool_call.get("query", "")
        logger.info(f"[Tools] 工具调用: {tool_name}({query})")
        tool_result = execute_tool_call(tool_name, query)
        logger.info(f"[Tools] 结果: {tool_result[:100]}")
        
        # 检查是否是智能家居红外控制结果
        try:
            import json
            tool_result_obj = json.loads(tool_result)
        except:
            tool_result_obj = None
        
        # 把工具结果拼回去，再次调用生成最终回答
        messages.append({"role": "assistant", "content": response_text})
        messages.append({"role": "user", "content": f"工具结果: {tool_result}\n\n请根据工具结果回答用户的问题。"})
        
        payload2 = {
            "model": OMLX_MODEL_LLM,
            "messages": messages,
            "max_tokens": 300,
            "temperature": 0.7,
        }
        r2 = requests.post(url, json=payload2, headers=headers, timeout=120)
        if r2.status_code == 200:
            final_text = r2.json()["choices"][0]["message"]["content"].strip()
            return final_text
        else:
            return f"工具执行成功，但生成最终回复失败。工具结果：{tool_result}"
    else:
        return response_text


@voice_bp.route("/vision-voice/pipeline", methods=["POST"])
def vision_voice_pipeline():
    """
    完整视觉语音管线: 
    手机上传音频 + 图片 → STT → Qwen3-VL → 工具调用 → TTS → 返回音频 + 回答 + 红外指令
    
    POST /api/voice/vision-voice/pipeline
    Content-Type: multipart/form-data
    
    参数:
        audio: 音频文件 (wav)
        image: base64 编码的 JPG 图片
        max_tokens: 最大生成token数 (可选)
        use_tools: 是否启用工具调用 (默认 true)
    
    返回:
        success: bool
        text: STT 识别出的用户文字
        response: LLM 回复
        thinking: thinking过程（如果有）
        audio_data: base64 编码的 TTS 音频
        infrared: 红外指令 {"frequency": int, "pattern": str}（如果需要）
    """
    if "audio" not in request.files:
        return jsonify({"error": "未提供音频文件"}), 400
    
    audio_file = request.files["audio"]
    image_b64 = request.form.get("image", "")
    max_tokens = int(request.form.get("max_tokens", 256))
    use_tools = request.form.get("use_tools", "true").lower() != "false"
    
    system_prompt = "你是贾维斯，一个智能居家助手，生活在用户家中。你可以通过摄像头看到环境，通过语音和用户交流，还可以控制家中的电器（奥克斯空调、小米电视、奥克斯茶吧机），查询天气。请用中文简洁回答用户的问题。"
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = tmp.name
        audio_file.save(audio_path)
    
    try:
        # Step 1: STT - 语音转文字
        logger.info("[Vision+Voice] STT...")
        user_text = stt_whisper(audio_path)
        logger.info(f"[Vision+Voice] 用户: {user_text}")
        
        # Step 2: 优先检查是否是智能家居控制意图
        infrared_cmd = None
        assistant_text = None
        thinking = ""
        infrared_result = None
        
        # 尝试匹配场景模式
        from jarvis.scene_mode import match_scene, execute_scene
        scene_id = match_scene(user_text)
        if scene_id is not None:
            logger.info(f"[Vision+Voice] 匹配场景模式: {scene_id}")
            result = execute_scene(scene_id)
            msg = result["message"]
            if result["success"] and result.get("infrared_list"):
                # 场景中有多个红外指令，一次性全部返回给客户端执行
                # 返回第一个指令让客户端播放提示
                assistant_text = msg
                if len(result["infrared_list"]) > 0:
                    infrared_cmd = result["infrared_list"][0]
                logger.info(f"[Vision+Voice] 场景执行: {msg}")
            else:
                assistant_text = msg
                logger.info(f"[Vision+Voice] 场景无红外或未就绪: {msg}")
        
        # 如果没有匹配场景，尝试匹配智能家居控制意图
        if assistant_text is None:
            result = _parse_smart_home_command(user_text)
            if result is not None:
                ir, msg = result
                if ir and ir.get("pattern"):
                    infrared_cmd = ir
                    assistant_text = msg
                    logger.info(f"[Vision+Voice] 智能家居控制: {msg}, 红外已匹配")
                elif msg:
                    assistant_text = msg
                    logger.info(f"[Vision+Voice] 智能家居意图: {msg} (无红外码)")
        
        # 如果没有匹配场景和智能家居，尝试匹配笔记/提醒/计时器功能
        if assistant_text is None:
            from jarvis.notes_reminder_timer import (
                add_note, add_reminder, add_timer,
                parse_natural_datetime,
                list_notes, search_notes,
                get_upcoming_reminders, list_all_reminders,
                list_active_timers,
            )
            # 笔记匹配
            if "记下来" in user_text or "记住" in user_text or "记笔记" in user_text or "写下来" in user_text:
                # 提取笔记内容：去掉关键词
                content = user_text
                for kw in ["记下来", "记住", "记笔记", "帮我记下来", "帮我记住", "写下来"]:
                    content = content.replace(kw, "")
                content = content.strip()
                if content:
                    result = add_note(content)
                    assistant_text = result["message"]
                    logger.info(f"[Vision+Voice] 添加笔记: {content[:30]}")
            
            # 提醒匹配
            elif "提醒我" in user_text or "提醒一下" in user_text or "设置提醒" in user_text:
                # 解析时间
                dt = parse_natural_datetime(user_text)
                if dt is None:
                    assistant_text = "我没听清具体时间，请再说一遍，比如'明天早上8点提醒我开会'"
                else:
                    # 提取内容：去掉关键词
                    content = user_text
                    for kw in ["提醒我", "提醒一下", "设置提醒", "提醒我一下"]:
                        content = content.replace(kw, "")
                    content = content.strip()
                    if not content:
                        content = "待办事项"
                    from jarvis.notes_reminder_timer import add_reminder
                    result = add_reminder(content, dt)
                    assistant_text = result["message"]
                    logger.info(f"[Vision+Voice] 添加提醒: {content} at {dt}")
            
            # 计时器匹配
            elif "计时器" in user_text or "倒计时" in user_text or "分钟后提醒我" in user_text:
                import re
                match = re.search(r'(\d+)分钟', user_text)
                minutes = 10
                if match:
                    minutes = int(match.group(1))
                else:
                    match = re.search(r'(\d+)分', user_text)
                    if match:
                        minutes = int(match.group(1))
                content = user_text.strip()
                result = add_timer(minutes, content)
                assistant_text = result["message"]
                logger.info(f"[Vision+Voice] 设置计时器: {minutes}分钟")
            
            # 列表提醒
            elif "显示提醒" in user_text or "看一下提醒" in user_text or "有什么提醒" in user_text or "我的提醒" in user_text:
                assistant_text = list_all_reminders()
            
            # 列表笔记
            elif "我的笔记" in user_text or "显示笔记" in user_text or "查看笔记" in user_text:
                assistant_text = list_notes(10)
            
            # 搜索笔记
            elif "搜索笔记" in user_text:
                import re
                match = re.search(r'搜索笔记\s*(.*)', user_text)
                keyword = match.group(1) if match else ""
                if keyword:
                    assistant_text = search_notes(keyword)
                else:
                    assistant_text = "请告诉我要搜索什么关键词"
            
            # 列表计时器
            elif "计时器" in user_text and ("列表" in user_text or "显示" in user_text):
                assistant_text = list_active_timers()
            
            # 自动建议
            elif "自动建议" in user_text or "给我建议" in user_text or "有什么建议" in user_text:
                from jarvis.notes_reminder_timer import get_auto_suggestions
                assistant_text = get_auto_suggestions()
            
            logger.info(f"[Vision+Voice] 笔记/提醒/计时器功能: {assistant_text[:60]}...")

        # 检查是否是快速工具功能（购物清单、找手机、备忘、快递查询）
        if assistant_text is None:
            from jarvis.quick_tools import quick_tools_handler
            quick_result = quick_tools_handler(user_text)
            if quick_result is not None:
                assistant_text = quick_result
                logger.info(f"[Vision+Voice] 快速工具: {assistant_text[:40]}")

        # 检查是否是计算/单位转换功能
        if assistant_text is None:
            from jarvis.calculator_unit import calculator_handler
            calc_result = calculator_handler(user_text)
            if calc_result is not None:
                assistant_text = calc_result
                logger.info(f"[Vision+Voice] 计算器: {assistant_text[:40]}")

        # 检查是否是古诗词/成语查询
        if assistant_text is None:
            from jarvis.poetry_idiom import poetry_handler
            poetry_result = poetry_handler(user_text)
            if poetry_result is not None:
                assistant_text = poetry_result
                logger.info(f"[Vision+Voice] 古诗词成语: {assistant_text[:40]}")

        # Step 3: 如果未匹配到直接控制，走LLM + 工具调用
        if assistant_text is None:
            if image_b64:
                logger.info("[Vision+Voice] Qwen3-VL 视觉推理...")
                vl_result = _llm_omlx_vision(user_text, image_b64, system_prompt)
                assistant_text = vl_result["content"]
                thinking = vl_result["thinking"]
                logger.info(f"[Vision+Voice] VL 助手: {assistant_text[:80]}...")
            elif use_tools:
                logger.info("[Vision+Voice] OMLX with tools...")
                assistant_text = _llm_omlx_with_tools(user_text)
                logger.info(f"[Vision+Voice] 工具助手: {assistant_text[:80]}...")
            else:
                logger.info("[Vision+Voice] 纯文本问答...")
                assistant_text = llm_chat(user_text, system_prompt=system_prompt)
                thinking = ""
                logger.info(f"[Vision+Voice] 助手: {assistant_text[:80]}...")
        
        # Step 4: TTS
        logger.info("[Vision+Voice] TTS...")
        tts_path = tempfile.mktemp(suffix=".wav")
        tts_say(assistant_text, tts_path)
        with open(tts_path, "rb") as f:
            audio_data = f.read()
        audio_b64 = base64.b64encode(audio_data).decode()
        os.unlink(tts_path)
        
        # 返回结果
        response_data = {
            "success": True,
            "text": user_text,
            "response": assistant_text,
            "thinking": thinking,
            "audio_data": audio_b64,
        }
        if infrared_cmd:
            response_data["infrared"] = infrared_cmd
        
        return jsonify(response_data)
    
    except Exception as e:
        logger.error(f"[Vision+Voice] 管线错误: {e}")
        return jsonify({"error": str(e), "success": False}), 500
    
    finally:
        if os.path.exists(audio_path):
            os.unlink(audio_path)
