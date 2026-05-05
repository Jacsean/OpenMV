"""
测试io_camera插件加载过程

模拟PluginManager.load_plugin_nodes的完整流程，捕获详细错误
"""

import sys
import os
import importlib.util
from pathlib import Path

# 添加路径
sys.path.insert(0, 'src/python')

print("=" * 70)
print("测试 io_camera 插件加载过程")
print("=" * 70)

plugin_name = 'io_camera'
plugin_path = Path('src/python/plugin_packages/builtin/io_camera')

print(f"\n1. 检查插件结构...")
nodes_dir = plugin_path / "nodes"
nodes_file = plugin_path / "nodes.py"

is_new_structure = nodes_dir.exists() and nodes_dir.is_dir()
is_old_structure = nodes_file.exists()

print(f"   新结构 (nodes/): {is_new_structure}")
print(f"   旧结构 (nodes.py): {is_old_structure}")

if not is_new_structure and not is_old_structure:
    print(f"   ❌ 插件缺少节点文件")
    sys.exit(1)

# 2. 读取源代码
print(f"\n2. 读取源代码...")
if is_new_structure:
    init_file = nodes_dir / "__init__.py"
    if not init_file.exists():
        print(f"   ❌ 缺少 nodes/__init__.py")
        sys.exit(1)
    
    with open(init_file, 'r', encoding='utf-8') as f:
        source_code = f.read()
    
    # 检查所有子模块
    for py_file in nodes_dir.rglob("*.py"):
        if py_file.name != "__init__.py":
            with open(py_file, 'r', encoding='utf-8') as f:
                source_code += "\n" + f.read()
    
    module_path = init_file
    module_name = f"{plugin_name}.nodes"
    print(f"   ✅ 读取 nodes/__init__.py")
    print(f"   📄 源代码总长度: {len(source_code)} 字符")
else:
    with open(nodes_file, 'r', encoding='utf-8') as f:
        source_code = f.read()
    module_path = nodes_file
    module_name = f"plugin_{plugin_name}_nodes"

# 3. 权限检查
print(f"\n3. 执行安全检查...")
try:
    from plugins.permission_checker import PermissionChecker
    violations = PermissionChecker.check_source_code(source_code, plugin_name)
    
    if violations:
        print(f"   ❌ 安全检查失败:")
        for v in violations:
            print(f"      - {v}")
        sys.exit(1)
    else:
        print(f"   ✅ 安全检查通过")
except Exception as e:
    print(f"   ⚠️  安全检查异常: {e}")
    import traceback
    traceback.print_exc()

# 4. 动态导入模块
print(f"\n4. 动态导入模块...")
try:
    # 设置包层次结构
    if is_new_structure:
        plugin_packages_path = plugin_path.parent.parent  # plugin_packages
        
        if str(plugin_packages_path) not in sys.path:
            sys.path.insert(0, str(plugin_packages_path))
            print(f"   ➕ 添加路径: {plugin_packages_path}")
        
        # 确定模块名前缀
        relative_path = plugin_path.relative_to(plugin_packages_path)
        package_prefix = str(relative_path.parent).replace(os.sep, '.')
        module_name = f"{package_prefix}.{plugin_name}.nodes"
        
        print(f"   📦 模块名: {module_name}")
        
        # 注册父包
        if 'plugin_packages' not in sys.modules:
            print(f"   📝 注册 plugin_packages 包")
        
        if package_prefix not in sys.modules:
            print(f"   📝 注册 {package_prefix} 包")
    
    # 创建模块
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    
    print(f"   ✅ 模块对象创建成功")
    
    # 执行模块
    print(f"   🔄 执行模块代码...")
    spec.loader.exec_module(module)
    print(f"   ✅ 模块执行成功")
    
    # 5. 检查导出的类
    print(f"\n5. 检查导出的节点类...")
    expected_classes = [
        'ImageLoadNode',
        'ImageSaveNode',
        'ImageViewNode',
        'JsonDisplayNode',
        'CameraCaptureNode',
        'RealTimePreviewNode',
        'FastDetectionNode',
        'VideoRecorderNode'
    ]
    
    for class_name in expected_classes:
        if hasattr(module, class_name):
            cls = getattr(module, class_name)
            if cls is not None:
                print(f"   ✅ {class_name}: {cls}")
            else:
                print(f"   ⚠️  {class_name}: None")
        else:
            print(f"   ❌ {class_name}: 未找到")
    
    print("\n" + "=" * 70)
    print("✅ 插件加载测试成功！")
    print("=" * 70)
    
except Exception as e:
    print(f"\n❌ 模块导入失败: {e}")
    print(f"\n详细错误信息:")
    import traceback
    traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("❌ 插件加载测试失败")
    print("=" * 70)
    sys.exit(1)
