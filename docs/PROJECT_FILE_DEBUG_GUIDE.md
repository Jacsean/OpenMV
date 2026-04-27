# 工程文件保存/打开问题排查指南

**问题描述**: 打开 .proj 工程文件后，中央区域没有任何显示

**排查时间**: 2026-04-27  
**版本**: v4.0.0

---

## 📋 排查思路

### 思路 1: 检查保存 proj 文件是否正常

#### 关键检查点

1. **工作流数据是否正确序列化**
   - 节点图数据是否被正确保存
   - 节点数量是否正确
   - 文件大小是否合理

2. **ZIP 压缩是否成功**
   - 所有必要文件是否都被包含
   - 文件结构是否正确

3. **日志输出位置**
   - `ProjectManager.export_project()` 方法
   - 详细记录每个工作流的保存过程

#### 预期日志输出示例

```
============================================================
📦 开始导出工程: 默认工程
   目标文件: D:/example/projects/StduyOpenCV/src/python/workspace/test.proj
   工作流数量: 1
============================================================

📁 创建临时目录: C:\Users\xxx\AppData\Local\Temp\proj_export_xxx
📁 创建工作流目录: C:\Users\xxx\AppData\Local\Temp\proj_export_xxx\workflows

--- 处理工作流 1: 工作流 1 ---
💾 保存节点图到: C:\Users\xxx\AppData\Local\Temp\proj_export_xxx\workflows\workflow_1.json
   📊 节点图数据大小: 12345 bytes
   🔢 节点数量: 5
   ✅ 文件已生成，大小: 12345 bytes

📝 生成索引文件...
   ✅ 索引文件已生成
📝 保存工程配置...
   ✅ 工程配置已保存

🗜️  压缩为ZIP文件...
   📦 添加文件: index.json
   📦 添加文件: project.json
   📦 添加文件: workflows/workflow_1.json
   ✅ 共压缩 3 个文件
🧹 清理临时目录

============================================================
✅ 工程导出成功!
   文件: D:/example/projects/StduyOpenCV/src/python/workspace/test.proj
   大小: 8192 bytes (8.00 KB)
============================================================
```

#### 常见问题及解决方案

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 节点数量为 0 | 工作流中没有添加节点 | 先添加节点再保存 |
| 文件大小为 0 | serialize_session() 返回空数据 | 检查 NodeGraph 是否有内容 |
| 文件未生成 | 路径错误或权限问题 | 检查临时目录权限 |
| ZIP 压缩失败 | 文件被占用或损坏 | 关闭其他程序，重试 |

---

### 思路 2: 检查打开 proj 文件是否正常

#### 关键检查点

1. **ZIP 解压是否成功**
   - 文件列表是否正确
   - 所有文件是否都解压到临时目录

2. **工程配置读取是否正确**
   - project.json 是否存在且格式正确
   - 工作流元数据是否正确加载

3. **节点图数据预加载是否成功**
   - workflow_*.json 文件是否被正确读取
   - JSON 数据是否完整
   - 节点数量和类型是否正确

4. **UI 标签页创建是否成功**
   - NodeGraph 实例是否创建
   - deserialize_session() 是否成功
   - 节点是否正确反序列化
   - 标签页是否添加到 tab_widget

#### 预期日志输出示例

```
============================================================
📂 UI: 开始打开工程流程
============================================================

📄 用户选择文件: D:/example/projects/StduyOpenCV/src/python/workspace/test.proj

🗑️ 关闭当前工程...
   🧹 清空标签页 (之前有 1 个)

📂 开始打开工程: D:/example/projects/StduyOpenCV/src/python/workspace/test.proj

============================================================
📂 开始导入工程
   文件路径: D:/example/projects/StduyOpenCV/src/python/workspace/test.proj
============================================================

📊 文件大小: 8192 bytes (8.00 KB)
📁 创建临时目录: C:\Users\xxx\AppData\Local\Temp\proj_import_xxx
🗜️  解压ZIP文件...
   📦 ZIP包含 3 个文件:
      - index.json
      - project.json
      - workflows/workflow_1.json
   ✅ 解压完成

📝 读取工程配置...
   ✅ 工程名称: 默认工程
   ✅ 工作流数量: 1
      [1] 工作流 1

📦 预加载工作流节点图数据...
   📁 找到 1 个工作流文件

   --- 加载工作流 1: workflow_1.json ---
   📊 文件大小: 12345 bytes
   🔢 节点数量: 5
   🏷️  节点类型: io_camera.ImageLoadNode, preprocessing.GrayscaleNode, ...
   ✅ 预加载成功

============================================================
✅ 工程导入成功!
   工作流数量: 1
   预加载节点图数据: 1 个
============================================================


✅ 工程数据加载成功: 默认工程
   工作流数量: 1
   预加载的工作流数据: 1 个

🏗️  开始创建工作流标签页...

--- 处理工作流 1/1: 工作流 1 ---
   🔨 创建新的 NodeGraph 实例
   📥 尝试反序列化节点图数据...
   ✅ 加载工作流: 工作流 1 (5 个节点)
   📋 节点列表:
      - 加载图像 (io_camera.ImageLoadNode)
      - 灰度化 (preprocessing.GrayscaleNode)
      - ...
   🔗 连接信号...
   📑 添加标签页到UI...
   📊 add_workflow_tab_to_ui 被调用
      工作流名称: 工作流 1
      NodeGraph 是否存在: True
      🖼️  获取 Graph Widget: <NodeGraphQt.widgets.node_graph.NodeGraphWidget object at 0x...>
      ➕ 添加标签页: '工作流 1'
      ✅ 标签页索引: 0
      📑 当前标签页总数: 1
   ✅ 标签页添加完成

🎯 激活第一个工作流...
   ✅ 激活完成

📋 添加到最近工程列表...

============================================================
✅ 工程打开流程完成!
============================================================
```

