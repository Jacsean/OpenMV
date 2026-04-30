#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试日志系统双模式功能
"""

import subprocess
import sys

print("=" * 60)
print("日志系统双模式测试")
print("=" * 60)

# 测试1: NORMAL模式（默认）
print("\n【测试1】NORMAL模式 - 应该几乎没有输出")
print("-" * 60)
result = subprocess.run(
    [sys.executable, 'src/python/main.py'],
    capture_output=True,
    text=True,
    timeout=5
)
print(f"STDOUT长度: {len(result.stdout)} 字符")
print(f"STDERR长度: {len(result.stderr)} 字符")
if result.returncode == 0:
    print("✅ 程序正常启动（无错误）")
else:
    print(f"❌ 程序启动失败: {result.stderr[:200]}")

# 测试2: DEBUG模式 - 所有模块
print("\n【测试2】DEBUG模式（所有模块）- 应该有大量输出")
print("-" * 60)
env = {'LOG_LEVEL': 'DEBUG'}
result = subprocess.run(
    [sys.executable, 'src/python/main.py'],
    capture_output=True,
    text=True,
    env={**subprocess.os.environ, **env},
    timeout=5
)
print(f"STDOUT长度: {len(result.stdout)} 字符")
lines = result.stdout.split('\n')
debug_lines = [l for l in lines if '[DEBUG]' in l]
print(f"DEBUG日志行数: {len(debug_lines)}")
if debug_lines:
    print("前3条DEBUG日志:")
    for line in debug_lines[:3]:
        print(f"  {line}")
    print("✅ DEBUG日志正常输出")
else:
    print("⚠️ 未检测到DEBUG日志")

# 测试3: DEBUG模式 - 指定模块
print("\n【测试3】DEBUG模式（仅plugin_manager模块）")
print("-" * 60)
env = {'LOG_LEVEL': 'DEBUG', 'DEBUG_MODULES': 'plugin_manager'}
result = subprocess.run(
    [sys.executable, 'src/python/main.py'],
    capture_output=True,
    text=True,
    env={**subprocess.os.environ, **env},
    timeout=5
)
lines = result.stdout.split('\n')
debug_lines = [l for l in lines if '[DEBUG]' in l]
print(f"DEBUG日志行数: {len(debug_lines)}")
if debug_lines:
    plugin_manager_lines = [l for l in debug_lines if '[plugin_manager]' in l]
    other_lines = [l for l in debug_lines if '[plugin_manager]' not in l]
    print(f"  plugin_manager模块: {len(plugin_manager_lines)} 条")
    print(f"  其他模块: {len(other_lines)} 条")
    if len(plugin_manager_lines) > 0 and len(other_lines) == 0:
        print("✅ 模块过滤正常工作")
    else:
        print("⚠️ 模块过滤可能有问题")
else:
    print("⚠️ 未检测到DEBUG日志")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
