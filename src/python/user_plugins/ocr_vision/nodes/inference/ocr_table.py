"""
OCR 表格识别节点（中量级）

基于 PaddleOCR 的表格结构识别功能，支持：
- 自动检测图像中的表格区域
- 识别表格单元格结构和内容
- 输出结构化数据（Excel/CSV/JSON）

硬件要求：
- CPU: 4+ 核心
- 内存: 8GB+
- GPU: 可选（推荐用于加速）
- 存储: ~600MB（包含表格模型）

警告：
- 表格识别比通用文字识别更耗时
- 建议先使用通用 OCR 节点验证图像质量
- 复杂表格可能需要后处理

使用方法：
1. 拖拽节点到画布
2. 连接输入图像（建议为清晰的表格截图）
3. 选择导出格式（excel/csv/json）
4. 设置置信度阈值
5. 运行识别
6. 获取结构化表格数据

示例工作流：
    [输入图像] → [OCR 表格识别] → [Excel 文件路径] + [JSON 数据]
"""

from ....base_nodes import AIBaseNode
import cv2
import numpy as np


class OCRTableRecognitionNode(AIBaseNode):
    """
    OCR 表格识别节点
    
    使用 PaddleOCR 进行表格结构识别与数据提取，支持：
    - 自动表格区域检测
    - 单元格结构识别
    - 多格式导出（Excel/CSV/JSON）
    - 合并单元格处理
    """
    
    __identifier__ = 'ocr_vision'
    NODE_NAME = 'OCR 表格识别'
    
    # 资源等级声明
    resource_level = "medium"
    hardware_requirements = {
        'cpu_cores': 4,
        'memory_gb': 8,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(OCRTableRecognitionNode, self).__init__()
        
        # 输入端口
        self.add_input('输入图像', color=(100, 255, 100))
        
        # 输出端口
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_output('Excel 文件路径', color=(100, 200, 255))
        self.add_output('JSON 数据', color=(255, 200, 100))
        
        # 参数配置
        self.add_combo_menu('export_format', '导出格式', 
                           items=['excel', 'csv', 'json'],
                           tab='properties')
        self.set_property('export_format', 'excel')
        
        self.add_text_input('output_dir', '输出目录', tab='properties')
        self.set_property('output_dir', './ocr_tables')
        
        self.add_text_input('det_db_thresh', '检测阈值(0-1)', tab='properties')
        self.set_property('det_db_thresh', '0.3')
        
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
            dict: 包含输出图像、Excel 文件路径、JSON 数据
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
            export_format = self.get_property('export_format')
            output_dir = self.get_property('output_dir')
            det_db_thresh = float(self.get_property('det_db_thresh'))
            use_gpu = self.get_property('use_gpu')
            show_visualization = self.get_property('show_visualization')
            
            # Step 4: 初始化 PaddleOCR 表格识别器
            self.log_info(f"初始化 PaddleOCR 表格识别 (GPU: {use_gpu})")
            
            from paddleocr import PPStructure
            
            table_recognizer = PPStructure(
                show_log=False,
                use_gpu=use_gpu,
                lang='ch',
                layout=False,  # 仅表格识别
                table=True
            )
            
            # Step 5: 执行表格识别
            self.log_info("开始表格识别...")
            result = table_recognizer(image)
            
            # Step 6: 解析表格结果
            tables_data = []
            
            for region in result:
                if region['type'] == 'table':
                    table_html = region.get('res', {}).get('html', '')
                    table_cells = region.get('res', {}).get('cells', [])
                    
                    tables_data.append({
                        'html': table_html,
                        'cells': table_cells,
                        'bbox': region.get('bbox', [])
                    })
            
            self.log_success(f"识别完成！共检测到 {len(tables_data)} 个表格")
            
            # Step 7: 导出数据
            import os
            import json
            os.makedirs(output_dir, exist_ok=True)
            
            excel_paths = []
            json_data_list = []
            
            for idx, table in enumerate(tables_data):
                # 生成文件名
                base_name = f"table_{idx+1}"
                
                # 导出 Excel
                if export_format in ['excel', 'csv']:
                    try:
                        import pandas as pd
                        from io import StringIO
                        
                        # 从 HTML 解析表格
                        html_table = table['html']
                        df = pd.read_html(StringIO(html_table))[0]
                        
                        if export_format == 'excel':
                            file_path = os.path.join(output_dir, f"{base_name}.xlsx")
                            df.to_excel(file_path, index=False)
                        else:  # csv
                            file_path = os.path.join(output_dir, f"{base_name}.csv")
                            df.to_csv(file_path, index=False, encoding='utf-8-sig')
                        
                        excel_paths.append(file_path)
                        self.log_info(f"导出 {export_format.upper()}: {file_path}")
                    except Exception as e:
                        self.log_warning(f"导出 {export_format} 失败: {e}")
                
                # 导出 JSON
                json_data_list.append({
                    'table_index': idx + 1,
                    'bbox': table['bbox'],
                    'html': table['html'],
                    'cells_count': len(table['cells'])
                })
            
            # Step 8: 生成可视化图像
            output_image = image.copy()
            
            if show_visualization and tables_data:
                for table in tables_data:
                    bbox = table['bbox']
                    if len(bbox) == 4:
                        x1, y1, x2, y2 = map(int, bbox)
                        cv2.rectangle(output_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(output_image, "TABLE", (x1, y1 - 10),
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            # Step 9: 构建输出数据
            json_output = json.dumps(json_data_list, ensure_ascii=False, indent=2)
            excel_output = "; ".join(excel_paths) if excel_paths else ""
            
            # Step 10: 返回结果
            return {
                '输出图像': output_image,
                'Excel 文件路径': excel_output,
                'JSON 数据': json_output
            }
            
        except Exception as e:
            self.log_error(f"表格识别失败: {e}")
            import traceback
            traceback.print_exc()
            return None
