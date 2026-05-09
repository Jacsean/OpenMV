#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Qt日志处理器

将日志消息转发到Qt UI组件（QTextBrowser）
用于在应用界面中实时显示日志

注意：此文件保持向后兼容性，新代码建议直接使用 utils.logger.QtLogHandler
"""

from typing import Optional
from PySide2 import QtCore, QtWidgets
from utils.logger import LogHandler as BaseLogHandler
from utils.logger import LogRecord, LogLevel


class QtLogHandler(BaseLogHandler):
    """
    Qt日志处理器
    
    将日志消息发送到QTextBrowser组件，实现UI中的日志显示
    
    兼容性说明：
    - 支持新的 emit(LogRecord) 接口（推荐使用）
    - 保持向后兼容旧的 handle() 接口
    """
    
    def __init__(self, text_browser: QtWidgets.QTextBrowser):
        """
        初始化Qt日志处理器
        
        Args:
            text_browser: QTextBrowser实例，用于显示日志
        """
        self.text_browser = text_browser
        
        # HTML颜色映射（用于富文本显示）
        self.html_colors = {
            'INFO': '#2ecc71',      # 绿色
            'WARNING': '#f39c12',   # 橙色
            'ERROR': '#e74c3c',     # 红色
            'DEBUG': '#3498db',     # 蓝色
            'CRITICAL': '#ff0000',  # 红色粗体
        }
        
        # 最大日志行数（防止内存溢出）
        self.max_lines = 1000
    
    def emit(self, record: LogRecord):
        """
        新的日志处理接口（推荐）
        
        Args:
            record: 日志记录对象
        """
        if self.text_browser:
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
            
            # 使用QMetaObject.invokeMethod确保线程安全
            QtCore.QMetaObject.invokeMethod(
                self,
                "_append_log_safe",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, formatted)
            )
    
    def handle(self, level: str, message: str, formatted: str, module: Optional[str] = None):
        """
        旧的日志处理接口（保持向后兼容）
        
        Args:
            level: 日志级别字符串 (INFO/WARNING/ERROR/DEBUG)
            message: 原始消息内容
            formatted: 格式化后的完整消息
            module: 模块名称（用于过滤）
        """
        if self.text_browser:
            QtCore.QMetaObject.invokeMethod(
                self,
                "_append_log_safe",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(str, formatted)
            )
    
    @QtCore.Slot(str)
    def _append_log_safe(self, formatted_text: str):
        """
        安全地追加日志到文本浏览器（槽函数）
        
        Args:
            formatted_text: 格式化后的日志文本
        """
        if not self.text_browser:
            return
        
        # 转换为HTML格式（带颜色）
        html_text = self._format_as_html(formatted_text)
        
        # 追加到文本浏览器
        self.text_browser.append(html_text)
        
        # 自动滚动到底部
        scrollbar = self.text_browser.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # 限制日志行数（防止内存溢出）
        self._limit_log_lines()
    
    def _format_as_html(self, text: str) -> str:
        """
        将纯文本日志转换为HTML格式（带颜色）
        
        Args:
            text: 纯文本日志
            
        Returns:
            str: HTML格式的日志
        """
        # 提取日志级别
        level = 'INFO'
        if '[WARNING]' in text:
            level = 'WARNING'
        elif '[ERROR]' in text:
            level = 'ERROR'
        elif '[DEBUG]' in text:
            level = 'DEBUG'
        elif '[CRITICAL]' in text:
            level = 'CRITICAL'
        
        # 获取颜色
        color = self.html_colors.get(level, '#000000')
        
        # 转换为等宽字体并着色
        return f'<span style="color: {color}; font-family: Consolas, monospace;">{text}</span>'
    
    def _limit_log_lines(self):
        """
        限制日志行数，删除旧日志
        """
        document = self.text_browser.document()
        line_count = document.lineCount()
        
        if line_count > self.max_lines:
            # 删除前一半的日志行
            cursor = self.text_browser.textCursor()
            cursor.movePosition(cursor.Start)
            
            lines_to_delete = line_count - (self.max_lines // 2)
            for _ in range(lines_to_delete):
                cursor.select(cursor.LineUnderCursor)
                cursor.removeSelectedText()
                cursor.deleteChar()  # 删除换行符
    
    def clear(self):
        """清空日志"""
        if self.text_browser:
            self.text_browser.clear()
