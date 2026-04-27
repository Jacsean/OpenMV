#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
修复所有插件节点的导入路径

将 ....base_nodes（4点）改为 ...base_nodes（3点）
适用于直接在 nodes/ 目录下的节点文件
"""

from pathlib import Path
import re


def fix_import_paths():
    """修复导入路径"""
    # 从 tools 目录向上两级到项目根目录
    project_root = Path(__file__).parent.parent
    plugins_dir = project_root / "src" / "python" / "user_plugins"
    
    fixed_count = 0
    
    for plugin_dir in plugins_dir.iterdir():
        if not plugin_dir.is_dir() or plugin_dir.name.startswith('.'):
            continue
        
        nodes_dir = plugin_dir / "nodes"
        if not nodes_dir.exists():
            continue
        
        # 遍历所有 .py 文件（包括子目录）
        for py_file in nodes_dir.rglob("*.py"):
            if py_file.name == "__init__.py":
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否需要修复
                if 'from ....base_nodes import' in content:
                    # 计算相对层级
                    # 如果文件在 nodes/ 目录下，应该用 3 个点
                    # 如果文件在 nodes/subdir/ 目录下，应该用 4 个点
                    
                    relative_path = py_file.relative_to(nodes_dir)
                    depth = len(relative_path.parts) - 1  # 减去文件名
                    
                    if depth == 0:
                        # 直接在 nodes/ 目录下，用 3 个点
                        new_content = content.replace(
                            'from ....base_nodes import',
                            'from ...base_nodes import'
                        )
                    else:
                        # 在子目录下，保持 4 个点
                        continue
                    
                    if new_content != content:
                        with open(py_file, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"✅ 修复: {py_file.relative_to(plugins_dir)}")
                        fixed_count += 1
            
            except Exception as e:
                print(f"❌ 处理失败 {py_file}: {e}")
    
    print(f"\n🎉 共修复 {fixed_count} 个文件")


if __name__ == "__main__":
    fix_import_paths()
