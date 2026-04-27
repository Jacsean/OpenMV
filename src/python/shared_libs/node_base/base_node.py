"""
通用节点基类模块

提供统一的节点基础框架，适用于所有类型节点，包括：
- 依赖检查与硬件检测
- 模型缓存管理
- 异步推理支持
- 资源等级声明
- 友好的错误提示
- 性能监控与结果缓存

遵循《AI 模块资源隔离设计规范》
"""

import os
import sys
import time
from typing import Dict, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, Future
from NodeGraphQt import BaseNode

# 导入性能监控工具
try:
    from .performance_monitor import PerformanceMonitor, ResultCache, ResourceOptimizer
    HAS_PERFORMANCE_TOOLS = True
except ImportError:
    HAS_PERFORMANCE_TOOLS = False


class BaseNode(BaseNode):
    """
    通用节点基类
    
    提供所有 AI 节点的通用功能：
    - 依赖检查（运行时验证）
    - 硬件检查（CPU/内存/GPU）
    - 模型缓存（类级别共享，避免重复加载）
    - 资源等级声明（light/medium/heavy）
    - 统一的错误处理和日志输出
    - 性能监控（执行时间、内存使用）
    - 结果缓存（避免重复计算）
    
    使用示例：
        class YOLODetectNode(BaseNode):
            __identifier__ = 'yolo_vision'
            NODE_NAME = 'YOLO 目标检测'
            
            def __init__(self):
                super().__init__()
                self.add_input('输入图像')
                self.add_output('输出标注图像')
                
            def process(self, inputs):
                # 自动进行依赖和硬件检查
                if not self.check_dependencies(['ultralytics']):
                    return None
                
                image = inputs.get('输入图像')
                # ... 执行推理 ...
                return {'输出标注图像': result}
    """
    
    # 类级别模型缓存（跨实例共享）
    _model_cache: Dict[str, Any] = {}
    
    def __init__(self):
        super(BaseNode, self).__init__()
        
        # 资源等级（子类应覆盖）
        self.resource_level = "light"  # light / medium / heavy
        
        # 硬件要求（子类应覆盖）
        self.hardware_requirements = {
            'cpu_cores': 2,
            'memory_gb': 2,
            'gpu_required': False,
            'gpu_memory_gb': 0
        }
        
        # 性能监控器（如果可用）
        if HAS_PERFORMANCE_TOOLS:
            self.performance_monitor = PerformanceMonitor()
            self.result_cache = ResultCache(max_size=5, ttl_seconds=1800)  # 30分钟TTL
        else:
            self.performance_monitor = None
            self.result_cache = None
    
    def measure_performance(self, label: str = "process"):
        """
        装饰器：测量 process 方法的性能
        
        Usage:
            @node.measure_performance("yolo_detect")
            def process(self, inputs):
                pass
        """
        if not HAS_PERFORMANCE_TOOLS or not self.performance_monitor:
            # 如果没有性能监控工具，返回空装饰器
            def decorator(func):
                return func
            return decorator
        
        return self.performance_monitor.measure_time(label)
    
    def check_dependencies(self, required_packages: list) -> bool:
        """
        检查依赖是否已安装
        
        Args:
            required_packages: 必需的包名列表，如 ['ultralytics', 'torch']
            
        Returns:
            bool: 所有依赖都已安装返回 True，否则返回 False
            
        示例：
            if not self.check_dependencies(['ultralytics', 'torch']):
                return None
        """
        missing = []
        for package in required_packages:
            # 解析包名（去除版本信息）
            pkg_name = package.split('>=')[0].split('==')[0].split('<=')[0].strip()
            
            try:
                __import__(pkg_name)
            except ImportError:
                missing.append(package)
        
        if missing:
            print(f"❌ 缺少依赖: {', '.join(missing)}")
            print(f"💡 安装命令: pip install {' '.join(missing)}")
            print(f"📖 详细说明: 请查看插件 README.md 中的安装指南")
            return False
        
        return True
    
    def check_hardware(self, custom_requirements: Optional[Dict] = None) -> bool:
        """
        检查硬件是否满足要求
        
        Args:
            custom_requirements: 自定义硬件要求，覆盖默认值
                {
                    'cpu_cores': 4,
                    'memory_gb': 8,
                    'gpu_required': True,
                    'gpu_memory_gb': 8
                }
            
        Returns:
            bool: 硬件满足要求返回 True，否则返回 False
            
        示例：
            if not self.check_hardware():
                return None
        """
        try:
            import psutil
        except ImportError:
            print("⚠️ 未安装 psutil，跳过硬件检查")
            print("💡 安装命令: pip install psutil")
            return True  # 无法检查时默认通过
        
        # 使用自定义要求或默认要求
        reqs = custom_requirements or self.hardware_requirements
        
        # 检查 CPU 核心数
        cpu_cores = psutil.cpu_count(logical=False)
        if cpu_cores < reqs.get('cpu_cores', 2):
            print(f"⚠️ CPU 核心数不足 ({cpu_cores} < {reqs['cpu_cores']})")
            print(f"💡 建议: 使用更高配置的计算机")
            return False
        
        # 检查可用内存
        memory_gb = psutil.virtual_memory().available / (1024 ** 3)
        if memory_gb < reqs.get('memory_gb', 2):
            print(f"⚠️ 可用内存不足 ({memory_gb:.1f}GB < {reqs['memory_gb']}GB)")
            print(f"💡 建议: 关闭其他程序或升级内存")
            return False
        
        # 检查 GPU
        if reqs.get('gpu_required', False):
            try:
                import torch
                if not torch.cuda.is_available():
                    print("❌ 未检测到 CUDA 设备")
                    print(f"💡 需要: NVIDIA GPU + CUDA {reqs.get('cuda_version', '11.8')}+")
                    print(f"📖 安装指南: https://pytorch.org/get-started/locally/")
                    return False
                
                # 检查显存
                gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
                required_gpu_gb = reqs.get('gpu_memory_gb', 0)
                if gpu_memory_gb < required_gpu_gb:
                    print(f"❌ GPU 显存不足 ({gpu_memory_gb:.1f}GB < {required_gpu_gb}GB)")
                    print(f"💡 需要: {required_gpu_gb}GB+ 显存的 NVIDIA GPU")
                    return False
                
                print(f"✅ GPU 可用: {torch.cuda.get_device_name(0)} ({gpu_memory_gb:.1f}GB)")
                
            except ImportError:
                print("❌ 未安装 PyTorch")
                print(f"💡 安装命令: pip install torch")
                print(f"📖 GPU 版本: pip install torch --index-url https://download.pytorch.org/whl/cu118")
                return False
        
        return True
    
    def get_or_load_model(self, model_key: str, loader_func: Callable) -> Any:
        """
        智能模型加载（带缓存）
        
        如果模型已在缓存中，直接返回；否则调用 loader_func 加载并缓存。
        
        Args:
            model_key: 模型的唯一标识符（如模型路径或名称）
            loader_func: 无参函数，用于加载模型
            
        Returns:
            加载的模型对象
            
        示例：
            model = self.get_or_load_model(
                'yolov8n',
                lambda: YOLO('yolov8n.pt')
            )
        """
        if model_key not in self._model_cache:
            print(f"🔄 首次加载模型: {model_key}")
            start_time = time.time()
            
            try:
                model = loader_func()
                elapsed = time.time() - start_time
                print(f"✅ 模型加载完成 (耗时: {elapsed:.2f}s)")
                
                self._model_cache[model_key] = model
                
            except Exception as e:
                print(f"❌ 模型加载失败: {e}")
                raise
        else:
            print(f"✅ 使用缓存模型: {model_key}")
        
        return self._model_cache[model_key]
    
    def clear_model_cache(self, model_key: Optional[str] = None):
        """
        清理模型缓存
        
        Args:
            model_key: 指定要清理的模型，None 则清空所有缓存
        """
        if model_key:
            if model_key in self._model_cache:
                del self._model_cache[model_key]
                print(f"🗑️ 已清理模型缓存: {model_key}")
        else:
            self._model_cache.clear()
            print("🗑️ 已清空所有模型缓存")
    
    def log_info(self, message: str):
        """记录信息日志"""
        print(f"ℹ️ [{self.NODE_NAME}] {message}")
    
    def log_warning(self, message: str):
        """记录警告日志"""
        print(f"⚠️ [{self.NODE_NAME}] {message}")
    
    def log_error(self, message: str):
        """记录错误日志"""
        print(f"❌ [{self.NODE_NAME}] {message}")
    
    def log_success(self, message: str):
        """记录成功日志"""
        print(f"✅ [{self.NODE_NAME}] {message}")
    
    def get_performance_report(self) -> Optional[Dict[str, Any]]:
        """
        获取性能报告
        
        Returns:
            dict: 性能报告字典，如果性能监控不可用则返回 None
        """
        if not HAS_PERFORMANCE_TOOLS or not self.performance_monitor:
            return None
        
        return self.performance_monitor.generate_report()
    
    def get_cache_stats(self) -> Optional[Dict[str, Any]]:
        """
        获取缓存统计信息
        
        Returns:
            dict: 缓存统计信息，如果缓存不可用则返回 None
        """
        if not HAS_PERFORMANCE_TOOLS or not self.result_cache:
            return None
        
        return self.result_cache.get_stats()
    
    def clear_result_cache(self):
        """清空结果缓存"""
        if HAS_PERFORMANCE_TOOLS and self.result_cache:
            self.result_cache.clear()
            self.log_info("已清空结果缓存")
    
    def optimize_resources(self):
        """优化资源使用（在执行重量级任务前调用）"""
        if HAS_PERFORMANCE_TOOLS:
            opt_result = ResourceOptimizer.optimize_before_heavy_task()
            self.log_info(f"资源优化完成: {opt_result['memory_before_mb']:.1f}MB")
            return opt_result
        return None
    
    def check_cached_result(self, **kwargs) -> Optional[Any]:
        """
        检查缓存中是否有结果
        
        Args:
            **kwargs: 缓存查询参数
            
        Returns:
            缓存的结果，如果不存在则返回 None
        """
        if not HAS_PERFORMANCE_TOOLS or not self.result_cache:
            return None
        
        return self.result_cache.get(**kwargs)
    
    def cache_result(self, result: Any, **kwargs):
        """
        将结果存入缓存
        
        Args:
            result: 要缓存的结果
            **kwargs: 缓存参数
        """
        if HAS_PERFORMANCE_TOOLS and self.result_cache:
            self.result_cache.set(result, **kwargs)


