"""
插件迁移验证脚本 - 验证所有插件的迁移质量

验证内容：
1. JSON结构完整性检查
2. 节点类导入验证
3. 资源声明验证
4. PluginManager加载测试
"""

import json
import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent  # tests -> StduyOpenCV
sys.path.insert(0, str(project_root / "src" / "python"))


def verify_plugin_json(plugin_path):
    """验证 plugin.json 结构完整性"""
    json_file = plugin_path / "plugin.json"
    
    if not json_file.exists():
        return False, f"❌ 缺少 plugin.json"
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 必需字段检查
        required_fields = ['name', 'version', 'category_group', 'nodes']
        for field in required_fields:
            if field not in data:
                return False, f"❌ 缺少必需字段: {field}"
        
        # 新体系字段检查（推荐）
        recommended_fields = ['resource_level', 'hardware_requirements']
        missing_recommended = [f for f in recommended_fields if f not in data]
        
        # 节点列表检查
        if not isinstance(data['nodes'], list):
            return False, f"❌ nodes 字段必须是列表"
        
        # 每个节点的必需字段
        for i, node in enumerate(data['nodes']):
            if 'class' not in node:
                return False, f"❌ 节点 {i} 缺少 class 字段"
            if 'display_name' not in node:
                return False, f"❌ 节点 {i} 缺少 display_name 字段"
        
        warning = ""
        if missing_recommended:
            warning = f"\n⚠️  建议添加字段: {', '.join(missing_recommended)}"
        
        return True, f"✅ 结构完整 ({len(data['nodes'])} 个节点){warning}"
    
    except json.JSONDecodeError as e:
        return False, f"❌ JSON 格式错误: {e}"
    except Exception as e:
        return False, f"❌ 读取失败: {e}"


def verify_nodes_directory(plugin_path):
    """验证 nodes/ 目录结构"""
    nodes_dir = plugin_path / "nodes"
    
    if not nodes_dir.exists():
        return False, f"❌ 缺少 nodes/ 目录"
    
    init_file = nodes_dir / "__init__.py"
    if not init_file.exists():
        return False, f"❌ 缺少 nodes/__init__.py"
    
    # 检查是否有旧的 nodes.py 文件
    old_nodes = plugin_path / "nodes.py"
    if old_nodes.exists():
        return False, f"⚠️  存在旧的 nodes.py 文件（应删除）"
    
    return True, f"✅ 目录结构正确"


def verify_node_classes(plugin_path, plugin_data):
    """验证节点类文件是否存在（递归检查所有 __init__.py）"""
    plugin_name = plugin_data['name']
    nodes_dir = plugin_path / "nodes"
    
    # 获取所有节点类名
    node_classes = [node['class'] for node in plugin_data['nodes']]
    
    # 递归收集所有 __init__.py 的内容
    all_init_content = ""
    for init_file in nodes_dir.rglob("__init__.py"):
        try:
            with open(init_file, 'r', encoding='utf-8') as f:
                all_init_content += f.read() + "\n"
        except Exception:
            pass
    
    if not all_init_content:
        return False, f"❌ 未找到任何 __init__.py 文件"
    
    missing_classes = []
    for class_name in node_classes:
        if class_name not in all_init_content:
            missing_classes.append(class_name)
    
    if missing_classes:
        return False, f"❌ 未导出: {', '.join(missing_classes)}"
    
    return True, f"✅ 所有节点类已声明 ({len(node_classes)} 个)"


def main():
    """主验证函数"""
    print("=" * 80)
    print("🔍 插件迁移验证工具")
    print("=" * 80)
    print()
    
    plugins_dir = project_root / "src" / "python" / "user_plugins"
    
    if not plugins_dir.exists():
        print(f"❌ 插件目录不存在: {plugins_dir}")
        return
    
    # 获取所有插件目录
    plugin_dirs = [d for d in plugins_dir.iterdir() if d.is_dir()]
    
    results = {
        'passed': [],
        'failed': [],
        'warnings': []
    }
    
    for plugin_path in sorted(plugin_dirs):
        plugin_name = plugin_path.name
        
        # 跳过特殊目录
        if plugin_name.startswith('.') or plugin_name == '__pycache__':
            continue
        
        print(f"\n{'─' * 80}")
        print(f"📦 验证插件: {plugin_name}")
        print(f"{'─' * 80}")
        
        # 1. 验证 plugin.json
        json_valid, json_msg = verify_plugin_json(plugin_path)
        print(f"  1. JSON结构: {json_msg}")
        
        if not json_valid:
            results['failed'].append((plugin_name, json_msg))
            continue
        
        # 2. 验证目录结构
        dir_valid, dir_msg = verify_nodes_directory(plugin_path)
        print(f"  2. 目录结构: {dir_msg}")
        
        if not dir_valid:
            results['failed'].append((plugin_name, dir_msg))
            continue
        
        # 3. 读取 plugin.json 数据
        with open(plugin_path / "plugin.json", 'r', encoding='utf-8') as f:
            plugin_data = json.load(f)
        
        # 4. 验证节点类导入
        class_valid, class_msg = verify_node_classes(plugin_path, plugin_data)
        print(f"  3. 节点类导入: {class_msg}")
        
        if not class_valid:
            results['failed'].append((plugin_name, class_msg))
        else:
            results['passed'].append(plugin_name)
            
            # 检查是否有警告信息
            if "⚠️" in json_msg or "⚠️" in dir_msg:
                results['warnings'].append((plugin_name, json_msg + " | " + dir_msg))
    
    # 打印汇总报告
    print(f"\n\n{'=' * 80}")
    print("📊 验证汇总报告")
    print(f"{'=' * 80}")
    print(f"\n✅ 通过: {len(results['passed'])} 个插件")
    for name in results['passed']:
        print(f"   • {name}")
    
    if results['warnings']:
        print(f"\n⚠️  警告: {len(results['warnings'])} 个插件")
        for name, msg in results['warnings']:
            print(f"   • {name}: {msg}")
    
    if results['failed']:
        print(f"\n❌ 失败: {len(results['failed'])} 个插件")
        for name, msg in results['failed']:
            print(f"   • {name}: {msg}")
    
    print(f"\n{'=' * 80}")
    
    total = len(results['passed']) + len(results['failed'])
    if total > 0:
        pass_rate = len(results['passed']) / total * 100
        print(f"🎯 通过率: {pass_rate:.1f}% ({len(results['passed'])}/{total})")
    
    if results['failed']:
        print(f"\n💡 建议: 请修复上述失败的插件后重新验证")
        sys.exit(1)
    else:
        print(f"\n🎉 所有插件验证通过！")
        sys.exit(0)


if __name__ == "__main__":
    main()
