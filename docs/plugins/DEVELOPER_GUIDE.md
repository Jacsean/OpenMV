# 统一插件体系开发指南（改进版）

## 📋 概述

本指南介绍如何在新的**两层架构**统一插件体系下开发和管理插件。

**核心改进：**
- ✅ 简化为两层结构：builtin/ + marketplace/
- ✅ 通用节点基类：node_base（原ai_base）
- ✅ 明确定位：builtin为官方内置，marketplace为市场共享

## 🏗️ 架构概览

### 两层插件目录结构
```
plugin_packages/
├── builtin/                ← 内置节点（官方发布，需编译）
│   ├── io_camera/          ← 图像IO
│   ├── preprocessing/      ← 预处理
│   └── ...
│
└── marketplace/            ← 市场插件（动态加载，可分享）
    ├── installed/          ← 已安装的插件
    ├── cache/              ← ZIP缓存
    └── binaries/           ← 二进制插件
```

### 共享库目录
```
shared_libs/
└── node_base/              ← 🆕 通用节点基类（原ai_base）
    ├── base_node.py        ← 统一节点基类
    ├── performance_monitor.py
    └── resource_manager.py
```

## 🚀 快速开始

### 1. 创建新插件包

#### 在marketplace中创建插件
```bash
# 在市场插件目录下创建新插件
mkdir -p src/python/plugin_packages/marketplace/installed/my_plugin
cd src/python/plugin_packages/marketplace/installed/my_plugin

# 创建必要文件
touch plugin.json nodes.py README.md
```

#### plugin.json模板
```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "My custom plugin for marketplace",
  "category_group": "自定义",
  "nodes": [
    {
      "class": "MyNode",
      "display_name": "我的节点",
      "category": "自定义处理",
      "color": [200, 200, 200]
    }
  ],
  "dependencies": ["numpy>=1.20"],
  "min_app_version": "4.0.0",
  "source": "marketplace"
}
```

#### nodes.py模板
```python
"""
我的自定义插件 - 市场插件示例
"""

from shared_libs.node_base import BaseNode


class MyNode(BaseNode):
    """
    我的自定义节点
    
    功能描述...
    """
    
    __identifier__ = 'my_plugin'
    NODE_NAME = '我的节点'
    
    def __init__(self):
        super(MyNode, self).__init__()
        # 添加输入端口
        self.add_input('输入图像', color=(100, 255, 100))
        
        # 添加输出端口
        self.add_output('输出图像', color=(100, 255, 100))
        
        # 添加参数控件
        self.add_text_input('param1', '参数1', tab='properties')
    
    def process(self, inputs=None):
        """处理节点逻辑"""
        if inputs and len(inputs) > 0 and inputs[0] is not None:
            image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
            try:
                # 你的处理逻辑
                result = image
                return {'输出图像': result}
            except Exception as e:
                print(f"处理错误: {e}")
                return {'输出图像': None}
        return {'输出图像': None}
```

### 2. 测试插件

1. **重启应用**以加载新插件
2. **检查节点库**是否显示新节点
3. **创建工作流**测试节点功能

## 📦 插件类型与存放位置

### builtin/ vs marketplace/ 的选择

| 场景 | 存放位置 | 说明 |
|------|----------|------|
| OpenCV基础算法 | builtin/ | 官方内置，随应用发布 |
| AI推理模型 | marketplace/ | 市场插件，可在线分享 |
| 行业专用算法 | marketplace/ | 第三方开发者贡献 |
| 用户实验性代码 | marketplace/ | 直接在marketplace中开发 |
| GPU加速插件 | marketplace/binaries/ | 二进制插件 |

### Python源码插件
- **适用场景**: 所有类型的节点
- **存放位置**: builtin/ 或 marketplace/installed/
- **加载方式**: 动态import
- **优点**: 易于开发和调试
- **缺点**: 性能相对较低

### ZIP打包插件
- **适用场景**: 市场分发、离线安装
- **存放位置**: marketplace/cache/
- **加载方式**: 解压后按Python加载
- **优点**: 便于分发和版本管理
- **缺点**: 需要解压步骤

### 二进制插件 (DLL/SO)
- **适用场景**: 高性能算法、商业插件
- **存放位置**: marketplace/binaries/{Windows,Linux,MacOS}/
- **加载方式**: ctypes/cffi加载
- **优点**: 性能优异，可保护源码
- **缺点**: 开发复杂，跨平台兼容性差

