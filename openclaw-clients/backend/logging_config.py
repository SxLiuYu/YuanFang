#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一结构化日志配置
"""

import logging
import sys
from typing import Optional

# 尝试导入 colorlog，失败则使用普通格式
try:
    from colorlog import ColoredFormatter
    HAS_COLORLOG = True
except ImportError:
    HAS_COLORLOG = False


def setup_logging(log_level: str = "INFO", name: Optional[str] = None) -> None:
    """
    配置统一日志格式

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        name: 根日志器名称，默认 None 使用根日志器
    """
    # 转换日志级别
    level = getattr(logging, log_level.upper(), logging.INFO)

    # 定义日志格式
    if HAS_COLORLOG:
        log_format = (
            "%(asctime)s "
            "%(log_color)s%(levelname)-8s%(reset)s "
            "%(cyan)s%(name)s:%(lineno)d%(reset)s "
            "%(message)s"
        )
        formatter = ColoredFormatter(log_format)
    else:
        plain_format = (
            "%(asctime)s %(levelname)-8s %(name)s:%(lineno)d %(message)s"
        )
        formatter = logging.Formatter(plain_format)

    # 创建 处理器（控制台输出）
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # 获取根日志器
    root_logger = logging.getLogger(name)
    root_logger.setLevel(level)

    # 移除现有处理器避免重复
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 添加新处理器
    root_logger.addHandler(console_handler)

    # 设置第三方库的日志级别
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)

    root_logger.info(f"✅ 日志系统初始化完成，级别: {logging.getLevelName(level)}")


def get_logger(name: str) -> logging.Logger:
    """
    获取命名日志器

    Args:
        name: 日志器名称

    Returns:
        配置好的日志器实例
    """
    return logging.getLogger(name)
