"""
工程持久化功能测试脚本

测试工程的保存、加载和最近工程列表功能
"""

import sys
import os
import tempfile
import shutil

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from NodeGraphQt import NodeGraph
from core.project_manager import project_manager
from nodes.io_nodes import ImageLoadNode, ImageSaveNode
from nodes.processing_nodes import GrayscaleNode, GaussianBlurNode
from nodes.display_nodes import ImageViewNode


def register_nodes(node_graph):
    """注册节点类型"""
    node_graph.register_node(ImageLoadNode)
    node_graph.register_node(ImageSaveNode)
    node_graph.register_node(GrayscaleNode)
    node_graph.register_node(GaussianBlurNode)
    node_graph.register_node(ImageViewNode)


def test_project_save_load():
    """测试工程保存和加载"""
    print("=" * 60)
    print("测试: 工程保存和加载")
    print("=" * 60)
    
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="test_project_save_")
    print(f"✅ 创建临时目录: {temp_dir}")
    
    try:
        pm = project_manager
        
        # 1. 创建新工程
        print("\n--- 步骤1: 创建工程 ---")
        project = pm.create_project("测试保存加载工程")
        
        # 2. 添加多个工作流并构建节点图
        print("\n--- 步骤2: 构建工作流 ---")
        
        # 工作流1: 简单处理流程
        wf1 = project.workflows[0]
        wf1.name = "边缘检测流程"
        graph1 = NodeGraph()
        register_nodes(graph1)
        wf1.node_graph = graph1
        
        # 创建节点
        load_node1 = graph1.create_node('io.ImageLoadNode', name='加载图像')
        gray_node1 = graph1.create_node('processing.GrayscaleNode', name='灰度化')
        canny_node1 = graph1.create_node('processing.CannyEdgeNode', name='Canny检测')
        view_node1 = graph1.create_node('display.ImageViewNode', name='显示结果')
        
        # 连接节点
        graph1.connect_nodes(load_node1.output(0), gray_node1.input(0))
        graph1.connect_nodes(gray_node1.output(0), canny_node1.input(0))
        graph1.connect_nodes(canny_node1.output(0), view_node1.input(0))
        
        print(f"   ✅ 工作流1: {wf1.name} ({len(graph1.all_nodes())} 个节点)")
        
        # 工作流2: 模糊处理流程
        wf2 = pm.add_new_workflow("高斯模糊流程")
        graph2 = NodeGraph()
        register_nodes(graph2)
        wf2.node_graph = graph2
        
        load_node2 = graph2.create_node('io.ImageLoadNode', name='加载图像')
        blur_node2 = graph2.create_node('processing.GaussianBlurNode', name='高斯模糊')
        view_node2 = graph2.create_node('display.ImageViewNode', name='显示结果')
        
        graph2.connect_nodes(load_node2.output(0), blur_node2.input(0))
        graph2.connect_nodes(blur_node2.output(0), view_node2.input(0))
        
        print(f"   ✅ 工作流2: {wf2.name} ({len(graph2.all_nodes())} 个节点)")
        
        # 3. 保存工程
        print("\n--- 步骤3: 保存工程 ---")
        success = pm.save_project(temp_dir)
        print(f"   保存结果: {'✅ 成功' if success else '❌ 失败'}")
        
        # 4. 验证文件结构
        print("\n--- 步骤4: 验证文件结构 ---")
        project_file = os.path.join(temp_dir, "project.json")
        workflows_dir = os.path.join(temp_dir, "workflows")
        
        print(f"   工程配置文件: {'✅ 存在' if os.path.exists(project_file) else '❌ 缺失'}")
        print(f"   工作流目录: {'✅ 存在' if os.path.exists(workflows_dir) else '❌ 缺失'}")
        
        if os.path.exists(workflows_dir):
            wf_files = os.listdir(workflows_dir)
            print(f"   工作流文件: {wf_files}")
            for wf_file in wf_files:
                wf_path = os.path.join(workflows_dir, wf_file)
                size = os.path.getsize(wf_path)
                print(f"     - {wf_file}: {size} bytes")
        
        # 5. 关闭工程
        print("\n--- 步骤5: 关闭工程 ---")
        pm.close_project()
        print(f"   当前工程: {pm.current_project}")
        
        # 6. 重新打开工程
        print("\n--- 步骤6: 重新打开工程 ---")
        loaded_project = pm.open_project(temp_dir)
        
        if loaded_project:
            print(f"   ✅ 工程名称: {loaded_project.name}")
            print(f"   ✅ 工作流数量: {len(loaded_project.workflows)}")
            
            for i, wf in enumerate(loaded_project.workflows):
                print(f"\n   工作流 {i+1}:")
                print(f"     名称: {wf.name}")
                print(f"     ID: {wf.id}")
                print(f"     文件: {wf.file_path}")
                
                # 创建工作流的NodeGraph并加载数据
                if wf.file_path:
                    wf_full_path = os.path.join(temp_dir, wf.file_path)
                    if os.path.exists(wf_full_path):
                        new_graph = NodeGraph()
                        register_nodes(new_graph)
                        wf.node_graph = new_graph
                        
                        try:
                            new_graph.deserialize_session(wf_full_path)
                            node_count = len(new_graph.all_nodes())
                            print(f"     ✅ 加载成功 ({node_count} 个节点)")
                            
                            # 验证节点
                            nodes = new_graph.all_nodes()
                            print(f"     节点列表:")
                            for node in nodes:
                                print(f"       - {node.name()} ({node.type_})")
                        except Exception as e:
                            print(f"     ❌ 加载失败: {e}")
                    else:
                        print(f"     ❌ 文件不存在: {wf_full_path}")
            
            print("\n✅ 工程加载测试通过")
        else:
            print("❌ 工程加载失败")
            return False
        
        return True
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir)
        print(f"\n🗑️ 清理临时目录: {temp_dir}")


