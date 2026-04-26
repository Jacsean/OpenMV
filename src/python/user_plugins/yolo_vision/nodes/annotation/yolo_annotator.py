"""
YOLO 标注辅助节点（中量级）

硬件要求：
- CPU: 4+ 核心
- 内存: 8GB+
- GPU: 可选（用于加速预标注）
- 存储: 充足的磁盘空间用于数据集和标注文件

警告：
- 此节点适合在办公室工作站或开发机上使用
- 工厂现场的低配工控机可以运行，但速度较慢
- 建议配合图形界面使用，便于人工修正标注结果

使用方法：
1. 准备待标注的图像文件夹
2. 拖拽节点到画布
3. 连接图像文件夹路径
4. 选择预标注模型（可选）
5. 设置类别名称
6. 运行自动标注
7. 人工修正标注结果
8. 导出 YOLO 格式数据集

示例工作流：
    [图像文件夹] → [YOLO 标注辅助] → [YOLO 格式数据集] + [标注报告]
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from user_plugins.base_nodes import AIBaseNode


class YOLOAnnotatorNode(AIBaseNode):
    """
    YOLO 标注辅助节点
    
    功能：
    - 支持批量图像自动预标注（使用 YOLO 模型）
    - 生成 Labelme 格式的 JSON 标注文件
    - 自动转换为 YOLO 格式（txt 标签文件）
    - 支持数据集划分（训练集/验证集/测试集）
    - 生成 dataset.yaml 配置文件
    - 提供标注统计报告
    
    硬件要求：
    - CPU: 4+ 核心
    - 内存: 8GB+
    - GPU: 可选（推荐用于加速预标注）
    
    性能指标：
    - 无 GPU: ~100ms/张图像（yolov8n）
    - 有 GPU: ~20ms/张图像（yolov8n）
    """
    
    __identifier__ = 'yolo_vision'
    NODE_NAME = 'YOLO 标注辅助'
    
    def __init__(self):
        super(YOLOAnnotatorNode, self).__init__()
        
        # 设置资源等级
        self.resource_level = "medium"
        
        # 设置硬件要求
        self.hardware_requirements = {
            'cpu_cores': 4,
            'memory_gb': 8,
            'gpu_required': False,
            'gpu_memory_gb': 0
        }
        
        # 输入端口
        self.add_input('图像文件夹路径')
        
        # 输出端口
        self.add_output('YOLO 数据集路径')
        self.add_output('dataset.yaml')
        self.add_output('标注报告(JSON)')
        
        # 标注参数
        self.add_text_input('classes', '类别名称(逗号分隔)', 'person,car,bicycle')
        self.add_combo_menu(
            'pretrain_model', 
            '预标注模型', 
            items=['无', 'yolov8n', 'yolov8s', 'yolov8m'],
            default='yolov8n'
        )
        self.add_text_input('conf_threshold', '置信度阈值', '0.5')
        self.add_text_input('output_dir', '输出目录', './annotated_dataset')
        
        # 数据集划分
        self.add_text_input('train_ratio', '训练集比例', '0.7')
        self.add_text_input('val_ratio', '验证集比例', '0.2')
        self.add_text_input('test_ratio', '测试集比例', '0.1')
        
        # 高级选项
        self.add_text_input('img_size', '图像尺寸', '640')
        self.add_combo_menu(
            'annotation_format', 
            '标注格式', 
            items=['yolo', 'labelme', 'both'],
            default='both'
        )
        
        # 硬件提示
        self.add_text_input(
            '_hardware_note', 
            '硬件建议', 
            '💡 推荐使用 GPU 加速预标注\n   CPU 也可运行，但速度较慢'
        )
    
    def check_hardware_detailed(self) -> tuple:
        """
        详细的硬件检查
        
        Returns:
            tuple: (是否通过, 消息)
        """
        try:
            import torch
            has_torch = True
        except ImportError:
            has_torch = False
        
        # 检查 ultralytics
        try:
            import ultralytics
            has_ultralytics = True
        except ImportError:
            return False, "❌ 未安装 ultralytics，请先安装: pip install ultralytics"
        
        # GPU 检查（可选）
        if has_torch and torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            cuda_version = torch.version.cuda
            return True, f"✅ GPU 可用: {gpu_name} ({gpu_memory_gb:.1f}GB, CUDA {cuda_version}) - 预标注将加速"
        else:
            return True, "⚠️ 未检测到 GPU，将使用 CPU 进行预标注（速度较慢）\n💡 建议: 安装 CUDA 版本的 PyTorch 以加速"
    
    def generate_yolo_labels(self, image_path: str, detections: List[Dict], output_dir: str) -> str:
        """
        生成 YOLO 格式的标签文件
        
        Args:
            image_path: 图像文件路径
            detections: 检测结果列表
            output_dir: 标签文件输出目录
            
        Returns:
            str: 标签文件路径
        """
        from PIL import Image
        
        # 获取图像尺寸
        img = Image.open(image_path)
        img_width, img_height = img.size
        
        # 生成标签文件名
        image_name = Path(image_path).stem
        label_path = os.path.join(output_dir, f"{image_name}.txt")
        
        # 写入 YOLO 格式标签
        with open(label_path, 'w') as f:
            for det in detections:
                class_id = det['class_id']
                x_center = det['x_center']
                y_center = det['y_center']
                width = det['width']
                height = det['height']
                
                # YOLO 格式: class_id x_center y_center width height (归一化)
                f.write(f"{class_id} {x_center:.6f} {y_center:.6f} {width:.6f} {height:.6f}\n")
        
        return label_path
    
    def generate_labelme_json(self, image_path: str, detections: List[Dict], classes: List[str]) -> Dict:
        """
        生成 Labelme 格式的 JSON 标注
        
        Args:
            image_path: 图像文件路径
            detections: 检测结果列表
            classes: 类别名称列表
            
        Returns:
            dict: Labelme 格式的标注数据
        """
        from PIL import Image
        import base64
        
        # 读取图像并编码为 base64
        with open(image_path, 'rb') as f:
            image_data = base64.b64encode(f.read()).decode('utf-8')
        
        # 获取图像尺寸
        img = Image.open(image_path)
        img_width, img_height = img.size
        
        # 构建 shapes
        shapes = []
        for det in detections:
            class_name = classes[det['class_id']]
            
            # 从归一化坐标转换回像素坐标
            x_center = det['x_center'] * img_width
            y_center = det['y_center'] * img_height
            width = det['width'] * img_width
            height = det['height'] * img_height
            
            # 计算边界框的左上角和右下角
            x_min = x_center - width / 2
            y_min = y_center - height / 2
            x_max = x_center + width / 2
            y_max = y_center + height / 2
            
            shape = {
                "label": class_name,
                "points": [
                    [float(x_min), float(y_min)],
                    [float(x_max), float(y_max)]
                ],
                "group_id": None,
                "description": "",
                "shape_type": "rectangle",
                "flags": {}
            }
            shapes.append(shape)
        
        # 构建完整的 Labelme JSON
        labelme_data = {
            "version": "5.0.0",
            "flags": {},
            "shapes": shapes,
            "imagePath": Path(image_path).name,
            "imageData": image_data,
            "imageHeight": img_height,
            "imageWidth": img_width
        }
        
        return labelme_data
    
    def process(self, inputs: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        执行标注流程
        
        Args:
            inputs: 输入数据字典，包含 '图像文件夹路径'
            
        Returns:
            dict: 包含以下键的输出字典
                - 'YOLO 数据集路径': YOLO 格式数据集根目录
                - 'dataset.yaml': 数据集配置文件路径
                - '标注报告(JSON)': JSON 格式的标注统计报告
            失败时返回 None
        """
        try:
            # Step 1: 检查依赖
            if not self.check_dependencies(['ultralytics']):
                return None
            
            # Step 2: 硬件检查
            hardware_ok, hardware_msg = self.check_hardware_detailed()
            self.log_info(hardware_msg)
            
            # Step 3: 获取输入
            image_folder = inputs.get('图像文件夹路径') if inputs else None
            if not image_folder:
                self.log_error("未接收到图像文件夹路径")
                return None
            
            if not os.path.exists(image_folder):
                self.log_error(f"图像文件夹不存在: {image_folder}")
                return None
            
            # Step 4: 获取参数
            classes_str = self.get_property('classes')
            classes = [c.strip() for c in classes_str.split(',')]
            pretrain_model = self.get_property('pretrain_model')
            conf_threshold = float(self.get_property('conf_threshold'))
            output_dir = self.get_property('output_dir')
            train_ratio = float(self.get_property('train_ratio'))
            val_ratio = float(self.get_property('val_ratio'))
            test_ratio = float(self.get_property('test_ratio'))
            img_size = int(self.get_property('img_size'))
            annotation_format = self.get_property('annotation_format')
            
            # 验证比例
            if abs(train_ratio + val_ratio + test_ratio - 1.0) > 0.01:
                self.log_warning(f"⚠️ 数据集比例总和不为 1.0 ({train_ratio}+{val_ratio}+{test_ratio})")
                self.log_warning("   将自动调整比例为: 0.7/0.2/0.1")
                train_ratio, val_ratio, test_ratio = 0.7, 0.2, 0.1
            
            # Step 5: 创建输出目录结构
            self.log_info(f"📁 创建数据集目录结构...")
            os.makedirs(output_dir, exist_ok=True)
            
            # YOLO 格式目录
            images_dir = os.path.join(output_dir, 'images')
            labels_dir = os.path.join(output_dir, 'labels')
            
            train_img_dir = os.path.join(images_dir, 'train')
            val_img_dir = os.path.join(images_dir, 'val')
            test_img_dir = os.path.join(images_dir, 'test')
            
            train_lbl_dir = os.path.join(labels_dir, 'train')
            val_lbl_dir = os.path.join(labels_dir, 'val')
            test_lbl_dir = os.path.join(labels_dir, 'test')
            
            for dir_path in [train_img_dir, val_img_dir, test_img_dir,
                           train_lbl_dir, val_lbl_dir, test_lbl_dir]:
                os.makedirs(dir_path, exist_ok=True)
            
            # Labelme 格式目录（如果需要）
            if annotation_format in ['labelme', 'both']:
                labelme_dir = os.path.join(output_dir, 'labelme_annotations')
                os.makedirs(labelme_dir, exist_ok=True)
            
            # Step 6: 加载预标注模型（如果启用）
            model = None
            if pretrain_model != '无':
                self.log_info(f"🔄 加载预标注模型: {pretrain_model}")
                from ultralytics import YOLO
                model = YOLO(f'{pretrain_model}.pt')
            
            # Step 7: 扫描图像文件
            self.log_info(f"🔍 扫描图像文件夹: {image_folder}")
            image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
            image_files = []
            
            for ext in image_extensions:
                image_files.extend(Path(image_folder).glob(f'*{ext}'))
                image_files.extend(Path(image_folder).glob(f'*{ext.upper()}'))
            
            image_files = sorted(list(set(image_files)))
            total_images = len(image_files)
            
            if total_images == 0:
                self.log_error(f"❌ 未在文件夹中找到图像文件")
                return None
            
            self.log_info(f"   找到 {total_images} 张图像")
            
            # Step 8: 划分数据集
            import random
            random.shuffle(image_files)
            
            train_count = int(total_images * train_ratio)
            val_count = int(total_images * val_ratio)
            test_count = total_images - train_count - val_count
            
            train_files = image_files[:train_count]
            val_files = image_files[train_count:train_count + val_count]
            test_files = image_files[train_count + val_count:]
            
            self.log_info(f"   训练集: {len(train_files)} 张")
            self.log_info(f"   验证集: {len(val_files)} 张")
            self.log_info(f"   测试集: {len(test_files)} 张")
            
            # Step 9: 处理每张图像
            stats = {
                'total_images': total_images,
                'total_annotations': 0,
                'class_distribution': {cls: 0 for cls in classes},
                'processed': 0,
                'failed': 0
            }
            
            def process_image_set(image_list, split_name):
                """处理一个数据集子集"""
                img_dir = eval(f'{split_name}_img_dir')
                lbl_dir = eval(f'{split_name}_lbl_dir')
                
                for img_path in image_list:
                    try:
                        # 复制图像到对应目录
                        import shutil
                        dest_img_path = os.path.join(img_dir, img_path.name)
                        shutil.copy2(str(img_path), dest_img_path)
                        
                        detections = []
                        
                        # 如果有模型，进行预标注
                        if model is not None:
                            results = model(str(img_path), conf=conf_threshold, verbose=False)
                            
                            for result in results:
                                boxes = result.boxes
                                if boxes is not None:
                                    for box in boxes:
                                        # 获取边界框坐标 (xyxy 格式)
                                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                                        class_id = int(box.cls[0].cpu().numpy())
                                        
                                        # 转换为 YOLO 格式 (x_center, y_center, width, height)
                                        img_w = result.orig_shape[1]
                                        img_h = result.orig_shape[0]
                                        
                                        x_center = ((x1 + x2) / 2) / img_w
                                        y_center = ((y1 + y2) / 2) / img_h
                                        width = (x2 - x1) / img_w
                                        height = (y2 - y1) / img_h
                                        
                                        detections.append({
                                            'class_id': class_id,
                                            'x_center': x_center,
                                            'y_center': y_center,
                                            'width': width,
                                            'height': height
                                        })
                                        
                                        # 更新统计
                                        if class_id < len(classes):
                                            stats['class_distribution'][classes[class_id]] += 1
                        
                        # 生成 YOLO 格式标签
                        if detections or annotation_format == 'yolo':
                            label_path = self.generate_yolo_labels(
                                str(img_path), detections, lbl_dir
                            )
                            stats['total_annotations'] += len(detections)
                        
                        # 生成 Labelme 格式标注（如果需要）
                        if annotation_format in ['labelme', 'both'] and detections:
                            labelme_data = self.generate_labelme_json(
                                str(img_path), detections, classes
                            )
                            labelme_path = os.path.join(
                                labelme_dir, f"{img_path.stem}.json"
                            )
                            with open(labelme_path, 'w', encoding='utf-8') as f:
                                json.dump(labelme_data, f, ensure_ascii=False, indent=2)
                        
                        stats['processed'] += 1
                        
                    except Exception as e:
                        self.log_warning(f"⚠️ 处理图像失败 {img_path.name}: {e}")
                        stats['failed'] += 1
            
            # 处理训练集
            self.log_info("📝 处理训练集...")
            process_image_set(train_files, 'train')
            
            # 处理验证集
            self.log_info("📝 处理验证集...")
            process_image_set(val_files, 'val')
            
            # 处理测试集
            if test_files:
                self.log_info("📝 处理测试集...")
                process_image_set(test_files, 'test')
            
            # Step 10: 生成 dataset.yaml
            self.log_info("📄 生成 dataset.yaml...")
            dataset_yaml_path = os.path.join(output_dir, 'dataset.yaml')
            
            yaml_content = f"""# YOLO 数据集配置文件
# 自动生成于: {Path(__file__).parent.parent.parent}

path: {os.path.abspath(output_dir)}  # 数据集根目录
train: images/train  # 训练集图像目录
val: images/val      # 验证集图像目录
test: images/test    # 测试集图像目录（可选）

# 类别定义
nc: {len(classes)}  # 类别数量
names: {classes}     # 类别名称列表

# 数据集统计
# 总图像数: {total_images}
# 训练集: {len(train_files)}
# 验证集: {len(val_files)}
# 测试集: {len(test_files)}
"""
            
            with open(dataset_yaml_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            # Step 11: 生成标注报告
            report = {
                'dataset_path': output_dir,
                'total_images': total_images,
                'split': {
                    'train': len(train_files),
                    'val': len(val_files),
                    'test': len(test_files)
                },
                'total_annotations': stats['total_annotations'],
                'class_distribution': stats['class_distribution'],
                'processed': stats['processed'],
                'failed': stats['failed'],
                'annotation_format': annotation_format,
                'pretrain_model': pretrain_model,
                'confidence_threshold': conf_threshold
            }
            
            report_log_lines = [
                f"标注完成！",
                f"数据集路径: {output_dir}",
                f"总图像数: {total_images}",
                f"  - 训练集: {len(train_files)}",
                f"  - 验证集: {len(val_files)}",
                f"  - 测试集: {len(test_files)}",
                f"",
                f"标注统计:",
                f"  总标注数: {stats['total_annotations']}",
                f"  成功处理: {stats['processed']}",
                f"  失败: {stats['failed']}",
                f"",
                f"类别分布:"
            ]
            
            for cls_name, count in stats['class_distribution'].items():
                report_log_lines.append(f"  {cls_name}: {count}")
            
            report_log = '\n'.join(report_log_lines)
            
            self.log_success(f"标注完成！数据集保存至: {output_dir}")
            
            # Step 12: 返回结果
            return {
                'YOLO 数据集路径': output_dir,
                'dataset.yaml': dataset_yaml_path,
                '标注报告(JSON)': str(report)
            }
            
        except ImportError as e:
            self.log_error(f"缺少依赖: {e}")
            self.log_error("💡 安装命令: pip install ultralytics Pillow")
            return None
            
        except Exception as e:
            self.log_error(f"标注失败: {e}")
            import traceback
            traceback.print_exc()
            return None
