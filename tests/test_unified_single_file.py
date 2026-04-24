"""
测试统一单文件模式（保存/打开）

验证保存和打开工程都使用单文件.proj格式
"""
import sys
import os
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_unified_single_file_mode():
    """测试统一的单文件模式"""
    print("=" * 70)
    print("测试: 统一单文件模式（保存/打开）")
    print("=" * 70)
    
    from PySide2 import QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    
    from core.project_manager import Project, Workflow, project_manager
    
    # === 1. 创建测试工程 ===
    print("\n📝 步骤1: 创建测试工程")
    print("-" * 70)
    
    project = project_manager.create_project("测试统一模式")
    project.description = "测试保存和打开都使用单文件模式"
    project.author = "测试用户"
    project.tags = ["测试", "单文件", "统一模式"]
    project.category = "测试工程"
    
    # 添加工作流
    project_manager.add_new_workflow("工作流 2")
    project_manager.add_new_workflow("工作流 3")
    
    print(f"✅ 工程名称: {project.name}")
    print(f"✅ 工作流数量: {len(project.workflows)}")
    
    # === 2. 保存为单文件 ===
    print("\n💾 步骤2: 保存工程为单文件")
    print("-" * 70)
    
    temp_dir = tempfile.gettempdir()
    output_file = os.path.join(temp_dir, "test_unified.proj")
    
    print(f"保存目标: {output_file}")
    
    success = project_manager.save_project(output_file)
    
    if success:
        print(f"✅ 保存成功")
        
        # 检查文件
        if os.path.exists(output_file):
            size_bytes = os.path.getsize(output_file)
            size_kb = size_bytes / 1024
            print(f"✅ 文件大小: {size_kb:.2f} KB")
            
            # 验证ZIP格式
            import zipfile
            if zipfile.is_zipfile(output_file):
                print(f"✅ 文件格式: ZIP压缩格式")
                
                with zipfile.ZipFile(output_file, 'r') as zipf:
                    file_list = zipf.namelist()
                    print(f"\n📁 ZIP内容:")
                    for filename in file_list[:10]:
                        print(f"   - {filename}")
            else:
                print(f"❌ 文件格式错误")
                return False
    else:
        print(f"❌ 保存失败")
        return False
    
    # === 3. 关闭工程 ===
    print("\n🗑️ 步骤3: 关闭当前工程")
    print("-" * 70)
    
    project_manager.close_project()
    print(f"✅ 工程已关闭")
    
    # === 4. 打开单文件工程 ===
    print("\n📂 步骤4: 打开单文件工程")
    print("-" * 70)
    
    opened_project = project_manager.open_project(output_file)
    
    if opened_project:
        print(f"✅ 打开成功")
        print(f"   工程名称: {opened_project.name}")
        print(f"   工作流数量: {len(opened_project.workflows)}")
        print(f"   描述: {opened_project.description}")
        print(f"   格式类型: {opened_project.format_type}")
        
        # 验证数据完整性
        if (opened_project.name == project.name and 
            len(opened_project.workflows) == len(project.workflows)):
            print(f"\n✅ 数据完整性验证通过")
        else:
            print(f"\n⚠️ 数据完整性验证失败")
            return False
    else:
        print(f"❌ 打开失败")
        return False
    
    # === 5. 再次保存（覆盖）===
    print("\n💾 步骤5: 再次保存（覆盖原文件）")
    print("-" * 70)
    
    success = project_manager.save_project(output_file)
    
    if success:
        print(f"✅ 覆盖保存成功")
        
        # 验证文件仍然有效
        import zipfile
        if zipfile.is_zipfile(output_file):
            print(f"✅ 文件仍然有效")
        else:
            print(f"❌ 文件损坏")
            return False
    else:
        print(f"❌ 覆盖保存失败")
        return False
    
    # === 6. 清理测试文件 ===
    print("\n🧹 步骤6: 清理测试文件")
    print("-" * 70)
    
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"✅ 已删除测试文件: {output_file}")
    
    print("\n" + "=" * 70)
    print("✅ 所有测试通过！")
    print("=" * 70)
    
    print("\n💡 功能说明:")
    print("   1. 保存工程 → 自动保存为.proj单文件（ZIP格式）")
    print("   2. 打开工程 → 自动从.proj单文件加载")
    print("   3. 无需区分'导出'和'导入'，统一使用'保存'和'打开'")
    print("   4. 用户体验更简洁，操作流程更直观")
    
    return True

if __name__ == '__main__':
    success = test_unified_single_file_mode()
    sys.exit(0 if success else 1)
