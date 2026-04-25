from fastapi import APIRouter, Request
import logging
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from services.chat_service import chat_service
from shared import success_response, error_response

router = APIRouter(tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"
    context: Optional[List[Dict]] = []
    voice_input: Optional[bool] = False
    voice_output: Optional[bool] = True

@router.post("/api/v1/agent/chat")
async def agent_chat(request: ChatRequest):
    try:
        result = await chat_service.chat(
            message=request.message, session_id=request.session_id,
            context=request.context, voice_output=request.voice_output
        )
        return success_response(result)
    except Exception as e:
        logging.error(f"Chat error: {e}")
        return error_response(str(e))