#### 常见问题及解决方案

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| 预加载数据为 0 | workflows 目录不存在或为空 | 检查保存时是否正确生成工作流文件 |
| 节点数量为 0 | JSON 文件中没有 nodes 字段 | 检查保存的 JSON 数据结构 |
| deserialize_session 失败 | JSON 格式错误或节点类型未注册 | 检查插件是否正确加载 |
| 标签页不显示 | tab_widget.addTab 未被调用 | 检查 add_workflow_tab_to_ui 是否被执行 |
| 中央区域空白 | NodeGraph widget 未正确添加 | 检查 graph_widget 是否有效 |

---

## 🔍 诊断步骤

### 步骤 1: 验证保存功能

1. 启动应用
2. 在工作流中添加至少一个节点（例如"加载图像"）
3. 保存工程为 test_save.proj
4. 观察终端输出，确认：
   - ✅ 节点数量 > 0
   - ✅ 文件大小 > 1KB
   - ✅ 所有文件都被压缩到 ZIP

### 步骤 2: 验证打开功能

1. 关闭当前工程（或直接重启应用）
2. 打开刚才保存的 test_save.proj
3. 观察终端输出，确认：
   - ✅ ZIP 解压成功，文件列表正确
   - ✅ 预加载节点图数据成功
   - ✅ 节点数量与保存时一致
   - ✅ 标签页成功添加
   - ✅ 中央区域显示节点图

### 步骤 3: 对比分析

如果保存正常但打开后无显示，重点检查：

1. **预加载数据是否正确传递**
   ```python
   workflows_session_data = getattr(project, '_workflows_session_data', {})
   print(f"预加载数据数量: {len(workflows_session_data)}")
   ```

2. **deserialize_session 是否成功**
   ```python
   node_graph.deserialize_session(session_data)
   node_count = len(node_graph.all_nodes())
   print(f"反序列化后节点数量: {node_count}")
   ```

3. **NodeGraph widget 是否正确添加到 UI**
   ```python
   tab_index = self.main_window.tab_widget.addTab(graph_widget, tab_title)
   print(f"标签页索引: {tab_index}, 总数: {self.main_window.tab_widget.count()}")
   ```

---

## 🛠️ 调试技巧

### 1. 启用 Python 断点

在关键位置添加断点：
```python
import pdb; pdb.set_trace()
```

### 2. 检查 NodeGraph 状态

```python
# 检查节点数量
print(f"节点数量: {len(node_graph.all_nodes())}")

# 检查节点类型
for node in node_graph.all_nodes():
    print(f"  - {node.name()}: {node.type_}")

# 检查序列化数据
session_data = node_graph.serialize_session()
print(f"序列化数据键: {session_data.keys()}")
```

### 3. 检查 UI 组件状态

```python
# 检查标签页数量
print(f"标签页数量: {tab_widget.count()}")

# 检查当前标签页
current_index = tab_widget.currentIndex()
print(f"当前标签页索引: {current_index}")

# 检查标签页 widget
if current_index >= 0:
    widget = tab_widget.widget(current_index)
    print(f"当前标签页 widget: {widget}")
```

---

## 📝 修改记录

### 2026-04-27

1. **增强 export_project 日志** (`project_manager.py`)
   - 添加文件大小统计
   - 记录每个工作流的节点数量和类型
   - 验证文件是否成功生成
   - 记录 ZIP 压缩的文件列表

2. **增强 import_project 日志** (`project_manager.py`)
   - 记录 ZIP 文件内容和大小
   - 详细记录每个工作流文件的加载过程
   - 统计节点数量和类型
   - 验证预加载数据完整性

3. **增强 open_project_from_ui 日志** (`project_ui_manager.py`)
   - 跟踪 UI 层面的打开流程
   - 记录标签页创建过程
   - 验证节点反序列化结果
   - 列出所有加载的节点

4. **增强 add_workflow_tab_to_ui 日志** (`project_ui_manager.py`)
   - 记录 NodeGraph 创建过程
   - 验证 widget 是否正确获取
   - 记录标签页添加结果

---

## ✅ 验收标准

工程文件保存和打开功能正常的标志：

- [ ] 保存时终端显示详细的进度信息
- [ ] 保存的文件大小合理（> 1KB，如果有节点）
- [ ] 打开时终端显示详细的加载过程
- [ ] 预加载的节点图数据数量与工作流数量一致
- [ ] 反序列化后的节点数量与保存时一致
- [ ] 标签页成功添加到 tab_widget
- [ ] 中央区域正确显示节点图
- [ ] 节点可以正常编辑和操作

---

**下一步**: 根据实际运行时的日志输出，定位具体问题所在。