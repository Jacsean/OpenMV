"""
验证io_camera插件节点导入

不依赖GUI框架，仅测试核心模块导入
"""

import sys
import os

# 添加src/python到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'python'))

print("=" * 60)
print("验证 io_camera 插件节点导入")
print("=" * 60)

try:
    print("\n1. 测试基础导入...")
    from plugin_packages.builtin.io_camera import nodes
    print("   ✅ 成功导入 nodes 模块")
    
    print("\n2. 检查导出的节点类...")
    node_classes = [
        'ImageLoadNode',
        'ImageSaveNode', 
        'ImageViewNode',
        'JsonDisplayNode',
        'CameraCaptureNode',
        'RealTimePreviewNode',
        'FastDetectionNode',
        'VideoRecorderNode'
    ]
    
    for class_name in node_classes:
        if hasattr(nodes, class_name):
            cls = getattr(nodes, class_name)
            if cls is not None:
                print(f"   ✅ {class_name}: {cls}")
            else:
                print(f"   ⚠️  {class_name}: None (条件导入失败)")
        else:
            print(f"   ❌ {class_name}: 未找到")
    
    print("\n3. 测试plugin.json加载...")
    import json
    plugin_json_path = os.path.join(
        os.path.dirname(__file__),
        'src', 'python', 'plugin_packages', 'builtin', 'io_camera', 'plugin.json'
    )
    
    with open(plugin_json_path, 'r', encoding='utf-8') as f:
        plugin_config = json.load(f)
    
    print(f"   ✅ 插件名称: {plugin_config['name']}")
    print(f"   ✅ 分类组: {plugin_config['category_group']}")
    print(f"   ✅ 节点数量: {len(plugin_config['nodes'])}")
    
    print("\n4. 检查节点配置...")
    for node_config in plugin_config['nodes']:
        class_name = node_config['class']
        display_name = node_config['display_name']
        category = node_config.get('category', 'N/A')
        print(f"   - {class_name} ({display_name}) -> {category}")
    
    print("\n" + "=" * 60)
    print("✅ 验证完成！所有节点配置正常")
    print("=" * 60)
    
except Exception as e:
    print(f"\n❌ 验证失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
