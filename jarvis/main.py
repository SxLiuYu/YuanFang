"""
贾维斯智能助理 - 主启动文件

用法:
  python main.py              # 启动服务 (默认)
  python main.py --web        # 启动 Web 界面
  python main.py --cli        # 启动命令行模式

核心架构:
  - FastAPI API 服务 (端口：8001)
  - FinnA AI 模型集成 (DeepSeek V3.1, Kimi K2, Qwen-32B)
  - CosyVoice2 (语音合成 TTS + 语音识别 ASR)
  - Qdrant (向量数据库，知识库)
  - Redis (会话缓存)

贾维斯使命：让老于更好地生活 🦞
"""

import asyncio
import argparse
import subprocess
import uuid
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
# import redis.asyncio as redis
# from qdrant_client import QdrantClient
import httpx
import json
from config import config

# ==================== 系统配置 ====================

APP_CONFIG = {
    "api_base": "http://localhost:8002",
    "redis_host": "localhost", 
    "redis_port": 6379,
    "qdrant_host": "localhost", 
    "qdrant_port": 6333,
}

# ==================== 本地模型配置 ====================
# 所有模型调用统一使用本地 OMLX Qwen3.5-4B 模型
LOCAL_MODEL_NAME = "qwen3.5-4b-mlx"

# ==================== 语音配置 ====================
# 语音服务调用本地 YuanFang 语音接口
VOICE_CONFIG = config.get_voice_config()

# ==================== 默认配置 ====================
DEFAULT_MODEL = LOCAL_MODEL_NAME
DEFAULT_VOICE = "james"  # James 声音

# ==================== YuanFang API (可选) ====================

YUANFANG_API = "http://localhost:8000"

# ==================== 本地模型 API 客户端 ====================

LOCAL_MODEL_CONFIG = config.get_local_model_config()

