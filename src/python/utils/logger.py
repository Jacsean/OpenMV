#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理器

提供统一的日志输出控制，支持两种模式：
- NORMAL: 仅输出正常日志（启动信息、提示、警告、错误）
- DEBUG: 关闭正常日志，仅输出需要调试模块的调试信息

使用方式：
    from utils.logger import logger
    
    # 正常日志（仅在NORMAL模式输出）
    logger.info("应用启动成功")
    logger.warning("插件加载失败")
    logger.error("严重错误")
    
    # 调试日志（仅在DEBUG模式输出）
    logger.debug("详细调试信息", module="plugin_loader")
    logger.debug_trace("事件过滤器安装完成", widget_count=10, module="ui_manager")
"""

import os
import sys
from enum import Enum
from datetime import datetime
from typing import List, Optional


class LogLevel(Enum):
    """日志级别枚举"""
    NORMAL = 1  # 正常模式：仅输出关键信息
    DEBUG = 2   # 调试模式：仅输出指定模块的调试信息


class LogHandler:
    """
    日志处理器基类
    
    子类需要实现 handle() 方法来处理日志消息
    """
    def handle(self, level: str, message: str, formatted: str, module: Optional[str] = None):
        """
        处理日志消息
        
        Args:
            level: 日志级别字符串 (INFO/WARNING/ERROR/DEBUG)
            message: 原始消息内容
            formatted: 格式化后的完整消息（包含时间戳等）
            module: 模块名称（用于过滤）
        """
        raise NotImplementedError


class ConsoleHandler(LogHandler):
    """
    控制台日志处理器
    
    将日志输出到标准输出（终端）
    """
    def __init__(self, use_color=True):
        """
        初始化控制台处理器
        
        Args:
            use_color: 是否启用彩色输出
        """
        self.use_color = use_color
        self.colors = {
            'INFO': '\033[92m',     # 绿色
            'WARNING': '\033[93m',  # 黄色
            'ERROR': '\033[91m',    # 红色
            'DEBUG': '\033[36m',    # 青色
            'RESET': '\033[0m'      # 重置
        }
    
    def handle(self, level: str, message: str, formatted: str, module: Optional[str] = None):
        """输出到控制台"""
        if self.use_color and level in self.colors:
            colored = f"{self.colors[level]}{formatted}{self.colors['RESET']}"
            print(colored)
        else:
            print(formatted)


class Logger:
    """
    统一日志管理器
    
    特性：
    - NORMAL模式：仅输出INFO/WARNING/ERROR/SUCCESS级别的关键信息
    - DEBUG模式：关闭正常日志，仅输出指定模块的DEBUG信息
    - 通过环境变量 LOG_LEVEL 和 DEBUG_MODULES 控制
    - 支持多Handler（控制台、UI面板等）
    - 自动添加时间戳和级别标识
    """
    
    def __init__(self, level=None, debug_modules=None):
        """
        初始化日志管理器
        
        Args:
            level: 日志级别，None时从环境变量读取
            debug_modules: 调试模块列表，None时从环境变量读取
        """
        if level is None:
            # 从环境变量读取，默认为NORMAL
            env_level = os.getenv('LOG_LEVEL', 'NORMAL').upper()
            self.level = LogLevel.DEBUG if env_level == 'DEBUG' else LogLevel.NORMAL
        else:
            self.level = level
        
        if debug_modules is None:
            # 从环境变量读取调试模块列表（逗号分隔）
            env_modules = os.getenv('DEBUG_MODULES', '')
            self.debug_modules = [m.strip() for m in env_modules.split(',') if m.strip()] if env_modules else []
        else:
            self.debug_modules = debug_modules
        
        # Handler列表
        self.handlers: List[LogHandler] = []
        
        # 默认添加控制台Handler
        self.add_handler(ConsoleHandler())
    
    def add_handler(self, handler: LogHandler):
        """
        添加日志处理器
        
        Args:
            handler: LogHandler实例
        """
        self.handlers.append(handler)
    
    def _format_message(self, level, message, module=None, **kwargs):
        """
        格式化日志消息
        
        Args:
            level: 日志级别字符串
            message: 消息内容
            module: 模块名称
            **kwargs: 额外的上下文信息
            
        Returns:
            str: 格式化后的消息
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        
        # 构建基础消息
        if module:
            formatted = f"[{timestamp}] [{level}] [{module}] {message}"
        else:
            formatted = f"[{timestamp}] [{level}] {message}"
        
        # DEBUG模式下附加上下文信息
        if kwargs and self.level == LogLevel.DEBUG:
            context = ', '.join([f"{k}={v}" for k, v in kwargs.items()])
            formatted += f" | {context}"
        
        return formatted
    
    def _should_log(self, level: str, module: Optional[str] = None) -> bool:
        """
        判断是否应该输出该日志
        
        Args:
            level: 日志级别
            module: 模块名称
            
        Returns:
            bool: 是否应该输出
        """
        if self.level == LogLevel.NORMAL:
            # NORMAL模式：仅输出非DEBUG级别的日志
            return level != 'DEBUG'
        else:
            # DEBUG模式：仅输出指定模块的DEBUG日志，或其他级别的日志
            if level == 'DEBUG':
                # 检查模块是否在调试列表中
                if not self.debug_modules:
                    # 如果未指定模块，输出所有DEBUG日志
                    return True
                return module in self.debug_modules
            else:
                # DEBUG模式下也输出WARNING/ERROR（便于发现问题）
                return level in ['WARNING', 'ERROR']
    
    def _log(self, level, message, module=None, **kwargs):
        """
        内部日志分发方法
        
        Args:
            level: 日志级别
            message: 消息内容
            module: 模块名称
            **kwargs: 额外参数
        """
        # 检查是否应该输出
        if not self._should_log(level, module):
            return
        
        formatted = self._format_message(level, message, module, **kwargs)
        for handler in self.handlers:
            try:
                handler.handle(level, message, formatted, module)
            except Exception:
                pass
    
    def info(self, message, module=None):
        """
        输出正常信息（NORMAL模式显示）
        
        Args:
            message: 信息内容
            module: 模块名称（可选）
        """
        self._log('INFO', message, module)
    
    def warning(self, message, module=None):
        """
        输出警告信息（始终显示）
        
        Args:
            message: 警告内容
            module: 模块名称（可选）
        """
        self._log('WARNING', message, module)
    
    def error(self, message, module=None):
        """
        输出错误信息（始终显示）
        
        Args:
            message: 错误内容
            module: 模块名称（可选）
        """
        self._log('ERROR', message, module)
    
    def success(self, message, module=None):
        """
        输出成功信息（NORMAL模式显示）
        
        Args:
            message: 成功内容
            module: 模块名称（可选）
        """
        self._log('INFO', f"✅ {message}", module)
    
    def debug(self, message, module=None, **kwargs):
        """
        输出调试信息（仅DEBUG模式且模块匹配时显示）
        
        Args:
            message: 调试内容
            module: 模块名称（必需）
            **kwargs: 额外的上下文信息
        """
        self._log('DEBUG', message, module, **kwargs)
    
    def debug_trace(self, message, module=None, **kwargs):
        """
        输出详细的调试追踪信息（仅DEBUG模式且模块匹配时显示）
        
        Args:
            message: 追踪内容
            module: 模块名称（必需）
            **kwargs: 详细的上下文数据
        """
        self._log('DEBUG', f"🔍 {message}", module, **kwargs)
    
    def separator(self, char='=', length=60):
        """
        输出分隔线（NORMAL模式显示）
        
        Args:
            char: 分隔字符
            length: 长度
        """
        if self.level == LogLevel.NORMAL:
            print(char * length)
    
    def section(self, title, module=None):
        """
        输出章节标题（NORMAL模式显示）
        
        Args:
            title: 标题内容
            module: 模块名称（可选）
        """
        if self.level == LogLevel.NORMAL:
            self.separator()
            self.info(title, module)
            self.separator()


