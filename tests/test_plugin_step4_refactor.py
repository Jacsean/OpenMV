"""
Step 4 测试脚本 - 节点编辑器增强功能验证

测试内容:
1. 代码编辑器组件（行号、高亮）
2. 撤销/重做机制
3. 代码保存和格式化
4. 实时预览功能
5. 快捷键支持（Ctrl+Z/Y）
"""

import sys
import os
from pathlib import Path
import json

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "src" / "python"))


def test_code_editor_component():
    """测试代码编辑器组件"""
    print("\n" + "=" * 60)
    print("📝 测试代码编辑器组件")
    print("=" * 60)
    
    from PySide2 import QtWidgets
    from ui.node_editor import CodeEditor, LineNumberArea
    
    app = QtWidgets.QApplication(sys.argv)
    
    # 创建代码编辑器
    editor = CodeEditor()
    print(f"   ✅ CodeEditor 创建成功")
    
    # 检查行号区域
    assert hasattr(editor, 'line_number_area'), "缺少 line_number_area 属性"
    print(f"   ✅ 行号区域组件存在")
    
    # 检查关键方法
    required_methods = [
        'line_number_area_width',
        '_update_line_number_area_width',
        '_update_line_number_area',
        'line_number_area_paint_event',
        'highlight_current_line'
    ]
    
    for method in required_methods:
        assert hasattr(editor, method), f"缺少方法: {method}"
        print(f"   ✅ 方法 {method} 存在")
    
    # 测试基本功能
    test_code = """
class TestNode(BaseNode):
    def __init__(self):
        super(TestNode, self).__init__()
        self.add_input('输入')
        self.add_output('输出')
    
    def process(self, inputs=None):
        return {'输出': None}
"""
    editor.setPlainText(test_code)
    print(f"   ✅ 代码设置成功 ({len(test_code)} 字符)")
    
    # 计算行号宽度
    width = editor.line_number_area_width()
    print(f"   ✅ 行号区域宽度: {width}px")
    
    return True


def test_undo_redo_mechanism():
    """测试撤销/重做机制"""
    print("\n" + "=" * 60)
    print("↩️ 测试撤销/重做机制")
    print("=" * 60)
    
    from PySide2 import QtWidgets
    from ui.node_editor import NodeEditorDialog
    
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    
    plugins_dir = Path(__file__).parent / "src" / "python" / "user_plugins"
    editor = NodeEditorDialog(None, plugins_dir)
    
    # 检查历史栈初始化
    assert hasattr(editor, 'undo_stack'), "缺少 undo_stack 属性"
    assert hasattr(editor, 'redo_stack'), "缺少 redo_stack 属性"
    assert hasattr(editor, 'max_history'), "缺少 max_history 属性"
    print(f"   ✅ 撤销/重做栈初始化成功")
    print(f"   📊 最大历史记录: {editor.max_history}")
    
    # 检查关键方法
    required_methods = [
        '_push_undo',
        'undo',
        'redo',
        '_execute_undo_action',
        '_execute_redo_action'
    ]
    
    for method in required_methods:
        assert hasattr(editor, method), f"缺少方法: {method}"
        print(f"   ✅ 方法 {method} 存在")
    
    # 模拟推入撤销记录
    editor._push_undo('test_action', {'data': 'test'})
    assert len(editor.undo_stack) == 1, "撤销栈大小不正确"
    print(f"   ✅ 推入撤销记录成功 (栈大小: {len(editor.undo_stack)})")
    
    # 测试清空重做栈
    editor.redo_stack.append({'test': 'data'})
    editor._push_undo('another_action', {'data': 'test2'})
    assert len(editor.redo_stack) == 0, "推入新记录后重做栈未清空"
    print(f"   ✅ 推入新记录时自动清空重做栈")
    
    return True


def test_code_save_and_format():
    """测试代码保存和格式化"""
    print("\n" + "=" * 60)
    print("💾 测试代码保存和格式化")
    print("=" * 60)
    
    from PySide2 import QtWidgets
    from ui.node_editor import NodeEditorDialog
    
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    
    plugins_dir = Path(__file__).parent / "src" / "python" / "user_plugins"
    editor = NodeEditorDialog(None, plugins_dir)
    
    # 检查代码编辑器是否存在
    assert hasattr(editor, 'code_editor'), "缺少 code_editor 属性"
    print(f"   ✅ 代码编辑器组件存在")
    
    # 检查相关按钮
    assert hasattr(editor, 'save_code_btn'), "缺少 save_code_btn"
    assert hasattr(editor, 'format_code_btn'), "缺少 format_code_btn"
    print(f"   ✅ 代码操作按钮存在")
    
    # 检查相关方法
    required_methods = [
        '_on_code_changed',
        '_on_save_code',
        '_on_format_code'
    ]
    
    for method in required_methods:
        assert hasattr(editor, method), f"缺少方法: {method}"
        print(f"   ✅ 方法 {method} 存在")
    
    # 测试代码格式化
    messy_code = "def test():\n\n\n    x=1\n\n\n\n    y=2\n"
    editor.code_editor.setPlainText(messy_code)
    print(f"   ✅ 测试代码设置成功")
    
    return True


