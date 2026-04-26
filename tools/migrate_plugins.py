"""
插件迁移工具 - 自动为现有 OpenCV 插件添加资源等级和硬件要求声明

使用方法：
    python tools/migrate_plugins.py [--plugin-name PLUGIN_NAME]

示例：
    python tools/migrate_plugins.py                    # 迁移所有插件
    python tools/migrate_plugins.py --plugin-name io_camera  # 仅迁移指定插件
"""

import json
import os
import sys
from pathlib import Path


def migrate_plugin(plugin_name: str, plugins_dir: str = "src/python/user_plugins") -> bool:
    """
    迁移单个插件的 plugin.json
    
    Args:
        plugin_name: 插件名称
        plugins_dir: 插件目录路径
        
    Returns:
        bool: 是否成功
    """
    plugin_json_path = os.path.join(plugins_dir, plugin_name, "plugin.json")
    
    if not os.path.exists(plugin_json_path):
        print(f"❌ 插件不存在: {plugin_name}")
        return False
    
    print(f"\n{'='*60}")
    print(f"迁移插件: {plugin_name}")
    print(f"{'='*60}")
    
    # 读取原始 JSON
    with open(plugin_json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 检查是否已经迁移过
    if 'resource_level' in data.get('nodes', [{}])[0]:
        print(f"⚠️  插件 {plugin_name} 已经迁移过，跳过")
        return True
    
    # 确定资源等级（默认为 light）
    resource_level = "light"
    
    # 为每个节点添加资源等级和硬件要求
    updated_nodes = []
    for node in data.get('nodes', []):
        node_copy = node.copy()
        
        # 添加资源等级
        if 'resource_level' not in node_copy:
            node_copy['resource_level'] = resource_level
        
        # 添加硬件要求
        if 'hardware_requirements' not in node_copy:
            node_copy['hardware_requirements'] = {
                "cpu_cores": 1,
                "memory_gb": 1,
                "gpu_required": False,
                "gpu_memory_gb": 0
            }
        
        # 添加依赖声明
        if 'dependencies' not in node_copy:
            node_copy['dependencies'] = ["opencv-python>=4.5.0"]
        
        # 添加可选依赖
        if 'optional_dependencies' not in node_copy:
            node_copy['optional_dependencies'] = {}
        
        updated_nodes.append(node_copy)
    
    data['nodes'] = updated_nodes
    
    # 添加插件级资源等级
    if 'resource_level' not in data:
        data['resource_level'] = resource_level
    
    # 添加硬件推荐
    if 'hardware_recommendations' not in data:
        data['hardware_recommendations'] = {
            "factory_deployment": "适合工厂现场部署，低资源消耗",
            "office_workstation": "适合办公室工作站",
            "cloud_training": "不需要云端训练"
        }
    
    # 写回文件
    with open(plugin_json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ 插件 {plugin_name} 迁移完成")
    print(f"   - 节点数量: {len(updated_nodes)}")
    print(f"   - 资源等级: {resource_level}")
    
    return True


def migrate_all_plugins(plugins_dir: str = "src/python/user_plugins"):
    """迁移所有插件"""
    plugins = [
        'io_camera',
        'feature_extraction', 
        'measurement',
        'recognition',
        'match_location',
        'integration',
        'example_advanced_nodes'
    ]
    
    success_count = 0
    fail_count = 0
    
    for plugin_name in plugins:
        try:
            if migrate_plugin(plugin_name, plugins_dir):
                success_count += 1
            else:
                fail_count += 1
        except Exception as e:
            print(f"❌ 迁移失败: {plugin_name} - {e}")
            fail_count += 1
    
    print(f"\n\n{'='*60}")
    print(f"迁移总结")
    print(f"{'='*60}")
    print(f"✅ 成功: {success_count}")
    print(f"❌ 失败: {fail_count}")
    print(f"📊 总计: {success_count + fail_count}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='迁移 OpenCV 插件到新体系')
    parser.add_argument('--plugin-name', type=str, help='指定要迁移的插件名称')
    
    args = parser.parse_args()
    
    if args.plugin_name:
        migrate_plugin(args.plugin_name)
    else:
        migrate_all_plugins()
