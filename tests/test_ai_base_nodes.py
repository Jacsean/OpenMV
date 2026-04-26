"""
AI 节点基类单元测试

测试 AIBaseNode 和 AsyncAINode 的核心功能
"""

import sys
import os
import time
import unittest
from unittest.mock import Mock, patch, MagicMock

# 添加项目根目录到路径
project_root = os.path.join(os.path.dirname(__file__), '..', 'src', 'python')
sys.path.insert(0, project_root)

from user_plugins.base_nodes import AIBaseNode, AsyncAINode


class TestAIBaseNode(unittest.TestCase):
    """测试 AIBaseNode 基类"""
    
    def setUp(self):
        """每个测试前的设置"""
        # 创建一个测试节点类
        class TestNode(AIBaseNode):
            __identifier__ = 'test_ai'
            NODE_NAME = '测试节点'
            
            def __init__(self):
                super().__init__()
                self.resource_level = "light"
        
        self.node = TestNode()
    
    def test_check_dependencies_success(self):
        """测试依赖检查 - 成功情况"""
        # 模拟所有依赖都已安装
        with patch('builtins.__import__', return_value=Mock()):
            result = self.node.check_dependencies(['package1', 'package2'])
            self.assertTrue(result)
    
    def test_check_dependencies_failure(self):
        """测试依赖检查 - 失败情况"""
        # 模拟缺少依赖
        def mock_import(name, *args, **kwargs):
            if name == 'missing_package':
                raise ImportError(f"No module named '{name}'")
            return Mock()
        
        with patch('builtins.__import__', side_effect=mock_import):
            result = self.node.check_dependencies(['existing_package', 'missing_package'])
            self.assertFalse(result)
    
    def test_check_hardware_cpu_only(self):
        """测试硬件检查 - 仅 CPU"""
        # 模拟低配置机器
        mock_psutil = Mock()
        mock_psutil.cpu_count.return_value = 4
        mock_psutil.virtual_memory.return_value.available = 4 * 1024**3  # 4GB
        
        with patch.dict('sys.modules', {'psutil': mock_psutil}):
            # 要求较低，应该通过
            result = self.node.check_hardware({
                'cpu_cores': 2,
                'memory_gb': 2,
                'gpu_required': False
            })
            self.assertTrue(result)
    
    def test_check_hardware_insufficient_memory(self):
        """测试硬件检查 - 内存不足"""
        mock_psutil = Mock()
        mock_psutil.cpu_count.return_value = 8
        mock_psutil.virtual_memory.return_value.available = 1 * 1024**3  # 1GB
        
        with patch.dict('sys.modules', {'psutil': mock_psutil}):
            result = self.node.check_hardware({
                'cpu_cores': 2,
                'memory_gb': 8,  # 需要 8GB
                'gpu_required': False
            })
            self.assertFalse(result)
    
    def test_check_hardware_gpu_required(self):
        """测试硬件检查 - 需要 GPU"""
        mock_psutil = Mock()
        mock_psutil.cpu_count.return_value = 8
        mock_psutil.virtual_memory.return_value.available = 16 * 1024**3
        
        mock_torch = Mock()
        mock_torch.cuda.is_available.return_value = False
        
        with patch.dict('sys.modules', {'psutil': mock_psutil, 'torch': mock_torch}):
            result = self.node.check_hardware({
                'cpu_cores': 2,
                'memory_gb': 2,
                'gpu_required': True
            })
            self.assertFalse(result)
    
    def test_model_cache_basic(self):
        """测试模型缓存 - 基本功能"""
        # 清空缓存
        AIBaseNode._model_cache.clear()
        
        call_count = [0]
        
        def mock_loader():
            call_count[0] += 1
            return "mock_model"
        
        # 第一次加载（应该调用 loader）
        model1 = self.node.get_or_load_model('test_model', mock_loader)
        self.assertEqual(model1, "mock_model")
        self.assertEqual(call_count[0], 1)
        
        # 第二次加载（应该使用缓存）
        model2 = self.node.get_or_load_model('test_model', mock_loader)
        self.assertEqual(model2, "mock_model")
        self.assertEqual(call_count[0], 1)  # loader 不应该再次调用
    
    def test_model_cache_clear(self):
        """测试模型缓存 - 清理功能"""
        AIBaseNode._model_cache.clear()
        
        def mock_loader():
            return "mock_model"
        
        # 加载模型
        self.node.get_or_load_model('model1', mock_loader)
        self.node.get_or_load_model('model2', mock_loader)
        
        self.assertEqual(len(AIBaseNode._model_cache), 2)
        
        # 清理指定模型
        self.node.clear_model_cache('model1')
        self.assertEqual(len(AIBaseNode._model_cache), 1)
        
        # 清理所有模型
        self.node.clear_model_cache()
        self.assertEqual(len(AIBaseNode._model_cache), 0)
    
    def test_logging_methods(self):
        """测试日志方法"""
        # 这些方法应该不抛出异常
        self.node.log_info("测试信息")
        self.node.log_warning("测试警告")
        self.node.log_error("测试错误")
        self.node.log_success("测试成功")


