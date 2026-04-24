#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单测试：验证插件扫描和加载
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "python"))

print("=" * 60)
print("插件系统测试")
print("=" * 60)

# 测试1：扫描插件
print("\n[测试1] 扫描插件...")
from plugins.plugin_manager import PluginManager
pm = PluginManager()
plugins = pm.scan_plugins()
print(f"发现 {len(plugins)} 个插件")

if plugins:
    for p in plugins:
        print(f"  - {p.name}: {len(p.nodes)} 节点, enabled={p.enabled}")
else:
    print("❌ 未找到任何插件！")
    print(f"   检查目录: {pm.plugins_dir}")
    print(f"   目录存在: {pm.plugins_dir.exists()}")
    
    if pm.plugins_dir.exists():
        print(f"   目录内容: {list(pm.plugins_dir.iterdir())}")

print("\n✅ 测试完成")
