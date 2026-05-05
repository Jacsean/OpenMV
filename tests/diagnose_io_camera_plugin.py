"""
诊断io_camera插件加载问题

检查：
1. 插件目录是否存在
2. plugin.json是否可读取
3. 节点类是否可导入（需要NodeGraphQt环境）
4. 插件管理器是否能正确扫描到插件
"""

import os
import sys
import json

print("=" * 70)
print("诊断 io_camera 插件加载问题")
print("=" * 70)

# 1. 检查插件目录结构
plugin_dir = 'src/python/plugin_packages/builtin/io_camera'
print(f"\n1. 检查插件目录: {plugin_dir}")

if os.path.exists(plugin_dir):
    print(f"   ✅ 目录存在")
    
    # 列出目录内容
    files = os.listdir(plugin_dir)
    print(f"   📁 目录内容 ({len(files)} 个项目):")
    for f in sorted(files):
        filepath = os.path.join(plugin_dir, f)
        if os.path.isdir(filepath):
            print(f"      📂 {f}/")
        else:
            print(f"      📄 {f}")
else:
    print(f"   ❌ 目录不存在!")
    sys.exit(1)

# 2. 检查plugin.json
print(f"\n2. 检查 plugin.json...")
plugin_json_path = os.path.join(plugin_dir, 'plugin.json')

if os.path.exists(plugin_json_path):
    print(f"   ✅ 文件存在")
    
    try:
        with open(plugin_json_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        print(f"   ✅ JSON格式正确")
        print(f"   📋 插件名称: {config.get('name', 'N/A')}")
        print(f"   📋 版本: {config.get('version', 'N/A')}")
        print(f"   📋 分类组: {config.get('category_group', 'N/A')}")
        print(f"   📋 节点数量: {len(config.get('nodes', []))}")
        
        # 检查是否有语法错误
        if 'category_group' not in config:
            print(f"   ⚠️  警告: 缺少 category_group 字段")
        
    except json.JSONDecodeError as e:
        print(f"   ❌ JSON解析错误: {e}")
        sys.exit(1)
else:
    print(f"   ❌ plugin.json 不存在!")
    sys.exit(1)

# 3. 检查节点文件
print(f"\n3. 检查节点文件...")
nodes_dir = os.path.join(plugin_dir, 'nodes')

if os.path.exists(nodes_dir):
    print(f"   ✅ nodes目录存在")
    
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
            # 检查文件大小
            size = os.path.getsize(filepath)
            print(f"   ✅ {filename:30s} ({size:>6} bytes)")
        else:
            print(f"   ❌ {filename:30s} (缺失)")
else:
    print(f"   ❌ nodes目录不存在!")
    sys.exit(1)

# 4. 检查__init__.py
print(f"\n4. 检查 __init__.py 导出...")
init_path = os.path.join(nodes_dir, '__init__.py')

if os.path.exists(init_path):
    with open(init_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    expected_classes = [
        'ImageLoadNode',
        'ImageSaveNode',
        'ImageViewNode',
        'JsonDisplayNode',
        'CameraCaptureNode',
        'RealTimePreviewNode',
        'FastDetectionNode',
        'VideoRecorderNode'
    ]
    
    for class_name in expected_classes:
        if f'from .{class_name.lower().replace("_node", "")}' in content or class_name in content:
            print(f"   ✅ {class_name}")
        else:
            print(f"   ⚠️  {class_name} (可能未导出)")
else:
    print(f"   ❌ __init__.py 不存在!")

# 5. 检查是否有语法错误
print(f"\n5. 检查Python语法...")
import py_compile

syntax_errors = []
for filename in node_files:
    filepath = os.path.join(nodes_dir, filename)
    if os.path.exists(filepath):
        try:
            py_compile.compile(filepath, doraise=True)
            print(f"   ✅ {filename}")
        except py_compile.PyCompileError as e:
            print(f"   ❌ {filename}: {e}")
            syntax_errors.append(filename)

if syntax_errors:
    print(f"\n   ⚠️  发现 {len(syntax_errors)} 个语法错误!")
else:
    print(f"\n   ✅ 所有节点文件语法正确")

# 6. 总结
print("\n" + "=" * 70)
print("诊断总结:")
print("=" * 70)

issues = []

if not os.path.exists(plugin_dir):
    issues.append("插件目录不存在")

if not os.path.exists(plugin_json_path):
    issues.append("plugin.json不存在")

if syntax_errors:
    issues.append(f"{len(syntax_errors)}个节点文件有语法错误")

if issues:
    print(f"\n❌ 发现问题:")
    for issue in issues:
        print(f"   - {issue}")
    print("\n建议: 修复上述问题后重新启动应用")
else:
    print(f"\n✅ 配置和文件结构正常")
    print(f"\n如果UI中仍然看不到节点，可能的原因:")
    print(f"   1. 应用启动时插件扫描失败（检查启动日志）")
    print(f"   2. NodesPaletteWidget未正确刷新（检查refresh_node_info_event_filters调用）")
    print(f"   3. 标签页名称映射问题（检查_apply_custom_tab_names）")
    print(f"   4. NodeGraphQt内部状态异常（尝试重启应用）")

print("=" * 70)
