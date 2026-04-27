"""
批量修复builtin插件的导入路径

将所有 builtin 插件中的旧导入：
    from ...base_nodes import AIBaseNode
替换为新导入：
    from shared_libs.node_base import BaseNode
"""
import os
from pathlib import Path

def fix_import_paths():
    """修复所有builtin插件的导入路径"""
    
    builtin_dir = Path('src/python/plugin_packages/builtin')
    
    if not builtin_dir.exists():
        print(f"❌ 目录不存在: {builtin_dir}")
        return
    
    print("=" * 80)
    print("批量修复builtin插件导入路径")
    print("=" * 80)
    
    fixed_count = 0
    error_count = 0
    
    # 遍历所有Python文件
    for py_file in builtin_dir.rglob('*.py'):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # 替换旧的相对导入
            if 'from ...base_nodes import AIBaseNode' in content:
                content = content.replace(
                    'from ...base_nodes import AIBaseNode',
                    'from shared_libs.node_base import BaseNode'
                )
                print(f"✅ {py_file.relative_to(Path('.'))}: 已修复导入路径")
                fixed_count += 1
            
            # 替换类继承（如果有直接使用AIBaseNode的地方）
            if '(AIBaseNode):' in content:
                content = content.replace('(AIBaseNode):', '(BaseNode):')
                print(f"   📝 {py_file.name}: 更新类继承为BaseNode")
            
            # 保存修改
            if content != original_content:
                with open(py_file, 'w', encoding='utf-8') as f:
                    f.write(content)
        
        except Exception as e:
            print(f"❌ {py_file}: 处理失败 - {e}")
            error_count += 1
    
    print("\n" + "=" * 80)
    print(f"修复完成！")
    print(f"  ✅ 成功修复: {fixed_count} 个文件")
    print(f"  ❌ 错误: {error_count} 个文件")
    print("=" * 80)

if __name__ == '__main__':
    fix_import_paths()