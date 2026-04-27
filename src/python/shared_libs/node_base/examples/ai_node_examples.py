"""
AI 节点开发示例

演示如何使用 AIBaseNode 和 AsyncAINode 创建 AI 节点
"""

# ============================================================================
# 示例 1: 轻量级推理节点（继承 AIBaseNode）
# ============================================================================

from user_plugins.base_nodes import AIBaseNode


class ExampleLightNode(AIBaseNode):
    """
    轻量级 AI 节点示例
    
    硬件要求：
    - CPU: 2 核心
    - 内存: 2GB
    - GPU: 可选
    """
    
    __identifier__ = 'example_ai'
    NODE_NAME = '示例轻量级节点'
    
    def __init__(self):
        super().__init__()
        
        # 设置资源等级
        self.resource_level = "light"
        
        # 设置硬件要求
        self.hardware_requirements = {
            'cpu_cores': 2,
            'memory_gb': 2,
            'gpu_required': False
        }
        
        # 定义端口
        self.add_input('输入图像')
        self.add_output('输出结果')
        
        # 添加参数
        self.add_text_input('param1', '参数1', 'default_value')
    
    def process(self, inputs):
        """
        执行处理逻辑
        
        Args:
            inputs: 输入数据字典
            
        Returns:
            dict: 输出数据字典，失败返回 None
        """
        try:
            # Step 1: 检查依赖
            if not self.check_dependencies(['package_name']):
                return None
            
            # Step 2: 检查硬件（可选，轻量级节点通常不需要）
            # if not self.check_hardware():
            #     return None
            
            # Step 3: 获取输入
            image = inputs.get('输入图像')
            if image is None:
                self.log_error("未接收到输入图像")
                return None
            
            # Step 4: 加载模型（带缓存）
            # model = self.get_or_load_model(
            #     'model_key',
            #     lambda: load_your_model()
            # )
            
            # Step 5: 执行推理
            # result = model.predict(image)
            
            # Step 6: 返回结果
            self.log_success("处理完成")
            return {'输出结果': 'result_data'}
            
        except Exception as e:
            self.log_error(f"处理失败: {e}")
            import traceback
            traceback.print_exc()
            return None


# ============================================================================
# 示例 2: 重量级训练节点（继承 AIBaseNode）
# ============================================================================

class ExampleHeavyNode(AIBaseNode):
    """
    重量级 AI 节点示例（需要 GPU）
    
    硬件要求：
    - CPU: 8+ 核心
    - 内存: 16GB+
    - GPU: 必需（CUDA 11.8+，8GB+ 显存）
    """
    
    __identifier__ = 'example_ai'
    NODE_NAME = '示例重量级节点'
    
    def __init__(self):
        super().__init__()
        
        # 设置资源等级
        self.resource_level = "heavy"
        
        # 设置硬件要求
        self.hardware_requirements = {
            'cpu_cores': 8,
            'memory_gb': 16,
            'gpu_required': True,
            'gpu_memory_gb': 8
        }
        
        # 定义端口
        self.add_input('输入数据集')
        self.add_output('训练好的模型')
        
        # 添加参数
        self.add_text_input('epochs', '训练轮数', '100')
        self.add_text_input('batch_size', '批处理大小', '16')
        
        # 添加硬件提示
        self.add_text_input('_hardware_note', '硬件要求', 
                           '⚠️ 需要 GPU (CUDA 11.8+, 8GB+ VRAM)')
    
    def process(self, inputs):
        """执行训练"""
        try:
            # Step 1: 检查依赖
            if not self.check_dependencies(['torch', 'ultralytics']):
                return None
            
            # Step 2: 检查硬件（重量级节点必须检查）
            if not self.check_hardware():
                self.log_warning("建议：在配备 GPU 的工作站上运行")
                return None
            
            # Step 3: 获取输入
            dataset = inputs.get('输入数据集')
            if not dataset:
                self.log_error("未接收到数据集")
                return None
            
            # Step 4: 执行训练
            self.log_info("开始训练...")
            # model = self.get_or_load_model(...)
            # results = model.train(...)
            
            self.log_success("训练完成")
            return {'训练好的模型': 'model_path'}
            
        except Exception as e:
            self.log_error(f"训练失败: {e}")
            import traceback
            traceback.print_exc()
            return None


# ============================================================================
# 示例 3: 异步推理节点（继承 AsyncAINode）
# ============================================================================

from user_plugins.base_nodes import AsyncAINode


class ExampleAsyncNode(AsyncAINode):
    """
    异步 AI 节点示例
    
    适用于耗时较长的推理任务，避免阻塞 UI
    """
    
    __identifier__ = 'example_ai'
    NODE_NAME = '示例异步节点'
    
    def __init__(self):
        super().__init__()
        
        self.resource_level = "medium"
        
        # 定义端口
        self.add_input('输入图像')
        self.add_output('输出结果')
        self.add_output('处理状态')
    
    def process(self, inputs):
        """
        同步处理（供异步调用）
        
        注意：这个方法会被线程池调用，不要直接操作 UI
        """
        try:
            # 检查依赖
            if not self.check_dependencies(['package_name']):
                return None
            
            # 获取输入
            image = inputs.get('输入图像')
            
            # 执行推理（耗时操作）
            # result = model.predict(image)
            
            self.log_success("异步处理完成")
            return {'output': 'result'}
            
        except Exception as e:
            self.log_error(f"异步处理失败: {e}")
            return None
    
    def custom_process_method(self, inputs):
        """
        自定义处理方法（可选）
        
        可以在启动异步任务时指定使用此方法
        """
        # ... 自定义逻辑 ...
        return {'output': 'custom_result'}


# ============================================================================
# 使用示例：在主窗口中调用异步节点
# ============================================================================

"""
# 在工作流执行器中：

node = graph.get_node_by_id('node_id')

# 方式 1: 同步调用（传统方式）
result = node.process(inputs)

# 方式 2: 异步调用（不阻塞 UI）
if isinstance(node, AsyncAINode):
    # 启动异步任务
    node.start_async_process(inputs)
    
    # 定期检查结果（如在定时器中）
    if not node.is_processing():
        result = node.get_async_result()
        if result:
            # 处理结果
            pass

# 方式 3: 使用自定义处理方法
node.start_async_process(inputs, process_func=node.custom_process_method)

# 取消任务
node.cancel_async_process()

# 清理资源（程序退出时）
node.cleanup()
"""


# ============================================================================
# 最佳实践总结
# ============================================================================

"""
1. 选择合适的基类：
   - 轻量级推理 → AIBaseNode
   - 重量级训练 → AIBaseNode（带硬件检查）
   - 耗时推理 → AsyncAINode

2. 始终进行依赖检查：
   if not self.check_dependencies(['package']):
       return None

3. 重量级节点必须检查硬件：
   if not self.check_hardware():
       return None

4. 使用模型缓存：
   model = self.get_or_load_model('key', loader_func)

5. 统一的日志输出：
   self.log_info("消息")
   self.log_warning("警告")
   self.log_error("错误")
   self.log_success("成功")

6. 完整的异常处理：
   try:
       # 业务逻辑
   except Exception as e:
       self.log_error(f"失败: {e}")
       return None

7. 清晰的 docstring：
   - 说明节点功能
   - 列出硬件要求
   - 提供使用示例

8. 语义化的端口命名：
   self.add_input('输入图像')  # ✅
   self.add_input('img_in')    # ❌
"""
