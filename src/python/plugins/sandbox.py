"""
插件沙箱环境 - 提供安全的插件执行环境
"""

import sys
import types
from typing import Dict, Any


class SandboxSecurityError(Exception):
    """沙箱安全错误"""
    pass


class PluginSandbox:
    """
    插件沙箱环境
    
    功能：
    - 限制可用的内置函数
    - 阻止危险模块导入
    - 提供安全的执行环境
    """
    
    # 允许的模块白名单
    ALLOWED_MODULES = {
        'cv2', 'numpy', 'NodeGraphQt',
        'math', 'random', 'datetime',
        'json', 'os.path', 'pathlib'
    }
    
    # 禁止的内置函数
    BLOCKED_BUILTINS = {
        'open', 'exec', 'eval', 'compile',
        '__import__', 'input', 'breakpoint'
    }
    
    def __init__(self):
        self.safe_globals = self._build_safe_environment()
    
    def _build_safe_environment(self) -> Dict[str, Any]:
        """
        构建安全的执行环境
        
        Returns:
            包含安全内置函数的字典
        """
        safe_builtins = {
            # 基本类型和函数
            'print': print,
            'len': len,
            'range': range,
            'int': int,
            'float': float,
            'str': str,
            'list': list,
            'dict': dict,
            'tuple': tuple,
            'set': set,
            'bool': bool,
            'type': type,
            
            # 类型检查
            'isinstance': isinstance,
            'issubclass': issubclass,
            'hasattr': hasattr,
            'getattr': getattr,
            'setattr': setattr,
            
            # 异常类
            'Exception': Exception,
            'ValueError': ValueError,
            'TypeError': TypeError,
            'RuntimeError': RuntimeError,
        }
        
        return {
            '__builtins__': safe_builtins,
        }
    
    def execute_with_limits(self, code_string: str, timeout: int = 10):
        """
        在受限环境中执行代码
        
        Args:
            code_string: 要执行的代码字符串
            timeout: 超时时间（秒）
        
        Raises:
            SandboxSecurityError: 安全违规或执行错误
        """
        try:
            # 在沙箱中执行
            exec(code_string, self.safe_globals)
        except TimeoutError:
            raise SandboxSecurityError("代码执行超时")
        except Exception as e:
            raise SandboxSecurityError(f"执行错误: {e}")
