#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
节点库加载诊断脚本 - 验证插件是否正确加载到节点库
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "python"))

from PySide2 import QtWidgets
from NodeGraphQt import NodeGraph, NodesPaletteWidget
from plugins.plugin_manager import PluginManager
from plugins.plugin_ui_manager import PluginUIManager


class MockMainWindow:
    """模拟MainWindow用于测试"""
    def __init__(self):
        self.plugin_manager = PluginManager()
        self.nodes_palette = None
        self._pending_plugins = None


def test_plugin_loading():
    """测试插件加载流程"""
    
    print("=" * 60)
    print("节点库加载诊断测试")
    print("=" * 60)
    
    # 创建Qt应用
    app = QtWidgets.QApplication(sys.argv)
    
    # 1. 扫描插件
    print("\n[步骤1] 扫描插件...")
    mock_window = MockMainWindow()
    plugins = mock_window.plugin_manager.scan_plugins()
    print(f"✅ 发现 {len(plugins)} 个插件")
    
    if not plugins:
        print("\n❌ 错误：未找到任何插件！")
        print("   请检查 user_plugins 目录是否存在")
        return False
    
    for p in plugins:
        print(f"   - {p.name}: {len(p.nodes)} 个节点")
    
    # 设置待加载插件
    mock_window._pending_plugins = plugins
    
    # 2. 创建临时NodeGraph和NodesPaletteWidget
    print("\n[步骤2] 创建UI组件...")
    temp_graph = NodeGraph()
    palette = NodesPaletteWidget(node_graph=temp_graph)
    mock_window.nodes_palette = palette
    print("✅ NodesPaletteWidget 创建成功")
    
    # 3. 加载插件到节点库Graph
    print("\n[步骤3] 加载插件到节点库Graph...")
    plugin_ui = PluginUIManager(mock_window.plugin_manager, mock_window)
    
    try:
        new_categories = plugin_ui.load_plugins_to_graph(temp_graph)
        print(f"✅ 加载完成，新增 {len(new_categories)} 个分类")
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 检查节点库中的标签页
    print("\n[步骤4] 检查节点库显示...")
    try:
        tab_widget = palette.tab_widget()
        tab_count = tab_widget.count()
        print(f"✅ 节点库中有 {tab_count} 个标签页")
        
        if tab_count == 0:
            print("\n❌ 错误：节点库中没有显示任何标签页！")
            print("   可能原因：")
            print("   1. 节点的 __identifier__ 未正确设置")
            print("   2. 节点注册失败")
            print("   3. NodesPaletteWidget 未正确绑定到Graph")
            return False
        
        print("\n   标签页列表：")
        for i in range(tab_count):
            tab_name = tab_widget.tabText(i)
            print(f"     [{i}] {tab_name}")
            
    except Exception as e:
        print(f"❌ 检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 显示窗口（人工验证）
    print("\n[步骤5] 显示节点库窗口...")
    print("💡 请检查窗口中是否显示了所有插件包的节点\n")
    
    palette.setWindowTitle("节点库诊断 - 验证测试")
    palette.resize(400, 600)
    palette.show()
    
    # 运行应用
    app.exec_()
    
    return True


if __name__ == '__main__':
    try:
        success = test_plugin_loading()
        if success:
            print("\n✅ 诊断测试完成")
        else:
            print("\n❌ 诊断测试失败")
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 诊断过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