class AsyncAINode(BaseNode):
    """
    异步 通用节点基类
    
    在 BaseNode 基础上增加异步推理支持，避免阻塞 UI。
    
    使用示例：
        class AsyncYOLONode(AsyncAINode):
            def process(self, inputs):
                # 启动异步推理
                self.start_async_process(inputs)
                return {'status': 'processing'}
            
            def get_async_result(self):
                # 获取异步结果
                result = super().get_async_result()
                if result:
                    return {'输出图像': result}
                return None
    """
    
    def __init__(self):
        super(AsyncAINode, self).__init__()
        
        # 线程池执行器
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._future: Optional[Future] = None
        self._start_time: Optional[float] = None
    
    def start_async_process(self, inputs: Dict[str, Any], process_func: Optional[Callable] = None):
        """
        启动异步处理
        
        Args:
            inputs: 输入数据字典
            process_func: 自定义处理函数，默认为 self.process
        """
        if self._future and not self._future.done():
            print("⚠️ 上一个任务仍在执行中")
            return
        
        self._start_time = time.time()
        func = process_func or self.process
        self._future = self._executor.submit(func, inputs)
        print("🔄 异步任务已启动")
    
    def get_async_result(self) -> Optional[Any]:
        """
        获取异步处理结果
        
        Returns:
            处理结果，如果任务未完成返回 None
        """
        if not self._future:
            return None
        
        if not self._future.done():
            return None
        
        try:
            result = self._future.result()
            elapsed = time.time() - self._start_time if self._start_time else 0
            print(f"✅ 异步任务完成 (耗时: {elapsed:.2f}s)")
            return result
            
        except Exception as e:
            print(f"❌ 异步任务失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def is_processing(self) -> bool:
        """
        检查是否正在处理
        
        Returns:
            bool: 正在处理返回 True
        """
        return self._future is not None and not self._future.done()
    
    def cancel_async_process(self):
        """取消异步处理"""
        if self._future:
            self._future.cancel()
            print("🗑️ 已取消异步任务")
    
    def cleanup(self):
        """清理资源"""
        if self._executor:
            self._executor.shutdown(wait=False)
        self.clear_model_cache()


# 导出基类
__all__ = ['BaseNode', 'AsyncAINode']
