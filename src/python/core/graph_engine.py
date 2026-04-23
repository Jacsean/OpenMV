"""
图执行引擎 - 执行节点图的处理流程
"""

import cv2
import numpy as np
from collections import defaultdict, deque


class GraphEngine:
    """
    图执行引擎
    负责执行节点图的处理流程
    """
    
    def __init__(self):
        self.graph = None
        self.node_outputs = {}
        
    def execute_graph(self, graph):
        """
        执行整个节点图
        """
        self.graph = graph
        self.node_outputs.clear()
        
        # 获取所有节点
        all_nodes = graph.all_nodes()
        
        # 构建依赖关系图
        dependencies = self._build_dependency_graph(all_nodes)
        
        # 拓扑排序
        ordered_nodes = self._topological_sort(dependencies, all_nodes)
        
        # 按顺序执行节点
        for node in ordered_nodes:
            self._execute_node(node)
            
        return self.node_outputs
    
    def _build_dependency_graph(self, all_nodes):
        """
        构建节点依赖关系图
        """
        dependencies = defaultdict(list)
        
        for node in all_nodes:
            # 获取该节点的所有输入连接
            for input_port in node.input_ports():
                connected_ports = input_port.connected_ports()
                for connected_port in connected_ports:
                    # 连接到该输入端口的输出节点是当前节点的依赖
                    source_node = connected_port.node()
                    dependencies[node].append(source_node)
                    
        return dependencies
    
    def _topological_sort(self, dependencies, all_nodes):
        """
        拓扑排序，确定节点执行顺序
        """
        # 计算每个节点的入度
        in_degree = {node: 0 for node in all_nodes}
        
        for node in all_nodes:
            for dep_node in dependencies[node]:
                in_degree[node] += 1
        
        # 使用Kahn算法进行拓扑排序
        queue = deque()
        for node in all_nodes:
            if in_degree[node] == 0:
                queue.append(node)
        
        sorted_nodes = []
        while queue:
            current_node = queue.popleft()
            sorted_nodes.append(current_node)
            
            # 遍历所有节点，减少依赖当前节点的节点的入度
            for node in all_nodes:
                if current_node in dependencies[node]:
                    in_degree[node] -= 1
                    if in_degree[node] == 0:
                        queue.append(node)
        
        # 如果排序后的节点数量小于原始节点数量，说明存在循环依赖
        if len(sorted_nodes) != len(all_nodes):
            raise ValueError("节点图中存在循环依赖")
            
        return sorted_nodes
    
    def _execute_node(self, node):
        """
        执行单个节点
        """
        # 获取节点的输入数据
        inputs = self._get_node_inputs(node)
        
        # 执行节点处理逻辑
        if hasattr(node, 'process'):
            outputs = node.process(inputs)
        else:
            # 如果节点没有process方法，尝试使用通用处理方法
            outputs = self._generic_process(node, inputs)
        
        # 保存节点输出
        if outputs:
            self.node_outputs[node.id] = outputs
            
    def _get_node_inputs(self, node):
        """
        获取节点的输入数据
        """
        inputs = []
        
        for input_port in node.input_ports():
            connected_ports = input_port.connected_ports()
            
            port_inputs = []
            for connected_port in connected_ports:
                # 获取连接的节点ID
                source_node = connected_port.node()
                source_node_id = source_node.id
                
                # 获取源节点的输出数据
                if source_node_id in self.node_outputs:
                    output_data = self.node_outputs[source_node_id]
                    
                    # 如果输出数据是字典，根据端口名称获取对应输出
                    if isinstance(output_data, dict):
                        port_name = connected_port.name()
                        if port_name in output_data:
                            port_inputs.append(output_data[port_name])
                    else:
                        # 如果输出数据不是字典，直接使用
                        port_inputs.append(output_data)
            
            # 将端口的所有输入合并到节点的输入列表中
            inputs.extend(port_inputs)
        
        return inputs
    
    def _generic_process(self, node, inputs):
        """
        通用节点处理方法（备用）
        """
        print(f"警告: 节点 {node.name()} 没有实现 process 方法")
        return {}
