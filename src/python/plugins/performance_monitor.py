"""
节点性能监控器

功能:
- 记录每个节点的执行耗时
- 统计内存使用情况
- 生成性能报告
- 识别瓶颈节点
"""

import time
import psutil
import os
from collections import defaultdict
from datetime import datetime


class PerformanceMonitor:
    """
    性能监控器单例
    
    跟踪所有节点的执行性能，提供统计分析
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PerformanceMonitor, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        
        # 性能数据统计
        self.execution_times = defaultdict(list)  # {node_class: [times]}
        self.memory_usage = defaultdict(list)     # {node_class: [memory_mb]}
        self.total_executions = 0
        self.start_time = datetime.now()
        
        # 当前进程
        self.process = psutil.Process(os.getpid())
        
    def record_execution(self, node_class, execution_time_ms, memory_before_mb, memory_after_mb):
        """
        记录节点执行性能
        
        Args:
            node_class (str): 节点类名
            execution_time_ms (float): 执行耗时（毫秒）
            memory_before_mb (float): 执行前内存（MB）
            memory_after_mb (float): 执行后内存（MB）
        """
        self.execution_times[node_class].append(execution_time_ms)
        self.memory_usage[node_class].append(memory_after_mb - memory_before_mb)
        self.total_executions += 1
        
    def get_node_stats(self, node_class):
        """
        获取节点性能统计
        
        Args:
            node_class (str): 节点类名
            
        Returns:
            dict: 统计数据
        """
        if node_class not in self.execution_times:
            return None
        
        times = self.execution_times[node_class]
        mem_diffs = self.memory_usage[node_class]
        
        return {
            'node_class': node_class,
            'total_calls': len(times),
            'avg_time_ms': sum(times) / len(times),
            'min_time_ms': min(times),
            'max_time_ms': max(times),
            'total_time_ms': sum(times),
            'avg_memory_delta_mb': sum(mem_diffs) / len(mem_diffs) if mem_diffs else 0,
            'max_memory_delta_mb': max(mem_diffs) if mem_diffs else 0
        }
    
    def get_all_stats(self):
        """
        获取所有节点的性能统计
        
        Returns:
            list[dict]: 所有节点的统计数据列表
        """
        stats = []
        for node_class in self.execution_times.keys():
            stat = self.get_node_stats(node_class)
            if stat:
                stats.append(stat)
        
        # 按平均耗时排序
        stats.sort(key=lambda x: x['avg_time_ms'], reverse=True)
        return stats
    
    def get_bottleneck_nodes(self, top_n=5):
        """
        获取性能瓶颈节点（最慢的N个）
        
        Args:
            top_n (int): 返回前N个瓶颈节点
            
        Returns:
            list[dict]: 瓶颈节点列表
        """
        all_stats = self.get_all_stats()
        return all_stats[:top_n]
    
    def get_system_info(self):
        """
        获取系统整体信息
        
        Returns:
            dict: 系统信息
        """
        current_mem = self.process.memory_info().rss / (1024 * 1024)  # MB
        uptime = datetime.now() - self.start_time
        
        return {
            'total_executions': self.total_executions,
            'uptime_seconds': uptime.total_seconds(),
            'current_memory_mb': current_mem,
            'unique_nodes': len(self.execution_times),
            'start_time': self.start_time.isoformat()
        }
    
    def generate_report(self):
        """
        生成性能报告文本
        
        Returns:
            str: 格式化的性能报告
        """
        sys_info = self.get_system_info()
        bottlenecks = self.get_bottleneck_nodes(5)
        
        report = f"""
╔══════════════════════════════════════════════════╗
║          节点性能监控报告
╠══════════════════════════════════════════════════╣
║ 总执行次数: {sys_info['total_executions']:<35} ║
║ 运行时长: {sys_info['uptime_seconds']:.1f}秒{' ' * 28}║
║ 当前内存: {sys_info['current_memory_mb']:.2f} MB{' ' * 26}║
║ 节点种类: {sys_info['unique_nodes']:<35} ║
╠══════════════════════════════════════════════════╣
║  🐌 性能瓶颈节点 (Top 5)
╠══════════════════════════════════════════════════╣
"""
        
        for i, node in enumerate(bottlenecks, 1):
            report += f"║ {i}. {node['node_class']:<30} ║\n"
            report += f"║    平均耗时: {node['avg_time_ms']:.2f}ms  调用: {node['total_calls']}次{' ' * 10}║\n"
            report += f"║    最大耗时: {node['max_time_ms']:.2f}ms  内存增量: {node['avg_memory_delta_mb']:.2f}MB{' ' * 2}║\n"
            report += f"╠{'═' * 50}╣\n"
        
        if not bottlenecks:
            report += "║    暂无数据\n"
            report += f"╠{'═' * 50}╣\n"
        
        report += "╚══════════════════════════════════════════════════╝\n"
        
        return report
    
    def reset(self):
        """重置所有统计数据"""
        self.execution_times.clear()
        self.memory_usage.clear()
        self.total_executions = 0
        self.start_time = datetime.now()
        print("🔄 性能统计数据已重置")


# 全局实例
perf_monitor = PerformanceMonitor()
