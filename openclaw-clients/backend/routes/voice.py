import logging
from fastapi import APIRouter
from services.voice_service import voice_service
from shared import success_response, error_response, VoiceInputRequest, VoiceOutputRequest, VideoInputRequest

router = APIRouter(prefix="/api/v1/voice", tags=["voice"])

@router.post("/input")
async def voice_input(request: VoiceInputRequest):
    try:
        result = await voice_service.speech_to_text(
            audio=request.audio, format=request.format,
            language=request.language, provider=request.provider
        )
        return success_response(result)
    except Exception as e:
        logging.error(f"Voice input error: {e}")
        return error_response(str(e))

@router.post("/output")
async def voice_output(request: VoiceOutputRequest):
    try:
        result = await voice_service.text_to_speech(
            text=request.text, voice=request.voice,
            format=request.format, speed=request.speed
        )
        return success_response(result)
    except Exception as e:
        logging.error(f"Voice output error: {e}")
        return error_response(str(e))

@router.post("/video/input")
async def video_input(request: VideoInputRequest):
    try:
        result = await voice_service.video_understanding(
            video=request.video, prompt=request.prompt,
            max_frames=request.max_frames
        )
        return success_response(result)
    except Exception as e:
        logging.error(f"Video input error: {e}")
        return error_response(str(e))