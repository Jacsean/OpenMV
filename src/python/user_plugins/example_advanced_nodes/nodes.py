"""
高级节点示例包

演示内容:
1. 多输入多输出节点
2. 复杂参数处理
3. 异常处理最佳实践
4. 性能优化技巧
"""

from NodeGraphQt import BaseNode
import cv2
import numpy as np


class MultiInputBlendNode(BaseNode):
    """
    多图像混合节点
    
    支持2-4张图像的加权混合
    演示多输入端口和动态参数处理
    """
    
    __identifier__ = 'example_advanced_nodes'
    NODE_NAME = '多图像混合'
    
    def __init__(self):
        super(MultiInputBlendNode, self).__init__()
        
        # 多个输入端口（最多4个）
        self.add_input('图像1', color=(100, 255, 100))
        self.add_input('图像2', color=(100, 255, 100))
        self.add_input('图像3', color=(100, 255, 100))
        self.add_input('图像4', color=(100, 255, 100))
        
        # 输出端口
        self.add_output('混合结果', color=(100, 255, 100))
        
        # 权重参数（4个图像的权重）
        self.add_text_input('weight1', '权重1(0-1)', tab='properties')
        self.set_property('weight1', '0.25')
        
        self.add_text_input('weight2', '权重2(0-1)', tab='properties')
        self.set_property('weight2', '0.25')
        
        self.add_text_input('weight3', '权重3(0-1)', tab='properties')
        self.set_property('weight3', '0.25')
        
        self.add_text_input('weight4', '权重4(0-1)', tab='properties')
        self.set_property('weight4', '0.25')
        
    def process(self, inputs=None):
        """
        处理多图像混合
        
        最佳实践:
        1. 检查所有输入有效性
        2. 统一图像尺寸
        3. 归一化权重
        4. 异常安全处理
        """
        try:
            # 收集有效输入
            valid_images = []
            weights = []
            
            for i in range(4):
                if inputs and len(inputs) > i and inputs[i] is not None:
                    image = inputs[i][0] if isinstance(inputs[i], list) else inputs[i]
                    if image is not None:
                        valid_images.append(image)
                        
                        # 获取对应权重
                        weight_key = f'weight{i+1}'
                        weight = float(self.get_property(weight_key))
                        weight = max(0.0, min(1.0, weight))  # 限制范围
                        weights.append(weight)
            
            # 至少需要2张图像
            if len(valid_images) < 2:
                return {'混合结果': valid_images[0] if valid_images else None}
            
            # 归一化权重
            weight_sum = sum(weights)
            if weight_sum > 0:
                weights = [w / weight_sum for w in weights]
            else:
                weights = [1.0 / len(valid_images)] * len(valid_images)
            
            # 统一到第一张图像的尺寸
            base_h, base_w = valid_images[0].shape[:2]
            resized_images = []
            for img in valid_images:
                if img.shape[:2] != (base_h, base_w):
                    img = cv2.resize(img, (base_w, base_h))
                resized_images.append(img)
            
            # 加权混合
            result = np.zeros_like(resized_images[0], dtype=np.float64)
            for img, weight in zip(resized_images, weights):
                result += img.astype(np.float64) * weight
            
            result = np.clip(result, 0, 255).astype(np.uint8)
            
            return {'混合结果': result}
            
        except Exception as e:
            print(f"多图像混合错误: {e}")
            import traceback
            traceback.print_exc()
            return {'混合结果': None}


