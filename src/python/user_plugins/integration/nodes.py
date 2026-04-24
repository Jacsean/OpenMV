"""
系统集成节点包 - PLC、数采、机器人通信
"""

from NodeGraphQt import BaseNode
import cv2
import numpy as np
import json
from datetime import datetime


class DataOutputNode(BaseNode):
    """
    数据输出节点
    将测量结果输出到外部系统（模拟MQTT/HTTP）
    """
    
    __identifier__ = 'integration'
    NODE_NAME = '数据输出'
    
    def __init__(self):
        super(DataOutputNode, self).__init__()
        self.add_input('输入数据', color=(100, 255, 100))
        self.add_output('状态', color=(100, 255, 100))
        self.add_text_input('output_type', '输出类型', tab='properties')
        self.set_property('output_type', 'JSON')
        self.add_text_input('endpoint', '端点地址', tab='properties')
        self.set_property('endpoint', 'http://localhost:8080/api/data')
        self.add_text_input('status', '状态', tab='properties')
        
    def process(self, inputs=None):
        """处理节点逻辑"""
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            data = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                output_type = self.get_property('output_type')
                endpoint = self.get_property('endpoint')
                
                # 构建输出数据包
                payload = {
                    'timestamp': datetime.now().isoformat(),
                    'data_type': output_type,
                    'endpoint': endpoint,
                    'content': str(data)
                }
                
                # 模拟发送数据（实际应用中替换为真实的MQTT/HTTP请求）
                json_str = json.dumps(payload, ensure_ascii=False, indent=2)
                
                status_msg = f"✅ 数据已准备发送\n端点: {endpoint}\n类型: {output_type}"
                self.set_property('status', status_msg)
                
                print(f"\n📤 数据输出模拟:")
                print(json_str)
                
                return {'状态': status_msg}
            except Exception as e:
                status_msg = f'❌ 错误: {str(e)}'
                self.set_property('status', status_msg)
                return {'状态': status_msg}
        
        status_msg = '无输入数据'
        self.set_property('status', status_msg)
        return {'状态': status_msg}
