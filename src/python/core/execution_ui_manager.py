import utils
from utils import logger
"""
执行UI管理器

负责处理与节点图执行相关的UI交互逻辑，包括：
- 执行当前工作流
- 批量执行所有工作流
- 清空工作流的确认对话框
- 节点图保存/加载
- 执行结果展示和预览窗口刷新

本模块已重构为事件驱动：
- 通过 EventBus 发布事件通知执行状态变更
- UI响应逻辑由订阅者处理
"""

import json
from core.event_bus import event_bus, Events

from PySide2 import QtWidgets


class ExecutionUIManager:
    """
    执行UI管理器

    职责：
    - 处理节点图执行相关的UI交互
    - 发布事件而非直接操作UI
    - 提供简洁的API供MainWindow调用

    事件发布：
    - WORKFLOW_EXECUTING: 工作流开始执行
    - WORKFLOW_EXECUTED: 工作流执行完成
    - WORKFLOW_EXECUTION_ERROR: 工作流执行出错
    - WORKFLOW_CLEARED: 工作流已清空
    - WORKFLOW_SAVED: 工作流已保存
    - WORKFLOW_LOADED: 工作流已加载
    """

    def __init__(self, graph_engine, main_window):
        """
        初始化执行UI管理器

        Args:
            graph_engine: GraphEngine实例
            main_window: MainWindow实例（用于访问UI组件）
        """
        self.graph_engine = graph_engine
        self.main_window = main_window

    def _get_current_workflow(self):
        """
        获取当前工作流对象

        Returns:
            Workflow or None
        """
        project = self.main_window.project_manager.current_project
        if project:
            tab_index = self.main_window.tab_widget.currentIndex()
            if 0 <= tab_index < len(project.workflows):
                return project.workflows[tab_index]
        return None

    def run_current_graph(self):
        """
        执行当前激活的节点图（UI触发）
        """
        if not self.main_window.current_node_graph:
            QtWidgets.QMessageBox.warning(self.main_window, "警告", "没有激活的工作流")
            return

        workflow = self._get_current_workflow()

        if not workflow:
            QtWidgets.QMessageBox.warning(self.main_window, "警告", "无法获取当前工作流")
            return

        utils.logger.info("=" * 50, module="execution_ui_manager")
        utils.logger.info("开始执行节点图...", module="execution_ui_manager")
        utils.logger.info("=" * 50, module="execution_ui_manager")

        event_bus.publish(Events.WORKFLOW_EXECUTING, workflow=workflow)

        try:
            results = self.graph_engine.execute_graph(self.main_window.current_node_graph)

            utils.logger.info("=" * 50, module="execution_ui_manager")
            utils.logger.success("节点图执行完成!", module="execution_ui_manager")
            utils.logger.info("=" * 50, module="execution_ui_manager")

            if results:
                utils.logger.info(f"处理了 {len(results)} 个节点的输出", module="execution_ui_manager")

            event_bus.publish(Events.WORKFLOW_EXECUTED, workflow=workflow, results=results)

        except Exception as e:
            utils.logger.error(f"执行错误: {e}", module="execution_ui_manager")
            import traceback
            traceback.print_exc()

            event_bus.publish(Events.WORKFLOW_EXECUTION_ERROR, workflow=workflow, error=e)

            QtWidgets.QMessageBox.critical(
                self.main_window,
                "执行错误",
                f"执行节点图时发生错误:\n{str(e)}"
            )

    def run_all_workflows(self):
        """
        执行所有工作流（UI触发）
        """
        project = self.main_window.project_manager.current_project
        if not project or not project.workflows:
            QtWidgets.QMessageBox.warning(self.main_window, "警告", "没有可执行的工作流")
            return

        utils.logger.info("=" * 50, module="execution_ui_manager")
        utils.logger.info("开始执行所有工作流...", module="execution_ui_manager")
        utils.logger.info("=" * 50, module="execution_ui_manager")

        success_count = 0
        for i, workflow in enumerate(project.workflows):
            utils.logger.info(f"\n--- 执行工作流 [{i+1}/{len(project.workflows)}]: {workflow.name} ---", module="execution_ui_manager")
            try:
                if workflow.node_graph:
                    event_bus.publish(Events.WORKFLOW_EXECUTING, workflow=workflow)
                    self.graph_engine.execute_graph(workflow.node_graph)
                    event_bus.publish(Events.WORKFLOW_EXECUTED, workflow=workflow, results={})
                    success_count += 1
            except Exception as e:
                utils.logger.error(f"❌ 工作流 '{workflow.name}' 执行失败: {e}", module="execution_ui_manager")
                event_bus.publish(Events.WORKFLOW_EXECUTION_ERROR, workflow=workflow, error=e)

        utils.logger.info("\n" + "=" * 50, module="execution_ui_manager")
        utils.logger.success(f"所有工作流执行完毕. 成功: {success_count}/{len(project.workflows)}", module="execution_ui_manager")
        utils.logger.info("=" * 50, module="execution_ui_manager")

        event_bus.publish(Events.PREVIEW_REFRESH)

    def clear_graph_with_confirmation(self):
        """
        清空当前激活的节点图（带确认对话框）
        """
        if not self.main_window.current_node_graph:
            return

        reply = QtWidgets.QMessageBox.question(
            self.main_window,
            "确认清空",
            "确定要清空当前节点图吗？",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            workflow = self._get_current_workflow()
            self.main_window.current_node_graph.clear_session()
            utils.logger.info("节点图已清空", module="execution_ui_manager")
            event_bus.publish(Events.WORKFLOW_CLEARED, workflow=workflow)

    def clear_all_graphs_with_confirmation(self):
        """
        清空所有工作流的节点图（带确认对话框）
        """
        project = self.main_window.project_manager.current_project
        if not project or not project.workflows:
            QtWidgets.QMessageBox.warning(self.main_window, "警告", "没有可清空的工作流")
            return

        workflow_count = len(project.workflows)
        
        reply = QtWidgets.QMessageBox.question(
            self.main_window,
            "确认清空所有",
            f"确定要清空所有 {workflow_count} 个工作流吗？\n此操作不可撤销！",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No,
            QtWidgets.QMessageBox.No
        )

        if reply == QtWidgets.QMessageBox.Yes:
            for workflow in project.workflows:
                if workflow.node_graph:
                    workflow.node_graph.clear_session()
                    workflow.mark_modified()
            
            utils.logger.info("所有节点图已清空", module="execution_ui_manager")
            event_bus.publish(Events.WORKFLOW_CLEARED, workflow=None)
            
            QtWidgets.QMessageBox.information(
                self.main_window,
                "清空成功",
                f"已清空所有 {workflow_count} 个工作流"
            )

    def save_graph_to_file(self):
        """
        保存当前节点图到JSON文件（UI触发）
        """
        if not self.main_window.current_node_graph:
            return

        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.main_window,
            "保存节点图",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                self.main_window.current_node_graph.save_session(file_path)

                utils.logger.info(f"节点图已保存到: {file_path}", module="execution_ui_manager")

                workflow = self._get_current_workflow()
                event_bus.publish(Events.WORKFLOW_SAVED, workflow=workflow, file_path=file_path)

                QtWidgets.QMessageBox.information(
                    self.main_window,
                    "保存成功",
                    f"节点图已保存到:\n{file_path}"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self.main_window,
                    "保存失败",
                    f"保存节点图时发生错误:\n{str(e)}"
                )

    def load_graph_from_file(self):
        """
        从JSON文件加载节点图到当前标签页（UI触发）
        """
        if not self.main_window.current_node_graph:
            return

        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.main_window,
            "加载节点图",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                self.main_window.current_node_graph.deserialize_session(session_data)

                utils.logger.info(f"节点图已从 {file_path} 加载", module="execution_ui_manager")

                workflow = self._get_current_workflow()
                event_bus.publish(Events.WORKFLOW_LOADED, workflow=workflow, file_path=file_path)

                QtWidgets.QMessageBox.information(
                    self.main_window,
                    "加载成功",
                    f"节点图已从:\n{file_path}\n加载"
                )
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self.main_window,
                    "加载失败",
                    f"加载节点图时发生错误:\n{str(e)}"
                )
