"""
OCR 文字识别节点测试脚本

验证 OCRTextRecognitionNode 的基本功能。
"""

import sys
import os

# 添加项目路径
project_root = os.path.join(os.path.dirname(__file__), '..', 'src', 'python')
sys.path.insert(0, project_root)


def test_ocr_node_import():
    """测试节点导入"""
    print("=" * 80)
    print("测试 1: 导入 OCR 节点")
    print("=" * 80)
    
    try:
        from user_plugins.ocr_vision.nodes.inference.ocr_recognize import OCRTextRecognitionNode
        print("✅ OCRTextRecognitionNode 导入成功")
        
        # 检查基类
        from user_plugins.base_nodes import AIBaseNode
        assert issubclass(OCRTextRecognitionNode, AIBaseNode), "节点未继承 AIBaseNode"
        print("✅ 正确继承 AIBaseNode")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ocr_node_creation():
    """测试节点实例化"""
    print("\n" + "=" * 80)
    print("测试 2: 创建 OCR 节点实例")
    print("=" * 80)
    
    try:
        from user_plugins.ocr_vision.nodes.inference.ocr_recognize import OCRTextRecognitionNode
        
        node = OCRTextRecognitionNode()
        print(f"✅ 节点创建成功: {node.NODE_NAME}")
        print(f"   - 标识符: {node.__identifier__}")
        print(f"   - 资源等级: {node.resource_level}")
        
        # 检查端口
        input_ports = node.input_ports()
        output_ports = node.output_ports()
        
        print(f"   - 输入端口数: {len(input_ports)}")
        print(f"   - 输出端口数: {len(output_ports)}")
        
        for port in input_ports:
            print(f"     输入: {port.name()}")
        
        for port in output_ports:
            print(f"     输出: {port.name()}")
        
        return True
    except Exception as e:
        print(f"❌ 实例化失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ocr_node_parameters():
    """测试节点参数"""
    print("\n" + "=" * 80)
    print("测试 3: 检查节点参数")
    print("=" * 80)
    
    try:
        from user_plugins.ocr_vision.nodes.inference.ocr_recognize import OCRTextRecognitionNode
        
        node = OCRTextRecognitionNode()
        
        # 检查参数是否存在
        params_to_check = ['lang', 'det_db_thresh', 'rec_batch_num', 'use_gpu', 'show_visualization']
        
        for param in params_to_check:
            try:
                value = node.get_property(param)
                print(f"✅ 参数 '{param}': {value}")
            except Exception as e:
                print(f"⚠️  参数 '{param}' 不存在或读取失败: {e}")
        
        return True
    except Exception as e:
        print(f"❌ 参数检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ocr_dependencies():
    """测试依赖检查"""
    print("\n" + "=" * 80)
    print("测试 4: 依赖检查")
    print("=" * 80)
    
    try:
        from user_plugins.ocr_vision.nodes.inference.ocr_recognize import OCRTextRecognitionNode
        
        node = OCRTextRecognitionNode()
        deps_ok, deps_msg = node.check_dependencies()
        
        if deps_ok:
            print(f"✅ 依赖检查通过: {deps_msg}")
        else:
            print(f"⚠️  依赖检查失败: {deps_msg}")
            print("💡 请运行以下命令安装依赖:")
            print("   pip install paddlepaddle>=2.4.0 paddleocr>=2.6.0")
        
        return True
    except Exception as e:
        print(f"❌ 依赖检查失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("开始测试 OCR 文字识别节点...\n")
    
    results = []
    
    # 执行测试
    results.append(("导入测试", test_ocr_node_import()))
    results.append(("实例化测试", test_ocr_node_creation()))
    results.append(("参数测试", test_ocr_node_parameters()))
    results.append(("依赖测试", test_ocr_dependencies()))
    
    # 汇总报告
    print(f"\n\n{'='*80}")
    print("测试汇总报告")
    print(f"{'='*80}")
    
    passed = sum(1 for _, result in results if result)
    failed = len(results) - passed
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    print(f"\n总计: {passed}/{len(results)} 通过")
    
    if failed > 0:
        print(f"\n⚠️  有 {failed} 个测试失败，请检查上述错误信息")
        sys.exit(1)
    else:
        print("\n🎉 所有测试通过！")
        sys.exit(0)
