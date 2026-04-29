#!/usr/bin/env python3
"""详细调试"""
import sys
sys.path.insert(0, 'src/python')

from utils.logger import Logger, LogLevel

print("测试1: 空列表")
l1 = Logger(LogLevel.DEBUG, [])
print(f"  debug_modules: {l1.debug_modules}")
print(f"  bool(debug_modules): {bool(l1.debug_modules)}")
print(f"  not debug_modules: {not l1.debug_modules}")
print(f"  _should_log('DEBUG', 'test'): {l1._should_log('DEBUG', 'test')}")
l1.debug('Message from l1', module='test')

print("\n测试2: 包含module1的列表")
l2 = Logger(LogLevel.DEBUG, ['module1'])
print(f"  debug_modules: {l2.debug_modules}")
print(f"  _should_log('DEBUG', 'module1'): {l2._should_log('DEBUG', 'module1')}")
print(f"  _should_log('DEBUG', 'module2'): {l2._should_log('DEBUG', 'module2')}")
l2.debug('✅ module1 message', module='module1')
l2.debug('❌ module2 message', module='module2')
