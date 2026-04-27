"""
深度诊断节点库为空的问题

检查点：
1. 插件是否正确扫描并保存到_pending_plugins
2. temp_graph是否正确创建
3. nodes_palette是否正确绑定到temp_graph
4. load_plugins_to_graph是否被调用
5. 节点是否成功注册到Graph
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'python'))

def diagnose_node_library_empty():
    print("=" * 80)
    print("深度诊断：节点库为空问题")
    print("=" * 80)
    
    # ==================== 检查1: 插件扫描 ====================
    print("\n【检查1】插件扫描状态")
    print("-" * 80)
    
    from plugins.plugin_manager import PluginManager
    pm = PluginManager()
    plugins = pm.scan_plugins()
    
    print(f"✅ 扫描到 {len(plugins)} 个插件")
    for p in plugins:
        print(f"   • {p.name:30s} ({p.source:12s}) - {len(p.nodes):2d} 个节点")
    
    if not plugins:
        print("❌ 严重问题：没有扫描到任何插件！")
        return
    
    # ==================== 检查2: main_window.py关键代码 ====================
    print("\n【检查2】main_window.py关键逻辑")
    print("-" * 80)
    
    main_window_path = Path('src/python/ui/main_window.py')
    with open(main_window_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = [
        ('_pending_plugins保存', '_pending_plugins = plugins' in content),
        ('temp_graph保存', 'self.temp_graph = temp_graph' in content),
        ('nodes_palette创建', 'NodesPaletteWidget(node_graph=temp_graph)' in content),
        ('load_plugins_to_graph调用', 'load_plugins_to_graph' in content),
    ]
    
    for check_name, result in checks:
        status = "✅" if result else "❌"
        print(f"{status} {check_name}")
    
    # ==================== 检查3: project_ui_manager.py加载逻辑 ====================
    print("\n【检查3】project_ui_manager.py插件加载逻辑")
    print("-" * 80)
    
    project_ui_path = Path('src/python/core/project_ui_manager.py')
    with open(project_ui_path, 'r', encoding='utf-8') as f:
        ui_content = f.read()
    
    # 检查add_workflow_tab中的加载逻辑
    has_pending_check = "hasattr(self.main_window, '_pending_plugins')" in ui_content
    has_load_call = "plugin_ui.load_plugins_to_graph(node_graph)" in ui_content
    has_temp_graph_load = "temp_graph" in ui_content and "load_plugins_to_graph" in ui_content
    
    print(f"{'✅' if has_pending_check else '❌'} 检查_pending_plugins存在")
    print(f"{'✅' if has_load_call else '❌'} 调用load_plugins_to_graph")
    print(f"{'✅' if has_temp_graph_load else '⚠️'} 同时加载到temp_graph（节点库）")
    
    if not has_temp_graph_load:
        print("\n⚠️ 警告：可能只加载到了工作流Graph，未加载到节点库Graph！")
    
    # ==================== 检查4: plugin_ui_manager.py加载实现 ====================
    print("\n【检查4】plugin_ui_manager.py加载实现")
    print("-" * 80)
    
    plugin_ui_path = Path('src/python/plugins/plugin_ui_manager.py')
    with open(plugin_ui_path, 'r', encoding='utf-8') as f:
        plugin_ui_content = f.read()
    
    # 检查双Graph加载逻辑
    loads_to_palette = "palette_graph" in plugin_ui_content or "nodes_palette" in plugin_ui_content
    loads_to_workflow = "node_graph" in plugin_ui_content
    clears_pending = "delattr(self.main_window, '_pending_plugins')" in plugin_ui_content
    
    print(f"{'✅' if loads_to_palette else '❌'} 加载到节点库Graph (palette_graph)")
    print(f"{'✅' if loads_to_workflow else '❌'} 加载到工作流Graph (node_graph)")
    print(f"{'✅' if clears_pending else '❌'} 清除_pending_plugins标记")
    
    # ==================== 检查5: NodeGraphQt兼容性 ====================
    print("\n【检查5】NodeGraphQt版本和API")
    print("-" * 80)
    
    try:
        import NodeGraphQt
        print(f"✅ NodeGraphQt版本: {NodeGraphQt.__version__ if hasattr(NodeGraphQt, '__version__') else '未知'}")
        
        # 检查NodesPaletteWidget的API
        from NodeGraphQt import NodesPaletteWidget, NodeGraph
        
        test_graph = NodeGraph()
        palette = NodesPaletteWidget(node_graph=test_graph)
        
        print(f"✅ NodesPaletteWidget创建成功")
        print(f"✅ node_graph属性: {hasattr(palette, 'node_graph')}")
        print(f"✅ tab_widget方法: {hasattr(palette, 'tab_widget')}")
        
        # 检查是否有已注册的节点类型
        registered_nodes = test_graph.registered_nodes()
        print(f"📊 当前Graph中已注册的节点类型数: {len(registered_nodes)}")
        
        if len(registered_nodes) == 0:
            print("⚠️ Graph中没有任何注册的节点类型！")
            print("   这说明插件节点尚未注册到Graph")
        
    except Exception as e:
        print(f"❌ NodeGraphQt检查失败: {e}")
        import traceback
        traceback.print_exc()
    
    # ==================== 总结和建议 ====================
    print("\n" + "=" * 80)
    print("诊断总结与建议")
    print("=" * 80)
    
    issues = []
    
    if not has_temp_graph_load:
        issues.append("1. 【高优先级】project_ui_manager.py可能未将节点加载到temp_graph")
    
    if not loads_to_palette:
        issues.append("2. 【高优先级】plugin_ui_manager.py可能未正确加载到节点库Graph")
    
    if not clears_pending:
        issues.append("3. 【中优先级】_pending_plugins可能未被清除，导致重复加载问题")
    
    if issues:
        print("\n发现的问题：")
        for issue in issues:
            print(f"   {issue}")
        print("\n建议操作：")
        print("   1. 检查project_ui_manager.py中add_workflow_tab的实现")
        print("   2. 确认plugin_ui_manager.py中load_plugins_to_graph的双Graph加载逻辑")
        print("   3. 重启应用后观察控制台日志输出")
    else:
        print("\n✅ 代码逻辑看起来正确")
        print("\n可能的原因：")
        print("   1. 应用未完全重启（需要关闭所有进程后重新启动）")
        print("   2. 节点注册成功但UI刷新延迟")
        print("   3. NodesPaletteWidget的tab_widget未正确更新")
        print("\n建议操作：")
        print("   1. 完全关闭应用后重新启动")
        print("   2. 启动时观察控制台是否有节点注册日志")
        print("   3. 检查左侧节点库是否有标签页（即使内容为空）")

if __name__ == '__main__':
    diagnose_node_library_empty()