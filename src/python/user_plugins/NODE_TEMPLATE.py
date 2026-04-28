"""
算法节点模板 - 快速创建新节点的参考示例

使用说明：
1. 复制此文件到你的节点包目录
2. 修改类名、标识符、端口和参数
3. 在process方法中实现你的算法逻辑
4. 在plugin.json中注册节点
"""

from shared_libs.node_base import BaseNode
import cv2
import numpy as np


class TemplateAlgorithmNode(BaseNode):
    """
    算法节点模板
    
    这是一个标准的算法节点实现模板，包含：
    - 完整的输入输出端口定义
    - 可配置参数
    - 完善的异常处理
    - 详细的日志输出
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    # ⚠️ 重要：必须与plugin.json中的name字段完全一致
    __identifier__ = 'your_package_name'
    
    # ⚠️ 重要：必须与plugin.json中的display_name完全一致
    NODE_NAME = '算法节点模板'
    
    # 资源等级声明（light / medium / heavy）
    resource_level = "light"
    
    # 硬件要求配置
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(TemplateAlgorithmNode, self).__init__()
        
        # ==================== 输入端口定义 ====================
        # 单输入示例（最常用）
        self.add_input('输入图像', color=(100, 255, 100))  # 绿色表示图像数据
        
        # 多输入示例（注释掉，需要时启用）
        # self.add_input('背景图像', color=(100, 255, 100))
        # self.add_input('前景图像', color=(100, 255, 100))
        # self.add_input('掩码图像', color=(100, 255, 100))
        
        # ==================== 输出端口定义 ====================
        # 单输出示例
        self.add_output('输出图像', color=(100, 255, 100))
        
        # 多输出示例（注释掉，需要时启用）
        # self.add_output('标注图像', color=(100, 255, 100))
        # self.add_output('检测结果', color=(255, 100, 100))  # 红色表示布尔/状态
        # self.add_output('统计信息', color=(100, 100, 255))  # 蓝色表示数值
        
        # ==================== 参数控件定义 ====================
        # 文本输入框（推荐方式）
        self.add_text_input('param1', '参数1说明(范围)', tab='properties')
        self.set_property('param1', '默认值')
        
        self.add_text_input('param2', '参数2说明(范围)', tab='properties')
        self.set_property('param2', '10')
        
        # 更多参数示例（根据需要添加）
        # self.add_text_input('threshold', '阈值(0-255)', tab='properties')
        # self.set_property('threshold', '128')
        
        # self.add_text_input('kernel_size', '核大小(3-15,奇数)', tab='properties')
        # self.set_property('kernel_size', '5')
    
    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: 输入数据列表
                   - inputs[0]: 第一个输入端口的数据
                   - inputs[1]: 第二个输入端口的数据（如果有）
                   
        Returns:
            dict: 输出端口名称 -> 数据字典
                  例如: {'输出图像': result_image}
        
        注意事项：
        1. 必须包含try-except异常处理
        2. 失败时返回None而非抛出异常
        3. 使用self.log_*()记录日志
        4. 验证输入数据的有效性
        """
        try:
            # ==================== Step 1: 验证输入 ====================
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入图像")
                return {'输出图像': None}
            
            # 提取输入图像（支持列表和直接传入两种方式）
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            # 验证图像格式
            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return {'输出图像': None}
            
            # 验证图像尺寸（可选）
            if image.size == 0:
                self.log_error("输入图像为空")
                return {'输出图像': None}
            
            # ==================== Step 2: 读取参数 ====================
            # 从UI控件获取参数值（返回字符串，需要转换类型）
            param1_value = self.get_property('param1')
            param2_value = int(self.get_property('param2'))
            
            # 参数验证和范围限制（重要！）
            try:
                param1_float = float(param1_value)
                # 限制参数范围
                param1_float = max(0.0, min(1.0, param1_float))
            except ValueError:
                self.log_warning(f"参数1无效: {param1_value}，使用默认值")
                param1_float = 0.5
            
            # ==================== Step 3: 执行算法 ====================
            # 在这里实现你的OpenCV算法逻辑
            
            # 示例1: 简单的图像处理
            # result = cv2.some_operation(image, param1_float, param2_value)
            
            # 示例2: 多步骤处理
            # gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            # result = cv2.threshold(blurred, param2_value, 255, cv2.THRESH_BINARY)[1]
            
            # 示例3: 条件分支处理
            # if param1_float > 0.5:
            #     result = self._method_a(image)
            # else:
            #     result = self._method_b(image)
            
            # TODO: 替换为你的实际算法
            result = image.copy()  # 占位符，实际应执行算法
            
            # ==================== Step 4: 返回结果 ====================
            self.log_success(f"处理完成 (参数1={param1_float}, 参数2={param2_value})")
            return {'输出图像': result}
            
        except Exception as e:
            # 捕获所有异常，避免崩溃
            self.log_error(f"处理错误: {e}")
            import traceback
            traceback.print_exc()  # 打印详细堆栈便于调试
            return {'输出图像': None}
    
    # ==================== 辅助方法（可选）====================
    def _helper_method_a(self, image):
        """
        辅助方法示例A
        
        Args:
            image: 输入图像
            
        Returns:
            处理后的图像
        """
        # 实现具体逻辑
        return image
    
    def _helper_method_b(self, image):
        """
        辅助方法示例B
        
        Args:
            image: 输入图像
            
        Returns:
            处理后的图像
        """
        # 实现具体逻辑
        return image


