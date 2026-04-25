#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一异常处理 - 自定义异常基类和异常处理中间件
支持 Flask 和 FastAPI
"""

from typing import Optional, Any, Dict
from flask import Flask, jsonify
from flask import Request
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


def setup_exception_handler(app: Flask) -> None:
    """设置全局异常处理器（Flask 版本）"""

    @app.errorhandler(AppBaseException)
    def handle_app_exception(exc: AppBaseException):
        """处理应用自定义异常"""
        logger.warning(
            f"应用异常: {exc.message} (code={exc.code}, status={exc.status_code})"
        )
        response = {
            "success": False,
            "code": exc.code,
            "message": exc.message,
            "data": exc.data
        }
        return jsonify(response), exc.status_code

    @app.errorhandler(404)
    def handle_404(exc):
        """处理 404 未找到"""
        from flask import request
        logger.debug(f"404 未找到: {request.path}")
        response = {
            "success": False,
            "code": 4040,
            "message": f"接口不存在: {request.path}",
            "data": None
        }
        return jsonify(response), 404

    @app.errorhandler(405)
    def handle_405(exc):
        """处理 405 方法不允许"""
        from flask import request
        response = {
            "success": False,
            "code": 4050,
            "message": f"请求方法不允许: {request.method} {request.path}",
            "data": None
        }
        return jsonify(response), 405

    @app.errorhandler(Exception)
    def handle_generic_exception(exc: Exception):
        """处理所有未捕获的异常"""
        from flask import request
        logger.error(
            f"未捕获异常: {str(exc)} "
            f"path={request.path} method={request.method}",
            exc_info=True
        )
        response = {
            "success": False,
            "code": 5000,
            "message": "服务器内部错误",
            "data": str(exc) if app.debug else None
        }
        return jsonify(response), 500

    logger.info("✅ 全局异常处理器已配置")
