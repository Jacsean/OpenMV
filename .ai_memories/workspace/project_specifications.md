# 项目特定规范：StduyOpenCV

> **说明**：此文件包含 StduyOpenCV 项目特有的开发规范和架构决策。
> **适用范围**：仅当前项目，随代码一起提交到 Git。
> **最后更新**：2026-04-28

---

## 项目概述

StduyOpenCV 是一个基于 OpenCV 的多语言图像处理与视觉分析系统，提供 Python（传统版/图形化版）和 C++ 三种实现。

**核心特点**：
- 完全离线运行，保护数据隐私
- 支持节点式可视化编程（Python 图形化版）
- 插件化架构，支持热加载和安全沙箱

---

## 插件系统规范

### 目录组织

```
src/python/user_plugins/          # 用户插件目录
├── io_camera/                    # 插件包（每个子目录是一个完整插件）
│   ├── plugin.json               # 插件元数据
│   ├── nodes/                    # 节点实现目录
│   │   ├── __init__.py           # 导出所有节点类
│   │   ├── image_load.py
│   │   └── image_save.py
│   └── README.md                 # 插件说明（可选）
│
├── preprocessing/                # 另一个插件包
└── ...

src/python/shared_libs/           # 共享库目录（非插件）
├── ai_base/                      # AI 节点基类
├── common_utils/                 # 通用工具函数
└── ...
```

**关键规则**：
- ✅ `user_plugins/` 仅包含插件包，禁止混入 `.py` 脚本或 `.md` 文档
- ✅ 共享代码放在 `shared_libs/` 目录
- ✅ 使用下划线前缀命名内部模块（如 `_internal_tools`），不会被扫描为插件

### 插件元数据（plugin.json）

```json
{
  "name": "io_camera",
  "version": "1.0.0",
  "author": "开发者姓名",
  "description": "图像相机相关节点",
  "category_group": "图像相机",
  "nodes": [
    {
      "class": "ImageLoadNode",
      "display_name": "加载图像",
      "category": "输入",
      "icon": "icons/load.png",
      "color": [100, 150, 200]
    }
  ],
  "dependencies": ["opencv-python>=4.5"],
  "min_app_version": "4.0.0",
  "resource_level": "lightweight",
  "hardware_requirements": {
    "cpu_cores": 2,
    "memory_gb": 2
  }
}
```

**必需字段**：
- `name`: 插件唯一标识符（应与目录名、`__identifier__` 一致）
- `version`: 语义化版本号
- `category_group`: UI 显示的分类名称
- `nodes`: 节点列表（可为空数组）
- `resource_level`: 资源等级（`lightweight` / `moderate` / `heavy`）
- `hardware_requirements`: 硬件要求声明

---

## 节点开发规范

### 基类继承

**所有节点必须继承 `AIBaseNode`**（而非 `BaseNode`）：

```python
from shared_libs.ai_base import AIBaseNode

class ImageLoadNode(AIBaseNode):
    """加载图像节点
    
    从文件系统加载图像并输出。
    """
    
    __identifier__ = 'io_camera'  # 决定节点库标签页名称
    NODE_NAME = '加载图像'
    
    # 资源声明
    resource_level = 'lightweight'
    hardware_requirements = {
        'cpu_cores': 2,
        'memory_gb': 2
    }
    
    def __init__(self):
        super().__init__()
        # 定义输入输出端口
        self.add_input('输入路径', str)
        self.add_output('输出图像', np.ndarray)
    
    def process(self, inputs):
        """处理节点逻辑
        
        Args:
            inputs: 输入字典 {'输入路径': '/path/to/image.jpg'}
        
        Returns:
            输出字典 {'输出图像': image_array} 或 None（失败时）
        """
        try:
            path = inputs.get('输入路径')
            if not path:
                self.log_error("未提供图像路径")
                return None
            
            image = cv2.imread(path)
            if image is None:
                self.log_error(f"无法加载图像: {path}")
                return None
            
            self.log_success(f"图像加载成功: {image.shape}")
            return {'输出图像': image}
            
        except Exception as e:
            self.log_error(f"处理失败: {e}")
            return None
```

### 关键要求

1. **异常处理**：`process()` 必须包含 try-except，返回 `None` 而非抛出异常
2. **日志方法**：使用统一的 `log_info/warning/error/success`
3. **端口命名**：输入端口"输入XXX"，输出端口"输出XXX"
4. **文档字符串**：每个节点类必须有完整 docstring
5. **参数控件**：优先使用 `add_text_input`，避免废弃的 `add_slider`

---

## UI 显示规范

### 节点库标签页命名

**三层命名体系**：
1. **内部标识符**：`__identifier__`（NodeGraphQt 用于分组）
2. **显示名称**：`category_group`（UI 实际显示）
3. **插件 ID**：`name`（用于加载/卸载）

**映射关系**：
```
plugin.json 的 name → 匹配 → nodes.py 的 __identifier__ → 替换为 → category_group
```

**关键规则**：
- ✅ `name`、`__identifier__`、目录名三者应保持一致
- ✅ 只有注册了至少一个节点的插件才会创建标签页
- ✅ 不同插件的 `category_group` 应避免重复
- ✅ 修改后必须**重启应用**才能看到变化

