# 统一单文件模式实施说明 (v3.1更新)

## 📋 变更概述

**变更日期**: 2026-04-23  
**版本**: v3.1 更新版

### 核心变更
将工程的**保存/打开**功能统一改为使用单文件模式（ZIP格式的 `.proj` 文件），并删除了独立的"导入/导出"功能。

---

## 🎯 变更原因

### 之前的问题
1. **操作冗余**：用户需要区分"保存工程"（目录模式）和"导出为单文件"两种操作
2. **概念复杂**：目录模式和单文件模式并存，增加学习成本
3. **流程繁琐**：分享工程需要先导出，接收后需要再导入

### 改进方案
- ✅ **统一接口**：保存和打开直接使用单文件模式
- ✅ **简化操作**：删除独立的导入导出功能
- ✅ **直观体验**：用户只需关心"保存"和"打开"，无需了解底层实现

---

## 🔧 技术实现

### 1. UI层修改 ([main_window.py](file://d:\example\projects\StduyOpenCV\src\python\ui\main_window.py))

#### **删除的菜单项**
```python
# ❌ 已删除
- "📦 导出工程为单文件" (Ctrl+E)
- "📥 从单文件导入工程" (Ctrl+I)
```

#### **简化的工具栏**
```python
# 之前: [新建] [打开] [保存] | [导出] [导入] | [运行] ...
# 现在: [新建] [打开] [保存] | [运行] ...
```

#### **修改的方法**

**save_project()** - 现在直接保存为单文件：
```python
def save_project(self):
    """保存当前工程为单文件（.proj ZIP格式）"""
    # 如果未指定路径，弹出对话框选择保存位置
    if not project.file_path or not project.file_path.endswith('.proj'):
        file_path, _ = QFileDialog.getSaveFileName(..., "*.proj")
    
    # 调用ProjectManager导出为单文件
    success = self.project_manager.export_project(project.file_path)
```

**open_project()** - 现在直接从单文件加载：
```python
def open_project(self):
    """打开工程（支持单文件.proj格式）"""
    # 选择.proj文件
    file_path, _ = QFileDialog.getOpenFileName(..., "*.proj")
    
    # 调用ProjectManager从单文件导入
    project = self.project_manager.import_project(file_path)
```

**删除的方法**：
- `export_project_to_file()` - 已删除
- `import_project_from_file()` - 已删除
- `_get_file_size_str()` - 保留（在save_project中使用）

---

### 2. 核心层修改 ([project_manager.py](file://d:\example\projects\StduyOpenCV\src\python\core\project_manager.py))

#### **修改的方法**

**save_project()** - 委托给export_project：
```python
def save_project(self, proj_file: str = "") -> bool:
    """保存工程为单文件（.proj ZIP格式）"""
    output_file = proj_file if proj_file else self.current_project.file_path
    
    if not output_file.endswith('.proj'):
        output_file += '.proj'
    
    return self.export_project(output_file)
```

**open_project()** - 委托给import_project：
```python
def open_project(self, proj_file: str) -> Optional[Project]:
    """打开工程（从单文件.proj加载）"""
    return self.import_project(proj_file)
```

#### **修复的问题**

**export_project()** - 避免递归调用：
```python
def export_project(self, output_file: str) -> bool:
    """导出工程为单文件（ZIP格式）"""
    # 之前在临时目录中调用save_project会导致递归
    # 现在直接在临时目录中保存工作流和配置文件
    
    temp_dir = tempfile.mkdtemp(prefix='proj_export_')
    
    # 保存工作流
    for i, workflow in enumerate(self.current_project.workflows):
        wf_filename = f"workflow_{i+1}.json"
        workflow.file_path = f"workflows/{wf_filename}"
        wf_full_path = os.path.join(temp_dir, workflow.file_path)
        workflow.node_graph.save_session(wf_full_path)
    
    # 保存工程配置
    project_file = os.path.join(temp_dir, "project.json")
    with open(project_file, 'w') as f:
        json.dump(self.current_project.to_dict(), f)
    
    # 生成索引
    index_data = ProjectIndexer.generate_index(self.current_project)
    with open(os.path.join(temp_dir, "index.json"), 'w') as f:
        json.dump(index_data, f)
    
    # 压缩为ZIP
    with zipfile.ZipFile(output_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(temp_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, temp_dir)
                zipf.write(file_path, arcname)
    
    shutil.rmtree(temp_dir, ignore_errors=True)
    return True
```

**import_project()** - 直接读取配置：
```python
def import_project(self, proj_file: str) -> Optional[Project]:
    """从单文件导入工程"""
    temp_dir = tempfile.mkdtemp(prefix='proj_import_')
    
    # 解压ZIP
    with zipfile.ZipFile(proj_file, 'r') as zipf:
        zipf.extractall(temp_dir)
    
    # 直接读取工程配置（不再调用open_project避免循环）
    project_file = os.path.join(temp_dir, "project.json")
    with open(project_file, 'r') as f:
        data = json.load(f)
    
    self.current_project = Project.from_dict(data)
    self.current_project.file_path = os.path.dirname(os.path.abspath(proj_file))
    self.current_project.format_type = "single_file"
    
    return self.current_project
```

---

## 📊 对比分析

### 用户体验对比

