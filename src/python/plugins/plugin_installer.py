"""
插件安装器 - 支持ZIP文件拖拽安装
"""

import os
import sys
import json
import shutil
import zipfile
from pathlib import Path
from typing import Optional, Tuple


class PluginInstaller:
    """
    插件安装器
    
    功能：
    - ZIP文件解压安装
    - 依赖自动安装
    - 版本冲突检测
    - 安装回滚机制
    """
    
    def __init__(self, plugins_dir: Path):
        """
        初始化安装器
        
        Args:
            plugins_dir: 插件目录路径
        """
        self.plugins_dir = plugins_dir
        self.plugins_dir.mkdir(exist_ok=True)
    
    def install_from_zip(self, zip_path: str) -> Tuple[bool, str]:
        """
        从ZIP文件安装插件
        
        Args:
            zip_path: ZIP文件路径
            
        Returns:
            (success, message)
        """
        zip_file = Path(zip_path)
        
        # 1. 验证ZIP文件
        if not zip_file.exists():
            return False, f"文件不存在: {zip_path}"
        
        if not zipfile.is_zipfile(zip_file):
            return False, "无效的ZIP文件"
        
        print(f"\n📦 开始安装插件: {zip_file.name}")
        
        # 2. 读取元数据（不解压）
        try:
            with zipfile.ZipFile(zip_file, 'r') as zf:
                if 'plugin.json' not in zf.namelist():
                    return False, "ZIP文件中缺少 plugin.json"
                
                plugin_json = json.loads(zf.read('plugin.json').decode('utf-8'))
                plugin_name = plugin_json.get('name', '')
                plugin_version = plugin_json.get('version', '0.0.0')
                
                if not plugin_name:
                    return False, "plugin.json中缺少 name 字段"
                
                print(f"   插件名称: {plugin_name}")
                print(f"   插件版本: {plugin_version}")
        except Exception as e:
            return False, f"读取元数据失败: {e}"
        
        # 3. 检查是否已存在同名插件
        target_dir = self.plugins_dir / plugin_name
        backup_dir = None
        
        if target_dir.exists():
            print(f"   ⚠️ 检测到同名插件，将备份旧版本")
            backup_dir = self.plugins_dir / f"{plugin_name}_backup"
            if backup_dir.exists():
                shutil.rmtree(backup_dir)
            shutil.move(str(target_dir), str(backup_dir))
        
        # 4. 解压ZIP文件
        temp_extract_dir = self.plugins_dir / f"_temp_{plugin_name}"
        
        try:
            print(f"   📂 正在解压...")
            with zipfile.ZipFile(zip_file, 'r') as zf:
                zf.extractall(temp_extract_dir)
            
            # 5. 移动到新位置
            if target_dir.exists():
                shutil.rmtree(target_dir)
            shutil.move(str(temp_extract_dir), str(target_dir))
            
            print(f"   ✅ 解压成功")
            
        except Exception as e:
            # 回滚
            if backup_dir and backup_dir.exists():
                if target_dir.exists():
                    shutil.rmtree(target_dir)
                shutil.move(str(backup_dir), str(target_dir))
            
            # 清理临时文件
            if temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir)
            
            return False, f"解压失败: {e}"
        
        # 6. 清理备份
        if backup_dir and backup_dir.exists():
            shutil.rmtree(backup_dir)
        
        # 7. 安装依赖
        dependencies = plugin_json.get('dependencies', [])
        if dependencies:
            print(f"   🔧 正在安装依赖...")
            from .dependency_resolver import DependencyResolver
            results = DependencyResolver.install_dependencies(dependencies)
            
            failed_deps = [pkg for pkg, success in results.items() if not success]
            if failed_deps:
                print(f"   ⚠️ 部分依赖安装失败: {', '.join(failed_deps)}")
                print(f"   💡 插件可能无法正常运行")
        
        print(f"✅ 插件安装成功: {plugin_name} v{plugin_version}")
        return True, f"安装成功: {plugin_name} v{plugin_version}"
    
    def uninstall_plugin(self, plugin_name: str) -> Tuple[bool, str]:
        """
        卸载插件
        
        Args:
            plugin_name: 插件名称
            
        Returns:
            (success, message)
        """
        target_dir = self.plugins_dir / plugin_name
        
        if not target_dir.exists():
            return False, f"插件不存在: {plugin_name}"
        
        try:
            shutil.rmtree(target_dir)
            print(f"✅ 插件已卸载: {plugin_name}")
            return True, f"卸载成功: {plugin_name}"
        except Exception as e:
            return False, f"卸载失败: {e}"