class TestAsyncAINode(unittest.TestCase):
    """测试 AsyncAINode 基类"""
    
    def setUp(self):
        """每个测试前的设置"""
        class TestAsyncNode(AsyncAINode):
            __identifier__ = 'test_async'
            NODE_NAME = '测试异步节点'
            
            def __init__(self):
                super().__init__()
            
            def process(self, inputs):
                time.sleep(0.1)  # 模拟耗时操作
                return {'result': 'success'}
        
        self.node = TestAsyncNode()
    
    def tearDown(self):
        """每个测试后的清理"""
        self.node.cleanup()
    
    def test_async_process_basic(self):
        """测试异步处理 - 基本功能"""
        inputs = {'data': 'test'}
        
        # 启动异步任务
        self.node.start_async_process(inputs)
        
        # 检查是否正在处理
        self.assertTrue(self.node.is_processing())
        
        # 等待完成
        time.sleep(0.2)
        
        # 获取结果
        result = self.node.get_async_result()
        self.assertIsNotNone(result)
        self.assertEqual(result['result'], 'success')
    
    def test_async_process_not_done(self):
        """测试异步处理 - 未完成时返回 None"""
        inputs = {'data': 'test'}
        
        # 启动异步任务
        self.node.start_async_process(inputs)
        
        # 立即获取结果（应该返回 None）
        result = self.node.get_async_result()
        self.assertIsNone(result)
    
    def test_async_cancel(self):
        """测试异步处理 - 取消任务"""
        inputs = {'data': 'test'}
        
        # 启动异步任务
        self.node.start_async_process(inputs)
        
        # 取消任务
        self.node.cancel_async_process()
        
        # 清理
        self.node.cleanup()
    
    def test_concurrent_tasks(self):
        """测试并发任务 - 不应同时运行多个任务"""
        inputs = {'data': 'test'}
        
        # 启动第一个任务
        self.node.start_async_process(inputs)
        
        # 尝试启动第二个任务（应该被阻止）
        self.node.start_async_process(inputs)
        
        # 等待完成
        time.sleep(0.2)
        
        # 应该只有一个结果
        result = self.node.get_async_result()
        self.assertIsNotNone(result)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_base_node_inheritance(self):
        """测试基类继承"""
        from NodeGraphQt import BaseNode
        
        # AIBaseNode 应该继承自 BaseNode
        self.assertTrue(issubclass(AIBaseNode, BaseNode))
        
        # AsyncAINode 应该继承自 AIBaseNode
        self.assertTrue(issubclass(AsyncAINode, AIBaseNode))
    
    def test_resource_level_attribute(self):
        """测试资源等级属性"""
        node = AIBaseNode()
        self.assertEqual(node.resource_level, "light")
        
        node.resource_level = "heavy"
        self.assertEqual(node.resource_level, "heavy")
    
    def test_hardware_requirements_attribute(self):
        """测试硬件要求属性"""
        node = AIBaseNode()
        
        self.assertIn('cpu_cores', node.hardware_requirements)
        self.assertIn('memory_gb', node.hardware_requirements)
        self.assertIn('gpu_required', node.hardware_requirements)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
