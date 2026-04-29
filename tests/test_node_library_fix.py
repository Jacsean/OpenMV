"""
测试节点库显示修复

运行应用并检查：
1. 左侧DockWidget标题是否为"节点库"
2. 节点库中是否显示所有插件节点
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'python'))

def test_node_library():
    print("=" * 60)
    print("测试节点库显示")
    print("=" * 60)
    
    # 检查main_window.py中的修改
    main_window_path = Path('src/python/ui/main_window.py')
    if not main_window_path.exists():
        print("❌ main_window.py不存在")
        return
    
    with open(main_window_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查1: DockWidget标题是否为"节点库"
    if 'QDockWidget("节点库"' in content:
        print("✅ DockWidget标题已修正为'节点库'")
    else:
        print("❌ DockWidget标题未修正")
    
    # 检查2: _register_nodes方法是否为空（已废弃）
    if 'def _register_nodes(self, node_graph):' in content and 'pass' in content:
        print("✅ _register_nodes方法已标记为废弃")
    else:
        print("⚠️ _register_nodes方法可能需要检查")
    
    # 检查3: temp_graph是否正确保存
    if 'self.temp_graph = temp_graph' in content:
        print("✅ temp_graph引用已保存")
    else:
        print("❌ temp_graph引用未保存")
    
    # 检查project_ui_manager.py
    project_ui_path = Path('src/python/core/project_ui_manager.py')
    if project_ui_path.exists():
        with open(project_ui_path, 'r', encoding='utf-8') as f:
            ui_content = f.read()
        
        # 检查4: load_plugins_to_graph是否被调用
        if 'plugin_ui.load_plugins_to_graph(node_graph)' in ui_content:
            print("✅ load_plugins_to_graph被正确调用")
        else:
            print("❌ load_plugins_to_graph未被调用")
    
    print("\n" + "=" * 60)
    print("请运行应用验证：")
    print("  python src/python/ui/main_window.py")
    print("=" * 60)

if __name__ == '__main__':
    test_node_library()