"""
AI 节点性能监控工具

提供性能基准测试、内存监控、缓存管理等功能
用于优化 AI 节点的运行时性能
"""

import time
import psutil
import os
from typing import Dict, Any, Optional
from functools import wraps


class PerformanceMonitor:
    """
    性能监控器
    
    功能：
    - 测量函数执行时间
    - 监控内存使用
    - 跟踪 GPU 显存（如果可用）
    - 生成性能报告
    """
    
    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.metrics: Dict[str, Any] = {}
    
    def measure_time(self, func_name: str):
        """
        装饰器：测量函数执行时间
        
        Usage:
            @monitor.measure_time("my_function")
            def my_function():
                pass
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                end_time = time.time()
                
                elapsed_ms = (end_time - start_time) * 1000
                self.metrics[f"{func_name}_time_ms"] = elapsed_ms
                
                return result
            return wrapper
        return decorator
    
    def get_memory_usage_mb(self) -> float:
        """获取当前进程的内存使用量（MB）"""
        memory_info = self.process.memory_info()
        return memory_info.rss / (1024 * 1024)
    
    def get_gpu_memory_mb(self) -> Optional[float]:
        """获取 GPU 显存使用量（MB）"""
        try:
            import torch
            if torch.cuda.is_available():
                gpu_memory_bytes = torch.cuda.memory_allocated(0)
                return gpu_memory_bytes / (1024 * 1024)
        except ImportError:
            pass
        return None
    
    def snapshot_performance(self, label: str = "snapshot"):
        """
        记录当前性能快照
        
        Args:
            label: 快照标签
        """
        snapshot = {
            'timestamp': time.time(),
            'memory_mb': self.get_memory_usage_mb(),
            'gpu_memory_mb': self.get_gpu_memory_mb()
        }
        
        self.metrics[f"{label}_snapshot"] = snapshot
        return snapshot
    
    def generate_report(self) -> Dict[str, Any]:
        """生成完整的性能报告"""
        report = {
            'metrics': self.metrics.copy(),
            'current_memory_mb': self.get_memory_usage_mb(),
            'current_gpu_memory_mb': self.get_gpu_memory_mb(),
            'timestamp': time.time()
        }
        
        return report
    
    def reset(self):
        """重置所有指标"""
        self.metrics.clear()


class ResultCache:
    """
    结果缓存管理器
    
    功能：
    - 基于输入参数的缓存键生成
    - TTL（Time-To-Live）过期策略
    - 最大缓存数量限制
    - 自动清理过期缓存
    """
    
    def __init__(self, max_size: int = 10, ttl_seconds: int = 3600):
        """
        初始化缓存
        
        Args:
            max_size: 最大缓存条目数
            ttl_seconds: 缓存有效期（秒）
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
    
    def _generate_cache_key(self, **kwargs) -> str:
        """
        生成缓存键
        
        Args:
            **kwargs: 参数字典
            
        Returns:
            str: 缓存键字符串
        """
        import hashlib
        import json
        
        # 将参数排序后转换为 JSON 字符串
        sorted_kwargs = dict(sorted(kwargs.items()))
        key_string = json.dumps(sorted_kwargs, sort_keys=True, default=str)
        
        # 使用 MD5 哈希生成固定长度的键
        cache_key = hashlib.md5(key_string.encode()).hexdigest()
        
        return cache_key
    
    def get(self, **kwargs) -> Optional[Any]:
        """
        从缓存中获取结果
        
        Args:
            **kwargs: 查询参数
            
        Returns:
            缓存的结果，如果不存在或已过期则返回 None
        """
        cache_key = self._generate_cache_key(**kwargs)
        
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            
            # 检查是否过期
            if time.time() - cached_item['timestamp'] < self.ttl_seconds:
                return cached_item['result']
            else:
                # 删除过期缓存
                del self.cache[cache_key]
        
        return None
    
    def set(self, result: Any, **kwargs):
        """
        将结果存入缓存
        
        Args:
            result: 要缓存的结果
            **kwargs: 缓存参数
        """
        cache_key = self._generate_cache_key(**kwargs)
        
        # 如果缓存已满，删除最旧的条目
        if len(self.cache) >= self.max_size:
            oldest_key = min(
                self.cache.keys(),
                key=lambda k: self.cache[k]['timestamp']
            )
            del self.cache[oldest_key]
        
        # 存入新缓存
        self.cache[cache_key] = {
            'result': result,
            'timestamp': time.time()
        }
    
    def clear(self):
        """清空所有缓存"""
        self.cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        now = time.time()
        valid_count = sum(
            1 for item in self.cache.values()
            if now - item['timestamp'] < self.ttl_seconds
        )
        
        return {
            'total_entries': len(self.cache),
            'valid_entries': valid_count,
            'expired_entries': len(self.cache) - valid_count,
            'max_size': self.max_size,
            'ttl_seconds': self.ttl_seconds
        }


class ResourceOptimizer:
    """
    资源优化器
    
    功能：
    - 智能释放未使用的模型
    - 垃圾回收触发
    - GPU 显存清理
    """
    
    @staticmethod
    def release_unused_models(model_cache: Dict):
        """
        释放未使用的模型以节省内存
        
        Args:
            model_cache: 模型缓存字典
        """
        import gc
        
        # 清除 Python 引用
        model_cache.clear()
        
        # 强制垃圾回收
        gc.collect()
    
    @staticmethod
    def clear_gpu_memory():
        """清理 GPU 显存"""
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
        except ImportError:
            pass
    
    @staticmethod
    def optimize_before_heavy_task():
        """在执行重量级任务前优化资源"""
        import gc
        
        # 垃圾回收
        gc.collect()
        
        # 清理 GPU 显存
        ResourceOptimizer.clear_gpu_memory()
        
        # 获取当前内存状态
        process = psutil.Process(os.getpid())
        memory_before = process.memory_info().rss / (1024 * 1024)
        
        return {
            'memory_before_mb': memory_before,
            'action': 'Resource optimization completed'
        }
