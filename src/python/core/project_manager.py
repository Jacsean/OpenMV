
import utils
from utils import logger
"""
工程和工作流管理模块

提供工程管理功能，支持：
- 工作流（Workflow）：独立的节点图和执行流程
- 工程（Project）：包含多个工作流的容器
- 工程管理器（ProjectManager）：单例模式，管理当前工程

数据结构:
    工程文件结构 (v3.1 - 支持高效拷贝和搜索):
    
    模式A - 目录模式（适合开发调试）:
    my_project.proj/
    ├── project.json              # 工程元数据和配置（含标签、描述等搜索字段）
    ├── thumbnail.png             # 工程缩略图（用于预览和搜索）
    ├── index.json                # 全文索引（支持快速搜索）
    ├── workflows/                # 工作流目录
    │   ├── workflow_1.json      # 工作流1的节点图数据
    │   ├── workflow_2.json      # 工作流2的节点图数据
    │   └── ...
    ├── assets/                   # 资源文件目录
    │   ├── images/              # 图片资源
    │   ├── models/              # 模型文件
    │   └── references.json      # 资源引用关系表
    └── cache/                    # 缓存目录（可选）
        └── previews/            # 节点预览缓存
    
    模式B - 单文件模式（适合拷贝和分发）:
    my_project.proj               # ZIP压缩包（重命名为.proj）
      （内部结构同模式A）
    
    设计特点:
    - 支持标签、描述等元数据，便于搜索
    - 内置全文索引，支持关键词快速检索
    - 资源引用追踪，支持去重和清理
    - 缩略图预览，提升用户体验
    - 兼容ZIP压缩，便于网络传输
"""

import os
import json
import uuid
import zipfile
import shutil
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
        description (str): 工作流描述（用于搜索）
        node_graph: NodeGraph实例（由外部管理）
        file_path (str): 工作流JSON文件路径
        is_modified (bool): 是否有未保存的修改
        node_count (int): 节点数量统计
        preview_image (str): 预览图路径
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
        self.description = ""  # 工作流描述
        self.node_graph = None  # 由外部设置
        self.file_path = file_path
        self.is_modified = False
        self.node_count = 0  # 节点数量
        self.preview_image = ""  # 预览图路径
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
            "description": self.description,
            "file": self.file_path,
            "created": self.created_time,
            "modified": self.modified_time,
            "is_modified": self.is_modified,
            "node_count": self.node_count,
            "preview_image": self.preview_image
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
        workflow.description = data.get("description", "")
        workflow.file_path = data.get("file", "")
        workflow.created_time = data.get("created", workflow.created_time)
        workflow.modified_time = data.get("modified", workflow.modified_time)
        workflow.is_modified = data.get("is_modified", False)
        workflow.node_count = data.get("node_count", 0)
        workflow.preview_image = data.get("preview_image", "")
        return workflow
        
    def __repr__(self):
        return f"Workflow(id='{self.id}', name='{self.name}', modified={self.is_modified})"


