#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
节点脚手架工具 - 快速创建新节点

用法:
    python tools/create_node.py

功能:
    1. 引导用户选择插件包
    2. 输入节点类名和显示名称
    3. 选择节点类型（OpenCV / AI / Async AI）
    4. 自动生成节点文件
    5. 自动更新 __init__.py
    6. 自动更新 plugin.json
"""

import json
import os
import sys
from pathlib import Path


def get_plugin_list():
    """获取所有可用的插件包"""
    plugins_dir = Path(__file__).parent.parent / "src" / "python" / "user_plugins"
    
    if not plugins_dir.exists():
        print(f"❌ 插件目录不存在: {plugins_dir}")
        return []
    
    plugins = []
    for item in plugins_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            plugin_json = item / "plugin.json"
            if plugin_json.exists():
                with open(plugin_json, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    plugins.append({
                        'name': item.name,
                        'display_name': data.get('description', ''),
                        'path': item
                    })
    
    return sorted(plugins, key=lambda x: x['name'])


def select_plugin(plugins):
    """让用户选择插件包"""
    print("\n" + "=" * 80)
    print("📦 可用插件包列表:")
    print("=" * 80)
    
    for i, plugin in enumerate(plugins, 1):
        print(f"{i}. {plugin['name']:30s} - {plugin['display_name'][:40]}")
    
    print("\n0. 退出")
    
    while True:
        try:
            choice = input("\n请选择插件包编号 (0-{0}): ".format(len(plugins)))
            choice = int(choice)
            
            if choice == 0:
                return None
            
            if 1 <= choice <= len(plugins):
                return plugins[choice - 1]
            else:
                print("❌ 无效的选择，请重新输入")
        except ValueError:
            print("❌ 请输入有效的数字")


def get_node_info():
    """获取节点信息"""
    print("\n" + "=" * 80)
    print("📝 节点信息")
    print("=" * 80)
    
    # 节点类名
    while True:
        class_name = input("节点类名 (如: MyNode): ").strip()
        if class_name and class_name[0].isupper() and class_name.isidentifier():
            break
        print("❌ 类名必须以大写字母开头，且为有效的标识符")
    
    # 节点显示名称
    display_name = input("节点显示名称 (如: 我的节点): ").strip()
    if not display_name:
        display_name = class_name
    
    # 节点类型
    print("\n节点类型:")
    print("1. BaseNode       - 传统 OpenCV 节点（同步）")
    print("2. AIBaseNode     - AI 节点（同步，带依赖检查）")
    print("3. AsyncAINode    - AI 节点（异步，支持取消）")
    
    while True:
        type_choice = input("\n请选择节点类型 (1/2/3): ").strip()
        if type_choice in ['1', '2', '3']:
            break
        print("❌ 无效的选择")
    
    node_types = {
        '1': {'base_class': 'BaseNode', 'async': False},
        '2': {'base_class': 'AIBaseNode', 'async': False},
        '3': {'base_class': 'AsyncAINode', 'async': True}
    }
    
    return {
        'class_name': class_name,
        'display_name': display_name,
        'node_type': node_types[type_choice]
    }


def generate_node_code(node_info, plugin_name):
    """生成节点代码"""
    class_name = node_info['class_name']
    base_class = node_info['node_type']['base_class']
    is_async = node_info['node_type']['async']
    
    # 计算导入路径的层级
    # 假设节点文件在: plugin_name/nodes/node_name.py
    # base_nodes 在: user_plugins/base_nodes.py
    # 需要向上 3 层：nodes -> plugin_name -> user_plugins
    import_path = "...base_nodes" if not is_async else "...base_nodes"
    
    code = f'''"""
{node_info['display_name']} 节点