## 🔧 高级功能

### 使用通用节点基类

#### 导入BaseNode
```python
from shared_libs.node_base import BaseNode

class MyNode(BaseNode):
    """
    使用统一节点基类
    
    适用于：
    - OpenCV算法节点
    - AI推理节点
    - 系统集成节点
    - 用户自定义节点
    """
    
    __identifier__ = 'my_plugin'
    NODE_NAME = '我的节点'
    
    def __init__(self):
        super().__init__()
        # 自动获得性能监控、资源管理等功能
```

#### 使用性能监控
```python
from shared_libs.node_base import PerformanceMonitor

monitor = PerformanceMonitor()

@monitor.measure_time("my_function")
def my_function():
    # 你的代码
    pass
```

### 依赖管理

#### 声明依赖
```json
{
  "dependencies": [
    "opencv-python>=4.5",
    "numpy>=1.20",
    "@builtin/shared_libs.node_base>=1.0"
  ]
}
```

#### 内部依赖引用
- `@builtin/`: 引用内置插件
- `@marketplace/`: 引用市场插件
- `@shared_libs/`: 引用共享库

## 🛠️ 插件管理

### 节点操作

#### 移动节点到不同包
1. 在节点编辑器中选择节点
2. 右键 → "移动到..." → 选择目标包
3. **重启应用**生效

**注意：**
- builtin/ ↔ marketplace/ 之间可以移动
- 移动后需更新plugin.json和代码文件

#### 重命名节点包
1. 在节点包列表中右键
2. 选择"重命名节点包"
3. 输入新名称
4. **重启应用**生效

### 插件排序
1. 点击工具栏"🔀 管理标签顺序"
2. 拖拽调整顺序
3. 保存配置

### 插件安装/卸载（仅marketplace/）
1. 浏览插件市场
2. 点击"安装"按钮
3. 插件自动下载到marketplace/installed/
4. 可随时卸载

**注意：** builtin/中的插件不可卸载

## ⚠️ 注意事项

### 安全限制
- 禁止导入os/subprocess/socket/requests等模块
- 禁止调用eval/exec/open('w')
- 文件系统访问受限

### 命名规范
- 插件目录名必须与plugin.json中的name字段一致
- 使用小写字母和下划线
- 避免使用特殊字符

### 热重载
- 文件保存后0.5秒触发重载
- 仅支持Python源码插件
- 二进制插件需重启

### 分类更新
- 新增分类需重启程序才能在UI中完全显示
- 修改category_group后必须重启

### builtin与marketplace的区别
- **builtin/**: 官方内置，不可删除，稳定性高
- **marketplace/**: 市场插件，可安装/卸载，灵活性高

## 📚 相关文档

- [PLUGIN_ARCHITECTURE.md](PLUGIN_ARCHITECTURE.md) - 架构设计规范
- [MIGRATION_PLAN.md](MIGRATION_PLAN.md) - 迁移计划
- [NODE_DEVELOPMENT_GUIDE.md](NODE_DEVELOPMENT_GUIDE.md) - 节点开发指南
- [NODE_API_REFERENCE.md](NODE_API_REFERENCE.md) - API参考手册

## 🆘 常见问题

### Q: 我应该把插件放在builtin还是marketplace？
A: 
- 如果是OpenCV基础算法且由官方维护 → builtin/
- 如果是AI模型、专用算法或用户开发 → marketplace/

### Q: marketplace/中的插件如何分享给他人？
A: 
1. 打包为ZIP格式
2. 上传到插件市场
3. 其他用户可通过市场下载安装

### Q: node_base和原来的ai_base有什么区别？
A: 
- node_base是通用节点基类，适用于所有类型节点
- ai_base仅暗示用于AI节点，容易造成误解
- node_base强调"统一节点"理念

### Q: 插件加载失败怎么办？
A: 检查控制台错误信息，确认plugin.json格式正确，节点类存在。

### Q: 节点库不显示新节点？
A: 确认节点已注册到正确的Graph实例，重启应用。

### Q: 如何调试插件？
A: 在节点代码中添加print语句，查看控制台输出。

### Q: 二进制插件如何开发？
A: 参考cpp_wrappers目录下的示例，实现标准C接口。