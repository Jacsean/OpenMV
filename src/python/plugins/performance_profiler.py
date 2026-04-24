"""
节点性能分析工具

功能:
- cProfile性能分析
- 内存使用监控
- 瓶颈定位
- 优化建议生成
"""

import cProfile
import pstats
import io
import tracemalloc
from functools import wraps


def profile_node_execution(func):
    """
    装饰器：分析节点执行性能
    
    用法:
    @profile_node_execution
    def process(self, inputs=None):
        # 节点处理逻辑
        pass
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # 开始性能分析
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            profiler.disable()
            
            # 获取性能数据
            node_instance = args[0] if args else None
            node_class = node_instance.__class__.__name__ if node_instance else "Unknown"
            
            # 打印统计信息
            stream = io.StringIO()
            stats = pstats.Stats(profiler, stream=stream)
            stats.sort_stats('cumulative')
            stats.print_stats(10)  # 前10个最耗时的函数
            
            print(f"\n📊 性能分析: {node_class}")
            print(f"   热点函数:\n{stream.getvalue()}")
    
    return wrapper


class PerformanceProfiler:
    """
    性能分析器
    
    提供细粒度的性能分析功能
    """
    
    def __init__(self):
        self.profiles = {}
        
    def start_profiling(self, name):
        """
        开始性能分析
        
        Args:
            name (str): 分析任务名称
        """
        tracemalloc.start()
        profiler = cProfile.Profile()
        profiler.enable()
        
        self.profiles[name] = {
            'profiler': profiler,
            'start_snapshot': tracemalloc.take_snapshot()
        }
        
        print(f"▶️  开始性能分析: {name}")
        
    def stop_profiling(self, name, top_n=10):
        """
        停止性能分析并生成报告
        
        Args:
            name (str): 分析任务名称
            top_n (int): 显示前N个热点
        """
        if name not in self.profiles:
            print(f"⚠️  未找到分析任务: {name}")
            return
        
        profile_data = self.profiles[name]
        profiler = profile_data['profiler']
        
        profiler.disable()
        
        # 生成CPU分析报告
        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats('cumulative')
        stats.print_stats(top_n)
        
        print(f"\n{'=' * 60}")
        print(f"📊 性能分析报告: {name}")
        print(f"{'=' * 60}")
        print(f"\n🔥 CPU热点 (Top {top_n}):")
        print(stream.getvalue())
        print(f"{'=' * 60}\n")
        
        del self.profiles[name]
        
    def clear_all(self):
        """清除所有分析数据"""
        self.profiles.clear()
        tracemalloc.stop()
        print("🗑️  已清除所有性能分析数据")


# 全局分析器实例
profiler = PerformanceProfiler()
