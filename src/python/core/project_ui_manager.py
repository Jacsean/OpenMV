"""
工程UI管理器

负责处理与工程/工作流相关的UI交互逻辑，包括：
- 工程创建/打开/保存的对话框交互
- 工作流管理（添加/删除/重命名）的UI操作
- 最近工程列表的UI展示和更新
- 标签页管理与同步
- 节点图保存/加载的文件对话框
"""

import os
from pathlib import Path
from PySide2 import QtWidgets, QtCore
from NodeGraphQt import NodeGraph


class ProjectUIManager:
    """
    工程UI管理器
    
    职责：
    - 封装所有工程相关的UI交互逻辑
    - 提供简洁的API供MainWindow调用
    - 处理工程创建、打开、保存、工作流管理的用户界面
    - 管理标签页和最近工程列表的UI同步
    """
    
    def __init__(self, project_manager, main_window):
        """
        初始化工程UI管理器
        
        Args:
            project_manager: ProjectManager实例
            main_window: MainWindow实例（用于访问UI组件）
        """
        self.project_manager = project_manager
        self.main_window = main_window
    
    def initialize_default_project(self):
        """
        初始化默认工程和工作流
        """
        # 创建新工程
        project = self.project_manager.create_project("默认工程")
        
        # 为第一个工作流创建NodeGraph并添加到标签页
        if project.workflows:
            workflow = project.workflows[0]
            self.add_workflow_tab(workflow)
    
    def add_workflow_tab(self, workflow):
        """
        添加工作流标签页
        
        Args:
            workflow: Workflow对象
        """
        # 创建新的NodeGraph实例
        node_graph = NodeGraph()
        
        # 注册基础节点（通过插件系统）
        # 注意：这里不再直接注册，而是由插件系统处理
        
        # 加载插件节点（仅在第一个工作流时加载一次）
        if hasattr(self.main_window, '_pending_plugins') and self.main_window.tab_widget.count() == 0:
            from plugins.plugin_ui_manager import PluginUIManager
            plugin_ui = PluginUIManager(self.main_window.plugin_manager, self.main_window)
            plugin_ui.load_plugins_to_graph(node_graph)
        
        # 关联到工作流
        workflow.node_graph = node_graph
        
        # 连接信号
        # 使用默认参数捕获当前的 workflow 对象，防止闭包问题
        node_graph.node_created.connect(lambda n, wf=workflow: self.main_window._on_node_created(n, wf))
        node_graph.node_double_clicked.connect(lambda n, wf=workflow: self.main_window._on_node_double_clicked(n, wf))
        
        # 获取NodeGraph的widget
        graph_widget = node_graph.widget
        
        # 添加到标签页
        tab_title = workflow.name
        if workflow.is_modified:
            tab_title += " *"
        tab_index = self.main_window.tab_widget.addTab(graph_widget, tab_title)
        
        # 如果是第一个标签页，设置为当前激活
        if self.main_window.tab_widget.count() == 1:
            self.on_tab_changed(0)
        
        print(f"✅ 添加工作流标签页: {workflow.name}")
    
    def remove_workflow_tab(self, index):
        """
        移除工作流标签页
        
        Args:
            index: 标签页索引
        """
        if index < 0 or index >= self.main_window.tab_widget.count():
            return
            
        # 获取工作流
        project = self.project_manager.current_project
        if project and index < len(project.workflows):
            workflow = project.workflows[index]
            
            # 从工程中移除
            self.project_manager.remove_workflow(index)
            
            # 移除标签页
            self.main_window.tab_widget.removeTab(index)
            
            print(f"🗑️ 移除工作流标签页: {workflow.name}")
    
    def on_tab_changed(self, index):
        """
        标签页切换时的回调
        
        Args:
            index: 新的标签页索引
        """
        if index < 0:
            return
            
        # 更新当前激活的NodeGraph
        project = self.project_manager.current_project
        if project and index < len(project.workflows):
            workflow = project.workflows[index]
            self.main_window.current_node_graph = workflow.node_graph
            
            # 注意：NodesPaletteWidget和PropertiesBinWidget不支持动态切换NodeGraph
            # 所以这里只更新引用，不尝试重新绑定
            
            # 更新工程激活索引
            project.set_active_workflow(index)
            
            print(f"🔄 切换到工作流: {workflow.name}")
    
    def on_tab_close_requested(self, index):
        """
        标签页关闭请求
        
        Args:
            index: 要关闭的标签页索引
        """
        project = self.project_manager.current_project
        if not project:
            return
            
        workflow = project.get_workflow(index)
        if not workflow:
            return
            
        # 检查是否有未保存的修改
        if workflow.is_modified:
            reply = QtWidgets.QMessageBox.question(
                self.main_window,
                "确认关闭",
                f"工作流 '{workflow.name}' 有未保存的修改\n是否保存？",
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel
            )
            
            if reply == QtWidgets.QMessageBox.Save:
                # TODO: 实现单个工作流的保存
                pass
            elif reply == QtWidgets.QMessageBox.Cancel:
                return
        
        # 移除标签页
        self.remove_workflow_tab(index)
    
    def new_project_from_ui(self):
        """
        创建新工程（UI触发）
        """
        # 检查当前工程是否有未保存修改
        if self.project_manager.has_unsaved_changes():
            reply = QtWidgets.QMessageBox.question(
                self.main_window,
                "确认",
                "当前工程有未保存的修改\n是否先保存？",
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel
            )
            
            if reply == QtWidgets.QMessageBox.Save:
                self.save_project_from_ui()
            elif reply == QtWidgets.QMessageBox.Cancel:
                return
        
        # 关闭当前工程
        self.project_manager.close_project()
        
        # 清空标签页
        self.main_window.tab_widget.clear()
        
        # 创建新工程
        self.initialize_default_project()
    
    def open_project_from_ui(self):
        """
        打开工程（支持单文件.proj格式）（UI触发）
        """
        # 检查当前工程是否有未保存修改
        if self.project_manager.has_unsaved_changes():
            reply = QtWidgets.QMessageBox.question(
                self.main_window,
                "确认",
                "当前工程有未保存的修改\n是否先保存？",
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel
            )
            
            if reply == QtWidgets.QMessageBox.Save:
                self.save_project_from_ui()
            elif reply == QtWidgets.QMessageBox.Cancel:
                return
        
        # 选择工程文件（.proj单文件）
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.main_window,
            "打开工程",
            "",
            "Project Files (*.proj);;All Files (*)"
        )
        
        if not file_path:
            return
        
        # 关闭当前工程
        self.project_manager.close_project()
        
        # 清空标签页
        self.main_window.tab_widget.clear()
        
        print(f"📂 开始打开工程: {file_path}")
        
        # 使用ProjectManager的import_project方法从单文件加载
        project = self.project_manager.import_project(file_path)
        
        if project:
            print(f"✅ 工程已打开: {project.name}")
            print(f"   工作流数量: {len(project.workflows)}")
            
            # 为每个工作流创建标签页
            for workflow in project.workflows:
                # 创建工作流的NodeGraph
                node_graph = NodeGraph()
                workflow.node_graph = node_graph
                
                # 加载节点图数据
                if workflow.file_path:
                    # 注意：导入时工程被解压到临时目录
                    import tempfile
                    import glob
                    temp_base = tempfile.gettempdir()
                    temp_dirs = glob.glob(os.path.join(temp_base, 'proj_import_*'))
                    if temp_dirs:
                        latest_temp = max(temp_dirs, key=os.path.getmtime)
                        wf_full_path = os.path.join(latest_temp, workflow.file_path)
                        
                        if os.path.exists(wf_full_path):
                            try:
                                import json
                                with open(wf_full_path, 'r', encoding='utf-8') as f:
                                    session_data = json.load(f)
                                node_graph.deserialize_session(session_data)
                                print(f"✅ 加载工作流: {workflow.name}")
                            except Exception as e:
                                print(f"❌ 加载工作流失败: {e}")
                                import traceback
                                traceback.print_exc()
                        else:
                            print(f"⚠️ 工作流文件不存在: {wf_full_path}")
                
                # 连接信号
                node_graph.node_created.connect(lambda n, wf=workflow: self.main_window._on_node_created(n, wf))
                node_graph.node_double_clicked.connect(lambda n, wf=workflow: self.main_window._on_node_double_clicked(n, wf))
                
                # 添加到标签页
                self.add_workflow_tab_to_ui(workflow)
            
            # 激活第一个工作流
            if project.workflows:
                self.main_window.tab_widget.setCurrentIndex(0)
                self.on_tab_changed(0)
            
            # 添加到最近工程列表
            self.add_to_recent_projects(os.path.dirname(os.path.abspath(file_path)))
        else:
            QtWidgets.QMessageBox.critical(
                self.main_window,
                "错误",
                "无法打开工程文件，请确认文件格式正确"
            )
    
    def save_project_from_ui(self):
        """
        保存当前工程为单文件（.proj ZIP格式）（UI触发）
        
        Returns:
            bool: 是否保存成功
        """
        project = self.project_manager.current_project
        if not project:
            QtWidgets.QMessageBox.warning(self.main_window, "警告", "没有打开的工程")
            return False
        
        # 如果工程还没有路径，询问保存位置
        if not project.file_path or not project.file_path.endswith('.proj'):
            default_name = f"{project.name}.proj"
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self.main_window,
                "保存工程",
                default_name,
                "Project Files (*.proj);;All Files (*)"
            )
            
            if not file_path:
                return False
            
            # 确保文件扩展名为.proj
            if not file_path.endswith('.proj'):
                file_path += '.proj'
            
            project.file_path = file_path
        
        print(f"💾 开始保存工程: {project.name}")
        print(f"   目标文件: {project.file_path}")
        
        # 使用ProjectManager的export_project方法保存为单文件
        success = self.project_manager.export_project(project.file_path)
        
        if success:
            # 更新标签页标题（移除*号）
            for i in range(self.main_window.tab_widget.count()):
                tab_text = self.main_window.tab_widget.tabText(i)
                if tab_text.endswith(" *"):
                    self.main_window.tab_widget.setTabText(i, tab_text[:-2])
            
            # 添加到最近工程列表
            self.add_to_recent_projects(os.path.dirname(os.path.abspath(project.file_path)))
            
            # 获取文件大小
            try:
                size_bytes = os.path.getsize(project.file_path)
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                print(f"✅ 工程已保存: {project.file_path} ({size_str})")
            except:
                print(f"✅ 工程已保存: {project.file_path}")
            
            QtWidgets.QMessageBox.information(
                self.main_window,
                "成功",
                f"工程已保存为单文件:\n{project.file_path}"
            )
            return True
        else:
            QtWidgets.QMessageBox.critical(
                self.main_window,
                "错误",
                "保存工程失败，请查看控制台输出"
            )
            return False
    
    def get_file_size_str(self, file_path: str) -> str:
        """
        获取文件大小的可读字符串
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: 文件大小字符串（如 "2.5 MB"）
        """
        try:
            size_bytes = os.path.getsize(file_path)
            if size_bytes < 1024:
                return f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                return f"{size_bytes / 1024:.1f} KB"
            elif size_bytes < 1024 * 1024 * 1024:
                return f"{size_bytes / (1024 * 1024):.1f} MB"
            else:
                return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
        except:
            return "未知大小"
    
    def add_to_recent_projects(self, project_path):
        """
        添加工程到最近打开列表
        
        Args:
            project_path: 工程目录路径
        """
        settings = QtCore.QSettings("VisionSystem", "StduyOpenCV")
        
        # 获取现有的最近工程列表
        recent_projects = settings.value("recent_projects", [])
        if isinstance(recent_projects, str):
            recent_projects = [recent_projects]
        
        # 移除重复项
        if project_path in recent_projects:
            recent_projects.remove(project_path)
        
        # 添加到列表开头
        recent_projects.insert(0, project_path)
        
        # 限制最多保存10个
        recent_projects = recent_projects[:10]
        
        # 保存
        settings.setValue("recent_projects", recent_projects)
        print(f"📋 已添加到最近工程列表: {project_path}")
    
    def get_recent_projects(self):
        """
        获取最近打开的工程列表
        
        Returns:
            list: 工程路径列表
        """
        settings = QtCore.QSettings("VisionSystem", "StduyOpenCV")
        recent_projects = settings.value("recent_projects", [])
        
        if isinstance(recent_projects, str):
            return [recent_projects]
        
        return recent_projects if recent_projects else []
    
    def clear_recent_projects(self):
        """
        清空最近工程列表
        """
        settings = QtCore.QSettings("VisionSystem", "StduyOpenCV")
        settings.remove("recent_projects")
        print("🗑️ 已清空最近工程列表")
    
    def update_recent_projects_menu(self, recent_menu):
        """
        更新最近工程菜单（动态刷新）
        
        Args:
            recent_menu: QMenu对象
        """
        recent_menu.clear()
        self.populate_recent_projects_menu(recent_menu)
    
    def populate_recent_projects_menu(self, recent_menu):
        """
        填充最近工程菜单
        
        Args:
            recent_menu: QMenu对象
        """
        recent_projects = self.get_recent_projects()
        
        if not recent_projects:
            no_recent_action = QtWidgets.QAction("(空)", self.main_window)
            no_recent_action.setEnabled(False)
            recent_menu.addAction(no_recent_action)
            return
        
        # 添加工程列表
        for i, project_path in enumerate(recent_projects):
            # 提取工程名称（目录名）
            project_name = os.path.basename(project_path)
            
            action = QtWidgets.QAction(f"{i+1}. {project_name}", self.main_window)
            action.setStatusTip(project_path)
            action.triggered.connect(lambda checked, path=project_path: self.open_recent_project(path))
            recent_menu.addAction(action)
        
        recent_menu.addSeparator()
        
        # 清空列表
        clear_action = QtWidgets.QAction("🗑 清空列表", self.main_window)
        clear_action.setStatusTip("清空最近工程列表")
        clear_action.triggered.connect(self.clear_recent_projects)
        recent_menu.addAction(clear_action)
    
    def open_recent_project(self, project_path):
        """
        打开最近的工程
        
        Args:
            project_path: 工程目录路径
        """
        if not os.path.exists(project_path):
            reply = QtWidgets.QMessageBox.question(
                self.main_window,
                "工程不存在",
                f"工程路径不存在:\n{project_path}\n\n是否从最近列表中移除？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                self.remove_from_recent_projects(project_path)
            return
        
        # 检查当前工程是否有未保存修改
        if self.project_manager.has_unsaved_changes():
            reply = QtWidgets.QMessageBox.question(
                self.main_window,
                "确认",
                "当前工程有未保存的修改\n是否先保存？",
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel
            )
            
            if reply == QtWidgets.QMessageBox.Save:
                self.save_project_from_ui()
            elif reply == QtWidgets.QMessageBox.Cancel:
                return
        
        # 关闭当前工程
        self.project_manager.close_project()
        
        # 清空标签页
        self.main_window.tab_widget.clear()
        
        # 打开工程
        project = self.project_manager.open_project(project_path)
        
        if project:
            # 为每个工作流创建标签页
            for workflow in project.workflows:
                # 创建工作流的NodeGraph
                node_graph = NodeGraph()
                workflow.node_graph = node_graph
                
                # 加载节点图数据
                if workflow.file_path:
                    wf_full_path = os.path.join(project_path, workflow.file_path)
                    if os.path.exists(wf_full_path):
                        try:
                            import json
                            with open(wf_full_path, 'r', encoding='utf-8') as f:
                                session_data = json.load(f)
                            node_graph.deserialize_session(session_data)
                            print(f"✅ 加载工作流: {workflow.name}")
                        except Exception as e:
                            print(f"❌ 加载工作流失败: {e}")
                
                # 连接信号
                node_graph.node_created.connect(lambda n, wf=workflow: self.main_window._on_node_created(n, wf))
                node_graph.node_double_clicked.connect(lambda n, wf=workflow: self.main_window._on_node_double_clicked(n, wf))
                
                # 添加到标签页
                self.add_workflow_tab_to_ui(workflow)
            
            # 激活第一个工作流
            if project.workflows:
                self.main_window.tab_widget.setCurrentIndex(0)
                self.on_tab_changed(0)
        else:
            QtWidgets.QMessageBox.critical(
                self.main_window,
                "错误",
                "无法打开工程"
            )
    
    def remove_from_recent_projects(self, project_path):
        """
        从最近工程列表中移除指定工程
        
        Args:
            project_path: 工程目录路径
        """
        settings = QtCore.QSettings("VisionSystem", "StduyOpenCV")
        recent_projects = settings.value("recent_projects", [])
        
        if isinstance(recent_projects, str):
            recent_projects = [recent_projects]
        
        if project_path in recent_projects:
            recent_projects.remove(project_path)
            settings.setValue("recent_projects", recent_projects)
            print(f"🗑️ 已从最近列表中移除: {project_path}")
    
    def add_new_workflow_from_ui(self):
        """
        添加新的工作流（UI触发）
        """
        project = self.project_manager.current_project
        if not project:
            QtWidgets.QMessageBox.warning(self.main_window, "警告", "没有打开的工程")
            return
        
        # 创建工作流
        workflow_name = f"工作流 {len(project.workflows) + 1}"
        workflow = self.project_manager.add_new_workflow(workflow_name)
        
        if workflow:
            # 创建NodeGraph
            node_graph = NodeGraph()
            workflow.node_graph = node_graph
            
            # 连接信号
            node_graph.node_created.connect(lambda n, wf=workflow: self.main_window._on_node_created(n, wf))
            node_graph.node_double_clicked.connect(lambda n, wf=workflow: self.main_window._on_node_double_clicked(n, wf))
            
            # 添加到UI
            self.add_workflow_tab_to_ui(workflow)
            
            # 切换到新标签页
            self.main_window.tab_widget.setCurrentIndex(self.main_window.tab_widget.count() - 1)
            self.on_tab_changed(self.main_window.tab_widget.count() - 1)
    
    def close_current_workflow_from_ui(self):
        """
        关闭当前工作流（UI触发）
        """
        current_index = self.main_window.tab_widget.currentIndex()
        if current_index >= 0:
            self.on_tab_close_requested(current_index)
    
    def rename_workflow_from_ui(self):
        """
        重命名当前工作流（UI触发）
        """
        project = self.project_manager.current_project
        if not project:
            return
        
        current_index = self.main_window.tab_widget.currentIndex()
        workflow = project.get_workflow(current_index)
        
        if not workflow:
            return
        
        # 弹出输入对话框
        new_name, ok = QtWidgets.QInputDialog.getText(
            self.main_window,
            "重命名工作流",
            "请输入新的工作流名称:",
            QtWidgets.QLineEdit.Normal,
            workflow.name
        )
        
        if ok and new_name:
            old_name = workflow.name
            workflow.name = new_name
            workflow.mark_modified()
            
            # 更新标签页标题
            tab_title = new_name
            if workflow.is_modified:
                tab_title += " *"
            self.main_window.tab_widget.setTabText(current_index, tab_title)
            
            print(f"✅ 工作流已重命名: {old_name} -> {new_name}")
    
    def add_workflow_tab_to_ui(self, workflow):
        """
        将工作流添加到UI标签页
        
        Args:
            workflow: Workflow对象
        """
        graph_widget = workflow.node_graph.widget
        
        tab_title = workflow.name
        if workflow.is_modified:
            tab_title += " *"
            
        self.main_window.tab_widget.addTab(graph_widget, tab_title)
