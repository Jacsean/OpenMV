"""
高级节点示例包 - 多输入多输出、复杂参数处理
"""

from shared_libs.node_base import BaseNode
import cv2
import numpy as np


class MultiInputBlendNode(BaseNode):
    """多图像混合节点"""
    
    __identifier__ = 'example_advanced_nodes'
    NODE_NAME = '多图像混合'
    resource_level = "light"
    hardware_requirements = {'cpu_cores': 1, 'memory_gb': 1, 'gpu_required': False, 'gpu_memory_gb': 0}
    
    def __init__(self):
        super(MultiInputBlendNode, self).__init__()
        self.add_input('图像1', color=(100, 255, 100))
        self.add_input('图像2', color=(100, 255, 100))
        self.add_input('图像3', color=(100, 255, 100))
        self.add_input('图像4', color=(100, 255, 100))
        self.add_output('混合结果', color=(100, 255, 100))
        self.add_text_input('weight1', '权重1(0-1)', tab='properties')
        self.set_property('weight1', '0.25')
        self.add_text_input('weight2', '权重2(0-1)', tab='properties')
        self.set_property('weight2', '0.25')
        self.add_text_input('weight3', '权重3(0-1)', tab='properties')
        self.set_property('weight3', '0.25')
        self.add_text_input('weight4', '权重4(0-1)', tab='properties')
        self.set_property('weight4', '0.25')
    
    def process(self, inputs=None):
        try:
            images = []
            weights = [float(self.get_property(f'weight{i}')) for i in range(1, 5)]
            
            if inputs:
                for i, inp in enumerate(inputs[:4]):
                    if inp is not None and len(inp) > 0:
                        img = inp[0] if isinstance(inp, list) else inp
                        if img is not None:
                            images.append((img, weights[i]))
            
            if not images:
                return {'混合结果': None}
            
            # 归一化权重
            total_weight = sum(w for _, w in images)
            if total_weight == 0:
                return {'混合结果': images[0][0]}
            
            # 加权混合
            result = np.zeros_like(images[0][0], dtype=np.float64)
            for img, weight in images:
                result += img.astype(np.float64) * (weight / total_weight)
            
            return {'混合结果': result.astype(np.uint8)}
        except Exception as e:
            self.log_error(f"多图像混合错误: {e}")
            return {'混合结果': None}