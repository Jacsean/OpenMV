"""
YOLO 训练节点测试脚本

验证训练节点类是否可以正常导入和实例化
"""

import sys
import os

# 添加项目路径
project_root = os.path.join(os.path.dirname(__file__), '..', 'src', 'python')
sys.path.insert(0, project_root)


def test_yolo_trainer_node():
    """测试 YOLO 训练节点"""
    print("=" * 60)
    print("测试 YOLO 训练节点")
    print("=" * 60)
    
    try:
        from user_plugins.yolo_vision.nodes.training import YOLOTrainerNode
        
        print("\n✅ 节点类导入成功\n")
        
        # 测试实例化
        print("测试节点实例化...")
        trainer_node = YOLOTrainerNode()
        
        print(f"  ✅ YOLOTrainerNode 实例化成功")
        print(f"     - 资源等级: {trainer_node.resource_level}")
        print(f"     - 硬件要求:")
        hw_req = trainer_node.hardware_requirements
        print(f"       * CPU: {hw_req['cpu_cores']} 核心")
        print(f"       * 内存: {hw_req['memory_gb']} GB")
        print(f"       * GPU: {'必需' if hw_req['gpu_required'] else '可选'}")
        print(f"       * 显存: {hw_req['gpu_memory_gb']} GB")
        
        # 检查端口
        print(f"\n  📌 输入端口:")
        for port in trainer_node.input_ports():
            print(f"     - {port.name()}")
        
        print(f"\n  📌 输出端口:")
        for port in trainer_node.output_ports():
            print(f"     - {port.name()}")
        
        # 检查参数
        print(f"\n  📌 训练参数:")
        params = ['model_type', 'epochs', 'batch_size', 'img_size', 'save_dir']
        for param in params:
            value = trainer_node.get_property(param)
            print(f"     - {param}: {value}")
        
        print("\n✅ 所有测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = test_yolo_trainer_node()
    sys.exit(0 if success else 1)
