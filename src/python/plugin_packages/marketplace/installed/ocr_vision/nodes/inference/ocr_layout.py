"""
OCR 版面分析节点（中量级）

基于 PaddleOCR 的文档版面分析功能，支持：
- 自动识别文档结构（标题、段落、图片、表格等）
- 提取各区域的位置和内容
- 输出结构化布局信息

硬件要求：
- CPU: 4+ 核心
- 内存: 8GB+
- GPU: 可选（推荐用于加速）
- 存储: ~700MB（包含版面分析模型）

警告：
- 版面分析需要较大的内存
- 建议处理分辨率适中的图像（1000-2000px）
- 复杂版面可能需要后处理

使用方法：
1. 拖拽节点到画布
2. 连接输入图像（建议为清晰的文档扫描件）
3. 选择分析模式（全文档/仅文本/仅图片）
4. 设置置信度阈值
5. 运行分析
6. 获取版面结构信息

示例工作流：
    [输入图像] → [OCR 版面分析] → [布局 JSON] + [可视化图像]
"""

from ....base_nodes import AIBaseNode
import cv2
import numpy as np


class OCRLanguageLayoutNode(AIBaseNode):
    """
    OCR 版面分析节点
    
    使用 PaddleOCR 进行文档版面结构分析，支持：
    - 自动检测文档区域类型（标题/段落/图片/表格）
    - 提取区域位置和层级关系
    - 结构化输出（JSON 格式）
    - 可视化标注
    """
    
    __identifier__ = 'ocr_vision'
    NODE_NAME = 'OCR 版面分析'
    
    # 资源等级声明
    resource_level = "medium"
    hardware_requirements = {
        'cpu_cores': 4,
        'memory_gb': 8,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(OCRLanguageLayoutNode, self).__init__()
        
        # 输入端口
        self.add_input('输入图像', color=(100, 255, 100))
        
        # 输出端口
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_output('布局 JSON', color=(100, 200, 255))
        self.add_output('区域数量', color=(255, 200, 100))
        
        # 参数配置
        self.add_combo_menu('analysis_mode', '分析模式', 
                           items=['full', 'text_only', 'image_only'],
                           tab='properties')
        self.set_property('analysis_mode', 'full')
        
        self.add_text_input('det_db_thresh', '检测阈值(0-1)', tab='properties')
        self.set_property('det_db_thresh', '0.3')
        
        self.add_checkbox('use_gpu', '使用 GPU 加速', tab='properties')
        self.set_property('use_gpu', False)
        
        self.add_checkbox('show_visualization', '显示可视化结果', tab='properties')
        self.set_property('show_visualization', True)
        
        self.add_checkbox('extract_text', '提取区域文本内容', tab='properties')
        self.set_property('extract_text', True)
    
    def check_dependencies(self):
        """检查依赖库"""
        try:
            from paddleocr import PPStructure
            return True, "PaddleOCR 已安装"
        except ImportError:
            return False, "缺少依赖: pip install paddlepaddle>=2.4.0 paddleocr>=2.6.0"
    
    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: 输入图像
            
        Returns:
            dict: 包含输出图像、布局 JSON、区域数量
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
            analysis_mode = self.get_property('analysis_mode')
            det_db_thresh = float(self.get_property('det_db_thresh'))
            use_gpu = self.get_property('use_gpu')
            show_visualization = self.get_property('show_visualization')
            extract_text = self.get_property('extract_text')
            
            # Step 4: 初始化 PaddleOCR 版面分析器
            self.log_info(f"初始化 PaddleOCR 版面分析 (模式: {analysis_mode}, GPU: {use_gpu})")
            
            from paddleocr import PPStructure
            
            layout_analyzer = PPStructure(
                show_log=False,
                use_gpu=use_gpu,
                lang='ch',
                layout=True,  # 启用版面分析
                table=False,  # 不单独处理表格
                ocr=extract_text  # 是否提取文本
            )
            
            # Step 5: 执行版面分析
            self.log_info("开始版面分析...")
            result = layout_analyzer(image)
            
            # Step 6: 解析版面结果
            layout_regions = []
            
            for region in result:
                region_type = region.get('type', 'unknown')
                
                # 根据分析模式过滤
                if analysis_mode == 'text_only' and region_type in ['figure', 'table']:
                    continue
                elif analysis_mode == 'image_only' and region_type not in ['figure']:
                    continue
                
                bbox = region.get('bbox', [])
                res_data = region.get('res', {})
                
                region_info = {
                    'type': region_type,
                    'bbox': bbox,
                    'confidence': res_data.get('score', 0.0) if isinstance(res_data, dict) else 0.0
                }
                
                # 如果启用了文本提取，添加文本内容
                if extract_text and 'text' in res_data:
                    region_info['text'] = res_data['text']
                elif extract_text and isinstance(res_data, list):
                    # OCR 结果可能是列表
                    texts = [item.get('text', '') for item in res_data if isinstance(item, dict)]
                    region_info['text'] = "\n".join(texts)
                
                layout_regions.append(region_info)
            
            self.log_success(f"分析完成！共检测到 {len(layout_regions)} 个区域")
            
            # Step 7: 生成可视化图像
            output_image = image.copy()
            
            if show_visualization and layout_regions:
                # 定义不同区域类型的颜色
                type_colors = {
                    'title': (255, 0, 0),      # 红色 - 标题
                    'text': (0, 255, 0),       # 绿色 - 文本
                    'figure': (0, 0, 255),     # 蓝色 - 图片
                    'table': (255, 255, 0),    # 黄色 - 表格
                    'header': (255, 0, 255),   # 紫色 - 页眉
                    'footer': (0, 255, 255),   # 青色 - 页脚
                    'reference': (128, 0, 128) # 深紫 - 引用
                }
                
                for region in layout_regions:
                    bbox = region['bbox']
                    region_type = region['type']
                    
                    if len(bbox) == 4:
                        x1, y1, x2, y2 = map(int, bbox)
                        
                        # 获取颜色
                        color = type_colors.get(region_type, (128, 128, 128))
                        
                        # 绘制矩形框
                        cv2.rectangle(output_image, (x1, y1), (x2, y2), color, 2)
                        
                        # 绘制标签
                        label = f"{region_type.upper()}"
                        if 'confidence' in region:
                            label += f" ({region['confidence']:.2f})"
                        
                        cv2.putText(output_image, label, (x1, y1 - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            
            # Step 8: 构建输出数据
            import json
            
            # 统计各类型区域数量
            type_counts = {}
            for region in layout_regions:
                rtype = region['type']
                type_counts[rtype] = type_counts.get(rtype, 0) + 1
            
            layout_output = {
                'total_regions': len(layout_regions),
                'type_distribution': type_counts,
                'regions': layout_regions
            }
            
            json_output = json.dumps(layout_output, ensure_ascii=False, indent=2)
            region_count = str(len(layout_regions))
            
            # Step 9: 返回结果
            return {
                '输出图像': output_image,
                '布局 JSON': json_output,
                '区域数量': region_count
            }
            
        except Exception as e:
            self.log_error(f"版面分析失败: {e}")
            import traceback
            traceback.print_exc()
            return None
