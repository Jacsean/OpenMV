# AI 节点开发指南

> **文档说明**: 本文档介绍如何使用 `AIBaseNode` 和 `AsyncAINode` 基类快速开发 AI 功能节点。

---

## 📋 目录

- [1. 概述](#1-概述)
- [2. 快速开始](#2-快速开始)
- [3. AIBaseNode 使用指南](#3-aibasenode-使用指南)
- [4. AsyncAINode 使用指南](#4-asyncainode-使用指南)
- [5. 最佳实践](#5-最佳实践)
- [6. 常见问题](#6-常见问题)

---

## 1. 概述

### 1.1 为什么需要基类？

在开发 AI 节点时，我们经常遇到以下问题：
- ❌ 重复编写依赖检查代码
- ❌ 每个节点都要处理模型缓存
- ❌ 硬件检查逻辑不一致
- ❌ 错误提示不友好
- ❌ 异步推理实现复杂

**解决方案**：使用统一的基类 `AIBaseNode` 和 `AsyncAINode`，提供开箱即用的通用功能。

### 1.2 基类功能对比

| 功能 | AIBaseNode | AsyncAINode |
|------|-----------|-------------|
| 依赖检查 | ✅ | ✅ |
| 硬件检查 | ✅ | ✅ |
| 模型缓存 | ✅ | ✅ |
| 日志输出 | ✅ | ✅ |
| 异步推理 | ❌ | ✅ |
| 任务取消 | ❌ | ✅ |

**选择建议**：
- 轻量级推理（< 1s）→ 使用 `AIBaseNode`
- 重量级训练/量化 → 使用 `AIBaseNode`
- 耗时推理（> 1s）→ 使用 `AsyncAINode`

---

## 2. 快速开始

### 2.1 创建第一个 AI 节点

```python
from user_plugins.base_nodes import AIBaseNode


class MyFirstAINode(AIBaseNode):
    """我的第一个 AI 节点"""
    
    __identifier__ = 'my_ai_plugin'
    NODE_NAME = '我的 AI 节点'
    
    def __init__(self):
        super().__init__()
        
        # 设置资源等级
        self.resource_level = "light"
        
        # 定义端口
        self.add_input('输入图像')
        self.add_output('输出结果')
    
    def process(self, inputs):
        # Step 1: 检查依赖
        if not self.check_dependencies(['ultralytics']):
            return None
        
        # Step 2: 获取输入
        image = inputs.get('输入图像')
        
        # Step 3: 执行推理
        # ... 你的代码 ...
        
        # Step 4: 返回结果
        return {'输出结果': result}
```

### 2.2 在 plugin.json 中注册

```json
{
  "name": "my_ai_plugin",
  "category_group": "识别分类",
  "nodes": [{
    "class": "MyFirstAINode",
    "display_name": "我的 AI 节点",
    "category": "AI推理",
    "resource_level": "light"
  }]
}
```

---

## 3. AIBaseNode 使用指南

### 3.1 依赖检查

```python
def process(self, inputs):
    # 检查单个依赖
    if not self.check_dependencies(['ultralytics']):
        return None
    
    # 检查多个依赖
    if not self.check_dependencies(['torch', 'ultralytics', 'opencv-python']):
        return None
    
    # 继续处理...
```

**输出示例**：
```
❌ 缺少依赖: torch, ultralytics
💡 安装命令: pip install torch ultralytics
📖 详细说明: 请查看插件 README.md 中的安装指南
```

### 3.2 硬件检查

```python
def __init__(self):
    super().__init__()
    
    # 设置硬件要求
    self.hardware_requirements = {
        'cpu_cores': 8,           # CPU 核心数
        'memory_gb': 16,          # 内存 (GB)
        'gpu_required': True,     # 是否需要 GPU
        'gpu_memory_gb': 8        # GPU 显存 (GB)
    }

def process(self, inputs):
    # 检查硬件
    if not self.check_hardware():
        self.log_warning("建议：在配备 GPU 的工作站上运行")
        return None
    
    # 继续处理...
```

**输出示例**：
```
✅ GPU 可用: NVIDIA GeForce RTX 3060 (12.0GB)
```

或

```
❌ GPU 显存不足 (6.0GB < 8GB)
💡 需要: 8GB+ 显存的 NVIDIA GPU
```

### 3.3 模型缓存

```python
def process(self, inputs):
    # 加载模型（自动缓存）
    model = self.get_or_load_model(
        'yolov8n',  # 模型标识符
        lambda: YOLO('yolov8n.pt')  # 加载函数
    )
    
    # 第二次调用时会直接使用缓存
    # 输出: ✅ 使用缓存模型: yolov8n
    
    # 执行推理
    result = model.predict(inputs['输入图像'])
    
    return {'输出结果': result}
```

**清理缓存**：
```python
# 清理指定模型
self.clear_model_cache('yolov8n')

# 清理所有缓存
self.clear_model_cache()
```

### 3.4 日志输出

```python
def process(self, inputs):
    self.log_info("开始处理")
    self.log_warning("警告信息")
    self.log_error("错误信息")
    self.log_success("处理完成")
```

**输出示例**：
```
ℹ️ [YOLO 目标检测] 开始处理
⚠️ [YOLO 目标检测] 警告信息
❌ [YOLO 目标检测] 错误信息
✅ [YOLO 目标检测] 处理完成
```

---

## 4. AsyncAINode 使用指南

### 4.1 基本用法

```python
from user_plugins.base_nodes import AsyncAINode


class AsyncYOLONode(AsyncAINode):
    """异步 YOLO 节点"""
    
    __identifier__ = 'yolo_vision'
    NODE_NAME = 'YOLO 异步检测'
    
    def __init__(self):
        super().__init__()
        self.add_input('输入图像')
        self.add_output('输出结果')
        self.add_output('处理状态')
    
    def process(self, inputs):
        """同步处理方法（被线程池调用）"""
        # 检查依赖
        if not self.check_dependencies(['ultralytics']):
            return None
        
        # 执行推理（耗时操作）
        model = self.get_or_load_model('yolov8n', ...)
        result = model.predict(inputs['输入图像'])
        
        self.log_success("异步处理完成")
        return {'output': result}
```

### 4.2 在主窗口中调用

```python
# 获取节点
node = graph.get_node_by_id('node_id')

# 启动异步任务
if isinstance(node, AsyncAINode):
    node.start_async_process(inputs)
    
    # 定期检查结果（如在定时器中）
    def check_result():
        if not node.is_processing():
            result = node.get_async_result()
            if result:
                # 处理结果
                print(f"结果: {result}")
```

### 4.3 取消任务

```python
# 取消正在执行的任务
node.cancel_async_process()

# 清理资源（程序退出时）
node.cleanup()
```

---

## 5. 最佳实践

### 5.1 选择合适的基类

```python
# 场景 1: 轻量级推理（< 1s）
class FastInferenceNode(AIBaseNode):
    resource_level = "light"

# 场景 2: 重量级训练（需要 GPU）
class TrainingNode(AIBaseNode):
    resource_level = "heavy"
    hardware_requirements = {
        'gpu_required': True,
        'gpu_memory_gb': 8
    }

# 场景 3: 耗时推理（> 1s，避免阻塞 UI）
class SlowInferenceNode(AsyncAINode):
    resource_level = "medium"
```

### 5.2 完整的异常处理

```python
def process(self, inputs):
    try:
        # Step 1: 检查依赖
        if not self.check_dependencies(['package']):
            return None
        
        # Step 2: 检查硬件
        if not self.check_hardware():
            return None
        
        # Step 3: 获取输入
        image = inputs.get('输入图像')
        if image is None:
            self.log_error("未接收到输入图像")
            return None
        
        # Step 4: 执行推理
        model = self.get_or_load_model(...)
        result = model.predict(image)
        
        # Step 5: 返回结果
        self.log_success("处理完成")
        return {'输出结果': result}
        
    except Exception as e:
        self.log_error(f"处理失败: {e}")
        import traceback
        traceback.print_exc()
        return None
```

### 5.3 清晰的文档字符串

```python
class YOLODetectNode(AIBaseNode):
    """
    YOLO 目标检测节点
    
    功能：
    - 支持 yolov8n/s/m/l/x 模型
    - 输出标注图像和检测结果
    - 支持 CPU/GPU 推理
    
    硬件要求：
    - CPU: 2 核心
    - 内存: 2GB
    - GPU: 可选（有则更快）
    
    使用方法：
    1. 拖拽节点到画布
    2. 连接图像输入
    3. 选择模型类型
    4. 运行查看结果
    
    示例：
        图像加载 → YOLO检测 → 图像显示
    """
```

### 5.4 语义化端口命名

```python
# ✅ 推荐
self.add_input('输入图像')
self.add_output('输出标注图像')
self.add_output('检测结果(JSON)')

# ❌ 避免
self.add_input('img_in')
self.add_output('out1')
self.add_output('out2')
```

---

## 6. 常见问题

### Q1: 如何调试依赖检查？

**A**: 使用 `check_dependencies` 的返回值：

```python
if not self.check_dependencies(['ultralytics']):
    print("依赖缺失，节点已跳过")
    return None
```

### Q2: 模型缓存何时失效？

**A**: 缓存在以下情况失效：
- 程序重启
- 手动调用 `clear_model_cache()`
- 修改了模型文件路径

### Q3: 异步节点如何更新 UI？

**A**: 在主窗口中使用定时器定期检查：

```python
# 在 MainWindow 中
def update_async_results(self):
    for node in self.current_graph.all_nodes():
        if isinstance(node, AsyncAINode) and not node.is_processing():
            result = node.get_async_result()
            if result:
                # 更新 UI
                self.update_node_display(node, result)
```

### Q4: 如何处理 GPU 不可用的情况？

**A**: 使用硬件检查并提供回退方案：

```python
def process(self, inputs):
    if not self.check_hardware():
        # 回退到 CPU
        self.log_warning("GPU 不可用，切换到 CPU 模式（速度较慢）")
        device = 'cpu'
    else:
        device = 'cuda'
    
    model = YOLO('yolov8n.pt')
    result = model.predict(inputs['image'], device=device)
    return {'output': result}
```

---

## 📚 相关资源

- [AI 模块资源隔离设计规范](../../docs/AI_MODULE_RESOURCE_ISOLATION.md)
- [节点开发示例](../ai_node_examples.py)
- [单元测试](../../tests/test_ai_base_nodes.py)

---

**最后更新**: 2026-04-26  
**维护者**: 项目开发团队
