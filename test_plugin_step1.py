"""
Step 1 测试脚本 - 验证插件元数据结构与基础框架
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'python'))

from plugins.plugin_manager import PluginManager
import shutil
from pathlib import Path


def test_step1():
    """测试Step 1: 插件扫描和元数据加载"""
    print("=" * 60)
    print("测试 Step 1: 插件元数据结构与基础框架")
    print("=" * 60)
    
    # 1. 复制示例插件到user_plugins
    template_path = Path("src/python/plugin_templates/simple_node")
    target_path = Path("src/python/user_plugins/test_morphology")
    
    if target_path.exists():
        shutil.rmtree(target_path)
    shutil.copytree(template_path, target_path)
    
    print("\n✅ 1. 示例插件已复制到 user_plugins/")
    
    # 2. 扫描插件
    pm = PluginManager()
    plugins = pm.scan_plugins()
    
    print(f"\n✅ 2. 扫描到 {len(plugins)} 个插件")
    
    # 3. 验证元数据
    if not plugins:
        print("\n❌ 未扫描到插件")
        return False
    
    plugin = plugins[0]
    print(f"\n📦 插件信息:")
    print(f"   名称: {plugin.name}")
    print(f"   版本: {plugin.version}")
    print(f"   作者: {plugin.author}")
    print(f"   描述: {plugin.description}")
    print(f"   节点数: {len(plugin.nodes)}")
    
    for i, node in enumerate(plugin.nodes):
        print(f"   节点{i+1}: {node.display_name} (分类: {node.category})")
    
    print("\n✅ 3. 元数据加载成功")
    
    # 4. 验证插件注册表
    all_plugins = pm.get_installed_plugins()
    print(f"\n✅ 4. 插件注册表中有 {len(all_plugins)} 个插件")
    
    # 5. 测试获取单个插件
    test_plugin = pm.get_plugin("test_morphology")
    if test_plugin:
        print(f"\n✅ 5. 成功获取指定插件: {test_plugin.name}")
    else:
        print("\n❌ 5. 获取指定插件失败")
        return False
    
    print("\n" + "=" * 60)
    print("Step 1 测试通过！✅")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_step1()
    sys.exit(0 if success else 1)
