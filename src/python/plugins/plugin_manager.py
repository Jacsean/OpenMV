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
        self.plugins_dir = Path(__file__).parent.parent / "user_plugins"
        self.plugins_dir.mkdir(exist_ok=True)
        
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
        
        if not self.plugins_dir.exists():
            return plugins
        
        for item in self.plugins_dir.iterdir():
            if item.is_dir():
                plugin_info = self._load_plugin_metadata(item)
                if plugin_info:
                    plugins.append(plugin_info)
                    self.plugins[plugin_info.name] = plugin_info
        
        return plugins
    
    def _load_plugin_metadata(self, plugin_path: Path) -> Optional[PluginInfo]:
        """
        加载插件元数据
        
        Args:
            plugin_path: 插件目录路径
            
        Returns:
            PluginInfo或None
        """
        metadata_file = plugin_path / "plugin.json"
        
        if not metadata_file.exists():
            print(f"⚠️ 插件缺少元数据文件: {plugin_path}")
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 验证必需字段
            required_fields = ['name', 'version']
            for field in required_fields:
                if field not in data:
                    print(f"⚠️ 插件元数据缺少必需字段 '{field}': {plugin_path}")
                    return None
            
            # 解析节点定义
            nodes = []
            for node_data in data.get('nodes', []):
                if 'class' not in node_data:
                    print(f"⚠️ 节点定义缺少'class'字段")
                    continue
                
                node_def = NodeDefinition(
                    class_name=node_data['class'],
                    display_name=node_data.get('display_name', node_data['class']),
                    category=node_data.get('category', '其他'),
                    icon=node_data.get('icon'),
                    width=node_data.get('width'),
                    height=node_data.get('height'),
                    description=node_data.get('description', ''),
                    color=node_data.get('color')
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
                path=str(plugin_path)
            )
            
            return plugin_info
            
        except json.JSONDecodeError as e:
            print(f"❌ 插件元数据JSON格式错误 {plugin_path}: {e}")
            return None
        except Exception as e:
            print(f"❌ 加载插件元数据失败 {plugin_path}: {e}")
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
            print(f"❌ 插件不存在: {plugin_name}")
            return False
        
        plugin_info = self.plugins[plugin_name]
        plugin_path = Path(plugin_info.path)
        
        try:
            # 1. 读取源代码进行安全检查
            nodes_file = plugin_path / "nodes.py"
            if not nodes_file.exists():
                print(f"❌ 插件缺少 nodes.py: {plugin_name}")
                return False
            
            with open(nodes_file, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # 2. 权限检查
            violations = PermissionChecker.check_source_code(source_code)
            if violations:
                print(f"🚫 插件 {plugin_name} 安全检查失败:")
                for v in violations:
                    print(f"   - {v}")
                return False
            
            print(f"✅ 安全检查通过: {plugin_name}")
            
            # 3. 动态导入模块
            module_name = f"plugin_{plugin_name}_nodes"
            spec = importlib.util.spec_from_file_location(module_name, nodes_file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            print(f"✅ 模块加载成功: {plugin_name}")
            
            # 4. 提取节点类并注册
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
                    print(f"   ✅ 注册节点: {node_def.display_name}")
                else:
                    print(f"   ⚠️ 未找到节点类: {class_name}")
            
            print(f"✅ 插件 {plugin_name} 加载完成，注册 {registered_count} 个节点")
            
            # 启动热重载监听
            plugin_path = self.plugins[plugin_name].path
            self.hot_reloader.start_watching(
                plugin_name,
                plugin_path,
                lambda name: self._on_plugin_changed(name)
            )
            
            return True
            
        except SandboxSecurityError as e:
            print(f"🚫 安全违规: {e}")
            return False
        except Exception as e:
            print(f"❌ 加载插件节点失败 {plugin_name}: {e}")
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
                print(f"   📌 节点图标: {icon}")
            
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
                print(f"   📐 节点尺寸: {width}x{height}")
            
            # 存储描述信息用于说明面板
            if node_def.description:
                description = node_def.description
                if not hasattr(node_class, '_node_description'):
                    node_class._node_description = description
                print(f"   📝 节点描述已加载 ({len(description)} 字符)")
                
            # 设置节点颜色（如果支持）
            if node_def.color:
                color = node_def.color
                print(f"   🎨 节点颜色: RGB{tuple(color)}")
                
        except Exception as e:
            print(f"   ⚠️ 应用节点样式失败: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_plugin_changed(self, plugin_name: str):
        """
        插件文件变化回调（由热重载器触发）
        
        Args:
            plugin_name: 插件名称
        """
        print(f"\n🔄 开始重载插件: {plugin_name}")
        
        # 1. 卸载旧节点
        self.unload_plugin_nodes(plugin_name)
        
        # 2. 重新扫描元数据
        plugin_path = Path(self.plugins[plugin_name].path)
        new_info = self._load_plugin_metadata(plugin_path)
        
        if new_info:
            self.plugins[plugin_name] = new_info
        
        # 3. 重新加载节点（需要外部传入node_graph，这里仅更新元数据）
        print(f"✅ 插件 {plugin_name} 元数据已更新")
        print(f"💡 提示：请刷新NodeGraph以应用更改")
    
    def unload_plugin_nodes(self, plugin_name: str, node_graph=None) -> bool:
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
                        print(f"   🗑️ 从Graph移除节点: {node_def.display_name}")
                    except Exception as e:
                        print(f"   ⚠️ 移除节点失败: {e}")
        
        # 移除已注册的节点
        nodes_to_remove = [
            key for key in self.loaded_nodes.keys()
            if key.startswith(f"{plugin_name}.")
        ]
        
        for node_key in nodes_to_remove:
            del self.loaded_nodes[node_key]
            print(f"   🗑️ 卸载节点: {node_key}")
        
        # 清除模块缓存
        module_name = f"plugin_{plugin_name}_nodes"
        if module_name in sys.modules:
            del sys.modules[module_name]
        
        print(f"✅ 插件 {plugin_name} 已卸载")
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
