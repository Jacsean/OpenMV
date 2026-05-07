import utils
from utils import logger

"""
插件管理器 - 负责插件的扫描、加载和管理
"""

import os
import sys
import json
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Type, Tuple

from .models import PluginInfo, NodeDefinition
from .sandbox import PluginSandbox, SandboxSecurityError
from .permission_checker import PermissionChecker
from .hot_reloader import HotReloader
from .dependency_resolver import DependencyResolver
from .plugin_installer import PluginInstaller


class PluginManager:
    """插件管理器（单例）"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        self.plugins: Dict[str, PluginInfo] = {}
        self.loaded_nodes: Dict[str, Type] = {}  # 已加载的节点类
        
        # 两层插件目录结构
        self.plugins_dir = Path(__file__).parent.parent / "plugin_packages"
        self.builtin_dir = self.plugins_dir / "builtin"
        self.marketplace_dir = self.plugins_dir / "marketplace" / "installed"
        
        # 确保目录存在
        self.builtin_dir.mkdir(parents=True, exist_ok=True)
        self.marketplace_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化沙箱环境
        self.sandbox = PluginSandbox()
        
        # 初始化热重载器
        self.hot_reloader = HotReloader()
        
        # 初始化依赖解析器
        self.dependency_resolver = DependencyResolver()
        
        # 初始化安装器
        self.installer = PluginInstaller(self.plugins_dir)

    def scan_plugins(self) -> List[PluginInfo]:
        """
        扫描插件目录，返回插件信息列表
        
        Returns:
            List[PluginInfo]: 插件信息列表
        """
        plugins = []
        
        # 扫描builtin目录（优先级最高）
        if self.builtin_dir.exists():
            utils.logger.info("\n📦 扫描内置插件 (builtin)...", module="plugin_manager")
            builtin_plugins = self._scan_directory(self.builtin_dir, source='builtin', priority=1)
            plugins.extend(builtin_plugins)
        
        # 扫描marketplace目录（优先级中等）
        if self.marketplace_dir.exists():
            utils.logger.info("\n📦 扫描市场插件 (marketplace)...", module="plugin_manager")
            marketplace_plugins = self._scan_directory(self.marketplace_dir, source='marketplace', priority=2)
            plugins.extend(marketplace_plugins)
        
        utils.logger.info(f"\n✅ 共扫描到 {len(plugins)} 个插件", module="plugin_manager")
        return plugins

    def _scan_directory(self, directory: Path, source='builtin', priority=1) -> List[PluginInfo]:
        """
        扫描指定目录下的插件
        
        Args:
            directory: 插件目录路径
            source: 插件来源 ('builtin' 或 'marketplace')
            priority: 加载优先级
            
        Returns:
            List[PluginInfo]: 插件信息列表
        """
        plugins = []
        
        if not directory.exists():
            return plugins
        
        # 特殊处理：builtin 目录本身可能是一个插件（新结构）
        if source == 'builtin':
            metadata_file = directory / "plugin.json"
            if metadata_file.exists():
                builtin_plugin_info = self._load_plugin_metadata(directory, source=source, priority=priority)
                if builtin_plugin_info:
                    plugins.append(builtin_plugin_info)
                    self.plugins[builtin_plugin_info.name] = builtin_plugin_info
                    utils.logger.info(f"   ✅ {directory.name} (source: {source}, new structure)", module="plugin_manager")
                    return plugins
        
        # 旧结构：扫描子目录
        for item in sorted(directory.iterdir()):
            if item.is_dir():
                plugin_info = self._load_plugin_metadata(item, source=source, priority=priority)
                if plugin_info:
                    plugins.append(plugin_info)
                    self.plugins[plugin_info.name] = plugin_info
                    utils.logger.info(f"   ✅ {item.name} (source: {source})", module="plugin_manager")
        
        return plugins

    def _load_plugin_metadata(self, plugin_path: Path, source='builtin', priority=1) -> Optional[PluginInfo]:
        """
        加载插件元数据
        
        Args:
            plugin_path: 插件目录路径
            
        Returns:
            PluginInfo或None
        """
        metadata_file = plugin_path / "plugin.json"
        
        if not metadata_file.exists():
            utils.logger.info(f"⚠️ 插件缺少元数据文件: {plugin_path}", module="plugin_manager")
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证必需字段
            required_fields = ['name', 'version']
            for field in required_fields:
                if field not in data:
                    utils.logger.info(f"⚠️ 插件元数据缺少必需字段 '{field}': {plugin_path}", module="plugin_manager")
                    return None
            
            # 解析节点定义
            nodes = []
            for node_data in data.get('nodes', []):
                if 'class' not in node_data:
                    utils.logger.info(f"⚠️ 节点定义缺少'class'字段", module="plugin_manager")
                    continue
                
                node_def = NodeDefinition(
                    class_name=node_data['class'],
                    display_name=node_data.get('display_name', node_data['class']),
                    category=node_data.get('category', '其他'),
                    icon=node_data.get('icon'),
                    width=node_data.get('width'),
                    height=node_data.get('height'),
                    description=node_data.get('description'),
                    resource_level=node_data.get('resource_level', 'light'),
                    hardware_requirements=node_data.get('hardware_requirements', {}),
                    dependencies=node_data.get('dependencies', []),
                    optional_dependencies=node_data.get('optional_dependencies', {}),
                    color=node_data.get('color', [100, 100, 100]),
                    identifier=node_data.get('__identifier__', data.get('name', ''))
                )
                nodes.append(node_def)
            
            # 创建插件信息对象
            plugin_info = PluginInfo(
                name=data['name'],
                version=data['version'],
                author=data.get('author', ''),
                description=data.get('description', ''),
                path=str(plugin_path),
                source=source,
                priority=priority,
                category_group=data.get('category_group', data['name']),
                nodes=nodes,
                dependencies=data.get('dependencies', []),
                resource_level=data.get('resource_level', 'light'),
                min_app_version=data.get('min_app_version', '1.0.0')
            )
            
            return plugin_info
            
        except Exception as e:
            utils.logger.info(f"❌ 加载插件元数据失败 {plugin_path}: {e}", module="plugin_manager")
            import traceback
            traceback.print_exc()
            return None

    def load_plugin_nodes(self, plugin_name: str, node_graph) -> bool:
        """
        安全地加载插件的节点类并注册到NodeGraph
        
        Args:
            plugin_name: 插件名称
            node_graph: NodeGraph实例
        
        Returns:
            bool: 加载是否成功
        """
        if plugin_name not in self.plugins:
            utils.logger.info(f"❌ 插件不存在: {plugin_name}", module="plugin_manager")
            return False
        
        plugin_info = self.plugins[plugin_name]
        plugin_path = Path(plugin_info.path)
        
        try:
            # 1. 确定插件结构类型（新体系 vs 旧体系）
            nodes_dir = plugin_path / "nodes"
            nodes_file = plugin_path / "nodes.py"
            
            is_new_structure = nodes_dir.exists() and nodes_dir.is_dir()
            is_old_structure = nodes_file.exists()
            
            if not is_new_structure and not is_old_structure:
                utils.logger.info(f"❌ 插件缺少节点文件: {plugin_name}", module="plugin_manager")
                return False
            
            # 2. 读取源代码进行安全检查
            if is_new_structure:
                # 新体系：检查 nodes/__init__.py
                init_file = nodes_dir / "__init__.py"
                if not init_file.exists():
                    utils.logger.info(f"❌ 新体系插件缺少 nodes/__init__.py: {plugin_name}", module="plugin_manager")
                    return False
                
                with open(init_file, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                # 还需要检查所有子模块
                for py_file in nodes_dir.rglob("*.py"):
                    if py_file.name != "__init__.py":
                        with open(py_file, 'r', encoding='utf-8') as f:
                            source_code += "\n" + f.read()
                
                module_path = init_file
                module_name = f"{plugin_name}.nodes"
            else:
                # 旧体系：检查 nodes.py
                with open(nodes_file, 'r', encoding='utf-8') as f:
                    source_code = f.read()
                
                module_path = nodes_file
                module_name = f"plugin_{plugin_name}_nodes"
            
            # 3. 权限检查
            violations = PermissionChecker.check_source_code(source_code, plugin_name)
            if violations:
                utils.logger.info(f"🚫 插件 {plugin_name} 安全检查失败:", module="plugin_manager")
                for v in violations:
                    utils.logger.info(f"   - {v}", module="plugin_manager")
                return False
            
            # 4. 动态导入模块
            # 关键修复：正确设置包层次结构以支持相对导入
            if is_new_structure:
                # 新体系：需要将 src/python 目录添加到 sys.path
                # 这样节点文件中的 "from shared_libs..." 才能正确导入
                src_python_path = plugin_path.parent.parent / "src" / "python"
                
                if str(src_python_path) not in sys.path:
                    sys.path.insert(0, str(src_python_path))
                
                # 使用完整的模块名（包含包路径）
                module_name = f"{plugin_name}.nodes"
            
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            
            spec.loader.exec_module(module)
            
            # 5. 提取节点类并注册
            registered_count = 0
            
            for node_def in plugin_info.nodes:
                class_name = node_def.class_name
                
                # 从模块中获取节点类
                if hasattr(module, class_name):
                    node_class = getattr(module, class_name)
                    
                    # 使用节点定义中的 identifier（用于工作流序列化/反序列化）
                    if node_def.identifier:
                        node_class.__identifier__ = node_def.identifier
                    
                    # 获取插件的 category_group（用于节点库标签名称）
                    category_group = plugin_info.category_group
                    
                    # 注册到NodeGraph
                    node_graph.register_node(node_class)
                    
                    # 应用节点样式配置（如果存在）
                    self._apply_node_style(node_class, node_def)
                    
                    # 记录已加载的节点
                    node_key = f"{plugin_name}.{class_name}"
                    self.loaded_nodes[node_key] = node_class
                    
                    registered_count += 1
                    utils.logger.info(f"   ✅ 注册节点: {node_def.display_name}", module="plugin_manager")
                else:
                    utils.logger.info(f"   ⚠️ 未找到节点类: {class_name}", module="plugin_manager")
            
            utils.logger.info(f"✅ 插件 {plugin_name} 加载完成，注册 {registered_count} 个节点", module="plugin_manager")
            
            # 启动热重载监听
            plugin_path = self.plugins[plugin_name].path
            self.hot_reloader.start_watching(
                plugin_name,
                plugin_path,
                lambda name: self._on_plugin_changed(name)
            )
            
            return True
            
        except SandboxSecurityError as e:
            utils.logger.info(f"🚫 安全违规: {e}", module="plugin_manager")
            return False
        except Exception as e:
            utils.logger.info(f"❌ 加载插件节点失败 {plugin_name}: {e}", module="plugin_manager")
            import traceback
            traceback.print_exc()
            return False

    def _apply_node_style(self, node_class, node_def):
        """
        应用节点样式配置
        
        Args:
            node_class: 节点类
            node_def: 节点定义（NodeDefinition）
        """
        try:
            # 设置节点图标（如果支持）
            if node_def.icon:
                icon = node_def.icon
                # NodeGraphQt 可能不支持直接设置图标，这里预留接口
                # node_class.set_icon(icon)
            
            # 设置节点颜色（如果支持）
            if node_def.color:
                # 预留颜色设置接口
                pass
        except Exception as e:
            utils.logger.info(f"⚠️ 应用节点样式失败: {e}", module="plugin_manager")

    def unload_plugin_nodes(self, plugin_name: str, node_graph=None):
        """
        卸载插件的节点类
        
        Args:
            plugin_name: 插件名称
            node_graph: NodeGraph实例（可选）
        """
        if plugin_name not in self.plugins:
            return
        
        # 停止热重载监听
        self.hot_reloader.stop_watching(plugin_name)
        
        # 从已加载节点字典中移除
        keys_to_remove = []
        for key in self.loaded_nodes:
            if key.startswith(f"{plugin_name}."):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.loaded_nodes[key]
        
        utils.logger.info(f"✅ 插件 {plugin_name} 已卸载", module="plugin_manager")

    def _on_plugin_changed(self, plugin_name: str):
        """
        插件文件变化时的回调
        
        Args:
            plugin_name: 插件名称
        """
        utils.logger.info(f"\n🔄 检测到插件变化: {plugin_name}", module="plugin_manager")
        
        # 卸载旧节点
        self.unload_plugin_nodes(plugin_name)
        
        # 重新扫描元数据
        plugin_info = self.plugins.get(plugin_name)
        if plugin_info:
            plugin_path = Path(plugin_info.path)
            new_info = self._load_plugin_metadata(plugin_path)
            
            if new_info:
                self.plugins[plugin_name] = new_info
                utils.logger.info(f"✅ 插件元数据已更新: {plugin_name}", module="plugin_manager")
        
        # 发布插件重载事件
        if hasattr(self, 'event_bus'):
            from core.event_bus import Events
            self.event_bus.publish(Events.PLUGIN_RELOADED, plugin_name=plugin_name)
        else:
            utils.logger.info(f"💡 提示：请刷新NodeGraph以应用更改", module="plugin_manager")

    def get_plugin_info(self, plugin_name: str) -> Optional[PluginInfo]:
        """
        获取插件信息
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            PluginInfo或None
        """
        return self.plugins.get(plugin_name)

    def get_all_plugins(self) -> List[PluginInfo]:
        """
        获取所有插件信息列表
        
        Returns:
            List[PluginInfo]: 插件信息列表
        """
        return list(self.plugins.values())

    def install_plugin(self, plugin_path: Path) -> bool:
        """
        安装插件
        
        Args:
            plugin_path: 插件包路径（.zip或目录）
            
        Returns:
            bool: 安装是否成功
        """
        return self.installer.install(plugin_path)

    def uninstall_plugin(self, plugin_name: str) -> bool:
        """
        卸载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 卸载是否成功
        """
        return self.installer.uninstall(plugin_name)

    def check_dependencies(self, plugin_name: str) -> List[str]:
        """
        检查插件依赖
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            List[str]: 缺失的依赖列表
        """
        plugin_info = self.plugins.get(plugin_name)
        if not plugin_info:
            return []
        
        return self.dependency_resolver.check_dependencies(plugin_info.dependencies)

    def install_dependencies(self, plugin_name: str) -> bool:
        """
        安装插件依赖
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            bool: 安装是否成功
        """
        plugin_info = self.plugins.get(plugin_name)
        if not plugin_info:
            return False
        
        return self.dependency_resolver.install_dependencies(plugin_info.dependencies)
