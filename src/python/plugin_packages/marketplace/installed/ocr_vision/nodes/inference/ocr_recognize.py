"""
OCR 文字识别节点（轻量级）

基于 PaddleOCR 实现高精度的中文/英文文字检测与识别。

硬件要求：
- CPU: 2+ 核心
- 内存: 4GB+
- GPU: 可选（推荐用于加速推理）
- 存储: 约 500MB（模型文件）

警告：
- 首次运行会自动下载模型文件（约 100MB）
- 建议在办公室工作站或云端进行初始化下载
- 工厂现场部署时需预装模型

使用方法：
1. 拖拽节点到画布
2. 连接输入图像
3. 选择语言类型（ch/en/korean/japan等）
4. 设置置信度阈值
5. 运行识别
6. 获取识别结果文本和坐标信息

示例工作流：
    [输入图像] → [OCR 文字识别] → [识别结果文本] + [检测框坐标]
"""

from ....base_nodes import AIBaseNode
import cv2
import numpy as np


class OCRTextRecognitionNode(AIBaseNode):
    """
    OCR 文字识别节点
    
    使用 PaddleOCR 进行通用文字检测与识别，支持：
    - 中英文混合识别
    - 80+ 语言支持
    - 高精度文本检测
    - 结构化输出（文本 + 坐标）
    """
    
    __identifier__ = 'ocr_vision'
    NODE_NAME = 'OCR 文字识别'
    
    # 资源等级声明
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 2,
        'memory_gb': 4,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(OCRTextRecognitionNode, self).__init__()
        
        # 输入端口
        self.add_input('输入图像', color=(100, 255, 100))
        
        # 输出端口
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_output('识别文本', color=(100, 200, 255))
        self.add_output('检测框坐标', color=(255, 200, 100))
        
        # 参数配置
        self.add_combo_menu('lang', '语言类型', 
                           items=['ch', 'en', 'korean', 'japan', 'german', 'french'],
                           tab='properties')
        self.set_property('lang', 'ch')
        
        self.add_text_input('det_db_thresh', '检测阈值(0-1)', tab='properties')
        self.set_property('det_db_thresh', '0.3')
        
        self.add_text_input('rec_batch_num', '识别批次大小', tab='properties')
        self.set_property('rec_batch_num', '6')
        
        self.add_checkbox('use_gpu', '使用 GPU 加速', tab='properties')
        self.set_property('use_gpu', False)
        
        self.add_checkbox('show_visualization', '显示可视化结果', tab='properties')
        self.set_property('show_visualization', True)
    
    def check_dependencies(self):
        """检查依赖库"""
        try:
            from paddleocr import PaddleOCR
            return True, "PaddleOCR 已安装"
        except ImportError:
            return False, "缺少依赖: pip install paddlepaddle>=2.4.0 paddleocr>=2.6.0"
    
    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: 输入图像
            
        Returns:
            dict: 包含输出图像、识别文本、检测框坐标
        """
        try:
            # Step 1: 检查依赖
            deps_ok, deps_msg = self.check_dependencies()
            if not deps_ok:
                self.log_error(f"依赖检查失败: {deps_msg}")
                return None
            
            # Step 2: 获取输入图像
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入图像")
                return None
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return None
            
            # Step 3: 读取参数
            lang = self.get_property('lang')
            det_db_thresh = float(self.get_property('det_db_thresh'))
            rec_batch_num = int(self.get_property('rec_batch_num'))
            use_gpu = self.get_property('use_gpu')
            show_visualization = self.get_property('show_visualization')
            
            # Step 4: 初始化 PaddleOCR
            self.log_info(f"初始化 PaddleOCR (语言: {lang}, GPU: {use_gpu})")
            
            from paddleocr import PaddleOCR
            
            ocr = PaddleOCR(
                use_angle_cls=True,
                lang=lang,
                use_gpu=use_gpu,
                det_db_thresh=det_db_thresh,
                rec_batch_num=rec_batch_num,
                show_log=False
            )
            
            # Step 5: 执行 OCR 识别
            self.log_info("开始文字识别...")
            result = ocr.ocr(image, cls=True)
            
            # Step 6: 解析识别结果
            recognized_texts = []
            bounding_boxes = []
            
            if result and result[0]:
                for line in result[0]:
                    box = line[0]  # 检测框坐标 [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
                    text = line[1][0]  # 识别文本
                    confidence = line[1][1]  # 置信度
                    
                    recognized_texts.append({
                        'text': text,
                        'confidence': confidence
                    })
                    
                    bounding_boxes.append({
                        'box': box,
                        'text': text,
                        'confidence': confidence
                    })
            
            self.log_success(f"识别完成！共检测到 {len(recognized_texts)} 个文本区域")
            
            # Step 7: 生成可视化图像（可选）
            output_image = image.copy()
            
            if show_visualization and bounding_boxes:
                for item in bounding_boxes:
                    box = np.array(item['box'], dtype=np.int32)
                    text = item['text']
                    confidence = item['confidence']
                    
                    # 绘制检测框
                    cv2.polylines(output_image, [box], True, (0, 255, 0), 2)
                    
                    # 绘制文本标签
                    label = f"{text} ({confidence:.2f})"
                    cv2.putText(output_image, label, (box[0][0], box[0][1] - 10),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Step 8: 构建输出数据
            output_text = "\n".join([item['text'] for item in recognized_texts])
            
            # 将检测框转换为 JSON 格式
            import json
            boxes_json = json.dumps([{
                'box': item['box'].tolist(),
                'text': item['text'],
                'confidence': item['confidence']
            } for item in bounding_boxes], ensure_ascii=False, indent=2)
            
            # Step 9: 返回结果
            return {
                '输出图像': output_image,
                '识别文本': output_text,
                '检测框坐标': boxes_json
            }
            
        except Exception as e:
            self.log_error(f"OCR 识别失败: {e}")
            import traceback
            traceback.print_exc()
            return None