class Project:
    """
    工程类
    
    表示一个完整的工程项目，包含多个工作流。
    工程可以保存为目录结构或单文件（ZIP），便于版本控制、拷贝和搜索。
    
    Attributes:
        name (str): 工程名称
        description (str): 工程描述（用于搜索）
        author (str): 作者信息
        tags (List[str]): 标签列表（用于搜索和分类）
        category (str): 工程分类
        file_path (str): 工程目录路径
        version (str): 工程格式版本（当前为 "3.1"）
        format_type (str): 存储格式（"directory" 或 "single_file"）
        thumbnail_path (str): 缩略图路径
        workflows (List[Workflow]): 工作流列表
        active_workflow_index (int): 当前激活的工作流索引
        created_time (str): 创建时间
        modified_time (str): 最后修改时间
        last_opened_time (str): 最后打开时间
        custom_metadata (Dict): 自定义元数据
    """
    
    def __init__(self, name: str = "新工程"):
        """
        初始化工程
        
        Args:
            name: 工程名称
        """
        self.name = name
        self.description = ""  # 工程描述
        self.author = ""  # 作者
        self.tags: List[str] = []  # 标签列表
        self.category = ""  # 分类
        self.file_path = ""
        self.version = "3.1"  # 更新版本号
        self.format_type = "directory"  # directory 或 single_file
        self.thumbnail_path = ""  # 缩略图路径
        self.workflows: List[Workflow] = []
        self.active_workflow_index = 0
        self.created_time = datetime.now().isoformat()
        self.modified_time = self.created_time
        self.last_opened_time = ""
        self.custom_metadata: Dict = {}  # 自定义元数据
        
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
            "format": self.format_type,
            "name": self.name,
            "description": self.description,
            "author": self.author,
            "tags": self.tags,
            "category": self.category,
            "thumbnail": self.thumbnail_path,
            "created": self.created_time,
            "modified": self.modified_time,
            "last_opened": self.last_opened_time,
            "active_workflow_index": self.active_workflow_index,
            "stats": self._calculate_stats(),
            "workflows": [wf.to_dict() for wf in self.workflows],
            "custom_metadata": self.custom_metadata
        }
        
    def _calculate_stats(self) -> dict:
        """
        计算工程统计信息
        
        Returns:
            dict: 统计信息
        """
        total_nodes = sum(wf.node_count for wf in self.workflows)
        return {
            "workflow_count": len(self.workflows),
            "node_count": total_nodes,
            "asset_count": 0,  # TODO: 从references.json读取
            "total_size_bytes": 0  # TODO: 计算实际大小
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
        project.version = data.get("version", "3.1")
        project.format_type = data.get("format", "directory")
        project.description = data.get("description", "")
        project.author = data.get("author", "")
        project.tags = data.get("tags", [])
        project.category = data.get("category", "")
        project.thumbnail_path = data.get("thumbnail", "")
        project.created_time = data.get("created", project.created_time)
        project.modified_time = data.get("modified", project.modified_time)
        project.last_opened_time = data.get("last_opened", "")
        project.active_workflow_index = data.get("active_workflow_index", 0)
        project.custom_metadata = data.get("custom_metadata", {})
        
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
        utils.logger.success(f"✅ 创建新工程: {name}", module="project_manager")
        return self.current_project
        
    def open_project(self, proj_file: str) -> Optional[Project]:
        """
        打开工程（从单文件.proj加载）
        
        Args:
            proj_file: .proj文件路径
            
        Returns:
            Project or None: 打开的工程对象，失败返回None
        """
        # 直接调用import_project方法
        return self.import_project(proj_file)
        
    def save_project(self, proj_file: str = "") -> bool:
        """
        保存工程为单文件（.proj ZIP格式）
        
        Args:
            proj_file: 输出文件路径（如果为空则使用当前路径）
            
        Returns:
            bool: 是否保存成功
        """
        if self.current_project is None:
            utils.logger.error("❌ 没有打开的工程", module="project_manager")
            return False
        
        # 确定保存路径
        output_file = proj_file if proj_file else self.current_project.file_path
        if not output_file:
            utils.logger.error("❌ 未指定保存路径", module="project_manager")
            return False
        
        # 确保文件扩展名为.proj
        if not output_file.endswith('.proj'):
            output_file += '.proj'
        
        # 直接调用export_project方法
        return self.export_project(output_file)
        
    def close_project(self):
        """关闭当前工程"""
        if self.current_project:
            utils.logger.info(f"🗑️ 关闭工程: {self.current_project.name}", module="project_manager")
            self.current_project = None
            
    def export_project(self, output_file: str) -> bool:
        """
        导出工程为单文件（ZIP格式）
        
        Args:
            output_file: 输出文件路径（.proj）
            
        Returns:
            bool: 是否导出成功
        """
        if self.current_project is None:
            utils.logger.error("❌ 没有打开的工程", module="project_manager")
            return False
        
        utils.logger.info(f"\n{'='*60}", module="project_manager")
        utils.logger.info(f"📦 开始导出工程: {self.current_project.name}", module="project_manager")
        utils.logger.info(f"   目标文件: {output_file}", module="project_manager")
        utils.logger.info(f"   工作流数量: {len(self.current_project.workflows)}", module="project_manager")
        utils.logger.info(f"{'='*60}\n", module="project_manager")
        
        try:
            # 先保存到临时目录
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix='proj_export_')
            utils.logger.info(f"📁 创建临时目录: {temp_dir}", module="project_manager")
            
            # === 在临时目录中保存工作流文件 ===
            workflows_dir = os.path.join(temp_dir, "workflows")
            os.makedirs(workflows_dir, exist_ok=True)
            utils.logger.info(f"📁 创建工作流目录: {workflows_dir}", module="project_manager")
            
            # 保存每个工作流
            for i, workflow in enumerate(self.current_project.workflows):
                utils.logger.info(f"\n--- 处理工作流 {i+1}: {workflow.name} ---", module="project_manager")
                
                if workflow.node_graph is None:
                    utils.logger.warning(f"⚠️ 工作流 {workflow.name} 没有 NodeGraph，跳过", module="project_manager")
                    continue
                
                wf_filename = f"workflow_{i+1}.json"
                workflow.file_path = f"workflows/{wf_filename}"
                
                # 保存节点图数据
                wf_full_path = os.path.join(temp_dir, workflow.file_path)
                utils.logger.info(f"💾 保存节点图到: {wf_full_path}", module="project_manager")
                
                # 获取序列化数据并记录大小
                session_data = workflow.node_graph.serialize_session()
                data_size = len(json.dumps(session_data))
                utils.logger.info(f"   📊 节点图数据大小: {data_size} bytes", module="project_manager")
                
                # 统计节点数量
                node_count = len(workflow.node_graph.all_nodes())
                utils.logger.info(f"   🔢 节点数量: {node_count}", module="project_manager")
                
                # 实际保存
                workflow.node_graph.save_session(wf_full_path)
                
                # 验证文件是否生成
                if os.path.exists(wf_full_path):
                    file_size = os.path.getsize(wf_full_path)
                    utils.logger.success(f"   ✅ 文件已生成，大小: {file_size} bytes", module="project_manager")
                else:
                    utils.logger.error(f"   ❌ 文件未生成！", module="project_manager")
                    return False
                
                workflow.mark_saved()
            
            # 生成索引文件
            utils.logger.info(f"\n📝 生成索引文件...", module="project_manager")
            index_data = ProjectIndexer.generate_index(self.current_project)
            index_file = os.path.join(temp_dir, "index.json")
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, indent=2, ensure_ascii=False)
            utils.logger.success(f"   ✅ 索引文件已生成", module="project_manager")
            
            # 保存工程配置文件
            utils.logger.info(f"📝 保存工程配置...", module="project_manager")
            project_file = os.path.join(temp_dir, "project.json")
            with open(project_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_project.to_dict(), f, indent=2, ensure_ascii=False)
            utils.logger.success(f"   ✅ 工程配置已保存", module="project_manager")
            
            # 压缩为ZIP
            utils.logger.info(f"\n🗜️  压缩为ZIP文件...", module="project_manager")
            with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
                file_count = 0
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, temp_dir)
                        zipf.write(file_path, arcname)
                        file_count += 1
                        utils.logger.info(f"   📦 添加文件: {arcname}", module="project_manager")
                utils.logger.success(f"   ✅ 共压缩 {file_count} 个文件", module="project_manager")
            
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)
            utils.logger.info(f"🧹 清理临时目录", module="project_manager")
            
            # 更新工程元数据
            self.current_project.format_type = "single_file"
            self.current_project.file_path = output_file
            
            final_size = os.path.getsize(output_file)
            utils.logger.info(f"\n{'='*60}", module="project_manager")
            utils.logger.success(f"✅ 工程导出成功!", module="project_manager")
            utils.logger.info(f"   文件: {output_file}", module="project_manager")
            utils.logger.info(f"   大小: {final_size} bytes ({final_size/1024:.2f} KB)", module="project_manager")
            utils.logger.info(f"{'='*60}\n", module="project_manager")
            return True
            
        except Exception as e:
            utils.logger.info(f"\n{'='*60}", module="project_manager")
            utils.logger.error(f"❌ 导出工程失败!", module="project_manager")
            utils.logger.error(f"   错误类型: {type(e).__name__}", module="project_manager")
            utils.logger.error(f"   错误信息: {str(e)}", module="project_manager")
            utils.logger.info(f"{'='*60}\n", module="project_manager")
            import traceback
            traceback.print_exc()
            return False
    
    def import_project(self, proj_file: str) -> Optional[Project]:
        """
        从单文件导入工程
        
        Args:
            proj_file: .proj文件路径
            
        Returns:
            Project or None: 导入的工程对象
        """
        utils.logger.info(f"\n{'='*60}", module="project_manager")
        utils.logger.info(f"📂 开始导入工程", module="project_manager")
        utils.logger.info(f"   文件路径: {proj_file}", module="project_manager")
        utils.logger.info(f"{'='*60}\n", module="project_manager")
        
        try:
            # 验证文件是否存在
            if not os.path.exists(proj_file):
                utils.logger.error(f"❌ 文件不存在: {proj_file}", module="project_manager")
                return None
            
            file_size = os.path.getsize(proj_file)
            utils.logger.info(f"📊 文件大小: {file_size} bytes ({file_size/1024:.2f} KB)", module="project_manager")
            
            # 创建临时目录解压
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix='proj_import_')
            utils.logger.info(f"📁 创建临时目录: {temp_dir}", module="project_manager")
            
            # 解压ZIP
            utils.logger.info(f"🗜️  解压ZIP文件...", module="project_manager")
            with zipfile.ZipFile(proj_file, 'r') as zipf:
                file_list = zipf.namelist()
                utils.logger.info(f"   📦 ZIP包含 {len(file_list)} 个文件:", module="project_manager")
                for fname in file_list:
                    utils.logger.info(f"      - {fname}", module="project_manager")
                zipf.extractall(temp_dir)
            utils.logger.success(f"   ✅ 解压完成", module="project_manager")
            
            # === 直接从临时目录读取工程配置 ===
            project_file = os.path.join(temp_dir, "project.json")
            if not os.path.exists(project_file):
                utils.logger.error(f"❌ 工程配置文件不存在: {project_file}", module="project_manager")
                shutil.rmtree(temp_dir, ignore_errors=True)
                return None
            
            utils.logger.info(f"\n📝 读取工程配置...", module="project_manager")
            # 读取工程配置
            with open(project_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.current_project = Project.from_dict(data)
            self.current_project.file_path = os.path.dirname(os.path.abspath(proj_file))
            self.current_project.format_type = "single_file"
            
            utils.logger.success(f"   ✅ 工程名称: {self.current_project.name}", module="project_manager")
            utils.logger.success(f"   ✅ 工作流数量: {len(self.current_project.workflows)}", module="project_manager")
            for i, wf in enumerate(self.current_project.workflows):
                utils.logger.info(f"      [{i+1}] {wf.name}", module="project_manager")
            
            # === 关键修复：预加载工作流节点图数据到内存 ===
            utils.logger.info(f"\n📦 预加载工作流节点图数据...", module="project_manager")
            workflows_data = {}
            workflows_dir = os.path.join(temp_dir, "workflows")
            if os.path.exists(workflows_dir):
                wf_files = [f for f in os.listdir(workflows_dir) if f.endswith('.json')]
                utils.logger.info(f"   📁 找到 {len(wf_files)} 个工作流文件", module="project_manager")
                
                for wf_file in wf_files:
                    wf_index = int(wf_file.replace('workflow_', '').replace('.json', '')) - 1
                    wf_full_path = os.path.join(workflows_dir, wf_file)
                    
                    try:
                        file_size = os.path.getsize(wf_full_path)
                        utils.logger.info(f"\n   --- 加载工作流 {wf_index+1}: {wf_file} ---", module="project_manager")
                        utils.logger.info(f"   📊 文件大小: {file_size} bytes", module="project_manager")
                        
                        with open(wf_full_path, 'r', encoding='utf-8') as f:
                            wf_data = json.load(f)
                        
                        # 统计节点数量
                        if 'nodes' in wf_data:
                            node_count = len(wf_data['nodes'])
                            utils.logger.info(f"   🔢 节点数量: {node_count}", module="project_manager")
                            
                            # 列出所有节点类型
                            if node_count > 0:
                                node_types = set()
                                for node_id, node_info in wf_data['nodes'].items():
                                    if 'type_' in node_info:
                                        node_types.add(node_info['type_'])
                                utils.logger.info(f"   🏷️  节点类型: {', '.join(sorted(node_types))}", module="project_manager")
                        
                        workflows_data[wf_index] = wf_data
                        utils.logger.success(f"   ✅ 预加载成功", module="project_manager")
                    except Exception as e:
                        utils.logger.error(f"   ❌ 加载工作流数据失败 {wf_file}: {e}", module="project_manager")
                        import traceback
                        traceback.print_exc()
            else:
                utils.logger.warning(f"   ⚠️ 未找到工作流目录: {workflows_dir}", module="project_manager")
            
            # 将预加载的数据附加到工程对象（供UI管理器使用）
            self.current_project._workflows_session_data = workflows_data
            self.current_project._import_temp_dir = temp_dir  # 保存临时目录引用
            
            utils.logger.info(f"\n{'='*60}", module="project_manager")
            utils.logger.success(f"✅ 工程导入成功!", module="project_manager")
            utils.logger.info(f"   工作流数量: {len(self.current_project.workflows)}", module="project_manager")
            utils.logger.info(f"   预加载节点图数据: {len(workflows_data)} 个", module="project_manager")
            utils.logger.info(f"{'='*60}\n", module="project_manager")
            
            return self.current_project
            
        except Exception as e:
            utils.logger.info(f"\n{'='*60}", module="project_manager")
            utils.logger.error(f"❌ 导入工程失败!", module="project_manager")
            utils.logger.error(f"   错误类型: {type(e).__name__}", module="project_manager")
            utils.logger.error(f"   错误信息: {str(e)}", module="project_manager")
            utils.logger.info(f"{'='*60}\n", module="project_manager")
            import traceback
            traceback.print_exc()
            return None
    
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
            utils.logger.error("❌ 没有打开的工程", module="project_manager")
            return None
            
        workflow = Workflow(name=name)
        index = self.current_project.add_workflow(workflow)
        utils.logger.success(f"✅ 添加工作流: {name} (索引: {index})", module="project_manager")
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
            utils.logger.error("❌ 没有打开的工程", module="project_manager")
            return False
            
        workflow = self.current_project.get_workflow(index)
        if workflow:
            result = self.current_project.remove_workflow(index)
            if result:
                utils.logger.info(f"🗑️ 移除工作流: {workflow.name}", module="project_manager")
            return result
        return False
        
    def __repr__(self):
        if self.current_project:
            return f"ProjectManager(current='{self.current_project.name}')"
        return "ProjectManager(no project)"


class ProjectIndexer:
    """
    工程索引器
    
    负责生成和维护工程的全文索引，支持快速搜索。
    
    Attributes:
        index_data (Dict): 索引数据
    """
    
    @staticmethod
    def generate_index(project: Project) -> dict:
        """
        为工程生成全文索引
        
        Args:
            project: 工程对象
            
        Returns:
            dict: 索引数据
        """
        # 收集所有可搜索文本
        workflow_names = " ".join(wf.name for wf in project.workflows)
        workflow_descriptions = " ".join(wf.description for wf in project.workflows if wf.description)
        
        # 提取节点类型（从工作流文件中）
        node_types_set = set()
        for wf in project.workflows:
            if wf.node_graph:
                for node in wf.node_graph.all_nodes():
                    node_types_set.add(type(node).__name__)
        node_types = " ".join(node_types_set)
        
        # 构建索引
        index_data = {
            "indexed_at": datetime.now().isoformat(),
            "searchable_text": {
                "title": project.name,
                "description": project.description,
                "tags": " ".join(project.tags),
                "category": project.category,
                "author": project.author,
                "workflow_names": workflow_names,
                "workflow_descriptions": workflow_descriptions,
                "node_types": node_types
            },
            "keywords": ProjectIndexer._build_keyword_index(project),
            "filters": {
                "has_images": False,  # TODO: 检查assets目录
                "has_models": False,
                "min_nodes": min((wf.node_count for wf in project.workflows), default=0),
                "max_nodes": max((wf.node_count for wf in project.workflows), default=0),
                "categories": [project.category] if project.category else []
            }
        }
        
        return index_data
    
    @staticmethod
    def _build_keyword_index(project: Project) -> dict:
        """
        构建关键词倒排索引
        
        Args:
            project: 工程对象
            
        Returns:
            dict: 关键词索引
        """
        keyword_index = {}
        
        # 从标签建立索引
        for tag in project.tags:
            keyword_index.setdefault(tag.lower(), []).append("project")
        
        # 从工作流名称建立索引
        for wf in project.workflows:
            words = wf.name.lower().split()
            for word in words:
                if len(word) > 1:  # 忽略单字符
                    keyword_index.setdefault(word, []).append(wf.id)
        
        # 从描述建立索引
        if project.description:
            for word in project.description.lower().split():
                if len(word) > 1:
                    keyword_index.setdefault(word, []).append("project")
        
        return keyword_index
    
    @staticmethod
    def search_projects(project_dirs: List[str], keywords: str) -> List[dict]:
        """
        在多个工程中搜索关键词
        
        Args:
            project_dirs: 工程目录列表
            keywords: 搜索关键词（空格分隔多个词）
            
        Returns:
            List[dict]: 匹配的工程信息列表（按相关度排序）
        """
        results = []
        search_terms = keywords.lower().split()
        
        for proj_dir in project_dirs:
            try:
                project_file = os.path.join(proj_dir, "project.json")
                if not os.path.exists(project_file):
                    continue
                
                with open(project_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 计算相关度得分
                score = ProjectIndexer._calculate_relevance(data, search_terms)
                
                if score > 0:
                    results.append({
                        "path": proj_dir,
                        "name": data.get("name", ""),
                        "description": data.get("description", ""),
                        "tags": data.get("tags", []),
                        "score": score,
                        "modified": data.get("modified", "")
                    })
            except Exception as e:
                utils.logger.error(f"⚠️ 读取工程失败 {proj_dir}: {e}", module="project_manager")
        
        # 按相关度排序
        results.sort(key=lambda x: x["score"], reverse=True)
        return results
    
    @staticmethod
    def _calculate_relevance(project_data: dict, search_terms: List[str]) -> float:
        """
        计算工程与搜索词的相关度
        
        Args:
            project_data: 工程数据
            search_terms: 搜索词列表
            
        Returns:
            float: 相关度得分
        """
        score = 0.0
        
        # 合并所有可搜索文本
        searchable = " ".join([
            project_data.get("name", "").lower(),
            project_data.get("description", "").lower(),
            " ".join(project_data.get("tags", [])).lower(),
            project_data.get("category", "").lower()
        ])
        
        # 检查每个搜索词
        for term in search_terms:
            if term in searchable:
                score += 1.0
                # 完全匹配名称加分更多
                if term in project_data.get("name", "").lower():
                    score += 2.0
                # 匹配标签加分
                if term in [t.lower() for t in project_data.get("tags", [])]:
                    score += 1.5
        
        return score


# 全局单例实例
project_manager = ProjectManager()