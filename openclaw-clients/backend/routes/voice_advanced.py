from fastapi import APIRouter, Request
import logging
from services.voice_command_service import VoiceCommandService
from services.voice_control_service import (
    VoiceControlService, get_voice_control_service,
    process_voice_input, end_voice_session
)
from services.voice_enhanced_service import (
    voice_enhanced_service, VoiceCommandRequest, ScheduleParseRequest
)
from shared import success_response, error_response

router = APIRouter(tags=["voice-advanced"])

_voice_command_service = None

def get_voice_command_service():
    global _voice_command_service
    if _voice_command_service is None:
        _voice_command_service = VoiceCommandService()
    return _voice_command_service

_voice_control_service = None

def get_voice_control_svc() -> VoiceControlService:
    global _voice_control_service
    if _voice_control_service is None:
        _voice_control_service = VoiceControlService()
    return _voice_control_service

@router.post("/api/v1/voice/parse")
async def parse_voice_command(request: Request):
    body = await request.json()
    text = body.get('text', '')
    if not text:
        return error_response('请提供语音文本')
    service = get_voice_command_service()
    result = service.parse_command(text)
    return success_response(result)

@router.post("/api/v1/voice/execute")
async def execute_voice_command(request: Request):
    body = await request.json()
    text = body.get('text', '')
    if not text:
        return error_response('请提供语音文本')
    service = get_voice_command_service()
    parsed = service.parse_command(text)
    intent = parsed.get('intent')
    slots = parsed.get('slots', {})
    executed = False
    result_data = {'parsed': parsed}
    if intent == 'accounting':
        from services.personal_data_service import get_service as get_personal_service
        personal_service = get_personal_service()
        personal_service.record_payment(
            amount=slots.get('amount', 0), category=slots.get('category'),
            merchant=slots.get('merchant'), payment_type=slots.get('action', 'expense')
        )
        executed = True
        result_data['action'] = 'recorded_payment'
    elif intent == 'reminder':
        from services.enhanced_reminder_service import get_enhanced_service
        reminder_service = get_enhanced_service()
        reminder_service.create_reminder(
            title=slots.get('content', '提醒'), trigger_time=slots.get('time'), reminder_type='time'
        )
        executed = True
        result_data['action'] = 'created_reminder'
    elif intent == 'control':
        result_data['action'] = 'device_control_pending'
    result_data['executed'] = executed
    return success_response(result_data)

@router.post("/api/v1/voice/control/input")
async def voice_control_input(request: Request):
    body = await request.json()
    text = body.get('text', '')
    session_id = body.get('session_id')
    if not text:
        return error_response('请提供语音文本')
    service = get_voice_control_svc()
    result = await service.process_input(text, session_id)
    return success_response(result)

@router.post("/api/v1/voice/control/session/end")
async def voice_control_end_session(request: Request):
    body = await request.json()
    session_id = body.get('session_id')
    service = get_voice_control_svc()
    result = await service.end_session(session_id)
    return success_response(result)

@router.get("/api/v1/voice/control/session/{session_id}/history")
async def voice_control_session_history(session_id: str, limit: int = 10):
    service = get_voice_control_svc()
    history = service.get_session_history(session_id, limit)
    return success_response(history)

@router.get("/api/v1/voice/control/sessions")
async def voice_control_sessions(limit: int = 50):
    service = get_voice_control_svc()
    sessions = service.get_all_sessions(limit)
    return success_response(sessions)

@router.get("/api/v1/voice/control/statistics")
async def voice_control_statistics():
    service = get_voice_control_svc()
    stats = service.get_statistics()
    return success_response(stats)

@router.post("/api/v1/voice/control/wake-word")
async def add_wake_word(request: Request):
    body = await request.json()
    wake_word = body.get('wake_word')
    aliases = body.get('aliases', [])
    sensitivity = body.get('sensitivity', 0.8)
    if not wake_word:
        return error_response('请提供唤醒词')
    service = get_voice_control_svc()
    result = service.add_custom_wake_word(wake_word, aliases, sensitivity)
    return success_response(result)

@router.get("/api/v1/voice/control/commands")
async def get_supported_commands():
    service = get_voice_control_svc()
    commands = service.get_supported_commands()
    return success_response(commands)

@router.post("/api/v1/voice/control/device")
async def voice_device_control(request: VoiceCommandRequest):
    try:
        result = await voice_enhanced_service.execute_device_control(text=request.text, context=request.context)
        return success_response(result.dict())
    except Exception as e:
        logging.error(f"Voice device control error: {e}")
        return error_response(str(e))

@router.post("/api/v1/voice/control/scene")
async def voice_scene_control(request: VoiceCommandRequest):
    try:
        result = await voice_enhanced_service.execute_scene_control(text=request.text, context=request.context)
        return success_response(result.dict())
    except Exception as e:
        logging.error(f"Voice scene control error: {e}")
        return error_response(str(e))

@router.get("/api/v1/voice/suggestions")
async def get_voice_suggestions(user_id: str = None):
    try:
        result = await voice_enhanced_service.get_suggestions(user_id=user_id)
        return success_response([s.dict() for s in result])
    except Exception as e:
        logging.error(f"Get suggestions error: {e}")
        return error_response(str(e))

@router.post("/api/v1/voice/schedule/parse")
async def parse_voice_schedule(request: ScheduleParseRequest):
    try:
        result = await voice_enhanced_service.parse_schedule(text=request.text, user_id=request.user_id)
        return success_response(result.dict())
    except Exception as e:
        logging.error(f"Schedule parse error: {e}")
        return error_response(str(e))

@router.post("/api/v1/voice/command")
async def process_voice_command(request: VoiceCommandRequest):
    try:
        result = await voice_enhanced_service.process_voice_command(request)
        return success_response(result.dict())
    except Exception as e:
        logging.error(f"Process voice command error: {e}")
        return error_response(str(e))