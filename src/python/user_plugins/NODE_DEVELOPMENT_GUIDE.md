# 节点开发完全指南

> 从零开始创建你的第一个OpenCV视觉节点

## 📋 目录

1. [快速开始](#快速开始)
2. [节点基础概念](#节点基础概念)
3. [创建第一个节点](#创建第一个节点)
4. [节点进阶开发](#节点进阶开发)
5. [打包与发布](#打包与发布)
6. [常见问题](#常见问题)

---

## 快速开始

### 环境准备

确保已安装以下依赖：

```bash
pip install opencv-python>=4.5 numpy PySide2 NodeGraphQt
```

### 项目结构

```
user_plugins/
├── my_custom_nodes/          # 你的节点包目录
│   ├── plugin.json           # 元数据文件（必需）
│   ├── nodes.py              # 节点代码（必需）
│   └── README.md             # 说明文档（可选）
└── ...其他节点包
```

---

## 节点基础概念

### 什么是节点？

节点是视觉处理流程中的基本单元，每个节点：
- **输入**：接收图像或数据
- **处理**：执行特定算法（如滤波、边缘检测）
- **输出**：返回处理结果

### 节点分类体系

| 分类 | 用途 | 示例 |
|------|------|------|
| 📷 图像相机 | IO操作 | 加载图像、保存图像 |
| 🎨 预处理 | 基础处理 | 灰度化、高斯模糊 |
| 🔍 特征提取 | 分析层 | Canny边缘检测 |
| 📏 测量分析 | 量化层 | 轮廓分析、边界框 |
| 🧠 识别分类 | AI层 | 模板匹配、OCR |
| 🔌 系统集成 | 通信层 | 数据输出、PLC交互 |

---

## 创建第一个节点

### Step 1: 创建节点包目录

```bash
cd src/python/user_plugins
mkdir brightness_adjust
```

### Step 2: 编写 plugin.json

```json
{
  "name": "brightness_adjust",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "亮度调节节点包",
  "category_group": "预处理",
  "nodes": [
    {
      "class": "BrightnessNode",
      "display_name": "亮度调节",
      "category": "色彩调整",
      "color": [200, 200, 100]
    }
  ],
  "dependencies": ["opencv-python>=4.5", "numpy"],
  "min_app_version": "4.0.0"
}
```

**字段说明**：
- `name`: 节点包唯一标识（小写字母+下划线）
- `version`: 语义化版本号
- `category_group`: 6大分类之一
- `nodes`: 节点列表，每个节点包含类名、显示名、子分类、颜色
- `dependencies`: Python依赖包列表
- `min_app_version`: 最低应用版本要求

### Step 3: 编写 nodes.py

```python
"""
亮度调节节点
调整图像亮度和对比度
"""

from NodeGraphQt import BaseNode
import cv2
import numpy as np


class BrightnessNode(BaseNode):
    """
    亮度调节节点
    
    通过alpha和beta参数调整图像亮度和对比度
    公式: dst = src * alpha + beta
    """
    
    __identifier__ = 'brightness_adjust'
    NODE_NAME = '亮度调节'
    
    def __init__(self):
        super(BrightnessNode, self).__init__()
        
        # 添加输入端口
        self.add_input('输入图像', color=(100, 255, 100))
        
        # 添加输出端口
        self.add_output('输出图像', color=(100, 255, 100))
        
        # 添加参数控件
        self.add_text_input('alpha', '对比度(0.0-3.0)', tab='properties')
        self.set_property('alpha', '1.0')
        
        self.add_text_input('beta', '亮度(-100-100)', tab='properties')
        self.set_property('beta', '0')
        
    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: 输入数据列表，inputs[0]为第一个端口的输入
            
        Returns:
            dict: 输出端口名称 -> 数据
        """
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            try:
                # 获取参数
                alpha = float(self.get_property('alpha'))
                beta = float(self.get_property('beta'))
                
                # 限制参数范围
                alpha = max(0.0, min(3.0, alpha))
                beta = max(-100, min(100, beta))
                
                # 应用亮度调节
                result = cv2.convertScaleAbs(image, alpha=alpha, beta=beta)
                
                return {'输出图像': result}
                
            except Exception as e:
                print(f"亮度调节错误: {e}")
                return {'输出图像': None}
        
        return {'输出图像': None}
```

**关键要点**：
1. **继承BaseNode**: 所有节点必须继承 `NodeGraphQt.BaseNode`
2. **定义标识**: `__identifier__` 必须与plugin.json中的name一致
3. **端口管理**: 使用 `add_input()` 和 `add_output()` 添加端口
4. **参数控件**: 使用 `add_text_input()` 添加可配置参数
5. **异常处理**: process方法必须包含try-except，返回None而非抛出异常

### Step 4: 测试节点

1. 启动应用程序
2. 菜单：**插件 → 🔄 刷新插件**
3. 在节点库中找到"亮度调节"节点
4. 拖拽到画布，连接输入输出端口
5. 调整参数查看效果

---

## 节点进阶开发

### 多输入多输出节点

```python
class ImageBlendNode(BaseNode):
    """图像混合节点 - 两个输入，一个输出"""
    
    __identifier__ = 'my_package'
    NODE_NAME = '图像混合'
    
    def __init__(self):
        super(ImageBlendNode, self).__init__()
        
        # 多个输入端口
        self.add_input('背景图像', color=(100, 255, 100))
        self.add_input('前景图像', color=(100, 255, 100))
        
        # 输出端口
        self.add_output('混合结果', color=(100, 255, 100))
        
        # 混合比例参数
        self.add_text_input('alpha', '混合比例(0.0-1.0)', tab='properties')
        self.set_property('alpha', '0.5')
        
    def process(self, inputs=None):
        if inputs and len(inputs) >= 2:
            bg_image = inputs[0][0] if inputs[0] else None
            fg_image = inputs[1][0] if inputs[1] else None
            
            if bg_image is not None and fg_image is not None:
                try:
                    alpha = float(self.get_property('alpha'))
                    # 确保两张图片尺寸相同
                    fg_resized = cv2.resize(fg_image, (bg_image.shape[1], bg_image.shape[0]))
                    result = cv2.addWeighted(bg_image, 1-alpha, fg_resized, alpha, 0)
                    return {'混合结果': result}
                except Exception as e:
                    print(f"图像混合错误: {e}")
                    return {'混合结果': None}
        
        return {'混合结果': None}
```

### 自定义颜色编码

```python
def __init__(self):
    super(CustomNode, self).__init__()
    
    # 端口颜色规范
    # 绿色 (100, 255, 100): 图像数据
    # 蓝色 (100, 100, 255): 数值数据
    # 黄色 (255, 255, 100): 文本数据
    # 红色 (255, 100, 100): 布尔/状态
    
    self.add_input('输入图像', color=(100, 255, 100))
    self.add_output('检测结果', color=(255, 100, 100))
```

### 复杂数据处理

```python
class ContourStatsNode(BaseNode):
    """轮廓统计节点 - 输出多个数据"""
    
    def __init__(self):
        super(ContourStatsNode, self).__init__()
        self.add_input('输入图像', color=(100, 255, 100))
        
        # 多个输出端口
        self.add_output('标注图像', color=(100, 255, 100))
        self.add_output('轮廓数量', color=(100, 100, 255))
        self.add_output('最大面积', color=(100, 100, 255))
        
    def process(self, inputs=None):
        if inputs and inputs[0]:
            image = inputs[0][0]
            try:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
                _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
                contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
                # 绘制轮廓
                result = image.copy()
                cv2.drawContours(result, contours, -1, (0, 255, 0), 2)
                
                # 计算统计信息
                count = len(contours)
                max_area = max([cv2.contourArea(c) for c in contours], default=0)
                
                return {
                    '标注图像': result,
                    '轮廓数量': count,
                    '最大面积': max_area
                }
            except Exception as e:
                print(f"轮廓统计错误: {e}")
                return {'标注图像': None, '轮廓数量': 0, '最大面积': 0}
        
        return {'标注图像': None, '轮廓数量': 0, '最大面积': 0}
```

---

## 打包与发布

### 导出为ZIP插件包

1. 在节点编辑器中选择节点包
2. 点击工具栏 **📤 导出节点包**
3. 选择保存路径，生成 `.zip` 文件

### ZIP文件结构

```
my_custom_nodes.zip
├── plugin.json
├── nodes.py
└── README.md (可选)
```

### 分享给他人

将ZIP文件发送给其他用户，他们可以通过：
- 菜单：**插件 → 📥 导入节点包**
- 选择ZIP文件自动安装

---

## 常见问题

### Q1: 节点不显示在节点库中？

**检查清单**：
1. ✅ plugin.json格式正确（使用JSON验证工具）
2. ✅ `category_group` 是6大分类之一
3. ✅ 已执行 **插件 → 🔄 刷新插件**
4. ✅ nodes.py无语法错误（运行 `python -m py_compile nodes.py`）

### Q2: 节点执行报错？

**调试步骤**：
1. 查看控制台输出的错误信息
2. 检查process方法的try-except块
3. 验证输入数据不为None
4. 确认依赖库已安装

### Q3: 如何修改已有节点？

**方法A - 使用节点编辑器**：
1. 打开 **插件 → 🛠️ 节点编辑器**
2. 选择节点包和节点
3. 切换到"代码"标签页
4. 编辑后点击 **💾 保存代码**

**方法B - 直接编辑文件**：
1. 打开 `user_plugins/{package}/nodes.py`
2. 修改代码
3. 重启应用或刷新插件

### Q4: 如何添加图标？

目前版本暂不支持自定义图标，节点颜色通过plugin.json中的`color`字段设置。

### Q5: 节点性能优化建议

1. **避免重复计算**：缓存中间结果
2. **图像缩放**：处理前缩小大图
3. **异常快速返回**：无效输入立即返回None
4. **减少内存拷贝**：使用原地操作（如`cv2.cvtColor(src, dst)`）

---

## 最佳实践

### ✅ 推荐做法

1. **完整的docstring**：每个节点类和方法都有文档字符串
2. **参数验证**：检查输入数据类型和范围
3. **清晰的命名**：类名用CamelCase，变量用snake_case
4. **单一职责**：每个节点只做一件事
5. **错误日志**：print输出便于调试

### ❌ 避免陷阱

1. **不要修改输入数据**：使用`.copy()`创建副本
2. **不要阻塞UI**：耗时操作考虑异步
3. **不要硬编码路径**：使用相对路径或参数
4. **不要忽略异常**：始终捕获并记录错误

---

## 下一步

- 📖 阅读 [API参考手册](NODE_API_REFERENCE.md)
- 💡 查看 [高级示例节点包](example_advanced_nodes/)
- 🛠️ 使用节点编辑器创建你的第一个节点

**祝你开发愉快！** 🚀
