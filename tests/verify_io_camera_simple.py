"""
简化验证：仅检查plugin.json和文件结构
不依赖任何GUI框架
"""

import json
import os

print("=" * 60)
print("验证 io_camera 插件配置")
print("=" * 60)

# 1. 检查plugin.json
plugin_json_path = 'src/python/plugin_packages/builtin/io_camera/plugin.json'
print(f"\n1. 加载 {plugin_json_path}...")

with open(plugin_json_path, 'r', encoding='utf-8') as f:
    plugin_config = json.load(f)

print(f"   ✅ 插件名称: {plugin_config['name']}")
print(f"   ✅ 分类组: {plugin_config['category_group']}")
print(f"   ✅ 节点数量: {len(plugin_config['nodes'])}")

print("\n2. 节点列表:")
for i, node_config in enumerate(plugin_config['nodes'], 1):
    class_name = node_config['class']
    display_name = node_config['display_name']
    category = node_config.get('category', 'N/A')
    print(f"   {i}. {class_name:30s} -> {display_name:20s} ({category})")

# 2. 检查节点文件是否存在
print("\n3. 检查节点文件:")
nodes_dir = 'src/python/plugin_packages/builtin/io_camera/nodes'
node_files = [
    'image_load.py',
    'image_save.py',
    'image_view.py',
    'json_display.py',
    'camera_capture.py',
    'realtime_preview.py',
    'fast_detection.py',
    'video_recorder.py'
]

for filename in node_files:
    filepath = os.path.join(nodes_dir, filename)
    if os.path.exists(filepath):
        print(f"   ✅ {filename}")
    else:
        print(f"   ❌ {filename} (缺失)")

# 3. 检查__init__.py导出
print("\n4. 检查 __init__.py 导出:")
init_path = os.path.join(nodes_dir, '__init__.py')
with open(init_path, 'r', encoding='utf-8') as f:
    init_content = f.read()

expected_exports = [
    'ImageLoadNode',
    'ImageSaveNode',
    'ImageViewNode',
    'JsonDisplayNode',
    'CameraCaptureNode',
    'RealTimePreviewNode',
    'FastDetectionNode',
    'VideoRecorderNode'
]

for class_name in expected_exports:
    if class_name in init_content:
        print(f"   ✅ {class_name}")
    else:
        print(f"   ❌ {class_name} (未导出)")

print("\n" + "=" * 60)
print("✅ 配置验证完成")
print("=" * 60)
