"""
JSON数据显示节点 - 以清单列表形式显示JSON数据结果
"""

from shared_libs.node_base import BaseNode
import json


class JsonDisplayNode(BaseNode):
    """
    JSON数据显示节点
    
    接收JSON字符串输入，以清单列表形式在节点上显示所有字段及其值
    
    功能说明：
    - 解析JSON字符串
    - 支持嵌套对象展开显示
    - 在节点本体上以清单/列表方式显示字段和值
    - 支持数组类型数据显示
    - 属性面板中提供完整JSON文本查看
    
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
        
        # 属性面板中的完整JSON文本显示
        self.add_text_input('full_json_text', '完整JSON文本', tab='properties')
        
        # 缓存解析后的数据和字段数量
        self._parsed_data = None
        self._field_count = 0
        
        # 用于跟踪已添加的动态属性
        self._dynamic_properties = []
    
    def _clear_dynamic_properties(self):
        """清除之前添加的动态属性"""
        for prop_name in self._dynamic_properties:
            try:
                # NodeGraphQt不支持直接删除属性，我们将其设置为空
                self.set_property(prop_name, '')
            except:
                pass
        self._dynamic_properties.clear()
    
    def _flatten_json(self, data, prefix=''):
        """
        将嵌套的JSON数据扁平化为键值对列表
        
        Args:
            data: JSON数据（字典、列表或基本类型）
            prefix: 前缀键名
            
        Returns:
            list: [(key, value), ...] 元组列表
        """
        items = []
        
        if isinstance(data, dict):
            for key, value in data.items():
                full_key = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    # 对于嵌套结构，添加标题并递归处理
                    items.append((full_key, '[复杂类型]'))
                    items.extend(self._flatten_json(value, full_key))
                else:
                    items.append((full_key, value))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                full_key = f"{prefix}[{i}]"
                if isinstance(item, (dict, list)):
                    items.append((full_key, '[复杂类型]'))
                    items.extend(self._flatten_json(item, full_key))
                else:
                    items.append((full_key, item))
        else:
            items.append((prefix if prefix else '值', data))
        
        return items
    
    def _format_value_for_display(self, value):
        """
        格式化值以便显示
        
        Args:
            value: 要格式化的值
            
        Returns:
            str: 格式化后的字符串
        """
        if isinstance(value, float):
            return f"{value:.4f}"
        elif isinstance(value, bool):
            return "是" if value else "否"
        elif value is None:
            return "空"
        else:
            return str(value)
    
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
                self._clear_dynamic_properties()
                self.set_property('full_json_text', '无输入数据')
                self._parsed_data = None
                self._field_count = 0
                # 更新节点名称显示状态
                self.NODE_NAME = 'JSON数据显示 (无数据)'
                return {'原始数据': None}
            
            json_str = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if not isinstance(json_str, str):
                self._clear_dynamic_properties()
                self.set_property('full_json_text', '输入不是字符串类型')
                self._parsed_data = None
                self._field_count = 0
                self.NODE_NAME = 'JSON数据显示 (错误)'
                return {'原始数据': None}
            
            # Step 2: 解析JSON字符串
            try:
                parsed_data = json.loads(json_str)
                self._parsed_data = parsed_data
            except json.JSONDecodeError as e:
                error_msg = f"JSON解析错误: {str(e)}"
                self._clear_dynamic_properties()
                self.set_property('full_json_text', error_msg)
                self.log_error(error_msg)
                self._field_count = 0
                self.NODE_NAME = 'JSON数据显示 (解析失败)'
                return {'原始数据': None}
            
            # Step 3: 保存完整JSON文本到属性面板
            formatted_json = json.dumps(parsed_data, ensure_ascii=False, indent=2)
            self.set_property('full_json_text', formatted_json)
            
            # Step 4: 清除之前的动态属性
            self._clear_dynamic_properties()
            
            # Step 5: 扁平化JSON数据并生成字段列表
            flat_items = self._flatten_json(parsed_data)
            self._field_count = len([item for item in flat_items if item[1] != '[复杂类型]'])
            
            # Step 6: 构建清单显示文本（用于日志和调试）
            display_lines = ["=== JSON 数据清单 ===", ""]
            for key, value in flat_items:
                if value != '[复杂类型]':
                    formatted_value = self._format_value_for_display(value)
                    display_lines.append(f"• {key}: {formatted_value}")
            
            display_text = "\n".join(display_lines)
            
            # Step 7: 更新节点名称以显示字段数量
            self.NODE_NAME = f'JSON数据显示 ({self._field_count}个字段)'
            
            self.log_success(f"JSON数据显示完成，共 {self._field_count} 个字段")
            self.log_info(display_text)
            
            # Step 8: 输出原始解析数据供下游使用
            return {'原始数据': parsed_data}
            
        except Exception as e:
            error_msg = f"处理错误: {str(e)}"
            self._clear_dynamic_properties()
            self.set_property('full_json_text', error_msg)
            self.log_error(f"JSON显示节点错误: {e}")
            self._field_count = 0
            self.NODE_NAME = 'JSON数据显示 (异常)'
            return {'原始数据': None}
    
    def get_parsed_data(self):
        """
        获取解析后的数据
        
        Returns:
            dict/list or None: 解析后的JSON数据
        """
        return self._parsed_data
    
    def get_field_count(self):
        """
        获取字段数量
        
        Returns:
            int: 字段数量
        """
        return self._field_count
