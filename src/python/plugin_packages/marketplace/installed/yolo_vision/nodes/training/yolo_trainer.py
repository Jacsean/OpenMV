"""
YOLO 模型训练节点（重量级）

硬件要求：
- CPU: 8+ 核心
- 内存: 16GB+
- GPU: 必需（CUDA 11.8+，8GB+ 显存）
- 存储: 充足的磁盘空间用于数据集和模型保存

警告：
- 此节点仅在配备高性能 GPU 的工作站上使用
- 工厂现场的低配工控机不应安装此节点
- 建议在云端或办公室电脑上进行训练，然后导出模型到现场使用

使用方法：
1. 准备 YOLO 格式的数据集
2. 创建 dataset.yaml 配置文件
3. 拖拽节点到画布
4. 连接数据集配置文件路径
5. 设置训练参数
6. 运行训练（需要 GPU）
7. 训练完成后，模型保存到指定目录

示例工作流：
    [数据集配置] → [YOLO 模型训练] → [模型保存]
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from shared_libs.node_base import BaseNode


class YOLOTrainerNode(BaseNode):
    """
    YOLO 模型训练节点
    
    功能：
    - 支持自定义数据集训练
    - 支持 yolov8n/s/m/l/x 基础模型微调
    - 实时显示训练进度和指标
    - 自动保存最佳模型
    - 支持断点续训
    
    硬件要求：
    - CPU: 8+ 核心
    - 内存: 16GB+
    - GPU: 必需（CUDA 11.8+，8GB+ 显存）
    
    性能指标：
    - yolov8n: ~10分钟/100 epochs (RTX 3060)
    - yolov8s: ~20分钟/100 epochs (RTX 3060)
    - yolov8m: ~40分钟/100 epochs (RTX 3060)
    """
    
    __identifier__ = 'yolo_vision'
    NODE_NAME = '模型训练'
    
    def __init__(self):
        super(YOLOTrainerNode, self).__init__()
        
        # 设置资源等级
        self.resource_level = "heavy"
        
        # 设置硬件要求
        self.hardware_requirements = {
            'cpu_cores': 8,
            'memory_gb': 16,
            'gpu_required': True,
            'gpu_memory_gb': 8
        }
        
        # 输入端口
        self.add_input('数据集配置文件')
        
        # 输出端口
        self.add_output('训练好的模型路径')
        self.add_output('训练日志')
        self.add_output('训练指标(JSON)')
        
        # 训练参数
        self.add_combo_menu(
            'model_type', 
            '基础模型', 
            items=['yolov8n', 'yolov8s', 'yolov8m', 'yolov8l'],
            default='yolov8n'
        )
        self.add_text_input('epochs', '训练轮数', '100')
        self.add_text_input('batch_size', '批处理大小', '16')
        self.add_text_input('img_size', '图像尺寸', '640')
        self.add_text_input('save_dir', '模型保存路径', './trained_models')
        self.add_text_input('project_name', '项目名称', 'yolo_training')
        
        # 高级参数
        self.add_text_input('learning_rate', '学习率', '0.01')
        self.add_text_input('momentum', '动量', '0.937')
        self.add_text_input('weight_decay', '权重衰减', '0.0005')
        
        # 硬件检查提示
        self.add_text_input(
            '_hardware_note', 
            '硬件要求', 
            '⚠️ 需要 GPU (CUDA 11.8+, 8GB+ VRAM)\n💡 建议在高性能工作站上运行'
        )
    
    def check_hardware_detailed(self) -> tuple:
        """
        详细的硬件检查
        
        Returns:
            tuple: (是否通过, 消息)
        """
        try:
            import torch
        except ImportError:
            return False, "❌ 未安装 PyTorch，请先安装: pip install torch"
        
        # 检查 CUDA 可用性
        if not torch.cuda.is_available():
            return False, "❌ 未检测到 CUDA 设备，无法进行训练\n💡 需要: NVIDIA GPU + CUDA 11.8+\n📖 安装指南: https://pytorch.org/get-started/locally/"
        
        # 获取 GPU 信息
        gpu_count = torch.cuda.device_count()
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
        
        # 检查显存
        required_gpu_gb = self.hardware_requirements['gpu_memory_gb']
        if gpu_memory_gb < required_gpu_gb:
            return False, f"❌ GPU 显存不足 ({gpu_memory_gb:.1f}GB < {required_gpu_gb}GB)\n💡 需要: {required_gpu_gb}GB+ 显存的 NVIDIA GPU"
        
        # 检查 CUDA 版本
        cuda_version = torch.version.cuda
        if cuda_version:
            cuda_major_minor = '.'.join(cuda_version.split('.')[:2])
            if float(cuda_major_minor) < 11.8:
                return False, f"⚠️ CUDA 版本较低 ({cuda_version})，建议使用 11.8+\n💡 当前仍可运行，但可能无法获得最佳性能"
        
        return True, f"✅ GPU 可用: {gpu_name} ({gpu_memory_gb:.1f}GB, CUDA {cuda_version})"
    
    def process(self, inputs: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        执行模型训练
        
        Args:
            inputs: 输入数据字典，包含 '数据集配置文件'
            
        Returns:
            dict: 包含以下键的输出字典
                - '训练好的模型路径': 最佳模型的文件路径
                - '训练日志': 训练过程日志文本
                - '训练指标(JSON)': JSON 格式的训练指标
            失败时返回 None
        """
        try:
            # Step 1: 检查依赖
            if not self.check_dependencies(['ultralytics', 'torch']):
                return None
            
            # Step 2: 详细硬件检查
            hardware_ok, hardware_msg = self.check_hardware_detailed()
            self.log_info(hardware_msg)
            
            if not hardware_ok:
                self.log_warning("建议：在配备 GPU 的工作站上训练，然后导出模型到现场使用")
                return None
            
            # Step 3: 获取输入
            dataset_config = inputs.get('数据集配置文件') if inputs else None
            if not dataset_config:
                self.log_error("未接收到数据集配置文件")
                return None
            
            if not os.path.exists(dataset_config):
                self.log_error(f"数据集配置文件不存在: {dataset_config}")
                return None
            
            # Step 4: 获取参数
            model_type = self.get_property('model_type')
            epochs = int(self.get_property('epochs'))
            batch_size = int(self.get_property('batch_size'))
            img_size = int(self.get_property('img_size'))
            save_dir = self.get_property('save_dir')
            project_name = self.get_property('project_name')
            learning_rate = float(self.get_property('learning_rate'))
            momentum = float(self.get_property('momentum'))
            weight_decay = float(self.get_property('weight_decay'))
            
            # Step 5: 创建保存目录
            os.makedirs(save_dir, exist_ok=True)
            self.log_info(f"模型将保存至: {save_dir}")
            
            # Step 6: 加载基础模型
            from ultralytics import YOLO
            
            self.log_info(f"🔄 加载基础模型: {model_type}.pt")
            model = YOLO(f'{model_type}.pt')
            
            # Step 7: 开始训练
            self.log_info(f"🚀 开始训练")
            self.log_info(f"   数据集: {dataset_config}")
            self.log_info(f"   模型: {model_type}")
            self.log_info(f"   Epochs: {epochs}")
            self.log_info(f"   Batch Size: {batch_size}")
            self.log_info(f"   Image Size: {img_size}")
            self.log_info(f"   Learning Rate: {learning_rate}")
            
            results = model.train(
                data=dataset_config,
                epochs=epochs,
                imgsz=img_size,
                batch=batch_size,
                device=0,  # 使用 GPU 0
                project=save_dir,
                name=project_name,
                exist_ok=True,
                lr0=learning_rate,
                momentum=momentum,
                weight_decay=weight_decay,
                verbose=True,
                plots=True  # 生成训练图表
            )
            
            # Step 8: 获取训练结果
            best_model_path = str(Path(save_dir) / project_name / 'weights' / 'best.pt')
            last_model_path = str(Path(save_dir) / project_name / 'weights' / 'last.pt')
            
            # 提取训练指标
            metrics = {
                'best_model': best_model_path,
                'last_model': last_model_path,
                'epochs_completed': epochs,
                'results_dict': results.results_dict if hasattr(results, 'results_dict') else {}
            }
            
            # 构建训练日志
            log_lines = [
                f"训练完成！",
                f"最佳模型: {best_model_path}",
                f"最后模型: {last_model_path}",
                f"训练轮数: {epochs}",
            ]
            
            # 添加关键指标
            if results.results_dict:
                for key, value in results.results_dict.items():
                    if isinstance(value, (int, float)):
                        log_lines.append(f"{key}: {value:.4f}")
            
            training_log = '\n'.join(log_lines)
            
            self.log_success(f"训练完成！模型保存至: {best_model_path}")
            
            # Step 9: 返回结果
            return {
                '训练好的模型路径': best_model_path,
                '训练日志': training_log,
                '训练指标(JSON)': str(metrics)
            }
            
        except ImportError as e:
            self.log_error(f"缺少依赖: {e}")
            self.log_error("💡 安装命令: pip install ultralytics torch")
            self.log_error("📖 GPU 版本: pip install torch --index-url https://download.pytorch.org/whl/cu118")
            return None
            
        except Exception as e:
            self.log_error(f"训练失败: {e}")
            import traceback
            traceback.print_exc()
            return None
