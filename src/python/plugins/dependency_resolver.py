"""
插件依赖解析器 - 自动管理插件依赖
"""

import sys
import subprocess
from typing import List, Dict


class DependencyResolver:
    """
    插件依赖解析器
    
    功能：
    - 解析插件依赖列表
    - 自动pip安装缺失的依赖
    - 版本冲突检测
    """
    
    @staticmethod
    def check_dependency(package_name: str) -> bool:
        """
        检查依赖是否已安装
        
        Args:
            package_name: 包名称（可包含版本，如 numpy>=1.20）
            
        Returns:
            bool: 是否已安装
        """
        try:
            # 提取包名（去除版本信息）
            pkg_name = package_name.split('>=')[0].split('<=')[0].split('==')[0].strip()
            
            __import__(pkg_name)
            return True
        except ImportError:
            return False
    
    @staticmethod
    def install_dependencies(dependencies: List[str]) -> Dict[str, bool]:
        """
        安装依赖列表
        
        Args:
            dependencies: 依赖列表，如 ['numpy>=1.20', 'opencv-python']
            
        Returns:
            dict: {package_name: success}
        """
        results = {}
        
        for dep in dependencies:
            pkg_name = dep.split('>=')[0].split('<=')[0].split('==')[0].strip()
            
            # 检查是否已安装
            if DependencyResolver.check_dependency(dep):
                print(f"   ✅ 依赖已存在: {dep}")
                results[pkg_name] = True
                continue
            
            # 安装依赖
            print(f"   📦 正在安装: {dep}...")
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', dep],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5分钟超时
                )
                
                if result.returncode == 0:
                    print(f"   ✅ 安装成功: {dep}")
                    results[pkg_name] = True
                else:
                    print(f"   ❌ 安装失败: {dep}")
                    print(f"      错误: {result.stderr[:200]}")
                    results[pkg_name] = False
                    
            except subprocess.TimeoutExpired:
                print(f"   ❌ 安装超时: {dep}")
                results[pkg_name] = False
            except Exception as e:
                print(f"   ❌ 安装异常: {dep} - {e}")
                results[pkg_name] = False
        
        return results
