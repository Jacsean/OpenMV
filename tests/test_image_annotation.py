"""
测试图像标注功能 - 单元测试部分

验证：
1. 标注数据模型（Annotation）
2. 标注层管理器（AnnotationLayer）
"""

import sys
import os

# 添加项目根目录到Python路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 直接导入，避免触发__init__.py
import importlib.util
spec = importlib.util.spec_from_file_location(
    "image_annotation",
    os.path.join(project_root, "src", "python", "ui", "image_annotation.py")
)
image_annotation = importlib.util.module_from_spec(spec)
spec.loader.exec_module(image_annotation)

Annotation = image_annotation.Annotation
AnnotationLayer = image_annotation.AnnotationLayer


def test_annotation_model():
    """测试标注数据模型"""
    print("=" * 60)
    print("测试1: Annotation数据模型")
    print("=" * 60)
    
    # 创建矩形标注
    rect_ann = Annotation(
        type='rect',
        points=[(10, 10), (100, 100)],
        properties={'color': (0, 255, 0), 'thickness': 2}
    )
    print(f"✅ 创建矩形标注: ID={rect_ann.id}, Type={rect_ann.type}")
    print(f"   坐标点: {rect_ann.points}")
    
    # 转换为字典
    data = rect_ann.to_dict()
    print(f"✅ 转换为字典: {list(data.keys())}")
    
    # 从字典恢复
    restored = Annotation.from_dict(data)
    print(f"✅ 从字典恢复: ID={restored.id}, Points={restored.points}")
    
    assert rect_ann.id == restored.id
    assert rect_ann.type == restored.type
    assert rect_ann.points == restored.points
    print("✅ 断言通过：序列化/反序列化一致")
    
    print()


def test_annotation_layer():
    """测试标注层管理器"""
    print("=" * 60)
    print("测试2: AnnotationLayer管理器")
    print("=" * 60)
    
    layer = AnnotationLayer()
    
    # 添加标注
    ann1 = Annotation(type='rect', points=[(10, 10), (100, 100)])
    ann2 = Annotation(type='circle', points=[(200, 200), (250, 250)])
    ann3 = Annotation(type='text', points=[(50, 50)], properties={'text': '测试'})
    
    layer.add_annotation(ann1)
    layer.add_annotation(ann2)
    layer.add_annotation(ann3)
    
    print(f"✅ 添加了3个标注，当前总数: {layer.get_count()}")
    assert layer.get_count() == 3
    
    # 获取可见标注
    visible = layer.get_visible_annotations()
    print(f"✅ 可见标注数量: {len(visible)}")
    assert len(visible) == 3
    
    # 删除一个标注
    layer.remove_annotation(ann2.id)
    print(f"✅ 删除1个标注后，剩余: {layer.get_count()}")
    assert layer.get_count() == 2
    
    # 更新标注
    layer.update_annotation(ann1.id, properties={'color': (255, 0, 0)})
    updated_ann = layer.get_annotation(ann1.id)
    print(f"✅ 更新标注颜色: {updated_ann.properties['color']}")
    assert updated_ann.properties['color'] == (255, 0, 0)
    
    # 清空所有
    layer.clear_all()
    print(f"✅ 清空后，剩余: {layer.get_count()}")
    assert layer.get_count() == 0
    
    print()


def test_export_import():
    """测试导出/导入功能"""
    print("=" * 60)
    print("测试3: 标注导出/导入")
    print("=" * 60)
    
    layer = AnnotationLayer()
    
    # 添加一些标注
    ann1 = Annotation(type='rect', points=[(10, 10), (100, 100)])
    ann2 = Annotation(type='text', points=[(50, 50)], properties={'text': 'Hello'})
    layer.add_annotation(ann1)
    layer.add_annotation(ann2)
    
    # 导出为JSON
    json_data = layer.export_to_json()
    print(f"✅ 导出为JSON，共{len(json_data)}条记录")
    assert len(json_data) == 2
    
    # 导入到新图层
    new_layer = AnnotationLayer()
    new_layer.import_from_json(json_data)
    print(f"✅ 导入到新图层，共{new_layer.get_count()}条记录")
    assert new_layer.get_count() == 2
    
    print()


if __name__ == '__main__':
    try:
        test_annotation_model()
        test_annotation_layer()
        test_export_import()
        
        print("=" * 60)
        print("🎉 所有单元测试通过！")
        print("=" * 60)
    except AssertionError as e:
        print(f"❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
