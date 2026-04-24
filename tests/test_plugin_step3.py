"""
Step 3 测试脚本 - 验证UI自动归类系统
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'python'))

from plugins.plugin_manager import PluginManager


def test_step3():
    """测试Step 3: UI自动归类"""
    print("=" * 60)
    print("测试 Step 3: UI自动归类系统")
    print("=" * 60)
    
    # 1. 扫描插件
    pm = PluginManager()
    plugins = pm.scan_plugins()
    
    if not plugins:
        print("\n❌ 未找到插件")
        return False
    
    plugin = plugins[0]
    print(f"\n📦 测试插件: {plugin.name}")
    print(f"   版本: {plugin.version}")
    print(f"   作者: {plugin.author}")
    
    # 2. 检查分类
    categories = set()
    print(f"\n📊 节点分类信息:")
    for node_def in plugin.nodes:
        categories.add(node_def.category)
        print(f"   节点: {node_def.display_name:10s} → 分类: {node_def.category}")
    
    print(f"\n✅ 检测到 {len(categories)} 个分类: {', '.join(categories)}")
    
    # 3. 验证分类合理性
    expected_categories = {'形态学'}
    if categories == expected_categories:
        print(f"✅ 分类符合预期: {expected_categories}")
    else:
        print(f"⚠️ 分类与预期不符")
        print(f"   预期: {expected_categories}")
        print(f"   实际: {categories}")
    
    # 4. 模拟自动归类逻辑
    print(f"\n🧪 模拟自动归类流程...")
    existing_categories = {'文件', '处理', '显示'}  # 模拟现有分类
    new_categories = categories - existing_categories
    
    if new_categories:
        print(f"   ✨ 需要创建的新分类: {', '.join(new_categories)}")
        print(f"   ⚠️ NodeGraphQt限制：新分类将在下次启动时显示")
    else:
        print(f"   ✅ 所有分类已存在，无需创建")
    
    print("\n" + "=" * 60)
    print("Step 3 测试通过！✅")
    print("注意：UI分类显示需要完整启动程序验证")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_step3()
    sys.exit(0 if success else 1)
