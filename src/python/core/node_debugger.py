"""
节点调试工具 - 提供节点运行时调试和诊断功能

功能:
- 节点状态检查
- 输入输出数据查看
- 执行日志记录
- 性能监控
- 错误诊断
"""

import time
import traceback
from collections import OrderedDict


class NodeDebugger:
    """
    节点调试工具类
    
    提供节点运行时的调试和诊断能力，帮助开发者排查节点问题。
    """
    
    def __init__(self):
        self._debug_mode = False
        self._log_buffer = []
        self._max_log_entries = 1000
        self._node_stats = {}
    
    @property
    def debug_mode(self):
        """是否启用调试模式"""
        return self._debug_mode
    
    @debug_mode.setter
    def debug_mode(self, value):
        """设置调试模式"""
        self._debug_mode = value
        if value:
            self.log("DEBUG", "节点调试模式已启用")
        else:
            self.log("INFO", "节点调试模式已禁用")
    
    def log(self, level, message, node_name=None):
        """
        记录调试日志
        
        Args:
            level: 日志级别 (DEBUG, INFO, WARNING, ERROR)
            message: 日志消息
            node_name: 节点名称（可选）
        """
        if not self._debug_mode and level == "DEBUG":
            return
        
        entry = {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'level': level,
            'node_name': node_name,
            'message': message
        }
        
        self._log_buffer.append(entry)
        
        # 限制日志缓冲区大小
        if len(self._log_buffer) > self._max_log_entries:
            self._log_buffer.pop(0)
        
        # 输出到控制台
        prefix = f"[{entry['timestamp']}] [{level}]"
        if node_name:
            prefix += f" [{node_name}]"
        print(f"{prefix} {message}")
    
    def inspect_node(self, node):
        """
        检查节点的完整状态
        
        Args:
            node: 节点实例
            
        Returns:
            dict: 节点状态信息
        """
        if node is None:
            return None
        
        try:
            state = {
                'id': node.id,
                'name': node.name(),
                'type': type(node).__name__,
                'class': f"{type(node).__module__}.{type(node).__name__}",
                'input_ports': [],
                'output_ports': [],
                'properties': {},
                'status': self._get_node_status(node)
            }
            
            # 获取输入端口
            for port in node.input_ports():
                state['input_ports'].append({
                    'name': port.name(),
                    'connected': len(port.connected_ports()) > 0,
                    'connections': [conn_port.node().name() for conn_port in port.connected_ports()]
                })
            
            # 获取输出端口
            for port in node.output_ports():
                state['output_ports'].append({
                    'name': port.name(),
                    'connected': len(port.connected_ports()) > 0,
                    'connections': [conn_port.node().name() for conn_port in port.connected_ports()]
                })
            
            # 获取属性
            if hasattr(node, 'get_properties'):
                try:
                    state['properties'] = node.get_properties()
                except Exception as e:
                    state['properties'] = {'error': str(e)}
            
            self.log("DEBUG", f"已检查节点状态: {node.name()}", node.name())
            
            return state
            
        except Exception as e:
            self.log("ERROR", f"检查节点状态失败: {e}", node.name if node else None)
            return None
    
    def _get_node_status(self, node):
        """获取节点状态描述"""
        if hasattr(node, 'get_state'):
            try:
                return node.get_state()
            except:
                pass
        
        # 默认状态检查
        if hasattr(node, 'is_active'):
            return "ACTIVE" if node.is_active() else "INACTIVE"
        
        return "UNKNOWN"
    
    def trace_execution(self, node, inputs):
        """
        追踪节点执行过程
        
        Args:
            node: 节点实例
            inputs: 输入数据
            
        Returns:
            dict: 执行追踪结果
        """
        result = {
            'node_name': node.name(),
            'start_time': time.time(),
            'inputs': self._format_inputs(inputs),
            'outputs': None,
            'execution_time': None,
            'success': False,
            'error': None
        }
        
        self.log("DEBUG", f"开始执行节点: {node.name()}", node.name())
        
        try:
            if hasattr(node, 'process'):
                outputs = node.process(inputs)
                result['outputs'] = self._format_outputs(outputs)
                result['success'] = True
                self.log("DEBUG", f"节点执行成功", node.name())
            else:
                result['error'] = "节点没有 process 方法"
                self.log("ERROR", "节点没有 process 方法", node.name())
                
        except Exception as e:
            result['error'] = str(e)
            result['traceback'] = traceback.format_exc()
            self.log("ERROR", f"节点执行失败: {e}", node.name())
        
        result['execution_time'] = (time.time() - result['start_time']) * 1000
        self.log("DEBUG", f"节点执行耗时: {result['execution_time']:.2f}ms", node.name())
        
        return result
    
    def _format_inputs(self, inputs):
        """格式化输入数据用于显示"""
        if inputs is None:
            return "None"
        
        if isinstance(inputs, list):
            formatted = []
            for i, item in enumerate(inputs):
                formatted.append(self._format_value(item, f"输入[{i}]"))
            return formatted
        
        return self._format_value(inputs, "输入")
    
    def _format_outputs(self, outputs):
        """格式化输出数据用于显示"""
        if outputs is None:
            return "None"
        
        if isinstance(outputs, dict):
            formatted = {}
            for key, value in outputs.items():
                formatted[key] = self._format_value(value, key)
            return formatted
        
        return self._format_value(outputs, "输出")
    
    def _format_value(self, value, label):
        """格式化单个值"""
        if value is None:
            return {'type': 'None', 'value': None}
        
        if isinstance(value, (int, float, str, bool)):
            return {
                'type': type(value).__name__,
                'value': value
            }
        
        if hasattr(value, 'shape'):  # numpy array or image
            return {
                'type': type(value).__name__,
                'shape': value.shape,
                'dtype': str(value.dtype) if hasattr(value, 'dtype') else None,
                'summary': f"{value.shape} {value.dtype if hasattr(value, 'dtype') else ''}"
            }
        
        if isinstance(value, list):
            return {
                'type': 'list',
                'length': len(value),
                'sample': value[:3] if len(value) > 3 else value
            }
        
        if isinstance(value, dict):
            return {
                'type': 'dict',
                'keys': list(value.keys()),
                'length': len(value)
            }
        
        return {
            'type': type(value).__name__,
            'repr': str(value)[:200]
        }
    
    def get_stats(self, node_id=None):
        """
        获取节点统计信息
        
        Args:
            node_id: 节点ID（可选，不传则返回所有）
            
        Returns:
            dict: 统计信息
        """
        if node_id:
            return self._node_stats.get(node_id, {})
        
        return self._node_stats
    
    def record_stat(self, node_id, key, value):
        """
        记录节点统计数据
        
        Args:
            node_id: 节点ID
            key: 统计键
            value: 统计值
        """
        if node_id not in self._node_stats:
            self._node_stats[node_id] = OrderedDict()
        
        self._node_stats[node_id][key] = value
    
    def clear_stats(self):
        """清除所有统计数据"""
        self._node_stats.clear()
        self.log("INFO", "统计数据已清除")
    
    def get_logs(self, count=None, level=None):
        """
        获取日志记录
        
        Args:
            count: 返回条数（默认全部）
            level: 过滤级别（DEBUG, INFO, WARNING, ERROR）
            
        Returns:
            list: 日志条目列表
        """
        logs = self._log_buffer
        
        if level:
            logs = [log for log in logs if log['level'] == level]
        
        if count:
            logs = logs[-count:]
        
        return logs
    
    def clear_logs(self):
        """清除日志缓冲区"""
        self._log_buffer.clear()
        self.log("INFO", "日志已清除")
    
    def validate_node(self, node):
        """
        验证节点是否有效
        
        Args:
            node: 节点实例
            
        Returns:
            dict: 验证结果
        """
        result = {
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        if node is None:
            result['valid'] = False
            result['issues'].append("节点为 None")
            return result
        
        # 检查必需属性
        required_attrs = ['id', 'name', 'input_ports', 'output_ports']
        for attr in required_attrs:
            if not hasattr(node, attr):
                result['valid'] = False
                result['issues'].append(f"缺少必需属性: {attr}")
        
        # 检查 process 方法
        if not hasattr(node, 'process'):
            result['warnings'].append("节点没有 process 方法")
        
        # 检查端口
        try:
            input_ports = node.input_ports()
            output_ports = node.output_ports()
            
            if len(input_ports) == 0 and len(output_ports) == 0:
                result['warnings'].append("节点没有输入/输出端口")
                
        except Exception as e:
            result['issues'].append(f"获取端口失败: {e}")
        
        # 检查标识符
        if hasattr(node, '__identifier__'):
            if not node.__identifier__:
                result['warnings'].append("__identifier__ 为空")
        else:
            result['warnings'].append("缺少 __identifier__ 属性")
        
        if hasattr(node, 'NODE_NAME'):
            if not node.NODE_NAME:
                result['warnings'].append("NODE_NAME 为空")
        else:
            result['warnings'].append("缺少 NODE_NAME 属性")
        
        if not result['valid']:
            self.log("WARNING", f"节点验证失败: {node.name() if hasattr(node, 'name') else 'Unknown'}")
        elif result['warnings']:
            self.log("INFO", f"节点验证通过，但有警告: {node.name()}", node.name() if hasattr(node, 'name') else None)
        
        return result


# 创建全局调试器实例
node_debugger = NodeDebugger()

# 便捷函数
def inspect_node(node):
    """检查节点状态"""
    return node_debugger.inspect_node(node)

def trace_execution(node, inputs):
    """追踪节点执行"""
    return node_debugger.trace_execution(node, inputs)

def validate_node(node):
    """验证节点"""
    return node_debugger.validate_node(node)

def enable_debug():
    """启用调试模式"""
    node_debugger.debug_mode = True

def disable_debug():
    """禁用调试模式"""
    node_debugger.debug_mode = False

def get_debug_logs(count=None, level=None):
    """获取调试日志"""
    return node_debugger.get_logs(count, level)