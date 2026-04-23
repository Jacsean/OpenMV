"""
工程和工作流管理模块

提供工程管理功能，支持：
- 工作流（Workflow）：独立的节点图和执行流程
- 工程（Project）：包含多个工作流的容器
- 工程管理器（ProjectManager）：单例模式，管理当前工程

数据结构:
    工程文件结构 (.proj 实际是目录):
    my_project.proj/
    ├── project.json              # 工程配置文件
    ├── workflows/                # 工作流目录
    │   ├── workflow_1.json      # 工作流1的节点图数据
    │   ├── workflow_2.json      # 工作流2的节点图数据
    │   └── ...
    └── assets/                   # 资源文件（可选）
"""

import os
import json
import uuid
from datetime import datetime
from typing import List, Optional, Dict


class Workflow:
    """
    工作流类
    
    表示一个独立的节点图和执行流程。
    每个工作流包含一个NodeGraph实例和相关的元数据。
    
    Attributes:
        id (str): 工作流唯一标识符
        name (str): 工作流名称
        node_graph: NodeGraph实例（由外部管理）
        file_path (str): 工作流JSON文件路径
        is_modified (bool): 是否有未保存的修改
        created_time (str): 创建时间
        modified_time (str): 最后修改时间
    """
    
    def __init__(self, name: str = "新工作流", file_path: str = ""):
        """
        初始化工作流
        
        Args:
            name: 工作流名称
            file_path: 工作流JSON文件路径（可选）
        """
        self.id = str(uuid.uuid4())[:8]  # 短UUID
        self.name = name
        self.node_graph = None  # 由外部设置
        self.file_path = file_path
        self.is_modified = False
        self.created_time = datetime.now().isoformat()
        self.modified_time = self.created_time
        
    def mark_modified(self):
        """标记工作流为已修改状态"""
        self.is_modified = True
        self.modified_time = datetime.now().isoformat()
        
    def mark_saved(self):
        """标记工作流为已保存状态"""
        self.is_modified = False
        
    def to_dict(self) -> dict:
        """
        转换为字典（用于序列化）
        
        Returns:
            dict: 工作流信息字典
        """
        return {
            "id": self.id,
            "name": self.name,
            "file": self.file_path,
            "created": self.created_time,
            "modified": self.modified_time,
            "is_modified": self.is_modified
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'Workflow':
        """
        从字典创建工作流对象
        
        Args:
            data: 工作流信息字典
            
        Returns:
            Workflow: 工作流对象
        """
        workflow = cls(name=data.get("name", "未命名工作流"))
        workflow.id = data.get("id", workflow.id)
        workflow.file_path = data.get("file", "")
        workflow.created_time = data.get("created", workflow.created_time)
        workflow.modified_time = data.get("modified", workflow.modified_time)
        workflow.is_modified = data.get("is_modified", False)
        return workflow
        
    def __repr__(self):
        return f"Workflow(id='{self.id}', name='{self.name}', modified={self.is_modified})"


class Project:
    """
    工程类
    
    表示一个完整的工程项目，包含多个工作流。
    工程可以保存为目录结构，便于版本控制和协作。
    
    Attributes:
        name (str): 工程名称
        file_path (str): 工程目录路径
        version (str): 工程格式版本
        workflows (List[Workflow]): 工作流列表
        active_workflow_index (int): 当前激活的工作流索引
        created_time (str): 创建时间
        modified_time (str): 最后修改时间
    """
    
    def __init__(self, name: str = "新工程"):
        """
        初始化工程
        
        Args:
            name: 工程名称
        """
        self.name = name
        self.file_path = ""
        self.version = "3.0"
        self.workflows: List[Workflow] = []
        self.active_workflow_index = 0
        self.created_time = datetime.now().isoformat()
        self.modified_time = self.created_time
        
    def add_workflow(self, workflow: Workflow) -> int:
        """
        添加工作流到工程
        
        Args:
            workflow: 要添加的工作流对象
            
        Returns:
            int: 工作流在列表中的索引
        """
        self.workflows.append(workflow)
        self.mark_modified()
        return len(self.workflows) - 1
        
    def remove_workflow(self, index: int) -> bool:
        """
        从工程中移除工作流
        
        Args:
            index: 工作流索引
            
        Returns:
            bool: 是否成功移除
        """
        if 0 <= index < len(self.workflows):
            self.workflows.pop(index)
            # 调整激活索引
            if self.active_workflow_index >= len(self.workflows):
                self.active_workflow_index = max(0, len(self.workflows) - 1)
            self.mark_modified()
            return True
        return False
        
    def get_workflow(self, index: int) -> Optional[Workflow]:
        """
        获取指定索引的工作流
        
        Args:
            index: 工作流索引
            
        Returns:
            Workflow or None: 工作流对象
        """
        if 0 <= index < len(self.workflows):
            return self.workflows[index]
        return None
        
    def get_active_workflow(self) -> Optional[Workflow]:
        """
        获取当前激活的工作流
        
        Returns:
            Workflow or None: 激活的工作流对象
        """
        return self.get_workflow(self.active_workflow_index)
        
    def set_active_workflow(self, index: int) -> bool:
        """
        设置激活的工作流
        
        Args:
            index: 工作流索引
            
        Returns:
            bool: 是否成功设置
        """
        if 0 <= index < len(self.workflows):
            self.active_workflow_index = index
            return True
        return False
        
    def mark_modified(self):
        """标记工程为已修改状态"""
        self.modified_time = datetime.now().isoformat()
        # 同时标记当前工作流
        active_wf = self.get_active_workflow()
        if active_wf:
            active_wf.mark_modified()
            
    def to_dict(self) -> dict:
        """
        转换为字典（用于序列化）
        
        Returns:
            dict: 工程信息字典
        """
        return {
            "version": self.version,
            "name": self.name,
            "created": self.created_time,
            "modified": self.modified_time,
            "active_workflow_index": self.active_workflow_index,
            "workflows": [wf.to_dict() for wf in self.workflows]
        }
        
    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        """
        从字典创建工程对象
        
        Args:
            data: 工程信息字典
            
        Returns:
            Project: 工程对象
        """
        project = cls(name=data.get("name", "未命名工程"))
        project.version = data.get("version", "3.0")
        project.created_time = data.get("created", project.created_time)
        project.modified_time = data.get("modified", project.modified_time)
        project.active_workflow_index = data.get("active_workflow_index", 0)
        
        # 恢复工作流列表
        for wf_data in data.get("workflows", []):
            workflow = Workflow.from_dict(wf_data)
            project.workflows.append(workflow)
            
        return project
        
    def __repr__(self):
        return f"Project(name='{self.name}', workflows={len(self.workflows)}, active={self.active_workflow_index})"


class ProjectManager:
    """
    工程管理器（单例模式）
    
    负责管理当前工程的创建、打开、保存和关闭。
    提供全局访问点，确保整个应用中只有一个工程管理器实例。
    
    Attributes:
        current_project (Optional[Project]): 当前打开的工程
    """
    
    _instance = None
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            cls._instance = super(ProjectManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
        
    def __init__(self):
        """初始化管理器"""
        if self._initialized:
            return
            
        self.current_project: Optional[Project] = None
        self._initialized = True
        
    def create_project(self, name: str = "新工程") -> Project:
        """
        创建新工程
        
        Args:
            name: 工程名称
            
        Returns:
            Project: 创建的工程对象
        """
        self.current_project = Project(name=name)
        # 自动添加一个默认工作流
        default_workflow = Workflow(name="工作流 1")
        self.current_project.add_workflow(default_workflow)
        print(f"✅ 创建新工程: {name}")
        return self.current_project
        
    def open_project(self, project_dir: str) -> Optional[Project]:
        """
        打开已有工程
        
        Args:
            project_dir: 工程目录路径
            
        Returns:
            Project or None: 打开的工程对象，失败返回None
        """
        try:
            project_file = os.path.join(project_dir, "project.json")
            if not os.path.exists(project_file):
                print(f"❌ 工程文件不存在: {project_file}")
                return None
                
            # 读取工程配置
            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            self.current_project = Project.from_dict(data)
            self.current_project.file_path = project_dir
            print(f"✅ 打开工程: {self.current_project.name} ({len(self.current_project.workflows)} 个工作流)")
            return self.current_project
            
        except Exception as e:
            print(f"❌ 打开工程失败: {e}")
            import traceback
            traceback.print_exc()
            return None
            
    def save_project(self, project_dir: str = "") -> bool:
        """
        保存工程
        
        Args:
            project_dir: 工程目录路径（如果为空则使用当前路径）
            
        Returns:
            bool: 是否保存成功
        """
        if self.current_project is None:
            print("❌ 没有打开的工程")
            return False
            
        try:
            # 确定保存路径
            save_dir = project_dir if project_dir else self.current_project.file_path
            if not save_dir:
                print("❌ 未指定保存路径")
                return False
                
            # 创建目录结构
            workflows_dir = os.path.join(save_dir, "workflows")
            os.makedirs(workflows_dir, exist_ok=True)
            
            # 保存每个工作流
            for i, workflow in enumerate(self.current_project.workflows):
                if workflow.node_graph is not None:
                    # 更新工作流文件路径
                    wf_filename = f"workflow_{i+1}.json"
                    workflow.file_path = f"workflows/{wf_filename}"
                    
                    # 保存节点图数据
                    wf_full_path = os.path.join(save_dir, workflow.file_path)
                    workflow.node_graph.serialize_session(wf_full_path)
                    workflow.mark_saved()
                    print(f"  💾 保存工作流 {i+1}: {workflow.name}")
                    
            # 保存工程配置
            project_file = os.path.join(save_dir, "project.json")
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_project.to_dict(), f, indent=2, ensure_ascii=False)
                
            self.current_project.file_path = save_dir
            self.current_project.mark_modified()  # 更新时间戳
            self.current_project.modified_time = datetime.now().isoformat()
            
            print(f"✅ 工程已保存到: {save_dir}")
            return True
            
        except Exception as e:
            print(f"❌ 保存工程失败: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    def close_project(self):
        """关闭当前工程"""
        if self.current_project:
            print(f"🗑️ 关闭工程: {self.current_project.name}")
            self.current_project = None
            
    def has_unsaved_changes(self) -> bool:
        """
        检查是否有未保存的修改
        
        Returns:
            bool: 是否有未保存的修改
        """
        if self.current_project is None:
            return False
        return any(wf.is_modified for wf in self.current_project.workflows)
        
    def add_new_workflow(self, name: str = "新工作流") -> Optional[Workflow]:
        """
        在当前工程中添加新工作流
        
        Args:
            name: 工作流名称
            
        Returns:
            Workflow or None: 创建的工作流对象
        """
        if self.current_project is None:
            print("❌ 没有打开的工程")
            return None
            
        workflow = Workflow(name=name)
        index = self.current_project.add_workflow(workflow)
        print(f"✅ 添加工作流: {name} (索引: {index})")
        return workflow
        
    def remove_workflow(self, index: int) -> bool:
        """
        从当前工程中移除工作流
        
        Args:
            index: 工作流索引
            
        Returns:
            bool: 是否成功移除
        """
        if self.current_project is None:
            print("❌ 没有打开的工程")
            return False
            
        workflow = self.current_project.get_workflow(index)
        if workflow:
            result = self.current_project.remove_workflow(index)
            if result:
                print(f"🗑️ 移除工作流: {workflow.name}")
            return result
        return False
        
    def __repr__(self):
        if self.current_project:
            return f"ProjectManager(current='{self.current_project.name}')"
        return "ProjectManager(no project)"


# 全局单例实例
project_manager = ProjectManager()