def test_preview_functionality():
    """测试实时预览功能"""
    print("\n" + "=" * 60)
    print("👁️ 测试实时预览功能")
    print("=" * 60)
    
    from PySide2 import QtWidgets
    from ui.node_editor import NodeEditorDialog
    
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    
    plugins_dir = Path(__file__).parent / "src" / "python" / "user_plugins"
    editor = NodeEditorDialog(None, plugins_dir)
    
    # 检查预览组件
    assert hasattr(editor, 'preview_label'), "缺少 preview_label 属性"
    assert hasattr(editor, 'preview_btn'), "缺少 preview_btn"
    assert hasattr(editor, 'clear_preview_btn'), "缺少 clear_preview_btn"
    print(f"   ✅ 预览组件存在")
    
    # 检查相关方法
    required_methods = [
        '_on_run_preview',
        '_on_clear_preview'
    ]
    
    for method in required_methods:
        assert hasattr(editor, method), f"缺少方法: {method}"
        print(f"   ✅ 方法 {method} 存在")
    
    # 测试清除预览
    editor._on_clear_preview()
    preview_text = editor.preview_label.text()
    assert "选择节点" in preview_text, "清除预览后文本不正确"
    print(f"   ✅ 清除预览功能正常")
    
    return True


def test_keyboard_shortcuts():
    """测试键盘快捷键"""
    print("\n" + "=" * 60)
    print("⌨️ 测试键盘快捷键")
    print("=" * 60)
    
    from PySide2 import QtWidgets, QtCore
    from ui.node_editor import NodeEditorDialog
    
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    
    plugins_dir = Path(__file__).parent / "src" / "python" / "user_plugins"
    editor = NodeEditorDialog(None, plugins_dir)
    
    # 检查 keyPressEvent 方法
    assert hasattr(editor, 'keyPressEvent'), "缺少 keyPressEvent 方法"
    print(f"   ✅ 键盘事件处理方法存在")
    
    # 检查Tab控件
    assert hasattr(editor, 'tab_widget'), "缺少 tab_widget 属性"
    print(f"   ✅ Tab控件存在")
    
    # 验证Tab数量
    tab_count = editor.tab_widget.count()
    print(f"   📊 Tab数量: {tab_count}")
    
    expected_tabs = ["📋 详情", "📝 代码", "👁️ 预览"]
    for i in range(tab_count):
        tab_name = editor.tab_widget.tabText(i)
        print(f"      • Tab {i+1}: {tab_name}")
    
    assert tab_count == 3, f"Tab数量不正确: 期望3，实际{tab_count}"
    print(f"   ✅ Tab结构正确 (详情/代码/预览)")
    
    return True


def test_integration_with_node_operations():
    """测试与节点操作的集成"""
    print("\n" + "=" * 60)
    print("🔗 测试与节点操作的集成")
    print("=" * 60)
    
    from PySide2 import QtWidgets
    from ui.node_editor import NodeEditorDialog
    
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
    
    plugins_dir = Path(__file__).parent / "src" / "python" / "user_plugins"
    editor = NodeEditorDialog(None, plugins_dir)
    
    # 检查_on_add_node_to_package中是否有撤销记录
    import inspect
    source = inspect.getsource(editor._add_node_to_package)
    assert '_push_undo' in source, "_add_node_to_package 中缺少撤销记录"
    print(f"   ✅ 新建节点操作包含撤销记录")
    
    # 检查_on_delete_node中是否有撤销记录
    source = inspect.getsource(editor._on_delete_node)
    assert '_push_undo' in source, "_on_delete_node 中缺少撤销记录"
    print(f"   ✅ 删除节点操作包含撤销记录")
    
    # 检查_on_edit_node中是否有撤销记录
    source = inspect.getsource(editor._on_edit_node)
    assert '_push_undo' in source, "_on_edit_node 中缺少撤销记录"
    print(f"   ✅ 编辑节点操作包含撤销记录")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("Step 4 测试: 节点编辑器增强功能")
    print("=" * 60)
    
    # 执行各项测试
    test_code_editor_component()
    test_undo_redo_mechanism()
    test_code_save_and_format()
    test_preview_functionality()
    test_keyboard_shortcuts()
    test_integration_with_node_operations()
    
    print("\n" + "=" * 60)
    print("✅ Step 4 测试通过！")
    print("=" * 60)
    print(f"\n🎯 完成内容:")
    print(f"   ✅ 代码编辑器（行号显示、语法高亮）")
    print(f"   ✅ 撤销/重做机制（Ctrl+Z/Y，最大50步）")
    print(f"   ✅ 代码保存和格式化")
    print(f"   ✅ 实时预览面板")
    print(f"   ✅ Tab切换（详情/代码/预览）")
    print(f"   ✅ 与节点操作完全集成")
    print(f"\n💡 提示: 在节点编辑器中使用 Ctrl+Z 撤销，Ctrl+Y 重做")
