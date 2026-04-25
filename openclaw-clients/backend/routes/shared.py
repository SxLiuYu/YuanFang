import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel


def success_response(data: Any = None, message: str = "success"):
    return {"success": True, "code": 200, "message": message, "data": data}


def error_response(message: str, code: int = 400):
    return {"success": False, "code": code, "message": message, "data": None}


class VoiceInputRequest(BaseModel):
    audio: Optional[str] = None
    format: Optional[str] = "wav"
    language: Optional[str] = "zh-CN"
    provider: Optional[str] = None

class VoiceOutputRequest(BaseModel):
    text: str
    voice: Optional[str] = None
    format: Optional[str] = "mp3"
    speed: Optional[float] = 1.0

class VideoInputRequest(BaseModel):
    video: Optional[str] = None
    prompt: Optional[str] = "描述这个视频的内容"
    max_frames: Optional[int] = 60

class SmartHomeControlRequest(BaseModel):
    device_id: str
    action: str
    value: Optional[Any] = None

class TransactionRequest(BaseModel):
    amount: float
    category: str
    type: str
    description: Optional[str] = ""
    date: Optional[str] = None

class TaskRequest(BaseModel):
    title: str
    description: Optional[str] = ""
    assignee: Optional[str] = None
    due_date: Optional[str] = None
    priority: Optional[str] = "normal"

class ShoppingItemRequest(BaseModel):
    name: str
    quantity: Optional[int] = 1
    category: Optional[str] = "other"