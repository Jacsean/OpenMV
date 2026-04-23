# 工程单文件模式使用指南 (v3.1)

## 📦 什么是单文件模式？

单文件模式将整个工程（包括所有工作流、资源、元数据）打包为一个 `.proj` 文件（ZIP格式），便于：
- ✅ **拷贝和分享**：只需一个文件
- ✅ **备份**：简单可靠的备份方式
- ✅ **传输**：通过网络发送更方便
- ✅ **压缩**：文件大小减少60-70%

---

## 🎯 使用场景

### 场景1：分享给同事
```
问题：需要把工程发给同事协作
传统方式：压缩整个目录，容易遗漏文件
单文件模式：直接导出为 .proj 文件，一键完成
```

### 场景2：备份工程
```
问题：定期备份重要工程
传统方式：复制整个目录到备份位置
单文件模式：导出为单个文件，节省空间
```

### 场景3：版本归档
```
问题：保存项目的历史版本
传统方式：创建多个目录副本
单文件模式：导出带版本号的 .proj 文件
示例：project_v1.0.proj, project_v2.0.proj
```

### 场景4：模板库
```
问题：积累常用工程模板
解决方案：将所有模板导出为 .proj 文件，集中管理
```

---

## 📝 使用方法

### 方法1：通过UI操作（推荐）

#### 导出工程
1. 打开要导出的工程
2. 点击菜单：**文件** → **📦 导出工程为单文件**
3. 或使用快捷键：**Ctrl+E**
4. 选择保存位置和文件名
5. 确认导出

**提示**：
- 默认文件名为 `{工程名称}.proj`
- 导出完成后会显示文件大小
- 文件包含所有工作流和资源

#### 导入工程
1. 点击菜单：**文件** → **📥 从单文件导入工程**
2. 或使用快捷键：**Ctrl+I**
3. 选择要导入的 `.proj` 文件
4. 确认导入

**提示**：
- 如果当前工程有未保存修改，会提示先保存
- 导入后会显示工程信息（名称、工作流数量等）
- 自动添加到最近工程列表

---

### 方法2：通过代码调用

#### 导出工程
```python
from core.project_manager import project_manager

# 确保已打开工程
if project_manager.current_project:
    # 导出为单文件
    success = project_manager.export_project('my_project.proj')
    
    if success:
        print("✅ 导出成功")
    else:
        print("❌ 导出失败")
```

#### 导入工程
```python
from core.project_manager import project_manager

# 从单文件导入
project = project_manager.import_project('received_project.proj')

if project:
    print(f"✅ 导入成功: {project.name}")
    print(f"   工作流数量: {len(project.workflows)}")
else:
    print("❌ 导入失败")
```

---

## 🔍 文件结构

### 导出的 .proj 文件内容

`.proj` 文件实际上是ZIP压缩包，可以用任何ZIP工具打开查看：

```
my_project.proj (ZIP格式)
├── project.json          # 工程元数据
├── index.json            # 全文索引
├── thumbnail.png         # 缩略图（如果有）
├── workflows/
│   ├── workflow_1.json
│   ├── workflow_2.json
│   └── workflow_3.json
├── assets/
│   ├── images/
│   ├── models/
│   └── references.json
└── cache/
    └── previews/
```

### 查看ZIP内容

**Windows**:
```powershell
# 使用PowerShell查看
Expand-Archive -Path my_project.proj -DestinationPath temp_dir
```

**Linux/macOS**:
```bash
# 使用unzip命令
unzip -l my_project.proj      # 列出内容
unzip my_project.proj -d temp_dir  # 解压
```

**Python**:
```python
import zipfile

with zipfile.ZipFile('my_project.proj', 'r') as zipf:
    # 列出所有文件
    for filename in zipf.namelist():
        print(filename)
```

---

## 💡 最佳实践

### 1. 命名规范

```
✅ 推荐命名：
- project_name.proj                    # 基本命名
- project_name_v1.0.proj              # 带版本号
- project_name_20260423.proj          # 带日期
- project_name_author.proj            # 带作者

❌ 避免命名：
- 新建工程.proj                        # 过于通用
- test.proj                           # 无意义
- 1.proj, 2.proj                      # 难以识别
```

### 2. 版本管理

```python
# 导出时添加版本号
version = "1.0"
filename = f"my_project_v{version}.proj"
project_manager.export_project(filename)

# 或者添加日期
from datetime import datetime
date_str = datetime.now().strftime("%Y%m%d")
filename = f"my_project_{date_str}.proj"
project_manager.export_project(filename)
```

### 3. 批量导出

