"""
YOLO 图像分类节点（轻量级）

硬件要求：
- CPU: 2 核心
- 内存: 2GB
- GPU: 可选

使用方法：
1. 拖拽节点到画布
2. 连接图像输入
3. 选择分类模型（yolov8n-cls/yolov8s-cls）
4. 运行查看分类结果

示例工作流：
    [图像加载] → [YOLO 图像分类] → [文本显示]
"""

import os
from typing import Dict, Any, Optional
from user_plugins.base_nodes import AIBaseNode


class YOLOClassifyNode(AIBaseNode):
    """
    YOLO 图像分类节点
    
    功能：
    - 支持 yolov8n-cls/yolov8s-cls 两种模型
    - 输出分类结果（类别名称和置信度）
    - 支持 Top-K 分类结果
    - 支持 CPU/GPU 自适应推理
    
    硬件要求：
    - CPU: 2 核心
    - 内存: 2GB
    - GPU: 可选
    
    性能指标：
    - yolov8n-cls: ~30ms/帧 (CPU), ~5ms/帧 (GPU)
    """
    
    __identifier__ = 'yolo_vision'
    NODE_NAME = 'YOLO 图像分类'
    
    def __init__(self):
        super(YOLOClassifyNode, self).__init__()
        
        # 设置资源等级
        self.resource_level = "light"
        
        # 设置硬件要求
        self.hardware_requirements = {
            'cpu_cores': 2,
            'memory_gb': 2,
            'gpu_required': False,
            'gpu_memory_gb': 0
        }
        
        # 输入端口
        self.add_input('输入图像')
        
        # 输出端口
        self.add_output('输出图像')  # 传递原始图像
        self.add_output('分类结果(JSON)')
        self.add_output('类别名称')
        self.add_output('置信度')
        
        # 参数配置
        self.add_combo_menu(
            'model_type', 
            '模型类型', 
            items=['yolov8n-cls', 'yolov8s-cls'],
            default='yolov8n-cls'
        )
        self.add_text_input('top_k', 'Top-K 结果数', '5')
        self.add_combo_menu('device', '计算设备', items=['auto', 'cpu', 'cuda'], default='auto')
        
        # 添加说明文本
        self.add_text_input(
            '_info', 
            '说明', 
            '💡 基于 ImageNet 1000 类训练\n📊 输出 Top-K 分类结果'
        )
    
    def process(self, inputs: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        执行图像分类
        
        Args:
            inputs: 输入数据字典，包含 '输入图像'
            
        Returns:
            dict: 包含以下键的输出字典
                - '输出图像': 原始图像（传递）
                - '分类结果(JSON)': JSON 格式的分类结果
                - '类别名称': 最高置信度的类别名称
                - '置信度': 最高置信度值
            失败时返回 None
        """
        try:
            # Step 1: 检查依赖
            if not self.check_dependencies(['ultralytics']):
                return None
            
            # Step 2: 获取输入
            image = inputs.get('输入图像') if inputs else None
            if image is None:
                self.log_error("未接收到输入图像")
                return None
            
            # Step 3: 获取参数
            model_type = self.get_property('model_type')
            top_k = int(self.get_property('top_k'))
            device = self.get_property('device')
            
            # Step 4: 自动选择设备
            if device == 'auto':
                try:
                    import torch
                    if torch.cuda.is_available():
                        device = 'cuda'
                        self.log_info("检测到 GPU，使用 CUDA 加速")
                    else:
                        device = 'cpu'
                        self.log_info("未检测到 GPU，使用 CPU 模式")
                except ImportError:
                    device = 'cpu'
                    self.log_info("未安装 PyTorch，使用 CPU 模式")
            
            # Step 5: 加载模型（带缓存）
            model_key = f'yolov8_cls_{model_type}_{device}'
            
            def load_model():
                """模型加载函数"""
                from ultralytics import YOLO
                
                # 构建模型路径
                model_path = f'{model_type}.pt'
                
                # 检查本地 models 目录
                local_model_path = os.path.join(
                    os.path.dirname(__file__), 
                    '..', 
                    '..', 
                    'yolo_vision', 
                    'models', 
                    model_path
                )
                
                if os.path.exists(local_model_path):
                    self.log_info(f"使用本地模型: {local_model_path}")
                    return YOLO(local_model_path)
                else:
                    self.log_info(f"自动下载模型: {model_type}.pt")
                    return YOLO(model_path)
            
            model = self.get_or_load_model(model_key, load_model)
            
            # Step 6: 执行分类
            self.log_info(f"开始分类 (模型: {model_type}, 设备: {device})")
            
            results = model(
                image,
                device=device,
                verbose=False
            )
            
            # Step 7: 提取结果
            probs = results[0].probs
            
            # 获取 Top-K 结果
            top_indices = probs.top5 if hasattr(probs, 'top5') else probs.topk(min(top_k, len(probs)))
            top_names = [results[0].names[idx] for idx in top_indices]
            top_confidences = [float(probs.data[idx]) for idx in top_indices]
            
            # 构建 JSON 结果
            classification_result = {
                'top_k': top_k,
                'results': [
                    {
                        'rank': i + 1,
                        'class_name': name,
                        'confidence': conf
                    }
                    for i, (name, conf) in enumerate(zip(top_names, top_confidences))
                ]
            }
            
            # 最高置信度的类别
            best_class = top_names[0] if top_names else "Unknown"
            best_confidence = top_confidences[0] if top_confidences else 0.0
            
            self.log_success(f"分类完成: {best_class} ({best_confidence:.2%})")
            
            # Step 8: 返回结果
            return {
                '输出图像': image,
                '分类结果(JSON)': str(classification_result),
                '类别名称': best_class,
                '置信度': str(best_confidence)
            }
            
        except ImportError as e:
            self.log_error(f"缺少依赖: {e}")
            self.log_error("💡 安装命令: pip install ultralytics")
            return None
            
        except Exception as e:
            self.log_error(f"分类失败: {e}")
            import traceback
            traceback.print_exc()
            return None
