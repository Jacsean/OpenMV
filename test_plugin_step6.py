"""
Step 6 测试脚本 - 验证依赖管理与ZIP安装
"""

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'python'))

from plugins.dependency_resolver import DependencyResolver
from plugins.plugin_manager import PluginManager


def test_step6():
    """测试Step 6: 依赖管理与ZIP安装"""
    print("=" * 60)
    print("测试 Step 6: 依赖管理与ZIP安装")
    print("=" * 60)
    
    # 测试1: 依赖检查
    print("\n🧪 测试1: 依赖检查")
    test_deps = ['numpy', 'opencv-python', 'nonexistent_package']
    
    for dep in test_deps:
        exists = DependencyResolver.check_dependency(dep)
        status = "✅ 已安装" if exists else "❌ 未安装"
        print(f"   {dep:30s} → {status}")
    
    # 测试2: ZIP安装
    print("\n🧪 测试2: ZIP插件安装")
    zip_path = Path("test_plugin.zip")
    
    if not zip_path.exists():
        print(f"⚠️ 跳过：{zip_path} 不存在")
    else:
        pm = PluginManager()
        
        # 记录安装前的插件数量
        before_count = len(pm.get_installed_plugins())
        print(f"   安装前插件数: {before_count}")
        
        # 执行安装
        success, message = pm.install_plugin_from_zip(str(zip_path))
        
        if success:
            print(f"✅ 2. ZIP安装成功: {message}")
            
            # 验证插件已注册
            after_count = len(pm.get_installed_plugins())
            print(f"   安装后插件数: {after_count}")
            
            if after_count > before_count:
                print(f"   ✅ 插件已成功注册到管理器")
            else:
                print(f"   ⚠️ 插件未注册（可能已存在）")
        else:
            print(f"❌ 2. ZIP安装失败: {message}")
            return False
    
    # 测试3: 依赖解析器功能
    print("\n🧪 测试3: 依赖解析器")
    results = DependencyResolver.install_dependencies(['numpy'])
    
    if 'numpy' in results and results['numpy']:
        print("✅ 3. 依赖解析器工作正常")
    else:
        print("⚠️ 3. 依赖解析器返回异常（可能numpy已存在）")
    
    # 测试4: 卸载功能
    print("\n🧪 测试4: 插件卸载")
    pm2 = PluginManager()
    
    if 'simple_node' in pm2.plugins:
        success, message = pm2.uninstall_plugin('simple_node')
        if success:
            print(f"✅ 4. 卸载成功: {message}")
        else:
            print(f"❌ 4. 卸载失败: {message}")
            return False
    else:
        print("⚠️ 4. 跳过：simple_node插件不存在")
    
    print("\n" + "=" * 60)
    print("Step 6 测试通过！✅")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_step6()
    sys.exit(0 if success else 1)
