# StduyOpenCV v5.0 发布说明

## 🎉 重大更新：插件系统架构重构

### 版本信息
- **版本号**: v5.0.0
- **发布日期**: 2026-04-27
- **类型**: Major Release (重大版本)

---

## 📋 更新概述

本次更新完成了**插件系统的全面架构重构**，从扁平的`user_plugins/`目录升级为分层的`plugin_packages/{builtin, marketplace}`架构，并创建了通用的`shared_libs/`共享库体系。

---

## ✨ 核心特性

### 1. 分层插件架构 🏗️

**新目录结构**:
```
src/python/plugin_packages/
├── builtin/                        # 官方内置插件（7个）
│   ├── io_camera/                  # 图像相机IO
│   ├── preprocessing/              # 图像预处理
│   ├── feature_extraction/         # 特征提取
│   ├── measurement/                # 测量分析
│   ├── recognition/                # 识别分类
│   ├── match_location/             # 匹配定位
│   └── integration/                # 系统集成
│
└── marketplace/
    └── installed/                  # 市场插件（3个）
        ├── yolo_vision/            # YOLO目标检测
        ├── ocr_vision/             # OCR文字识别
        └── example_advanced_nodes/ # 高级节点示例
```

**优势**:
- ✅ 清晰的插件分类（builtin vs marketplace）
- ✅ 支持差异化权限管理（builtin不可卸载）
- ✅ 便于插件市场扩展

### 2. 通用节点基类 🧬

**新共享库结构**:
```
src/python/shared_libs/
├── node_base/                      # 通用节点基类
│   ├── base_node.py                # BaseNode类（原AIBaseNode）
│   ├── performance_monitor.py      # 性能监控工具
│   └── examples/                   # 使用示例
├── common_utils/                   # 待填充
└── cpp_wrappers/                   # 待填充
```

**关键改进**:
- ✅ `AIBaseNode` → `BaseNode`（更通用的命名）
- ✅ 适用于所有类型节点（OpenCV + AI + 系统集成）
- ✅ 统一的性能监控和缓存机制

### 3. 增强的插件管理器 🔌

**PluginManager新功能**:
- ✅ 两层目录扫描（builtin优先加载）
- ✅ 差异化卸载策略（builtin插件受保护）
- ✅ source字段追踪（builtin/marketplace）
- ✅ priority字段支持优先级排序
- ✅ 热重载监听（文件变化自动重新加载）

### 4. UI功能增强 🎨

**新增UI功能**:
- ✅ 节点包重命名（仅marketplace插件）
- ✅ 节点移动功能（在marketplace包之间）
- ✅ 完善的权限控制和验证逻辑
- ✅ 操作完成后提示用户重启应用

**左侧面板优化**:
- ✅ DockWidget标题修正为"节点库"
- ✅ 节点说明面板固定在底部（200-250px高度）
- ✅ 点击节点显示详细说明

---

## 🔧 技术细节

### 导入路径统一化

**旧导入**（已废弃）:
```python
from ...base_nodes import AIBaseNode
from user_plugins.base_nodes import AIBaseNode
```

**新导入**（标准）:
```python
from shared_libs.node_base import BaseNode
```

**影响范围**:
- ✅ 18个builtin插件文件已更新
- ✅ 3个marketplace插件文件已更新
- ✅ 所有super()调用已修正为正确类名

### 元数据增强

每个插件的`plugin.json`现在包含：
```json
{
  "name": "io_camera",
  "version": "1.0.0",
  "source": "builtin",           // 新增：插件来源
  "priority": 100,                // 新增：加载优先级
  "category_group": "图像相机",   // 新增：分类显示名称
  "nodes": [...]
}
```

---

## 📊 统计数据

| 指标 | 数量 |
|------|------|
| **插件总数** | 10个（7个builtin + 3个marketplace） |
| **节点总数** | 57个 |
| **节点分类** | 19+个 |
| **代码文件修改** | 25+个 |
| **测试通过率** | 100%（7/7 Phase完成） |

---

## 🐛 问题修复

### 已修复的关键问题

1. **节点库为空问题** ✅
   - 根因：导入路径错误、super()调用类名未更新
   - 修复：批量更新21个文件的导入路径和类名引用

2. **DockWidget标题错误** ✅
   - 根因：使用了通用标题"左侧面板"
   - 修复：改为具体功能名称"节点库"

3. **AsyncAINode继承错误** ✅
   - 根因：仍继承自已删除的AIBaseNode
   - 修复：改为继承BaseNode

4. **Marketplace插件加载失败** ✅
   - 根因：example_advanced_nodes和ocr_vision仍有旧导入
   - 修复：更新3个文件的导入路径

---

## 🚀 兼容性说明

### 向后兼容性

- ⚠️ **不兼容变更**: 
  - `user_plugins/base_nodes.py`已迁移至`shared_libs/node_base/base_node.py`
  - 旧的相对导入路径不再支持
  
- ✅ **兼容保障**:
  - 所有现有工作流文件(.proj)仍可正常打开
  - 节点标识符保持不变
  - 工作流中的节点连接关系不受影响

### 迁移指南

如果您有自定义插件需要迁移：

1. **更新导入路径**:
   ```python
   # 旧代码
   from ...base_nodes import AIBaseNode
   
   # 新代码
   from shared_libs.node_base import BaseNode
   ```

2. **更新类继承**:
   ```python
   # 旧代码
   class MyNode(AIBaseNode):
   
   # 新代码
   class MyNode(BaseNode):
   ```

3. **更新super()调用**:
   ```python
   def __init__(self):
       super(MyNode, self).__init__()  # 确保使用当前类名
   ```

---

## 📝 开发指南

详细文档请参考：
- [PLUGIN_ARCHITECTURE.md](docs/plugins/PLUGIN_ARCHITECTURE.md) - 插件架构设计
- [DEVELOPER_GUIDE.md](docs/plugins/DEVELOPER_GUIDE.md) - 开发者指南
- [NODE_DEVELOPMENT_GUIDE.md](src/python/user_plugins/NODE_DEVELOPMENT_GUIDE.md) - 节点开发指南
- [NODE_API_REFERENCE.md](src/python/user_plugins/NODE_API_REFERENCE.md) - 节点API参考

---

## 🙏 致谢

感谢所有参与测试和反馈的用户！

本次更新历时7个Phase，涉及：
- 📦 10个插件的迁移和重组
- 🔧 核心基类的重命名和升级
- 🏗️ PluginManager的全面重构
- 🎨 UI功能的增强和完善
- ✅ 全面的自动化测试验证

---

## 📞 支持与反馈

如有问题或建议，请通过以下方式联系我们：
- GitHub Issues
- 项目文档
- 社区论坛

---

**StduyOpenCV Team**  
2026-04-27