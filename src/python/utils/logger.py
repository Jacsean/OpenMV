#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志管理系统（重构版）

提供统一的日志输出控制，支持：
- 日志级别：DEBUG/INFO/WARNING/ERROR/CRITICAL
- 异步文件写入：避免阻塞主线程
- 日志轮转：自动清理过期日志
- 结构化日志：JSON格式支持
- 多Handler：控制台、UI面板、文件

使用方式：
    from utils.logger import logger

    # 日志输出
    logger.debug("调试信息")
    logger.info("普通信息")
    logger.warning("警告信息")
    logger.error("错误信息")
    logger.success("成功信息")

    # 带模块
    logger.info("插件加载完成", module="plugin_manager")

    # 带上下文
    logger.debug("节点处理", module="graph", node_count=10, duration=0.05)
"""

import os
import sys
import json
import time
import queue
import threading
import inspect
from enum import IntEnum
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor


class LogLevel(IntEnum):
    """日志级别枚举（数值越小级别越高）"""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50


class LogLevelLegacy:
    """兼容旧版本的日志级别"""
    NORMAL = LogLevel.INFO
    DEBUG = LogLevel.DEBUG


class LogRecord:
    """
    日志记录

    包含日志的所有信息
    """

    def __init__(
        self,
        level: LogLevel,
        message: str,
        module: Optional[str] = None,
        timestamp: Optional[datetime] = None,
        context: Optional[Dict[str, Any]] = None,
        exc_info: Optional[tuple] = None,
        func_name: Optional[str] = None,
        line_number: Optional[int] = None
    ):
        self.level = level
        self.message = message
        self.module = module
        self.timestamp = timestamp or datetime.now()
        self.context = context or {}
        self.exc_info = exc_info
        self.func_name = func_name
        self.line_number = line_number

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            'level': self.level.name,
            'message': self.message,
            'module': self.module,
            'func_name': self.func_name,
            'line_number': self.line_number,
            'context': self.context
        }

    def to_json(self) -> str:
        """转换为JSON字符串"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class LogHandler:
    """
    日志处理器基类
    """

    def emit(self, record: LogRecord):
        """
        发送日志记录

        Args:
            record: 日志记录
        """
        raise NotImplementedError

    def flush(self):
        """刷新缓冲区"""
        pass

    def close(self):
        """关闭处理器"""
        pass


class ConsoleHandler(LogHandler):
    """
    控制台日志处理器

    将日志输出到标准输出（终端），支持彩色输出
    """

    def __init__(self, use_color: bool = True):
        self.use_color = use_color
        self.colors = {
            LogLevel.DEBUG: '\033[36m',     # 青色
            LogLevel.INFO: '\033[92m',     # 绿色
            LogLevel.WARNING: '\033[93m',  # 黄色
            LogLevel.ERROR: '\033[91m',    # 红色
            LogLevel.CRITICAL: '\033[1;31m',  # 粗体红色
            'RESET': '\033[0m'
        }
        self.success_color = '\033[92m'

    def emit(self, record: LogRecord):
        """输出到控制台"""
        timestamp = record.timestamp.strftime('%H:%M:%S')

        func_part = ""
        if record.func_name:
            if record.line_number:
                func_part = f"[{record.func_name}][{record.line_number}]"
            else:
                func_part = f"[{record.func_name}]"

        if record.module:
            formatted = f"[{timestamp}] [{record.level.name:<8}] [{record.module}] {func_part} {record.message}"
        else:
            formatted = f"[{timestamp}] [{record.level.name:<8}] {func_part} {record.message}"

        if record.context:
            context_str = ', '.join([f"{k}={v}" for k, v in record.context.items()])
            formatted += f" | {context_str}"

        if self.use_color and record.level in self.colors:
            colored = f"{self.colors[record.level]}{formatted}{self.colors['RESET']}"
            print(colored, flush=True)
        else:
            print(formatted, flush=True)


