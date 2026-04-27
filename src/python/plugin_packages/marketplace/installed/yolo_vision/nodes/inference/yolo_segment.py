"""
YOLO 实例分割节点（轻量级）

硬件要求：
- CPU: 2 核心
- 内存: 2GB
- GPU: 可选

使用方法：
1. 拖拽节点到画布
2. 连接图像输入
3. 选择分割模型（yolov8n-seg/yolov8s-seg）
4. 运行查看分割结果

示例工作流：
    [图像加载] → [YOLO 实例分割] → [图像显示]
"""

import os
from typing import Dict, Any, Optional
from user_plugins.base_nodes import AIBaseNode


class YOLOSegmentNode(AIBaseNode):
    """
    YOLO 实例分割节点
    
    功能：
    - 支持 yolov8n-seg/yolov8s-seg 两种模型
    - 输出标注后的图像（带掩码）
    - 输出分割结果（JSON 格式）
    - 输出掩码数据
    - 支持 CPU/GPU 自适应推理
    
    硬件要求：
    - CPU: 2 核心
    - 内存: 2GB
    - GPU: 可选
    
    性能指标：
    - yolov8n-seg: ~80ms/帧 (CPU), ~15ms/帧 (GPU)
    """
    
    __identifier__ = 'yolo_vision'
    NODE_NAME = 'YOLO 实例分割'
    
    def __init__(self):
        super(YOLOSegmentNode, self).__init__()
        
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
        self.add_output('输出标注图像')
        self.add_output('分割结果(JSON)')
        self.add_output('掩码数据')
        
        # 参数配置
        self.add_combo_menu(
            'model_type', 
            '模型类型', 
            items=['yolov8n-seg', 'yolov8s-seg'],
            default='yolov8n-seg'
        )
        self.add_text_input('confidence', '置信度阈值', '0.5')
        self.add_combo_menu('device', '计算设备', items=['auto', 'cpu', 'cuda'], default='auto')
        
        # 添加说明文本
        self.add_text_input(
            '_info', 
            '说明', 
            '💡 像素级物体分割\n🎨 输出带彩色掩码的图像'
        )
    
    def process(self, inputs: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        执行实例分割
        
        Args:
            inputs: 输入数据字典，包含 '输入图像'
            
        Returns:
            dict: 包含以下键的输出字典
                - '输出标注图像': 标注后的图像（带掩码）
                - '分割结果(JSON)': JSON 格式的分割结果
                - '掩码数据': 掩码数组
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
            confidence = float(self.get_property('confidence'))
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
            model_key = f'yolov8_seg_{model_type}_{device}'
            
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
            
            # Step 6: 执行分割
            self.log_info(f"开始分割 (模型: {model_type}, 设备: {device})")
            
            results = model(
                image, 
                conf=confidence,
                device=device,
                verbose=False
            )
            
            # Step 7: 提取结果
            annotated_image = results[0].plot()  # 标注后的图像（带掩码）
            
            # 提取掩码数据
            if results[0].masks is not None:
                masks = results[0].masks.data.cpu().numpy()
                masks_json = str(masks.shape)  # 简化为形状信息
            else:
                masks = None
                masks_json = "No masks detected"
            
            # 构建 JSON 结果
            segmentation_result = {
                'num_objects': len(results[0].boxes) if results[0].boxes is not None else 0,
                'has_masks': results[0].masks is not None
            }
            
            num_objects = segmentation_result['num_objects']
            self.log_success(f"分割完成，发现 {num_objects} 个对象")
            
            # Step 8: 返回结果
            return {
                '输出标注图像': annotated_image,
                '分割结果(JSON)': str(segmentation_result),
                '掩码数据': masks_json
            }
            
        except ImportError as e:
            self.log_error(f"缺少依赖: {e}")
            self.log_error("💡 安装命令: pip install ultralytics")
            return None
            
        except Exception as e:
            self.log_error(f"分割失败: {e}")
            import traceback
            traceback.print_exc()
            return None
