"""
统一日志配置模块
提供标准的日志配置和获取方法
"""

import logging
import os
from datetime import datetime

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO').upper()
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
LOG_DIR = os.getenv('LOG_DIR', 'logs')

_initialized = False


def setup_logging(log_file=None):
    """
    初始化日志配置
    
    Args:
        log_file: 日志文件路径，默认为 logs/openclaw_YYYYMMDD.log
    """
    global _initialized
    
    if _initialized:
        return
    
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    if log_file is None:
        log_file = os.path.join(LOG_DIR, f'openclaw_{datetime.now().strftime("%Y%m%d")}.log')
    
    handlers = [
        logging.StreamHandler(),
        logging.FileHandler(log_file, encoding='utf-8')
    ]
    
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format=LOG_FORMAT,
        datefmt=LOG_DATE_FORMAT,
        handlers=handlers
    )
    
    _initialized = True
    logging.info("日志系统初始化完成")


def get_logger(name):
    """
    获取日志记录器
    
    Args:
        name: 模块名称，通常使用 __name__
    
    Returns:
        logging.Logger: 日志记录器实例
    """
    if not _initialized:
        setup_logging()
    return logging.getLogger(name)


class LogContext:
    """
    日志上下文管理器，用于临时修改日志级别
    """
    def __init__(self, logger, level):
        self.logger = logger
        self.level = level
        self.original_level = None
    
    def __enter__(self):
        self.original_level = self.logger.level
        self.logger.setLevel(self.level)
        return self.logger
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.logger.setLevel(self.original_level)


def log_function_call(func):
    """
    函数调用日志装饰器
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        logger.debug(f"调用函数: {func.__name__}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数 {func.__name__} 执行成功")
            return result
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行失败: {e}", exc_info=True)
            raise
    return wrapper


def log_api_request(method, url, params=None, data=None):
    """
    记录 API 请求
    """
    logger = get_logger('api')
    logger.info(f"API请求: {method} {url}")
    if params:
        logger.debug(f"参数: {params}")
    if data:
        logger.debug(f"数据: {data}")


def log_api_response(status_code, response_time, success=True):
    """
    记录 API 响应
    """
    logger = get_logger('api')
    level = logging.INFO if success else logging.WARNING
    logger.log(level, f"API响应: {status_code}, 耗时: {response_time:.2f}ms")