class FileHandler(LogHandler):
    """
    文件日志处理器

    支持日志轮转和异步写入
    """

    def __init__(
        self,
        log_dir: str = None,
        filename: str = "app.log",
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5,
        encoding: str = 'utf-8'
    ):
        if log_dir is None:
            log_dir = Path(__file__).parent.parent / "workspace" / "logs"
        else:
            log_dir = Path(log_dir)

        log_dir.mkdir(parents=True, exist_ok=True)

        self.log_dir = log_dir
        self.filename = filename
        self.max_bytes = max_bytes
        self.backup_count = backup_count
        self.encoding = encoding
        self.file_lock = threading.Lock()

        self._current_file = log_dir / filename
        self._write_buffer = []
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix='log_file_writer')

    def emit(self, record: LogRecord):
        """异步写入文件"""
        self._executor.submit(self._write, record)

    def _write(self, record: LogRecord):
        """写入日志到文件"""
        with self.file_lock:
            try:
                self._check_rotation()

                log_line = record.to_json() + '\n'

                with open(self._current_file, 'a', encoding=self.encoding) as f:
                    f.write(log_line)

            except Exception as e:
                print(f"日志写入失败: {e}", flush=True)

    def _check_rotation(self):
        """检查是否需要日志轮转"""
        if not self._current_file.exists():
            return

        file_size = self._current_file.stat().st_size

        if file_size >= self.max_bytes:
            self._rotate()

    def _rotate(self):
        """执行日志轮转"""
        # 删除最旧的备份
        oldest_backup = self.log_dir / f"{self.filename}.{self.backup_count}"
        if oldest_backup.exists():
            oldest_backup.unlink()

        # 轮转现有备份
        for i in range(self.backup_count - 1, 0, -1):
            src = self.log_dir / f"{self.filename}.{i}"
            dst = self.log_dir / f"{self.filename}.{i + 1}"
            if src.exists():
                src.rename(dst)

        # 重命名当前文件为.1
        backup = self.log_dir / f"{self.filename}.1"
        if self._current_file.exists():
            self._current_file.rename(backup)

    def flush(self):
        """刷新缓冲区"""
        pass

    def close(self):
        """关闭处理器"""
        self._executor.shutdown(wait=True)


class QtLogHandler(LogHandler):
    """
    Qt界面日志处理器

    将日志输出到Qt界面（如QTextEdit/QTextBrowser）
    
    注意：此Handler使用QTimer实现线程安全的UI更新
    """

    def __init__(self, text_widget=None, max_lines: int = 1000):
        self.text_widget = text_widget
        self.max_lines = max_lines
        self._pending_logs = []
        self._timer = None

    def emit(self, record: LogRecord):
        """将日志加入待处理队列"""
        if not self.text_widget:
            return
            
        # 格式化日志消息
        timestamp = record.timestamp.strftime('%H:%M:%S')

        func_part = ""
        if record.func_name:
            if record.line_number:
                func_part = f"[{record.func_name}][{record.line_number}]"
            else:
                func_part = f"[{record.func_name}]"

        if record.module:
            formatted = f"[{timestamp}] [{record.level.name:<8}] [{record.module}] {func_part} {record.message}"
        else:
            formatted = f"[{timestamp}] [{record.level.name:<8}] {func_part} {record.message}"

        if record.context:
            context_str = ', '.join([f"{k}={v}" for k, v in record.context.items()])
            formatted += f" | {context_str}"

        # 直接在主线程中追加（如果text_widget存在）
        try:
            self._append_safe(formatted)
        except Exception:
            pass

    def _append_safe(self, text: str):
        """线程安全地追加日志到Qt组件"""
        if not self.text_widget:
            return

        try:
            # 尝试使用QMetaObject.invokeMethod确保线程安全
            try:
                from PySide2.QtCore import QMetaObject, Qt, Q_ARG
                
                # 先追加文本
                QMetaObject.invokeMethod(
                    self.text_widget,
                    "append",
                    Qt.QueuedConnection,
                    Q_ARG(str, text)
                )
                
                # 延迟滚动到底部（确保append已完成）
                from PySide2.QtCore import QTimer
                QTimer.singleShot(10, self._scroll_to_bottom)
                
            except ImportError:
                # 如果PySide2不可用，直接追加（可能在测试环境）
                self.text_widget.append(text)
                self._scroll_to_bottom()

            # 限制行数
            self._limit_lines()

        except Exception as e:
            print(f"Qt log output failed: {e}", flush=True)

    def _scroll_to_bottom(self):
        """滚动到日志底部"""
        if not self.text_widget:
            return
        try:
            scrollbar = self.text_widget.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception:
            pass

    def _limit_lines(self):
        """限制日志行数，删除旧日志防止内存溢出"""
        if not self.text_widget:
            return

        try:
            document = self.text_widget.document()
            line_count = document.blockCount()
            
            if line_count > self.max_lines:
                # 删除多余的旧日志（保留后 max_lines 行）
                cursor = self.text_widget.textCursor()
                cursor.movePosition(cursor.Start)
                
                # 计算需要删除的行数
                lines_to_delete = line_count - self.max_lines
                
                for _ in range(lines_to_delete):
                    cursor.select(cursor.LineUnderCursor)
                    cursor.removeSelectedText()
                    cursor.deleteChar()  # 删除换行符
                    
        except Exception:
            pass

    def clear(self):
        """清空日志面板（仅清空UI显示，不影响终端和文件输出）"""
        if self.text_widget:
            try:
                self.text_widget.clear()
            except Exception:
                pass

    def flush(self):
        """刷新"""
        pass

    def close(self):
        """关闭"""
        pass


