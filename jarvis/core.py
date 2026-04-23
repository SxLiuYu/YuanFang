"""
贾维斯智能助理核心系统
基于 FinnA AI + CosyVoice2 语音交互 + FastAPI
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import subprocess
import uuid
import httpx
import redis.asyncio as redis
from qdrant_client import QdrantClient
from litellm import completion
import json
from config import config

# 初始化组件
app = FastAPI(title="贾维斯智能助理", version="1.0.0")

# Redis 缓存
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

# Qdrant 向量数据库
qdrant_client = QdrantClient(host='localhost', port=6333)

# 本地模型配置
LOCAL_MODEL_NAME = "qwen3.5-4b-mlx"
LOCAL_MODEL_CONFIG = config.get_local_model_config()

# 配置Litellm指向本地模型API
import litellm
litellm.api_base = LOCAL_MODEL_CONFIG["api_base"]
litellm.api_key = LOCAL_MODEL_CONFIG["api_key"]

# 语音配置
VOICE_CONFIG = config.get_voice_config()

# 默认模型选择
DEFAULT_MODEL = LOCAL_MODEL_NAME

# 元芳 API
YUANFANG_API = "http://localhost:8000"

# ==================== 核心功能 ====================

@app.on_event("startup")
async def startup():
    """启动时初始化系统"""
    print("[贾维斯] 系统启动中...")
    
# ==================== 语音交互 API ====================

@app.post("/api/voice/speak")
async def speak(text: str, voice_id: str = "default"):
    """
    语音合成 (TTS) - 贾维斯说话
    """
    try:
        # 调用本地 TTS API
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                VOICE_CONFIG["tts"]["endpoint"],
                json={"text": text, "voice_id": voice_id, "speed": 1.0}
            )
            response.raise_for_status()
            result = response.json()

        return {"status": "success", "message": f"贾维斯正在用{voice_id}的声音说话：{text}", "audio_url": result.get("audio_url", "/tmp/jarvis_voice.mp3")}
    except Exception as e:
        return {"status": "error", "message": f"语音合成失败：{str(e)}"}

@app.post("/api/voice/listen")
async def listen(text: str):
    """
    语音识别 (ASR) - 贾维斯听
    """
    try:
        # 调用本地 ASR API
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 假设ASR接口接收音频文件路径或者base64，这里先适配，暂时用传入的text模拟
            response = await client.post(
                VOICE_CONFIG["asr"]["endpoint"],
                json={"audio": text, "language": "zh"}
            )
            response.raise_for_status()
            result = response.json()
            recognized_text = result.get("text", text)

        return {"status": "success", "recognized_text": recognized_text, "message": f"贾维斯已收到：{recognized_text}"}
    except Exception as e:
        return {"status": "error", "message": f"语音识别失败：{str(e)}"}

# ==================== 自然语言理解 API ====================

@app.post("/api/nlu/understand")
async def understand(question: str, context: str = None):
    """
    自然语言理解 - 贾维斯理解你的意图
    """
    try:
        # 使用本地 Qwen3.5-4B 大模型进行意图识别
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
            model=LOCAL_MODEL_NAME,
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
        return {"status": "error", "message": f"理解失败：{str(e)}"}

# ==================== 任务执行 API ====================

@app.post("/api/execute")
async def execute(command: str, context: str = None):
    """
    任务执行 - 贾维斯执行命令
    """
    try:
        # 安全检查：防止危险命令
        dangerous_patterns = ["rm -rf /", "dd if=/dev/zero", "mkfs"]
        for pattern in dangerous_patterns:
            if pattern in command.lower():
                return {"status": "blocked", "message": f"命令被阻止：{command}"}
        
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
        return {"status": "error", "message": f"执行失败：{str(e)}"}

# ==================== 知识库 API ====================

@app.post("/api/knowledge/search")
async def search_knowledge(query: str, limit: int = 5):
    """
    知识库搜索 - 贾维斯查询记忆
    """
    try:
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
        return {"status": "error", "message": f"搜索失败：{str(e)}"}

# ==================== 智能对话 API ====================

@app.post("/api/chat")
async def chat(message: str, user_id: str = None):
    """
    智能对话 - 贾维斯回答你的问题
    """
    try:
        # 直接调用本地大模型
        response = await completion(
            model=LOCAL_MODEL_NAME,
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
@app.get("/api/status")
async def get_status():
    """获取贾维斯当前状态"""
    return {
        "status": "online",
        "version": "1.0.0",
        "models": {
            "local_qwen": {"model": "Qwen3.5-4B-MLX", "type": "本地离线大模型"}
        },
        "voice_config": VOICE_CONFIG,
        "redis_connected": False if redis_client.ping() is None else redis_client.ping(),
        "qdrant_connected": False if qdrant_client.is_ready() is None else qdrant_client.is_ready()
    }

# ==================== 主入口 ====================

if __name__ == "__main__":
    import uvicorn
    # 启动贾维斯服务：http://0.0.0.0:8000
    uvicorn.run("core:app", host="0.0.0.0", port=8001, reload=False)

# ==================== 系统测试 ====================

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "jarvis": "running"}

# ==================== 错误处理 ====================

@app.exception_handler(Exception)
async def exception_handler(request, exc):
    return {"status": "error", "message": f"内部错误：{str(exc)}"}