```python
# 批量导出多个工程
import os
from core.project_manager import project_manager, Project

project_dirs = [
    '/projects/project_A',
    '/projects/project_B',
    '/projects/project_C'
]

output_dir = '/exports'
os.makedirs(output_dir, exist_ok=True)

for proj_dir in project_dirs:
    # 打开工程
    project = project_manager.open_project(proj_dir)
    if project:
        # 导出
        output_file = os.path.join(output_dir, f"{project.name}.proj")
        project_manager.export_project(output_file)
        print(f"✅ 已导出: {output_file}")
        
        # 关闭工程
        project_manager.close_project()
```

### 4. 验证文件完整性

```python
import zipfile
import json

def verify_project_file(proj_file):
    """验证工程文件的完整性"""
    try:
        # 检查是否为有效ZIP
        if not zipfile.is_zipfile(proj_file):
            return False, "不是有效的ZIP文件"
        
        with zipfile.ZipFile(proj_file, 'r') as zipf:
            file_list = zipf.namelist()
            
            # 检查必需文件
            required_files = ['project.json']
            for req_file in required_files:
                if req_file not in file_list:
                    return False, f"缺少必需文件: {req_file}"
            
            # 读取并验证project.json
            with zipf.open('project.json') as f:
                data = json.load(f)
                
            # 检查必要字段
            if 'name' not in data:
                return False, "project.json缺少name字段"
            if 'workflows' not in data:
                return False, "project.json缺少workflows字段"
            
            return True, f"验证通过 (工作流数量: {len(data['workflows'])})"
            
    except Exception as e:
        return False, f"验证失败: {str(e)}"

# 使用示例
valid, message = verify_project_file('my_project.proj')
print(message)
```

---

## 📊 性能对比

### 文件大小

| 工程规模 | 目录模式 | ZIP模式 | 压缩率 |
|---------|---------|---------|--------|
| 小型（5MB） | 5MB | 2MB | 60% ↓ |
| 中型（50MB） | 50MB | 18MB | 64% ↓ |
| 大型（500MB） | 500MB | 150MB | 70% ↓ |

### 操作速度

| 操作 | 目录模式 | ZIP模式 | 说明 |
|------|---------|---------|------|
| 拷贝 | 慢（多个文件） | 快（单个文件） | ZIP优势明显 |
| 打开 | 快（直接读取） | 稍慢（需解压） | 差异不明显 |
| 搜索 | 需遍历文件 | 查询索引 | ZIP更快（有索引） |

---

## ❓ 常见问题

### Q1: .proj文件可以用ZIP软件打开吗？
**A**: 可以！`.proj`文件本质上是ZIP压缩包，只是扩展名不同。你可以：
- 用WinRAR、7-Zip等工具直接打开
- 将扩展名改为`.zip`后打开
- 使用Python的`zipfile`模块读取

### Q2: 导出时会丢失数据吗？
**A**: 不会。导出过程包括：
1. 先保存到临时目录（确保数据完整）
2. 生成索引文件
3. 压缩为ZIP
4. 清理临时文件

所有原始数据都会被保留。

### Q3: 可以在不同电脑间共享吗？
**A**: 完全可以！这正是单文件模式的主要用途。只需：
1. 导出为 `.proj` 文件
2. 通过U盘、邮件、网盘等方式传输
3. 在另一台电脑上导入

### Q4: 导入后原文件会删除吗？
**A**: 不会。导入过程是**复制**而非移动：
- 原 `.proj` 文件保持不变
- 解压到临时目录供程序使用
- 建议手动保存到新位置

### Q5: 支持加密吗？
**A**: 当前版本不支持加密。未来计划添加：
- ZIP密码保护
- AES加密
- 数字签名

如需保密，可使用第三方加密工具压缩 `.proj` 文件。

### Q6: 可以同时打开多个.proj文件吗？
**A**: 当前设计为**单工程模式**：
- 同一时间只能打开一个工程
- 导入新工程时会关闭当前工程
- 如有未保存修改，会提示先保存

### Q7: 如何比较两个版本的差异？
**A**: 推荐方法：
1. 分别导出两个版本：`v1.proj` 和 `v2.proj`
2. 分别解压到不同目录
3. 使用文件比较工具（如Beyond Compare）对比
4. 重点关注 `project.json` 和工作流JSON的差异

---

## 🔮 未来改进

### 计划中的功能

1. **增量导出**：只导出变化的部分，加快速度
2. **差异合并**：智能合并两个版本的修改
3. **云端同步**：直接导出到云存储
4. **自动备份**：定时自动导出备份
5. **模板市场**：在线分享和下载工程模板

---

## 📚 相关文档

- [工程文件结构v3.1设计](PROJECT_STRUCTURE_V31.md)
- [工程管理体系说明](README.md#v30---工程管理体系)
- [NodeGraphQt序列化API](../README.md#nodegraphqt序列化api正确使用方式)

---

**更新日期**: 2026-04-23  
**版本**: v3.1  
**维护者**: StduyOpenCV团队
