"""
YOLO 标注节点测试脚本

验证标注节点类是否可以正常导入和实例化
"""

import sys
import os

# 添加项目路径
project_root = os.path.join(os.path.dirname(__file__), '..', 'src', 'python')
sys.path.insert(0, project_root)


def test_yolo_annotator_node():
    """测试 YOLO 标注节点"""
    print("=" * 60)
    print("测试 YOLO 标注节点")
    print("=" * 60)
    
    try:
        from user_plugins.yolo_vision.nodes.annotation import YOLOAnnotatorNode
        
        print("\n✅ 节点类导入成功\n")
        
        # 测试实例化
        print("测试节点实例化...")
        annotator_node = YOLOAnnotatorNode()
        
        print(f"  ✅ YOLOAnnotatorNode 实例化成功")
        print(f"     - 资源等级: {annotator_node.resource_level}")
        print(f"     - 硬件要求:")
        hw_req = annotator_node.hardware_requirements
        print(f"       * CPU: {hw_req['cpu_cores']} 核心")
        print(f"       * 内存: {hw_req['memory_gb']} GB")
        print(f"       * GPU: {'必需' if hw_req['gpu_required'] else '可选'}")
        
        # 检查端口
        print(f"\n  📌 输入端口:")
        for port in annotator_node.input_ports():
            print(f"     - {port.name()}")
        
        print(f"\n  📌 输出端口:")
        for port in annotator_node.output_ports():
            print(f"     - {port.name()}")
        
        # 检查参数
        print(f"\n  📌 标注参数:")
        params = ['classes', 'pretrain_model', 'conf_threshold', 'output_dir', 'annotation_format']
        for param in params:
            value = annotator_node.get_property(param)
            print(f"     - {param}: {value}")
        
        print(f"\n  📌 数据集划分:")
        split_params = ['train_ratio', 'val_ratio', 'test_ratio']
        for param in split_params:
            value = annotator_node.get_property(param)
            print(f"     - {param}: {value}")
        
        print("\n✅ 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_yolo_annotator_node()
    sys.exit(0 if success else 1)
