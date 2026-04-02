"""
📋 统一日志配置
所有模块统一使用 logging，不再使用 print()。
"""
import os
import sys
import logging


def setup_logging(level: str = None):
    """
    配置全局日志系统。
    level: DEBUG / INFO / WARNING / ERROR（默认从环境变量 LOG_LEVEL 读取，否则 INFO）
    """
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO").upper()

    numeric_level = getattr(logging, level, logging.INFO)

    # 确保 stdout 使用 UTF-8 编码
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")

    # 统一格式
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台 handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # 根 logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # 清除已有 handler，避免重复
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # 抑制第三方库的冗余日志
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    root_logger.info(f"日志系统已初始化（级别: {level}）")
    return root_logger
