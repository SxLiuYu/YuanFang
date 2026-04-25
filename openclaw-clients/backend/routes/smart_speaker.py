from fastapi import APIRouter, Request
import logging
from services.smart_speaker import (
    tmall_handler, xiaomi_handler, baidu_handler,
    huawei_handler, jd_handler, samsung_handler, homekit_handler
)
from shared import success_response, error_response

router = APIRouter(prefix="/api/v1/smart-speaker", tags=["smart-speaker"])

@router.post("/tmall")
async def smart_speaker_tmall(request: Request):
    try:
        body = await request.json()
        result = await tmall_handler.handle(body)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.post("/xiaomi")
async def smart_speaker_xiaomi(request: Request):
    try:
        body = await request.json()
        result = await xiaomi_handler.handle(body)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.post("/baidu")
async def smart_speaker_baidu(request: Request):
    try:
        body = await request.json()
        result = await baidu_handler.handle(body)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.post("/huawei")
async def smart_speaker_huawei(request: Request):
    try:
        body = await request.json()
        result = await huawei_handler(body)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.post("/jd")
async def smart_speaker_jd(request: Request):
    try:
        body = await request.json()
        result = await jd_handler(body)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.post("/samsung")
async def smart_speaker_samsung(request: Request):
    try:
        body = await request.json()
        result = await samsung_handler(body)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))

@router.post("/homekit")
async def smart_speaker_homekit(request: Request):
    try:
        body = await request.json()
        result = await homekit_handler(body)
        return success_response(result)
    except Exception as e:
        return error_response(str(e))