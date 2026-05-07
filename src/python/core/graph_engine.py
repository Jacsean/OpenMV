"""
图执行引擎 - 执行节点图的处理流程

支持统一的节点输入输出数据格式：
- 标准化端口数据传输协议
- 自动处理新旧体系节点格式兼容
- 统一的错误处理和日志记录
- 集成节点调试器
"""

import cv2
import numpy as np
from collections import defaultdict, deque

from utils import logger
from core.node_debugger import node_debugger


class NodeProtocol:
    """
    标准化节点输入输出协议

    统一节点输入输出数据格式，确保不同节点之间的数据交换一致。

    数据格式规范：
    - 输入: list，每个元素对应一个输入端口
    - 输出: dict，键为输出端口名称，值为输出数据
    - 单值输出: 直接使用 {'result': value}
    - 多值输出: {'output1': value1, 'output2': value2}
    """

    @staticmethod
    def get_input(inputs, port_index=0, default=None):
        """
        从输入列表中获取指定端口的输入值

        Args:
            inputs: 输入列表（来自 graph_engine）
            port_index: 端口索引（从0开始）
            default: 默认值

        Returns:
            输入值或默认值
        """
        if inputs is None:
            return default

        if isinstance(inputs, list):
            if port_index < len(inputs):
                value = inputs[port_index]
                if isinstance(value, list) and len(value) > 0:
                    return value[0] if len(value) == 1 else value
                return value
            return default

        return default

    @staticmethod
    def get_dict_input(inputs, port_name, default=None):
        """
        从字典格式的输入中获取指定端口的输入值

        Args:
            inputs: 输入字典或列表
            port_name: 端口名称
            default: 默认值

        Returns:
            输入值或默认值
        """
        if inputs is None:
            return default

        if isinstance(inputs, dict):
            return inputs.get(port_name, default)

        return default

    @staticmethod
    def format_output(**kwargs):
        """
        统一格式化节点输出

        Args:
            **kwargs: 输出数据，键为端口名称，值为数据

        Returns:
            dict: 格式化后的输出字典
        """
        return kwargs

    @staticmethod
    def wrap_output(value):
        """
        包装单个输出值为标准格式

        Args:
            value: 输出值

        Returns:
            dict: 包装后的输出字典
        """
        return {'result': value}

    @staticmethod
    def unwrap_output(outputs, port_name='result', default=None):
        """
        从输出字典中提取指定端口的值

        Args:
            outputs: 输出字典
            port_name: 端口名称
            default: 默认值

        Returns:
            输出值或默认值
        """
        if outputs is None:
            return default

        if isinstance(outputs, dict):
            return outputs.get(port_name, default)

        return outputs if outputs is not None else default


