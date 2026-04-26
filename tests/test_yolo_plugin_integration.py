"""
YOLO 插件集成测试

验证 YOLO 插件能否被 PluginManager 正确加载和解析
"""

import sys
import os
from pathlib import Path

# 添加项目路径
project_root = os.path.join(os.path.dirname(__file__), '..', 'src', 'python')
sys.path.insert(0, project_root)

from plugins.plugin_manager import PluginManager


def test_yolo_plugin_loading():
    """测试 YOLO 插件加载"""
    print("=" * 60)
    print("测试 YOLO 插件加载")
    print("=" * 60)
    
    # 获取 PluginManager 单例
    manager = PluginManager()
    
    # 扫描插件
    print("\n1. 扫描插件目录...")
    plugins = manager.scan_plugins()
    print(f"   发现 {len(plugins)} 个插件")
    
    # 查找 YOLO 插件
    yolo_plugin = None
    for plugin in plugins:
        if plugin.name == 'yolo_vision':
            yolo_plugin = plugin
            break
    
    if not yolo_plugin:
        print("\n❌ 未找到 yolo_vision 插件")
        return False
    
    print(f"\n2. 找到 YOLO 插件:")
    print(f"   名称: {yolo_plugin.name}")
    print(f"   版本: {yolo_plugin.version}")
    print(f"   分类组: {yolo_plugin.category_group}")
    print(f"   节点数量: {len(yolo_plugin.nodes)}")
    
    # 检查节点定义
    print(f"\n3. 检查节点定义:")
    for i, node_def in enumerate(yolo_plugin.nodes, 1):
        print(f"\n   [{i}] {node_def.display_name}")
        print(f"       类名: {node_def.class_name}")
        print(f"       分类: {node_def.category}")
        print(f"       资源等级: {node_def.resource_level}")
        print(f"       硬件要求:")
        hw_req = node_def.hardware_requirements
        print(f"         - CPU: {hw_req.get('cpu_cores')} 核心")
        print(f"         - 内存: {hw_req.get('memory_gb')} GB")
        print(f"         - GPU: {'必需' if hw_req.get('gpu_required') else '可选'}")
        if hw_req.get('gpu_memory_gb', 0) > 0:
            print(f"         - 显存: {hw_req['gpu_memory_gb']} GB")
        print(f"       依赖: {', '.join(node_def.dependencies) if node_def.dependencies else '无'}")
    
    # 检查安装指南
    if yolo_plugin.installation_guide:
        print(f"\n4. 安装指南:")
        for mode, guide in yolo_plugin.installation_guide.items():
            print(f"   - {mode}: {guide.get('description', '')}")
    
    # 检查硬件推荐
    if yolo_plugin.hardware_recommendations:
        print(f"\n5. 硬件推荐:")
        for scenario, rec in yolo_plugin.hardware_recommendations.items():
            print(f"   - {scenario}: {rec.get('description', '')}")
    
    print("\n✅ YOLO 插件加载测试通过！")
    return True


if __name__ == '__main__':
    try:
        success = test_yolo_plugin_loading()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
