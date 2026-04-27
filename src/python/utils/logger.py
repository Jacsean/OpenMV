#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理器

提供统一的日志输出控制，支持两种模式：
- NORMAL: 仅输出正常日志（启动信息、提示、警告、错误）
- DEBUG: 输出所有日志（包括详细调试信息）

使用方式：
    from utils.logger import logger
    
    # 正常日志（始终输出）
    logger.info("应用启动成功")
    logger.warning("插件加载失败")
    logger.error("严重错误")
    
    # 调试日志（仅在DEBUG模式下输出）
    logger.debug("详细调试信息")
    logger.debug_trace("事件过滤器安装完成", widget_count=10)
"""

import os
import sys
from enum import Enum
from datetime import datetime


class LogLevel(Enum):
    """日志级别枚举"""
    NORMAL = 1  # 正常模式：仅输出关键信息
    DEBUG = 2   # 调试模式：输出所有信息


class Logger:
    """
    统一日志管理器
    
    特性：
    - 通过环境变量 LOG_LEVEL 控制输出级别
    - 支持彩色终端输出（Windows/Linux/macOS）
    - 自动添加时间戳和级别标识
    - 调试日志可携带额外上下文信息
    """
    
    def __init__(self, level=None):
        """
        初始化日志管理器
        
        Args:
            level: 日志级别，None时从环境变量读取
        """
        if level is None:
            # 从环境变量读取，默认为NORMAL
            env_level = os.getenv('LOG_LEVEL', 'NORMAL').upper()
            self.level = LogLevel.DEBUG if env_level == 'DEBUG' else LogLevel.NORMAL
        else:
            self.level = level
        
        # ANSI颜色代码（Windows 10+ 和 Unix系统支持）
        self.colors = {
            'INFO': '\033[92m',     # 绿色
            'WARNING': '\033[93m',  # 黄色
            'ERROR': '\033[91m',    # 红色
            'DEBUG': '\033[36m',    # 青色
            'RESET': '\033[0m'      # 重置
        }
        
        # 检测是否支持彩色输出
        self.use_color = sys.platform != 'win32' or os.getenv('TERM')
    
    def _format_message(self, level, message, **kwargs):
        """
        格式化日志消息
        
        Args:
            level: 日志级别字符串
            message: 消息内容
            **kwargs: 额外的上下文信息（仅DEBUG模式有效）
            
        Returns:
            str: 格式化后的消息
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 构建基础消息
        formatted = f"[{timestamp}] [{level}] {message}"
        
        # DEBUG模式下附加上下文信息
        if kwargs and self.level == LogLevel.DEBUG:
            context = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
            formatted += f" | {context}"
        
        # 添加颜色
        if self.use_color and level in self.colors:
            formatted = f"{self.colors[level]}{formatted}{self.colors['RESET']}"
        
        return formatted
    
    def info(self, message):
        """
        输出正常信息（始终显示）
        
        Args:
            message: 信息内容
        """
        print(self._format_message('INFO', message))
    
    def warning(self, message):
        """
        输出警告信息（始终显示）
        
        Args:
            message: 警告内容
        """
        print(self._format_message('WARNING', message))
    
    def error(self, message):
        """
        输出错误信息（始终显示）
        
        Args:
            message: 错误内容
        """
        print(self._format_message('ERROR', message))
    
    def success(self, message):
        """
        输出成功信息（始终显示）
        
        Args:
            message: 成功内容
        """
        print(self._format_message('INFO', f"✅ {message}"))
    
    def debug(self, message, **kwargs):
        """
        输出调试信息（仅DEBUG模式显示）
        
        Args:
            message: 调试内容
            **kwargs: 额外的上下文信息
        """
        if self.level == LogLevel.DEBUG:
            print(self._format_message('DEBUG', message, **kwargs))
    
    def debug_trace(self, message, **kwargs):
        """
        输出详细的调试追踪信息（仅DEBUG模式显示）
        
        Args:
            message: 追踪内容
            **kwargs: 详细的上下文数据
        """
        if self.level == LogLevel.DEBUG:
            print(self._format_message('DEBUG', f"🔍 {message}", **kwargs))
    
    def separator(self, char='=', length=60):
        """
        输出分隔线（始终显示）
        
        Args:
            char: 分隔字符
            length: 长度
        """
        print(char * length)
    
    def section(self, title):
        """
        输出章节标题（始终显示）
        
        Args:
            title: 标题内容
        """
        self.separator()
        self.info(title)
        self.separator()


# 全局单例
logger = Logger()


def set_log_level(level):
    """
    动态设置日志级别
    
    Args:
        level: LogLevel枚举值或字符串('NORMAL'/'DEBUG')
    """
    global logger
    if isinstance(level, str):
        level = LogLevel.DEBUG if level.upper() == 'DEBUG' else LogLevel.NORMAL
    logger = Logger(level)
    logger.info(f"日志级别已设置为: {level.name}")


# 便捷函数（向后兼容旧的print语句）
def log_info(message):
    """兼容旧代码的info日志"""
    logger.info(message)


def log_warning(message):
    """兼容旧代码的warning日志"""
    logger.warning(message)


def log_error(message):
    """兼容旧代码的error日志"""
    logger.error(message)


def log_debug(message, **kwargs):
    """兼容旧代码的debug日志"""
    logger.debug(message, **kwargs)
