#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移准备检查工具

在重装系统或更换设备前运行此脚本，确保所有重要内容已备份。

使用方法：
    python tools/check_migration_readiness.py
"""

import os
import sys
from pathlib import Path


def check_docs_completeness(project_root):
    """检查文档完整性"""
    print("=" * 80)
    print("📋 检查文档完整性")
    print("=" * 80)
    
    docs_dir = project_root / "docs"
    required_docs = [
        "AI_MODULE_RESOURCE_ISOLATION.md",
        "UNIFIED_NODE_DEVELOPMENT_GUIDE.md",
        "PLUGIN_MIGRATION_TUTORIAL.md",
        "Unified_Plugin_System.md",
        "CROSS_ENVIRONMENT_MIGRATION.md",  # 新增的迁移指南
    ]
    
    missing = []
    for doc in required_docs:
        doc_path = docs_dir / doc
        if doc_path.exists():
            size = doc_path.stat().st_size
            print(f"  ✅ {doc:<40} ({size/1024:.1f} KB)")
        else:
            print(f"  ❌ {doc:<40} (缺失)")
            missing.append(doc)
    
    if missing:
        print(f"\n⚠️  警告：缺少 {len(missing)} 个关键文档")
        for doc in missing:
            print(f"   - {doc}")
        return False
    else:
        print(f"\n✅ 所有关键文档完整")
        return True


def check_git_status(project_root):
    """检查 Git 状态"""
    print("\n" + "=" * 80)
    print("🔍 检查 Git 状态")
    print("=" * 80)
    
    git_dir = project_root / ".git"
    if not git_dir.exists():
        print("  ❌ 未检测到 Git 仓库")
        print("  💡 建议：运行 'git init' 并提交所有文件")
        return False
    
    print("  ✅ Git 仓库存在")
    
    # 检查是否有未提交的更改
    try:
        import subprocess
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.stdout.strip():
            print("  ⚠️  警告：有未提交的更改")
            print("  💡 建议：运行 'git add . && git commit -m \"保存迁移前状态\"'")
            return False
        else:
            print("  ✅ 工作区干净，无未提交更改")
            return True
            
    except Exception as e:
        print(f"  ⚠️  无法检查 Git 状态：{e}")
        return True  # 不阻塞迁移


def check_project_structure(project_root):
    """检查项目结构"""
    print("\n" + "=" * 80)
    print("🏗️  检查项目结构")
    print("=" * 80)
    
    required_dirs = [
        "src/python",
        "src/python/user_plugins",
        "src/python/shared_libs",
        "src/python/workspace",  # 修正路径
    ]
    
    missing = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  ✅ {dir_path}")
        else:
            print(f"  ❌ {dir_path} (缺失)")
            missing.append(dir_path)
    
    if missing:
        print(f"\n⚠️  警告：缺少 {len(missing)} 个关键目录")
        return False
    else:
        print(f"\n✅ 项目结构完整")
        return True


def check_plugin_packages(project_root):
    """检查插件包"""
    print("\n" + "=" * 80)
    print("📦 检查插件包")
    print("=" * 80)
    
    plugins_dir = project_root / "src" / "python" / "user_plugins"
    if not plugins_dir.exists():
        print("  ❌ 插件目录不存在")
        return False
    
    plugin_count = 0
    plugins_without_json = []
    
    for item in plugins_dir.iterdir():
        if item.is_dir() and not item.name.startswith('_') and not item.name.startswith('.'):
            plugin_count += 1
            json_file = item / "plugin.json"
            if not json_file.exists():
                plugins_without_json.append(item.name)
    
    print(f"  ✅ 发现 {plugin_count} 个插件包")
    
    if plugins_without_json:
        print(f"  ⚠️  以下插件缺少 plugin.json：")
        for name in plugins_without_json:
            print(f"     - {name}")
        return False
    else:
        print(f"  ✅ 所有插件都有 plugin.json")
        return True


def generate_checklist(project_root):
    """生成迁移检查清单"""
    print("\n" + "=" * 80)
    print("📝 迁移检查清单")
    print("=" * 80)
    
    checklist = [
        ("文档完整性", check_docs_completeness(project_root)),
        ("Git 状态", check_git_status(project_root)),
        ("项目结构", check_project_structure(project_root)),
        ("插件包", check_plugin_packages(project_root)),
    ]
    
    print("\n" + "=" * 80)
    print("📊 检查结果汇总")
    print("=" * 80)
    
    all_passed = True
    for name, passed in checklist:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {status} - {name}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 所有检查通过！可以安全迁移")
        print("\n下一步：")
        print("  1. 推送所有 Git 更改: git push")
        print("  2. 备份全局记忆（如果使用）")
        print("  3. 创建迁移包（可选）")
        print("  4. 参考 docs/CROSS_ENVIRONMENT_MIGRATION.md 进行迁移")
    else:
        print("⚠️  存在未通过的检查项，建议先修复后再迁移")
        print("\n请参考上述详细输出进行修复")
    
    print("=" * 80)
    
    return all_passed


def main():
    """主函数"""
    print("\n" + "=" * 80)
    print("🔄 StduyOpenCV 迁移准备检查工具")
    print("=" * 80 + "\n")
    
    # 确定项目根目录
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    
    print(f"项目根目录: {project_root}\n")
    
    # 执行检查
    success = generate_checklist(project_root)
    
    # 返回退出码
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
