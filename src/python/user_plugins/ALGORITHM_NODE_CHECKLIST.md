# 算法节点开发检查清单

> 在创建新算法节点前，请对照此清单确保所有步骤正确完成

## 📋 开发前准备

### 1. 确定节点分类
- [ ] 选择6大分类之一：图像相机 / 预处理 / 特征提取 / 测量分析 / 识别分类 / 系统集成
- [ ] 确定子分类（如：滤波、边缘检测、二值化等）
- [ ] 评估资源等级：light（轻量）/ medium（中等）/ heavy（重量级）

### 2. 设计节点接口
- [ ] 确定输入端口数量和类型（图像/数值/文本）
- [ ] 确定输出端口数量和类型
- [ ] 列出可配置参数及其默认值、取值范围
- [ ] 绘制节点连接示意图

---

## 🛠️ 代码实现步骤

### Step 1: 创建节点包目录结构

```bash
cd src/python/plugin_packages/builtin
mkdir your_package_name
cd your_package_name
mkdir nodes
touch nodes/__init__.py
touch plugin.json
```

**目录结构示例**:
```
your_package_name/
├── plugin.json          # 元数据配置
└── nodes/
    ├── __init__.py      # 导出所有节点类
    └── your_node.py     # 节点实现
```

### Step 2: 编写 plugin.json

```json
{
  "name": "your_package_name",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "节点包功能描述",
  "category_group": "预处理",
  "nodes": [
    {
      "class": "YourNodeClass",
      "display_name": "显示名称",
      "category": "子分类",
      "color": [255, 150, 100],
      "icon": "🔧",
      "width": 180,
      "height": 100,
      "description": "节点详细说明",
      "resource_level": "light",
      "hardware_requirements": {
        "cpu_cores": 1,
        "memory_gb": 1,
        "gpu_required": false,
        "gpu_memory_gb": 0
      },
      "dependencies": ["opencv-python>=4.5.0"]
    }
  ],
  "dependencies": ["opencv-python>=4.5", "numpy"],
  "min_app_version": "4.0.0"
}
```

**✅ 检查项**:
- [ ] `name` 使用小写字母+下划线
- [ ] `category_group` 是6大分类之一
- [ ] `nodes` 数组不为空
- [ ] `class` 字段与Python类名一致
- [ ] `display_name` 简洁明了
- [ ] `color` 为RGB数组 `[R, G, B]`
- [ ] `dependencies` 列出所有必需依赖

### Step 3: 实现节点类

创建 `nodes/your_node.py`:

```python
"""
节点功能简述 - 一句话说明用途
"""

from shared_libs.node_base import BaseNode
import cv2
import numpy as np


class YourNodeClass(BaseNode):
    """
    节点详细文档字符串
    
    功能说明：
    - 主要功能1
    - 主要功能2
    
    硬件要求：
    - CPU: X+ 核心
    - 内存: YGB+
    - GPU: 是否需要
    """
    
    __identifier__ = 'your_package_name'  # ⚠️ 必须与plugin.json的name一致
    NODE_NAME = '显示名称'                 # ⚠️ 必须与plugin.json的display_name一致
    
    # 资源等级声明
    resource_level = "light"  # light / medium / heavy
    
    # 硬件要求
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 1,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }
    
    def __init__(self):
        super(YourNodeClass, self).__init__()
        
        # 输入端口（绿色表示图像数据）
        self.add_input('输入图像', color=(100, 255, 100))
        
        # 输出端口
        self.add_output('输出图像', color=(100, 255, 100))
        
        # 参数控件
        self.add_text_input('param1', '参数1说明', tab='properties')
        self.set_property('param1', '默认值')
        
        self.add_text_input('param2', '参数2说明', tab='properties')
        self.set_property('param2', '10')
    
    def process(self, inputs=None):
        """
        处理节点逻辑
        
        Args:
            inputs: 输入数据列表，inputs[0]为第一个端口的输入
            
        Returns:
            dict: 输出端口名称 -> 数据字典
        """
        try:
            # Step 1: 验证输入
            if not inputs or len(inputs) == 0 or inputs[0] is None:
                self.log_warning("未接收到输入图像")
                return {'输出图像': None}
            
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            
            if image is None or not isinstance(image, np.ndarray):
                self.log_error("输入图像格式错误")
                return {'输出图像': None}
            
            # Step 2: 读取参数
            param1 = self.get_property('param1')
            param2 = int(self.get_property('param2'))
            
            # Step 3: 执行算法
            result = cv2.some_operation(image, param1, param2)
            
            # Step 4: 返回结果
            self.log_success("处理完成")
            return {'输出图像': result}
            
        except Exception as e:
            self.log_error(f"处理错误: {e}")
            return {'输出图像': None}
```

**✅ 检查项**:
- [ ] 继承 `BaseNode`（不是 `NodeGraphQt.BaseNode`）
- [ ] `__identifier__` 与plugin.json的name完全一致
- [ ] `NODE_NAME` 与plugin.json的display_name完全一致
- [ ] 定义了 `resource_level` 和 `hardware_requirements`
- [ ] 端口颜色符合规范（图像用绿色）
- [ ] 使用 `add_text_input()` 添加参数
- [ ] process方法包含完整的try-except
- [ ] 失败时返回None而非抛出异常
- [ ] 使用 `self.log_*()` 记录日志

### Step 4: 导出节点类

编辑 `nodes/__init__.py`:

