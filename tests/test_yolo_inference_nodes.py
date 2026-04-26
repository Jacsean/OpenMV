"""
YOLO 推理节点测试脚本

验证节点类是否可以正常导入和实例化
"""

import sys
import os

# 添加项目路径
project_root = os.path.join(os.path.dirname(__file__), '..', 'src', 'python')
sys.path.insert(0, project_root)


def test_import_nodes():
    """测试节点导入"""
    print("=" * 60)
    print("测试 YOLO 推理节点导入")
    print("=" * 60)
    
    try:
        from user_plugins.yolo_vision.nodes.inference import (
            YOLODetectNode,
            YOLOClassifyNode,
            YOLOSegmentNode,
            YOLOPoseNode
        )
        print("✅ 所有节点类导入成功\n")
        
        # 测试实例化
        print("测试节点实例化...")
        
        detect_node = YOLODetectNode()
        print(f"  ✅ YOLODetectNode 实例化成功")
        print(f"     - 资源等级: {detect_node.resource_level}")
        print(f"     - 硬件要求: {detect_node.hardware_requirements}")
        
        classify_node = YOLOClassifyNode()
        print(f"  ✅ YOLOClassifyNode 实例化成功")
        print(f"     - 资源等级: {classify_node.resource_level}")
        
        segment_node = YOLOSegmentNode()
        print(f"  ✅ YOLOSegmentNode 实例化成功")
        print(f"     - 资源等级: {segment_node.resource_level}")
        
        pose_node = YOLOPoseNode()
        print(f"  ✅ YOLOPoseNode 实例化成功")
        print(f"     - 资源等级: {pose_node.resource_level}")
        
        print("\n✅ 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_import_nodes()
    sys.exit(0 if success else 1)