# 全局单例
logger = Logger()


def set_log_level(level, debug_modules=None):
    """
    动态设置日志级别和调试模块
    
    Args:
        level: LogLevel枚举值或字符串('NORMAL'/'DEBUG')
        debug_modules: 调试模块列表（仅DEBUG模式有效）
    """
    global logger
    if isinstance(level, str):
        level = LogLevel.DEBUG if level.upper() == 'DEBUG' else LogLevel.NORMAL
    
    if debug_modules is None:
        # 从环境变量读取
        env_modules = os.getenv('DEBUG_MODULES', '')
        debug_modules = [m.strip() for m in env_modules.split(',') if m.strip()] if env_modules else []
    
    # 直接修改现有logger对象的属性，而不是创建新对象
    logger.level = level
    logger.debug_modules = debug_modules
    
    # 使用print直接输出，避免被过滤
    timestamp = datetime.now().strftime('%H:%M:%S')
    if level == LogLevel.DEBUG:
        modules_str = ', '.join(debug_modules) if debug_modules else '全部'
        print(f"[{timestamp}] [INFO] 日志级别已设置为: DEBUG (调试模块: {modules_str})")
    else:
        print(f"[{timestamp}] [INFO] 日志级别已设置为: NORMAL")


# 便捷函数（向后兼容旧的print语句）
def log_info(message, module=None):
    """兼容旧代码的info日志"""
    logger.info(message, module)


def log_warning(message, module=None):
    """兼容旧代码的warning日志"""
    logger.warning(message, module)


def log_error(message, module=None):
    """兼容旧代码的error日志"""
    logger.error(message, module)


def log_debug(message, module=None, **kwargs):
    """兼容旧代码的debug日志"""
    logger.debug(message, module, **kwargs)
