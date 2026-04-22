"""
显示节点 - 图像显示和可视化
"""

from NodeGraphQt import BaseNode


class ImageViewNode(BaseNode):
    """
    图像显示节点
    用于在界面中显示图像
    """
    
    __identifier__ = 'display'
    NODE_NAME = '图像显示'
    
    def __init__(self):
        super(ImageViewNode, self).__init__()
        self.add_input('输入图像', color=(100, 100, 255))
        # 添加一个文本输出用于状态显示
        self.add_output('状态', color=(100, 100, 255))
        self.add_text_input('status', '状态', tab='properties')
        
    def process(self, inputs):
        """
        处理节点逻辑
        """
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            if image is not None:
                height, width = image.shape[:2]
                status_msg = f"图像尺寸: {width}x{height}"
                self.set_property('status', status_msg)
                return {'状态': status_msg}
            else:
                self.set_property('status', '无有效图像')
                return {'状态': '无有效图像'}
        else:
            self.set_property('status', '无输入')
            return {'状态': '无输入'}
