#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OpenClaw Family Assistant - 后端服务主入口
所有业务路由已拆分到 routes/ 模块中
"""

import logging
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# 统一配置和异常处理
from config import config
from exceptions import setup_exception_handler
from logging_config import setup_logging

# 初始化日志
setup_logging(config.log_level)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OpenClaw Family Assistant API",
    description="家庭助手后端服务 - 18 大类功能完整支持",
    version="1.0.0",
    debug=config.debug
)

# CORS 配置
cors_origins = config.security.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置统一异常处理
setup_exception_handler(app)

from routes.shared import success_response, error_response

@app.get("/")
async def root():
    return success_response({
        "name": "OpenClaw Family Assistant API",
        "version": "1.0.0",
        "status": "running",
        "features": [name for name, enabled in config.features.model_dump().items() if enabled]
    })

@app.get("/health")
async def health_check():
    return success_response({"status": "healthy"})


# 延迟导入路由避免循环导入
from routes.voice import router as voice_router
from routes.chat import router as chat_router
from routes.smart_home import router as smart_home_router
from routes.finance import router as finance_router
from routes.task import router as task_router
from routes.shopping_recipe import router as shopping_recipe_router
from routes.health_calendar import router as health_calendar_router
from routes.other_services import router as other_services_router
from routes.smart_speaker import router as smart_speaker_router
from routes.voice_advanced import router as voice_advanced_router
from routes.family import router as family_router
from routes.hardware import router as hardware_router
from routes.analysis_reminder_export import router as analysis_router
from routes.device_personal import router as device_personal_router

app.include_router(voice_router)
app.include_router(chat_router)
app.include_router(smart_home_router)
app.include_router(finance_router)
app.include_router(task_router)
app.include_router(shopping_recipe_router)
app.include_router(health_calendar_router)
app.include_router(other_services_router)
app.include_router(smart_speaker_router)
app.include_router(voice_advanced_router)
app.include_router(family_router)
app.include_router(hardware_router)
app.include_router(analysis_router)
app.include_router(device_personal_router)


if __name__ == "__main__":
    data_dir = config.get_data_dir()
    data_dir.mkdir(exist_ok=True)
    uvicorn.run(
        app,
        host=config.server_host,
        port=config.server_port,
        log_level=config.log_level.lower()
    )