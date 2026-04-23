"""
API 响应包装器
统一所有 API 的响应格式
"""

from flask import jsonify
from typing import Any, Optional, Dict, List


def success(data: Any = None, message: str = "操作成功", **kwargs) -> tuple:
    """
    成功响应
    
    Args:
        data: 响应数据
        message: 成功消息
        **kwargs: 额外字段
        
    Returns:
        Flask response tuple
    """
    response = {
        "success": True,
        "message": message
    }
    if data is not None:
        response["data"] = data
    response.update(kwargs)
    return jsonify(response), 200


def error(message: str = "操作失败", code: int = 400, error_code: str = None) -> tuple:
    """
    错误响应
    
    Args:
        message: 错误消息
        code: HTTP 状态码
        error_code: 业务错误码
        
    Returns:
        Flask response tuple
    """
    response = {
        "success": False,
        "message": message
    }
    if error_code:
        response["error_code"] = error_code
    return jsonify(response), code


def paginated(items: List, total: int, page: int = 1, page_size: int = 20, **kwargs) -> tuple:
    """
    分页响应
    
    Args:
        items: 数据列表
        total: 总数
        page: 当前页
        page_size: 每页大小
        **kwargs: 额外字段
        
    Returns:
        Flask response tuple
    """
    response = {
        "success": True,
        "data": items,
        "pagination": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    }
    response.update(kwargs)
    return jsonify(response), 200


def created(data: Any = None, message: str = "创建成功") -> tuple:
    """创建成功响应"""
    return success(data, message, status="created"), 201


def updated(data: Any = None, message: str = "更新成功") -> tuple:
    """更新成功响应"""
    return success(data, message, status="updated")


def deleted(message: str = "删除成功") -> tuple:
    """删除成功响应"""
    return success(message=message, status="deleted")


def not_found(message: str = "资源不存在") -> tuple:
    """404 响应"""
    return error(message, 404, "NOT_FOUND")


def unauthorized(message: str = "未授权") -> tuple:
    """401 响应"""
    return error(message, 401, "UNAUTHORIZED")


def forbidden(message: str = "禁止访问") -> tuple:
    """403 响应"""
    return error(message, 403, "FORBIDDEN")


def bad_request(message: str = "请求参数错误") -> tuple:
    """400 响应"""
    return error(message, 400, "BAD_REQUEST")


def server_error(message: str = "服务器内部错误") -> tuple:
    """500 响应"""
    return error(message, 500, "SERVER_ERROR")


class ApiResponse:
    """
    API 响应构建器
    
    使用示例:
        @app.route('/api/users')
        def get_users():
            users = get_all_users()
            return ApiResponse.success(users, "获取用户列表成功")
            
        @app.route('/api/users/<int:id>')
        def get_user(id):
            user = get_user_by_id(id)
            if not user:
                return ApiResponse.not_found("用户不存在")
            return ApiResponse.success(user)
    """
    
    @staticmethod
    def success(data: Any = None, message: str = "操作成功", **kwargs):
        return success(data, message, **kwargs)
    
    @staticmethod
    def error(message: str = "操作失败", code: int = 400, error_code: str = None):
        return error(message, code, error_code)
    
    @staticmethod
    def paginated(items: List, total: int, page: int = 1, page_size: int = 20, **kwargs):
        return paginated(items, total, page, page_size, **kwargs)
    
    @staticmethod
    def created(data: Any = None, message: str = "创建成功"):
        return created(data, message)
    
    @staticmethod
    def updated(data: Any = None, message: str = "更新成功"):
        return updated(data, message)
    
    @staticmethod
    def deleted(message: str = "删除成功"):
        return deleted(message)
    
    @staticmethod
    def not_found(message: str = "资源不存在"):
        return not_found(message)
    
    @staticmethod
    def unauthorized(message: str = "未授权"):
        return unauthorized(message)
    
    @staticmethod
    def forbidden(message: str = "禁止访问"):
        return forbidden(message)
    
    @staticmethod
    def bad_request(message: str = "请求参数错误"):
        return bad_request(message)
    
    @staticmethod
    def server_error(message: str = "服务器内部错误"):
        return server_error(message)