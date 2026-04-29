#!/usr/bin/env python3
"""简单调试测试"""
import sys
sys.path.insert(0, 'src/python')

from utils.logger import Logger, LogLevel

print("创建DEBUG模式的Logger...")
l = Logger(LogLevel.DEBUG, [])
print(f"Level: {l.level}")
print(f"Debug modules: {l.debug_modules}")
print(f"Should log DEBUG (module=test): {l._should_log('DEBUG', 'test')}")
print(f"Should log DEBUG (module=None): {l._should_log('DEBUG', None)}")
print("\n输出DEBUG日志:")
l.debug('Test debug message', module='test')
print("\n完成！")