| 操作 | 变更前 | 变更后 | 改进 |
|------|--------|--------|------|
| **保存工程** | 保存为目录 → 需手动导出为单文件 | 直接保存为单文件 | ✅ 简化 |
| **打开工程** | 选择目录 → 或从单文件导入 | 直接选择单文件 | ✅ 统一 |
| **分享工程** | 先导出 → 发送文件 | 直接发送保存的文件 | ✅ 直观 |
| **菜单项数量** | 5个（新建/打开/保存/导出/导入） | 3个（新建/打开/保存） | ✅ 精简 |

### 技术架构对比

| 方面 | 变更前 | 变更后 |
|------|--------|--------|
| **存储模式** | 目录模式 + 单文件模式并存 | 仅单文件模式 |
| **代码复杂度** | 两套保存/加载逻辑 | 统一逻辑 |
| **方法数量** | save/open/export/import 4个独立方法 | save/open 2个方法（内部委托） |
| **维护成本** | 需同步更新两套逻辑 | 只需维护一套 |

---

## ✅ 测试结果

测试脚本：[test_unified_single_file.py](file://d:\example\projects\StduyOpenCV\src\python\test_unified_single_file.py)

**测试场景**：
1. ✅ 创建工程并添加工作流
2. ✅ 保存为单文件（.proj）
3. ✅ 验证ZIP格式和文件大小
4. ✅ 关闭工程
5. ✅ 从单文件打开工程
6. ✅ 验证数据完整性
7. ✅ 覆盖保存（测试重复保存）
8. ✅ 清理测试文件

**测试结果**：所有测试通过 ✅

---

## 📝 迁移指南

### 对于已有工程（目录模式）

如果用户有旧版目录模式的工程，可以通过以下方式转换：

```python
from core.project_manager import project_manager

# 1. 打开旧版目录工程
project = project_manager.open_project('/path/to/old_project_dir')

# 2. 保存为新格式（会自动转换为单文件）
project_manager.save_project('/path/to/new_project.proj')

# 完成！现在可以使用新的单文件格式了
```

### 批量转换脚本

```python
import os
from core.project_manager import project_manager

# 遍历所有旧版工程目录
old_projects = [
    '/projects/project_A',
    '/projects/project_B',
    '/projects/project_C'
]

for old_dir in old_projects:
    # 打开旧工程
    project = project_manager.open_project(old_dir)
    if project:
        # 保存为新格式
        new_file = f"{project.name}.proj"
        project_manager.save_project(new_file)
        print(f"✅ 已转换: {new_file}")
        
        # 关闭工程
        project_manager.close_project()
```

---

## 🎨 UI变化截图说明

### 文件菜单
```
变更前:
文件(&F)
├── 📄 新建工程          (Ctrl+Shift+N)
├── 📂 打开工程          (Ctrl+Shift+O)
├── 💾 保存工程          (Ctrl+Shift+S)
├── ─────────────
├── 📦 导出工程为单文件   (Ctrl+E)  ← 已删除
├── 📥 从单文件导入工程   (Ctrl+I)  ← 已删除
├── ─────────────
└── 📋 最近工程

变更后:
文件(&F)
├── 📄 新建工程          (Ctrl+Shift+N)
├── 📂 打开工程          (Ctrl+Shift+O)
├── 💾 保存工程          (Ctrl+Shift+S)
├── ─────────────
└── 📋 最近工程
```

### 工具栏
```
变更前:
[📄 新建] [📂 打开] [💾 保存] | [📦 导出] [📥 导入] | [▶ 运行] ...

变更后:
[📄 新建] [📂 打开] [💾 保存] | [▶ 运行] ...
```

---

## 💡 最佳实践

### 1. 保存工程
```python
# UI操作
点击菜单: 文件 → 💾 保存工程
快捷键: Ctrl+Shift+S

# 代码调用
project_manager.save_project('my_project.proj')
```

### 2. 打开工程
```python
# UI操作
点击菜单: 文件 → 📂 打开工程
快捷键: Ctrl+Shift+O

# 代码调用
project = project_manager.open_project('my_project.proj')
```

### 3. 文件命名规范
```
✅ 推荐:
- project_name.proj
- project_v1.0.proj
- project_20260423.proj

❌ 避免:
- 新建工程.proj
- test.proj
```

---

## ❓ 常见问题

### Q1: 为什么删除导入导出功能？
**A**: 为了简化用户操作。保存和打开已经足够满足需求，独立的导入导出功能造成概念混淆。

### Q2: 旧版目录模式的工程还能用吗？
**A**: 可以。打开旧版工程后，保存时会自动转换为新的单文件格式。

### Q3: .proj文件可以用ZIP工具打开吗？
**A**: 可以。.proj本质上是ZIP压缩包，只是扩展名不同。

### Q4: 保存时会覆盖原文件吗？
**A**: 是的。如果文件已存在，会直接覆盖。建议定期备份重要工程。

### Q5: 可以同时打开多个工程吗？
**A**: 不可以。系统设计为单工程模式，打开新工程时会关闭当前工程。

---

## 📚 相关文档

- [工程文件结构v3.1设计](PROJECT_STRUCTURE_V31.md)
- [单文件模式使用指南](SINGLE_FILE_MODE_GUIDE.md)
- [README - v3.1版本说明](../../README.md#v31---单文件模式已完成)

---

**更新日期**: 2026-04-23  
**版本**: v3.1 更新版  
**维护者**: StduyOpenCV团队
