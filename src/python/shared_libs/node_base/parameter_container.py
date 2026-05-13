"""
自定义参数容器控件 - 垂直布局 + 透明背景 + 滚动条

实现功能：
- 垂直布局排列参数控件
- 背景透明
- 固定显示两行参数，超出部分滚动条翻找
- 标签固定宽度70px
- 支持多种控件类型
"""

from Qt.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea
from Qt.QtCore import Qt
from NodeGraphQt.widgets.node_widgets import NodeBaseWidget


class ParameterContainerWidget(NodeBaseWidget):
    """
    自定义参数容器控件

    特性：
    - 垂直布局排列参数控件
    - 透明背景
    - 标签固定宽度70px，确保对齐
    - 固定显示两行参数，超出部分滚动条翻找
    - 支持整数/浮点数值输入、布尔复选框、枚举下拉菜单、文本输入
    """

    def __init__(self, parent=None, name='', label=''):
        super().__init__(parent, name, label)

        # 创建滚动区域（固定显示两行）
        self._scroll_area = QScrollArea()
        self._scroll_area.setStyleSheet("""
            QScrollArea {
                background-color: transparent;             /* 滚动条背景透明 */
                border: none;
            }
            QScrollBar:vertical {
                width: 15px;                               /* 滚动条宽度 */
                background: transparent;                   /* 滚动条背景透明 */
            }
            QScrollBar::handle:vertical {
                background: #666;                          /* 滚动条滑块颜色 */
                min-height: 15px;                          /* 滚动条滑块最小高度 */
                border-radius: 5px;                        /* 滚动条滑块圆角 */ 
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0;                                 /* 滚动条增加/减少按钮高度 */
            }
        """)
        self._scroll_area.setMaximumHeight(
            80)                                             # 两行参数的高度（约37.5px/行，增加5px避免遮挡）
        self._scroll_area.setMinimumWidth(360)              # 设置最小宽度，确保内容完整显示
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff)                          # 水平滚动条在必要时显示
        self._scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded)                           # 垂直滚动条仅在必要时显示
        self._scroll_area.setWidgetResizable(
            True)                                           # 允许滚动区域宽高根据内容调整

        # 创建主容器
        self._container = QWidget()
        self._container.setStyleSheet(
            "background-color: transparent;")               # 透明背景，避免滚动条遮挡
        
        # 设置容器尺寸策略：允许水平扩展
        from Qt.QtWidgets import QSizePolicy
        self._container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

        # 创建垂直布局
        self._layout = QVBoxLayout(self._container)
        # 控件间距
        self._layout.setSpacing(6)
        # 内边距(右侧留20px给滚动条)
        self._layout.setContentsMargins(4, 4, 20, 4)

        # 设置滚动区域内容
        # 设置滚动区域内容为主容器
        self._scroll_area.setWidget(self._container)

        # 存储控件引用和值更新回调
        self._widgets = {}
        self._value_changed_callback = None

        # 设置为自定义控件
        self.set_custom_widget(self._scroll_area)

    def add_spinbox(self, name, label, value=100, min_value=0, max_value=255, double=False):
        """
        添加数值输入控件

        Args:
            name: 参数名称（唯一标识）
            label: 显示标签
            value: 默认值
            min_value: 最小值
            max_value: 最大值
            double: 是否为浮点数（True=QDoubleSpinBox, False=QSpinBox）

        Returns:
            创建的控件实例
        """
        from NodeGraphQt.custom_widgets.properties_bin.prop_widgets_base import (
            PropSpinBox, PropDoubleSpinBox
        )

        # 创建行容器
        row_widget = QWidget()
        row_widget.setStyleSheet("background-color: transparent;")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setSpacing(4)
        row_layout.setContentsMargins(0, 0, 0, 0)

        # 添加标签
        label_widget = QLabel(label)
        label_widget.setMinimumWidth(80)  # 设置最小宽度，确保短标签也有足够空间
        label_widget.setStyleSheet("""
            color: #e0e0e0;
            qproperty-alignment: 'AlignRight | AlignVCenter';
        """)     # 标签对齐右垂直居中
        row_layout.addWidget(label_widget)

        # 创建数值控件
        if double:
            widget = PropDoubleSpinBox()
        else:
            widget = PropSpinBox()

        widget.setMinimum(min_value)
        widget.setMaximum(max_value)
        widget.setValue(value)
        widget.setFixedWidth(200)       # 数值控件设置固定宽度

        # 设置控件样式（背景反色）
        widget.setStyleSheet("""
            QSpinBox, QDoubleSpinBox {
                color: #ffffff;
                background-color: #3a3a3a;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 2px 5px;
                qproperty-alignment: 'AlignRight | AlignVCenter';
            }
            QSpinBox:focus, QDoubleSpinBox:focus {
                border-color: #4a90d9;
            }
            QSpinBox::up-button, QDoubleSpinBox::up-button {
                subcontrol-origin: border;
                subcontrol-position: top right;
                width: 16px;
                border-left: 1px solid #5a5a5a;
            }
            QSpinBox::down-button, QDoubleSpinBox::down-button {
                subcontrol-origin: border;
                subcontrol-position: bottom right;
                width: 16px;
                border-left: 1px solid #5a5a5a;
            }
        """)

        widget.set_name(name)
        widget.value_changed.connect(
            lambda v, n=name: self._on_value_changed(n, v))

        row_layout.addWidget(widget)

        # 添加到垂直布局
        self._layout.addWidget(row_widget)
        self._widgets[name] = widget

        return widget

    def add_checkbox(self, name, label, state=False):
        """
        添加布尔复选框控件

        Args:
            name: 参数名称
            label: 显示标签
            state: 默认状态

        Returns:
            创建的控件实例
        """
        from NodeGraphQt.custom_widgets.properties_bin.prop_widgets_base import PropCheckBox

        row_widget = QWidget()
        row_widget.setStyleSheet("background-color: transparent;")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setSpacing(4)
        row_layout.setContentsMargins(0, 0, 0, 0)

        # 添加标签
        label_widget = QLabel(label)
        label_widget.setMinimumWidth(80)  # 设置最小宽度，确保短标签也有足够空间
        label_widget.setStyleSheet("""
            color: #e0e0e0;
            qproperty-alignment: 'AlignRight | AlignVCenter';
        """)     # 标签对齐右垂直居中
        row_layout.addWidget(label_widget)

        # 创建复选框
        widget = PropCheckBox()
        widget.set_name(name)
        widget.set_value(state)
        widget.setFixedWidth(200)       # 复选框控件设置固定宽度

        # 设置复选框样式
        widget.setStyleSheet("""
            QCheckBox {
                color: #ffffff;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                background-color: #3a3a3a;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
            }
            QCheckBox::indicator:checked {
                background-color: #4a90d9;
                border: 1px solid #4a90d9;
                border-radius: 3px;
            }
        """)

        widget.value_changed.connect(
            lambda v, n=name: self._on_value_changed(n, v))

        row_layout.addWidget(widget)

        self._layout.addWidget(row_widget)
        self._widgets[name] = widget

        return widget

    def add_combobox(self, name, label, items=[]):
        """
        添加下拉菜单控件

        Args:
            name: 参数名称
            label: 显示标签
            items: 选项列表

        Returns:
            创建的控件实例
        """
        from NodeGraphQt.custom_widgets.properties_bin.prop_widgets_base import PropComboBox

        row_widget = QWidget()
        row_widget.setStyleSheet("background-color: transparent;")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setSpacing(4)
        row_layout.setContentsMargins(0, 0, 0, 0)

        # 添加标签
        label_widget = QLabel(label)
        label_widget.setMinimumWidth(80)  # 设置最小宽度，确保短标签也有足够空间
        label_widget.setStyleSheet("""
            color: #e0e0e0;
            qproperty-alignment: 'AlignRight | AlignVCenter';
        """)     # 标签对齐右垂直居中
        row_layout.addWidget(label_widget)

        # 创建下拉菜单
        widget = PropComboBox()
        widget.set_name(name)
        widget.set_items(items)

        # 设置下拉菜单样式
        widget.setStyleSheet("""
            QComboBox {
                color: #ffffff;
                background-color: #3a3a3a;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 2px 5px;
                min-width: 100px;
            }
            QComboBox:focus {
                border-color: #4a90d9;
            }
            QComboBox::drop-down {
                subcontrol-origin: padding;
                subcontrol-position: top right;
                width: 20px;
                border-left: 1px solid #5a5a5a;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 5px solid #e0e0e0;
            }
            QComboBox QAbstractItemView {
                background-color: #3a3a3a;
                color: #ffffff;
                border: 1px solid #5a5a5a;
            }
        """)

        widget.setFixedWidth(200)       # 下拉菜单控件设置固定宽度
        widget.value_changed.connect(
            lambda v, n=name: self._on_value_changed(n, v))

        row_layout.addWidget(widget)

        self._layout.addWidget(row_widget)
        self._widgets[name] = widget

        return widget

    def add_text_input(self, name, label, text=''):
        """
        添加文本输入控件

        Args:
            name: 参数名称
            label: 显示标签
            text: 默认文本

        Returns:
            创建的控件实例
        """
        from NodeGraphQt.custom_widgets.properties_bin.prop_widgets_base import PropLineEdit

        row_widget = QWidget()
        row_widget.setStyleSheet("background-color: transparent;")
        row_layout = QHBoxLayout(row_widget)
        row_layout.setSpacing(4)
        row_layout.setContentsMargins(0, 0, 0, 0)

        # 添加标签
        label_widget = QLabel(label)
        label_widget.setMinimumWidth(80)  # 设置最小宽度，确保短标签也有足够空间
        label_widget.setStyleSheet(
            "color: #e0e0e0; qproperty-alignment: 'AlignRight';")     # 标签对齐右
        row_layout.addWidget(label_widget)

        # 创建文本框
        widget = PropLineEdit()
        widget.set_name(name)
        widget.set_value(text)
        widget.setFixedWidth(200)       # 文本框控件设置固定宽度

        # 设置文本框样式
        widget.setStyleSheet("""
            QLineEdit {
                color: #ffffff;
                background-color: #3a3a3a;
                border: 1px solid #5a5a5a;
                border-radius: 3px;
                padding: 2px 5px;
            }
            QLineEdit:focus {
                border-color: #4a90d9;
            }
        """)

        widget.value_changed.connect(
            lambda v, n=name: self._on_value_changed(n, v))

        row_layout.addWidget(widget)

        self._layout.addWidget(row_widget)
        self._widgets[name] = widget

        return widget

    def _on_value_changed(self, name, value):
        """
        控件值变化时的回调
        """
        if self._value_changed_callback:
            self._value_changed_callback(name, value)

    def set_value_changed_callback(self, callback):
        """
        设置值变化回调函数
        """
        self._value_changed_callback = callback

    def get_widget(self, name):
        """
        获取指定名称的控件

        Args:
            name: 参数名称

        Returns:
            控件实例，如果不存在返回 None
        """
        return self._widgets.get(name)

    def get_value(self):
        """
        返回所有参数值（JSON字符串格式）

        Returns:
            str: JSON格式的参数值
        """
        import json
        values = {}
        for name, widget in self._widgets.items():
            values[name] = widget.get_value()
        return json.dumps(values)

    def set_value(self, value):
        """
        设置所有参数值

        Args:
            value: JSON字符串格式的参数值
        """
        if isinstance(value, str):
            import json
            try:
                values = json.loads(value)
                for name, val in values.items():
                    if name in self._widgets:
                        self._widgets[name].set_value(val)
            except Exception as e:
                pass

    def get_values_dict(self):
        """
        返回参数值字典

        Returns:
            dict: 参数名称到值的映射
        """
        values = {}
        for name, widget in self._widgets.items():
            values[name] = widget.get_value()
        return values
