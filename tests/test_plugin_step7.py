"""
Step 7 测试脚本 - 验证插件管理UI集成
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'python'))

from plugins.plugin_manager import PluginManager


def test_step7():
    """测试Step 7: 插件管理UI与完整集成"""
    print("=" * 60)
    print("测试 Step 7: 插件管理UI与完整集成")
    print("=" * 60)
    
    # 1. 验证PluginManager集成
    print("\n🧪 测试1: PluginManager功能完整性")
    pm = PluginManager()
    
    required_attrs = [
        'install_plugin_from_zip',
        'uninstall_plugin',
        'get_installed_plugins',
        'hot_reloader',
        'installer'
    ]
    
    missing = []
    for attr in required_attrs:
        if not hasattr(pm, attr):
            missing.append(attr)
    
    if not missing:
        print("✅ 1. PluginManager包含所有必需方法")
    else:
        print(f"❌ 1. 缺少方法: {missing}")
        return False
    
    # 2. 扫描并加载插件
    print("\n🧪 测试2: 插件扫描与加载")
    plugins = pm.scan_plugins()
    
    if plugins:
        print(f"✅ 2. 扫描到 {len(plugins)} 个插件")
        for p in plugins:
            print(f"   - {p.name} v{p.version} ({len(p.nodes)} 节点)")
    else:
        print("⚠️ 2. 未找到插件（可能user_plugins为空）")
    
    # 3. 验证热重载器集成
    print("\n🧪 测试3: 热重载器集成")
    if hasattr(pm, 'hot_reloader') and pm.hot_reloader is not None:
        print("✅ 3. 热重载器已初始化")
    else:
        print("❌ 3. 热重载器未初始化")
        return False
    
    # 4. 验证安装器集成
    print("\n🧪 测试4: 安装器集成")
    if hasattr(pm, 'installer') and pm.installer is not None:
        print("✅ 4. 安装器已初始化")
    else:
        print("❌ 4. 安装器未初始化")
        return False
    
    # 5. 验证依赖解析器
    print("\n🧪 测试5: 依赖解析器")
    from plugins.dependency_resolver import DependencyResolver
    
    test_result = DependencyResolver.check_dependency('numpy')
    if test_result:
        print("✅ 5. 依赖解析器工作正常")
    else:
        print("⚠️ 5. numpy未安装（不影响功能）")
    
    # 6. 验证安全检查
    print("\n🧪 测试6: 安全检查机制")
    from plugins.permission_checker import PermissionChecker
    
    dangerous_code = "import os; os.system('test')"
    violations = PermissionChecker.check_source_code(dangerous_code)
    
    if violations:
        print(f"✅ 6. 安全检查拦截危险代码 ({len(violations)} 项违规)")
    else:
        print("❌ 6. 安全检查未拦截危险代码")
        return False
    
    # 7. 模拟UI调用流程
    print("\n🧪 测试7: 模拟UI调用流程")
    try:
        # 模拟获取插件列表
        installed = pm.get_installed_plugins()
        print(f"   ✅ get_installed_plugins() 返回 {len(installed)} 个插件")
        
        # 模拟卸载（如果存在测试插件）
        if 'test_morphology' in pm.plugins:
            print(f"   ✅ 可以访问 test_morphology 插件信息")
        
        print("✅ 7. UI调用流程模拟成功")
    except Exception as e:
        print(f"❌ 7. UI调用流程失败: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("Step 7 测试通过！✅")
    print("注意：完整UI功能需启动GUI程序验证")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_step7()
    sys.exit(0 if success else 1)
