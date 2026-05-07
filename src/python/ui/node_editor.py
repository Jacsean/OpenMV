"""
节点编辑器 - 节点管理界面

功能:
- 浏览所有节点（内置节点 + 市场节点）
- 添加新内置节点
- 删除节点或市场插件
- 编辑节点属性（显示名称、分组、是否启用）
- 导入/导出节点配置
- 刷新节点库
- 市场节点管理（本地删除、网站下载）
"""

import os
import json
import ast
import shutil
from pathlib import Path
from PySide2 import QtWidgets, QtCore, QtGui


class TreeBranchDelegate(QtWidgets.QStyledItemDelegate):
    """自定义树形视图委托，绘制分支连线"""
    
    def paint(self, painter, option, index):
        # 先调用父类绘制
        super(TreeBranchDelegate, self).paint(painter, option, index)
        
        tree = option.widget
        if not isinstance(tree, QtWidgets.QTreeWidget):
            return
        
        # 获取节点信息
        item = tree.itemFromIndex(index)
        if not item:
            return
        
        # 计算层级
        indent = tree.indentation()
        level = 0
        parent = item.parent()
        while parent:
            level += 1
            parent = parent.parent()
        
        # 绘制连线
        painter.save()
        painter.setPen(QtGui.QPen(QtGui.QColor(180, 180, 180), 1))
        
        rect = option.rect
        x = 10  # 起始位置
        
        # 根节点（level = 0）：如果有子节点，绘制垂直线
        if level == 0:
            if item.childCount() > 0:
                # 绘制根节点下方的垂直线
                line_x = x - 5
                painter.drawLine(line_x, rect.top() + 8, line_x, rect.bottom())
                
                # 绘制子节点的水平连线起点
                child_y = rect.bottom()
                painter.drawLine(line_x, child_y, line_x + indent // 2, child_y)
        else:
            # 非根节点：绘制水平连线
            line_y = rect.center().y()
            start_x = x + (level - 1) * indent - 5
            end_x = x + level * indent - 5
            painter.drawLine(start_x, line_y, end_x, line_y)
            
            # 绘制垂直连线（如果不是最后一个子节点或有子节点）
            has_next_sibling = False
            parent_item = item.parent()
            if parent_item:
                for i in range(parent_item.childCount()):
                    if parent_item.child(i) == item:
                        if i < parent_item.childCount() - 1:
                            has_next_sibling = True
                        break
            
            if has_next_sibling or item.childCount() > 0:
                line_x = x + level * indent - 5
                if item.childCount() > 0:
                    painter.drawLine(line_x, rect.top() + 8, line_x, rect.bottom())
                else:
                    painter.drawLine(line_x, rect.top() + 8, line_x, rect.center().y())
        
        painter.restore()


class NodeEditorDialog(QtWidgets.QDialog):
    """
    节点编辑器对话框
    
    提供可视化的节点管理界面，支持节点的完整生命周期管理
    """

    def __init__(self, parent=None, plugin_manager=None, plugins_dir=None):
        super(NodeEditorDialog, self).__init__(parent)
        self.plugin_manager = plugin_manager
        self.plugins_dir = plugins_dir  # 保留向后兼容
        self.setWindowTitle("节点编辑器")
        self.resize(600, 400)

        # 节点数据
        self.builtin_plugin_info = None
        self.marketplace_plugins = {}
        
        # 当前选中状态
        self.current_selection = {
            'type': None,  # 'builtin_root', 'group', 'node', 'market_local', 'market_remote'
            'name': None,
            'data': None
        }

        # 构建UI
        self._setup_ui()
        
        # 加载数据
        self._load_plugin_data()

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
        
        try:
            splitter.setAnimated(False)
        except AttributeError:
            pass
        
        # 左侧：节点树形视图（宽度约为右侧的1/4）
        left_panel = self._create_left_panel()
        left_panel.setMinimumWidth(160)
        left_panel.setMaximumWidth(200)
        splitter.addWidget(left_panel)

        # 右侧：详情编辑区
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 4)  # 左侧:右侧 = 1:4
        main_layout.addWidget(splitter)

    def _create_toolbar(self):
        """创建顶部工具栏"""
        toolbar = QtWidgets.QToolBar()
        toolbar.setIconSize(QtCore.QSize(24, 24))

        # 增加节点
        add_action = toolbar.addAction("➕ 增加")
        add_action.triggered.connect(self._on_add_node)
        add_action.setToolTip("添加新内置节点到选中的分组")

        # 删除节点/插件
        delete_action = toolbar.addAction("➖ 删除")
        delete_action.triggered.connect(self._on_delete)
        delete_action.setToolTip("删除选中的节点或市场插件")

        toolbar.addSeparator()

        # 导入节点配置
        import_action = toolbar.addAction("📥 导入")
        import_action.triggered.connect(self._on_import)
        import_action.setToolTip("导入市场节点配置文件")

        # 导出节点配置
        export_action = toolbar.addAction("📤 导出")
        export_action.triggered.connect(self._on_export)
        export_action.setToolTip("导出当前节点配置")

        toolbar.addSeparator()

        # 刷新节点库
        refresh_action = toolbar.addAction("🔄 刷新节点库")
        refresh_action.triggered.connect(self._on_refresh_node_library)
        refresh_action.setToolTip("刷新节点库并重新加载所有节点")

        # 帮助
        help_action = toolbar.addAction("❓ 帮助")
        help_action.triggered.connect(self._on_help)
        help_action.setToolTip("打开帮助文档")

        return toolbar

    def _create_left_panel(self):
        """创建左侧面板（节点树形视图）"""
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title_label = QtWidgets.QLabel("节点列表")
        title_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        layout.addWidget(title_label)

        # 树形视图
        self.node_tree = QtWidgets.QTreeWidget()
        self.node_tree.setHeaderLabels(["名称"])
        self.node_tree.setColumnWidth(0, 140)
        self.node_tree.setIndentation(18)
        
        # 设置自定义委托绘制树状连线
        self.node_tree.setItemDelegate(TreeBranchDelegate(self.node_tree))
        
        # 移除默认的展开/折叠图标
        self.node_tree.setStyleSheet("""
            QTreeWidget::branch {
                image: none;
            }
            QTreeWidget::item {
                padding: 2px 0px;
            }
        """)
        
        self.node_tree.itemSelectionChanged.connect(self._on_tree_selection_changed)
        layout.addWidget(self.node_tree)

        return panel

    def _create_right_panel(self):
        """创建右侧面板（详情编辑区）"""
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)

        # 标题
        title_label = QtWidgets.QLabel("详情")
        title_label.setFont(QtGui.QFont("Arial", 10, QtGui.QFont.Bold))
        layout.addWidget(title_label)

        # 滚动区域
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        layout.addWidget(scroll)

        # 详情内容widget
        self.detail_widget = QtWidgets.QWidget()
        self.detail_layout = QtWidgets.QVBoxLayout(self.detail_widget)
        self.detail_layout.setSpacing(10)
        scroll.setWidget(self.detail_widget)

        return panel

    def _load_plugin_data(self):
        """加载插件数据"""
        try:
            # 加载内置插件信息
            builtin_path = Path(__file__).parent.parent / "plugin_packages" / "builtin"
            plugin_json = builtin_path / "plugin.json"
            
            if plugin_json.exists():
                with open(plugin_json, 'r', encoding='utf-8') as f:
                    self.builtin_plugin_info = json.load(f)
            
            # 加载市场插件
            marketplace_path = Path(__file__).parent.parent / "plugin_packages" / "marketplace"
            if marketplace_path.exists():
                for plugin_dir in marketplace_path.iterdir():
                    if plugin_dir.is_dir():
                        pkg_json = plugin_dir / "plugin.json"
                        if pkg_json.exists():
                            try:
                                with open(pkg_json, 'r', encoding='utf-8') as f:
                                    self.marketplace_plugins[plugin_dir.name] = {
                                        'path': plugin_dir,
                                        'data': json.load(f)
                                    }
                            except Exception as e:
                                print(f"加载市场插件失败 {plugin_dir.name}: {e}")
            
            # 刷新树视图
            self._refresh_tree()
        except Exception as e:
            print(f"加载插件数据失败: {e}")

    def _refresh_tree(self):
        """刷新树形视图"""
        self.node_tree.clear()

        # === 内置节点 ===
        builtin_root = QtWidgets.QTreeWidgetItem(["内置节点"])
        builtin_root.setIcon(0, QtGui.QIcon.fromTheme("package"))
        builtin_root.setData(0, QtCore.Qt.UserRole, {
            'type': 'builtin_root',
            'name': 'builtin'
        })

        if self.builtin_plugin_info:
            # 获取分组顺序
            group_order = self.builtin_plugin_info.get('group', [])
            groups = {}
            
            # 按分组组织节点
            for node_def in self.builtin_plugin_info.get('nodes', []):
                identifier = node_def.get('__identifier__', '未分类')
                if identifier not in groups:
                    groups[identifier] = []
                groups[identifier].append(node_def)
            
            # 按照 group_order 排序分组
            ordered_groups = []
            for group_id in group_order:
                if group_id in groups:
                    ordered_groups.append((group_id, groups[group_id]))
                    del groups[group_id]
            # 添加剩余未排序的分组
            for group_id, nodes in sorted(groups.items()):
                ordered_groups.append((group_id, nodes))
            
            # 创建分组节点
            group_display_names = {
                'Image_Source': '图像源',
                'Image_Analysis': '图像分析',
                'Image_Transform': '图像变换',
                'Image_Process': '图像处理',
                'Integration': '系统集成',
                'OCR': 'OCR',
                'YOLO': 'YOLO'
            }
            
            for group_id, nodes in ordered_groups:
                display_name = group_display_names.get(group_id, group_id)
                group_item = QtWidgets.QTreeWidgetItem([display_name])
                group_item.setData(0, QtCore.Qt.UserRole, {
                    'type': 'group',
                    'name': group_id,
                    'display_name': display_name
                })
                
                # 添加节点
                for node in sorted(nodes, key=lambda x: x.get('display_name', '')):
                    node_name = node.get('display_name', node.get('class', ''))
                    node_item = QtWidgets.QTreeWidgetItem([node_name])
                    node_item.setData(0, QtCore.Qt.UserRole, {
                        'type': 'node',
                        'name': node.get('class', ''),
                        'data': node
                    })
                    group_item.addChild(node_item)
                
                builtin_root.addChild(group_item)

        self.node_tree.addTopLevelItem(builtin_root)

        # === 市场节点 ===
        market_root = QtWidgets.QTreeWidgetItem(["市场节点"])
        market_root.setIcon(0, QtGui.QIcon.fromTheme("cloud"))
        market_root.setData(0, QtCore.Qt.UserRole, {
            'type': 'market_root',
            'name': 'marketplace'
        })

        # 本地插件
        local_item = QtWidgets.QTreeWidgetItem(["本地"])
        local_item.setData(0, QtCore.Qt.UserRole, {
            'type': 'market_local_root',
            'name': 'local'
        })
        
        for pkg_name, pkg_info in sorted(self.marketplace_plugins.items()):
            pkg_version = pkg_info['data'].get('version', '1.0.0')
            node_count = len(pkg_info['data'].get('nodes', []))
            display_name = f"{pkg_name} (v{pkg_version}, {node_count}节点)"
            
            pkg_item = QtWidgets.QTreeWidgetItem([display_name])
            pkg_item.setData(0, QtCore.Qt.UserRole, {
                'type': 'market_local',
                'name': pkg_name,
                'path': str(pkg_info['path']),
                'data': pkg_info['data']
            })
            local_item.addChild(pkg_item)
        
        market_root.addChild(local_item)

        # 网站分享
        remote_item = QtWidgets.QTreeWidgetItem(["网站分享"])
        remote_item.setData(0, QtCore.Qt.UserRole, {
            'type': 'market_remote',
            'name': 'remote'
        })
        
        # 从配置读取或使用默认网址
        remote_url = self._get_remote_url()
        url_item = QtWidgets.QTreeWidgetItem([remote_url])
        url_item.setData(0, QtCore.Qt.UserRole, {
            'type': 'market_remote_url',
            'name': remote_url,
            'url': remote_url
        })
        remote_item.addChild(url_item)
        
        market_root.addChild(remote_item)

        self.node_tree.addTopLevelItem(market_root)

        # 展开所有节点
        self.node_tree.expandAll()

    def _get_remote_url(self):
        """获取远程插件仓库URL"""
        # 从配置文件读取，默认使用示例URL
        config_path = Path(__file__).parent.parent / "config" / "plugins.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    return config.get('remote_repo_url', 'https://example.com/plugins')
            except:
                pass
        return 'https://example.com/plugins'

    def _clear_detail_layout(self):
        """清空详情布局"""
        while self.detail_layout.count() > 0:
            item = self.detail_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
            # 也需要删除布局
            layout = item.layout()
            if layout:
                # 递归删除布局中的内容
                while layout.count() > 0:
                    sub_item = layout.takeAt(0)
                    sub_widget = sub_item.widget()
                    if sub_widget:
                        sub_widget.deleteLater()
                layout.deleteLater()

    def _on_tree_selection_changed(self):
        """树形视图选择变化"""
        selected_items = self.node_tree.selectedItems()
        if not selected_items:
            self._clear_detail_layout()
            return

        item = selected_items[0]
        data = item.data(0, QtCore.Qt.UserRole)
        if not data:
            return

        self.current_selection = data
        self._update_detail_panel(data)

    def _update_detail_panel(self, data):
        """更新详情面板"""
        self._clear_detail_layout()
        selection_type = data.get('type')

        if selection_type == 'builtin_root':
            self._show_builtin_root_info()
        elif selection_type == 'group':
            self._show_group_info(data)
        elif selection_type == 'node':
            self._show_node_info(data)
        elif selection_type == 'market_local':
            self._show_market_local_info(data)
        elif selection_type == 'market_local_root':
            self._show_market_local_root_info()
        elif selection_type == 'market_remote':
            self._show_market_remote_info(data)
        elif selection_type == 'market_remote_url':
            self._show_market_remote_url_info(data)
        elif selection_type == 'market_root':
            self._show_market_root_info()

    def _show_builtin_root_info(self):
        """显示内置节点根目录信息"""
        if not self.builtin_plugin_info:
            return

        layout = self.detail_layout

        # 目录路径
        path_label = QtWidgets.QLabel(f"<b>目录:</b> {Path(__file__).parent.parent / 'plugin_packages' / 'builtin'}")
        layout.addWidget(path_label)

        # 节点总数
        total_nodes = len(self.builtin_plugin_info.get('nodes', []))
        nodes_label = QtWidgets.QLabel(f"<b>节点总数:</b> {total_nodes}")
        layout.addWidget(nodes_label)

        # 分组数
        groups = set()
        for node in self.builtin_plugin_info.get('nodes', []):
            groups.add(node.get('__identifier__', ''))
        groups_label = QtWidgets.QLabel(f"<b>分组数:</b> {len(groups)}")
        layout.addWidget(groups_label)

        # 版本信息
        version = self.builtin_plugin_info.get('version', '1.0.0')
        version_label = QtWidgets.QLabel(f"<b>版本:</b> {version}")
        layout.addWidget(version_label)

    def _show_group_info(self, data):
        """显示分组信息"""
        layout = self.detail_layout

        # 分组名称
        name_label = QtWidgets.QLabel(f"<b>分组名称:</b> {data.get('name', '')}")
        layout.addWidget(name_label)

        # 显示名称
        display_label = QtWidgets.QLabel(f"<b>显示名称:</b> {data.get('display_name', '')}")
        layout.addWidget(display_label)

        # 节点数量
        node_count = 0
        if self.builtin_plugin_info:
            for node in self.builtin_plugin_info.get('nodes', []):
                if node.get('__identifier__') == data.get('name'):
                    node_count += 1
        count_label = QtWidgets.QLabel(f"<b>节点数:</b> {node_count}")
        layout.addWidget(count_label)

    def _show_node_info(self, data):
        """显示节点信息（可编辑）"""
        layout = self.detail_layout
        layout.setSpacing(12)
        node_data = data.get('data', {})

        # 创建一个容器widget来组织布局
        container = QtWidgets.QWidget()
        container_layout = QtWidgets.QFormLayout(container)
        container_layout.setSpacing(10)
        container_layout.setLabelAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
        container_layout.setFormAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignTop)

        # 显示名称编辑
        self.node_name_edit = QtWidgets.QLineEdit(node_data.get('display_name', ''))
        self.node_name_edit.setMinimumWidth(200)
        container_layout.addRow("显示名称:", self.node_name_edit)

        # 所属分组选择
        self.group_combo = QtWidgets.QComboBox()
        self.group_combo.setMinimumWidth(200)
        
        group_order = self.builtin_plugin_info.get('group', []) if self.builtin_plugin_info else []
        group_display_names = {
            'Image_Source': '图像源',
            'Image_Analysis': '图像分析',
            'Image_Transform': '图像变换',
            'Image_Process': '图像处理',
            'Integration': '系统集成',
            'OCR': 'OCR',
            'YOLO': 'YOLO'
        }
        
        for group_id in group_order:
            display_name = group_display_names.get(group_id, group_id)
            self.group_combo.addItem(display_name, group_id)
        
        current_group = node_data.get('__identifier__', '')
        index = self.group_combo.findData(current_group)
        if index >= 0:
            self.group_combo.setCurrentIndex(index)
        
        container_layout.addRow("所属分组:", self.group_combo)

        # 是否启用
        self.enabled_check = QtWidgets.QCheckBox()
        self.enabled_check.setChecked(node_data.get('enabled', True))
        container_layout.addRow("是否启用:", self.enabled_check)

        # 类名（只读）
        class_value = QtWidgets.QLabel(f"<b>{node_data.get('class', '')}</b>")
        class_value.setStyleSheet("color: #666;")
        container_layout.addRow("类名:", class_value)

        # 添加分隔线
        separator = QtWidgets.QFrame()
        separator.setFrameShape(QtWidgets.QFrame.HLine)
        separator.setFrameShadow(QtWidgets.QFrame.Sunken)
        separator_layout = QtWidgets.QHBoxLayout()
        separator_layout.addWidget(separator)
        container_layout.addRow("", separator_layout)

        # 操作按钮
        btn_widget = QtWidgets.QWidget()
        btn_layout = QtWidgets.QHBoxLayout(btn_widget)
        btn_layout.setSpacing(10)
        
        self.save_node_btn = QtWidgets.QPushButton("💾 保存")
        self.save_node_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        self.save_node_btn.clicked.connect(self._on_save_node)
        
        self.cancel_node_btn = QtWidgets.QPushButton("取消")
        self.cancel_node_btn.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                color: #333;
                border: 1px solid #ccc;
                padding: 6px 16px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
        """)
        self.cancel_node_btn.clicked.connect(self._on_cancel_node_edit)
        
        btn_layout.addWidget(self.save_node_btn)
        btn_layout.addWidget(self.cancel_node_btn)
        btn_layout.addStretch()
        
        container_layout.addRow("", btn_widget)

        # 添加到主布局
        layout.addWidget(container)
        layout.addStretch()

    def _show_market_local_info(self, data):
        """显示本地市场插件信息"""
        layout = self.detail_layout
        pkg_data = data.get('data', {})

        # 目录路径
        path_label = QtWidgets.QLabel(f"<b>目录:</b> {data.get('path', '')}")
        layout.addWidget(path_label)

        # 版本
        version_label = QtWidgets.QLabel(f"<b>版本:</b> {pkg_data.get('version', '1.0.0')}")
        layout.addWidget(version_label)

        # 节点数
        node_count = len(pkg_data.get('nodes', []))
        count_label = QtWidgets.QLabel(f"<b>节点数:</b> {node_count}")
        layout.addWidget(count_label)

        # 作者
        author_label = QtWidgets.QLabel(f"<b>作者:</b> {pkg_data.get('author', '')}")
        layout.addWidget(author_label)

        # 删除按钮
        delete_btn = QtWidgets.QPushButton("🗑️ 删除插件")
        delete_btn.clicked.connect(lambda: self._on_delete_market_plugin(data))
        layout.addWidget(delete_btn)

    def _show_market_local_root_info(self):
        """显示本地插件根目录信息"""
        layout = self.detail_layout

        count = len(self.marketplace_plugins)
        label = QtWidgets.QLabel(f"<b>本地市场插件:</b> {count} 个")
        layout.addWidget(label)

        path = Path(__file__).parent.parent / "plugin_packages" / "marketplace"
        path_label = QtWidgets.QLabel(f"<b>目录:</b> {path}")
        layout.addWidget(path_label)

    def _show_market_remote_info(self, data):
        """显示网站分享根目录信息"""
        layout = self.detail_layout

        label = QtWidgets.QLabel("<b>网站分享</b>")
        layout.addWidget(label)

        desc = QtWidgets.QLabel("从远程网站下载和安装节点插件")
        layout.addWidget(desc)

    def _show_market_remote_url_info(self, data):
        """显示远程网站URL信息"""
        layout = self.detail_layout

        # 网址编辑
        url_layout = QtWidgets.QHBoxLayout()
        url_label = QtWidgets.QLabel("网址:")
        self.remote_url_edit = QtWidgets.QLineEdit(data.get('url', ''))
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.remote_url_edit)
        layout.addLayout(url_layout)

        # 刷新按钮
        refresh_btn = QtWidgets.QPushButton("🔄 刷新插件列表")
        refresh_btn.clicked.connect(self._on_refresh_remote_plugins)
        layout.addWidget(refresh_btn)

        # 可下载插件列表（模拟）
        list_label = QtWidgets.QLabel("<b>可下载节点:</b>")
        layout.addWidget(list_label)

        # 模拟插件列表
        plugins_list = [
            {'name': 'Advanced Filter', 'version': '1.0.0', 'description': '高级图像滤镜节点'},
            {'name': '3D Reconstruction', 'version': '2.0.1', 'description': '3D重建节点'},
            {'name': 'Video Analytics', 'version': '1.5.0', 'description': '视频分析节点'}
        ]

        for plugin in plugins_list:
            plugin_layout = QtWidgets.QHBoxLayout()
            plugin_info = QtWidgets.QLabel(f"<b>{plugin['name']}</b> v{plugin['version']}")
            download_btn = QtWidgets.QPushButton("⬇️ 下载")
            download_btn.clicked.connect(lambda p=plugin: self._on_download_plugin(p))
            plugin_layout.addWidget(plugin_info)
            plugin_layout.addWidget(download_btn)
            plugin_layout.addStretch()
            layout.addLayout(plugin_layout)

    def _show_market_root_info(self):
        """显示市场节点根目录信息"""
        layout = self.detail_layout

        local_count = len(self.marketplace_plugins)
        label = QtWidgets.QLabel(f"<b>本地插件:</b> {local_count} 个")
        layout.addWidget(label)

    def _on_add_node(self):
        """添加新节点"""
        # 检查当前选中是否为分组或节点
        selection = self.current_selection
        if selection.get('type') not in ['group', 'node']:
            QtWidgets.QMessageBox.warning(self, "提示", "请先选中一个节点分组或节点")
            return

        # 获取目标分组
        target_group = selection.get('name')
        if selection.get('type') == 'node' and selection.get('data'):
            target_group = selection['data'].get('__identifier__', target_group)

        # 弹出添加节点对话框
        dlg = AddNodeDialog(self, target_group)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            new_node = {
                'class': dlg.class_name_edit.text().strip(),
                'display_name': dlg.display_name_edit.text().strip(),
                '__identifier__': dlg.group_combo.currentData(),
                'enabled': dlg.enabled_check.isChecked()
            }

            # 添加到 plugin.json
            if self.builtin_plugin_info:
                self.builtin_plugin_info['nodes'].append(new_node)
                self._save_builtin_config()
                self._refresh_tree()
                QtWidgets.QMessageBox.information(self, "成功", "节点已添加，请刷新节点库生效")

    def _on_delete(self):
        """删除节点或插件"""
        selection = self.current_selection
        selection_type = selection.get('type')

        if selection_type == 'node':
            self._on_delete_node()
        elif selection_type == 'market_local':
            self._on_delete_market_plugin(selection)
        else:
            QtWidgets.QMessageBox.warning(self, "提示", "只能删除节点或本地市场插件")

    def _on_delete_node(self):
        """删除节点"""
        selection = self.current_selection
        node_class = selection.get('name', '')
        display_name = selection.get('data', {}).get('display_name', node_class)

        reply = QtWidgets.QMessageBox.question(
            self, "确认删除",
            f"确定要删除节点 '{display_name}' 吗？\n\n删除后将从节点库中移除，需要刷新节点库才能生效。",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            if self.builtin_plugin_info:
                nodes = self.builtin_plugin_info.get('nodes', [])
                self.builtin_plugin_info['nodes'] = [
                    n for n in nodes if n.get('class') != node_class
                ]
                self._save_builtin_config()
                self._refresh_tree()
                self._clear_detail_layout()
                QtWidgets.QMessageBox.information(self, "成功", "节点已删除")

    def _on_delete_market_plugin(self, data):
        """删除市场插件"""
        pkg_name = data.get('name', '')
        pkg_path = Path(data.get('path', ''))

        reply = QtWidgets.QMessageBox.question(
            self, "确认删除",
            f"确定要删除插件 '{pkg_name}' 吗？\n\n此操作将删除所有相关文件，且无法恢复。",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            try:
                if pkg_path.exists():
                    shutil.rmtree(pkg_path)
                del self.marketplace_plugins[pkg_name]
                self._refresh_tree()
                self._clear_detail_layout()
                QtWidgets.QMessageBox.information(self, "成功", "插件已删除")
            except Exception as e:
                QtWidgets.QMessageBox.error(self, "错误", f"删除失败: {str(e)}")

    def _on_save_node(self):
        """保存节点编辑"""
        selection = self.current_selection
        node_class = selection.get('name', '')

        if self.builtin_plugin_info:
            for node in self.builtin_plugin_info.get('nodes', []):
                if node.get('class') == node_class:
                    node['display_name'] = self.node_name_edit.text().strip()
                    node['__identifier__'] = self.group_combo.currentData()
                    node['enabled'] = self.enabled_check.isChecked()
                    break

            self._save_builtin_config()
            self._refresh_tree()
            QtWidgets.QMessageBox.information(self, "成功", "节点信息已保存，请刷新节点库生效")

    def _on_cancel_node_edit(self):
        """取消节点编辑"""
        self._update_detail_panel(self.current_selection)

    def _save_builtin_config(self):
        """保存内置插件配置"""
        if self.builtin_plugin_info:
            builtin_path = Path(__file__).parent.parent / "plugin_packages" / "builtin"
            plugin_json = builtin_path / "plugin.json"
            with open(plugin_json, 'w', encoding='utf-8') as f:
                json.dump(self.builtin_plugin_info, f, indent=2, ensure_ascii=False)

    def _on_import(self):
        """导入节点配置"""
        # 检查是否选中市场节点根目录
        selection = self.current_selection
        if selection.get('type') != 'market_root' and selection.get('type') != 'market_local_root':
            QtWidgets.QMessageBox.warning(self, "提示", "请先选中市场节点")
            return

        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择节点配置文件", "", "JSON文件 (*.json)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 检查配置格式
                if 'name' not in config or 'nodes' not in config:
                    QtWidgets.QMessageBox.error(self, "错误", "无效的节点配置文件")
                    return

                # 创建插件目录
                pkg_name = config['name']
                marketplace_path = Path(__file__).parent.parent / "plugin_packages" / "marketplace"
                pkg_path = marketplace_path / pkg_name
                
                if pkg_path.exists():
                    reply = QtWidgets.QMessageBox.question(
                        self, "覆盖确认",
                        f"插件 '{pkg_name}' 已存在，是否覆盖？",
                        QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
                    )
                    if reply != QtWidgets.QMessageBox.Yes:
                        return
                    shutil.rmtree(pkg_path)

                pkg_path.mkdir(parents=True)
                
                # 保存 plugin.json
                with open(pkg_path / "plugin.json", 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)

                # 刷新数据
                self._load_plugin_data()
                QtWidgets.QMessageBox.information(self, "成功", "插件已导入")
            except Exception as e:
                QtWidgets.QMessageBox.error(self, "错误", f"导入失败: {str(e)}")

    def _on_export(self):
        """导出节点配置"""
        selection = self.current_selection
        export_data = None
        export_name = ""

        if selection.get('type') == 'builtin_root':
            export_data = self.builtin_plugin_info
            export_name = "builtin"
        elif selection.get('type') == 'market_root':
            export_data = {
                'plugins': list(self.marketplace_plugins.keys()),
                'marketplace': self.marketplace_plugins
            }
            export_name = "marketplace"
        elif selection.get('type') == 'market_local':
            export_data = selection.get('data', {})
            export_name = selection.get('name', 'plugin')
        else:
            QtWidgets.QMessageBox.warning(self, "提示", "请选择要导出的内容")
            return

        if export_data:
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "保存配置文件", f"{export_name}.json", "JSON文件 (*.json)"
            )

            if file_path:
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        json.dump(export_data, f, indent=2, ensure_ascii=False)
                    QtWidgets.QMessageBox.information(self, "成功", "配置已导出")
                except Exception as e:
                    QtWidgets.QMessageBox.error(self, "错误", f"导出失败: {str(e)}")

    def _on_refresh_node_library(self):
        """刷新节点库"""
        if self.plugin_manager and hasattr(self.plugin_manager, 'reload_all_plugins'):
            try:
                # 调用插件管理器的刷新方法
                from core.node_registry import NodeRegistry
                node_registry = NodeRegistry()
                node_registry.register_nodes_to_graph()
                
                # 如果主窗口有刷新方法，也调用
                if self.parent() and hasattr(self.parent(), '_refresh_node_palette_display'):
                    self.parent()._refresh_node_palette_display()
                
                QtWidgets.QMessageBox.information(self, "成功", "节点库已刷新")
            except Exception as e:
                QtWidgets.QMessageBox.error(self, "错误", f"刷新失败: {str(e)}")
        else:
            QtWidgets.QMessageBox.information(self, "提示", "节点库已刷新（需要重启应用才能完全生效）")

    def _on_refresh_remote_plugins(self):
        """刷新远程插件列表"""
        url = self.remote_url_edit.text().strip()
        if not url:
            QtWidgets.QMessageBox.warning(self, "提示", "请输入有效的网址")
            return

        # 保存URL到配置
        config_path = Path(__file__).parent.parent / "config" / "plugins.json"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            config = {}
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            config['remote_repo_url'] = url
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            # 模拟刷新（实际应调用API）
            QtWidgets.QMessageBox.information(self, "成功", "插件列表已刷新")
        except Exception as e:
            QtWidgets.QMessageBox.error(self, "错误", f"刷新失败: {str(e)}")

    def _on_download_plugin(self, plugin_info):
        """下载插件"""
        reply = QtWidgets.QMessageBox.question(
            self, "确认下载",
            f"确定要下载 '{plugin_info['name']}' 吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            # 模拟下载过程
            QtWidgets.QMessageBox.information(
                self, "成功",
                f"插件 '{plugin_info['name']}' 已下载并安装\n\n描述: {plugin_info['description']}"
            )
            self._refresh_tree()

    def _on_help(self):
        """显示帮助信息"""
        help_text = """
