#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
诊断 category_group 属性在各个环节的变化
追踪从 plugin.json 到 UI 标签页的完整数据流
"""

import sys
import json
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "python"))

print("=" * 80)
print("category_group 属性全流程诊断")
print("=" * 80)

# ==================== 步骤1：检查 plugin.json 原始数据 ====================
print("\n【步骤1】检查 plugin.json 原始配置")
print("-" * 80)

plugins_dir = Path(__file__).parent.parent / "src" / "python" / "user_plugins"

if not plugins_dir.exists():
    print(f"❌ 插件目录不存在: {plugins_dir}")
    sys.exit(1)

print(f"✅ 插件目录存在: {plugins_dir}\n")

plugin_configs = {}
for plugin_dir in sorted(plugins_dir.iterdir()):
    if not plugin_dir.is_dir():
        continue
    
    metadata_file = plugin_dir / "plugin.json"
    if not metadata_file.exists():
        print(f"⚠️  {plugin_dir.name}: 缺少 plugin.json")
        continue
    
    try:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        name = data.get('name', '')
        category_group = data.get('category_group', '未设置')
        
        plugin_configs[name] = {
            'name': name,
            'category_group': category_group,
            'has_field': 'category_group' in data
        }
        
        status = "✅" if category_group != name else "⚠️"
        print(f"{status} {plugin_dir.name:30} | name='{name}' | category_group='{category_group}'")
        
    except Exception as e:
        print(f"❌ {plugin_dir.name}: 读取失败 - {e}")

if not plugin_configs:
    print("\n❌ 错误：未找到任何有效的插件配置")
    sys.exit(1)

# ==================== 步骤2：检查 PluginInfo 模型加载 ====================
print("\n【步骤2】检查 PluginInfo 模型加载")
print("-" * 80)

try:
    from plugins.plugin_manager import PluginManager
    
    pm = PluginManager()
    plugins = pm.scan_plugins()
    
    print(f"✅ PluginManager 扫描完成，发现 {len(plugins)} 个插件\n")
    
    plugin_info_map = {}
    for p in plugins:
        plugin_info_map[p.name] = {
            'name': p.name,
            'category_group': p.category_group,
            'enabled': p.enabled,
            'nodes_count': len(p.nodes)
        }
        
        # 对比原始配置和加载后的值
        original = plugin_configs.get(p.name, {})
        orig_cg = original.get('category_group', 'N/A')
        
        match = "✅" if p.category_group == orig_cg else "❌"
        print(f"{match} {p.name:30} | category_group='{p.category_group}' (原始: '{orig_cg}') | 节点数: {len(p.nodes)}")
        
except Exception as e:
    print(f"❌ PluginManager 加载失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# ==================== 步骤3：检查映射表构建 ====================
print("\n【步骤3】检查 identifier_to_display_name 映射表构建")
print("-" * 80)

identifier_to_display_name = {}
for p in plugins:
    if p.enabled:
        if hasattr(p, 'category_group') and p.category_group:
            identifier_to_display_name[p.name] = p.category_group

print(f"✅ 映射表构建完成，共 {len(identifier_to_display_name)} 项:\n")
for identifier, display_name in sorted(identifier_to_display_name.items()):
    print(f"   '{identifier}' → '{display_name}'")

# ==================== 步骤4：模拟 NodesPaletteWidget 行为 ====================
print("\n【步骤4】模拟 NodeGraphQt 节点注册机制")
print("-" * 80)

print("💡 说明：")
print("   NodeGraphQt 的 NodesPaletteWidget 会根据节点的 __identifier__ 自动分组")
print("   标签页名称 = 节点的 __identifier__ 属性值")
print("   我们的代码会在节点注册后，通过 setTabText() 修改标签页名称\n")

# 检查一个示例节点的 __identifier__
if plugins:
    sample_plugin = plugins[0]
    print(f"示例插件: {sample_plugin.name}")
    if sample_plugin.nodes:
        sample_node = sample_plugin.nodes[0]
        print(f"  节点类名: {sample_node.class_name}")
        print(f"  预期 __identifier__: '{sample_plugin.name}'")
        print(f"  预期标签页名称: '{sample_plugin.category_group}' (重命名后)")

# ==================== 步骤5：生成诊断报告 ====================
print("\n" + "=" * 80)
print("诊断总结")
print("=" * 80)

issues = []

# 检查1：所有插件都有 category_group
for name, config in plugin_configs.items():
    if not config['has_field']:
        issues.append(f"⚠️  {name}: plugin.json 中缺少 category_group 字段")
    elif config['category_group'] == config['name']:
        issues.append(f"ℹ️  {name}: category_group 与 name 相同，将显示为 '{config['name']}'")

# 检查2：PluginInfo 加载是否正确
for name, info in plugin_info_map.items():
    orig = plugin_configs.get(name, {})
    if info['category_group'] != orig.get('category_group', ''):
        issues.append(f"❌ {name}: PluginInfo.category_group 值不匹配")

# 检查3：映射表是否为空
if not identifier_to_display_name:
    issues.append("❌ 映射表为空，无法进行标签页重命名")

if issues:
    print("\n发现的问题:")
    for issue in issues:
        print(f"  {issue}")
else:
    print("\n✅ 所有检查通过，数据流正常")

print("\n下一步操作建议:")
print("  1. 运行主程序: python src/python/main.py")
print("  2. 观察控制台输出中是否有以下日志:")
print("     - '🏷️  开始应用标签页名称映射...'")
print("     - '✅ 重命名: xxx → yyy'")
print("  3. 如果没有看到重命名日志，说明 _apply_custom_tab_names 未被调用")
print("  4. 如果看到日志但UI未变化，可能是 tab_widget() 返回的对象不正确")

print("\n💡 调试技巧:")
print("  在 main_window.py 的 _setup_ui() 中添加:")
print("    print(f'nodes_palette 类型: {type(self.nodes_palette)}')")
print("    print(f'是否有 tab_widget 方法: {hasattr(self.nodes_palette, \"tab_widget\")}')")
print("  在 plugin_ui_manager.py 的 _apply_custom_tab_names() 中添加:")
print("    print(f'tab_widget 对象: {tab_widget}')")
print("    print(f'标签页数量: {tab_widget.count()}')")
print("    for i in range(tab_widget.count()):")
print("        print(f'  [{i}] {tab_widget.tabText(i)}')")
