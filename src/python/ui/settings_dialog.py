"""
设置对话框模块

提供系统配置的可视化界面：
- 外观设置（主题、语言）
- 字体设置
- 窗口设置
- 项目配置
- 快捷键配置

使用示例：
    from ui.settings_dialog import SettingsDialog
    
    dialog = SettingsDialog(parent=main_window)
    if dialog.exec_() == QtWidgets.QDialog.Accepted:
        # 配置已保存
        pass
"""

import json
import os
from pathlib import Path
from PySide2 import QtWidgets, QtCore, QtGui

from utils.logger import logger
from core.config_manager import config_manager, ConfigCategory
from core.theme_manager import theme_manager
from language.translator import TranslatorManager


class SettingsDialog(QtWidgets.QDialog):
    """
    系统设置对话框
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._translator = TranslatorManager()
        self.setFixedSize(700, 700)

        # 保存原始配置（用于取消时恢复）
        self._original_configs = {}
        self._save_original_configs()

        # UI组件
        self._tab_widget = None
        self._pages = {}

        # 设置语言变化监听器
        self._setup_language_listener()

        # 创建UI
        self._setup_ui()
        
        # 设置窗口标题（必须在_setup_ui之后调用，确保_translator已初始化）
        self.setWindowTitle(self._translator.get_ui("settings.title", "系统设置"))
    
    def _setup_language_listener(self):
        """设置语言变化监听器"""
        self._translator.language_changed.connect(self._on_language_changed)
    
    def _on_language_changed(self, lang_code):
        """语言变化时的回调"""
        # 重新创建UI以应用新语言
        self._rebuild_ui()
    
    def _rebuild_ui(self):
        """重新创建UI以应用新语言"""
        # 清空现有布局
        if self.layout():
            # 移除布局中的所有widget
            while self.layout().count():
                item = self.layout().takeAt(0)
                widget = item.widget()
                if widget:
                    widget.deleteLater()
        
        # 重新创建UI
        self._setup_ui()
        
        # 更新窗口标题
        self.setWindowTitle(self._translator.get_ui("settings.title", "系统设置"))

    def _save_original_configs(self):
        """保存原始配置"""
        self._original_configs['system.theme'] = config_manager.get('system.theme', 'dark')
        self._original_configs['system.language'] = config_manager.get('system.language', 'zh_CN')
        self._original_configs['system.font_family'] = config_manager.get('system.font_family', 'Microsoft YaHei')
        self._original_configs['system.font_size'] = config_manager.get('system.font_size', 9)
        self._original_configs['system.window_width'] = config_manager.get('system.window_width', 1600)
        self._original_configs['system.window_height'] = config_manager.get('system.window_height', 1024)
        self._original_configs['system.window_maximized'] = config_manager.get('system.window_maximized', False)
        self._original_configs['system.auto_save'] = config_manager.get('system.auto_save', True)
        self._original_configs['system.auto_save_interval'] = config_manager.get('system.auto_save_interval', 300)

    def _setup_ui(self):
        """设置UI布局"""
        # 主布局
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 标签页控件
        self._tab_widget = QtWidgets.QTabWidget()
        main_layout.addWidget(self._tab_widget)

        # 添加页面
        self._add_appearance_page()
        self._add_font_page()
        self._add_window_page()
        self._add_project_page()
        self._add_shortcuts_page()

        # 按钮栏
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.setSpacing(10)

        self.apply_button = QtWidgets.QPushButton(self._translator.get_ui("settings.buttons.apply", "应用"))
        self.apply_button.clicked.connect(self._apply_configs)
        button_layout.addWidget(self.apply_button)

        self.reset_button = QtWidgets.QPushButton(self._translator.get_ui("settings.buttons.reset", "重置"))
        self.reset_button.clicked.connect(self._reset_configs)
        button_layout.addWidget(self.reset_button)

        self.cancel_button = QtWidgets.QPushButton(self._translator.get_ui("settings.buttons.cancel", "取消"))
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)

        button_layout.addStretch()

        main_layout.addLayout(button_layout)

    def _add_appearance_page(self):
        """添加外观设置页面"""
        t = self._translator.get_ui
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 主题设置
        theme_group = QtWidgets.QGroupBox(t("settings.appearance.theme", "主题"))
        theme_layout = QtWidgets.QVBoxLayout(theme_group)

        # 主题模式选择
        self._theme_mode_group = QtWidgets.QButtonGroup()

        themes = [
            ('system', t("settings.appearance.system", "跟随系统")),
            ('light', t("settings.appearance.light", "亮色")),
            ('dark', t("settings.appearance.dark", "暗色")),
            ('custom', t("settings.appearance.custom", "自定义"))
        ]

        current_theme = config_manager.get('system.theme', 'dark')

        for mode, label in themes:
            radio = QtWidgets.QRadioButton(label)
            radio.setProperty('mode', mode)
            if mode == current_theme:
                radio.setChecked(True)
            self._theme_mode_group.addButton(radio)
            theme_layout.addWidget(radio)

        # 自定义主题文件选择
        custom_layout = QtWidgets.QHBoxLayout()
        self._custom_theme_path = QtWidgets.QLineEdit()
        self._custom_theme_path.setText(config_manager.get('system.custom_theme_path', ''))
        custom_layout.addWidget(self._custom_theme_path)

        browse_btn = QtWidgets.QPushButton(t("settings.buttons.browse", "浏览..."))
        browse_btn.clicked.connect(self._browse_theme_file)
        custom_layout.addWidget(browse_btn)
        theme_layout.addLayout(custom_layout)

        layout.addWidget(theme_group)

        # 自定义颜色编辑
        color_group = QtWidgets.QGroupBox(t("settings.appearance.custom_colors", "自定义颜色"))
        color_layout = QtWidgets.QGridLayout(color_group)
        color_layout.setSpacing(10)

        colors = theme_manager.get_colors()
        self._color_pickers = {}

        color_items = [
            ('primary', t("settings.appearance.primary", "主题色")),
            ('accent', t("settings.appearance.accent", "强调色")),
            ('background', t("settings.appearance.background", "背景色")),
            ('surface', t("settings.appearance.surface", "表面色")),
            ('text', t("settings.appearance.text", "文字色")),
            ('border', t("settings.appearance.border", "边框色")),
            ('success', t("settings.appearance.success", "成功色")),
            ('warning', t("settings.appearance.warning", "警告色")),
            ('error', t("settings.appearance.error", "错误色")),
            ('info', t("settings.appearance.info", "信息色"))
        ]

        row = 0
        col = 0
        for key, label in color_items:
            color_layout.addWidget(QtWidgets.QLabel(label), row, col)
            
            picker = ColorPickerWidget(colors.get(key, '#ffffff'))
            self._color_pickers[key] = picker
            color_layout.addWidget(picker, row, col + 1)
            
            col += 2
            if col >= 4:
                col = 0
                row += 1

        layout.addWidget(color_group)

        # 语言设置
        lang_group = QtWidgets.QGroupBox(t("settings.appearance.language", "语言"))
        lang_layout = QtWidgets.QHBoxLayout(lang_group)

        self._language_combo = QtWidgets.QComboBox()
        self._language_combo.addItem(t("settings.appearance.chinese", "中文"), 'zh_CN')
        self._language_combo.addItem(t("settings.appearance.english", "English"), 'en_US')
        
        current_lang = config_manager.get('system.language', 'zh_CN')
        index = self._language_combo.findData(current_lang)
        if index >= 0:
            self._language_combo.setCurrentIndex(index)
        
        lang_layout.addWidget(self._language_combo)
        lang_layout.addStretch()

        layout.addWidget(lang_group)

        layout.addStretch()

        self._tab_widget.addTab(page, "🎨 " + t("settings.tabs.appearance", "外观"))
        self._pages['appearance'] = page

    def _add_font_page(self):
        """添加字体设置页面"""
        t = self._translator.get_ui
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 字体设置
        font_group = QtWidgets.QGroupBox(t("settings.font.settings", "字体设置"))
        font_layout = QtWidgets.QFormLayout(font_group)

        # 字体家族
        self._font_family_combo = QtWidgets.QComboBox()
        font_families = self._get_system_fonts()
        self._font_family_combo.addItems(font_families)
        
        current_font = config_manager.get('system.font_family', 'Microsoft YaHei')
        index = self._font_family_combo.findText(current_font)
        if index >= 0:
            self._font_family_combo.setCurrentIndex(index)
        
        font_layout.addRow(t("settings.font.family", "字体:"), self._font_family_combo)

        # 字体大小
        font_size_layout = QtWidgets.QHBoxLayout()
        self._font_size_spin = QtWidgets.QSpinBox()
        self._font_size_spin.setRange(6, 24)
        self._font_size_spin.setValue(config_manager.get('system.font_size', 9))
        font_size_layout.addWidget(self._font_size_spin)
        font_size_layout.addWidget(QtWidgets.QLabel("px"))
        font_size_layout.addStretch()
        
        font_layout.addRow(t("settings.font.size", "字体大小:"), font_size_layout)

        layout.addWidget(font_group)

        # 预览区域
        preview_group = QtWidgets.QGroupBox(t("settings.font.preview", "预览"))
        preview_layout = QtWidgets.QVBoxLayout(preview_group)

        self._preview_label = QtWidgets.QLabel()
        self._preview_label.setText(t("settings.font.preview_text", "预览文本示例") + "\nPreview Text Example\n" + t("settings.font.test_effect", "测试字体显示效果"))
        self._preview_label.setStyleSheet("padding: 10px;")
        preview_layout.addWidget(self._preview_label)

        layout.addWidget(preview_group)

        # 连接字体变化信号
        self._font_family_combo.currentTextChanged.connect(self._update_font_preview)
        self._font_size_spin.valueChanged.connect(self._update_font_preview)

        layout.addStretch()

        self._tab_widget.addTab(page, "✏️ " + t("settings.tabs.font", "字体"))
        self._pages['font'] = page

    def _add_window_page(self):
        """添加窗口设置页面"""
        t = self._translator.get_ui
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 窗口大小设置
        size_group = QtWidgets.QGroupBox(t("settings.window.size", "窗口大小"))
        size_layout = QtWidgets.QFormLayout(size_group)

        # 宽度
        width_layout = QtWidgets.QHBoxLayout()
        self._window_width_spin = QtWidgets.QSpinBox()
        self._window_width_spin.setRange(800, 4000)
        self._window_width_spin.setValue(config_manager.get('system.window_width', 1600))
        width_layout.addWidget(self._window_width_spin)
        width_layout.addWidget(QtWidgets.QLabel(t("settings.window.pixel", "像素")))
        size_layout.addRow(t("settings.window.width", "宽度:"), width_layout)

        # 高度
        height_layout = QtWidgets.QHBoxLayout()
        self._window_height_spin = QtWidgets.QSpinBox()
        self._window_height_spin.setRange(600, 3000)
        self._window_height_spin.setValue(config_manager.get('system.window_height', 1024))
        height_layout.addWidget(self._window_height_spin)
        height_layout.addWidget(QtWidgets.QLabel(t("settings.window.pixel", "像素")))
        size_layout.addRow(t("settings.window.height", "高度:"), height_layout)

        layout.addWidget(size_group)

        # 启动选项
        startup_group = QtWidgets.QGroupBox(t("settings.window.startup", "启动选项"))
        startup_layout = QtWidgets.QVBoxLayout(startup_group)

        self._maximized_check = QtWidgets.QCheckBox(t("settings.window.maximize_on_startup", "启动时最大化窗口"))
        self._maximized_check.setChecked(config_manager.get('system.window_maximized', False))
        startup_layout.addWidget(self._maximized_check)

        layout.addWidget(startup_group)

        # 自动保存设置
        save_group = QtWidgets.QGroupBox(t("settings.window.auto_save", "自动保存"))
        save_layout = QtWidgets.QFormLayout(save_group)

        self._auto_save_check = QtWidgets.QCheckBox(t("settings.window.enable_auto_save", "启用自动保存"))
        self._auto_save_check.setChecked(config_manager.get('system.auto_save', True))
        save_layout.addRow(self._auto_save_check)

        interval_layout = QtWidgets.QHBoxLayout()
        self._auto_save_interval_spin = QtWidgets.QSpinBox()
        self._auto_save_interval_spin.setRange(60, 3600)
        self._auto_save_interval_spin.setValue(config_manager.get('system.auto_save_interval', 300))
        interval_layout.addWidget(self._auto_save_interval_spin)
        interval_layout.addWidget(QtWidgets.QLabel(t("settings.window.seconds", "秒")))
        save_layout.addRow(t("settings.window.interval", "自动保存间隔:"), interval_layout)

        layout.addWidget(save_group)

        layout.addStretch()

        self._tab_widget.addTab(page, "📐 " + t("settings.tabs.window", "窗口"))
        self._pages['window'] = page

    def _add_project_page(self):
        """添加项目配置页面"""
        t = self._translator.get_ui
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 项目设置
        project_group = QtWidgets.QGroupBox(t("settings.project.defaults", "项目默认设置"))
        project_layout = QtWidgets.QFormLayout(project_group)

        # 默认工作流名称
        self._default_workflow_name_edit = QtWidgets.QLineEdit()
        self._default_workflow_name_edit.setText(config_manager.get('project.default_workflow_name', t("main_window.menu.workflow", "工作流")))
        project_layout.addRow(t("settings.project.default_workflow_name", "默认工作流名称:"), self._default_workflow_name_edit)

        layout.addWidget(project_group)

        # 节点设置
        node_group = QtWidgets.QGroupBox(t("settings.project.node_settings", "节点设置"))
        node_layout = QtWidgets.QVBoxLayout(node_group)

        self._auto_connect_check = QtWidgets.QCheckBox(t("settings.project.auto_connect", "自动连接节点"))
        self._auto_connect_check.setChecked(config_manager.get('project.auto_connect_nodes', False))
        node_layout.addWidget(self._auto_connect_check)

        self._show_description_check = QtWidgets.QCheckBox(t("settings.project.show_description", "显示节点描述"))
        self._show_description_check.setChecked(config_manager.get('project.show_node_description', True))
        node_layout.addWidget(self._show_description_check)

        node_size_layout = QtWidgets.QFormLayout()
        
        node_width_layout = QtWidgets.QHBoxLayout()
        self._node_width_spin = QtWidgets.QSpinBox()
        self._node_width_spin.setRange(100, 400)
        self._node_width_spin.setValue(config_manager.get('project.node_width', 200))
        node_width_layout.addWidget(self._node_width_spin)
        node_width_layout.addWidget(QtWidgets.QLabel(t("settings.window.pixel", "像素")))
        node_size_layout.addRow(t("settings.project.node_width", "节点宽度:"), node_width_layout)

        node_spacing_layout = QtWidgets.QHBoxLayout()
        self._node_spacing_spin = QtWidgets.QSpinBox()
        self._node_spacing_spin.setRange(10, 200)
        self._node_spacing_spin.setValue(config_manager.get('project.node_spacing', 50))
        node_spacing_layout.addWidget(self._node_spacing_spin)
        node_spacing_layout.addWidget(QtWidgets.QLabel(t("settings.window.pixel", "像素")))
        node_size_layout.addRow(t("settings.project.node_spacing", "节点间距:"), node_spacing_layout)

        node_layout.addLayout(node_size_layout)

        layout.addWidget(node_group)

        # 执行设置
        exec_group = QtWidgets.QGroupBox(t("settings.project.execution", "执行设置"))
        exec_layout = QtWidgets.QFormLayout(exec_group)

        timeout_layout = QtWidgets.QHBoxLayout()
        self._execution_timeout_spin = QtWidgets.QSpinBox()
        self._execution_timeout_spin.setRange(10, 300)
        self._execution_timeout_spin.setValue(config_manager.get('project.execution_timeout', 30))
        timeout_layout.addWidget(self._execution_timeout_spin)
        timeout_layout.addWidget(QtWidgets.QLabel(t("settings.window.seconds", "秒")))
        exec_layout.addRow(t("settings.project.timeout", "执行超时时间:"), timeout_layout)

        layout.addWidget(exec_group)

        layout.addStretch()

        self._tab_widget.addTab(page, "📁 " + t("settings.tabs.project", "项目"))
        self._pages['project'] = page

    def _add_shortcuts_page(self):
        """添加快捷键设置页面"""
        t = self._translator.get_ui
        page = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(page)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # 快捷键列表
        shortcuts_group = QtWidgets.QGroupBox(t("settings.shortcuts.action", "快捷键"))
        shortcuts_layout = QtWidgets.QVBoxLayout(shortcuts_group)

        self._shortcuts_table = QtWidgets.QTableWidget()
        self._shortcuts_table.setColumnCount(2)
        self._shortcuts_table.setHorizontalHeaderLabels([t("settings.shortcuts.action", "功能"), t("settings.shortcuts.shortcut", "快捷键")])
        self._shortcuts_table.horizontalHeader().setStretchLastSection(True)
        self._shortcuts_table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)

        shortcuts = self._get_default_shortcuts()
        
        self._shortcuts_table.setRowCount(len(shortcuts))
        for i, (name, key) in enumerate(shortcuts.items()):
            self._shortcuts_table.setItem(i, 0, QtWidgets.QTableWidgetItem(name))
            self._shortcuts_table.setItem(i, 1, QtWidgets.QTableWidgetItem(key))

        shortcuts_layout.addWidget(self._shortcuts_table)

        layout.addWidget(shortcuts_group)

        # 提示信息
        hint_label = QtWidgets.QLabel()
        hint_label.setText(t("settings.shortcuts.hint", "提示：快捷键配置将在下一次启动时生效"))
        hint_label.setStyleSheet("color: #858585; font-size: 12px;")
        layout.addWidget(hint_label)

        layout.addStretch()

        self._tab_widget.addTab(page, "🎯 " + t("settings.tabs.shortcuts", "快捷键"))
        self._pages['shortcuts'] = page

    def _get_system_fonts(self):
        """获取系统字体列表"""
        fonts = []
        try:
            font_db = QtGui.QFontDatabase()
            fonts = font_db.families()
        except Exception:
            fonts = ['Microsoft YaHei', 'SimSun', 'SimHei', 'KaiTi', 'Arial', 'Times New Roman']
        return sorted(fonts)

    def _get_default_shortcuts(self):
        """获取默认快捷键列表"""
        t = self._translator.get_ui
        return {
            t("main_window.menu.new_project", "新建工程"): 'Ctrl+Shift+N',
            t("main_window.menu.open_project", "打开工程"): 'Ctrl+Shift+O',
            t("main_window.menu.save_project", "保存工程"): 'Ctrl+Shift+S',
            t("main_window.menu.add_workflow", "添加工作流"): 'Ctrl+N',
            t("main_window.menu.close_workflow", "关闭工作流"): 'Ctrl+W',
            t("main_window.menu.run_workflow", "运行工作流"): 'F5',
            t("main_window.menu.run_all_workflows", "运行全部工作流"): 'Shift+F5',
            t("main_window.menu.system_settings", "打开设置"): 'Ctrl+,',
            t("main_window.toolbar.fit", "适应视图"): 'Ctrl+F',
            t("main_window.menu.delete", "删除节点"): 'Delete'
        }

    def _browse_theme_file(self):
        """浏览主题文件"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "选择主题文件",
            "",
            "主题文件 (*.json);;所有文件 (*)"
        )

        if file_path:
            self._custom_theme_path.setText(file_path)

    def _update_font_preview(self):
        """更新字体预览"""
        font_family = self._font_family_combo.currentText()
        font_size = self._font_size_spin.value()
        
        self._preview_label.setStyleSheet(f"""
            font-family: {font_family};
            font-size: {font_size}px;
        """)

    def _apply_configs(self):
        """应用配置"""
        try:
            # 外观配置
            selected_theme = None
            for radio in self._theme_mode_group.buttons():
                if radio.isChecked():
                    selected_theme = radio.property('mode')
                    break

            if selected_theme:
                config_manager.set('system.theme', selected_theme)
                config_manager.set('system.theme_mode', selected_theme)
                
                if selected_theme == 'custom':
                    custom_path = self._custom_theme_path.text()
                    config_manager.set('system.custom_theme_path', custom_path)
                    theme_manager.load_theme_from_file(custom_path)
                else:
                    theme_manager.apply_theme(selected_theme)

            # 自定义颜色
            for key, picker in self._color_pickers.items():
                color = picker.get_color()
                config_manager.set(f'theme.{key}_color', color)
                theme_manager.set_color(key, color)

            # 语言配置
            lang = self._language_combo.currentData()
            config_manager.set('system.language', lang)
            
            # 切换语言
            self._translator.set_language(lang)

            # 字体配置
            font_family = self._font_family_combo.currentText()
            font_size = self._font_size_spin.value()
            config_manager.set('system.font_family', font_family)
            config_manager.set('system.font_size', font_size)

            # 窗口配置
            config_manager.set('system.window_width', self._window_width_spin.value())
            config_manager.set('system.window_height', self._window_height_spin.value())
            config_manager.set('system.window_maximized', self._maximized_check.isChecked())
            config_manager.set('system.auto_save', self._auto_save_check.isChecked())
            config_manager.set('system.auto_save_interval', self._auto_save_interval_spin.value())

            # 项目配置
            config_manager.set('project.default_workflow_name', self._default_workflow_name_edit.text())
            config_manager.set('project.auto_connect_nodes', self._auto_connect_check.isChecked())
            config_manager.set('project.show_node_description', self._show_description_check.isChecked())
            config_manager.set('project.node_width', self._node_width_spin.value())
            config_manager.set('project.node_spacing', self._node_spacing_spin.value())
            config_manager.set('project.execution_timeout', self._execution_timeout_spin.value())

            logger.info(self._translator.get_log("config_saved", "配置已保存"), module="settings")
            
            # 通知主题变更（直接调用apply_theme确保颜色被更新）
            current_mode = theme_manager.get_current_mode()
            theme_manager.apply_theme(current_mode)

            self.accept()

        except Exception as e:
            t = self._translator.get_ui
            logger.error(f"{t('settings.messages.save_failed', '保存配置失败')}: {e}", module="settings")
            QtWidgets.QMessageBox.error(self, t("settings.messages.error", "错误"), f"{t('settings.messages.save_failed', '保存配置失败')}: {e}")

    def _reset_configs(self):
        """重置配置到原始值"""
        t = self._translator.get_ui
        for key, value in self._original_configs.items():
            config_manager.set(key, value)
        
        # 重置UI控件
        self._setup_ui()
        logger.info(self._translator.get_log("config_saved", "配置已重置"), module="settings")
        QtWidgets.QMessageBox.information(self, t("settings.messages.info", "提示"), t("settings.messages.config_restored", "配置已重置为原始值"))


