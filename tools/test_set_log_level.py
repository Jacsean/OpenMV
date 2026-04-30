#!/usr/bin/env python3
"""测试set_log_level"""
import sys
sys.path.insert(0, 'src/python')

import utils
from utils import set_log_level

print("初始状态:")
print(f"  logger id: {id(utils.logger)}")
print(f"  logger level: {utils.logger.level}")

print("\n切换到DEBUG模式（空列表）:")
set_log_level('DEBUG', [])
print(f"  logger id: {id(utils.logger)}")
print(f"  logger level: {utils.logger.level}")
print(f"  debug_modules: {utils.logger.debug_modules}")

print("\n输出DEBUG日志:")
utils.logger.debug('Test message', module='test')