```python
"""
节点包导出模块
"""

from .your_node import YourNodeClass

__all__ = ['YourNodeClass']
```

**✅ 检查项**:
- [ ] 导出了所有节点类
- [ ] 文件名使用 `__init__.py`（双下划线）
- [ ] 使用相对导入（`.your_node`）

---

## 🧪 测试与调试

### Step 5: 语法检查

```bash
cd src/python/plugin_packages/builtin/your_package_name
python -m py_compile nodes/your_node.py
```

**✅ 检查项**:
- [ ] 无语法错误
- [ ] 无导入错误

### Step 6: 刷新插件

1. 启动应用程序
2. 菜单：**插件(P)** → **🔄 刷新插件**
3. 查看控制台输出

**预期输出**:
```
📦 扫描内置插件 (builtin)...
   ✅ your_package_name (source: builtin)
✅ 共扫描到 X 个插件

✅ 插件 your_package_name 加载完成，注册 1 个节点
   ✅ 注册节点: 显示名称
```

**✅ 检查项**:
- [ ] 插件扫描成功
- [ ] 节点注册成功
- [ ] 无报错信息

### Step 7: UI测试

1. 在左侧节点库找到对应分类标签页
2. 拖拽节点到画布
3. 连接输入输出端口
4. 双击节点调整参数
5. 点击"▶ 运行"执行工作流
6. 查看预览窗口结果

**✅ 检查项**:
- [ ] 节点出现在正确的标签页
- [ ] 节点显示名称正确
- [ ] 参数可以正常调整
- [ ] 节点执行无报错
- [ ] 输出结果符合预期

---

## 🐛 常见问题排查

### 问题1: 节点不显示在节点库中

**可能原因**:
- [ ] `__identifier__` 与plugin.json的name不一致
- [ ] 未执行"刷新插件"
- [ ] nodes/__init__.py未导出节点类
- [ ] plugin.json格式错误（缺少必需字段）
- [ ] nodes.py有语法错误

**解决方案**:
1. 检查控制台是否有报错
2. 运行 `python -m py_compile nodes/your_node.py` 验证语法
3. 确认 `__identifier__` 与plugin.json的name完全一致
4. 重启应用程序（新增节点时必须重启）

### 问题2: 标签页名称不正确

**原因**: 标签页名称由 `__identifier__` 决定

**解决方案**:
1. 修改 `__identifier__` 为期望的名称
2. 同步修改plugin.json的name字段
3. **重启应用程序**（修改后必须重启）

### 问题3: 节点执行报错

**调试步骤**:
1. 查看控制台错误信息
2. 检查process方法的try-except块
3. 验证输入数据不为None
4. 确认依赖库已安装
5. 使用 `print()` 或 `self.log_info()` 输出中间变量

### 问题4: 工程文件打开后节点丢失

**原因**: 反序列化前节点类型未注册

**解决方案**:
1. 确保在加载session_data前调用 `plugin_manager.load_plugin_nodes()`
2. 检查控制台是否有"注册节点"日志
3. 对比JSON中的节点数量与反序列化后的实际数量

---

## 📦 打包与发布

### Step 8: 创建README.md（可选但推荐）

```markdown
# 你的节点包名称

## 功能介绍
简要说明节点包的功能和用途

## 节点列表
- **节点1名称**: 功能说明
- **节点2名称**: 功能说明

## 使用方法
1. 拖拽节点到画布
2. 连接输入输出端口
3. 调整参数
4. 执行工作流

## 依赖安装
```bash
pip install opencv-python>=4.5 numpy
```

## 示例工作流
提供示例截图或JSON文件路径
```

### Step 9: 导出为ZIP（分享给他人）

1. 压缩节点包目录：
```bash
cd src/python/plugin_packages/builtin
zip -r your_package_name.zip your_package_name/
```

2. ZIP文件结构：
```
your_package_name.zip
├── plugin.json
└── nodes/
    ├── __init__.py
    └── your_node.py
```

3. 安装方式：
   - 菜单：**插件(P)** → **📥 安装插件** → 选择ZIP文件

---

## ✅ 最终验收清单

### 代码质量
- [ ] 所有节点类有完整的docstring
- [ ] 变量命名清晰（snake_case）
- [ ] 类名使用CamelCase
- [ ] 代码有适当注释
- [ ] 无硬编码路径或魔法数字

### 功能完整性
- [ ] 输入验证完善
- [ ] 参数范围限制合理
- [ ] 异常处理完整
- [ ] 日志输出清晰
- [ ] 返回数据格式正确

### 性能优化
- [ ] 避免不必要的深拷贝
- [ ] 大图处理前先缩放
- [ ] 缓存重复计算结果
- [ ] 快速失败（无效输入立即返回）

### 文档完整性
- [ ] plugin.json填写完整
- [ ] README.md说明清晰
- [ ] 节点docstring详细
- [ ] 参数说明准确

### 兼容性
- [ ] 最低应用版本设置合理
- [ ] 依赖版本约束明确
- [ ] 跨平台测试通过（Windows/Linux/macOS）

---

## 🎯 下一步行动

完成以上步骤后，你的节点已经可以正常使用。接下来可以：

1. **优化性能**: 使用性能监控工具分析瓶颈
2. **添加单元测试**: 确保代码稳定性
3. **编写教程**: 帮助用户快速上手
4. **收集反馈**: 根据用户建议改进
5. **发布到市场**: 分享给更多用户

**祝你开发顺利！** 🚀
