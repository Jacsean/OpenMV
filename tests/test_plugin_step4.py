"""
Step 4 测试脚本 - 验证安全沙箱机制
"""

import sys
import os
import shutil
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'python'))

from plugins.permission_checker import PermissionChecker
from plugins.plugin_manager import PluginManager


def test_step4():
    """测试Step 4: 安全沙箱机制"""
    print("=" * 60)
    print("测试 Step 4: 安全沙箱机制")
    print("=" * 60)
    
    # 测试1: 安全代码应通过检查
    print("\n🧪 测试1: 安全代码检查")
    safe_code = """
import cv2
import numpy as np
from NodeGraphQt import BaseNode

class SafeNode(BaseNode):
    def process(self, image):
        return cv2.blur(image, (3, 3))
"""
    
    violations = PermissionChecker.check_source_code(safe_code)
    if not violations:
        print("✅ 1. 安全代码通过检查")
    else:
        print(f"❌ 1. 安全代码误报: {violations}")
        return False
    
    # 测试2: 危险代码应被拦截
    print("\n🧪 测试2: 危险代码拦截")
    dangerous_code = """
import os
import subprocess

os.system('rm -rf /')
subprocess.call(['malicious'])
"""
    
    violations = PermissionChecker.check_source_code(dangerous_code)
    if violations:
        print(f"✅ 2. 危险代码被拦截:")
        for v in violations:
            print(f"   - {v}")
    else:
        print("❌ 2. 危险代码未被拦截")
        return False
    
    # 测试3: 导入禁止模块应被拦截
    print("\n🧪 测试3: 禁止模块导入拦截")
    forbidden_import = """
import socket
import requests
"""
    
    violations = PermissionChecker.check_source_code(forbidden_import)
    if violations:
        print(f"✅ 3. 禁止模块导入被拦截:")
        for v in violations:
            print(f"   - {v}")
    else:
        print("❌ 3. 禁止模块导入未被拦截")
        return False
    
    # 测试4: 实际插件加载测试 - 安全插件
    print("\n🧪 测试4: 安全插件加载")
    from PySide2 import QtWidgets
    from NodeGraphQt import NodeGraph
    
    app = QtWidgets.QApplication(sys.argv)
    graph = NodeGraph()
    
    pm = PluginManager()
    pm.scan_plugins()
    
    if 'test_morphology' in pm.plugins:
        success = pm.load_plugin_nodes('test_morphology', graph)
        if success:
            print("✅ 4. 安全插件加载成功")
        else:
            print("❌ 4. 安全插件加载失败（误拦截）")
            return False
    else:
        print("⚠️ 4. 跳过：test_morphology插件不存在")
    
    # 测试5: 实际插件加载测试 - 危险插件
    print("\n🧪 测试5: 危险插件拦截")
    template_path = Path("src/python/plugin_templates/dangerous_node")
    target_path = Path("src/python/user_plugins/test_dangerous")
    
    if template_path.exists():
        if target_path.exists():
            shutil.rmtree(target_path)
        shutil.copytree(template_path, target_path)
        
        # 重新扫描
        pm2 = PluginManager()
        pm2.scan_plugins()
        
        graph2 = NodeGraph()
        
        if 'test_dangerous' in pm2.plugins:
            success = pm2.load_plugin_nodes('test_dangerous', graph2)
            if not success:
                print("✅ 5. 危险插件被成功拦截")
            else:
                print("❌ 5. 危险插件未被拦截")
                return False
        else:
            print("⚠️ 5. 跳过：test_dangerous插件未扫描到")
    else:
        print("⚠️ 5. 跳过：危险插件模板不存在")
    
    print("\n" + "=" * 60)
    print("Step 4 测试通过！✅")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_step4()
    sys.exit(0 if success else 1)