### UI 组件限制

- ❌ `NodesPaletteWidget` 不支持动态切换绑定的 Graph
- ❌ `BaseNode` 不支持重写 `build_menu`
- ❌ `NodeButton` 无 `clicked` 信号
- ✅ 图像预览使用 `QGraphicsView` + `Scene`
- ✅ 支持拖拽平移、滚轮缩放（10%-500%）

---

## 应用程序启动顺序

为确保依赖组件就绪，必须遵循以下严格顺序：

1. **扫描插件元数据**：`_load_plugins()` 解析 `plugin.json` 并暂存至 `_pending_plugins`（**不执行节点注册**）
2. **创建 UI 组件**：`_setup_ui()` 初始化主界面
   - 创建临时 `NodeGraph` 实例
   - 创建 `NodesPaletteWidget` 并绑定到临时 Graph
   - 确保 `tab_widget` 等关键 UI 组件已实例化
3. **初始化工程与工作流**：`initialize_default_project()`
   - 创建默认工作流及其 `NodeGraph`
   - **仅在第一个工作流创建时**，触发插件节点的实际加载

**禁止事项**：
- ❌ 禁止在 UI 组件创建之前尝试加载或注册插件节点
- ❌ 禁止在 `NodeGraph` 实例创建之前执行依赖 Graph 的操作

---

## NodeGraphQt API 正确使用

### 序列化

```python
# ✅ 正确用法
data = graph.serialize_session()  # 无参，返回 dict
graph.save_session('/path/to/file.json')  # 保存文件
graph.deserialize_session(data)  # 从 dict 加载
graph.deserialize_session('/path/to/file.json')  # 从文件加载

# ❌ 错误用法
graph.session_to_dict()  # 不存在此方法
graph.serialize_session('/path')  # 不接受路径参数
```

### 节点操作

```python
# ✅ 正确用法
node_id = node.id  # 通过 .id 属性获取
node.set_property('custom_param', value)

# ❌ 错误用法
node._properties  # 禁止访问私有属性
node.add_slider('param', ...)  # 已废弃
node.add_text_input('param', placeholder='...')  # placeholder 参数不支持
```

### 调试技巧

```python
# 遇到问题时使用 dir() 检查可用方法
print(dir(graph))
print(dir(node))
```

---

## 日志系统规范

### 双重输出机制

- **终端输出**：用于应用启动阶段调试，便于快速定位加载问题
- **UI 面板显示**：用于应用运行阶段监控，无需切换窗口查看日志

### 输出精简原则

- ✅ 保留：安全检查结果、模块加载成功/失败、节点注册数量
- ❌ 移除：节点图标、尺寸、颜色、描述长度等非必要详细信息
- ❌ 简化："已在监听中"等重复状态提示

**量化目标**：日志输出量减少 75% 以上，同时保持足够的调试信息。

---

## 工程管理体系

### 持久化格式

支持两种模式：
1. **目录模式**（`.proj`）：包含 `project.json`、`workflows/`、`assets/` 等
2. **ZIP 单文件模式**：将所有内容打包为单个 `.proj` 文件

### 文件结构

```
my_project.proj/
├── project.json          # 工程元数据
├── index.json            # 全文索引（加速搜索）
├── thumbnail.png         # 缩略图
├── workflows/
│   ├── workflow_1.json   # 工作流定义
│   └── ...
├── assets/               # 资源文件
└── cache/                # 缓存数据
```

### 搜索优化

- **机制**：引入 `index.json` 全文索引，预构建倒排索引
- **效果**：搜索速度提升 50 倍以上，支持模糊/多关键词/字段过滤

---

## 常见问题排查

### 节点库不显示

1. 检查 `__identifier__` 设置是否正确
2. 确认节点是否同时注册到节点库 Graph 和工作流 Graph
3. 检查控制台是否有加载错误
4. **重启应用**（修改后必须重启）

### 标签页名称异常

- 确认是由 `__identifier__` 决定
- 检查 `plugin.json` 的 `category_group` 字段
- 修改后需重启应用

### 标签页未重命名

- 检查插件是否注册了节点（`nodes.py` 不能为空）
- 检查 `plugin.json` 的 `nodes` 数组是否为空

### 标签页名称重复

- 检查是否有多个插件使用了相同的 `category_group` 值

---

## 测试与验证

### 迁移准备检查

使用自动化工具验证项目状态：

```bash
python tools/check_migration_readiness.py
```

**检查项**：
- ✅ 文档完整性
- ✅ Git 状态
- ✅ 项目结构
- ✅ 插件包配置

### 插件验证标准

1. **语法检查**：所有节点文件无语法错误
2. **导入路径**：相对导入路径正确，无 `ModuleNotFoundError`
3. **资源声明**：`resource_level` 和 `hardware_requirements` 完整
4. **日志方法**：使用统一的日志方法
5. **兼容性**：节点标识符、名称、端口保持不变
6. **功能验证**：重启应用后能正常加载注册

---

**维护者**：StduyOpenCV 开发团队  
**文档版本**：1.0  
**最后审查**：2026-04-28
