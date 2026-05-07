"""
工程UI管理器

负责处理与工程/工作流相关的UI交互逻辑，包括：
- 工程创建/打开/保存的对话框交互
- 工作流管理（添加/删除/重命名）的UI操作
- 最近工程列表的UI展示和更新
- 标签页管理与同步
- 节点图保存/加载的文件对话框

本模块已重构为事件驱动：
- 通过 EventBus 发布事件通知工程/工作流变更
- UI响应逻辑由订阅者处理

节点注册时机：
- 在工作流创建时（add_workflow_tab）统一注册节点到 NodeGraph
- 使用 NodeRegistry 确保每个 NodeGraph 只注册一次
"""

import os
from pathlib import Path
from PySide2 import QtWidgets, QtCore
from NodeGraphQt import NodeGraph

import utils
from core.event_bus import event_bus, Events
from core.node_registry import register_nodes_on_workflow_create, node_registry
from core.node_lifecycle import lifecycle_manager


class ProjectUIManager:
    """
    工程UI管理器

    职责：
    - 处理工程/工作流相关的UI交互
    - 发布事件而非直接操作其他模块
    - 管理标签页和工程状态

    事件发布：
    - PROJECT_CREATED: 工程已创建
    - PROJECT_OPENED: 工程已打开
    - PROJECT_SAVED: 工程已保存
    - PROJECT_CLOSED: 工程已关闭
    - WORKFLOW_ADDED: 工作流已添加
    - WORKFLOW_REMOVED: 工作流已移除
    - WORKFLOW_SELECTED: 工作流已选中
    - WORKFLOW_RENAMED: 工作流已重命名
    - TAB_ADDED: 标签页已添加
    - TAB_REMOVED: 标签页已移除
    - TAB_CHANGED: 标签页已切换
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
        
        # 订阅插件重载事件
        event_bus.subscribe(Events.PLUGIN_RELOADED, self._on_plugin_reloaded)

    def initialize_default_project(self):
        """
        初始化默认工程和工作流
        """
        project = self.project_manager.create_project("默认工程")
        event_bus.publish(Events.PROJECT_CREATED, project=project)

        if project.workflows:
            workflow = project.workflows[0]
            self.add_workflow_tab(workflow)
            event_bus.publish(Events.WORKFLOW_ADDED, workflow=workflow)

    def add_workflow_tab(self, workflow):
        """
        添加工作流标签页

        Args:
            workflow: Workflow对象
        """
        node_graph = NodeGraph()

        if hasattr(self.main_window, 'plugin_manager'):
            register_nodes_on_workflow_create(node_graph, workflow, self.main_window.plugin_manager)
        else:
            utils.logger.warning(f"⚠️ 未找到 plugin_manager，跳过节点注册", module="project_ui_manager")

        workflow.node_graph = node_graph

        node_graph.node_created.connect(lambda n, wf=workflow: self.main_window._on_node_created(n, wf))
        node_graph.node_double_clicked.connect(lambda n, wf=workflow: self.main_window._on_node_double_clicked(n, wf))

        graph_widget = node_graph.widget

        tab_title = workflow.name
        if workflow.is_modified:
            tab_title += " *"
        
        tab_index = self.main_window.tab_widget.addTab(graph_widget, tab_title)
        
        # 首次创建工作流时，初始化共享组件
        if hasattr(self.main_window, '_shared_components_initialized') and not self.main_window._shared_components_initialized:
            utils.logger.info("首次创建工作流，初始化共享组件...", module="project_ui_manager")
            self.main_window._initialize_shared_components(node_graph)

        if self.main_window.tab_widget.count() == 1:
            self.on_tab_changed(0)

        event_bus.publish(Events.TAB_ADDED, tab_index=tab_index, workflow=workflow)
        utils.logger.success(f"✅ 添加工作流标签页: {workflow.name}", module="project_ui_manager")

    def remove_workflow_tab(self, index):
        """
        移除工作流标签页

        Args:
            index: 标签页索引
        """
        if index < 0 or index >= self.main_window.tab_widget.count():
            return

        project = self.project_manager.current_project
        if project and index < len(project.workflows):
            workflow = project.workflows[index]

            if workflow.node_graph:
                # 清理所有节点
                for node in list(workflow.node_graph.all_nodes()):
                    lifecycle_manager.delete_node_with_cleanup(node)
                
                try:
                    workflow.node_graph.node_created.disconnect()
                    workflow.node_graph.node_double_clicked.disconnect()
                except:
                    pass

            self.project_manager.remove_workflow(index)
            self.main_window.tab_widget.removeTab(index)

            event_bus.publish(Events.TAB_REMOVED, tab_index=index, workflow=workflow)
            event_bus.publish(Events.WORKFLOW_REMOVED, workflow=workflow)
            utils.logger.info(f"🗑️ 移除工作流标签页: {workflow.name}", module="project_ui_manager")

    def on_tab_changed(self, index):
        """
        标签页切换时的回调

        Args:
            index: 新的标签页索引
        """
        if index < 0:
            return

        project = self.project_manager.current_project
        if project and index < len(project.workflows):
            workflow = project.workflows[index]
            self.main_window.current_node_graph = workflow.node_graph
            project.set_active_workflow(index)

            event_bus.publish(Events.TAB_CHANGED, tab_index=index, workflow=workflow)
            event_bus.publish(Events.WORKFLOW_SELECTED, workflow=workflow)
            utils.logger.info(f"🔄 切换到工作流: {workflow.name}", module="project_ui_manager")
            
            # 更新共享组件引用（消除临时Graph问题）
            self.main_window._update_shared_components()

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

        if workflow.is_modified:
            reply = QtWidgets.QMessageBox.question(
                self.main_window,
                "确认关闭",
                f"工作流 '{workflow.name}' 有未保存的修改\n是否保存？",
                QtWidgets.QMessageBox.Save | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel
            )

            if reply == QtWidgets.QMessageBox.Save:
                pass
            elif reply == QtWidgets.QMessageBox.Cancel:
                return

        self.remove_workflow_tab(index)

    def new_project_from_ui(self):
        """
        创建新工程（UI触发）
        """
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

        event_bus.publish(Events.PROJECT_CLOSED, project=self.project_manager.current_project)
        self.project_manager.close_project()
        self.main_window.tab_widget.clear()

        self.initialize_default_project()

    def open_project_from_ui(self):
        """
        打开工程（支持单文件.proj格式）（UI触发）
        """
        utils.logger.info(f"\n{'='*60}", module="project_ui_manager")
        utils.logger.info(f"📂 UI: 开始打开工程流程", module="project_ui_manager")
        utils.logger.info(f"{'='*60}\n", module="project_ui_manager")

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
                utils.logger.warning("⚠️ 用户取消打开工程", module="project_ui_manager")
                return

        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.main_window,
            "打开工程",
            "",
            "Project Files (*.proj);;All Files (*)"
        )

        if not file_path:
            utils.logger.warning("⚠️ 用户取消选择文件", module="project_ui_manager")
            return

        utils.logger.info(f"📄 用户选择文件: {file_path}", module="project_ui_manager")

        event_bus.publish(Events.PROJECT_CLOSED, project=self.project_manager.current_project)
        self.project_manager.close_project()

        tab_count_before = self.main_window.tab_widget.count()
        self.main_window.tab_widget.clear()
        utils.logger.info(f"   🧹 清空标签页 (之前有 {tab_count_before} 个)", module="project_ui_manager")

        utils.logger.info(f"\n📂 开始打开工程: {file_path}", module="project_ui_manager")

        project = self.project_manager.import_project(file_path)

        if project:
            utils.logger.success(f"\n✅ 工程数据加载成功: {project.name}", module="project_ui_manager")
            utils.logger.info(f"   工作流数量: {len(project.workflows)}", module="project_ui_manager")

            event_bus.publish(Events.PROJECT_OPENED, project=project)

            workflows_session_data = getattr(project, '_workflows_session_data', {})
            utils.logger.info(f"   预加载的工作流数据: {len(workflows_session_data)} 个", module="project_ui_manager")

            for i, workflow in enumerate(project.workflows):
                utils.logger.info(f"\n--- 处理工作流 {i+1}/{len(project.workflows)}: {workflow.name} ---", module="project_ui_manager")

                if workflow.node_graph is None:
                    utils.logger.info(f"   🔨 创建新的 NodeGraph 实例", module="project_ui_manager")
                    from NodeGraphQt import NodeGraph
                    node_graph = NodeGraph()

                    utils.logger.info(f"   🔌 注册插件节点到 NodeGraph...", module="project_ui_manager")
                    if hasattr(self.main_window, 'plugin_manager'):
                        register_nodes_on_workflow_create(node_graph, workflow, self.main_window.plugin_manager)
                    else:
                        utils.logger.warning(f"      ⚠️ 未找到 plugin_manager，跳过节点注册", module="project_ui_manager")

                    workflow.node_graph = node_graph

                    session_data = workflows_session_data.get(i)
                    if session_data:
                        utils.logger.info(f"   📥 尝试反序列化节点图数据...", module="project_ui_manager")
                        utils.logger.info(f"      数据类型: {type(session_data)}", module="project_ui_manager")
                        utils.logger.info(f"      数据键: {session_data.keys() if isinstance(session_data, dict) else 'N/A'}", module="project_ui_manager")

                        if isinstance(session_data, dict) and 'nodes' in session_data:
                            node_count_in_data = len(session_data['nodes'])
                            utils.logger.info(f"      📊 JSON 中的节点数量: {node_count_in_data}", module="project_ui_manager")
                            if node_count_in_data > 0:
                                utils.logger.info(f"      📋 节点列表:", module="project_ui_manager")
                                for node_id, node_info in session_data['nodes'].items():
                                    node_type = node_info.get('type_', 'Unknown')
                                    node_name = node_info.get('name', 'Unnamed')
                                    utils.logger.info(f"         - {node_name} ({node_type})", module="project_ui_manager")

                        try:
                            before_count = len(node_graph.all_nodes())
                            utils.logger.info(f"      🔢 反序列化前节点数: {before_count}", module="project_ui_manager")

                            result = node_graph.deserialize_session(session_data)
                            utils.logger.info(f"      🔄 deserialize_session 返回值: {result}", module="project_ui_manager")

                            after_count = len(node_graph.all_nodes())
                            utils.logger.info(f"      🔢 反序列化后节点数: {after_count}", module="project_ui_manager")

                            if after_count == 0 and node_count_in_data > 0:
                                utils.logger.warning(f"      ⚠️  警告: 数据中有 {node_count_in_data} 个节点，但反序列化后为 0", module="project_ui_manager")

                            utils.logger.success(f"   ✅ 加载工作流: {workflow.name} ({after_count} 个节点)", module="project_ui_manager")

                            if after_count > 0:
                                utils.logger.info(f"   📋 节点列表:", module="project_ui_manager")
                                for node in node_graph.all_nodes():
                                    utils.logger.info(f"      - {node.name()} ({node.type_})", module="project_ui_manager")
                        except Exception as e:
                            utils.logger.error(f"   ❌ 加载工作流失败: {e}", module="project_ui_manager")
                            import traceback
                            traceback.print_exc()
                    elif workflow.file_path:
                        utils.logger.info(f"   📁 尝试从文件路径加载...", module="project_ui_manager")
                        wf_full_path = os.path.join(os.path.dirname(file_path), workflow.file_path)
                        if os.path.exists(wf_full_path):
                            try:
                                node_graph.deserialize_session(wf_full_path)
                                utils.logger.success(f"   ✅ 从文件加载工作流: {workflow.name}", module="project_ui_manager")
                            except Exception as e:
                                utils.logger.error(f"   ❌ 从文件加载工作流失败: {e}", module="project_ui_manager")
                        else:
                            utils.logger.warning(f"   ⚠️ 文件不存在: {wf_full_path}", module="project_ui_manager")
                    else:
                        utils.logger.warning(f"   ⚠️ 没有节点图数据，创建空工作流", module="project_ui_manager")

                    utils.logger.info(f"   🔗 连接信号...", module="project_ui_manager")
                    node_graph.node_created.connect(lambda n, wf=workflow: self.main_window._on_node_created(n, wf))
                    node_graph.node_double_clicked.connect(lambda n, wf=workflow: self.main_window._on_node_double_clicked(n, wf))
                else:
                    utils.logger.info(f"   ♻️  使用已存在的 NodeGraph", module="project_ui_manager")
                    try:
                        workflow.node_graph.node_created.disconnect()
                        workflow.node_graph.node_double_clicked.disconnect()
                    except:
                        pass

                    workflow.node_graph.node_created.connect(lambda n, wf=workflow: self.main_window._on_node_created(n, wf))
                    workflow.node_graph.node_double_clicked.connect(lambda n, wf=workflow: self.main_window._on_node_double_clicked(n, wf))

                utils.logger.info(f"   📑 添加标签页到UI...", module="project_ui_manager")
                self.add_workflow_tab_to_ui(workflow)
                utils.logger.success(f"   ✅ 标签页添加完成", module="project_ui_manager")

                event_bus.publish(Events.WORKFLOW_ADDED, workflow=workflow)

            if project.workflows:
                utils.logger.info(f"\n🎯 激活第一个工作流...", module="project_ui_manager")
                self.main_window.tab_widget.setCurrentIndex(0)
                self.on_tab_changed(0)
                utils.logger.success(f"   ✅ 激活完成", module="project_ui_manager")

            self.add_to_recent_projects(os.path.dirname(os.path.abspath(file_path)))

            utils.logger.info(f"\n{'='*60}", module="project_ui_manager")
            utils.logger.success(f"✅ 工程打开流程完成!", module="project_ui_manager")
            utils.logger.info(f"{'='*60}\n", module="project_ui_manager")
        else:
            utils.logger.error(f"\n❌ 工程数据加载失败", module="project_ui_manager")
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

            if not file_path.endswith('.proj'):
                file_path += '.proj'

            project.file_path = file_path

        utils.logger.info(f"💾 开始保存工程: {project.name}", module="project_ui_manager")
        utils.logger.info(f"   目标文件: {project.file_path}", module="project_ui_manager")

        success = self.project_manager.export_project(project.file_path)

        if success:
            for i in range(self.main_window.tab_widget.count()):
                tab_text = self.main_window.tab_widget.tabText(i)
                if tab_text.endswith(" *"):
                    self.main_window.tab_widget.setTabText(i, tab_text[:-2])

            self.add_to_recent_projects(os.path.dirname(os.path.abspath(project.file_path)))

            try:
                size_bytes = os.path.getsize(project.file_path)
                if size_bytes < 1024:
                    size_str = f"{size_bytes} B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f} KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                utils.logger.success(f"✅ 工程已保存: {project.file_path} ({size_str})", module="project_ui_manager")
            except:
                utils.logger.success(f"✅ 工程已保存: {project.file_path}", module="project_ui_manager")

            event_bus.publish(Events.PROJECT_SAVED, project=project, file_path=project.file_path)
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

        recent_projects = settings.value("recent_projects", [])
        if isinstance(recent_projects, str):
            recent_projects = [recent_projects]

        if project_path in recent_projects:
            recent_projects.remove(project_path)

        recent_projects.insert(0, project_path)
        recent_projects = recent_projects[:10]

        settings.setValue("recent_projects", recent_projects)
        utils.logger.info(f"📋 已添加到最近工程列表: {project_path}", module="project_ui_manager")

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
        utils.logger.info("🗑️ 已清空最近工程列表", module="project_ui_manager")

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

        for i, project_path in enumerate(recent_projects):
            project_name = os.path.basename(project_path)

            action = QtWidgets.QAction(f"{i+1}. {project_name}", self.main_window)
            action.setStatusTip(project_path)
            action.triggered.connect(lambda checked, path=project_path: self.open_recent_project(path))
            recent_menu.addAction(action)

        recent_menu.addSeparator()

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

        event_bus.publish(Events.PROJECT_CLOSED, project=self.project_manager.current_project)
        self.project_manager.close_project()
        self.main_window.tab_widget.clear()

        project = self.project_manager.import_project(project_path)

        if project:
            event_bus.publish(Events.PROJECT_OPENED, project=project)

            workflows_session_data = getattr(project, '_workflows_session_data', {})

            for i, workflow in enumerate(project.workflows):
                if workflow.node_graph is None:
                    from NodeGraphQt import NodeGraph
                    node_graph = NodeGraph()

                    if hasattr(self.main_window, 'plugin_manager'):
                        register_nodes_on_workflow_create(node_graph, workflow, self.main_window.plugin_manager)

                    workflow.node_graph = node_graph

                    session_data = workflows_session_data.get(i)
                    if session_data:
                        try:
                            node_graph.deserialize_session(session_data)
                        except Exception as e:
                            utils.logger.error(f"❌ 加载工作流失败: {e}", module="project_ui_manager")

                    node_graph.node_created.connect(lambda n, wf=workflow: self.main_window._on_node_created(n, wf))
                    node_graph.node_double_clicked.connect(lambda n, wf=workflow: self.main_window._on_node_double_clicked(n, wf))

                self.add_workflow_tab_to_ui(workflow)
                event_bus.publish(Events.WORKFLOW_ADDED, workflow=workflow)

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
            utils.logger.info(f"🗑️ 已从最近列表中移除: {project_path}", module="project_ui_manager")

    def add_new_workflow_from_ui(self):
        """
        添加新的工作流（UI触发）
        """
        project = self.project_manager.current_project
        if not project:
            QtWidgets.QMessageBox.warning(self.main_window, "警告", "没有打开的工程")
            return

        workflow_name = f"工作流 {len(project.workflows) + 1}"
        workflow = self.project_manager.add_new_workflow(workflow_name)

        if workflow:
            node_graph = NodeGraph()
            workflow.node_graph = node_graph

            node_graph.node_created.connect(lambda n, wf=workflow: self.main_window._on_node_created(n, wf))
            node_graph.node_double_clicked.connect(lambda n, wf=workflow: self.main_window._on_node_double_clicked(n, wf))

            self.add_workflow_tab_to_ui(workflow)

            self.main_window.tab_widget.setCurrentIndex(self.main_window.tab_widget.count() - 1)
            self.on_tab_changed(self.main_window.tab_widget.count() - 1)

            event_bus.publish(Events.WORKFLOW_ADDED, workflow=workflow)

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

            tab_title = new_name
            if workflow.is_modified:
                tab_title += " *"
            self.main_window.tab_widget.setTabText(current_index, tab_title)

            event_bus.publish(Events.WORKFLOW_RENAMED, workflow=workflow, old_name=old_name, new_name=new_name)
            utils.logger.success(f"✅ 工作流已重命名: {old_name} -> {new_name}", module="project_ui_manager")

    def add_workflow_tab_to_ui(self, workflow):
        """
        将工作流添加到UI标签页

        Args:
            workflow: Workflow对象
        """
        utils.logger.info(f"   📊 add_workflow_tab_to_ui 被调用", module="project_ui_manager")
        utils.logger.info(f"      工作流名称: {workflow.name}", module="project_ui_manager")
        utils.logger.info(f"      NodeGraph 是否存在: {workflow.node_graph is not None}", module="project_ui_manager")

        if workflow.node_graph is None:
            utils.logger.warning(f"      ⚠️ NodeGraph 不存在，创建新的...", module="project_ui_manager")
            from NodeGraphQt import NodeGraph
            node_graph = NodeGraph()

            if hasattr(self.main_window, 'plugin_manager'):
                register_nodes_on_workflow_create(node_graph, workflow, self.main_window.plugin_manager)
            else:
                utils.logger.warning(f"      ⚠️ 未找到 plugin_manager，跳过节点注册", module="project_ui_manager")

            workflow.node_graph = node_graph

            utils.logger.info(f"      🔗 连接信号...", module="project_ui_manager")
            node_graph.node_created.connect(lambda n, wf=workflow: self.main_window._on_node_created(n, wf))
            node_graph.node_double_clicked.connect(lambda n, wf=workflow: self.main_window._on_node_double_clicked(n, wf))

        graph_widget = workflow.node_graph.widget
        utils.logger.info(f"      🖼️  获取 Graph Widget: {graph_widget}", module="project_ui_manager")

        graph_widget.installEventFilter(self.main_window)

        tab_title = workflow.name
        if workflow.is_modified:
            tab_title += " *"

        utils.logger.info(f"      ➕ 添加标签页: '{tab_title}'", module="project_ui_manager")
        tab_index = self.main_window.tab_widget.addTab(graph_widget, tab_title)
        utils.logger.success(f"      ✅ 标签页索引: {tab_index}", module="project_ui_manager")
        utils.logger.info(f"      📑 当前标签页总数: {self.main_window.tab_widget.count()}", module="project_ui_manager")
    
    def _on_plugin_reloaded(self, plugin_name: str):
        """
        插件重载事件处理（由事件总线触发）
        
        当插件文件发生变化并重新加载后，刷新所有工作流的节点注册表
        
        Args:
            plugin_name: 重载的插件名称
        """
        utils.logger.info(f"\n{'='*60}", module="project_ui_manager")
        utils.logger.info(f"🔄 收到插件重载事件: {plugin_name}", module="project_ui_manager")
        utils.logger.info(f"{'='*60}", module="project_ui_manager")
        
        project = self.project_manager.current_project
        if not project:
            utils.logger.warning(f"⚠️ 没有打开的工程，跳过节点刷新", module="project_ui_manager")
            return
        
        if not hasattr(self.main_window, 'plugin_manager'):
            utils.logger.warning(f"⚠️ 未找到 plugin_manager，跳过节点刷新", module="project_ui_manager")
            return
        
        utils.logger.info(f"📋 开始刷新所有工作流的节点...", module="project_ui_manager")
        
        for workflow in project.workflows:
            if workflow.node_graph:
                utils.logger.info(f"\n--- 刷新工作流: {workflow.name} ---", module="project_ui_manager")
                
                try:
                    # 使用 NodeRegistry 的重载方法刷新节点
                    node_registry.reload_nodes(workflow.node_graph, workflow)
                    utils.logger.success(f"   ✅ 工作流节点刷新完成", module="project_ui_manager")
                except Exception as e:
                    utils.logger.error(f"   ❌ 刷新工作流节点失败: {e}", module="project_ui_manager")
        
        utils.logger.info(f"\n{'='*60}", module="project_ui_manager")
        utils.logger.success(f"✅ 所有工作流节点刷新完成!", module="project_ui_manager")
        utils.logger.info(f"{'='*60}\n", module="project_ui_manager")