async def completion(messages: list):
    """调用本地模型 API 完成对话"""
    headers = {
        "Authorization": f"Bearer {LOCAL_MODEL_CONFIG['api_key']}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": LOCAL_MODEL_CONFIG["model_name"],
        "messages": messages,
        "stream": False
    }
    
    async with httpx.AsyncClient(timeout=120.0) as client:
        response = await client.post(
            f"{LOCAL_MODEL_CONFIG['api_base']}/chat/completions",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        result = await response.json()
        return result["choices"]

# ==================== 初始化组件 ====================

app = FastAPI(
    title="贾维斯智能助理", 
    description="让老于更好地生活的 AI 助手系统 🦞",
    version="1.0.0"
)

# Redis 缓存
redis_client = redis.Redis(
    host=APP_CONFIG["redis_host"], 
    port=APP_CONFIG["redis_port"], 
    db=0, 
    decode_responses=True
)

# Qdrant 向量数据库
qdrant_client = QdrantClient(
    host=APP_CONFIG["qdrant_host"], 
    port=APP_CONFIG["qdrant_port"]
)

# ==================== CORS 配置 ====================

app.add_middleware(
    CORSMiddleware, 
    allow_origins=["*"],  # 生产环境应限制为特定域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== 核心功能实现 ====================

@app.on_event("startup")
async def startup():
    """系统启动"""
    print("[贾维斯] 正在初始化系统...")
    
# ==================== TTS API - 语音合成 ====================

class SpeakRequest(BaseModel):
    text: str
    voice_id: str = DEFAULT_VOICE

@app.post("/api/voice/speak")
async def speak(request: SpeakRequest):
    """
    语音合成 (TTS) - 贾维斯说话
    
    Args:
        request (SpeakRequest): 语音合成请求，包含 text 和可选 voice_id
    """
    try:
        text = request.text
        voice_id = request.voice_id
        
        # 调用本地 TTS API
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                response = await client.post(
                    VOICE_CONFIG["tts"]["endpoint"],
                    json={"text": text, "voice_id": voice_id, "speed": 1.0}
                )
                response.raise_for_status()
                result = response.json()
                audio_url = result.get("audio_url", "/tmp/jarvis_voice.mp3")
            except:
                # 语音服务不可用的时候返回默认路径
                audio_url = "/tmp/jarvis_voice.mp3"
        
        return {
            "status": "success", 
            "message": f"贾维斯正在用{voice_id}的声音说话：{text}",
            "audio_url": "/tmp/jarvis_voice.mp3",
            "voice_id": voice_id,
            "speed": 1.0
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"语音合成失败：{str(e)}"
        }

# ==================== ASR API - 语音识别 ====================

class ListenRequest(BaseModel):
    audio_data: str
    text: str = None

@app.post("/api/voice/listen")
async def listen(request: ListenRequest):
    """
    语音识别 (ASR) - 贾维斯听
    
    Args:
        request (ListenRequest): 语音识别请求，包含音频数据
    """
    try:
        text = request.text if request.text else request.audio_data
        # 调用本地 ASR API
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    VOICE_CONFIG["asr"]["endpoint"],
                    json={"audio": text, "language": "zh"}
                )
                response.raise_for_status()
                result = response.json()
                recognized_text = result.get("text", text)
        except:
            # 语音服务不可用的时候直接返回传入的文本
            recognized_text = text
        
        return {
            "status": "success", 
            "recognized_text": recognized_text, 
            "message": f"贾维斯已收到：{recognized_text}"
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"语音识别失败：{str(e)}"
        }

# ==================== NLU API - 自然语言理解 ====================

class UnderstandRequest(BaseModel):
    question: str
    context: str = None

@app.post("/api/nlu/understand")
async def understand(request: UnderstandRequest):
    """
    自然语言理解 - 贾维斯理解你的意图
    
    Args:
        request (UnderstandRequest): 意图识别请求，包含 question 和可选 context
    """
    try:
        question = request.question
        context = request.context
        
        prompt = f"""你是一个智能助手，请分析以下用户问题：
用户输入："{question}"

请按以下格式输出 JSON:
{{
  "intent": "意图类型 (如：search, weather, calendar, file, system)",
  "parameters": {{参数}},
  "confidence": 0-1 之间的置信度分数，
  "suggested_actions": ["建议操作 1", "建议操作 2"]
}}

只返回 JSON，不要其他文本。
"""
        
        response = await completion(
            messages=[{"role": "user", "content": prompt}]
        )
        
        # 解析结果
        import json
        result = json.loads(response[0]["content"])
        
        return {
            "status": "success", 
            "intent": result["intent"],
            "parameters": result["parameters"],
            "confidence": result["confidence"],
            "suggested_actions": result["suggested_actions"]
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"理解失败：{str(e)}"
        }

# ==================== 任务执行 API ====================

class ExecuteRequest(BaseModel):
    command: str
    context: str = None

@app.post("/api/execute")
async def execute(request: ExecuteRequest):
    """
    任务执行 - 贾维斯执行命令
    
    Args:
        request (ExecuteRequest): 执行请求，包含 command 和可选 context
    """
    try:
        command = request.command
        context = request.context
        # 安全检查：防止危险命令
        dangerous_patterns = ["rm -rf /", "dd if=/dev/zero", "mkfs"]
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                return {
                    "status": "blocked", 
                    "message": f"命令被阻止：{command}"
                }
        
        # 执行命令（使用 subprocess）
        process = await asyncio.create_subprocess_shell(
            command, 
            stdout=asyncio.subprocess.PIPE, 
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            return {
                "status": "error", 
                "message": f"命令执行失败：{command}\n错误信息：{stderr.decode()}",
                "output": stdout.decode() if stdout else None
            }
        
        return {
            "status": "success", 
            "message": f"命令执行成功：{command}",
            "output": stdout.decode() if stdout else None,
            "exit_code": process.returncode
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"执行失败：{str(e)}"
        }

# ==================== 知识库 API ====================

class SearchRequest(BaseModel):
    query: str
    limit: int = 5

@app.post("/api/knowledge/search")
async def search_knowledge(request: SearchRequest):
    """
    知识库搜索 - 贾维斯查询记忆
    
    Args:
        request (SearchRequest): 搜索请求，包含 query 和可选 limit
    """
    try:
        query = request.query
        limit = request.limit
        # 在 Qdrant 中搜索相似向量
        results = qdrant_client.search(
            collection_name="jarvis_knowledge",
            query_vector=qdrant_client.get_embedding(query),  # 需要嵌入向量
            limit=limit
        )
        
        return {
            "status": "success", 
            "results": [item["payload"]["text"] for item in results] if results else [],
            "count": len(results)
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"搜索失败：{str(e)}"
        }

# ==================== 智能对话 API ====================

class ChatRequest(BaseModel):
    message: str
    user_id: str = None

@app.post("/api/chat")
async def chat(request: ChatRequest):
    """
    智能对话 - 贾维斯回答你的问题
    """
    try:
        message = request.message
        # 直接调用本地大模型
        response = await completion(
            messages=[{"role": "user", "content": f"你是贾维斯，老于的智能助手。用户问：{message}"}]
        )
        return {
            "status": "success", 
            "response": response[0]["content"],
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": f"对话失败：{str(e)}"
        }

# ==================== 系统状态 API ====================

@app.get("/api/status")
async def get_status():
    """获取贾维斯当前状态"""
    redis_ok = False
    try:
        await redis_client.ping()
        redis_ok = True
    except:
        pass
    
    qdrant_ok = False
    try:
        qdrant_ok = qdrant_client.is_ready()
    except:
        pass
        
    return {
        "status": "online", 
        "version": "1.0.0",
        "models": {
            "local_qwen": {"model": "Qwen3.5-4B-MLX", "type": "本地离线大模型"}
        },
        "voice_config": VOICE_CONFIG,
        "redis_connected": redis_ok,
        "qdrant_connected": qdrant_ok
    }

# ==================== 健康检查 API ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy", 
        "jarvis": "running"
    }

# ==================== 命令行模式 ====================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="贾维斯智能助理")
    parser.add_argument(
        "--web", 
        action="store_true", 
        help="启动 Web 界面"
    )
    parser.add_argument(
        "--cli", 
        action="store_true", 
        help="启动命令行模式"
    )
    parser.add_argument(
        "--host", 
        default="0.0.0.0", 
        help="监听地址"
    )
    parser.add_argument(
        "--port", 
        default=8002, 
        type=int, 
        help="监听端口"
    )
    
    args = parser.parse_args()
    
    if args.cli:
        # 命令行模式
        print("[贾维斯] 启动中...")
        
        # 检查服务是否运行
        import urllib3
        urllib3.disable()  # 禁用 HTTPS warnings
        
        try:
            response = subprocess.check_output(
                f"curl -s http://{args.host}:{args.port}/health", 
                shell=True, text=True
            )
            print(f"[贾维斯] 服务已运行在 http://{args.host}:{args.port}")
            print("[贾维斯] 可用命令:")
            print("  - jarvis hello           # 问候")
            print("  - jarvis whoami          # 你是谁？")
            print("  - jarvis execute 'ls'    # 执行命令")
        except Exception as e:
            print(f"[贾维斯] 服务未运行，正在启动...")
            
    else:
        # Web 模式
        print("[贾维斯] 启动中...")
        
        uvicorn.run(
            "main:app", 
            host=args.host, 
            port=args.port, 
            reload=False
        )
