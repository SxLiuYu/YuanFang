#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一异常处理 - 自定义异常基类和异常处理中间件
"""

from typing import Optional, Any, Dict
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import FastAPI
import logging

logger = logging.getLogger(__name__)


class AppBaseException(Exception):
    """应用自定义异常基类"""
    def __init__(
        self,
        message: str = "服务器内部错误",
        code: int = 500,
        status_code: int = 500,
        data: Optional[Any] = None
    ):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.data = data
        super().__init__(self.message)


class ConfigurationError(AppBaseException):
    """配置错误"""
    def __init__(self, message: str = "配置错误", data: Any = None):
        super().__init__(
            message=message,
            code=4001,
            status_code=500,
            data=data
        )


class ValidationError(AppBaseException):
    """参数验证错误"""
    def __init__(self, message: str = "参数验证失败", data: Any = None):
        super().__init__(
            message=message,
            code=4002,
            status_code=400,
            data=data
        )


class AuthenticationError(AppBaseException):
    """认证失败"""
    def __init__(self, message: str = "认证失败", data: Any = None):
        super().__init__(
            message=message,
            code=4011,
            status_code=401,
            data=data
        )


class PermissionDenied(AppBaseException):
    """权限拒绝"""
    def __init__(self, message: str = "权限不足", data: Any = None):
        super().__init__(
            message=message,
            code=4031,
            status_code=403,
            data=data
        )


class ResourceNotFound(AppBaseException):
    """资源未找到"""
    def __init__(self, message: str = "资源未找到", data: Any = None):
        super().__init__(
            message=message,
            code=4041,
            status_code=404,
            data=data
        )


class ServiceUnavailable(AppBaseException):
    """服务不可用"""
    def __init__(self, message: str = "服务暂时不可用", data: Any = None):
        super().__init__(
            message=message,
            code=5031,
            status_code=503,
            data=data
        )


class ExternalAPIError(AppBaseException):
    """外部 API 调用错误"""
    def __init__(self, message: str = "外部服务调用失败", data: Any = None):
        super().__init__(
            message=message,
            code=5021,
            status_code=502,
            data=data
        )


def setup_exception_handler(app: FastAPI) -> None:
    """设置全局异常处理器"""

    @app.exception_handler(AppBaseException)
    async def handle_app_exception(request: Request, exc: AppBaseException) -> JSONResponse:
        """处理应用自定义异常"""
        logger.warning(
            f"应用异常: {exc.message} (code={exc.code}, status={exc.status_code}) "
            f"path={request.url.path}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "code": exc.code,
                "message": exc.message,
                "data": exc.data
            }
        )

    @app.exception_handler(404)
    async def handle_404(request: Request, exc: Exception) -> JSONResponse:
        """处理 404 未找到"""
        logger.debug(f"404 未找到: {request.url.path}")
        return JSONResponse(
            status_code=404,
            content={
                "success": False,
                "code": 4040,
                "message": f"接口不存在: {request.url.path}",
                "data": None
            }
        )

    @app.exception_handler(405)
    async def handle_405(request: Request, exc: Exception) -> JSONResponse:
        """处理 405 方法不允许"""
        return JSONResponse(
            status_code=405,
            content={
                "success": False,
                "code": 4050,
                "message": f"请求方法不允许: {request.method} {request.url.path}",
                "data": None
            }
        )

    @app.exception_handler(Exception)
    async def handle_generic_exception(request: Request, exc: Exception) -> JSONResponse:
        """处理所有未捕获的异常"""
        logger.error(
            f"未捕获异常: {str(exc)} "
            f"path={request.url.path} method={request.method}",
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "code": 5000,
                "message": "服务器内部错误",
                "data": str(exc) if app.debug else None
            }
        )

    logger.info("✅ 全局异常处理器已配置")
