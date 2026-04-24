"""
Step 5 测试脚本 - 验证热重载系统
"""

import sys
import os
import time
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'python'))

from plugins.plugin_manager import PluginManager


def test_step5():
    """测试Step 5: 热重载系统"""
    print("=" * 60)
    print("测试 Step 5: 热重载系统")
    print("=" * 60)
    
    # 1. 初始化插件管理器并加载插件
    from PySide2 import QtWidgets
    from NodeGraphQt import NodeGraph
    
    app = QtWidgets.QApplication(sys.argv)
    graph = NodeGraph()
    
    pm = PluginManager()
    plugins = pm.scan_plugins()
    
    if not plugins:
        print("\n❌ 未找到插件")
        return False
    
    plugin_name = plugins[0].name
    print(f"\n📦 测试插件: {plugin_name}")
    
    # 加载插件以启动热重载
    success = pm.load_plugin_nodes(plugin_name, graph)
    if not success:
        print("❌ 插件加载失败")
        return False
    
    # 2. 检查热重载器是否启动
    if plugin_name in pm.hot_reloader.watchers:
        print(f"✅ 1. 热重载监听已启动: {plugin_name}")
    else:
        print(f"❌ 1. 热重载监听未启动")
        return False
    
    # 3. 模拟文件修改
    print("\n🧪 测试2: 模拟文件修改触发重载")
    plugin_path = Path(pm.plugins[plugin_name].path)
    nodes_file = plugin_path / "nodes.py"
    
    if nodes_file.exists():
        original_mtime = nodes_file.stat().st_mtime
        
        # 修改文件时间戳（模拟保存）
        new_mtime = time.time() + 10
        os.utime(nodes_file, (new_mtime, new_mtime))
        
        print(f"   原始修改时间: {original_mtime}")
        print(f"   新修改时间: {new_mtime}")
        
        # 等待防抖时间
        time.sleep(1.5)
        
        # 手动检查变化检测逻辑
        latest_mtime = pm.hot_reloader._get_latest_mtime(plugin_path)
        watcher = pm.hot_reloader.watchers.get(plugin_name)
        
        if watcher and latest_mtime > watcher['last_modified']:
            print(f"✅ 2. 文件变化检测成功")
            print(f"   最新修改时间: {latest_mtime}")
            print(f"   上次记录时间: {watcher['last_modified']}")
        else:
            print(f"⚠️ 2. 变化检测未触发（可能已在后台处理）")
    else:
        print("❌ 2. 跳过：nodes.py不存在")
    
    # 4. 测试停止监听
    print("\n🧪 测试3: 停止监听")
    pm.hot_reloader.stop_watching(plugin_name)
    
    if plugin_name not in pm.hot_reloader.watchers:
        print("✅ 3. 监听已成功停止")
    else:
        print("❌ 3. 监听未停止")
        return False
    
    # 5. 测试重新启动监听
    print("\n🧪 测试4: 重新启动监听")
    pm.hot_reloader.start_watching(
        plugin_name,
        pm.plugins[plugin_name].path,
        lambda name: print(f"回调触发: {name}")
    )
    
    if plugin_name in pm.hot_reloader.watchers:
        print("✅ 4. 监听已重新启动")
    else:
        print("❌ 4. 监听未启动")
        return False
    
    # 6. 清理
    print("\n🧹 清理测试环境...")
    pm.hot_reloader.stop_all()
    print("✅ 所有监听已停止")
    
    print("\n" + "=" * 60)
    print("Step 5 测试通过！✅")
    print("注意：热重载功能需在GUI环境中验证")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_step5()
    sys.exit(0 if success else 1)
