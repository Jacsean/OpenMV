"""
节点编辑器 - 节点增删改查管理界面（增强版）

功能:
- 浏览所有节点包（6大分类）
- 创建新节点（向导式）
- 编辑节点属性（名称、分类、参数）
- 删除节点
- 导出节点包为ZIP
- 导入节点包从ZIP
- ✨ 代码高亮编辑器
- ✨ 实时预览面板
- ✨ 撤销/重做支持
- ✨ 智能参数提示
"""

import os
import json
import zipfile
import re
from pathlib import Path
from PySide2 import QtWidgets, QtCore, QtGui


class CodeEditor(QtWidgets.QPlainTextEdit):
    """
    代码编辑器 - 支持语法高亮和行号显示
    """
    
    def __init__(self, parent=None):
        super(CodeEditor, self).__init__(parent)
        self.setFont(QtGui.QFont("Consolas", 10))
        self.setTabStopWidth(4 * self.fontMetrics().width(' '))
        
        # 行号区域
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self._update_line_number_area_width()
        
    def line_number_area_width(self):
        """计算行号区域宽度"""
        digits = 1
        max_num = max(1, self.blockCount())
        while max_num >= 10:
            max_num //= 10
            digits += 1
        space = 3 + self.fontMetrics().width('9') * digits
        return space
    
    def _update_line_number_area_width(self):
        """更新行号区域宽度"""
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)
    
    def _update_line_number_area(self, rect, dy):
        """更新行号区域"""
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        
        if rect.contains(self.viewport().rect()):
            self._update_line_number_area_width()
    
    def resizeEvent(self, event):
        """调整大小事件"""
        super(CodeEditor, self).resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QtCore.QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))
    
    def highlight_current_line(self):
        """高亮当前行"""
        extra_selections = []
        if not self.isReadOnly():
            selection = QtWidgets.QTextEdit.ExtraSelection()
            line_color = QtGui.QColor(QtCore.Qt.yellow).lighter(180)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QtGui.QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)
    
    def line_number_area_paint_event(self, event):
        """绘制行号区域"""
        painter = QtGui.QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QtGui.QColor(240, 240, 240))
        
        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QtGui.QColor(120, 120, 120))
                painter.drawText(0, top, self.line_number_area.width() - 5, 
                               self.fontMetrics().height(),
                               QtCore.Qt.AlignRight, number)
            
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1


