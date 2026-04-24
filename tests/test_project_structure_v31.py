   """
工程文件结构v3.1功能演示

展示新的工程结构特性：
1. 增强的元数据（标签、描述等）
2. 全文索引生成
3. 工程搜索
4. ZIP打包和导入
"""
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

def demo_project_structure():
    """演示工程文件结构功能"""
    print("=" * 70)
    print("工程文件结构 v3.1 功能演示")
    print("=" * 70)
    
    from PySide2 import QtWidgets
    app = QtWidgets.QApplication(sys.argv)
    
    from core.project_manager import Project, Workflow, ProjectIndexer, project_manager
    
    # === 1. 创建带有增强元数据的工程 ===
    print("\n📝 步骤1: 创建带有增强元数据的工程")
    print("-" * 70)
    
    project = Project(name="工件外观检测系统")
    project.description = "用于生产线工件外观缺陷检测的视觉系统，支持多种算法"
    project.author = "张三"
    project.tags = ["检测", "外观", "Canny", "工业视觉", "质量控制"]
    project.category = "质量检测"
    
    print(f"✅ 工程名称: {project.name}")
    print(f"✅ 描述: {project.description}")
    print(f"✅ 作者: {project.author}")
    print(f"✅ 标签: {', '.join(project.tags)}")
    print(f"✅ 分类: {project.category}")
    
    # === 2. 添加工作流 ===
    print("\n📊 步骤2: 添加工作流")
    print("-" * 70)
    
    wf1 = Workflow(name="边缘检测流程")
    wf1.description = "使用Canny算法进行边缘提取"
    wf1.node_count = 15
    project.add_workflow(wf1)
    print(f"✅ 添加工作流1: {wf1.name} ({wf1.node_count}个节点)")
    
    wf2 = Workflow(name="缺陷识别流程")
    wf2.description = "基于形态学的缺陷检测"
    wf2.node_count = 20
    project.add_workflow(wf2)
    print(f"✅ 添加工作流2: {wf2.name} ({wf2.node_count}个节点)")
    
    wf3 = Workflow(name="尺寸测量流程")
    wf3.description = "精确测量工件尺寸"
    wf3.node_count = 18
    project.add_workflow(wf3)
    print(f"✅ 添加工作流3: {wf3.name} ({wf3.node_count}个节点)")
    
    # === 3. 生成工程元数据 ===
    print("\n💾 步骤3: 生成工程元数据（project.json内容预览）")
    print("-" * 70)
    
    project_data = project.to_dict()
    print(f"版本: {project_data['version']}")
    print(f"格式: {project_data['format']}")
    print(f"统计信息:")
    print(f"  - 工作流数量: {project_data['stats']['workflow_count']}")
    print(f"  - 节点总数: {project_data['stats']['node_count']}")
    print(f"  - 资源数量: {project_data['stats']['asset_count']}")
    
    # === 4. 生成全文索引 ===
    print("\n🔍 步骤4: 生成全文索引（index.json内容预览）")
    print("-" * 70)
    
    index_data = ProjectIndexer.generate_index(project)
    print(f"索引生成时间: {index_data['indexed_at']}")
    print(f"\n可搜索文本:")
    for key, value in index_data['searchable_text'].items():
        if value:
            print(f"  {key}: {value[:50]}..." if len(value) > 50 else f"  {key}: {value}")
    
    print(f"\n关键词索引示例:")
    for keyword, targets in list(index_data['keywords'].items())[:5]:
        print(f"  '{keyword}' -> {targets}")
    
    # === 5. 演示搜索功能 ===
    print("\n🎯 步骤5: 演示搜索功能")
    print("-" * 70)
    
    # 模拟多个工程目录
    test_projects = [
        {"path": "/projects/project_A", "data": {
            "name": "零件尺寸检测",
            "description": "高精度尺寸测量",
            "tags": ["检测", "尺寸", "测量"],
            "category": "尺寸检测"
        }},
        {"path": "/projects/project_B", "data": {
            "name": "表面缺陷检测",
            "description": "Canny边缘检测结合形态学处理",
            "tags": ["检测", "缺陷", "Canny"],
            "category": "质量检测"
        }},
        {"path": "/projects/project_C", "data": {
            "name": "颜色分选系统",
            "description": "基于HSV颜色空间的分选",
            "tags": ["颜色", "分选"],
            "category": "分选"
        }}
    ]
    
    # 模拟搜索
    search_keywords = "Canny 检测"
    print(f"搜索关键词: '{search_keywords}'\n")
    
    results = []
    for proj_info in test_projects:
        score = ProjectIndexer._calculate_relevance(proj_info['data'], search_keywords.lower().split())
        if score > 0:
            results.append({
                "path": proj_info['path'],
                "name": proj_info['data']['name'],
                "score": score
            })
    
    results.sort(key=lambda x: x['score'], reverse=True)
    
    if results:
        print("搜索结果（按相关度排序）:")
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['name']} (相关度: {result['score']:.1f})")
            print(f"     路径: {result['path']}")
    else:
        print("未找到匹配的工程")
    
    # === 6. 工程打包说明 ===
    print("\n📦 步骤6: 工程打包功能说明")
    print("-" * 70)
    print("导出为单文件（ZIP格式）:")
    print("  project_manager.export_project('my_project.proj')")
    print("\n从单文件导入:")
    print("  project = project_manager.import_project('my_project.proj')")
    print("\n优势:")
    print("  ✅ 单一文件，便于拷贝和分享")
    print("  ✅ ZIP压缩，减小文件大小")
    print("  ✅ 可用标准ZIP工具解压查看")
    print("  ✅ 支持加密和数字签名（未来扩展）")
    
    # === 7. 文件结构对比 ===
    print("\n📁 步骤7: 新旧文件结构对比")
    print("-" * 70)
    print("旧版 (v3.0):")
    print("  my_project.proj/")
    print("  ├── project.json          # 基本元数据")
    print("  └── workflows/")
    print("      └── workflow_1.json")
    print("\n新版 (v3.1):")
    print("  my_project.proj/ 或 my_project.proj (ZIP)")
    print("  ├── project.json          # ⭐ 增强元数据（标签、描述等）")
    print("  ├── thumbnail.png         # ⭐ 缩略图")
    print("  ├── index.json            # ⭐ 全文索引")
    print("  ├── workflows/")
    print("  │   └── workflow_1.json")
    print("  ├── assets/")
    print("  │   └── references.json   # ⭐ 资源引用表")
    print("  └── cache/")
    print("      └── previews/")
    
    print("\n" + "=" * 70)
    print("✅ 演示完成！")
    print("=" * 70)

if __name__ == '__main__':
    demo_project_structure()
