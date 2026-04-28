"""
JSON数据显示节点 - 以表格形式显示JSON数据结果
"""

from shared_libs.node_base import BaseNode
import json


class JsonDisplayNode(BaseNode):
    """
    JSON数据显示节点
    
    接收JSON字符串输入，以结构化表格形式显示数据
    
    功能说明：
    - 解析JSON字符串
    - 支持嵌套对象展开显示
    - 以键值对表格形式展示
    - 支持数组类型数据显示
    
    硬件要求：
    - CPU: 1+ 核心
    - 内存: 1GB+
    - GPU: 不需要
    """
    
    __identifier__ = 'io_camera'
    NODE_NAME = 'JSON数据显示'
    
    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(JsonDisplayNode, self).__init__()
        
        # 输入端口 - 接收JSON字符串
        self.add_input('JSON数据', color=(100, 100, 255))
        
        # 输出端口 - 传递原始数据
        self.add_output('原始数据', color=(100, 100, 255))
        
        # 添加文本显示区域（多行）
        self.add_text_input('display_data', '数据显示', tab='properties')
        
        # 缓存解析后的数据
        self._parsed_data = None
    
    def _format_json_to_table(self, data, indent=0):
        """
        将JSON数据格式化为表格字符串
        
        Args:
            data: JSON数据（字典、列表或基本类型）
            indent: 缩进层级
            
        Returns:
            str: 格式化后的表格字符串
        """
        lines = []
        prefix = "  " * indent
        
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    lines.append(f"{prefix}{key}:")
                    lines.append(self._format_json_to_table(value, indent + 1))
                else:
                    lines.append(f"{prefix}{key}: {value}")
        elif isinstance(data, list):
            for i, item in enumerate(data):
                if isinstance(item, (dict, list)):
                    lines.append(f"{prefix}[{i}]:")
                    lines.append(self._format_json_to_table(item, indent + 1))
                else:
                    lines.append(f"{prefix}[{i}]: {item}")
        else:
            lines.append(f"{prefix}{data}")
        
        return "\n".join(lines)
    
    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: 输入数据列表，inputs[0]为JSON字符串
            
        Returns:
            dict: 包含原始数据的字典
        """
        try:
            # Step 1: 获取输入数据
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.set_property('display_data', '无输入数据')
                self._parsed_data = None
                return {'原始数据': None}
            
            json_str = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if not isinstance(json_str, str):
                self.set_property('display_data', '输入不是字符串类型')
                self._parsed_data = None
                return {'原始数据': None}
            
            # Step 2: 解析JSON字符串
            try:
                parsed_data = json.loads(json_str)
                self._parsed_data = parsed_data
            except json.JSONDecodeError as e:
                error_msg = f"JSON解析错误: {str(e)}"
                self.set_property('display_data', error_msg)
                self.log_error(error_msg)
                return {'原始数据': None}
            
            # Step 3: 格式化为表格显示
            table_str = self._format_json_to_table(parsed_data)
            
            # Step 4: 更新显示内容
            display_text = f"=== JSON 数据 ===\n\n{table_str}"
            self.set_property('display_data', display_text)
            
            self.log_success(f"JSON数据显示完成，共 {len(parsed_data) if isinstance(parsed_data, dict) else 'N/A'} 个字段")
            
            # Step 5: 输出原始解析数据供下游使用
            return {'原始数据': parsed_data}
            
        except Exception as e:
            error_msg = f"处理错误: {str(e)}"
            self.set_property('display_data', error_msg)
            self.log_error(f"JSON显示节点错误: {e}")
            return {'原始数据': None}
    
    def get_parsed_data(self):
        """
        获取解析后的数据
        
        Returns:
            dict/list or None: 解析后的JSON数据
        """
        return self._parsed_data
