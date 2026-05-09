"""
主题管理器模块

提供主题管理功能：
- 四种主题模式（跟随系统/亮色/暗色/自定义）
- 动态样式表生成
- 主题文件加载/保存
- 配置变更监听

使用示例：
    from core.theme_manager import theme_manager

    # 获取当前主题
    current_theme = theme_manager.get_current_theme()

    # 应用主题
    theme_manager.apply_theme('dark')

    # 生成样式表
    stylesheet = theme_manager.generate_stylesheet()
    app.setStyleSheet(stylesheet)
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from enum import Enum
import threading

from utils.logger import logger
from core.config_manager import config_manager


class ThemeMode(Enum):
    """主题模式枚举"""
    SYSTEM = "system"       # 跟随系统
    LIGHT = "light"         # 亮色
    DARK = "dark"           # 暗色
    CUSTOM = "custom"       # 自定义


class ThemeManager:
    """
    主题管理器（单例）

    特性：
    - 四种主题模式切换
    - 动态样式表生成
    - 主题文件加载/保存
    - 配置变更监听
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
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

        # 当前主题模式
        self._current_mode: ThemeMode = ThemeMode.DARK

        # 主题颜色配置
        self._colors: Dict[str, str] = {}

        # 监听器
        self._listeners: List[Callable[[ThemeMode], None]] = []

        # 主题文件目录
        self._theme_dir = Path(__file__).parent.parent / "resources" / "themes"
        self._theme_dir.mkdir(parents=True, exist_ok=True)

        # 初始化
        self._load_default_colors()
        self._setup_config_listeners()

    def _load_default_colors(self):
        """加载默认颜色配置"""
        self._colors = {
            # 暗色主题默认值
            'primary': '#2563eb',
            'accent': '#3b82f6',
            'background': '#1e1e1e',
            'surface': '#252526',
            'text': '#cccccc',
            'text_disabled': '#858585',
            'border': '#3c3c3c',
            'success': '#10b981',
            'warning': '#f59e0b',
            'error': '#dc2626',
            'info': '#3b82f6'
        }

    def _setup_config_listeners(self):
        """设置配置变更监听"""
        config_manager.subscribe('system.theme', self._on_theme_changed)
        config_manager.subscribe('system.theme_mode', self._on_theme_changed)
        config_manager.subscribe('theme.primary_color', self._on_color_changed)
        config_manager.subscribe('theme.accent_color', self._on_color_changed)
        config_manager.subscribe('theme.bg_color', self._on_color_changed)
        config_manager.subscribe('theme.surface_color', self._on_color_changed)
        config_manager.subscribe('theme.text_color', self._on_color_changed)
        config_manager.subscribe('theme.border_color', self._on_color_changed)

    def _on_theme_changed(self, key: str, value: str):
        """主题变更回调"""
        self.apply_theme(value)

    def _on_color_changed(self, key: str, value: str):
        """颜色配置变更回调"""
        color_key = key.replace('theme.', '').replace('_color', '')
        self._colors[color_key] = value
        self._notify_listeners(self._current_mode)

    def apply_theme(self, mode: str):
        """
        应用主题

        Args:
            mode: 主题模式 ('system', 'light', 'dark', 'custom')
        """
        try:
            self._current_mode = ThemeMode(mode)
        except ValueError:
            self._current_mode = ThemeMode.DARK
            logger.warning(f"无效的主题模式: {mode}，使用默认暗色主题", module="theme")

        if self._current_mode == ThemeMode.SYSTEM:
            self._apply_system_theme()
        elif self._current_mode == ThemeMode.LIGHT:
            self._apply_light_theme()
        elif self._current_mode == ThemeMode.DARK:
            self._apply_dark_theme()
        elif self._current_mode == ThemeMode.CUSTOM:
            self._apply_custom_theme()

        # 保存到配置
        config_manager.set('system.theme', mode)
        config_manager.set('system.theme_mode', mode)

        # 通知监听器
        self._notify_listeners(self._current_mode)

        logger.info(f"主题已切换为: {mode}", module="theme")

    def _apply_system_theme(self):
        """跟随系统主题"""
        try:
            from PySide2.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                palette = app.palette()
                bg_color = palette.window().color().name()
                text_color = palette.windowText().color().name()

                # 根据亮度判断是亮色还是暗色
                if self._is_dark_color(bg_color):
                    self._apply_dark_theme()
                else:
                    self._apply_light_theme()
            else:
                self._apply_dark_theme()
        except Exception as e:
            logger.warning(f"获取系统主题失败，使用默认暗色主题: {e}", module="theme")
            self._apply_dark_theme()

    def _apply_light_theme(self):
        """应用亮色主题"""
        self._colors.update({
            'primary': '#2563eb',
            'accent': '#3b82f6',
            'background': '#ffffff',
            'surface': '#f8f9fa',
            'text': '#212529',
            'text_disabled': '#adb5bd',
            'border': '#dee2e6',
            'success': '#10b981',
            'warning': '#f59e0b',
            'error': '#dc2626',
            'info': '#3b82f6'
        })

        # 保存到配置
        self._save_colors_to_config()

    def _apply_dark_theme(self):
        """应用暗色主题"""
        self._colors.update({
            'primary': '#2563eb',
            'accent': '#3b82f6',
            'background': '#1e1e1e',
            'surface': '#252526',
            'text': '#cccccc',
            'text_disabled': '#858585',
            'border': '#3c3c3c',
            'success': '#10b981',
            'warning': '#f59e0b',
            'error': '#dc2626',
            'info': '#3b82f6'
        })

        # 保存到配置
        self._save_colors_to_config()

    def _apply_custom_theme(self):
        """应用自定义主题"""
        custom_path = config_manager.get('system.custom_theme_path', '')
        
        if custom_path and Path(custom_path).exists():
            self.load_theme_from_file(custom_path)
        else:
            # 从配置加载颜色
            self._load_colors_from_config()
            logger.info("使用配置中的自定义颜色", module="theme")

    def _save_colors_to_config(self):
        """保存颜色配置到config_manager"""
        config_manager.set('theme.primary_color', self._colors['primary'])
        config_manager.set('theme.accent_color', self._colors['accent'])
        config_manager.set('theme.bg_color', self._colors['background'])
        config_manager.set('theme.surface_color', self._colors['surface'])
        config_manager.set('theme.text_color', self._colors['text'])
        config_manager.set('theme.text_disabled_color', self._colors['text_disabled'])
        config_manager.set('theme.border_color', self._colors['border'])
        config_manager.set('theme.success_color', self._colors['success'])
        config_manager.set('theme.warning_color', self._colors['warning'])
        config_manager.set('theme.error_color', self._colors['error'])
        config_manager.set('theme.info_color', self._colors['info'])

    def _load_colors_from_config(self):
        """从config_manager加载颜色配置"""
        self._colors.update({
            'primary': config_manager.get('theme.primary_color', '#2563eb'),
            'accent': config_manager.get('theme.accent_color', '#3b82f6'),
            'background': config_manager.get('theme.bg_color', '#1e1e1e'),
            'surface': config_manager.get('theme.surface_color', '#252526'),
            'text': config_manager.get('theme.text_color', '#cccccc'),
            'text_disabled': config_manager.get('theme.text_disabled_color', '#858585'),
            'border': config_manager.get('theme.border_color', '#3c3c3c'),
            'success': config_manager.get('theme.success_color', '#10b981'),
            'warning': config_manager.get('theme.warning_color', '#f59e0b'),
            'error': config_manager.get('theme.error_color', '#dc2626'),
            'info': config_manager.get('theme.info_color', '#3b82f6')
        })

    def _is_dark_color(self, hex_color: str) -> bool:
        """判断颜色是否为暗色"""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # 计算亮度 (Luma)
            brightness = (0.299 * r + 0.587 * g + 0.114 * b) / 255
            return brightness < 0.5
        except Exception:
            return False

    def generate_stylesheet(self) -> str:
        """
        生成Qt样式表

        Returns:
            完整的样式表字符串
        """
        colors = self._colors
        font_family = config_manager.get('system.font_family', 'Microsoft YaHei')
        font_size = config_manager.get('system.font_size', 9)

        stylesheet = f"""
/* ===== 主题样式表 ===== */

/* 基础字体 */
QWidget {{
    font-family: {font_family};
    font-size: {font_size}px;
    color: {colors['text']};
    background-color: {colors['background']};
}}

/* 主窗口 */
QMainWindow {{
    background-color: {colors['background']};
}}

/* 中央部件 */
QWidget#centralwidget {{
    background-color: {colors['background']};
}}

/* 菜单条 */
QMenuBar {{
    background-color: {colors['surface']};
    color: {colors['text']};
    border-bottom: 1px solid {colors['border']};
}}

QMenuBar::item {{
    padding: 4px 12px;
}}

QMenuBar::item:selected {{
    background-color: {colors['primary']};
}}

QMenu {{
    background-color: {colors['surface']};
    color: {colors['text']};
    border: 1px solid {colors['border']};
}}

QMenu::item {{
    padding: 6px 24px 6px 24px;
}}

QMenu::item:selected {{
    background-color: {colors['primary']};
}}

QMenu::separator {{
    height: 1px;
    background-color: {colors['border']};
}}

/* 工具栏 */
QToolBar {{
    background-color: {colors['surface']};
    border-bottom: 1px solid {colors['border']};
    spacing: 4px;
}}

QToolBar QToolButton {{
    background-color: transparent;
    border: none;
    padding: 4px 8px;
}}

QToolBar QToolButton:hover {{
    background-color: {colors['border']};
    border-radius: 4px;
}}

QToolBar QToolButton:pressed {{
    background-color: {colors['primary']};
}}

/* 按钮 */
QPushButton {{
    background-color: {colors['primary']};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 6px 16px;
    min-width: 80px;
}}

QPushButton:hover {{
    background-color: {colors['accent']};
}}

QPushButton:pressed {{
    background-color: {colors['primary']};
}}

QPushButton:disabled {{
    background-color: {colors['border']};
    color: {colors['text_disabled']};
}}

QPushButton#flatButton {{
    background-color: transparent;
    color: {colors['text']};
    border: 1px solid {colors['border']};
}}

QPushButton#flatButton:hover {{
    background-color: {colors['border']};
}}

/* 标签 */
QLabel {{
    color: {colors['text']};
}}

QLabel#titleLabel {{
    font-weight: bold;
    font-size: {font_size + 2}px;
}}

/* 文本框 */
QLineEdit {{
    background-color: {colors['surface']};
    color: {colors['text']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
    padding: 4px 8px;
}}

QLineEdit:focus {{
    border-color: {colors['primary']};
}}

QLineEdit:disabled {{
    background-color: {colors['border']};
    color: {colors['text_disabled']};
}}

/* 文本编辑 */
QTextEdit {{
    background-color: {colors['surface']};
    color: {colors['text']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
}}

QTextEdit:focus {{
    border-color: {colors['primary']};
}}

/* 列表框 */
QListWidget {{
    background-color: {colors['surface']};
    color: {colors['text']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
}}

QListWidget::item {{
    padding: 4px 8px;
}}

QListWidget::item:selected {{
    background-color: {colors['primary']};
}}

/* 树形控件 */
QTreeWidget {{
    background-color: {colors['surface']};
    color: {colors['text']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
}}

QTreeWidget::item {{
    padding: 2px 4px;
}}

QTreeWidget::item:selected {{
    background-color: {colors['primary']};
}}

QTreeWidget::branch {{
    background-color: {colors['surface']};
}}

/* 表格 */
QTableWidget {{
    background-color: {colors['surface']};
    color: {colors['text']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
}}

QTableWidget::item {{
    padding: 4px 8px;
}}

QTableWidget::item:selected {{
    background-color: {colors['primary']};
}}

QTableWidget::horizontalHeader {{
    background-color: {colors['surface']};
    color: {colors['text']};
    border-bottom: 1px solid {colors['border']};
}}

QTableWidget::verticalHeader {{
    background-color: {colors['surface']};
    color: {colors['text']};
    border-right: 1px solid {colors['border']};
}}

/* 组合框 */
QComboBox {{
    background-color: {colors['surface']};
    color: {colors['text']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
    padding: 4px 8px;
    min-width: 120px;
}}

QComboBox::drop-down {{
    border: none;
    background-color: {colors['surface']};
}}

QComboBox::down-arrow {{
    image: none;
    border: 4px solid transparent;
    border-top-color: {colors['text']};
    margin-right: 4px;
}}

QComboBox QAbstractItemView {{
    background-color: {colors['surface']};
    color: {colors['text']};
    border: 1px solid {colors['border']};
}}

/* 复选框 */
QCheckBox {{
    color: {colors['text']};
}}

QCheckBox::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {colors['border']};
    border-radius: 3px;
    background-color: {colors['surface']};
}}

QCheckBox::indicator:checked {{
    background-color: {colors['primary']};
    border-color: {colors['primary']};
}}

QCheckBox::indicator:checked::after {{
    image: url(data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'><path d='M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z'/></svg>);
}}

/* 单选按钮 */
QRadioButton {{
    color: {colors['text']};
}}

QRadioButton::indicator {{
    width: 18px;
    height: 18px;
    border: 2px solid {colors['border']};
    border-radius: 9px;
    background-color: {colors['surface']};
}}

QRadioButton::indicator:checked {{
    background-color: {colors['primary']};
    border-color: {colors['primary']};
}}

QRadioButton::indicator:checked::after {{
    width: 8px;
    height: 8px;
    border-radius: 4px;
    background-color: white;
    margin: 3px;
}}

/* 滑块 */
QSlider::groove:horizontal {{
    height: 6px;
    background-color: {colors['border']};
    border-radius: 3px;
}}

QSlider::handle:horizontal {{
    width: 16px;
    height: 16px;
    background-color: {colors['primary']};
    border-radius: 8px;
    margin: -5px 0;
}}

QSlider::groove:vertical {{
    width: 6px;
    background-color: {colors['border']};
    border-radius: 3px;
}}

QSlider::handle:vertical {{
    width: 16px;
    height: 16px;
    background-color: {colors['primary']};
    border-radius: 8px;
    margin: 0 -5px;
}}

/* 滚动条 */
QScrollBar::vertical {{
    width: 12px;
    background-color: {colors['surface']};
}}

QScrollBar::handle:vertical {{
    background-color: {colors['border']};
    border-radius: 6px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {colors['text_disabled']};
}}

QScrollBar::horizontal {{
    height: 12px;
    background-color: {colors['surface']};
}}

QScrollBar::handle:horizontal {{
    background-color: {colors['border']};
    border-radius: 6px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {colors['text_disabled']};
}}

/* 分组框 */
QGroupBox {{
    color: {colors['text']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
    margin-top: 10px;
    padding-top: 8px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 8px 0 8px;
}}

/* 选项卡 */
QTabWidget::pane {{
    background-color: {colors['surface']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
}}

QTabBar::tab {{
    background-color: {colors['surface']};
    color: {colors['text_disabled']};
    border: 1px solid {colors['border']};
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    padding: 6px 16px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {colors['background']};
    color: {colors['text']};
    border-color: {colors['border']};
}}

QTabBar::tab:hover:not(selected) {{
    color: {colors['text']};
}}

/* DockWidget */
QDockWidget {{
    titlebar-close-icon: url(data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='{self._hex_to_rgb(colors['text'])}'><path d='M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z'/></svg>);
    titlebar-normal-icon: url(data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='{self._hex_to_rgb(colors['text'])}'><path d='M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z'/></svg>);
}}

QDockWidget::title {{
    background-color: {colors['surface']};
    padding: 4px 8px;
}}

/* 进度条 */
QProgressBar {{
    background-color: {colors['border']};
    border-radius: 4px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {colors['primary']};
    border-radius: 4px;
}}

/* 对话框 */
QDialog {{
    background-color: {colors['background']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
}}

/* 消息框 */
QMessageBox {{
    background-color: {colors['background']};
    color: {colors['text']};
}}

/* 状态栏 */
QStatusBar {{
    background-color: {colors['surface']};
    color: {colors['text']};
    border-top: 1px solid {colors['border']};
}}

/* 日志面板 */
QTextBrowser#logPanel {{
    background-color: {colors['background']};
    color: {colors['text']};
    font-family: Consolas, monospace;
}}

/* 节点编辑器相关 */
NodeGraphQt--Node {{
    background-color: {colors['surface']};
    border-color: {colors['border']};
}}

NodeGraphQt--Node.selected {{
    border-color: {colors['primary']};
}}

NodeGraphQt--Port {{
    background-color: {colors['primary']};
}}

NodeGraphQt--Port.selected {{
    background-color: {colors['accent']};
}}

/* 自定义滚动区域 */
QScrollArea {{
    background-color: transparent;
    border: none;
}}

QScrollArea QWidget {{
    background-color: transparent;
}}

/* 工具提示 */
QToolTip {{
    background-color: {colors['surface']};
    color: {colors['text']};
    border: 1px solid {colors['border']};
    border-radius: 4px;
    padding: 4px 8px;
}}
"""

        return stylesheet

    def _hex_to_rgb(self, hex_color: str) -> str:
        """将十六进制颜色转换为RGB格式"""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f'rgb({r},{g},{b})'
        except Exception:
            return 'rgb(255,255,255)'

    def load_theme_from_file(self, file_path: str) -> bool:
        """
        从文件加载主题

        Args:
            file_path: 主题文件路径

        Returns:
            是否加载成功
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logger.error(f"主题文件不存在: {file_path}", module="theme")
                return False

            with open(path, 'r', encoding='utf-8') as f:
                theme_data = json.load(f)

            if 'colors' in theme_data:
                self._colors.update(theme_data['colors'])
            
            # 保存自定义主题路径
            config_manager.set('system.custom_theme_path', file_path)
            
            # 保存颜色到配置
            self._save_colors_to_config()

            logger.info(f"成功加载主题文件: {file_path}", module="theme")
            return True

        except Exception as e:
            logger.error(f"加载主题文件失败: {e}", module="theme")
            return False

    def save_theme_to_file(self, file_path: str, name: str = "自定义主题") -> bool:
        """
        保存主题到文件

        Args:
            file_path: 保存路径
            name: 主题名称

        Returns:
            是否保存成功
        """
        try:
            theme_data = {
                'name': name,
                'version': '1.0',
                'colors': self._colors
            }

            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(theme_data, f, indent=4, ensure_ascii=False)

            logger.info(f"成功保存主题文件: {file_path}", module="theme")
            return True

        except Exception as e:
            logger.error(f"保存主题文件失败: {e}", module="theme")
            return False

    def get_current_theme(self) -> ThemeMode:
        """获取当前主题模式"""
        return self._current_mode

    def get_colors(self) -> Dict[str, str]:
        """获取当前颜色配置"""
        return self._colors.copy()

    def set_color(self, key: str, value: str):
        """
        设置单个颜色

        Args:
            key: 颜色键名
            value: 十六进制颜色值
        """
        if key in self._colors:
            self._colors[key] = value
            config_manager.set(f'theme.{key}_color', value)
            self._notify_listeners(self._current_mode)

    def subscribe(self, callback: Callable[[ThemeMode], None]):
        """
        订阅主题变更

        Args:
            callback: 回调函数，签名：callback(mode)
        """
        self._listeners.append(callback)

    def unsubscribe(self, callback: Callable[[ThemeMode], None]):
        """
        取消订阅主题变更

        Args:
            callback: 回调函数
        """
        if callback in self._listeners:
            self._listeners.remove(callback)

    def _notify_listeners(self, mode: ThemeMode):
        """通知所有监听器主题变更"""
        for callback in self._listeners:
            try:
                callback(mode)
            except Exception as e:
                logger.error(f"主题变更通知失败: {e}", module="theme")

    def get_available_themes(self) -> list:
        """获取可用的主题文件列表"""
        themes = []
        
        # 添加内置主题
        themes.append({'name': '跟随系统', 'mode': 'system', 'is_builtin': True})
        themes.append({'name': '亮色', 'mode': 'light', 'is_builtin': True})
        themes.append({'name': '暗色', 'mode': 'dark', 'is_builtin': True})
        themes.append({'name': '自定义', 'mode': 'custom', 'is_builtin': True})

        # 扫描主题目录
        if self._theme_dir.exists():
            for file in self._theme_dir.glob('*.json'):
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        name = data.get('name', file.stem)
                        themes.append({
                            'name': name,
                            'path': str(file),
                            'is_builtin': False
                        })
                except Exception:
                    pass

        return themes


# 创建全局单例
theme_manager = ThemeManager()

__all__ = [
    'ThemeManager',
    'ThemeMode',
    'theme_manager'
]