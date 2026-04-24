#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
节点库显示诊断脚本

验证插件节点是否正确加载到节点库中
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from PySide2 import QtWidgets, QtCore
from NodeGraphQt import NodeGraph, NodesPaletteWidget

# 导入插件管理器
from plugins.plugin_manager import PluginManager


def diagnose_node_palette():
    """诊断节点库显示问题"""
    
    print("=" * 60)
    print("节点库显示诊断工具")
    print("=" * 60)
    
    # 创建Qt应用
    app = QtWidgets.QApplication(sys.argv)
    
    # 1. 扫描插件
    print("\n[1/5] 扫描插件...")
    plugin_manager = PluginManager()
    plugins = plugin_manager.scan_plugins()
    print(f"✅ 发现 {len(plugins)} 个插件:")
    for p in plugins:
        print(f"   - {p.name} (v{p.version}): {len(p.nodes)} 个节点")
    
    if not plugins:
        print("\n❌ 未找到任何插件，请检查 user_plugins 目录")
        return
    
    # 2. 创建临时NodeGraph（模拟节点库绑定的Graph）
    print("\n[2/5] 创建临时NodeGraph...")
    temp_graph = NodeGraph()
    print("✅ NodeGraph 创建成功")
    
    # 3. 加载插件节点到临时Graph
    print("\n[3/5] 加载插件节点到NodeGraph...")
    loaded_count = 0
    for plugin_info in plugins:
        if plugin_info.enabled:
            success = plugin_manager.load_plugin_nodes(plugin_info.name, temp_graph)
            if success:
                loaded_count += len(plugin_info.nodes)
                print(f"   ✅ {plugin_info.name}: {len(plugin_info.nodes)} 个节点")
            else:
                print(f"   ❌ {plugin_info.name}: 加载失败")
    
    print(f"\n✅ 共加载 {loaded_count} 个节点")
    
    # 4. 创建NodesPaletteWidget
    print("\n[4/5] 创建NodesPaletteWidget...")
    palette = NodesPaletteWidget(node_graph=temp_graph)
    palette.setWindowTitle("节点库诊断")
    palette.resize(400, 600)
    
    # 获取标签页信息
    try:
        tab_widget = palette.tab_widget()
        tab_count = tab_widget.count()
        print(f"✅ NodesPaletteWidget 创建成功")
        print(f"   标签页数量: {tab_count}")
        
        print("\n   标签页列表:")
        for i in range(tab_count):
            tab_name = tab_widget.tabText(i)
            print(f"     [{i}] {tab_name}")
            
    except Exception as e:
        print(f"⚠️ 无法获取标签页信息: {e}")
    
    # 5. 显示窗口
    print("\n[5/5] 显示节点库窗口...")
    print("\n💡 请检查窗口中是否显示了所有插件包的节点")
    print("   - 每个插件包应该对应一个标签页")
    print("   - 标签页名称应该是插件的 __identifier__ 值")
    print("   - 点击标签页可以看到该包下的所有节点\n")
    
    palette.show()
    
    # 运行应用
    sys.exit(app.exec_())


if __name__ == '__main__':
    try:
        diagnose_node_palette()
    except Exception as e:
        print(f"\n❌ 诊断过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
