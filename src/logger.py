"""
日志管理模块
根据 config.LOG 设置，决定是否输出日志到文件和控制台
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from config import LOG, LOG_DIR, LOG_LEVEL


class LoggerManager:
    """日志管理器 - 单例模式"""
    
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
            cls._instance._init_logger()
        return cls._instance
    
    def _init_logger(self):
        """初始化日志系统"""
        self._logger = logging.getLogger("RAG_System")
        self._logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
        
        # 清除旧的 handler
        self._logger.handlers.clear()
        
        if LOG:
            # 创建日志目录
            Path(LOG_DIR).mkdir(parents=True, exist_ok=True)
            
            # 日志文件名（带时间戳）
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(LOG_DIR, f"rag_{timestamp}.log")
            
            # 文件 handler（记录详细信息）
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self._logger.addHandler(file_handler)
            
            # 控制台 handler（仅输出 INFO 及以上）
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            self._logger.addHandler(console_handler)
            
            self._logger.info(f"✅ 日志系统已初始化，文件位置: {log_file}")
        else:
            # 若 LOG=False，只添加 NullHandler（忽略所有输出）
            self._logger.addHandler(logging.NullHandler())
    
    @property
    def logger(self):
        """获取 logger 对象"""
        return self._logger
    
    @classmethod
    def get_logger(cls):
        """获取 logger 实例"""
        return cls().logger


# 全局 logger 对象
logger = LoggerManager.get_logger()


def debug(msg, *args, **kwargs):
    """DEBUG 级别日志"""
    logger.debug(msg, *args, **kwargs)


def info(msg, *args, **kwargs):
    """INFO 级别日志"""
    logger.info(msg, *args, **kwargs)


def warning(msg, *args, **kwargs):
    """WARNING 级别日志"""
    logger.warning(msg, *args, **kwargs)


def error(msg, *args, **kwargs):
    """ERROR 级别日志"""
    logger.error(msg, *args, **kwargs)


def critical(msg, *args, **kwargs):
    """CRITICAL 级别日志"""
    logger.critical(msg, *args, **kwargs)


# 便捷别名
warn = warning

__all__ = ['logger', 'debug', 'info', 'warning', 'warn', 'error', 'critical']
