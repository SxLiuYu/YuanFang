#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI 对话服务
支持阿里云、OpenAI、Anthropic、本地模型
"""

import os
import logging
from typing import Optional, List, Dict, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)

# 会话历史存储
_session_history: Dict[str, List[Dict]] = {}

async def chat(
    message: str,
    session_id: str = "default",
    context: Optional[List[Dict]] = None,
    voice_output: bool = True
) -> Dict[str, Any]:
    """
    AI 对话
    
    Args:
        message: 用户消息
        session_id: 会话 ID
        context: 历史对话上下文
        voice_output: 是否返回语音
        
    Returns:
        {
            "text": "AI 回复",
            "audio_url": "/audio/xxx.mp3",
            "session_id": "default",
            "turn_id": 42
        }
    """
    from . import voice_service
    
    # 获取配置
    config = _get_config()
    chat_config = config.get("ai_chat", {})
    provider = chat_config.get("provider", "aliyun")
    
    logger.info(f"Chat: session={session_id}, provider={provider}, message_length={len(message)}")
    
    # 构建对话历史
    if session_id not in _session_history:
        _session_history[session_id] = []
    
    # 添加用户消息
    _session_history[session_id].append({"role": "user", "content": message})
    
    # 限制历史长度
    max_turns = config.get("advanced", {}).get("conversation_memory", {}).get("max_turns", 10)
    if len(_session_history[session_id]) > max_turns * 2:
        _session_history[session_id] = _session_history[session_id][-max_turns * 2:]
    
    # 调用 LLM
    if provider == "aliyun":
        response_text = await _chat_aliyun(message, _session_history[session_id], chat_config)
    elif provider == "openai":
        response_text = await _chat_openai(message, _session_history[session_id], chat_config)
    elif provider == "anthropic":
        response_text = await _chat_anthropic(message, _session_history[session_id], chat_config)
    elif provider == "ollama":
        response_text = await _chat_ollama(message, _session_history[session_id], chat_config)
    else:
        raise ValueError(f"Unknown chat provider: {provider}")
    
    # 添加 AI 回复到历史
    _session_history[session_id].append({"role": "assistant", "content": response_text})
    
    # 生成语音（可选）
    audio_url = None
    if voice_output:
        try:
            tts_result = await voice_service.text_to_speech(response_text)
            audio_url = tts_result.get("audio_url")
        except Exception as e:
            logger.error(f"TTS failed: {e}")
    
    return {
        "text": response_text,
        "audio_url": audio_url,
        "session_id": session_id,
        "turn_id": len(_session_history[session_id]) // 2
    }

async def _chat_aliyun(message: str, history: List[Dict], config: Dict) -> str:
    """阿里云 DashScope 对话"""
    try:
        from http import HTTPStatus
        import dashscope
        
        api_key = config.get("aliyun", {}).get("api_key")
        if not api_key:
            api_key = os.environ.get("DASHSCOPE_API_KEY")
        
        if not api_key:
            raise ValueError("Aliyun API Key not configured")
        
        dashscope.api_key = api_key
        model = config.get("model", "qwen-max")
        
        # 调用 Qwen
        messages = [{"role": "system", "content": "你是一个家庭助手，帮助用户管理家庭生活。"}] + history
        
        response = dashscope.Generation.call(
            model=model,
            messages=messages,
            result_format='message'
        )
        
        if response.status_code == HTTPStatus.OK:
            return response.output.choices[0].message.content
        else:
            logger.error(f"Aliyun chat error: {response.code}, {response.message}")
            return f"抱歉，出现错误：{response.message}"
            
    except Exception as e:
        logger.error(f"Aliyun chat error: {e}")
        return f"抱歉，出现错误：{str(e)}"

async def _chat_openai(message: str, history: List[Dict], config: Dict) -> str:
    """OpenAI 对话"""
    try:
        from openai import OpenAI
        
        api_key = config.get("openai", {}).get("api_key")
        if not api_key:
            api_key = os.environ.get("OPENAI_API_KEY")
        
        if not api_key:
            raise ValueError("OpenAI API Key not configured")
        
        client = OpenAI(api_key=api_key)
        base_url = config.get("openai", {}).get("base_url")
        if base_url:
            client.base_url = base_url
        
        model = config.get("model", "gpt-3.5-turbo")
        
        messages = [{"role": "system", "content": "你是一个家庭助手。"}] + history
        
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 2048)
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        logger.error(f"OpenAI chat error: {e}")
        return f"抱歉，出现错误：{str(e)}"

async def _chat_anthropic(message: str, history: List[Dict], config: Dict) -> str:
    """Anthropic Claude 对话"""
    try:
        from anthropic import Anthropic
        
        api_key = config.get("anthropic", {}).get("api_key")
        if not api_key:
            api_key = os.environ.get("ANTHROPIC_API_KEY")
        
        if not api_key:
            raise ValueError("Anthropic API Key not configured")
        
        client = Anthropic(api_key=api_key)
        
        # 转换历史格式
        messages = []
        for msg in history:
            if msg["role"] == "user":
                messages.append({"role": "user", "content": msg["content"]})
            elif msg["role"] == "assistant":
                messages.append({"role": "assistant", "content": msg["content"]})
        
        response = client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=config.get("max_tokens", 2048),
            messages=messages
        )
        
        return response.content[0].text
        
    except Exception as e:
        logger.error(f"Anthropic chat error: {e}")
        return f"抱歉，出现错误：{str(e)}"

async def _chat_ollama(message: str, history: List[Dict], config: Dict) -> str:
    """Ollama 本地模型对话"""
    try:
        import requests
        
        base_url = config.get("ollama", {}).get("base_url", "http://localhost:11434")
        model = config.get("ollama", {}).get("model", "qwen2.5:7b")
        
        # 构建 prompt
        prompt = "\n".join([f"{m['role']}: {m['content']}" for m in history])
        prompt += f"\nuser: {message}\nassistant: "
        
        response = requests.post(
            f"{base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        
        result = response.json()
        return result.get("response", "")
        
    except Exception as e:
        logger.error(f"Ollama chat error: {e}")
        return f"抱歉，出现错误：{str(e)}"

def _get_config() -> Dict:
    """获取配置（从主配置加载）"""
    # TODO: 从主配置加载
    return {
        "ai_chat": {
            "provider": "aliyun",
            "aliyun": {
                "api_key": os.environ.get("DASHSCOPE_API_KEY", "")
            }
        }
    }

def get_session_history(session_id: str) -> List[Dict]:
    """获取会话历史"""
    return _session_history.get(session_id, [])

def clear_session(session_id: str):
    """清除会话历史"""
    if session_id in _session_history:
        del _session_history[session_id]