# ==================== 多输入多输出节点示例 ====================
class MultiIONodeTemplate(BaseNode):
    """
    多输入多输出节点模板
    
    演示如何处理多个输入和输出端口
    """
    
    __identifier__ = 'your_package_name'
    NODE_NAME = '多IO节点模板'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(MultiIONodeTemplate, self).__init__()
        
        # 多个输入端口
        self.add_input('背景图像', color=(100, 255, 100))
        self.add_input('前景图像', color=(100, 255, 100))
        
        # 多个输出端口
        self.add_output('混合结果', color=(100, 255, 100))
        self.add_output('遮罩图像', color=(100, 255, 100))
        
        # 参数
        self.add_text_input('alpha', '混合比例(0.0-1.0)', tab='properties')
        self.set_property('alpha', '0.5')
    
    def process(self, inputs=None):
        """处理多输入多输出逻辑"""
        try:
            # 验证输入数量
            if not inputs or len(inputs) < 2:
                self.log_warning("需要两个输入图像")
                return {'混合结果': None, '遮罩图像': None}
            
            # 提取输入
            bg_image = inputs[0][0] if inputs[0] else None
            fg_image = inputs[1][0] if inputs[1] else None
            
            if bg_image is None or fg_image is None:
                self.log_error("输入图像为空")
                return {'混合结果': None, '遮罩图像': None}
            
            # 读取参数
            alpha = float(self.get_property('alpha'))
            alpha = max(0.0, min(1.0, alpha))  # 限制范围
            
            # 确保尺寸一致
            if bg_image.shape[:2] != fg_image.shape[:2]:
                fg_resized = cv2.resize(fg_image, (bg_image.shape[1], bg_image.shape[0]))
            else:
                fg_resized = fg_image
            
            # 执行混合
            mixed = cv2.addWeighted(bg_image, 1-alpha, fg_resized, alpha, 0)
            
            # 生成遮罩（示例）
            mask = np.ones_like(bg_image) * 255
            
            self.log_success(f"混合完成 (alpha={alpha})")
            return {'混合结果': mixed, '遮罩图像': mask}
            
        except Exception as e:
            self.log_error(f"处理错误: {e}")
            return {'混合结果': None, '遮罩图像': None}


# ==================== AI节点示例（需要异步处理）====================
class AINodeTemplate(BaseNode):
    """
    AI节点模板
    
    演示如何使用依赖检查和模型缓存功能
    """
    
    __identifier__ = 'ai_vision'
    NODE_NAME = 'AI节点模板'
    
    resource_level = "heavy"  # AI模型通常是重量级
    hardware_requirements = {
        'cpu_cores': 4,
        'memory_gb': 8,
        'gpu_required': True,  # 需要GPU
        'gpu_memory_gb': 4
    }
    
    def __init__(self):
        super(AINodeTemplate, self).__init__()
        
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('标注图像', color=(100, 255, 100))
        self.add_output('检测结果', color=(100, 100, 255))  # 数值数据
        
        self.add_text_input('confidence', '置信度阈值(0.0-1.0)', tab='properties')
        self.set_property('confidence', '0.5')
    
    def process(self, inputs=None):
        """AI推理处理"""
        try:
            # Step 1: 检查依赖
            if not self.check_dependencies(['torch', 'ultralytics']):
                self.log_error("缺少必需依赖，请先安装")
                return {'标注图像': None, '检测结果': None}
            
            # Step 2: 检查硬件
            if not self.check_hardware():
                self.log_error("硬件不满足要求")
                return {'标注图像': None, '检测结果': None}
            
            # Step 3: 验证输入
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {'标注图像': None, '检测结果': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            # Step 4: 加载模型（带缓存）
            model = self.get_or_load_model(
                'yolov8n',
                lambda: self._load_yolo_model()  # 懒加载函数
            )
            
            # Step 5: 执行推理
            confidence = float(self.get_property('confidence'))
            results = model(image, conf=confidence)
            
            # Step 6: 处理结果
            annotated_image = results[0].plot()
            detection_count = len(results[0].boxes)
            
            self.log_success(f"检测完成，发现 {detection_count} 个目标")
            return {'标注图像': annotated_image, '检测结果': detection_count}
            
        except Exception as e:
            self.log_error(f"AI推理错误: {e}")
            return {'标注图像': None, '检测结果': None}
    
    def _load_yolo_model(self):
        """加载YOLO模型（仅在首次调用时执行）"""
        from ultralytics import YOLO
        return YOLO('yolov8n.pt')
