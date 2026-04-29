
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
"""

import json
from PySide2 import QtWidgets


class ExecutionUIManager:
    """
    执行UI管理器
    
    职责：
    - 封装所有执行相关的UI交互逻辑
    - 提供简洁的API供MainWindow调用
    - 处理节点图执行、保存、加载的用户界面
    - 管理预览窗口的自动刷新
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
    
    def run_current_graph(self):
        """
        执行当前激活的节点图（UI触发）
        """
        if not self.main_window.current_node_graph:
            QtWidgets.QMessageBox.warning(self.main_window, "警告", "没有激活的工作流")
            return

        utils.logger.info("=" * 50, module="execution_ui_manager")
        utils.logger.info("开始执行节点图...", module="execution_ui_manager")
        utils.logger.info("=" * 50, module="execution_ui_manager")
        
        try:
            # 执行节点图
            results = self.graph_engine.execute_graph(self.main_window.current_node_graph)
            
            utils.logger.info("=" * 50, module="execution_ui_manager")
            utils.logger.success("节点图执行完成!", module="execution_ui_manager")
            utils.logger.info("=" * 50, module="execution_ui_manager")
            
            # 显示结果摘要
            if results:
                utils.logger.info(f"处理了 {len(results)} 个节点的输出", module="execution_ui_manager")
                
            # 自动刷新所有打开的预览窗口
            self.refresh_all_previews()
                
        except Exception as e:
            utils.logger.error(f"执行错误: {e}", module="execution_ui_manager")
            import traceback
            traceback.print_exc()
            
            # 显示错误对话框
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
                    self.graph_engine.execute_graph(workflow.node_graph)
                    success_count += 1
            except Exception as e:
                utils.logger.error(f"❌ 工作流 '{workflow.name}' 执行失败: {e}", module="execution_ui_manager")
                
        utils.logger.info("\n" + "=" * 50, module="execution_ui_manager")
        utils.logger.success(f"所有工作流执行完毕. 成功: {success_count}/{len(project.workflows)}", module="execution_ui_manager")
        utils.logger.info("=" * 50, module="execution_ui_manager")
        
        # 刷新所有预览
        self.refresh_all_previews()
    
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
            self.main_window.current_node_graph.clear_session()
            utils.logger.info("节点图已清空", module="execution_ui_manager")
    
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
                # 使用save_session()直接保存
                self.main_window.current_node_graph.save_session(file_path)
                
                utils.logger.info(f"节点图已保存到: {file_path}", module="execution_ui_manager")
                
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
                # 读取JSON文件，然后使用deserialize_session()
                with open(file_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                self.main_window.current_node_graph.deserialize_session(session_data)
                
                utils.logger.info(f"节点图已从 {file_path} 加载", module="execution_ui_manager")
                
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
    
    def refresh_all_previews(self):
        """
        刷新所有打开的预览窗口
        """
        if not self.main_window.preview_windows:
            return
        
        refreshed_count = 0
        for node_id, dialog in list(self.main_window.preview_windows.items()):
            # 检查窗口是否仍然有效
            if dialog.isVisible():
                dialog.refresh_preview()
                refreshed_count += 1
        
        if refreshed_count > 0:
            utils.logger.success(f"✅ 已自动刷新 {refreshed_count} 个预览窗口", module="execution_ui_manager")
