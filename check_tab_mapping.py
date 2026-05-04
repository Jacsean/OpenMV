"""
检查节点库标签页名称映射

验证category_group到标签页名称的转换是否正确
"""

import sys
sys.path.insert(0, 'src/python')

from plugins.plugin_manager import PluginManager

print("=" * 70)
print("检查节点库标签页名称映射")
print("=" * 70)

# 扫描插件
pm = PluginManager()
plugins = pm.scan_plugins()

print(f"\n扫描到 {len(plugins)} 个插件\n")

# 构建 category_group 到插件的映射
category_groups = {}
for plugin in plugins:
    cg = getattr(plugin, 'category_group', plugin.name)
    if cg not in category_groups:
        category_groups[cg] = []
    category_groups[cg].append(plugin.name)

print("分类组映射:")
for cg, plugin_names in sorted(category_groups.items()):
    print(f"   📁 {cg}")
    for name in plugin_names:
        print(f"      - {name}")

# 特别检查"图像相机"
print("\n" + "=" * 70)
if "图像相机" in category_groups:
    print("✅ 找到 '图像相机' 分类组")
    print(f"   包含插件: {', '.join(category_groups['图像相机'])}")
    
    # 检查io_camera的详细信息
    io_camera_plugin = pm.get_plugin('io_camera')
    if io_camera_plugin:
        print(f"\n   io_camera 详情:")
        print(f"      - category_group: {io_camera_plugin.category_group}")
        print(f"      - 节点数: {len(io_camera_plugin.nodes)}")
        print(f"      - 节点列表:")
        for node in io_camera_plugin.nodes:
            print(f"         • {node.display_name} (category={node.category})")
else:
    print("❌ 未找到 '图像相机' 分类组")
    print(f"   可用的分类组: {list(category_groups.keys())}")

print("=" * 70)