class Logger:
    """
    统一日志管理器

    特性：
    - 日志级别控制：DEBUG/INFO/WARNING/ERROR/CRITICAL
    - 模块级别过滤
    - 多Handler支持（控制台、文件、UI）
    - 异步文件写入
    - 日志轮转
    - 结构化日志
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True

        # 日志级别
        self.level = LogLevel.INFO
        self._level_name_map = {
            'DEBUG': LogLevel.DEBUG,
            'INFO': LogLevel.INFO,
            'WARNING': LogLevel.WARNING,
            'WARN': LogLevel.WARNING,
            'ERROR': LogLevel.ERROR,
            'CRITICAL': LogLevel.CRITICAL,
            'NORMAL': LogLevel.INFO,
        }

        # 模块级别过滤
        self._module_levels: Dict[str, LogLevel] = {}

        # Handler列表
        self.handlers: List[LogHandler] = []

        # 默认添加控制台Handler
        self.add_handler(ConsoleHandler())
        
        # 默认添加文件Handler（自动启用）
        try:
            file_handler = FileHandler()
            self.add_handler(file_handler)
            print(f"[OK] Log file enabled, saved to: {file_handler.log_dir / file_handler.filename}")
        except Exception as e:
            print(f"[WARN] File log init failed: {e}")

        # 从环境变量读取日志级别
        env_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        self.set_level(env_level)

    def add_handler(self, handler: LogHandler):
        """
        添加日志处理器

        Args:
            handler: LogHandler实例
        """
        self.handlers.append(handler)

    def remove_handler(self, handler: LogHandler):
        """
        移除日志处理器

        Args:
            handler: LogHandler实例
        """
        if handler in self.handlers:
            self.handlers.remove(handler)

    def set_level(self, level):
        """
        设置全局日志级别

        Args:
            level: 日志级别（字符串或LogLevel枚举）
        """
        if isinstance(level, str):
            level = self._level_name_map.get(level.upper(), LogLevel.INFO)

        self.level = level

    def set_module_level(self, module: str, level):
        """
        设置指定模块的日志级别

        Args:
            module: 模块名称
            level: 日志级别
        """
        if isinstance(level, str):
            level = self._level_name_map.get(level.upper(), LogLevel.INFO)

        self._module_levels[module] = level

    def _should_log(self, level: LogLevel, module: Optional[str] = None) -> bool:
        """
        判断是否应该输出该日志

        Args:
            level: 日志级别
            module: 模块名称

        Returns:
            bool: 是否应该输出
        """
        # 检查模块级别
        effective_level = self.level
        if module and module in self._module_levels:
            effective_level = self._module_levels[module]

        return level >= effective_level

    def _emit(self, level: LogLevel, message: str, module: Optional[str] = None, **kwargs):
        """
        内部日志发送方法

        Args:
            level: 日志级别
            message: 消息内容
            module: 模块名称
            **kwargs: 额外上下文信息
        """
        if not self._should_log(level, module):
            return

        func_name = None
        line_number = None

        try:
            stack = inspect.stack()
            for i in range(2, min(len(stack), 6)):
                frame = stack[i]
                if frame.function not in ['_emit', 'debug', 'info', 'warning', 'error', 'critical', 'success', 'exception', 'debug_trace']:
                    func_name = frame.function
                    line_number = frame.lineno
                    break
        except Exception:
            pass

        record = LogRecord(
            level=level,
            message=message,
            module=module,
            context=kwargs,
            func_name=func_name,
            line_number=line_number
        )

        for handler in self.handlers:
            try:
                handler.emit(record)
            except Exception:
                pass

    def debug(self, message: str, module: Optional[str] = None, **kwargs):
        """输出调试信息"""
        self._emit(LogLevel.DEBUG, message, module, **kwargs)

    def info(self, message: str, module: Optional[str] = None, **kwargs):
        """输出普通信息"""
        self._emit(LogLevel.INFO, message, module, **kwargs)

    def warning(self, message: str, module: Optional[str] = None, **kwargs):
        """输出警告信息"""
        self._emit(LogLevel.WARNING, message, module, **kwargs)

    def error(self, message: str, module: Optional[str] = None, **kwargs):
        """输出错误信息"""
        self._emit(LogLevel.ERROR, message, module, **kwargs)

    def critical(self, message: str, module: Optional[str] = None, **kwargs):
        """输出严重错误信息"""
        self._emit(LogLevel.CRITICAL, message, module, **kwargs)

    def success(self, message: str, module: Optional[str] = None, **kwargs):
        """输出成功信息（作为INFO级别）"""
        self._emit(LogLevel.INFO, f"✅ {message}", module, **kwargs)

    def exception(self, message: str, module: Optional[str] = None, **kwargs):
        """输出异常信息（自动包含堆栈）"""
        import traceback
        exc_info = sys.exc_info()
        kwargs['exc_info'] = ''.join(traceback.format_exception(*exc_info))
        self._emit(LogLevel.ERROR, f"❌ {message}", module, **kwargs)

    def debug_trace(self, message: str, module: Optional[str] = None, **kwargs):
        """输出详细的调试追踪信息"""
        self._emit(LogLevel.DEBUG, f"🔍 {message}", module, **kwargs)

    def section(self, title: str, module: Optional[str] = None):
        """
        输出章节标题

        Args:
            title: 标题内容
            module: 模块名称
        """
        self.info("=" * 60, module)
        self.info(title, module)
        self.info("=" * 60, module)

    def separator(self, char: str = '=', length: int = 60, module: Optional[str] = None):
        """
        输出分隔线

        Args:
            char: 分隔字符
            length: 长度
            module: 模块名称
        """
        self.info(char * length, module)

    def flush(self):
        """刷新所有Handler"""
        for handler in self.handlers:
            try:
                handler.flush()
            except Exception:
                pass

    def close(self):
        """关闭所有Handler"""
        for handler in self.handlers:
            try:
                handler.close()
            except Exception:
                pass


# 创建全局单例
logger = Logger()


def set_log_level(level, debug_modules=None):
    """
    动态设置日志级别

    Args:
        level: 日志级别（字符串或LogLevel枚举）
        debug_modules: 调试模块列表（已废弃，保留兼容性）
    """
    global logger
    logger.set_level(level)

    timestamp = datetime.now().strftime('%H:%M:%S')
    level_name = level if isinstance(level, str) else level.name
    print(f"[{timestamp}] [INFO] 日志级别已设置为: {level_name}", flush=True)


def get_logger() -> Logger:
    """获取日志管理器实例"""
    return logger


# 便捷函数（向后兼容）
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


__all__ = [
    'Logger',
    'logger',
    'LogLevel',
    'LogHandler',
    'ConsoleHandler',
    'FileHandler',
    'QtLogHandler',
    'LogRecord',
    'set_log_level',
    'get_logger',
    'log_info',
    'log_warning',
    'log_error',
    'log_debug'
]
