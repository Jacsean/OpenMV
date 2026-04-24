"""
测试工程保存功能 - 验证save_session() API修复
"""
import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_save_session_api():
    """测试NodeGraphQt的save_session API"""
    print("=" * 60)
    print("测试: NodeGraphQt save_session() API")
    print("=" * 60)
    
    from PySide2 import QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    
    from NodeGraphQt import NodeGraph
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix='test_save_')
    print(f"\n✅ 创建临时目录: {temp_dir}")
    
    try:
        # 创建NodeGraph实例
        graph = NodeGraph()
        print("✅ 创建NodeGraph实例")
        
        # 测试save_session
        test_file = os.path.join(temp_dir, 'test_workflow.json')
        graph.save_session(test_file)
        print(f"✅ 保存工作流到: {test_file}")
        
        # 验证文件存在
        if os.path.exists(test_file):
            file_size = os.path.getsize(test_file)
            print(f"✅ 文件已创建，大小: {file_size} bytes")
            
            # 读取并验证JSON格式
            import json
            with open(test_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ JSON格式验证通过，包含 {len(data)} 个键")
            
            # 测试deserialize_session
            graph2 = NodeGraph()
            graph2.deserialize_session(data)
            print("✅ deserialize_session() 加载成功")
            
            print("\n" + "=" * 60)
            print("🎉 所有测试通过！")
            print("=" * 60)
            return True
        else:
            print("❌ 文件未创建")
            return False
            
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"\n🗑️ 清理临时目录: {temp_dir}")

if __name__ == '__main__':
    success = test_save_session_api()
    sys.exit(0 if success else 1)
