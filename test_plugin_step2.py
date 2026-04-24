"""
Step 2 测试脚本 - 验证插件节点动态加载与注册
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'python'))

from PySide2 import QtWidgets
from NodeGraphQt import NodeGraph
from plugins.plugin_manager import PluginManager


def test_step2():
    """测试Step 2: 插件节点动态加载"""
    print("=" * 60)
    print("测试 Step 2: 插件节点动态加载与注册")
    print("=" * 60)
    
    # 1. 创建NodeGraph
    app = QtWidgets.QApplication(sys.argv)
    graph = NodeGraph()
    
    print("\n✅ 1. NodeGraph 创建成功")
    
    # 2. 扫描并加载插件
    pm = PluginManager()
    plugins = pm.scan_plugins()
    
    if not plugins:
        print("\n❌ 未找到插件")
        return False
    
    print(f"\n📦 发现 {len(plugins)} 个插件")
    
    # 3. 加载插件节点
    plugin = plugins[0]
    success = pm.load_plugin_nodes(plugin.name, graph)
    
    if success:
        print("\n✅ 2. 插件节点加载成功")
    else:
        print("\n❌ 2. 插件节点加载失败")
        return False
    
    # 4. 验证节点已注册
    registered_nodes = graph.registered_nodes()
    print(f"\n📊 已注册节点标识符: {registered_nodes}")
    
    # 检查是否包含形态学节点
    has_dilate = any('DilateNode' in str(n) for n in registered_nodes)
    has_erode = any('ErodeNode' in str(n) for n in registered_nodes)
    
    if has_dilate and has_erode:
        print(f"✅ 3. 找到形态学节点:")
        print(f"   - 膨胀 (DilateNode)")
        print(f"   - 腐蚀 (ErodeNode)")
    else:
        print("❌ 3. 未找到形态学节点")
        print(f"   has_dilate: {has_dilate}, has_erode: {has_erode}")
        return False
    
    # 5. 尝试创建节点实例
    try:
        dilate_node = graph.create_node('morphology.DilateNode')
        print(f"\n✅ 4. 成功创建节点实例: {dilate_node.name()}")
    except Exception as e:
        print(f"\n❌ 4. 创建节点实例失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 6. 测试卸载功能
    print("\n🧪 测试节点卸载...")
    pm.unload_plugin_nodes(plugin.name)
    
    remaining_nodes = [
        key for key in pm.loaded_nodes.keys()
        if key.startswith(f"{plugin.name}.")
    ]
    
    if not remaining_nodes:
        print("✅ 5. 节点卸载成功")
    else:
        print(f"❌ 5. 节点卸载失败，仍有 {len(remaining_nodes)} 个节点")
        return False
    
    print("\n" + "=" * 60)
    print("Step 2 测试通过！✅")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_step2()
    sys.exit(0 if success else 1)
