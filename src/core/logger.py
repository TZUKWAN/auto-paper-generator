# -*- coding: utf-8 -*-
"""
日志系统
提供统一的日志记录和查看功能
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional
import sys


class Logger:
    """日志管理器"""

    def __init__(self, name: str = "BusinessPlan", log_dir: str = None):
        """
        初始化日志管理器
        
        Args:
            name: 日志器名称
            log_dir: 日志目录，默认为当前目录下的logs
        """
        self.name = name
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "logs"
        
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建日志器
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)
        
        # 避免重复添加处理器
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """设置日志处理器"""
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # 文件处理器 - 所有日志
        log_file = self.log_dir / f"{self.name}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        self.logger.addHandler(file_handler)
        
        # 文件处理器 - 错误日志
        error_log_file = self.log_dir / f"{self.name}_error.log"
        error_handler = logging.FileHandler(error_log_file, encoding='utf-8')
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        self.logger.addHandler(error_handler)

    def debug(self, message: str):
        """调试日志"""
        self.logger.debug(message)

    def info(self, message: str):
        """信息日志"""
        self.logger.info(message)

    def warning(self, message: str):
        """警告日志"""
        self.logger.warning(message)

    def error(self, message: str):
        """错误日志"""
        self.logger.error(message)

    def critical(self, message: str):
        """严重错误日志"""
        self.logger.critical(message)

    def get_logs(self, level: str = "INFO", lines: int = 100) -> list:
        """
        获取日志内容
        
        Args:
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            lines: 读取的行数
            
        Returns:
            日志行列表
        """
        log_file = self.log_dir / f"{self.name}.log"
        if not log_file.exists():
            return []
        
        logs = []
        with open(log_file, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            recent_lines = all_lines[-lines:] if lines else all_lines
            
            for line in recent_lines:
                if level.upper() in line or level.upper() == "ALL":
                    logs.append(line.strip())
        
        return logs

    def clear_logs(self):
        """清空日志文件"""
        log_file = self.log_dir / f"{self.name}.log"
        error_log_file = self.log_dir / f"{self.name}_error.log"
        
        for file in [log_file, error_log_file]:
            if file.exists():
                with open(file, 'w', encoding='utf-8') as f:
                    f.write('')
        
        self.info("日志已清空")


class LogViewer:
    """日志查看器（用于GUI显示）"""

    def __init__(self, logger: Logger):
        """
        初始化日志查看器
        
        Args:
            logger: Logger实例
        """
        self.logger = logger

    def get_recent_logs(self, count: int = 50, filter_level: str = None) -> list:
        """
        获取最近的日志
        
        Args:
            count: 日志条数
            filter_level: 过滤级别
            
        Returns:
            格式化的日志列表
        """
        logs = self.logger.get_logs(lines=count)
        
        if filter_level:
            logs = [log for log in logs if filter_level.upper() in log]
        
        return logs

    def format_log_entry(self, log: str) -> dict:
        """
        格式化单条日志
        
        Args:
            log: 日志字符串
            
        Returns:
            格式化的字典
        """
        try:
            parts = log.split(' - ', 3)
            if len(parts) >= 4:
                return {
                    'timestamp': parts[0],
                    'name': parts[1],
                    'level': parts[2],
                    'message': parts[3]
                }
        except:
            pass
        
        return {
            'timestamp': '',
            'name': self.logger.name,
            'level': 'INFO',
            'message': log
        }


# 全局日志器实例
_global_logger = None


def get_logger(name: str = "BusinessPlan") -> Logger:
    """
    获取全局日志器实例
    
    Args:
        name: 日志器名称
        
    Returns:
        Logger实例
    """
    global _global_logger
    if _global_logger is None:
        _global_logger = Logger(name)
    return _global_logger


def log_debug(message: str):
    """快捷方式：调试日志"""
    get_logger().debug(message)


def log_info(message: str):
    """快捷方式：信息日志"""
    get_logger().info(message)


def log_warning(message: str):
    """快捷方式：警告日志"""
    get_logger().warning(message)


def log_error(message: str):
    """快捷方式：错误日志"""
    get_logger().error(message)


def log_critical(message: str):
    """快捷方式：严重错误日志"""
    get_logger().critical(message)
