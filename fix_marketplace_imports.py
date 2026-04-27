"""
修复marketplace插件的导入路径

将 example_advanced_nodes 和 ocr_vision 中的旧导入路径修复为新路径
"""
import os
from pathlib import Path

def fix_marketplace_imports():
    """修复marketplace插件的导入路径"""
    
    marketplace_dir = Path('src/python/plugin_packages/marketplace/installed')
    
    if not marketplace_dir.exists():
        print(f"❌ 目录不存在: {marketplace_dir}")
        return
    
    print("=" * 80)
    print("修复marketplace插件导入路径")
    print("=" * 80)
    
    # 需要修复的插件列表
    plugins_to_fix = ['example_advanced_nodes', 'ocr_vision']
    
    fixed_count = 0
    error_count = 0
    
    for plugin_name in plugins_to_fix:
        plugin_path = marketplace_dir / plugin_name
        
        if not plugin_path.exists():
            print(f"⚠️ 插件不存在: {plugin_name}")
            continue
        
        print(f"\n📦 处理插件: {plugin_name}")
        
        # 遍历所有Python文件
        for py_file in plugin_path.rglob('*.py'):
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # 替换旧的相对导入（不同层级的相对路径）
                replacements = [
                    ('from ...base_nodes import AIBaseNode', 'from shared_libs.node_base import BaseNode'),
                    ('from ....base_nodes import AIBaseNode', 'from shared_libs.node_base import BaseNode'),
                    ('from .....base_nodes import AIBaseNode', 'from shared_libs.node_base import BaseNode'),
                ]
                
                for old_import, new_import in replacements:
                    if old_import in content:
                        content = content.replace(old_import, new_import)
                        print(f"   ✅ {py_file.relative_to(Path('.'))}: 修复导入路径")
                        fixed_count += 1
                
                # 替换类继承
                if '(AIBaseNode):' in content:
                    content = content.replace('(AIBaseNode):', '(BaseNode):')
                    print(f"   📝 {py_file.name}: 更新类继承为BaseNode")
                
                # 保存修改
                if content != original_content:
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
            
            except Exception as e:
                print(f"   ❌ {py_file}: 处理失败 - {e}")
                error_count += 1
    
    print("\n" + "=" * 80)
    print(f"修复完成！")
    print(f"  ✅ 成功修复: {fixed_count} 个文件")
    print(f"  ❌ 错误: {error_count} 个文件")
    print("=" * 80)

if __name__ == '__main__':
    fix_marketplace_imports()