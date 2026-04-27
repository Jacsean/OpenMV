"""
诊断节点库显示问题

检查：
1. 插件是否正确扫描
2. 节点是否正确注册到Graph
3. NodesPaletteWidget是否正确显示
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / 'src' / 'python'))

from plugins.plugin_manager import PluginManager

def diagnose():
    print("=" * 60)
    print("诊断节点库显示问题")
    print("=" * 60)
    
    # 1. 检查PluginManager扫描结果
    print("\n1. 检查插件扫描...")
    pm = PluginManager()
    plugins = pm.scan_plugins()
    
    print(f"   发现 {len(plugins)} 个插件:")
    for p in plugins:
        print(f"   - {p.name}: {len(p.nodes)} 个节点 (source={p.source})")
        for node in p.nodes:
            print(f"     • {node.display_name} (category={node.category})")
    
    # 2. 检查plugin_packages目录结构
    print("\n2. 检查目录结构...")
    base_path = Path('src/python/plugin_packages')
    
    builtin_count = len(list((base_path / 'builtin').iterdir())) if (base_path / 'builtin').exists() else 0
    marketplace_count = len(list((base_path / 'marketplace' / 'installed').iterdir())) if (base_path / 'marketplace' / 'installed').exists() else 0
    
    print(f"   builtin插件数: {builtin_count}")
    print(f"   marketplace插件数: {marketplace_count}")
    
    # 3. 检查关键文件
    print("\n3. 检查关键文件...")
    key_files = [
        'src/python/shared_libs/node_base/base_node.py',
        'src/python/shared_libs/node_base/__init__.py',
        'src/python/plugins/plugin_manager.py',
    ]
    
    for file_path in key_files:
        exists = Path(file_path).exists()
        status = "✅" if exists else "❌"
        print(f"   {status} {file_path}")
    
    # 4. 检查plugin.json配置
    print("\n4. 检查plugin.json配置示例...")
    sample_plugin_json = base_path / 'builtin' / 'io_camera' / 'plugin.json'
    if sample_plugin_json.exists():
        import json
        with open(sample_plugin_json, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"   插件名: {data.get('name')}")
        print(f"   category_group: {data.get('category_group', 'N/A')}")
        print(f"   nodes数量: {len(data.get('nodes', []))}")
        if data.get('nodes'):
            first_node = data['nodes'][0]
            print(f"   第一个节点: {first_node.get('display_name')}")
            print(f"   节点class: {first_node.get('class')}")
    else:
        print("   ❌ 找不到示例plugin.json")
    
    print("\n" + "=" * 60)
    print("诊断完成")
    print("=" * 60)

if __name__ == '__main__':
    diagnose()