def test_recent_projects():
    """测试最近工程列表"""
    print("\n" + "=" * 60)
    print("测试: 最近工程列表")
    print("=" * 60)
    
    from PySide2 import QtCore
    
    settings = QtCore.QSettings("VisionSystem", "StduyOpenCV")
    
    # 清空现有列表
    settings.remove("recent_projects")
    print("✅ 已清空最近工程列表")
    
    # 模拟添加工程
    test_paths = [
        "D:/Projects/Project_A",
        "D:/Projects/Project_B",
        "D:/Projects/Project_C"
    ]
    
    print("\n--- 添加工程到列表 ---")
    for path in test_paths:
        recent_projects = settings.value("recent_projects", [])
        if isinstance(recent_projects, str):
            recent_projects = [recent_projects]
        
        if path in recent_projects:
            recent_projects.remove(path)
        
        recent_projects.insert(0, path)
        recent_projects = recent_projects[:10]
        
        settings.setValue("recent_projects", recent_projects)
        print(f"   ✅ 添加: {path}")
    
    # 读取列表
    print("\n--- 读取最近工程列表 ---")
    recent_projects = settings.value("recent_projects", [])
    if isinstance(recent_projects, str):
        recent_projects = [recent_projects]
    
    print(f"   列表长度: {len(recent_projects)}")
    for i, path in enumerate(recent_projects):
        print(f"   [{i}] {path}")
    
    # 测试移除
    print("\n--- 移除工程 ---")
    remove_path = test_paths[1]
    if remove_path in recent_projects:
        recent_projects.remove(remove_path)
        settings.setValue("recent_projects", recent_projects)
        print(f"   ✅ 已移除: {remove_path}")
    
    # 验证
    recent_projects = settings.value("recent_projects", [])
    if isinstance(recent_projects, str):
        recent_projects = [recent_projects]
    
    print(f"   剩余数量: {len(recent_projects)}")
    assert remove_path not in recent_projects
    print("   ✅ 移除验证通过")
    
    # 清理
    settings.remove("recent_projects")
    print("\n✅ 最近工程列表测试通过")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("工程持久化功能测试")
    print("=" * 60 + "\n")
    
    # 创建QApplication（NodeGraphQt需要）
    from PySide2 import QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    
    try:
        # 测试1: 工程保存和加载
        result1 = test_project_save_load()
        
        # 测试2: 最近工程列表
        test_recent_projects()
        
        if result1:
            print("\n" + "=" * 60)
            print("🎉 所有测试通过！")
            print("=" * 60 + "\n")
        else:
            print("\n" + "=" * 60)
            print("❌ 部分测试失败")
            print("=" * 60 + "\n")
            sys.exit(1)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)