class ColorPickerWidget(QtWidgets.QWidget):
    """
    颜色选择器组件
    """

    def __init__(self, initial_color='#ffffff', parent=None):
        super().__init__(parent)
        
        self._color = initial_color
        
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 颜色预览框
        self._color_box = QtWidgets.QFrame()
        self._color_box.setFixedSize(30, 24)
        self._color_box.setStyleSheet(f"background-color: {initial_color}; border: 1px solid #3c3c3c;")
        layout.addWidget(self._color_box)

        # 颜色值输入
        self._color_edit = QtWidgets.QLineEdit()
        self._color_edit.setFixedWidth(80)
        self._color_edit.setText(initial_color)
        self._color_edit.editingFinished.connect(self._on_color_edit)
        layout.addWidget(self._color_edit)

        # 颜色选择按钮
        self._pick_button = QtWidgets.QPushButton("...")
        self._pick_button.setFixedWidth(28)
        self._pick_button.clicked.connect(self._pick_color)
        layout.addWidget(self._pick_button)

    def _pick_color(self):
        """打开颜色选择对话框"""
        color = QtWidgets.QColorDialog.getColor(QtGui.QColor(self._color), self)
        if color.isValid():
            self._color = color.name()
            self._update_display()

    def _on_color_edit(self):
        """颜色输入框编辑完成"""
        text = self._color_edit.text()
        if self._is_valid_color(text):
            self._color = text
            self._update_display()
        else:
            self._color_edit.setText(self._color)

    def _is_valid_color(self, text):
        """检查颜色值是否有效"""
        try:
            QtGui.QColor(text)
            return True
        except Exception:
            return False

    def _update_display(self):
        """更新显示"""
        self._color_box.setStyleSheet(f"background-color: {self._color}; border: 1px solid #3c3c3c;")
        self._color_edit.setText(self._color)

    def get_color(self):
        """获取当前颜色"""
        return self._color

    def set_color(self, color):
        """设置颜色"""
        if self._is_valid_color(color):
            self._color = color
            self._update_display()


__all__ = ['SettingsDialog', 'ColorPickerWidget']