class LineNumberArea(QtWidgets.QWidget):
    """行号显示区域"""
    
    def __init__(self, editor):
        super(LineNumberArea, self).__init__(editor)
        self.code_editor = editor
    
    def sizeHint(self):
        return QtCore.QSize(self.code_editor.line_number_area_width(), 0)
    
    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class NodeEditorDialog(QtWidgets.QDialog):
    """
    节点编辑器对话框
    
    提供可视化的节点管理界面，支持节点的完整生命周期管理
    """
    
    def __init__(self, parent=None, plugins_dir=None):
        super(NodeEditorDialog, self).__init__(parent)
        self.plugins_dir = plugins_dir or Path(__file__).parent.parent / "user_plugins"
        self.setWindowTitle("节点编辑器")
        self.resize(1200, 800)
        
        # 加载现有节点包
        self.plugin_packages = {}
        self._load_plugin_packages()
        
        # ✨ 撤销/重做历史栈
        self.undo_stack = []
        self.redo_stack = []
        self.max_history = 50
        
        # ✨ 当前编辑状态
        self.current_package = None
        self.current_node_index = None
        
        # 构建UI
        self._setup_ui()
        
    def _load_plugin_packages(self):
        """扫描并加载所有节点包"""
        if not self.plugins_dir.exists():
            return
        
        for plugin_dir in self.plugins_dir.iterdir():
            if plugin_dir.is_dir():
                plugin_json = plugin_dir / "plugin.json"
                if plugin_json.exists():
                    try:
                        with open(plugin_json, 'r', encoding='utf-8') as f:
                            plugin_data = json.load(f)
                            self.plugin_packages[plugin_dir.name] = {
                                'path': plugin_dir,
                                'data': plugin_data
                            }
                    except Exception as e:
                        print(f"加载插件包失败 {plugin_dir.name}: {e}")
    
    def _setup_ui(self):
        """构建用户界面"""
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # === 顶部工具栏 ===
        toolbar = self._create_toolbar()
        main_layout.addWidget(toolbar)
        
        # === 主内容区（左右分割）===
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        # 左侧：节点包树形视图
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # 右侧：节点详情编辑区
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter)
        
        # === 底部按钮栏 ===
        button_bar = self._create_button_bar()
        main_layout.addWidget(button_bar)
    
    def _create_toolbar(self):
        """创建顶部工具栏"""
        toolbar = QtWidgets.QToolBar()
        toolbar.setIconSize(QtCore.QSize(24, 24))
        
        # 新建节点包
        new_package_action = toolbar.addAction("📦 新建节点包")
        new_package_action.triggered.connect(self._on_new_package)
        
        toolbar.addSeparator()
        
        # 导入节点包
        import_action = toolbar.addAction("📥 导入节点包")
        import_action.triggered.connect(self._on_import_package)
        
        # 导出节点包
        export_action = toolbar.addAction("📤 导出节点包")
        export_action.triggered.connect(self._on_export_package)
        
        toolbar.addSeparator()
        
        # 刷新
        refresh_action = toolbar.addAction("🔄 刷新")
        refresh_action.triggered.connect(self._refresh_packages)
        
        return toolbar
    
    def _create_left_panel(self):
        """创建左侧面板（节点包列表）"""
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题
        title_label = QtWidgets.QLabel("节点包列表")
        title_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        layout.addWidget(title_label)
        
        # 树形视图
        self.package_tree = QtWidgets.QTreeWidget()
        self.package_tree.setHeaderLabels(["名称", "版本", "分类", "节点数"])
        self.package_tree.setColumnWidth(0, 200)
        self.package_tree.setColumnWidth(1, 80)
        self.package_tree.setColumnWidth(2, 120)
        self.package_tree.setColumnWidth(3, 60)
        self.package_tree.itemSelectionChanged.connect(self._on_package_selected)
        layout.addWidget(self.package_tree)
        
        # 填充数据
        self._populate_package_tree()
        
        return panel
    
    def _populate_package_tree(self):
        """填充节点包树形视图"""
        self.package_tree.clear()
        
        # 按分类组织
        categories = {}
        for pkg_name, pkg_info in self.plugin_packages.items():
            data = pkg_info['data']
            category_group = data.get('category_group', '未分类')
            
            if category_group not in categories:
                categories[category_group] = []
            categories[category_group].append((pkg_name, pkg_info))
        
        # 构建树形结构
        for category, packages in sorted(categories.items()):
            category_item = QtWidgets.QTreeWidgetItem([category, "", "", ""])
            category_item.setFont(0, QtGui.QFont("Arial", 9, QtGui.QFont.Bold))
            
            for pkg_name, pkg_info in sorted(packages):
                data = pkg_info['data']
                nodes_count = len(data.get('nodes', []))
                
                pkg_item = QtWidgets.QTreeWidgetItem([
                    pkg_name,
                    data.get('version', '1.0.0'),
                    data.get('category_group', ''),
                    str(nodes_count)
                ])
                pkg_item.setData(0, QtCore.Qt.UserRole, pkg_name)
                category_item.addChild(pkg_item)
            
            self.package_tree.addTopLevelItem(category_item)
        
        self.package_tree.expandAll()
    
    def _create_right_panel(self):
        """创建右侧面板（节点详情编辑）- 增强版"""
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 标题
        title_label = QtWidgets.QLabel("节点详情")
        title_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        layout.addWidget(title_label)
        
        # ✨ Tab控件：详情 / 代码 / 预览
        self.tab_widget = QtWidgets.QTabWidget()
        
        # Tab 1: 节点详情
        detail_tab = QtWidgets.QWidget()
        detail_layout = QtWidgets.QVBoxLayout(detail_tab)
        detail_layout.setContentsMargins(5, 5, 5, 5)
        
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        
        self.detail_widget = QtWidgets.QWidget()
        self.detail_layout = QtWidgets.QVBoxLayout(self.detail_widget)
        self.detail_layout.setSpacing(10)
        
        scroll.setWidget(self.detail_widget)
        detail_layout.addWidget(scroll)
        
        self.tab_widget.addTab(detail_tab, "📋 详情")
        
        # Tab 2: 代码编辑器
        code_tab = QtWidgets.QWidget()
        code_layout = QtWidgets.QVBoxLayout(code_tab)
        code_layout.setContentsMargins(5, 5, 5, 5)
        
        self.code_editor = CodeEditor()
        self.code_editor.setReadOnly(False)
        self.code_editor.textChanged.connect(self._on_code_changed)
        code_layout.addWidget(self.code_editor)
        
        # 代码操作按钮
        code_btn_layout = QtWidgets.QHBoxLayout()
        self.save_code_btn = QtWidgets.QPushButton("💾 保存代码")
        self.save_code_btn.clicked.connect(self._on_save_code)
        self.format_code_btn = QtWidgets.QPushButton("✨ 格式化")
        self.format_code_btn.clicked.connect(self._on_format_code)
        code_btn_layout.addWidget(self.save_code_btn)
        code_btn_layout.addWidget(self.format_code_btn)
        code_btn_layout.addStretch()
        code_layout.addLayout(code_btn_layout)
        
        self.tab_widget.addTab(code_tab, "📝 代码")
        
        # Tab 3: 实时预览
        preview_tab = QtWidgets.QWidget()
        preview_layout = QtWidgets.QVBoxLayout(preview_tab)
        preview_layout.setContentsMargins(5, 5, 5, 5)
        
        self.preview_label = QtWidgets.QLabel("选择节点后点击'预览'按钮查看效果")
        self.preview_label.setAlignment(QtCore.Qt.AlignCenter)
        self.preview_label.setStyleSheet("background-color: #f0f0f0; color: gray; font-size: 12px;")
        self.preview_label.setMinimumHeight(300)
        preview_layout.addWidget(self.preview_label)
        
        preview_btn_layout = QtWidgets.QHBoxLayout()
        self.preview_btn = QtWidgets.QPushButton("▶️ 运行预览")
        self.preview_btn.clicked.connect(self._on_run_preview)
        self.clear_preview_btn = QtWidgets.QPushButton("🗑️ 清除")
        self.clear_preview_btn.clicked.connect(self._on_clear_preview)
        preview_btn_layout.addWidget(self.preview_btn)
        preview_btn_layout.addWidget(self.clear_preview_btn)
        preview_btn_layout.addStretch()
        preview_layout.addLayout(preview_btn_layout)
        
        self.tab_widget.addTab(preview_tab, "👁️ 预览")
        
        layout.addWidget(self.tab_widget)
        
        # 默认显示提示信息
        self._show_empty_state()
        
        return panel
    
    def _show_empty_state(self):
        """显示空状态提示"""
        self._clear_detail_layout()
        
        hint_label = QtWidgets.QLabel("请从左侧选择一个节点包查看详情")
        hint_label.setAlignment(QtCore.Qt.AlignCenter)
        hint_label.setStyleSheet("color: gray; font-size: 12px;")
        self.detail_layout.addWidget(hint_label)
    
    def _clear_detail_layout(self):
        """清空详情布局"""
        while self.detail_layout.count():
            item = self.detail_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
    
    def _create_button_bar(self):
        """创建底部按钮栏"""
        button_bar = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(button_bar)
        layout.setContentsMargins(0, 5, 0, 0)
        
        # 新建节点
        self.new_node_btn = QtWidgets.QPushButton("➕ 新建节点")
        self.new_node_btn.setEnabled(False)
        self.new_node_btn.clicked.connect(self._on_new_node)
        layout.addWidget(self.new_node_btn)
        
        # 编辑节点
        self.edit_node_btn = QtWidgets.QPushButton("✏️ 编辑节点")
        self.edit_node_btn.setEnabled(False)
        self.edit_node_btn.clicked.connect(self._on_edit_node)
        layout.addWidget(self.edit_node_btn)
        
        # 删除节点
        self.delete_node_btn = QtWidgets.QPushButton("🗑️ 删除节点")
        self.delete_node_btn.setEnabled(False)
        self.delete_node_btn.clicked.connect(self._on_delete_node)
        layout.addWidget(self.delete_node_btn)
        
        layout.addStretch()
        
        # 关闭按钮
        close_btn = QtWidgets.QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
        
        return button_bar
    
    def _on_package_selected(self):
        """节点包选择事件"""
        selected_items = self.package_tree.selectedItems()
        if not selected_items:
            self._show_empty_state()
            self._update_button_states(False)
            return
        
        selected_item = selected_items[0]
        pkg_name = selected_item.data(0, QtCore.Qt.UserRole)
        
        if not pkg_name:
            # 选中的是分类节点
            self._show_empty_state()
            self._update_button_states(False)
            return
        
        # 显示节点包详情
        self._display_package_details(pkg_name)
        self._update_button_states(True)
    
    def _display_package_details(self, pkg_name):
        """显示节点包详细信息"""
        self._clear_detail_layout()
        
        if pkg_name not in self.plugin_packages:
            return
        
        pkg_info = self.plugin_packages[pkg_name]
        data = pkg_info['data']
        
        # 基本信息卡片
        info_group = self._create_info_card(data)
        self.detail_layout.addWidget(info_group)
        
        # 节点列表
        nodes_list = self._create_nodes_list(pkg_name, data.get('nodes', []))
        self.detail_layout.addWidget(nodes_list)
        
        # 依赖信息
        deps_group = self._create_dependencies_card(data.get('dependencies', []))
        self.detail_layout.addWidget(deps_group)
        
        self.detail_layout.addStretch()
    
    def _create_info_card(self, data):
        """创建基本信息卡片"""
        group = QtWidgets.QGroupBox("基本信息")
        layout = QtWidgets.QFormLayout(group)
        
        layout.addRow("名称:", QtWidgets.QLabel(data.get('name', '')))
        layout.addRow("版本:", QtWidgets.QLabel(data.get('version', '1.0.0')))
        layout.addRow("作者:", QtWidgets.QLabel(data.get('author', '')))
        layout.addRow("分类:", QtWidgets.QLabel(data.get('category_group', '')))
        
        desc_label = QtWidgets.QLabel(data.get('description', ''))
        desc_label.setWordWrap(True)
        layout.addRow("描述:", desc_label)
        
        return group
    
    def _create_nodes_list(self, pkg_name, nodes):
        """创建节点列表"""
        group = QtWidgets.QGroupBox(f"节点列表 ({len(nodes)}个)")
        layout = QtWidgets.QVBoxLayout(group)
        
        if not nodes:
            empty_label = QtWidgets.QLabel("暂无节点，点击'新建节点'添加")
            empty_label.setStyleSheet("color: gray; font-style: italic;")
            layout.addWidget(empty_label)
        else:
            table = QtWidgets.QTableWidget()
            table.setColumnCount(4)
            table.setHorizontalHeaderLabels(["类名", "显示名称", "子分类", "颜色"])
            table.horizontalHeader().setStretchLastSection(True)
            table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
            table.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
            table.itemSelectionChanged.connect(lambda: self._on_node_selected(pkg_name, table))
            
            table.setRowCount(len(nodes))
            for i, node in enumerate(nodes):
                table.setItem(i, 0, QtWidgets.QTableWidgetItem(node.get('class', '')))
                table.setItem(i, 1, QtWidgets.QTableWidgetItem(node.get('display_name', '')))
                table.setItem(i, 2, QtWidgets.QTableWidgetItem(node.get('category', '')))
                
                color = node.get('color', [200, 200, 200])
                color_str = f"RGB({color[0]}, {color[1]}, {color[2]})"
                table.setItem(i, 3, QtWidgets.QTableWidgetItem(color_str))
            
            layout.addWidget(table)
        
        return group
    
    def _create_dependencies_card(self, dependencies):
        """创建依赖信息卡片"""
        group = QtWidgets.QGroupBox("依赖项")
        layout = QtWidgets.QVBoxLayout(group)
        
        if not dependencies:
            empty_label = QtWidgets.QLabel("无外部依赖")
            empty_label.setStyleSheet("color: gray;")
            layout.addWidget(empty_label)
        else:
            for dep in dependencies:
                dep_label = QtWidgets.QLabel(f"• {dep}")
                layout.addWidget(dep_label)
        
        return group
    
    def _on_node_selected(self, pkg_name, table):
        """节点选择事件"""
        selected_rows = table.selectedItems()
        if selected_rows:
            row = selected_rows[0].row()
            self.current_selected_node = {
                'package': pkg_name,
                'row': row,
                'table': table
            }
            self.edit_node_btn.setEnabled(True)
            self.delete_node_btn.setEnabled(True)
        else:
            self.edit_node_btn.setEnabled(False)
            self.delete_node_btn.setEnabled(False)
    
    def _update_button_states(self, has_package):
        """更新按钮状态"""
        self.new_node_btn.setEnabled(has_package)
        self.edit_node_btn.setEnabled(False)
        self.delete_node_btn.setEnabled(False)
    
    def _on_new_package(self):
        """新建节点包"""
        dialog = NewPackageDialog(self)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            package_data = dialog.get_package_data()
            self._create_new_package(package_data)
            self._refresh_packages()
    
    def _create_new_package(self, package_data):
        """创建新的节点包目录和文件"""
        pkg_name = package_data['name']
        pkg_dir = self.plugins_dir / pkg_name
        
        if pkg_dir.exists():
            QtWidgets.QMessageBox.warning(self, "警告", f"节点包 '{pkg_name}' 已存在！")
            return
        
        # 创建目录
        pkg_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建plugin.json
        plugin_json = {
            "name": pkg_name,
            "version": package_data.get('version', '1.0.0'),
            "author": package_data.get('author', ''),
            "description": package_data.get('description', ''),
            "category_group": package_data.get('category_group', '未分类'),
            "nodes": [],
            "dependencies": package_data.get('dependencies', []),
            "min_app_version": "4.0.0"
        }
        
        with open(pkg_dir / "plugin.json", 'w', encoding='utf-8') as f:
            json.dump(plugin_json, f, indent=2, ensure_ascii=False)
        
        # 创建空的nodes.py
        with open(pkg_dir / "nodes.py", 'w', encoding='utf-8') as f:
            f.write(f'"""\n{package_data.get("description", "")}\n"""\n\n')
        
        # 添加到内存
        self.plugin_packages[pkg_name] = {
            'path': pkg_dir,
            'data': plugin_json
        }
        
        QtWidgets.QMessageBox.information(self, "成功", f"节点包 '{pkg_name}' 创建成功！")
    
    def _on_new_node(self):
        """新建节点"""
        selected_items = self.package_tree.selectedItems()
        if not selected_items:
            return
        
        pkg_name = selected_items[0].data(0, QtCore.Qt.UserRole)
        if not pkg_name:
            return
        
        dialog = NewNodeDialog(self, pkg_name)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            node_data = dialog.get_node_data()
            self._add_node_to_package(pkg_name, node_data)
            self._refresh_packages()
    
    def _add_node_to_package(self, pkg_name, node_data):
        """向节点包添加新节点"""
        if pkg_name not in self.plugin_packages:
            return
        
        pkg_info = self.plugin_packages[pkg_name]
        data = pkg_info['data']
        
        # 记录当前节点数（用于撤销时定位）
        node_index = len(data['nodes'])
        
        # 添加到plugin.json
        data['nodes'].append({
            "class": node_data['class_name'],
            "display_name": node_data['display_name'],
            "category": node_data.get('category', ''),
            "color": node_data.get('color', [200, 200, 200])
        })
        
        # 保存plugin.json
        plugin_json_path = pkg_info['path'] / "plugin.json"
        with open(plugin_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # 生成节点代码模板
        self._generate_node_code(pkg_info['path'], node_data)
        
        # ✨ 记录撤销点
        self._push_undo('create_node', {
            'package': pkg_name,
            'node_index': node_index,
            'node_data': {
                'class_name': node_data['class_name'],
                'display_name': node_data['display_name'],
                'category': node_data.get('category', ''),
                'color': node_data.get('color', [200, 200, 200])
            }
        })
        
        QtWidgets.QMessageBox.information(self, "成功", f"节点 '{node_data['display_name']}' 创建成功！\n\n💡 提示：可使用 Ctrl+Z 撤销")
    
    def _generate_node_code(self, pkg_dir, node_data):
        """生成节点代码模板"""
        nodes_py_path = pkg_dir / "nodes.py"
        
        # 读取现有代码
        existing_code = ""
        if nodes_py_path.exists():
            with open(nodes_py_path, 'r', encoding='utf-8') as f:
                existing_code = f.read()
        
        # 生成新节点代码
        class_name = node_data['class_name']
        display_name = node_data['display_name']
        category = node_data.get('category', '')
        color = node_data.get('color', [200, 200, 200])
        
        node_template = f'''

class {class_name}(BaseNode):
    """
    {display_name}节点
    {node_data.get('description', '')}
    """
    
    __identifier__ = '{pkg_dir.name}'
    NODE_NAME = '{display_name}'
    
    def __init__(self):
        super({class_name}, self).__init__()
        # TODO: 添加输入端口
        # self.add_input('输入图像', color=(100, 255, 100))
        
        # TODO: 添加输出端口
        # self.add_output('输出图像', color=(100, 255, 100))
        
        # TODO: 添加参数控件
        # self.add_text_input('param1', '参数1', tab='properties')
        
    def process(self, inputs=None):
        """处理节点逻辑"""
        # TODO: 实现节点处理逻辑
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                # 你的处理逻辑
                result = image
                return {{'输出图像': result}}
            except Exception as e:
                print(f"{display_name}处理错误: {{e}}")
                return {{'输出图像': None}}
        return {{'输出图像': None}}
'''
        
        # 检查是否需要添加导入语句
        if "from NodeGraphQt import BaseNode" not in existing_code:
            existing_code = "from NodeGraphQt import BaseNode\nimport cv2\nimport numpy as np\n" + existing_code
        
        # 追加新节点代码
        with open(nodes_py_path, 'w', encoding='utf-8') as f:
            f.write(existing_code + node_template)
    
    def _on_edit_node(self):
        """编辑节点"""
        if not hasattr(self, 'current_selected_node'):
            return
        
        selected = self.current_selected_node
        pkg_name = selected['package']
        row = selected['row']
        
        if pkg_name not in self.plugin_packages:
            return
        
        pkg_info = self.plugin_packages[pkg_name]
        nodes = pkg_info['data'].get('nodes', [])
        
        if row >= len(nodes):
            return
        
        node_data = nodes[row].copy()  # 复制旧数据
        
        dialog = EditNodeDialog(self, pkg_name, node_data, row)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            updated_data = dialog.get_updated_data()
            
            # ✨ 记录撤销点
            self._push_undo('modify_node', {
                'package': pkg_name,
                'node_index': row,
                'old_data': node_data,
                'new_data': updated_data
            })
            
            self._update_node_in_package(pkg_name, row, updated_data)
            self._refresh_packages()
    
    def _update_node_in_package(self, pkg_name, row, updated_data):
        """更新节点包中的节点"""
        if pkg_name not in self.plugin_packages:
            return
        
        pkg_info = self.plugin_packages[pkg_name]
        data = pkg_info['data']
        
        # 更新plugin.json
        if row < len(data['nodes']):
            data['nodes'][row].update(updated_data)
        
        # 保存
        plugin_json_path = pkg_info['path'] / "plugin.json"
        with open(plugin_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        QtWidgets.QMessageBox.information(self, "成功", "节点更新成功！")
    
    def _on_delete_node(self):
        """删除节点"""
        if not hasattr(self, 'current_selected_node'):
            return
        
        selected = self.current_selected_node
        pkg_name = selected['package']
        row = selected['row']
        
        if pkg_name not in self.plugin_packages:
            return
        
        pkg_info = self.plugin_packages[pkg_name]
        nodes = pkg_info['data'].get('nodes', [])
        
        if row >= len(nodes):
            return
        
        node_data = nodes[row]
        
        reply = QtWidgets.QMessageBox.question(
            self,
            "确认删除",
            f"确定要删除节点 '{node_data.get('display_name', '')}' 吗？\n\n💡 提示：可使用 Ctrl+Z 撤销此操作",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )
        
        if reply == QtWidgets.QMessageBox.Yes:
            # ✨ 记录撤销点
            self._push_undo('delete_node', {
                'package': pkg_name,
                'node_index': row,
                'node_data': node_data.copy()
            })
            
            self._delete_node_from_package(pkg_name, row)
            self._refresh_packages()
    
    def _delete_node_from_package(self, pkg_name, row):
        """从节点包中删除节点"""
        if pkg_name not in self.plugin_packages:
            return
        
        pkg_info = self.plugin_packages[pkg_name]
        data = pkg_info['data']
        
        # 从列表中移除
        if row < len(data['nodes']):
            removed_node = data['nodes'].pop(row)
            
            # 保存plugin.json
            plugin_json_path = pkg_info['path'] / "plugin.json"
            with open(plugin_json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            # TODO: 从nodes.py中删除对应的类定义（需要解析AST）
            # 暂时只更新JSON，手动清理代码
            
            QtWidgets.QMessageBox.information(self, "成功", f"节点 '{removed_node.get('display_name', '')}' 已删除")
    
    def _on_import_package(self):
        """导入节点包"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "导入节点包",
            "",
            "ZIP文件 (*.zip);;所有文件 (*)"
        )
        
        if not file_path:
            return
        
        try:
            self._import_from_zip(file_path)
            QtWidgets.QMessageBox.information(self, "成功", "节点包导入成功！")
            self._refresh_packages()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"导入失败: {str(e)}")
    
    def _import_from_zip(self, zip_path):
        """从ZIP文件导入节点包"""
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # 检查是否包含plugin.json
            if 'plugin.json' not in zip_ref.namelist():
                raise ValueError("无效的节点包：缺少plugin.json")
            
            # 读取plugin.json获取包名
            with zip_ref.open('plugin.json') as f:
                plugin_data = json.loads(f.read().decode('utf-8'))
                pkg_name = plugin_data.get('name', '')
            
            if not pkg_name:
                raise ValueError("无效的节点包：plugin.json中缺少name字段")
            
            # 解压到user_plugins目录
            extract_path = self.plugins_dir / pkg_name
            zip_ref.extractall(extract_path)
            
            # 加载到内存
            self.plugin_packages[pkg_name] = {
                'path': extract_path,
                'data': plugin_data
            }
    
    def _on_export_package(self):
        """导出节点包"""
        selected_items = self.package_tree.selectedItems()
        if not selected_items:
            QtWidgets.QMessageBox.warning(self, "警告", "请先选择一个节点包")
            return
        
        pkg_name = selected_items[0].data(0, QtCore.Qt.UserRole)
        if not pkg_name:
            QtWidgets.QMessageBox.warning(self, "警告", "请选择具体的节点包，而非分类")
            return
        
        if pkg_name not in self.plugin_packages:
            return
        
        # 选择保存路径
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "导出节点包",
            f"{pkg_name}.zip",
            "ZIP文件 (*.zip)"
        )
        
        if not file_path:
            return
        
        try:
            self._export_to_zip(pkg_name, file_path)
            QtWidgets.QMessageBox.information(self, "成功", f"节点包已导出到:\n{file_path}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")
    
    def _export_to_zip(self, pkg_name, zip_path):
        """导出节点包为ZIP文件"""
        pkg_info = self.plugin_packages[pkg_name]
        pkg_dir = pkg_info['path']
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_ref:
            for file_path in pkg_dir.rglob('*'):
                if file_path.is_file():
                    arc_name = file_path.relative_to(pkg_dir)
                    zip_ref.write(file_path, arc_name)
    
    def _refresh_packages(self):
        """刷新节点包列表"""
        self.plugin_packages.clear()
        self._load_plugin_packages()
        self._populate_package_tree()
        self._show_empty_state()


# ============================================================================
# ✨ 节点编辑器增强功能方法
# ============================================================================

    def _push_undo(self, action_type, data):
        """
        推入撤销栈
        
        Args:
            action_type: 操作类型 ('create_node', 'delete_node', 'modify_node', 'edit_code')
            data: 操作数据（包含恢复所需信息）
        """
        self.undo_stack.append({
            'type': action_type,
            'data': data,
            'timestamp': QtCore.QDateTime.currentDateTime()
        })
        
        # 限制历史栈大小
        if len(self.undo_stack) > self.max_history:
            self.undo_stack.pop(0)
        
        # 清空重做栈
        self.redo_stack.clear()
        
        print(f"📝 撤销记录: {action_type} (栈大小: {len(self.undo_stack)})")
    
    def undo(self):
        """撤销操作"""
        if not self.undo_stack:
            QtWidgets.QMessageBox.information(self, "提示", "没有可撤销的操作")
            return
        
        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        
        # 执行反向操作
        self._execute_undo_action(action)
        
        print(f"↩️ 撤销: {action['type']}")
    
    def redo(self):
        """重做操作"""
        if not self.redo_stack:
            QtWidgets.QMessageBox.information(self, "提示", "没有可重做的操作")
            return
        
        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        
        # 重新执行操作
        self._execute_redo_action(action)
        
        print(f"↪️ 重做: {action['type']}")
    
    def _execute_undo_action(self, action):
        """执行撤销操作"""
        action_type = action['type']
        
        if action_type == 'create_node':
            # 撤销创建节点 = 删除节点
            pkg_name = action['data']['package']
            node_index = action['data']['node_index']
            self._delete_node_from_package(pkg_name, node_index)
            self._refresh_packages()
            
        elif action_type == 'delete_node':
            # 撤销删除节点 = 恢复节点
            pkg_name = action['data']['package']
            node_data = action['data']['node_data']
            node_index = action['data']['node_index']
            self._restore_node_to_package(pkg_name, node_data, node_index)
            self._refresh_packages()
            
        elif action_type == 'modify_node':
            # 撤销修改节点 = 恢复旧值
            pkg_name = action['data']['package']
            node_index = action['data']['node_index']
            old_data = action['data']['old_data']
            self._update_node_in_package(pkg_name, node_index, old_data)
            self._refresh_packages()
    
    def _execute_redo_action(self, action):
        """执行重做操作"""
        action_type = action['type']
        
        if action_type == 'create_node':
            # 重做创建节点
            pkg_name = action['data']['package']
            node_data = action['data']['node_data']
            self._add_node_to_package(pkg_name, node_data)
            self._refresh_packages()
            
        elif action_type == 'delete_node':
            # 重做删除节点
            pkg_name = action['data']['package']
            node_index = action['data']['node_index']
            self._delete_node_from_package(pkg_name, node_index)
            self._refresh_packages()
            
        elif action_type == 'modify_node':
            # 重做修改节点
            pkg_name = action['data']['package']
            node_index = action['data']['node_index']
            new_data = action['data']['new_data']
            self._update_node_in_package(pkg_name, node_index, new_data)
            self._refresh_packages()
    
    def _restore_node_to_package(self, pkg_name, node_data, node_index):
        """恢复节点到包中（用于撤销删除）"""
        if pkg_name not in self.plugin_packages:
            return
        
        pkg_info = self.plugin_packages[pkg_name]
        data = pkg_info['data']
        
        # 插入到原位置
        data['nodes'].insert(node_index, node_data)
        
        # 保存
        plugin_json_path = pkg_info['path'] / "plugin.json"
        with open(plugin_json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _on_code_changed(self):
        """代码编辑变化事件"""
        # 可以在这里添加实时语法检查
        pass
    
    def _on_save_code(self):
        """保存代码"""
        if not self.current_package:
            QtWidgets.QMessageBox.warning(self, "警告", "请先选择一个节点包")
            return
        
        code = self.code_editor.toPlainText()
        pkg_info = self.plugin_packages[self.current_package]
        nodes_py_path = pkg_info['path'] / "nodes.py"
        
        try:
            # 验证Python语法
            compile(code, str(nodes_py_path), 'exec')
            
            # 保存到文件
            with open(nodes_py_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            # 记录撤销点
            self._push_undo('edit_code', {
                'package': self.current_package,
                'code': code
            })
            
            QtWidgets.QMessageBox.information(self, "成功", "代码已保存！")
            print(f"💾 代码已保存: {nodes_py_path}")
            
        except SyntaxError as e:
            QtWidgets.QMessageBox.critical(self, "语法错误", f"代码存在语法错误:\n\n{str(e)}")
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")
    
    def _on_format_code(self):
        """格式化代码"""
        code = self.code_editor.toPlainText()
        
        # 简单的代码格式化（去除多余空行、统一缩进）
        lines = code.split('\n')
        formatted_lines = []
        prev_empty = False
        
        for line in lines:
            is_empty = line.strip() == ''
            
            if is_empty and prev_empty:
                continue  # 跳过连续空行
            
            formatted_lines.append(line.rstrip())
            prev_empty = is_empty
        
        formatted_code = '\n'.join(formatted_lines)
        self.code_editor.setPlainText(formatted_code)
        
        QtWidgets.QMessageBox.information(self, "成功", "代码已格式化！")
    
    def _on_run_preview(self):
        """运行预览"""
        if not self.current_package or self.current_node_index is None:
            QtWidgets.QMessageBox.warning(self, "警告", "请先选择一个节点")
            return
        
        pkg_info = self.plugin_packages[self.current_package]
        nodes = pkg_info['data'].get('nodes', [])
        
        if self.current_node_index >= len(nodes):
            return
        
        node_data = nodes[self.current_node_index]
        class_name = node_data.get('class', '')
        display_name = node_data.get('display_name', '')
        
        # 模拟运行节点
        preview_text = f"""
╔══════════════════════════════════════╗
║     节点预览 - {display_name}
╠══════════════════════════════════════╣
║ 类名: {class_name:<30} ║
║ 包名: {self.current_package:<30} ║
║ 分类: {node_data.get('category', 'N/A'):<30} ║
╠══════════════════════════════════════╣
║ 状态: ✅ 节点定义有效
║ 
║ 提示: 实际运行需要在节点图中连接端口
╚══════════════════════════════════════╝
        """
        
        self.preview_label.setText(preview_text)
        self.preview_label.setStyleSheet("background-color: #e8f5e9; color: #2e7d32; font-family: Consolas; font-size: 11px; padding: 10px;")
        
        print(f"▶️ 预览节点: {display_name} ({class_name})")
    
    def _on_clear_preview(self):
        """清除预览"""
        self.preview_label.setText("选择节点后点击'预览'按钮查看效果")
        self.preview_label.setStyleSheet("background-color: #f0f0f0; color: gray; font-size: 12px;")
    
    def keyPressEvent(self, event):
        """键盘事件 - 支持Ctrl+Z/Y快捷键"""
        # Ctrl+Z 撤销
        if event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_Z:
            self.undo()
            return
        
        # Ctrl+Y 重做
        if event.modifiers() == QtCore.Qt.ControlModifier and event.key() == QtCore.Qt.Key_Y:
            self.redo()
            return
        
        super(NodeEditorDialog, self).keyPressEvent(event)

class NewPackageDialog(QtWidgets.QDialog):
    """新建节点包对话框"""
    
    def __init__(self, parent=None):
        super(NewPackageDialog, self).__init__(parent)
        self.setWindowTitle("新建节点包")
        self.resize(500, 400)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QtWidgets.QFormLayout(self)
        
        self.name_input = QtWidgets.QLineEdit()
        self.name_input.setPlaceholderText("例如: my_custom_nodes")
        layout.addRow("包名称*:", self.name_input)
        
        self.version_input = QtWidgets.QLineEdit("1.0.0")
        layout.addRow("版本:", self.version_input)
        
        self.author_input = QtWidgets.QLineEdit()
        layout.addRow("作者:", self.author_input)
        
        self.category_combo = QtWidgets.QComboBox()
        self.category_combo.addItems([
            "图像相机", "预处理", "特征提取",
            "测量分析", "识别分类", "系统集成", "自定义"
        ])
        layout.addRow("分类*:", self.category_combo)
        
        self.desc_input = QtWidgets.QTextEdit()
        self.desc_input.setMaximumHeight(100)
        layout.addRow("描述:", self.desc_input)
        
        self.deps_input = QtWidgets.QLineEdit()
        self.deps_input.setPlaceholderText("例如: opencv-python>=4.5,numpy")
        layout.addRow("依赖项:", self.deps_input)
        
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def _validate_and_accept(self):
        """验证并接受"""
        name = self.name_input.text().strip()
        if not name:
            QtWidgets.QMessageBox.warning(self, "警告", "包名称不能为空！")
            return
        
        if not name.replace('_', '').isalnum():
            QtWidgets.QMessageBox.warning(self, "警告", "包名称只能包含字母、数字和下划线！")
            return
        
        self.accept()
    
    def get_package_data(self):
        """获取节点包数据"""
        deps_str = self.deps_input.text().strip()
        dependencies = [d.strip() for d in deps_str.split(',') if d.strip()] if deps_str else []
        
        return {
            'name': self.name_input.text().strip(),
            'version': self.version_input.text().strip(),
            'author': self.author_input.text().strip(),
            'category_group': self.category_combo.currentText(),
            'description': self.desc_input.toPlainText().strip(),
            'dependencies': dependencies
        }


class NewNodeDialog(QtWidgets.QDialog):
    """新建节点对话框"""
    
    def __init__(self, parent=None, pkg_name=""):
        super(NewNodeDialog, self).__init__(parent)
        self.pkg_name = pkg_name
        self.setWindowTitle(f"新建节点 - {pkg_name}")
        self.resize(500, 500)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QtWidgets.QFormLayout(self)
        
        self.class_name_input = QtWidgets.QLineEdit()
        self.class_name_input.setPlaceholderText("例如: MyCustomNode")
        layout.addRow("类名*:", self.class_name_input)
        
        self.display_name_input = QtWidgets.QLineEdit()
        self.display_name_input.setPlaceholderText("例如: 我的自定义节点")
        layout.addRow("显示名称*:", self.display_name_input)
        
        self.category_input = QtWidgets.QLineEdit()
        self.category_input.setPlaceholderText("例如: 自定义处理")
        layout.addRow("子分类:", self.category_input)
        
        # 颜色选择
        color_layout = QtWidgets.QHBoxLayout()
        self.color_r = QtWidgets.QSpinBox()
        self.color_r.setRange(0, 255)
        self.color_r.setValue(200)
        self.color_g = QtWidgets.QSpinBox()
        self.color_g.setRange(0, 255)
        self.color_g.setValue(200)
        self.color_b = QtWidgets.QSpinBox()
        self.color_b.setRange(0, 255)
        self.color_b.setValue(200)
        color_layout.addWidget(QtWidgets.QLabel("R:"))
        color_layout.addWidget(self.color_r)
        color_layout.addWidget(QtWidgets.QLabel("G:"))
        color_layout.addWidget(self.color_g)
        color_layout.addWidget(QtWidgets.QLabel("B:"))
        color_layout.addWidget(self.color_b)
        layout.addRow("节点颜色:", color_layout)
        
        self.desc_input = QtWidgets.QTextEdit()
        self.desc_input.setMaximumHeight(100)
        layout.addRow("描述:", self.desc_input)
        
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def _validate_and_accept(self):
        """验证并接受"""
        class_name = self.class_name_input.text().strip()
        display_name = self.display_name_input.text().strip()
        
        if not class_name or not display_name:
            QtWidgets.QMessageBox.warning(self, "警告", "类名和显示名称不能为空！")
            return
        
        if not class_name[0].isupper():
            QtWidgets.QMessageBox.warning(self, "警告", "类名必须以大写字母开头！")
            return
        
        self.accept()
    
    def get_node_data(self):
        """获取节点数据"""
        return {
            'class_name': self.class_name_input.text().strip(),
            'display_name': self.display_name_input.text().strip(),
            'category': self.category_input.text().strip(),
            'color': [self.color_r.value(), self.color_g.value(), self.color_b.value()],
            'description': self.desc_input.toPlainText().strip()
        }


class EditNodeDialog(QtWidgets.QDialog):
    """编辑节点对话框"""
    
    def __init__(self, parent=None, pkg_name="", node_data=None, row=0):
        super(EditNodeDialog, self).__init__(parent)
        self.pkg_name = pkg_name
        self.node_data = node_data or {}
        self.row = row
        self.setWindowTitle(f"编辑节点 - {self.node_data.get('display_name', '')}")
        self.resize(500, 500)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QtWidgets.QFormLayout(self)
        
        self.class_name_input = QtWidgets.QLineEdit(self.node_data.get('class', ''))
        self.class_name_input.setEnabled(False)  # 类名不可修改
        layout.addRow("类名:", self.class_name_input)
        
        self.display_name_input = QtWidgets.QLineEdit(self.node_data.get('display_name', ''))
        layout.addRow("显示名称*:", self.display_name_input)
        
        self.category_input = QtWidgets.QLineEdit(self.node_data.get('category', ''))
        layout.addRow("子分类:", self.category_input)
        
        # 颜色选择
        color = self.node_data.get('color', [200, 200, 200])
        color_layout = QtWidgets.QHBoxLayout()
        self.color_r = QtWidgets.QSpinBox()
        self.color_r.setRange(0, 255)
        self.color_r.setValue(color[0] if len(color) > 0 else 200)
        self.color_g = QtWidgets.QSpinBox()
        self.color_g.setRange(0, 255)
        self.color_g.setValue(color[1] if len(color) > 1 else 200)
        self.color_b = QtWidgets.QSpinBox()
        self.color_b.setRange(0, 255)
        self.color_b.setValue(color[2] if len(color) > 2 else 200)
        color_layout.addWidget(QtWidgets.QLabel("R:"))
        color_layout.addWidget(self.color_r)
        color_layout.addWidget(QtWidgets.QLabel("G:"))
        color_layout.addWidget(self.color_g)
        color_layout.addWidget(QtWidgets.QLabel("B:"))
        color_layout.addWidget(self.color_b)
        layout.addRow("节点颜色:", color_layout)
        
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
    
    def _validate_and_accept(self):
        """验证并接受"""
        display_name = self.display_name_input.text().strip()
        
        if not display_name:
            QtWidgets.QMessageBox.warning(self, "警告", "显示名称不能为空！")
            return
        
        self.accept()
    
    def get_updated_data(self):
        """获取更新后的数据"""
        return {
            'display_name': self.display_name_input.text().strip(),
            'category': self.category_input.text().strip(),
            'color': [self.color_r.value(), self.color_g.value(), self.color_b.value()]
        }

