"""
测试插件管理器是否正确记录了已扫描的插件
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src" / "python"))

from plugins.plugin_manager import PluginManager

print("=" * 60)
print("🧪 测试PluginManager状态")
print("=" * 60)

pm = PluginManager()

print(f"\n📁 插件目录: {pm.plugins_dir}")
print(f"   存在: {pm.plugins_dir.exists()}")

# 扫描插件
print("\n🔍 执行scan_plugins()...")
plugins = pm.scan_plugins()
print(f"   返回值数量: {len(plugins)}")
print(f"   插件名称: {[p.name for p in plugins]}")

# 检查内部状态
print(f"\n📊 PluginManager内部状态:")
print(f"   self.plugins字典大小: {len(pm.plugins)}")
print(f"   self.plugins键列表: {list(pm.plugins.keys())}")

# 测试get_installed_plugins
print(f"\n📋 调用get_installed_plugins():")
installed = pm.get_installed_plugins()
print(f"   返回数量: {len(installed)}")
print(f"   插件名称: {[p.name for p in installed]}")

print("\n" + "=" * 60)
if len(installed) > 0:
    print("✅ 插件管理器正常工作")
else:
    print("❌ 插件管理器未记录任何插件！")
print("=" * 60)