节点编辑器使用说明：

【工具栏】
• ➕ 增加：添加新内置节点到选中的分组
• ➖ 删除：删除选中的节点或市场插件
• 📥 导入：导入市场节点配置文件
• 📤 导出：导出当前节点配置
• 🔄 刷新节点库：刷新节点库并重新加载
• ❓ 帮助：显示此帮助信息

【左侧列表】
• 内置节点：系统内置的节点分组和节点
• 市场节点：本地下载和网站分享的插件

【右侧详情】
• 选中内置节点根目录：显示目录、节点总数、分组数
• 选中分组：显示分组名称、显示名称、节点数
• 选中节点：可编辑显示名称、所属分组、是否启用
• 选中本地插件：显示目录、版本、节点数，可删除
• 选中网站分享：可编辑网址、刷新插件列表、下载插件

【注意事项】
• 修改节点信息后需要点击"保存"按钮
• 删除操作不可恢复，请谨慎操作
• 修改后需要刷新节点库才能生效
        """
        QtWidgets.QMessageBox.information(self, "帮助", help_text)


class AddNodeDialog(QtWidgets.QDialog):
    """添加新节点对话框"""

    def __init__(self, parent=None, default_group=None):
        super(AddNodeDialog, self).__init__(parent)
        self.setWindowTitle("添加新节点")
        self.resize(400, 250)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # 文件路径
        file_layout = QtWidgets.QHBoxLayout()
        file_label = QtWidgets.QLabel("文件路径:")
        self.file_edit = QtWidgets.QLineEdit()
        browse_btn = QtWidgets.QPushButton("浏览...")
        browse_btn.clicked.connect(self._on_browse_file)
        file_layout.addWidget(file_label)
        file_layout.addWidget(self.file_edit)
        file_layout.addWidget(browse_btn)
        layout.addLayout(file_layout)

        # 类名
        class_layout = QtWidgets.QHBoxLayout()
        class_label = QtWidgets.QLabel("类名:")
        self.class_name_edit = QtWidgets.QLineEdit()
        class_layout.addWidget(class_label)
        class_layout.addWidget(self.class_name_edit)
        layout.addLayout(class_layout)

        # 显示名称
        name_layout = QtWidgets.QHBoxLayout()
        name_label = QtWidgets.QLabel("显示名称:")
        self.display_name_edit = QtWidgets.QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.display_name_edit)
        layout.addLayout(name_layout)

        # 所属分组
        group_layout = QtWidgets.QHBoxLayout()
        group_label = QtWidgets.QLabel("所属分组:")
        self.group_combo = QtWidgets.QComboBox()
        
        groups = [
            ('Image_Source', '图像源'),
            ('Image_Analysis', '图像分析'),
            ('Image_Transform', '图像变换'),
            ('Image_Process', '图像处理'),
            ('Integration', '系统集成')
        ]
        
        for group_id, display_name in groups:
            self.group_combo.addItem(display_name, group_id)
        
        if default_group:
            index = self.group_combo.findData(default_group)
            if index >= 0:
                self.group_combo.setCurrentIndex(index)
        
        group_layout.addWidget(group_label)
        group_layout.addWidget(self.group_combo)
        layout.addLayout(group_layout)

        # 是否启用
        self.enabled_check = QtWidgets.QCheckBox("是否启用")
        self.enabled_check.setChecked(True)
        layout.addWidget(self.enabled_check)

        # 按钮
        btn_layout = QtWidgets.QHBoxLayout()
        ok_btn = QtWidgets.QPushButton("确定")
        ok_btn.clicked.connect(self._on_ok)
        cancel_btn = QtWidgets.QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        btn_layout.addStretch()
        layout.addLayout(btn_layout)

    def _on_browse_file(self):
        """浏览选择节点文件"""
        nodes_dir = Path(__file__).parent.parent / "plugin_packages" / "builtin" / "nodes"
        
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "选择节点文件", str(nodes_dir), "Python文件 (*.py)"
        )

        if file_path:
            self.file_edit.setText(file_path)
            # 尝试自动提取类名
            self._extract_class_name(file_path)

    def _extract_class_name(self, file_path):
        """从文件中提取类名"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # 查找继承自 BaseNode 的类
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == 'BaseNode':
                            self.class_name_edit.setText(node.name)
                            # 自动生成显示名称（去掉 Node 后缀）
                            display_name = node.name.replace('Node', '')
                            if display_name:
                                self.display_name_edit.setText(display_name)
                            return
        except Exception as e:
            print(f"提取类名失败: {e}")

    def _on_ok(self):
        """确定添加"""
        if not self.class_name_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "提示", "请输入类名")
            return
        
        if not self.display_name_edit.text().strip():
            QtWidgets.QMessageBox.warning(self, "提示", "请输入显示名称")
            return
        
        self.accept()
