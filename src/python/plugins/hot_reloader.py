"""
插件热重载器 - 监听插件文件变化并自动重新加载
"""

import os
import sys
import time
from pathlib import Path
from typing import Dict, Callable, Optional


class HotReloader:
    """
    插件热重载器
    
    功能：
    - 监听插件目录文件变化
    - 防抖机制避免频繁重载
    - 自动触发重新加载回调
    """
    
    def __init__(self, check_interval: float = 1.0, debounce_time: float = 0.5):
        """
        初始化热重载器
        
        Args:
            check_interval: 检查间隔（秒）
            debounce_time: 防抖时间（秒）
        """
        self.check_interval = check_interval
        self.debounce_time = debounce_time
        self.watchers: Dict[str, Dict] = {}  # plugin_name -> watcher info
        self._running = False
        self._thread = None
    
    def start_watching(self, plugin_name: str, plugin_path: str, 
                      on_reload: Callable[[str], None]):
        """
        开始监听指定插件的文件变化
        
        Args:
            plugin_name: 插件名称
            plugin_path: 插件路径
            on_reload: 重载回调函数，接收插件名称作为参数
        """
        if plugin_name in self.watchers:
            print(f"⚠️ 插件 {plugin_name} 已在监听中")
            return
        
        watcher_info = {
            'path': plugin_path,
            'on_reload': on_reload,
            'last_modified': self._get_latest_mtime(Path(plugin_path)),
            'last_trigger': 0,
        }
        
        self.watchers[plugin_name] = watcher_info
        print(f"✅ 开始监听插件: {plugin_name}")
        
        # 启动监听线程（如果尚未启动）
        if not self._running:
            self._start_listener_thread()
    
    def stop_watching(self, plugin_name: str):
        """
        停止监听指定插件
        
        Args:
            plugin_name: 插件名称
        """
        if plugin_name in self.watchers:
            del self.watchers[plugin_name]
            print(f"🛑 停止监听插件: {plugin_name}")
    
    def stop_all(self):
        """停止所有监听"""
        self._running = False
        self.watchers.clear()
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2)
        print("🛑 停止所有插件监听")
    
    def _start_listener_thread(self):
        """启动监听线程"""
        import threading
        
        self._running = True
        self._thread = threading.Thread(target=self._listener_loop, daemon=True)
        self._thread.start()
        print("✅ 热重载监听线程已启动")
    
    def _listener_loop(self):
        """监听循环（在后台线程中运行）"""
        while self._running:
            try:
                self._check_for_changes()
            except Exception as e:
                print(f"⚠️ 监听错误: {e}")
            
            time.sleep(self.check_interval)
    
    def _check_for_changes(self):
        """检查所有被监听的插件是否有文件变化"""
        current_time = time.time()
        
        for plugin_name, watcher in list(self.watchers.items()):
            try:
                plugin_path = Path(watcher['path'])
                if not plugin_path.exists():
                    continue
                
                # 获取最新修改时间
                latest_mtime = self._get_latest_mtime(plugin_path)
                
                # 检测变化
                if latest_mtime > watcher['last_modified']:
                    # 防抖检查
                    if current_time - watcher['last_trigger'] >= self.debounce_time:
                        print(f"\n🔄 检测到插件变化: {plugin_name}")
                        
                        # 触发重载回调
                        try:
                            watcher['on_reload'](plugin_name)
                            watcher['last_modified'] = latest_mtime
                            watcher['last_trigger'] = current_time
                        except Exception as e:
                            print(f"❌ 重载失败: {e}")
                
            except Exception as e:
                print(f"⚠️ 检查插件 {plugin_name} 时出错: {e}")
    
    @staticmethod
    def _get_latest_mtime(directory: Path) -> float:
        """
        获取目录下所有文件的最新修改时间
        
        Args:
            directory: 目录路径
            
        Returns:
            最新修改时间戳
        """
        latest = 0.0
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                try:
                    mtime = file_path.stat().st_mtime
                    if mtime > latest:
                        latest = mtime
                except (OSError, FileNotFoundError):
                    pass
        return latest
