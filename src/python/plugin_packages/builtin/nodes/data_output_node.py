"""
数据输出节点 - 将数据发送到服务器
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class DataOutputNode(BaseNode):
    """
    数据输出节点
    
    用于将处理结果输出到数据采集服务器或数据库
    """
    
    __identifier__ = 'integration'
    NODE_NAME = '数据输出'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(DataOutputNode, self).__init__()
        
        self.add_input('输入数据', color=(100, 255, 100))
        self.add_output('输出', color=(100, 255, 100))
        
        self._param_container = ParameterContainerWidget(self.view, 'data_output_params', '')
        self._param_container.add_text_input('server_url', '服务器地址', text='http://localhost:8080')
        self._param_container.add_text_input('api_endpoint', 'API端点', text='/api/data')
        
        self._param_container.set_value_changed_callback(self._on_param_changed)
        self.add_custom_widget(self._param_container, tab='properties')
    
    def _on_param_changed(self, name, value):
        self.set_property(name, str(value))
    
    def process(self, inputs=None):
        """处理节点逻辑"""
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入数据")
                return {'输出': None}
            
            input_data = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            params = self._param_container.get_values_dict()
            server_url = params.get('server_url', 'http://localhost:8080')
            endpoint = params.get('api_endpoint', '/api/data')
            
            result = {
                'status': 'simulated',
                'server': server_url,
                'endpoint': endpoint,
                'data_received': str(type(input_data)),
                'success': True
            }
            
            self.log_success("数据输出完成")
            return {'输出': result}
            
        except Exception as e:
            self.log_error(f"数据输出错误: {e}")
            return {'输出': None}