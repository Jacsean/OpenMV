"""
插件管理器 - 负责插件的扫描、加载和管理
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional

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
