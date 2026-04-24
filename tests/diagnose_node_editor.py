"""
诊断脚本：检查节点编辑器能否正确加载插件包
"""

import sys
from pathlib import Path
import json

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src" / "python"))

print("=" * 60)
print("🔍 节点编辑器插件包加载诊断")
print("=" * 60)

# 1. 检查user_plugins目录
plugins_dir = Path(__file__).parent / "src" / "python" / "user_plugins"
print(f"\n📁 插件目录: {plugins_dir}")
print(f"   存在: {plugins_dir.exists()}")

if not plugins_dir.exists():
    print("❌ 插件目录不存在！")
    sys.exit(1)

# 2. 扫描插件包
plugin_packages = {}
for plugin_dir in plugins_dir.iterdir():
    if plugin_dir.is_dir():
        plugin_json = plugin_dir / "plugin.json"
        if plugin_json.exists():
            try:
                with open(plugin_json, 'r', encoding='utf-8') as f:
                    plugin_data = json.load(f)
                    plugin_packages[plugin_dir.name] = {
                        'path': plugin_dir,
                        'data': plugin_data
                    }
                print(f"✅ 找到插件包: {plugin_dir.name}")
                print(f"   - 版本: {plugin_data.get('version', 'N/A')}")
                print(f"   - 分类: {plugin_data.get('category_group', '未分类')}")
                print(f"   - 节点数: {len(plugin_data.get('nodes', []))}")
            except Exception as e:
                print(f"❌ 加载失败 {plugin_dir.name}: {e}")

print(f"\n📊 总计发现 {len(plugin_packages)} 个插件包")

# 3. 测试NodeEditorDialog初始化
print("\n🧪 测试NodeEditorDialog初始化...")
try:
    from PySide2 import QtWidgets
    from ui.node_editor import NodeEditorDialog
    
    app = QtWidgets.QApplication.instance()
    if app is None:
        app = QtWidgets.QApplication(sys.argv)
    
    editor = NodeEditorDialog(None, plugins_dir)
    
    print(f"✅ NodeEditorDialog创建成功")
    print(f"   - plugin_packages数量: {len(editor.plugin_packages)}")
    print(f"   - 包列表: {list(editor.plugin_packages.keys())}")
    
    # 检查树形视图
    tree_count = editor.package_tree.topLevelItemCount()
    print(f"   - 树形视图顶级项数: {tree_count}")
    
    for i in range(tree_count):
        category_item = editor.package_tree.topLevelItem(i)
        category_name = category_item.text(0)
        child_count = category_item.childCount()
        print(f"     • {category_name}: {child_count} 个子项")
        
except Exception as e:
    print(f"❌ NodeEditorDialog初始化失败: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 60)
print("诊断完成")
print("=" * 60)