class GraphEngine:
    """
    图执行引擎
    负责执行节点图的处理流程

    支持：
    - 统一的节点输入输出格式
    - 自动处理新旧体系节点格式兼容
    - 详细的执行日志
    """

    def __init__(self):
        self.graph = None
        self.node_outputs = {}

    def execute_graph(self, graph):
        """
        执行整个节点图

        Returns:
            dict: 所有节点的输出结果
        """
        self.graph = graph
        self.node_outputs.clear()

        all_nodes = graph.all_nodes()

        if not all_nodes:
            logger.info("节点图为空，跳过执行", module="graph_engine")
            return {}

        logger.info(f"\n{'='*60}", module="graph_engine")
        logger.info(f"🚀 开始执行节点图 ({len(all_nodes)} 个节点)", module="graph_engine")

        dependencies = self._build_dependency_graph(all_nodes)
        ordered_nodes = self._topological_sort(dependencies, all_nodes)

        for i, node in enumerate(ordered_nodes):
            logger.info(f"\n--- [{i+1}/{len(ordered_nodes)}] 执行节点: {node.name()} ---", module="graph_engine")
            self._execute_node(node)

        logger.info(f"\n{'='*60}", module="graph_engine")
        logger.success(f"✅ 节点图执行完成", module="graph_engine")
        logger.info(f"{'='*60}\n", module="graph_engine")

        return self.node_outputs

    def _build_dependency_graph(self, all_nodes):
        """
        构建节点依赖关系图
        """
        dependencies = defaultdict(list)

        for node in all_nodes:
            for input_port in node.input_ports():
                connected_ports = input_port.connected_ports()
                for connected_port in connected_ports:
                    source_node = connected_port.node()
                    dependencies[node].append(source_node)

        return dependencies

    def _topological_sort(self, dependencies, all_nodes):
        """
        拓扑排序，确定节点执行顺序（Kahn算法）
        """
        in_degree = {node: 0 for node in all_nodes}

        for node in all_nodes:
            for dep_node in dependencies[node]:
                in_degree[node] += 1

        queue = deque()
        for node in all_nodes:
            if in_degree[node] == 0:
                queue.append(node)

        sorted_nodes = []
        while queue:
            current_node = queue.popleft()
            sorted_nodes.append(current_node)

            for node in all_nodes:
                if current_node in dependencies[node]:
                    in_degree[node] -= 1
                    if in_degree[node] == 0:
                        queue.append(node)

        if len(sorted_nodes) != len(all_nodes):
            raise ValueError("节点图中存在循环依赖")

        return sorted_nodes

    def _execute_node(self, node):
        """
        执行单个节点（集成调试支持）
        """
        # 调试模式：检查节点状态
        if node_debugger.debug_mode:
            node_debugger.log("DEBUG", f"准备执行节点: {node.name()}", node.name())
            node_state = node_debugger.inspect_node(node)
            if node_state:
                node_debugger.log("DEBUG", f"节点状态: {node_state['status']}", node.name())

        try:
            inputs = self._get_node_inputs(node)

            # 调试模式：记录输入
            if node_debugger.debug_mode:
                node_debugger.log("DEBUG", f"输入数据: {len(inputs) if isinstance(inputs, list) else 'N/A'} 个端口", node.name())

            if hasattr(node, 'process'):
                # 调试模式：追踪执行
                if node_debugger.debug_mode:
                    trace_result = node_debugger.trace_execution(node, inputs)
                    outputs = trace_result.get('outputs')
                    
                    if trace_result['success']:
                        node_debugger.record_stat(node.id, 'execution_time', trace_result['execution_time'])
                        node_debugger.record_stat(node.id, 'last_execution', trace_result['start_time'])
                    else:
                        logger.error(f"   ❌ 节点执行失败: {trace_result['error']}", module="graph_engine")
                else:
                    outputs = node.process(inputs)
            else:
                logger.warning(f"节点 {node.name()} 没有 process 方法，使用通用处理", module="graph_engine")
                outputs = self._generic_process(node, inputs)

            if outputs:
                self.node_outputs[node.id] = outputs
                logger.info(f"   输出键: {list(outputs.keys()) if isinstance(outputs, dict) else 'N/A'}", module="graph_engine")
                
                # 调试模式：记录输出
                if node_debugger.debug_mode:
                    node_debugger.log("DEBUG", f"输出数据: {list(outputs.keys()) if isinstance(outputs, dict) else 'N/A'}", node.name())
            else:
                logger.warning(f"   节点没有输出", module="graph_engine")
                if node_debugger.debug_mode:
                    node_debugger.log("WARNING", "节点没有输出", node.name())

        except Exception as e:
            logger.error(f"   ❌ 执行节点 {node.name()} 失败: {e}", module="graph_engine")
            import traceback
            traceback.print_exc()
            
            # 调试模式：记录错误
            if node_debugger.debug_mode:
                node_debugger.log("ERROR", f"执行失败: {e}", node.name())

            self.node_outputs[node.id] = {'error': str(e)}

    def _get_node_inputs(self, node):
        """
        获取节点的输入数据（统一格式）

        Returns:
            list: 按端口顺序排列的输入列表
        """
        inputs = []

        for input_port in node.input_ports():
            connected_ports = input_port.connected_ports()

            if not connected_ports:
                inputs.append(None)
                continue

            port_value = None
            for connected_port in connected_ports:
                source_node = connected_port.node()
                source_node_id = source_node.id
                port_name = connected_port.name()

                if source_node_id in self.node_outputs:
                    output_data = self.node_outputs[source_node_id]
                    value = NodeProtocol.get_dict_input(output_data, port_name)
                    port_value = value
                    break

            inputs.append(port_value)

        return inputs

    def _generic_process(self, node, inputs):
        """
        通用节点处理方法（备用）
        """
        logger.warning(f"警告: 节点 {node.name()} 没有实现 process 方法", module="graph_engine")
        return {}


get_input = NodeProtocol.get_input
get_dict_input = NodeProtocol.get_dict_input
format_output = NodeProtocol.format_output
wrap_output = NodeProtocol.wrap_output
unwrap_output = NodeProtocol.unwrap_output