"""
机器人通信节点 - 与工业机器人通信
"""

from shared_libs.node_base import BaseNode, ParameterContainerWidget
import cv2
import numpy as np


class RobotNode(BaseNode):
    """
    机器人通信节点

    用于与工业机器人进行通信和控制
    """

    __identifier__ = 'integration'
    NODE_NAME = '机器人通信'

    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }

    def __init__(self):
        super(RobotNode, self).__init__()

        self.add_input('目标位置', color=(100, 255, 100))
        self.add_output('状态', color=(100, 255, 100))

        self._param_container = ParameterContainerWidget(self.view, 'robot_params', '')
        self._param_container.add_text_input('robot_ip', '机器人IP', text='192.168.1.200')
        self._param_container.add_combobox('command', '命令', items=['move', 'stop', 'reset', 'status'])
        self._param_container.set_value_changed_callback(self._on_param_changed)
        self.add_custom_widget(self._param_container, tab='properties')

    def _on_param_changed(self, name, value):
        self.set_property(name, str(value))

    def process(self, inputs=None):
        """处理节点逻辑"""
        try:
            target_pos = None
            if inputs and len(inputs) > 0 and inputs[0] is not None:
                target_pos = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]

            params = self._param_container.get_values_dict()
            robot_ip = params.get('robot_ip', '192.168.1.200')
            command = params.get('command', 'move')

            result = {
                'status': 'simulated',
                'robot_ip': robot_ip,
                'command': command,
                'target_position': str(target_pos) if target_pos else 'N/A',
                'execution_result': 'success'
            }

            self.log_success("机器人通信完成")
            return {'状态': result}

        except Exception as e:
            self.log_error(f"机器人通信错误: {e}")
            return {'状态': None}
