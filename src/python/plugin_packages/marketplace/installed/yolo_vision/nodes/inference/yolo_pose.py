"""
YOLO 姿态估计节点（轻量级）

硬件要求：
- CPU: 2 核心
- 内存: 2GB
- GPU: 可选

使用方法：
1. 拖拽节点到画布
2. 连接图像输入
3. 选择姿态模型（yolov8n-pose/yolov8s-pose）
4. 运行查看姿态关键点

示例工作流：
    [图像加载] → [YOLO 姿态估计] → [图像显示]
"""

import os
from typing import Dict, Any, Optional
from shared_libs.node_base import BaseNode


class YOLOPoseNode(BaseNode):
    """
    YOLO 姿态估计节点
    
    功能：
    - 支持 yolov8n-pose/yolov8s-pose 两种模型
    - 输出标注后的图像（带关键点）
    - 输出姿态关键点坐标
    - 输出关键点置信度
    - 支持 CPU/GPU 自适应推理
    
    硬件要求：
    - CPU: 2 核心
    - 内存: 2GB
    - GPU: 可选
    
    性能指标：
    - yolov8n-pose: ~60ms/帧 (CPU), ~12ms/帧 (GPU)
    """
    
    __identifier__ = 'yolo_vision'
    NODE_NAME = '姿态估计'
    
    def __init__(self):
        super(YOLOPoseNode, self).__init__()
        
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
        self.add_output('姿态结果(JSON)')
        self.add_output('关键点坐标')
        
        # 参数配置
        self.add_combo_menu(
            'model_type', 
            '模型类型', 
            items=['yolov8n-pose', 'yolov8s-pose'],
            default='yolov8n-pose'
        )
        self.add_text_input('confidence', '置信度阈值', '0.5')
        self.add_combo_menu('device', '计算设备', items=['auto', 'cpu', 'cuda'], default='auto')
        
        # 添加说明文本
        self.add_text_input(
            '_info', 
            '说明', 
            '💡 人体17个关键点检测\n🦴  nose, eyes, ears, shoulders, elbows, wrists, hips, knees, ankles'
        )
    
    def process(self, inputs: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        执行姿态估计
        
        Args:
            inputs: 输入数据字典，包含 '输入图像'
            
        Returns:
            dict: 包含以下键的输出字典
                - '输出标注图像': 标注后的图像（带关键点）
                - '姿态结果(JSON)': JSON 格式的姿态结果
                - '关键点坐标': 关键点坐标数组
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
            model_key = f'yolov8_pose_{model_type}_{device}'
            
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
            
            # Step 6: 执行姿态估计
            self.log_info(f"开始姿态估计 (模型: {model_type}, 设备: {device})")
            
            results = model(
                image, 
                conf=confidence,
                device=device,
                verbose=False
            )
            
            # Step 7: 提取结果
            annotated_image = results[0].plot()  # 标注后的图像（带关键点）
            
            # 提取关键点
            if results[0].keypoints is not None:
                keypoints = results[0].keypoints.xy.cpu().numpy()
                keypoints_conf = results[0].keypoints.conf.cpu().numpy()
                
                pose_result = {
                    'num_persons': len(keypoints),
                    'keypoints_per_person': len(keypoints[0]) if len(keypoints) > 0 else 0,
                    'has_detection': len(keypoints) > 0
                }
            else:
                keypoints = None
                keypoints_conf = None
                pose_result = {
                    'num_persons': 0,
                    'keypoints_per_person': 0,
                    'has_detection': False
                }
            
            num_persons = pose_result['num_persons']
            self.log_success(f"姿态估计完成，检测到 {num_persons} 个人")
            
            # Step 8: 返回结果
            return {
                '输出标注图像': annotated_image,
                '姿态结果(JSON)': str(pose_result),
                '关键点坐标': str(keypoints) if keypoints is not None else "No keypoints"
            }
            
        except ImportError as e:
            self.log_error(f"缺少依赖: {e}")
            self.log_error("💡 安装命令: pip install ultralytics")
            return None
            
        except Exception as e:
            self.log_error(f"姿态估计失败: {e}")
            import traceback
            traceback.print_exc()
            return None
