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
                    description=node_data.get('description', ''),
                    color=node_data.get('color'),
                    # AI 节点扩展字段
                    resource_level=node_data.get('resource_level', 'light'),
                    hardware_requirements=node_data.get('hardware_requirements', {
                        'cpu_cores': 2,
                        'memory_gb': 2,
                        'gpu_required': False,
                        'gpu_memory_gb': 0
                    }),
                    dependencies=node_data.get('dependencies', []),
                    optional_dependencies=node_data.get('optional_dependencies', {})
                )
                nodes.append(node_def)
            
            plugin_info = PluginInfo(
                name=data['name'],
                version=data.get('version', '1.0.0'),
                author=data.get('author', 'Unknown'),
                description=data.get('description', ''),
                category_group=data.get('category_group', data['name']),  # 使用category_group，如果没有则使用name
                nodes=nodes,
                dependencies=data.get('dependencies', []),
                min_app_version=data.get('min_app_version', '3.1.0'),
                path=str(plugin_path),
                source=data.get('source', source),  # 从plugin.json读取或使用默认值
                priority=priority,  # 加载优先级
                # AI 插件扩展字段
                resource_level=data.get('resource_level', 'light'),
                installation_guide=data.get('installation_guide', {}),
                hardware_recommendations=data.get('hardware_recommendations', {})
            )
            
            return plugin_info
            
        except json.JSONDecodeError as e:
            utils.logger.info(f"❌ 插件元数据JSON格式错误 {plugin_path}: {e}", module="plugin_manager")
            return None
        except Exception as e:
            utils.logger.info(f"❌ 加载插件元数据失败 {plugin_path}: {e}", module="plugin_manager")
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
                # 新体系：需要将 user_plugins 作为包根
                user_plugins_path = plugin_path.parent
                
                # 确保 user_plugins 在 sys.path 中
                if str(user_plugins_path) not in sys.path:
                    sys.path.insert(0, str(user_plugins_path))
                
                # 使用完整的模块名（包含包路径）
                module_name = f"user_plugins.{plugin_name}.nodes"
            
            spec = importlib.util.spec_from_file_location(module_name, module_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            
            # 如果是新体系，还需要注册父包到 sys.modules
            if is_new_structure:
                # 确定插件所在的根目录（plugin_packages）
                plugin_packages_path = plugin_path.parent.parent  # plugin_packages
                
                # 确保 plugin_packages 在 sys.path 中
                if str(plugin_packages_path) not in sys.path:
                    sys.path.insert(0, str(plugin_packages_path))
                
                # 确定模块名前缀（builtin 或 marketplace.installed）
                relative_path = plugin_path.relative_to(plugin_packages_path)
                package_prefix = str(relative_path.parent).replace(os.sep, '.')
                
                # 使用完整的模块名（包含包路径）
                module_name = f"{package_prefix}.{plugin_name}.nodes"
                
                # 注册 plugin_packages 包
                if 'plugin_packages' not in sys.modules:
                    plugin_packages_spec = importlib.util.spec_from_file_location(
                        'plugin_packages',
                        plugin_packages_path / '__init__.py' if (plugin_packages_path / '__init__.py').exists() else None
                    )
                    if plugin_packages_spec:
                        plugin_packages_module = importlib.util.module_from_spec(plugin_packages_spec)
                        sys.modules['plugin_packages'] = plugin_packages_module
                
                # 注册子包（builtin 或 marketplace）
                if package_prefix not in sys.modules:
                    sub_package_path = plugin_packages_path / relative_path.parent
                    sub_package_spec = importlib.util.spec_from_file_location(
                        package_prefix,
                        sub_package_path / '__init__.py' if (sub_package_path / '__init__.py').exists() else None
                    )
                    if sub_package_spec:
                        sub_package_module = importlib.util.module_from_spec(sub_package_spec)
                        sys.modules[package_prefix] = sub_package_module
                
                # 注册插件包
                plugin_package_name = f"{package_prefix}.{plugin_name}"
                if plugin_package_name not in sys.modules:
                    plugin_package_spec = importlib.util.spec_from_file_location(
                        plugin_package_name,
                        plugin_path / '__init__.py'
                    )
                    plugin_package_module = importlib.util.module_from_spec(plugin_package_spec)
                    sys.modules[plugin_package_name] = plugin_package_module
            
            spec.loader.exec_module(module)
            
            # 5. 提取节点类并注册
            registered_count = 0
            for node_def in plugin_info.nodes:
                class_name = node_def.class_name
                
                # 从模块中获取节点类
                if hasattr(module, class_name):
                    node_class = getattr(module, class_name)
                    
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
            
            # 设置节点尺寸（如果支持）
            if node_def.width is not None or node_def.height is not None:
                width = node_def.width
                height = node_def.height
                # NodeGraphQt 的节点尺寸通常在创建实例时设置
                # 这里可以存储配置供后续使用
                if hasattr(node_class, '_style_config'):
                    node_class._style_config['width'] = width
                    node_class._style_config['height'] = height
                else:
                    node_class._style_config = {'width': width, 'height': height}
            
            # 存储描述信息用于说明面板
            if node_def.description:
                description = node_def.description
                if not hasattr(node_class, '_node_description'):
                    node_class._node_description = description
                
            # 设置节点颜色（如果支持）
            if node_def.color:
                color = node_def.color
                
        except Exception as e:
            utils.logger.info(f"   ⚠️ 应用节点样式失败: {e}", module="plugin_manager")
            import traceback
            traceback.print_exc()
    
    def _on_plugin_changed(self, plugin_name: str):
        """
        插件文件变化回调（由热重载器触发）
        
        Args:
            plugin_name: 插件名称
        """
        utils.logger.info(f"\n🔄 开始重载插件: {plugin_name}", module="plugin_manager")
        
        # 1. 卸载旧节点
        self.unload_plugin_nodes(plugin_name)
        
        # 2. 重新扫描元数据
        plugin_path = Path(self.plugins[plugin_name].path)
        new_info = self._load_plugin_metadata(plugin_path)
        
        if new_info:
            self.plugins[plugin_name] = new_info
        
        # 3. 触发热重载事件，通知所有工作流刷新节点
        try:
            from core.event_bus import event_bus, Events
            event_bus.publish(Events.PLUGIN_RELOADED, plugin_name=plugin_name)
            utils.logger.success(f"✅ 插件 {plugin_name} 已重载，已通知所有工作流", module="plugin_manager")
        except Exception as e:
            utils.logger.warning(f"⚠️ 触发热重载事件失败: {e}", module="plugin_manager")
            utils.logger.info(f"💡 提示：请手动刷新NodeGraph以应用更改", module="plugin_manager")
    
    def unload_plugin_nodes(self, plugin_name: str) -> bool:
        """
        卸载插件节点
        
        Args:
            plugin_name: 插件名称
            node_graph: NodeGraph实例（可选），如果提供则从Graph中注销节点
        
        Returns:
            bool: 卸载是否成功
        """
        if plugin_name not in self.plugins:
            return False
        
        # 停止热重载监听
        self.hot_reloader.stop_watching(plugin_name)
        
        # 从NodeGraph中注销节点（如果提供了node_graph）
        if node_graph:
            plugin_info = self.plugins[plugin_name]
            for node_def in plugin_info.nodes:
                class_name = node_def.class_name
                node_key = f"{plugin_name}.{class_name}"
                
                if node_key in self.loaded_nodes:
                    node_class = self.loaded_nodes[node_key]
                    try:
                        # NodeGraphQt没有直接的unregister_node方法
                        # 只能通过重新创建NodesPalette来刷新
                        utils.logger.info(f"   🗑️ 从Graph移除节点: {node_def.display_name}", module="plugin_manager")
                    except Exception as e:
                        utils.logger.info(f"   ⚠️ 移除节点失败: {e}", module="plugin_manager")
        
        # 移除已注册的节点
        nodes_to_remove = [
            key for key in self.loaded_nodes.keys()
            if key.startswith(f"{plugin_name}.")
        ]
        
        for node_key in nodes_to_remove:
            del self.loaded_nodes[node_key]
            utils.logger.info(f"   🗑️ 卸载节点: {node_key}", module="plugin_manager")
        
        # 清除模块缓存
        module_name = f"plugin_{plugin_name}_nodes"
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        utils.logger.info(f"✅ 插件 {plugin_name} 已卸载", module="plugin_manager")
        return True
    
    def get_installed_plugins(self) -> List[PluginInfo]:
        """
        获取已安装的插件列表
        
        Returns:
            List[PluginInfo]: 插件信息列表
        """
        return list(self.plugins.values())
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginInfo]:
        """
        获取指定插件信息
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            PluginInfo或None
        """
        return self.plugins.get(plugin_name)
    
    def install_plugin_from_zip(self, zip_path: str) -> Tuple[bool, str]:
        """
        从ZIP文件安装插件
        
        Args:
            zip_path: ZIP文件路径
            
        Returns:
            (success, message)
        """
        success, message = self.installer.install_from_zip(zip_path)
        
        if success:
            # 重新扫描以加载新插件
            self.scan_plugins()
        
        return success, message
    
    def get_loaded_plugins(self) -> List[PluginInfo]:
        """
        获取已加载的插件列表
        
        Returns:
            已加载的插件信息列表
        """
        loaded = []
        for plugin_name, plugin_info in self.plugins.items():
            # 检查是否有节点被加载
            has_loaded_nodes = any(
                key.startswith(f"{plugin_name}.")
                for key in self.loaded_nodes.keys()
            )
            if has_loaded_nodes:
                loaded.append(plugin_info)
        
        return loaded

    def uninstall_plugin(self, plugin_name: str) -> Tuple[bool, str]:
        """
        卸载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            (success, message)
        """
        if plugin_name not in self.plugins:
            return False, f"插件不存在: {plugin_name}"
        
        plugin_info = self.plugins[plugin_name]
        
        # builtin中的插件不可卸载
        if hasattr(plugin_info, 'source') and plugin_info.source == 'builtin':
            return False, "内置插件不可卸载"
        
        # marketplace中的插件可卸载
        if hasattr(plugin_info, 'source') and plugin_info.source == 'marketplace':
            # 先卸载节点
            if plugin_name in self.loaded_nodes:
                self.unload_plugin_nodes(plugin_name)
            
            # 再卸载文件
            success, message = self.installer.uninstall_plugin(plugin_name)
            
            if success:
                # 从注册表中移除
                if plugin_name in self.plugins:
                    del self.plugins[plugin_name]
            
            return success, message
        
        # 兼容旧版本（没有source字段）
        # 先卸载节点
        if plugin_name in self.loaded_nodes:
            self.unload_plugin_nodes(plugin_name)
        
        # 再卸载文件
        success, message = self.installer.uninstall_plugin(plugin_name)
        
        if success:
            # 从注册表中移除
            if plugin_name in self.plugins:
                del self.plugins[plugin_name]
        
        return success, message
