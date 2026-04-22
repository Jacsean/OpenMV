"""
节点注册表 - 管理所有可用的节点类型
"""

from NodeGraphQt import BaseNode


class BaseVisualNode(BaseNode):
    """
    视觉编程系统的基础节点类
    """
    
    def __init__(self):
        super(BaseVisualNode, self).__init__()
        # 设置节点默认大小
        self.set_property('width', 200)
        self.set_property('height', 100)
        
    def process(self, inputs=None):
        """
        处理节点逻辑
        子类应该重写此方法
        
        Args:
            inputs: 输入数据列表
            
        Returns:
            dict: 输出数据字典
        """
        raise NotImplementedError("子类必须实现process方法")


def register_all_nodes(graph):
    """
    注册所有节点到图形引擎
    
    Args:
        graph: NodeGraph实例
    """
    from nodes.io_nodes import ImageLoadNode, ImageSaveNode
    from nodes.processing_nodes import GrayscaleNode, GaussianBlurNode, CannyEdgeNode, ThresholdNode
    from nodes.display_nodes import ImageViewNode
    
    # 注册IO节点
    graph.register_node(ImageLoadNode)
    graph.register_node(ImageSaveNode)
    
    # 注册处理节点
    graph.register_node(GrayscaleNode)
    graph.register_node(GaussianBlurNode)
    graph.register_node(CannyEdgeNode)
    graph.register_node(ThresholdNode)
    
    # 注册显示节点
    graph.register_node(ImageViewNode)
    
    print("所有节点已注册完成")
