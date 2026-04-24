"""
插件管理器 - 负责插件的扫描、加载和管理
"""

import os
import sys
import json
import importlib.util
from pathlib import Path
from typing import Dict, List, Optional, Type

from .models import PluginInfo, NodeDefinition


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
                    icon=node_data.get('icon')
                )
                nodes.append(node_def)
            
            plugin_info = PluginInfo(
                name=data['name'],
                version=data.get('version', '1.0.0'),
                author=data.get('author', 'Unknown'),
                description=data.get('description', ''),
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
        加载插件的节点类并注册到NodeGraph
        
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
            # 1. 加载 nodes.py 模块
            nodes_file = plugin_path / "nodes.py"
            if not nodes_file.exists():
                print(f"❌ 插件缺少 nodes.py: {plugin_name}")
                return False
            
            # 动态导入模块
            module_name = f"plugin_{plugin_name}_nodes"
            spec = importlib.util.spec_from_file_location(module_name, nodes_file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            print(f"✅ 模块加载成功: {plugin_name}")
            
            # 2. 提取节点类并注册
            registered_count = 0
            for node_def in plugin_info.nodes:
                class_name = node_def.class_name
                
                # 从模块中获取节点类
                if hasattr(module, class_name):
                    node_class = getattr(module, class_name)
                    
                    # 注册到NodeGraph
                    node_graph.register_node(node_class)
                    
                    # 记录已加载的节点
                    node_key = f"{plugin_name}.{class_name}"
                    self.loaded_nodes[node_key] = node_class
                    
                    registered_count += 1
                    print(f"   ✅ 注册节点: {node_def.display_name}")
                else:
                    print(f"   ⚠️ 未找到节点类: {class_name}")
            
            print(f"✅ 插件 {plugin_name} 加载完成，注册 {registered_count} 个节点")
            return True
            
        except Exception as e:
            print(f"❌ 加载插件节点失败 {plugin_name}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def unload_plugin_nodes(self, plugin_name: str) -> bool:
        """
        卸载插件节点
        
        Args:
            plugin_name: 插件名称
        
        Returns:
            bool: 卸载是否成功
        """
        if plugin_name not in self.plugins:
            return False
        
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
