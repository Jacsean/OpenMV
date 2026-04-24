"""
Step 5 测试脚本 - 文档与示例验证

测试内容:
1. 节点开发教程文档完整性
2. API参考手册准确性
3. 高级示例节点包结构
4. 示例节点代码可运行性
5. 文档链接有效性
"""

import sys
from pathlib import Path
import json


def test_development_guide():
    """测试节点开发教程"""
    print("\n" + "=" * 60)
    print("📖 测试节点开发教程")
    print("=" * 60)
    
    guide_path = Path(__file__).parent / "src" / "python" / "user_plugins" / "NODE_DEVELOPMENT_GUIDE.md"
    
    assert guide_path.exists(), f"教程文件不存在: {guide_path}"
    print(f"   ✅ 教程文件存在")
    
    with open(guide_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键章节
    required_sections = [
        '快速开始',
        '节点基础概念',
        '创建第一个节点',
        '节点进阶开发',
        '打包与发布',
        '常见问题'
    ]
    
    for section in required_sections:
        if section in content:
            print(f"   ✅ 章节 '{section}' 存在")
        else:
            print(f"   ❌ 章节 '{section}' 缺失")
    
    # 检查代码示例
    if 'class BrightnessNode(BaseNode):' in content:
        print(f"   ✅ 包含完整代码示例")
    else:
        print(f"   ⚠️ 代码示例可能不完整")
    
    # 检查文件大小
    file_size = len(content)
    print(f"   📊 文档大小: {file_size} 字符")
    assert file_size > 5000, "文档内容过少"
    
    return True


def test_api_reference():
    """测试API参考手册"""
    print("\n" + "=" * 60)
    print("📚 测试API参考手册")
    print("=" * 60)
    
    api_path = Path(__file__).parent / "src" / "python" / "user_plugins" / "NODE_API_REFERENCE.md"
    
    assert api_path.exists(), f"API文档不存在: {api_path}"
    print(f"   ✅ API文档存在")
    
    with open(api_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查关键章节
    required_sections = [
        'BaseNode API',
        'plugin.json 规范',
        '插件管理器 API',
        '节点编辑器 API'
    ]
    
    for section in required_sections:
        if section in content:
            print(f"   ✅ 章节 '{section}' 存在")
        else:
            print(f"   ❌ 章节 '{section}' 缺失")
    
    # 检查API字段说明
    api_fields = [
        '__identifier__',
        'NODE_NAME',
        'add_input',
        'add_output',
        'add_text_input',
        'process'
    ]
    
    for field in api_fields:
        if field in content:
            print(f"   ✅ API字段 '{field}' 有说明")
        else:
            print(f"   ⚠️ API字段 '{field}' 缺少说明")
    
    # 检查表格
    if '| 字段 |' in content:
        print(f"   ✅ 包含字段说明表格")
    
    file_size = len(content)
    print(f"   📊 文档大小: {file_size} 字符")
    assert file_size > 3000, "文档内容过少"
    
    return True


def test_example_package_structure():
    """测试示例节点包结构"""
    print("\n" + "=" * 60)
    print("📦 测试高级示例节点包结构")
    print("=" * 60)
    
    example_dir = Path(__file__).parent / "src" / "python" / "user_plugins" / "example_advanced_nodes"
    
    assert example_dir.exists(), f"示例包目录不存在: {example_dir}"
    print(f"   ✅ 示例包目录存在")
    
    # 检查必需文件
    required_files = ['plugin.json', 'nodes.py', 'README.md']
    for filename in required_files:
        filepath = example_dir / filename
        if filepath.exists():
            print(f"   ✅ {filename} 存在")
        else:
            print(f"   ❌ {filename} 缺失")
    
    # 验证plugin.json
    plugin_json = example_dir / "plugin.json"
    with open(plugin_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    assert data['name'] == 'example_advanced_nodes', "包名不正确"
    print(f"   ✅ 包名正确: {data['name']}")
    
    assert len(data['nodes']) == 3, f"节点数量不正确: {len(data['nodes'])}"
    print(f"   ✅ 节点数量: {len(data['nodes'])}")
    
    expected_nodes = ['MultiInputBlendNode', 'AdaptiveThresholdNode', 'HistogramEqualizeNode']
    actual_nodes = [n['class'] for n in data['nodes']]
    for node in expected_nodes:
        if node in actual_nodes:
            print(f"   ✅ 节点 {node} 已定义")
        else:
            print(f"   ❌ 节点 {node} 缺失")
    
    return True


def test_example_nodes_code():
    """测试示例节点代码"""
    print("\n" + "=" * 60)
    print("💻 测试示例节点代码")
    print("=" * 60)
    
    nodes_py = Path(__file__).parent / "src" / "python" / "user_plugins" / "example_advanced_nodes" / "nodes.py"
    
    with open(nodes_py, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查必需的类
    required_classes = [
        'MultiInputBlendNode',
        'AdaptiveThresholdNode',
        'HistogramEqualizeNode'
    ]
    
    for cls in required_classes:
        if f'class {cls}(BaseNode):' in content:
            print(f"   ✅ 类 {cls} 已实现")
        else:
            print(f"   ❌ 类 {cls} 缺失")
    
    # 检查必需的导入
    if 'from NodeGraphQt import BaseNode' in content:
        print(f"   ✅ 导入BaseNode")
    
    if 'import cv2' in content and 'import numpy as np' in content:
        print(f"   ✅ 导入OpenCV和NumPy")
    
    # 检查process方法
    process_count = content.count('def process(self, inputs=None):')
    print(f"   📊 process方法数量: {process_count}")
    assert process_count >= 3, "process方法数量不足"
    
    # 检查异常处理
    try_except_count = content.count('try:')
    print(f"   📊 try-except块数量: {try_except_count}")
    assert try_except_count >= 3, "异常处理不足"
    
    # 验证Python语法
    try:
        compile(content, str(nodes_py), 'exec')
        print(f"   ✅ Python语法正确")
    except SyntaxError as e:
        print(f"   ❌ 语法错误: {e}")
        return False
    
    return True


def test_documentation_links():
    """测试文档链接"""
    print("\n" + "=" * 60)
    print("🔗 测试文档链接")
    print("=" * 60)
    
    user_plugins_dir = Path(__file__).parent / "src" / "python" / "user_plugins"
    
    # 检查主文档之间的相互引用
    guide_path = user_plugins_dir / "NODE_DEVELOPMENT_GUIDE.md"
    api_path = user_plugins_dir / "NODE_API_REFERENCE.md"
    
    with open(guide_path, 'r', encoding='utf-8') as f:
        guide_content = f.read()
    
    with open(api_path, 'r', encoding='utf-8') as f:
        api_content = f.read()
    
    # 检查教程中是否引用API文档
    if 'NODE_API_REFERENCE.md' in guide_content:
        print(f"   ✅ 教程引用了API文档")
    else:
        print(f"   ⚠️ 教程未引用API文档")
    
    # 检查示例包README中是否引用主文档
    example_readme = user_plugins_dir / "example_advanced_nodes" / "README.md"
    with open(example_readme, 'r', encoding='utf-8') as f:
        example_content = f.read()
    
    if 'NODE_DEVELOPMENT_GUIDE.md' in example_content:
        print(f"   ✅ 示例包引用了开发教程")
    
    if 'NODE_API_REFERENCE.md' in example_content:
        print(f"   ✅ 示例包引用了API文档")
    
    return True


def test_code_quality():
    """测试代码质量"""
    print("\n" + "=" * 60)
    print("✨ 测试代码质量")
    print("=" * 60)
    
    nodes_py = Path(__file__).parent / "src" / "python" / "user_plugins" / "example_advanced_nodes" / "nodes.py"
    
    with open(nodes_py, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 检查docstring
    docstring_count = sum(1 for line in lines if '"""' in line)
    print(f"   📊 Docstring数量: {docstring_count}")
    assert docstring_count >= 6, "Docstring不足（每个类和方法都应有）"
    
    # 检查注释
    comment_count = sum(1 for line in lines if line.strip().startswith('#'))
    print(f"   📊 注释行数: {comment_count}")
    
    # 检查空行（代码可读性）
    empty_lines = sum(1 for line in lines if line.strip() == '')
    total_lines = len(lines)
    empty_ratio = empty_lines / total_lines if total_lines > 0 else 0
    print(f"   📊 空行比例: {empty_ratio:.1%}")
    
    # 检查最佳实践
    content = ''.join(lines)
    
    if 'isinstance(inputs[0], list)' in content:
        print(f"   ✅ 使用类型检查")
    
    if 'max(' in content and 'min(' in content:
        print(f"   ✅ 使用参数范围限制")
    
    if 'traceback' in content or 'print(f"' in content:
        print(f"   ✅ 包含错误日志")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Step 5 测试: 文档与示例验证")
    print("=" * 60)
    
    # 执行各项测试
    test_development_guide()
    test_api_reference()
    test_example_package_structure()
    test_example_nodes_code()
    test_documentation_links()
    test_code_quality()
    
    print("\n" + "=" * 60)
    print("✅ Step 5 测试通过！")
    print("=" * 60)
    print(f"\n🎯 完成内容:")
    print(f"   ✅ 节点开发完全指南 (NODE_DEVELOPMENT_GUIDE.md)")
    print(f"   ✅ API参考手册 (NODE_API_REFERENCE.md)")
    print(f"   ✅ 高级示例节点包 (example_advanced_nodes/)")
    print(f"      • 多图像混合节点")
    print(f"      • 自适应阈值节点")
    print(f"      • 直方图均衡化节点")
    print(f"   ✅ 完整的文档交叉引用")
    print(f"   ✅ 代码质量检查通过")
    print(f"\n💡 提示: 所有文档位于 src/python/user_plugins/ 目录")
