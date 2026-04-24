# 节点系统 API 参考手册

> 完整的接口说明和字段定义

## 📋 目录

1. [BaseNode API](#basenode-api)
2. [plugin.json 规范](#pluginjson-规范)
3. [插件管理器 API](#插件管理器-api)
4. [节点编辑器 API](#节点编辑器-api)

---

## BaseNode API

### 类继承关系

```python
NodeGraphQt.BaseNode  # NodeGraphQt库提供的基类
    └── YourCustomNode  # 你的节点类
```

### 必需属性

#### `__identifier__`
- **类型**: `str`
- **说明**: 节点唯一标识符，必须与plugin.json中的`name`字段一致
- **示例**: `'brightness_adjust'`

#### `NODE_NAME`
- **类型**: `str`
- **说明**: 节点显示名称（中文）
- **示例**: `'亮度调节'`

### 构造函数方法

#### `add_input(name, color=(R, G, B))`
添加输入端口

**参数**:
- `name` (str): 端口名称，如"输入图像"
- `color` (tuple): RGB颜色元组
  - `(100, 255, 100)`: 图像数据
  - `(100, 100, 255)`: 数值数据
  - `(255, 255, 100)`: 文本数据
  - `(255, 100, 100)`: 布尔/状态

**示例**:
```python
self.add_input('输入图像', color=(100, 255, 100))
```

#### `add_output(name, color=(R, G, B))`
添加输出端口

**参数**: 同`add_input`

**示例**:
```python
self.add_output('输出图像', color=(100, 255, 100))
```

#### `add_text_input(name, label, tab='properties')`
添加文本输入参数控件

**参数**:
- `name` (str): 参数内部名称（英文）
- `label` (str): 显示标签（中文）
- `tab` (str): 属性页签名称，默认'properties'

**示例**:
```python
self.add_text_input('threshold', '阈值(0-255)', tab='properties')
self.set_property('threshold', '127')  # 设置默认值
```

#### `set_property(name, value)`
设置参数默认值

**参数**:
- `name` (str): 参数名称（与add_text_input的name一致）
- `value` (str): 默认值字符串

**示例**:
```python
self.set_property('alpha', '1.0')
```

### 核心处理方法

#### `process(inputs=None)`
节点处理逻辑（必须实现）

**参数**:
- `inputs` (list): 输入端口数据列表
  - `inputs[0]`: 第一个输入端口的数据
  - `inputs[0][0]`: 解包后的实际数据（如果是列表）
  - 可能为`None`（未连接或无数据）

**返回值**:
- `dict`: 输出端口名称 -> 数据的映射
- 键名必须与`add_output`中定义的端口名称一致
- 处理失败时返回`None`而非抛出异常

**示例**:
```python
def process(self, inputs=None):
    if inputs and len(inputs) > 0 and inputs[0] is not None:
        image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
        try:
            # 处理逻辑
            result = some_operation(image)
            return {'输出图像': result}
        except Exception as e:
            print(f"错误: {e}")
            return {'输出图像': None}
    return {'输出图像': None}
```

### 辅助方法

#### `get_property(name)`
获取参数当前值

**参数**:
- `name` (str): 参数名称

**返回**: `str` 参数字符串值（需要自行转换类型）

**示例**:
```python
threshold = int(self.get_property('threshold'))
alpha = float(self.get_property('alpha'))
```

---

## plugin.json 规范

### 完整结构

```json
{
  "name": "package_name",
  "version": "1.0.0",
  "author": "作者名",
  "description": "节点包描述",
  "category_group": "分类名称",
  "nodes": [
    {
      "class": "NodeClassName",
      "display_name": "显示名称",
      "category": "子分类",
      "color": [R, G, B]
    }
  ],
  "dependencies": ["opencv-python>=4.5", "numpy"],
  "min_app_version": "4.0.0"
}
```

### 字段详解

#### 顶层字段

| 字段 | 类型 | 必需 | 说明 | 示例 |
|------|------|------|------|------|
| `name` | string | ✅ | 节点包唯一标识（小写+下划线） | `"brightness_adjust"` |
| `version` | string | ✅ | 语义化版本号 | `"1.0.0"` |
| `author` | string | ✅ | 作者名称 | `"张三"` |
| `description` | string | ✅ | 简短描述 | `"亮度调节节点包"` |
| `category_group` | string | ✅ | 6大分类之一 | `"预处理"` |
| `nodes` | array | ✅ | 节点列表（见下方） | `[...]` |
| `dependencies` | array | ❌ | Python依赖包 | `["opencv-python>=4.5"]` |
| `min_app_version` | string | ✅ | 最低应用版本 | `"4.0.0"` |

#### category_group 可选值

- `"图像相机"` - IO操作
- `"预处理"` - 基础图像处理
- `"特征提取"` - 边缘检测、Blob分析
- `"测量分析"` - 尺寸、位置、轮廓
- `"识别分类"` - 二维码、OCR、模板匹配
- `"系统集成"` - PLC、MQTT、机器人

#### nodes 数组元素字段

| 字段 | 类型 | 必需 | 说明 | 示例 |
|------|------|------|------|------|
| `class` | string | ✅ | Python类名（CamelCase） | `"BrightnessNode"` |
| `display_name` | string | ✅ | 显示名称（中文） | `"亮度调节"` |
| `category` | string | ❌ | 子分类 | `"色彩调整"` |
| `color` | array | ❌ | RGB颜色 [0-255] | `[200, 200, 100]` |

### 验证规则

1. **name**: 只能包含小写字母、数字、下划线
2. **version**: 遵循语义化版本 `MAJOR.MINOR.PATCH`
3. **class**: 必须以大写字母开头，与nodes.py中的类名完全一致
4. **color**: 三个整数，范围0-255
5. **dependencies**: 使用pip格式，可指定版本范围

---

## 插件管理器 API

### PluginManager 类

#### `scan_plugins()`
扫描并加载所有插件

**返回**: `list[PluginInfo]` 插件信息列表

**示例**:
```python
plugins = plugin_manager.scan_plugins()
for plugin in plugins:
    print(f"{plugin.name} v{plugin.version}")
```

#### `load_plugin_nodes(plugin_name, node_graph)`
将插件节点注册到NodeGraph

**参数**:
- `plugin_name` (str): 插件包名称
- `node_graph` (NodeGraph): 节点图实例

**示例**:
```python
plugin_manager.load_plugin_nodes('brightness_adjust', self.current_node_graph)
```

#### `install_plugin(zip_path)`
从ZIP文件安装插件

**参数**:
- `zip_path` (str): ZIP文件路径

**返回**: `(success: bool, message: str)`

**示例**:
```python
success, msg = plugin_manager.install_plugin('my_plugin.zip')
if success:
    print("安装成功")
else:
    print(f"安装失败: {msg}")
```

#### `uninstall_plugin(plugin_name)`
卸载插件

**参数**:
- `plugin_name` (str): 插件包名称

**返回**: `(success: bool, message: str)`

**示例**:
```python
success, msg = plugin_manager.uninstall_plugin('brightness_adjust')
```

### PluginInfo 数据类

```python
@dataclass
class PluginInfo:
    name: str              # 插件名称
    version: str           # 版本号
    author: str            # 作者
    description: str       # 描述
    category_group: str    # 分类
    enabled: bool          # 是否启用
    path: Path             # 插件目录路径
    nodes: list            # 节点列表
    dependencies: list     # 依赖项
```

---

## 节点编辑器 API

### NodeEditorDialog 类

#### 构造函数

```python
editor = NodeEditorDialog(parent=None, plugins_dir=None)
```

**参数**:
- `parent` (QWidget): 父窗口
- `plugins_dir` (Path): 插件目录路径

#### 主要功能

1. **浏览节点包**: 左侧树形视图按分类展示
2. **新建节点包**: 工具栏 → 📦 新建节点包
3. **新建节点**: 选择包后点击 ➕ 新建节点
4. **编辑节点**: 选择节点后点击 ✏️ 编辑节点
5. **删除节点**: 选择节点后点击 🗑️ 删除节点
6. **导出ZIP**: 工具栏 → 📤 导出节点包
7. **导入ZIP**: 工具栏 → 📥 导入节点包

#### 快捷键

- `Ctrl+Z`: 撤销操作
- `Ctrl+Y`: 重做操作

#### Tab页签

1. **📋 详情**: 节点包信息、节点列表、依赖项
2. **📝 代码**: 代码编辑器（支持保存和格式化）
3. **👁️ 预览**: 运行预览（显示节点元数据）

---

## 常见错误码

### 节点加载错误

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `ModuleNotFoundError` | 缺少依赖库 | 安装dependencies中声明的包 |
| `SyntaxError` | nodes.py语法错误 | 检查Python语法 |
| `KeyError: 'class'` | plugin.json格式错误 | 验证JSON格式 |
| `节点不显示` | 未刷新插件 | 执行"插件 → 🔄 刷新插件" |

### 节点执行错误

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| `IndexError` | 输入端口未连接 | 检查inputs是否为None |
| `TypeError` | 数据类型错误 | 验证输入数据类型 |
| `cv2.error` | OpenCV处理失败 | 检查图像格式和尺寸 |

---

## 调试技巧

### 1. 启用详细日志

在nodes.py中添加：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process(self, inputs=None):
    logger.debug(f"输入数据: {inputs}")
    # ...
```

### 2. 验证JSON格式

```bash
python -m json.tool plugin.json
```

### 3. 检查Python语法

```bash
python -m py_compile nodes.py
```

### 4. 查看控制台输出

所有print语句会输出到应用程序控制台，便于调试。

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 4.0.0 | 2026-04-24 | 初始版本，支持6大分类节点体系 |

---

**最后更新**: 2026-04-24
