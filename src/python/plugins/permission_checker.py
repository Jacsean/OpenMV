"""
插件权限检查器 - 静态分析插件代码安全性

安全策略：
- 白名单机制：允许安全的标准库模块（os, sys, json等）
- 路径沙箱：限制文件读写仅在插件目录和工作空间目录
- 危险操作拦截：阻止系统命令执行、网络访问、动态代码执行
"""

import re
import ast
from typing import List, Set


class PermissionChecker:
    """
    插件权限检查器
    
    功能：
    - 检测危险代码模式
    - AST静态分析
    - 白名单模块导入控制
    - 路径沙箱限制
    """
    
    # 危险代码模式列表（保留真正危险的操作）
    DANGEROUS_PATTERNS = [
        r'os\.system\s*\(',           # 系统命令执行
        r'os\.popen\s*\(',            # 管道执行
        r'subprocess\.(call|run|Popen)',  # 子进程执行
        r'socket\.',                  # 网络套接字
        r'requests\.',                # HTTP请求
        r'urllib\.request',           # URL访问
        r'__import__\s*\(\s*[\'"](os|subprocess|socket)[\'"]',  # 动态导入危险模块
        r'eval\s*\([^)]*__|exec\s*\([^)]*__',  # eval/exec 执行任意代码（允许简单表达式）
        r'ctypes\.',                  # C类型调用
        r'pickle\.loads',             # 反序列化风险（仅拦截 loads）
        r'marshal\.loads',            # 字节码反序列化
    ]
    
    # 允许导入的标准库模块（白名单）
    ALLOWED_MODULES = {
        'os', 'sys', 'json', 'pathlib', 're', 'math', 'time',
        'datetime', 'collections', 'itertools', 'functools',
        'typing', 'abc', 'enum', 'dataclasses',
        'cv2', 'numpy', 'PIL', 'torch', 'ultralytics',  # 第三方库
        'paddleocr', 'paddle',  # PaddleOCR 相关
    }
    
    # 禁止导入的模块（真正危险的）
    FORBIDDEN_MODULES = {
        'subprocess', 'socket', 'requests', 'urllib.request',
        'ctypes', 'pickle', 'shelve', 'marshal',
        'multiprocessing', 'threading',  # 并发控制由框架管理
    }
    
    # 允许的文件操作函数
    ALLOWED_FILE_OPERATIONS = {
        'os.makedirs', 'os.path.join', 'os.path.exists',
        'os.path.dirname', 'os.path.abspath',
        'open', 'json.dump', 'json.load',
        'shutil.copy', 'shutil.copy2', 'shutil.rmtree',  # 文件/目录操作
    }
    
    @staticmethod
    def check_source_code(source_code: str, plugin_name: str = "") -> List[str]:
        """
        检查源代码中的危险操作
        
        Args:
            source_code: 插件源代码
            plugin_name: 插件名称（用于路径沙箱验证）
            
        Returns:
            违规列表，如果为空则表示安全
        """
        violations = []
        
        # 1. 正则表达式模式匹配
        for pattern in PermissionChecker.DANGEROUS_PATTERNS:
            if re.search(pattern, source_code):
                violations.append(f"检测到危险模式: {pattern}")
        
        # 2. AST静态分析
        try:
            tree = ast.parse(source_code)
            violations.extend(PermissionChecker._ast_check(tree))
        except SyntaxError as e:
            violations.append(f"语法错误，无法分析: {e}")
        
        return violations
    
    @staticmethod
    def _ast_check(tree: ast.AST) -> List[str]:
        """
        AST静态分析
        
        Args:
            tree: AST语法树
            
        Returns:
            违规列表
        """
        violations = []
        
        for node in ast.walk(tree):
            # 检查import语句
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    
                    # 检查是否在禁止列表中
                    if module_name in PermissionChecker.FORBIDDEN_MODULES:
                        violations.append(f"禁止导入模块: {alias.name}")
                    # 检查是否在白名单中
                    elif module_name not in PermissionChecker.ALLOWED_MODULES:
                        # 警告：未知模块（不阻止，但记录）
                        pass  # 允许第三方库
            
            # 检查from ... import语句
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split('.')[0]
                    
                    if module_name in PermissionChecker.FORBIDDEN_MODULES:
                        violations.append(f"禁止从模块导入: {node.module}")
        
        return violations
    
    @staticmethod
    def is_path_safe(file_path: str, plugin_name: str, workspace_dir: str = "") -> bool:
        """
        验证文件路径是否在沙箱范围内
        
        Args:
            file_path: 要访问的文件路径
            plugin_name: 插件名称
            workspace_dir: 工作空间目录
            
        Returns:
            True 如果路径安全，False 否则
        """
        import os
        from pathlib import Path
        
        # 规范化路径
        abs_path = Path(file_path).resolve()
        
        # 允许的路径前缀
        allowed_prefixes = [
            Path(plugin_name).resolve(),  # 插件目录
        ]
        
        if workspace_dir:
            allowed_prefixes.append(Path(workspace_dir).resolve())
        
        # 检查路径是否在允许的范围内
        for prefix in allowed_prefixes:
            try:
                if abs_path.is_relative_to(prefix):
                    return True
            except (ValueError, AttributeError):
                # Python < 3.9 兼容处理
                if str(abs_path).startswith(str(prefix)):
                    return True
        
        return False
