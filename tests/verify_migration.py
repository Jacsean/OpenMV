"""
验证插件迁移效果

检查所有插件的 plugin.json 是否正确包含新字段，
并验证 PluginManager 能否正确解析。
"""

import sys
import os
import json
from pathlib import Path

# 添加项目路径
project_root = os.path.join(os.path.dirname(__file__), '..', 'src', 'python')
sys.path.insert(0, project_root)


def verify_plugin_json_structure():
    """验证所有插件的 JSON 结构"""
    print("=" * 80)
    print("验证插件 JSON 结构")
    print("=" * 80)
    
    plugins_dir = Path(project_root) / "user_plugins"
    plugins = [p for p in plugins_dir.iterdir() if p.is_dir() and (p / "plugin.json").exists()]
    
    results = []
    
    for plugin_path in sorted(plugins):
        plugin_name = plugin_path.name
        
        # 跳过特殊目录
        if plugin_name.startswith('__') or plugin_name == '.gitkeep':
            continue
        
        try:
            with open(plugin_path / "plugin.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查必需字段
            checks = {
                'name': 'name' in data,
                'version': 'version' in data,
                'category_group': 'category_group' in data,
                'nodes_array': 'nodes' in data and isinstance(data['nodes'], list),
            }
            
            # 检查新字段（迁移后应该有）
            new_fields = {
                'resource_level': 'resource_level' in data,
                'hardware_recommendations': 'hardware_recommendations' in data,
            }
            
            # 检查节点级别的新字段
            nodes_with_new_fields = 0
            total_nodes = len(data.get('nodes', []))
            
            # 如果是空插件（没有节点），跳过节点级别检查
            if total_nodes == 0:
                node_check = {
                    'all_nodes_have_resource_level': True,
                    'all_nodes_have_hardware_req': True,
                    'total_nodes': 0,
                    'nodes_migrated': 0
                }
                print(f"\nℹ️  插件: {plugin_name} (空插件，无节点)")
                
                # 空插件只要有插件级 resource_level 就算通过
                all_checks = {**checks, **new_fields, **node_check}
                # 对于空插件，只检查插件级字段，不检查节点级字段
                all_passed = all(v for k, v in all_checks.items() if k not in ['total_nodes', 'nodes_migrated'])
            else:
                for node in data.get('nodes', []):
                    has_resource_level = 'resource_level' in node
                    has_hardware_req = 'hardware_requirements' in node
                    has_dependencies = 'dependencies' in node
                    
                    if has_resource_level and has_hardware_req and has_dependencies:
                        nodes_with_new_fields += 1
                
                node_check = {
                    'all_nodes_have_resource_level': nodes_with_new_fields == total_nodes,
                    'all_nodes_have_hardware_req': nodes_with_new_fields == total_nodes,
                    'total_nodes': total_nodes,
                    'nodes_migrated': nodes_with_new_fields
                }
                
                print(f"\n{status} 插件: {plugin_name}")
                print(f"   节点数量: {total_nodes}")
                print(f"   已迁移节点: {nodes_with_new_fields}/{total_nodes}")
            
                all_checks = {**checks, **new_fields, **node_check}
                all_passed = all(all_checks.values())
            
            status = "✅" if all_passed else "⚠️"
            
            if not all_passed:
                print(f"   ❌ 失败的检查:")
                for check_name, passed in all_checks.items():
                    if not passed:
                        print(f"      - {check_name}")
            
            results.append({
                'plugin': plugin_name,
                'passed': all_passed,
                'details': all_checks
            })
            
        except Exception as e:
            print(f"\n❌ 插件: {plugin_name} - 解析失败: {e}")
            results.append({
                'plugin': plugin_name,
                'passed': False,
                'error': str(e)
            })
    
    # 汇总报告
    print(f"\n\n{'='*80}")
    print("验证汇总报告")
    print(f"{'='*80}")
    
    passed_count = sum(1 for r in results if r['passed'])
    failed_count = len(results) - passed_count
    
    print(f"\n✅ 通过: {passed_count}")
    print(f"❌ 失败: {failed_count}")
    print(f"📊 总计: {len(results)}")
    
    if failed_count > 0:
        print(f"\n失败的插件:")
        for r in results:
            if not r['passed']:
                print(f"  - {r['plugin']}")
    
    return passed_count == len(results)


def verify_plugin_manager_parsing():
    """验证 PluginManager 能否正确解析新字段"""
    print(f"\n\n{'='*80}")
    print("验证 PluginManager 解析能力")
    print(f"{'='*80}\n")
    
    try:
        from plugins.plugin_manager import PluginManager
        from plugins.models import NodeDefinition, PluginInfo
        
        print("✅ PluginManager 导入成功\n")
        
        # 创建 PluginManager 实例
        pm = PluginManager()
        
        # 加载所有插件（scan_plugins 不需要参数，会自动扫描 user_plugins 目录）
        pm.scan_plugins()
        
        print(f"📦 扫描到 {len(pm.plugins)} 个插件\n")
        
        # 检查每个插件的元数据
        success_count = 0
        fail_count = 0
        
        for plugin_id, plugin_info in pm.plugins.items():
            print(f"检查插件: {plugin_id}")
            
            try:
                # 检查 PluginInfo 是否有新字段
                has_installation_guide = hasattr(plugin_info, 'installation_guide')
                has_hardware_rec = hasattr(plugin_info, 'hardware_recommendations')
                
                # 检查节点定义
                nodes_checked = 0
                nodes_with_resource_level = 0
                
                for node_def in plugin_info.nodes:
                    nodes_checked += 1
                    if hasattr(node_def, 'resource_level'):
                        nodes_with_resource_level += 1
                
                all_ok = nodes_with_resource_level == nodes_checked
                
                if all_ok:
                    print(f"  ✅ {plugin_info.name} ({len(plugin_info.nodes)} 个节点)")
                    print(f"     - resource_level: {plugin_info.resource_level if hasattr(plugin_info, 'resource_level') else 'N/A'}")
                    success_count += 1
                else:
                    print(f"  ⚠️ {plugin_info.name} - 部分节点缺少字段")
                    print(f"     - 节点总数: {nodes_checked}")
                    print(f"     - 有 resource_level: {nodes_with_resource_level}")
                    fail_count += 1
                    
            except Exception as e:
                print(f"  ❌ {plugin_id} - 检查失败: {e}")
                fail_count += 1
        
        print(f"\n\n{'='*80}")
        print("PluginManager 解析验证汇总")
        print(f"{'='*80}")
        print(f"✅ 成功: {success_count}")
        print(f"⚠️  警告: {fail_count}")
        
        return fail_count == 0
        
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        print("💡 请确保项目路径正确")
        return False
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("开始验证插件迁移效果...\n")
    
    # 验证 1: JSON 结构
    json_valid = verify_plugin_json_structure()
    
    # 验证 2: PluginManager 解析
    pm_valid = verify_plugin_manager_parsing()
    
    # 最终结论
    print(f"\n\n{'='*80}")
    print("最终结论")
    print(f"{'='*80}")
    
    if json_valid and pm_valid:
        print("✅ 所有验证通过！迁移成功！")
        sys.exit(0)
    else:
        print("⚠️  存在验证失败，请检查上述报告")
        sys.exit(1)
