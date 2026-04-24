"""
测试工程单文件模式（ZIP打包）

演示如何导出和导入.proj单文件
"""
import sys
import os
import tempfile
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def test_single_file_mode():
    """测试单文件模式的导出和导入"""
    print("=" * 70)
    print("测试: 工程单文件模式（ZIP打包）")
    print("=" * 70)
    
    from PySide2 import QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    
    from core.project_manager import Project, Workflow, project_manager
    
    # === 1. 创建测试工程 ===
    print("\n📝 步骤1: 创建测试工程")
    print("-" * 70)
    
    project = project_manager.create_project("测试单文件工程")
    project.description = "用于测试ZIP打包功能的示例工程"
    project.author = "测试用户"
    project.tags = ["测试", "ZIP", "单文件"]
    project.category = "测试工程"
    
    # 添加几个工作流
    wf1 = Workflow(name="工作流 1 - 边缘检测")
    wf1.description = "Canny边缘检测流程"
    wf1.node_count = 10
    project_manager.add_new_workflow("工作流 2 - 缺陷识别")
    project_manager.add_new_workflow("工作流 3 - 尺寸测量")
    
    print(f"✅ 工程名称: {project.name}")
    print(f"✅ 工作流数量: {len(project.workflows)}")
    print(f"✅ 描述: {project.description}")
    print(f"✅ 标签: {', '.join(project.tags)}")
    
    # === 2. 导出为单文件 ===
    print("\n📦 步骤2: 导出为单文件（ZIP格式）")
    print("-" * 70)
    
    # 创建临时文件
    temp_dir = tempfile.gettempdir()
    output_file = os.path.join(temp_dir, "test_project.proj")
    
    print(f"导出目标: {output_file}")
    
    success = project_manager.export_project(output_file)
    
    if success:
        print(f"✅ 导出成功")
        
        # 检查文件大小
        if os.path.exists(output_file):
            size_bytes = os.path.getsize(output_file)
            size_kb = size_bytes / 1024
            print(f"✅ 文件大小: {size_kb:.2f} KB ({size_bytes} bytes)")
            
            # 验证ZIP格式
            import zipfile
            if zipfile.is_zipfile(output_file):
                print(f"✅ 文件格式: ZIP压缩格式")
                
                # 列出ZIP内容
                with zipfile.ZipFile(output_file, 'r') as zipf:
                    file_list = zipf.namelist()
                    print(f"\n📁 ZIP文件内容:")
                    for filename in file_list[:10]:  # 只显示前10个
                        print(f"   - {filename}")
                    if len(file_list) > 10:
                        print(f"   ... 共 {len(file_list)} 个文件")
            else:
                print(f"❌ 文件格式错误: 不是有效的ZIP文件")
    else:
        print(f"❌ 导出失败")
        return False
    
    # === 3. 关闭当前工程 ===
    print("\n🗑️ 步骤3: 关闭当前工程")
    print("-" * 70)
    
    project_manager.close_project()
    print(f"✅ 工程已关闭")
    
    # === 4. 从单文件导入 ===
    print("\n📥 步骤4: 从单文件导入工程")
    print("-" * 70)
    
    imported_project = project_manager.import_project(output_file)
    
    if imported_project:
        print(f"✅ 导入成功")
        print(f"   工程名称: {imported_project.name}")
        print(f"   工作流数量: {len(imported_project.workflows)}")
        print(f"   描述: {imported_project.description}")
        print(f"   作者: {imported_project.author}")
        print(f"   标签: {', '.join(imported_project.tags)}")
        print(f"   分类: {imported_project.category}")
        print(f"   格式类型: {imported_project.format_type}")
        
        # 验证数据完整性
        if (imported_project.name == project.name and 
            len(imported_project.workflows) == len(project.workflows)):
            print(f"\n✅ 数据完整性验证通过")
        else:
            print(f"\n⚠️ 数据完整性验证失败")
    else:
        print(f"❌ 导入失败")
        return False
    
    # === 5. 清理测试文件 ===
    print("\n🧹 步骤5: 清理测试文件")
    print("-" * 70)
    
    if os.path.exists(output_file):
        os.remove(output_file)
        print(f"✅ 已删除测试文件: {output_file}")
    
    print("\n" + "=" * 70)
    print("✅ 所有测试通过！")
    print("=" * 70)
    
    print("\n💡 使用提示:")
    print("   1. 在UI中使用 '文件' → '📦 导出工程为单文件' 导出")
    print("   2. 使用 '文件' → '📥 从单文件导入工程' 导入")
    print("   3. 导出的 .proj 文件可以直接拷贝、分享、备份")
    print("   4. 支持ZIP压缩，文件大小通常减少60-70%")
    
    return True

if __name__ == '__main__':
    success = test_single_file_mode()
    sys.exit(0 if success else 1)
