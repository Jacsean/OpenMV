"""
配置管理模块

提供统一的配置管理框架：
- 配置分类（系统/项目/插件）
- 配置验证和默认值
- 配置热重载
- 配置变更通知
- 持久化存储

使用示例：
    from core.config_manager import config_manager, ConfigCategory

    # 获取配置
    recent_projects = config_manager.get('system.recent_projects', [])

    # 设置配置
    config_manager.set('system.recent_projects', ['project1', 'project2'])

    # 订阅配置变更
    config_manager.subscribe('system.recent_projects', lambda key, value: logger.info(f"配置变更: {value}", module="config"))

    # 热重载
    config_manager.reload()
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import threading

from utils.logger import logger


class ConfigCategory(Enum):
    """配置分类枚举"""
    SYSTEM = "system"       # 系统配置
    PROJECT = "project"     # 项目配置
    PLUGIN = "plugin"       # 插件配置
    USER = "user"          # 用户配置


@dataclass
class ConfigSchema:
    """
    配置Schema定义

    提供配置的类型验证和默认值支持
    """
    name: str
    default: Any
    type: type = str
    description: str = ""
    validator: Optional[Callable[[Any], bool]] = None
    options: Optional[List[Any]] = None  # 可选值列表


class ConfigChangeEvent:
    """配置变更事件"""

    def __init__(self, key: str, old_value: Any, new_value: Any):
        self.key = key
        self.old_value = old_value
        self.new_value = new_value


class ConfigManager:
    """
    配置管理器（单例）

    特性：
    - 线程安全
    - 配置热重载
    - 配置变更通知
    - Schema 验证
    - 多存储后端支持
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True

        # 配置存储
        self._configs: Dict[str, Any] = {}

        # 配置Schema
        self._schemas: Dict[str, ConfigSchema] = {}

        # 变更监听器
        self._listeners: Dict[str, List[Callable[[str, Any], None]]] = {}

        # 存储路径
        self._config_dir = Path(__file__).parent.parent / "workspace" / "config"
        self._config_dir.mkdir(parents=True, exist_ok=True)

        # 存储后端
        self._json_storage = self._config_dir / "config.json"

        # 初始化
        self._load_configs()
        self._register_default_schemas()
        self._setup_system_config()

    def _setup_system_config(self):
        """设置系统级配置项"""
        # 确保最近项目列表存在
        if 'system.recent_projects' not in self._configs:
            self._configs['system.recent_projects'] = []

        # 确保窗口状态配置存在
        if 'system.window_state' not in self._configs:
            self._configs['system.window_state'] = {
                'geometry': None,
                'state': None,
                'maximized': False
            }

        # 确保插件配置存在
        if 'plugin.enabled_list' not in self._configs:
            self._configs['plugin.enabled_list'] = []

        # 确保标签页顺序配置存在
        if 'system.tab_order' not in self._configs:
            self._configs['system.tab_order'] = []

    def _register_default_schemas(self):
        """注册默认配置Schema"""
        schemas = [
            ConfigSchema(
                name='system.recent_projects',
                default=[],
                type=list,
                description='最近打开的项目列表'
            ),
            ConfigSchema(
                name='system.tab_order',
                default=[],
                type=list,
                description='标签页排序'
            ),
            ConfigSchema(
                name='system.window_state',
                default={'geometry': None, 'state': None, 'maximized': False},
                type=dict,
                description='窗口状态'
            ),
            ConfigSchema(
                name='plugin.enabled_list',
                default=[],
                type=list,
                description='已启用的插件列表'
            ),
            ConfigSchema(
                name='user.language',
                default='zh_CN',
                type=str,
                description='界面语言',
                options=['zh_CN', 'en_US']
            ),
            ConfigSchema(
                name='user.theme',
                default='dark',
                type=str,
                description='界面主题',
                options=['dark', 'light']
            ),
            ConfigSchema(
                name='system.auto_save',
                default=True,
                type=bool,
                description='自动保存'
            ),
            ConfigSchema(
                name='system.auto_save_interval',
                default=300,
                type=int,
                description='自动保存间隔（秒）',
                validator=lambda v: 60 <= v <= 3600
            ),
        ]

        for schema in schemas:
            self._schemas[schema.name] = schema

    def _load_configs(self):
        """从JSON文件加载配置"""
        if not self._json_storage.exists():
            return

        try:
            with open(self._json_storage, 'r', encoding='utf-8') as f:
                loaded = json.load(f)
                self._configs.update(loaded)
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}", module="config")

    def _save_configs(self):
        """保存配置到JSON文件"""
        try:
            with open(self._json_storage, 'w', encoding='utf-8') as f:
                json.dump(self._configs, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存配置文件失败: {e}", module="config")

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键（格式：category.key，如 system.recent_projects）
            default: 默认值

        Returns:
            配置值，如果不存在返回默认值
        """
        # 兼容不带前缀的key
        full_key = key if key.startswith(('system.', 'project.', 'plugin.', 'user.')) else f'system.{key}'

        if full_key in self._configs:
            return self._configs[full_key]

        # 检查schema中的默认值
        if key in self._schemas:
            return self._schemas[key].default

        return default

    def set(self, key: str, value: Any, save: bool = True):
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
            save: 是否立即保存到磁盘
        """
        # 兼容不带前缀的key
        full_key = key if key.startswith(('system.', 'project.', 'plugin.', 'user.')) else f'system.{key}'

        # 验证配置
        if full_key in self._schemas:
            schema = self._schemas[full_key]
            value = self._validate_value(full_key, value, schema)

        old_value = self._configs.get(full_key)
        self._configs[full_key] = value

        # 通知变更
        if old_value != value:
            self._notify_listeners(full_key, old_value, value)

        # 保存到磁盘
        if save:
            self._save_configs()

    def _validate_value(self, key: str, value: Any, schema: ConfigSchema) -> Any:
        """
        验证配置值

        Args:
            key: 配置键
            value: 配置值
            schema: 配置Schema

        Returns:
            验证通过的值，如果验证失败返回默认值
        """
        # 类型检查
        if not isinstance(value, schema.type):
            logger.warning(f"配置 {key} 类型错误，期望 {schema.type.__name__}，实际 {type(value).__name__}，使用默认值", module="config")
            return schema.default

        # 选项验证
        if schema.options and value not in schema.options:
            logger.warning(f"配置 {key} 值不在选项范围内，使用默认值", module="config")
            return schema.default

        # 自定义验证
        if schema.validator and not schema.validator(value):
            logger.warning(f"配置 {key} 验证失败，使用默认值", module="config")
            return schema.default

        return value

    def subscribe(self, key: str, callback: Callable[[str, Any], None]):
        """
        订阅配置变更

        Args:
            key: 配置键
            callback: 回调函数，签名：callback(key, new_value)
        """
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)

    def unsubscribe(self, key: str, callback: Callable[[str, Any], None]):
        """
        取消订阅配置变更

        Args:
            key: 配置键
            callback: 回调函数
        """
        if key in self._listeners:
            self._listeners[key].remove(callback)

    def _notify_listeners(self, key: str, old_value: Any, new_value: Any):
        """
        通知所有监听器配置变更

        Args:
            key: 配置键
            old_value: 旧值
            new_value: 新值
        """
        if key in self._listeners:
            for callback in self._listeners[key]:
                try:
                    callback(key, new_value)
                except Exception as e:
                    logger.error(f"配置变更通知失败: {e}", module="config")

    def reload(self):
        """重新加载配置（热重载）"""
        self._configs.clear()
        self._load_configs()
        self._setup_system_config()
        logger.info("配置已热重载", module="config")

    def get_category(self, category: ConfigCategory) -> Dict[str, Any]:
        """
        获取指定分类的所有配置

        Args:
            category: 配置分类

        Returns:
            该分类的所有配置
        """
        prefix = f"{category.value}."
        return {
            k.replace(prefix, ''): v
            for k, v in self._configs.items()
            if k.startswith(prefix)
        }

    def set_category(self, category: ConfigCategory, configs: Dict[str, Any], save: bool = True):
        """
        批量设置分类配置

        Args:
            category: 配置分类
            configs: 配置字典
            save: 是否立即保存
        """
        prefix = f"{category.value}."
        for key, value in configs.items():
            full_key = prefix + key
            self.set(full_key, value, save=False)

        if save:
            self._save_configs()

    def reset(self, key: Optional[str] = None):
        """
        重置配置到默认值

        Args:
            key: 配置键，None则重置所有
        """
        if key:
            if key in self._schemas:
                self.set(key, self._schemas[key].default)
        else:
            # 重置所有
            for schema_key, schema in self._schemas.items():
                self._configs[schema_key] = schema.default
            self._save_configs()

    def register_schema(self, schema: ConfigSchema):
        """
        注册新的配置Schema

        Args:
            schema: 配置Schema
        """
        self._schemas[schema.name] = schema

    def get_schema(self, key: str) -> Optional[ConfigSchema]:
        """
        获取配置Schema

        Args:
            key: 配置键

        Returns:
            配置Schema，如果不存在返回None
        """
        return self._schemas.get(key)

    def export_config(self, path: Optional[Path] = None) -> str:
        """
        导出配置到文件

        Args:
            path: 导出路径，None则返回JSON字符串

        Returns:
            导出的JSON字符串
        """
        json_str = json.dumps(self._configs, indent=4, ensure_ascii=False)

        if path:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(json_str)

        return json_str

    def import_config(self, data: str):
        """
        从JSON导入配置

        Args:
            data: JSON字符串
        """
        try:
            imported = json.loads(data)
            self._configs.update(imported)
            self._save_configs()
            logger.info("配置导入成功", module="config")
        except Exception as e:
            logger.error(f"配置导入失败: {e}", module="config")

    # === 便捷方法 ===

    def add_recent_project(self, project_path: str, max_count: int = 10):
        """
        添加最近项目

        Args:
            project_path: 项目路径
            max_count: 最大保存数量
        """
        recent = self.get('system.recent_projects', [])

        # 移除已存在的
        if project_path in recent:
            recent.remove(project_path)

        # 添加到最前面
        recent.insert(0, project_path)

        # 限制数量
        if len(recent) > max_count:
            recent = recent[:max_count]

        self.set('system.recent_projects', recent)

    def remove_recent_project(self, project_path: str):
        """
        移除最近项目

        Args:
            project_path: 项目路径
        """
        recent = self.get('system.recent_projects', [])
        if project_path in recent:
            recent.remove(project_path)
            self.set('system.recent_projects', recent)

    def clear_recent_projects(self):
        """清空最近项目"""
        self.set('system.recent_projects', [])

    def set_tab_order(self, tab_order: List[str]):
        """
        设置标签页顺序

        Args:
            tab_order: 标签页顺序列表
        """
        self.set('system.tab_order', tab_order)

    def get_tab_order(self) -> List[str]:
        """
        获取标签页顺序

        Returns:
            标签页顺序列表
        """
        return self.get('system.tab_order', [])

    def enable_plugin(self, plugin_name: str):
        """
        启用插件

        Args:
            plugin_name: 插件名称
        """
        enabled_list = self.get('plugin.enabled_list', [])
        if plugin_name not in enabled_list:
            enabled_list.append(plugin_name)
            self.set('plugin.enabled_list', enabled_list)

    def disable_plugin(self, plugin_name: str):
        """
        禁用插件

        Args:
            plugin_name: 插件名称
        """
        enabled_list = self.get('plugin.enabled_list', [])
        if plugin_name in enabled_list:
            enabled_list.remove(plugin_name)
            self.set('plugin.enabled_list', enabled_list)

    def is_plugin_enabled(self, plugin_name: str) -> bool:
        """
        检查插件是否启用

        Args:
            plugin_name: 插件名称

        Returns:
            是否启用
        """
        return plugin_name in self.get('plugin.enabled_list', [])


# 创建全局单例
config_manager = ConfigManager()

__all__ = [
    'ConfigManager',
    'ConfigCategory',
    'ConfigSchema',
    'ConfigChangeEvent',
    'config_manager'
]