class AdaptiveThresholdNode(BaseNode):
    """
    自适应阈值节点
    
    根据局部区域自动调整阈值
    演示复杂参数处理和多种算法选择
    """
    
    __identifier__ = 'example_advanced_nodes'
    NODE_NAME = '自适应阈值'
    
    def __init__(self):
        super(AdaptiveThresholdNode, self).__init__()
        
        # 输入输出
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('二值图像', color=(100, 255, 100))
        
        # 算法类型参数
        self.add_text_input('method', '算法(0=均值,1=高斯)', tab='properties')
        self.set_property('method', '1')
        
        # 块大小（必须是奇数）
        self.add_text_input('block_size', '块大小(奇数3-99)', tab='properties')
        self.set_property('block_size', '11')
        
        # 常数C
        self.add_text_input('C', '常数C(-10-10)', tab='properties')
        self.set_property('C', '2')
        
    def process(self, inputs=None):
        """
        自适应阈值处理
        
        最佳实践:
        1. 参数验证和修正
        2. 提供合理的默认值
        3. 详细的错误信息
        """
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            try:
                # 转换为灰度图
                if len(image.shape) == 3:
                    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                else:
                    gray = image
                
                # 获取并验证参数
                method_val = int(self.get_property('method'))
                method = cv2.ADAPTIVE_THRESH_GAUSSIAN_C if method_val == 1 else cv2.ADAPTIVE_THRESH_MEAN_C
                
                block_size = int(self.get_property('block_size'))
                # 确保是奇数且在合理范围内
                block_size = max(3, min(99, block_size))
                if block_size % 2 == 0:
                    block_size += 1
                
                C = float(self.get_property('C'))
                C = max(-10, min(10, C))
                
                # 执行自适应阈值
                binary = cv2.adaptiveThreshold(
                    gray, 
                    255, 
                    method, 
                    cv2.THRESH_BINARY, 
                    block_size, 
                    C
                )
                
                # 转换回BGR以便显示
                result = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)
                
                return {'二值图像': result}
                
            except Exception as e:
                error_msg = f"自适应阈值错误: {str(e)}"
                print(error_msg)
                return {'二值图像': None}
        
        return {'二值图像': None}


class HistogramEqualizeNode(BaseNode):
    """
    直方图均衡化节点
    
    增强图像对比度
    演示彩色图像处理和多通道操作
    """
    
    __identifier__ = 'example_advanced_nodes'
    NODE_NAME = '直方图均衡化'
    
    def __init__(self):
        super(HistogramEqualizeNode, self).__init__()
        
        # 输入输出
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_output('增强图像', color=(100, 255, 100))
        self.add_output('直方图数据', color=(255, 255, 100))
        
        # 处理模式
        self.add_text_input('mode', '模式(0=全局,1=CLAHE)', tab='properties')
        self.set_property('mode', '1')
        
        # CLAHE参数
        self.add_text_input('clip_limit', 'CLAHE限制(1-40)', tab='properties')
        self.set_property('clip_limit', '2.0')
        
        self.add_text_input('grid_size', '网格大小(2-16)', tab='properties')
        self.set_property('grid_size', '8')
        
    def process(self, inputs=None):
        """
        直方图均衡化处理
        
        最佳实践:
        1. 支持多种算法模式
        2. 返回额外统计信息
        3. 彩色图像正确处理
        """
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            try:
                mode = int(self.get_property('mode'))
                
                if len(image.shape) == 3:
                    # 彩色图像：转换到LAB空间处理L通道
                    lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
                    l, a, b = cv2.split(lab)
                    
                    if mode == 1:  # CLAHE
                        clip_limit = float(self.get_property('clip_limit'))
                        grid_size = int(self.get_property('grid_size'))
                        clahe = cv2.createCLAHE(
                            clipLimit=max(1, min(40, clip_limit)),
                            tileGridSize=(max(2, min(16, grid_size)),) * 2
                        )
                        l_eq = clahe.apply(l)
                        hist_info = f"CLAHE (limit={clip_limit}, grid={grid_size})"
                    else:  # 全局均衡化
                        l_eq = cv2.equalizeHist(l)
                        hist_info = "全局均衡化"
                    
                    lab_eq = cv2.merge([l_eq, a, b])
                    result = cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)
                else:
                    # 灰度图像
                    if mode == 1:  # CLAHE
                        clip_limit = float(self.get_property('clip_limit'))
                        grid_size = int(self.get_property('grid_size'))
                        clahe = cv2.createCLAHE(
                            clipLimit=max(1, min(40, clip_limit)),
                            tileGridSize=(max(2, min(16, grid_size)),) * 2
                        )
                        result = clahe.apply(image)
                        hist_info = f"CLAHE (limit={clip_limit}, grid={grid_size})"
                    else:  # 全局均衡化
                        result = cv2.equalizeHist(image)
                        hist_info = "全局均衡化"
                    
                    # 转回BGR
                    if len(result.shape) == 2:
                        result = cv2.cvtColor(result, cv2.COLOR_GRAY2BGR)
                
                return {
                    '增强图像': result,
                    '直方图数据': hist_info
                }
                
            except Exception as e:
                print(f"直方图均衡化错误: {e}")
                return {'增强图像': None, '直方图数据': '错误'}
        
        return {'增强图像': None, '直方图数据': '无输入'}
