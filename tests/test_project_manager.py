"""
工程和工作流管理模块测试脚本

测试Workflow、Project、ProjectManager类的功能
"""

import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.project_manager import Workflow, Project, ProjectManager, project_manager


def test_workflow():
    """测试Workflow类"""
    print("=" * 60)
    print("测试1: Workflow类")
    print("=" * 60)
    
    # 创建工作流
    wf = Workflow(name="边缘检测流程")
    print(f"✅ 创建工作流: {wf}")
    print(f"   ID: {wf.id}")
    print(f"   名称: {wf.name}")
    print(f"   已修改: {wf.is_modified}")
    
    # 标记为已修改
    wf.mark_modified()
    print(f"\n✅ 标记为已修改: {wf.is_modified}")
    
    # 标记为已保存
    wf.mark_saved()
    print(f"✅ 标记为已保存: {wf.is_modified}")
    
    # 序列化/反序列化
    data = wf.to_dict()
    print(f"\n✅ 序列化为字典:")
    for key, value in data.items():
        print(f"   {key}: {value}")
        
    wf2 = Workflow.from_dict(data)
    print(f"\n✅ 从字典恢复: {wf2}")
    assert wf2.id == wf.id
    assert wf2.name == wf.name
    print("✅ 序列化/反序列化测试通过")
    
    print("\n" + "=" * 60 + "\n")


def test_project():
    """测试Project类"""
    print("=" * 60)
    print("测试2: Project类")
    print("=" * 60)
    
    # 创建工程
    proj = Project(name="视觉检测工程")
    print(f"✅ 创建工程: {proj}")
    
    # 添加工作流
    wf1 = Workflow(name="工作流 1 - 边缘检测")
    wf2 = Workflow(name="工作流 2 - 二值化")
    wf3 = Workflow(name="工作流 3 - 形态学")
    
    idx1 = proj.add_workflow(wf1)
    idx2 = proj.add_workflow(wf2)
    idx3 = proj.add_workflow(wf3)
    
    print(f"✅ 添加工作流 1 (索引: {idx1})")
    print(f"✅ 添加工作流 2 (索引: {idx2})")
    print(f"✅ 添加工作流 3 (索引: {idx3})")
    print(f"   工程包含 {len(proj.workflows)} 个工作流")
    
    # 获取工作流
    wf = proj.get_workflow(1)
    print(f"\n✅ 获取索引1的工作流: {wf.name}")
    
    # 设置激活工作流
    proj.set_active_workflow(2)
    active_wf = proj.get_active_workflow()
    print(f"✅ 激活工作流: {active_wf.name} (索引: {proj.active_workflow_index})")
    
    # 移除工作流
    proj.remove_workflow(0)
    print(f"\n✅ 移除索引0的工作流")
    print(f"   工程包含 {len(proj.workflows)} 个工作流")
    print(f"   当前激活索引: {proj.active_workflow_index}")
    
    # 序列化/反序列化
    data = proj.to_dict()
    print(f"\n✅ 工程序列化:")
    print(f"   版本: {data['version']}")
    print(f"   名称: {data['name']}")
    print(f"   工作流数量: {len(data['workflows'])}")
    
    proj2 = Project.from_dict(data)
    print(f"\n✅ 从字典恢复: {proj2}")
    assert len(proj2.workflows) == len(proj.workflows)
    print("✅ 序列化/反序列化测试通过")
    
    print("\n" + "=" * 60 + "\n")


def test_project_manager():
    """测试ProjectManager单例"""
    print("=" * 60)
    print("测试3: ProjectManager单例")
    print("=" * 60)
    
    # 获取单例实例
    pm1 = ProjectManager()
    pm2 = ProjectManager()
    print(f"✅ 单例测试: pm1 is pm2 = {pm1 is pm2}")
    assert pm1 is pm2
    
    # 使用全局实例
    pm = project_manager
    print(f"✅ 全局实例: {pm}")
    
    # 创建新工程
    project = pm.create_project("测试工程")
    print(f"✅ 创建工程: {project}")
    print(f"   工作流数量: {len(project.workflows)}")
    print(f"   默认工作流: {project.workflows[0].name}")
    
    # 添加工作流
    wf = pm.add_new_workflow("新增工作流")
    print(f"\n✅ 添加工作流: {wf}")
    print(f"   工程工作流总数: {len(pm.current_project.workflows)}")
    
    # 检查未保存修改
    has_changes = pm.has_unsaved_changes()
    print(f"\n✅ 有未保存修改: {has_changes}")
    
    # 移除工作流
    pm.remove_workflow(0)
    print(f"✅ 移除工作流后总数: {len(pm.current_project.workflows)}")
    
    # 关闭工程
    pm.close_project()
    print(f"✅ 关闭工程后: {pm}")
    assert pm.current_project is None
    
    print("\n" + "=" * 60 + "\n")


def test_project_persistence():
    """测试工程持久化（保存/加载）"""
    print("=" * 60)
    print("测试4: 工程持久化")
    print("=" * 60)
    
    import tempfile
    import shutil
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="test_project_")
    print(f"✅ 创建临时目录: {temp_dir}")
    
    try:
        pm = project_manager
        
        # 创建工程
        project = pm.create_project("持久化测试工程")
        
        # 添加多个工作流
        pm.add_new_workflow("工作流 A")
        pm.add_new_workflow("工作流 B")
        
        print(f"✅ 工程包含 {len(project.workflows)} 个工作流")
        
        # 保存工程
        success = pm.save_project(temp_dir)
        print(f"✅ 保存工程: {'成功' if success else '失败'}")
        
        # 检查文件结构
        project_file = os.path.join(temp_dir, "project.json")
        workflows_dir = os.path.join(temp_dir, "workflows")
        
        print(f"\n✅ 文件结构:")
        print(f"   工程配置文件: {os.path.exists(project_file)}")
        print(f"   工作流目录: {os.path.exists(workflows_dir)}")
        
        if os.path.exists(workflows_dir):
            wf_files = os.listdir(workflows_dir)
            print(f"   工作流文件: {wf_files}")
        
        # 读取并显示工程配置
        if os.path.exists(project_file):
            with open(project_file, 'r', encoding='utf-8') as f:
                import json
                data = json.load(f)
                print(f"\n✅ 工程配置内容:")
                print(f"   名称: {data['name']}")
                print(f"   版本: {data['version']}")
                print(f"   工作流数量: {len(data['workflows'])}")
                for i, wf in enumerate(data['workflows']):
                    print(f"     [{i}] {wf['name']} ({wf['id']})")
        
        # 关闭工程
        pm.close_project()
        
        # 重新打开工程
        loaded_project = pm.open_project(temp_dir)
        print(f"\n✅ 重新打开工程: {loaded_project}")
        print(f"   工作流数量: {len(loaded_project.workflows)}")
        for i, wf in enumerate(loaded_project.workflows):
            print(f"     [{i}] {wf.name} (ID: {wf.id})")
        
        print("\n✅ 持久化测试通过")
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)
        print(f"\n🗑️ 清理临时目录: {temp_dir}")
    
    print("\n" + "=" * 60 + "\n")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("工程和工流管理模块测试")
    print("=" * 60 + "\n")
    
    try:
        test_workflow()
        test_project()
        test_project_manager()
        test_project_persistence()
        
        print("\n" + "=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)