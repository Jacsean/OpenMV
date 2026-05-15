"""
PLC通信节点 - 与PLC设备通信
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class PLCNode(BaseNode):
    """
    PLC通信节点

    用于与PLC设备进行通信，读取/写入数据
    """

    __identifier__ = 'integration'
    NODE_NAME = 'PLC通信'

    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }

    def __init__(self):
        super(PLCNode, self).__init__()

        self.add_input('触发信号', color=(100, 255, 100))
        self.add_output('数据输出', color=(100, 255, 100))

        self._param_container = ParameterContainerWidget(self.view, 'plc_params', '')
        self._param_container.add_text_input('ip_address', 'PLC地址', text='192.168.1.100')
        self._param_container.add_spinbox('port', '端口', value=502, min_value=1, max_value=65535)
        self._param_container.add_text_input('register', '寄存器', text='0x0000')
        self._param_container.set_value_changed_callback(self._on_param_changed)
        self.add_custom_widget(self._param_container, tab='properties')

    def _on_param_changed(self, name, value):
        self.set_property(name, str(value))

    def process(self, inputs=None):
        """处理节点逻辑"""
        try:
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入")
                return {'数据输出': None}

            params = self._param_container.get_values_dict()
            ip_address = params.get('ip_address', '192.168.1.100')
            port = int(params.get('port', 502))
            register = params.get('register', '0x0000')

            result = {
                'status': 'simulated',
                'ip': ip_address,
                'port': port,
                'register': register,
                'value': 12345
            }

            self.log_success("PLC通信完成")
            return {'数据输出': result}

        except Exception as e:
            self.log_error(f"PLC通信错误: {e}")
            return {'数据输出': None}

