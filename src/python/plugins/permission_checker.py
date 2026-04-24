"""
插件权限检查器 - 静态分析插件代码安全性
"""

import re
import ast
from typing import List


class PermissionChecker:
    """
    插件权限检查器
    
    功能：
    - 检测危险代码模式
    - AST静态分析
    - 阻止危险模块导入
    """
    
    # 危险代码模式列表
    DANGEROUS_PATTERNS = [
        r'os\.system',           # 系统命令执行
        r'os\.popen',            # 管道执行
        r'subprocess\.',         # 子进程
        r'socket\.',             # 网络套接字
        r'requests\.',           # HTTP请求
        r'urllib\.',             # URL访问
        r'__import__\s*\(\s*[\'"]os[\'"]',  # 动态导入os
        r'eval\s*\(',            # eval执行
        r'exec\s*\(',            # exec执行
        r'open\s*\(.*[\'"]w[\'"]',  # 写文件操作
        r'shutil\.',             # 文件操作
        r'ctypes\.',             # C类型调用
        r'pickle\.',             # 反序列化风险
    ]
    
    # 禁止导入的模块
    FORBIDDEN_MODULES = {
        'os', 'subprocess', 'socket',
        'requests', 'urllib', 'ctypes',
        'pickle', 'shelve', 'marshal'
    }
    
    @staticmethod
    def check_source_code(source_code: str) -> List[str]:
        """
        检查源代码中的危险操作
        
        Args:
            source_code: 插件源代码
            
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
                    if alias.name in PermissionChecker.FORBIDDEN_MODULES:
                        violations.append(f"禁止导入模块: {alias.name}")
            
            # 检查from ... import语句
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] in PermissionChecker.FORBIDDEN_MODULES:
                    violations.append(f"禁止从模块导入: {node.module}")
        
        return violations
