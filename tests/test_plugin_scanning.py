"""
测试插件扫描机制

模拟PluginManager扫描插件的过程
"""

import os
import sys
import json

print("=" * 70)
print("测试插件扫描机制")
print("=" * 70)

# 添加路径
sys.path.insert(0, 'src/python')

# 1. 检查内置插件目录
builtin_plugins_dir = 'src/python/plugin_packages/builtin'
print(f"\n1. 扫描内置插件目录: {builtin_plugins_dir}")

if os.path.exists(builtin_plugins_dir):
    plugin_dirs = [d for d in os.listdir(builtin_plugins_dir) 
                   if os.path.isdir(os.path.join(builtin_plugins_dir, d))]
    print(f"   找到 {len(plugin_dirs)} 个插件目录:")
    for d in sorted(plugin_dirs):
        print(f"      - {d}")
else:
    print(f"   ❌ 目录不存在")
    sys.exit(1)

# 2. 检查io_camera插件是否在其中
print(f"\n2. 检查 io_camera 插件...")
io_camera_dir = os.path.join(builtin_plugins_dir, 'io_camera')

if os.path.exists(io_camera_dir):
    print(f"   ✅ io_camera 目录存在")
    
    # 检查plugin.json
    plugin_json = os.path.join(io_camera_dir, 'plugin.json')
    if os.path.exists(plugin_json):
        print(f"   ✅ plugin.json 存在")
        
        with open(plugin_json, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"   📋 插件名称: {config['name']}")
        print(f"   📋 分类组: {config.get('category_group', 'N/A')}")
        print(f"   📋 节点数: {len(config.get('nodes', []))}")
        
        # 检查source字段
        source = config.get('source', 'unknown')
        print(f"   📋 来源: {source}")
        
        if source == 'builtin':
            print(f"   ✅ 标记为内置插件")
        else:
            print(f"   ⚠️  来源不是builtin: {source}")
    else:
        print(f"   ❌ plugin.json 不存在")
else:
    print(f"   ❌ io_camera 目录不存在")

# 3. 尝试导入PluginManager（如果可能）
print(f"\n3. 检查PluginManager...")
try:
    from plugins.plugin_manager import PluginManager
    print(f"   ✅ PluginManager可导入")
    
    # 创建实例
    pm = PluginManager()
    print(f"   ✅ PluginManager实例创建成功")
    
    # 扫描插件
    print(f"\n4. 执行插件扫描...")
    all_plugins = pm.scan_plugins()
    print(f"   扫描到 {len(all_plugins)} 个插件:")
    
    found_io_camera = False
    for plugin_info in all_plugins:
        print(f"      - {plugin_info.name} (source={plugin_info.source}, category_group={getattr(plugin_info, 'category_group', 'N/A')})")
        if plugin_info.name == 'io_camera':
            found_io_camera = True
            print(f"         ✅ 找到 io_camera!")
            print(f"         📋 节点数: {len(plugin_info.nodes)}")
            for node in plugin_info.nodes:
                print(f"            • {node.display_name} ({node.class_name})")
    
    if not found_io_camera:
        print(f"\n   ❌ 未扫描到 io_camera 插件!")
        print(f"   可能原因:")
        print(f"      1. plugin.json解析失败")
        print(f"      2. 节点类导入失败")
        print(f"      3. 插件被禁用")
    
except ImportError as e:
    print(f"   ⚠️  无法导入PluginManager: {e}")
    print(f"   跳过运行时测试")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)
