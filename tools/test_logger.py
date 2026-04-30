#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
日志系统双模式快速测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'python'))

import utils
from utils import set_log_level

print("\n" + "="*60)
print("日志系统双模式测试")
print("="*60)

# 测试1: NORMAL模式
print("\n【测试1】NORMAL模式（仅显示关键信息）")
print("-"*60)
set_log_level('NORMAL')
utils.logger.info("应用启动", module="main")
utils.logger.success("插件加载完成", module="plugin_loader")
utils.logger.warning("警告信息", module="test")
utils.logger.error("错误信息", module="test")
utils.logger.debug("这条不会显示", module="test")

# 测试2: DEBUG模式 - 所有模块
print("\n【测试2】DEBUG模式 - 调试所有模块")
print("-"*60)
set_log_level('DEBUG', [])
utils.logger.warning("警告始终显示", module="test")
utils.logger.error("错误始终显示", module="test")
utils.logger.debug("✅ 调试信息1", module="module1")
utils.logger.debug("✅ 调试信息2", module="module2")
utils.logger.debug("✅ 无module也显示")

# 测试3: DEBUG模式 - 过滤模块
print("\n【测试3】DEBUG模式 - 仅调试module1")
print("-"*60)
set_log_level('DEBUG', ['module1'])
utils.logger.warning("警告始终显示", module="any")
utils.logger.debug("✅ module1的调试", module="module1")
utils.logger.debug("❌ module2的调试（被过滤）", module="module2")
utils.logger.debug("❌ 无module（被过滤）")

print("\n" + "="*60)
print("✅ 测试完成！")
print("="*60 + "\n")