自动生成于 {{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}}
"""

from {import_path} import {base_class}
import cv2
import numpy as np


class {class_name}({base_class}):
    """{node_info['display_name']} 节点"""
    
    __identifier__ = '{plugin_name}'
    NODE_NAME = '{node_info['display_name']}'
'''
    
    # 如果是 AI 节点，添加资源声明
    if base_class in ['AIBaseNode', 'AsyncAINode']:
        code += f'''    resource_level = "light"
    hardware_requirements = {{
        'cpu_cores': 2,
        'memory_gb': 2,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }}
'''
    
    # 添加 __init__ 方法
    code += f'''
    def __init__(self):
        super({class_name}, self).__init__()
        # 定义输入端口
        self.add_input('输入图像', color=(100, 255, 100))
        
        # 定义输出端口
        self.add_output('输出图像', color=(100, 255, 100))
        
        # TODO: 添加参数控件
        # self.add_text_input('param1', '参数1', tab='properties')
        # self.set_property('param1', 'default_value')
'''
    
    # 添加 process 或 async_process 方法
    if is_async:
        code += f'''
    async def async_process(self, inputs=None):
        """异步处理逻辑"""
        try:
            # 1. 获取输入
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("无输入图像")
                return {{'输出图像': None}}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            # 2. TODO: 执行处理逻辑
            
            # 3. 返回结果
            self.log_success("处理完成")
            return {{'输出图像': image}}
        
        except Exception as e:
            self.log_error(f"处理失败: {{e}}")
            return {{'输出图像': None}}
'''
    else:
        code += f'''
    def process(self, inputs=None):
        """处理逻辑"""
        try:
            # 1. 获取输入
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                return {{'输出图像': None}}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            # 2. TODO: 执行处理逻辑
            result = image  # 替换为实际处理代码
            
            # 3. 返回结果
            return {{'输出图像': result}}
        
        except Exception as e:
            print(f"处理错误: {{e}}")
            return {{'输出图像': None}}
'''
    
    return code


def create_node_file(plugin_path, node_info):
    """创建节点文件"""
    nodes_dir = plugin_path / "nodes"
    
    if not nodes_dir.exists():
        print(f"❌ nodes 目录不存在: {nodes_dir}")
        return None
    
    # 生成文件名
    filename = f"{node_info['class_name'].lower()}.py"
    filepath = nodes_dir / filename
    
    if filepath.exists():
        overwrite = input(f"⚠️  文件已存在: {filepath}\n是否覆盖? (y/n): ").strip().lower()
        if overwrite != 'y':
            return None
    
    # 生成代码
    from datetime import datetime
    code = generate_node_code(node_info, plugin_path.name)
    
    # 写入文件
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(code)
    
    print(f"✅ 创建节点文件: {filepath}")
    return filepath


def update_init_py(plugin_path, node_info):
    """更新 nodes/__init__.py"""
    init_file = plugin_path / "nodes" / "__init__.py"
    
    if not init_file.exists():
        print(f"❌ __init__.py 不存在: {init_file}")
        return False
    
    # 读取现有内容
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已经导入
    if node_info['class_name'] in content:
        print(f"⚠️  节点类已存在于 __init__.py")
        return True
    
    # 添加导入语句
    module_name = node_info['class_name'].lower()
    import_line = f"from .{module_name} import {node_info['class_name']}"
    
    # 找到最后一行导入语句的位置
    lines = content.split('\n')
    insert_pos = 0
    
    for i, line in enumerate(lines):
        if line.startswith('from .') or line.startswith('import'):
            insert_pos = i + 1
    
    # 插入导入语句
    lines.insert(insert_pos, import_line)
    
    # 更新 __all__
    all_updated = False
    for i, line in enumerate(lines):
        if '__all__' in line:
            # 提取现有的类名列表
            if '[' in line and ']' in line:
                # 单行格式
                old_all = line
                classes = old_all.split('[')[1].split(']')[0]
                classes = [c.strip().strip("'\"") for c in classes.split(',') if c.strip()]
                classes.append(node_info['class_name'])
                new_all = f"__all__ = [{', '.join([repr(c) for c in classes])}]"
                lines[i] = new_all
                all_updated = True
            else:
                # 多行格式，找到结束位置
                j = i
                while ']' not in lines[j]:
                    j += 1
                # 在最后一个类名后添加新类
                lines[j-1] = lines[j-1].rstrip(',') + ','
                lines.insert(j, f"    '{node_info['class_name']}',")
                all_updated = True
            break
    
    if not all_updated:
        # 如果没有 __all__，添加一个
        lines.append(f"\n__all__ = ['{node_info['class_name']}']")
    
    # 写回文件
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    
    print(f"✅ 更新 __init__.py")
    return True


def update_plugin_json(plugin_path, node_info):
    """更新 plugin.json"""
    plugin_json = plugin_path / "plugin.json"
    
    if not plugin_json.exists():
        print(f"❌ plugin.json 不存在: {plugin_json}")
        return False
    
    # 读取现有配置
    with open(plugin_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 检查节点是否已存在
    for node in data.get('nodes', []):
        if node.get('class') == node_info['class_name']:
            print(f"⚠️  节点已在 plugin.json 中注册")
            return True
    
    # 创建新节点配置
    base_class = node_info['node_type']['base_class']
    
    node_config = {
        "class": node_info['class_name'],
        "display_name": node_info['display_name'],
        "category": "自定义",
        "color": [200, 200, 200],
        "resource_level": "light",
        "hardware_requirements": {
            "cpu_cores": 2,
            "memory_gb": 2,
            "gpu_required": False,
            "gpu_memory_gb": 0
        },
        "dependencies": ["opencv-python>=4.5.0"],
        "optional_dependencies": {}
    }
    
    # 如果是 AI 节点，添加 ultralytics 依赖
    if base_class in ['AIBaseNode', 'AsyncAINode']:
        node_config['dependencies'].append("ultralytics>=8.0.0")
    
    # 添加到节点列表
    if 'nodes' not in data:
        data['nodes'] = []
    
    data['nodes'].append(node_config)
    
    # 写回文件
    with open(plugin_json, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 更新 plugin.json")
    return True


def main():
    """主函数"""
    print("=" * 80)
    print("🚀 StduyOpenCV 节点脚手架工具")
    print("=" * 80)
    
    # 获取插件列表
    plugins = get_plugin_list()
    
    if not plugins:
        print("❌ 未找到任何插件包")
        return
    
    # 选择插件
    plugin = select_plugin(plugins)
    
    if not plugin:
        print("👋 已取消")
        return
    
    print(f"\n✅ 已选择插件: {plugin['name']}")
    
    # 获取节点信息
    node_info = get_node_info()
    
    print(f"\n📋 节点信息:")
    print(f"   类名: {node_info['class_name']}")
    print(f"   显示名称: {node_info['display_name']}")
    print(f"   类型: {node_info['node_type']['base_class']}")
    
    confirm = input("\n确认创建? (y/n): ").strip().lower()
    if confirm != 'y':
        print("👋 已取消")
        return
    
    # 创建节点文件
    print("\n" + "-" * 80)
    print("🔨 开始创建节点...")
    print("-" * 80)
    
    node_file = create_node_file(plugin['path'], node_info)
    
    if not node_file:
        print("❌ 创建节点文件失败")
        return
    
    # 更新 __init__.py
    if not update_init_py(plugin['path'], node_info):
        print("❌ 更新 __init__.py 失败")
        return
    
    # 更新 plugin.json
    if not update_plugin_json(plugin['path'], node_info):
        print("❌ 更新 plugin.json 失败")
        return
    
    # 完成
    print("\n" + "=" * 80)
    print("🎉 节点创建成功！")
    print("=" * 80)
    print(f"\n📁 节点文件: {node_file}")
    print(f"\n💡 下一步:")
    print(f"   1. 编辑节点文件，实现处理逻辑")
    print(f"   2. 重启应用程序测试节点")
    print(f"   3. 在工作流中使用新节点")
    print("\n📚 参考文档:")
    print(f"   - docs/UNIFIED_NODE_DEVELOPMENT_GUIDE.md")
    print(f"   - docs/PLUGIN_MIGRATION_TUTORIAL.md")


if __name__ == "__main__":
    main()
