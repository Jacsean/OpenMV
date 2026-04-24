"""
识别分类节点包 - 二维码、OCR、模板匹配
"""

from NodeGraphQt import BaseNode
import cv2
import numpy as np


class TemplateMatchNode(BaseNode):
    """
    模板匹配节点
    在图像中查找与模板最匹配的区域
    """
    
    __identifier__ = 'recognition'
    NODE_NAME = '模板匹配'
    
    def __init__(self):
        super(TemplateMatchNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        self.add_input('模板图像', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_output('匹配结果', color=(255, 200, 100))
        self.add_text_input('template_path', '模板路径', tab='properties')
        self.add_text_input('threshold', '阈值(0-1)', tab='properties')
        self.set_property('threshold', '0.8')
        
    def process(self, inputs=None):
        """处理节点逻辑"""
        if inputs and len(inputs) >= 1 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                template_path = self.get_property('template_path')
                threshold_val = float(self.get_property('threshold'))
                
                if not template_path:
                    return {'输出图像': image, '匹配结果': '未指定模板路径'}
                
                # 加载模板
                template = cv2.imread(template_path)
                if template is None:
                    return {'输出图像': image, '匹配结果': f'无法加载模板: {template_path}'}
                
                # 转换为灰度图
                if len(image.shape) == 3:
                    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                else:
                    gray_image = image
                
                if len(template.shape) == 3:
                    gray_template = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)
                else:
                    gray_template = template
                
                # 执行模板匹配
                result = cv2.matchTemplate(gray_image, gray_template, cv2.TM_CCOEFF_NORMED)
                min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
                
                # 绘制匹配结果
                output = image.copy()
                h, w = gray_template.shape[:2]
                top_left = max_loc
                bottom_right = (top_left[0] + w, top_left[1] + h)
                
                if max_val >= threshold_val:
                    cv2.rectangle(output, top_left, bottom_right, (0, 255, 0), 2)
                    match_info = f"匹配成功! 置信度: {max_val:.2f}"
                else:
                    match_info = f"匹配失败! 置信度: {max_val:.2f} < 阈值: {threshold_val}"
                
                return {'输出图像': output, '匹配结果': match_info}
            except Exception as e:
                print(f"模板匹配错误: {e}")
                return {'输出图像': None, '匹配结果': f'错误: {str(e)}'}
        return {'输出图像': None, '匹配结果': '无输入'}
