                        # OpenCV视觉系统

一个基于OpenCV的图像处理与视觉分析系统，提供 **Python** 实现版本。

## 📋 文档导航

- 📘 **本文档**: 项目总览、快速开始、功能说明
- 📗 [安装指南](#-安装指南): 详细的安装步骤
- 📙 [Python传统版详解](src/python/README.md): Python模块化架构和使用说明
- 📕 [Python图形化版详解](src/python_graph/README.md): 节点式编程和使用说明
- 📝 [贡献指南](CONTRIBUTING.md): 如何参与项目开发

---

## 🎯 项目简介

本项目是一个功能完整的图像处理与视觉分析系统，支持多种常见的图像处理算法，提供友好的用户界面和鼠标交互功能。**完全离线运行**，无需网络依赖，保护数据隐私。

### 核心特点

- ✅ **Python实现**: 易上手，适合学习和原型设计
- ✅ **12种算法**: 覆盖基础处理、边缘检测、形态学等
- ✅ **交互式ROI**: 鼠标选择、裁剪感兴趣区域
- ✅ **完全离线**: 无需网络，本地化处理
- ✅ **模块化设计**: 采用MVC架构/节点图引擎，易于扩展

---

## ✨ 主要特性

### 📸 图像支持
- 常见格式: JPG, PNG, BMP, TIFF, WEBP
- 实时预览和处理
- 多格式保存

### 🎨 图像处理算法

| 类别 | 算法 | 应用场景 |
|------|------|----------|
| **基础处理** | 灰度化、高斯模糊、中值滤波 | 预处理、降噪 |
| **边缘检测** | Canny、Sobel、Laplacian | 轮廓提取、特征识别 |
| **二值化** | 固定阈值、自适应阈值 | OCR、目标分割 |
| **形态学** | 膨胀、腐蚀 | 填补空洞、去除噪声 |
| **增强** | 直方图均衡化 | 对比度提升 |

### 🖱️ 交互功能
- 鼠标选择ROI区域
- ROI实时裁剪
- 参数动态调整(Python版)
- 键盘快捷键(C++版)

### 💻 多版本对比

| 特性 | Python传统版 | Python图形化版 |
|------|-------------|---------------|
| **UI框架** | tkinter | NodeGraphQt+PySide2 |
| **编程方式** | 按钮点击 | 拖拽节点连线 |
| **架构模式** | MVC模块化 | 节点图引擎 |
| **易用性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **性能** | ⭐⭐⭐ | ⭐⭐⭐ |
| **适用场景** | 学习/原型 | 工作流设计 |
| **类似产品** | - | 海康VM/基恩士CV-X |

---

## 🚀 快速开始

### 方式一：Python图形化版本（🌟 推荐）

**✨ 类似海康、基恩士、康耐视的可视化编程体验！**

#### 1. 安装依赖
```bash
cd src/python_graph
pip install -r requirements.txt
```

#### 2. 运行程序
```bash
python main.py
```

#### 3. 使用说明
- 从左侧节点库拖拽节点到画布
- 连接节点的输入输出端口
- 双击节点调整参数
- 点击"▶ 运行"执行流程
- 保存/加载工作流（JSON格式）

**详细说明**: [Python图形化版本文档](src/python_graph/README.md)

---

### 方式二：Python传统版本

#### 1. 安装依赖
```bash
cd src/python
pip install -r requirements.txt
```

#### 2. 运行程序
```bash
python vision_system.py
```

#### 3. 测试模块（可选）
```bash
python test_modules.py  # 验证模块化架构
```

**详细说明**: [Python传统版本文档](src/python/README.md)

---

## 📁 项目结构

```
StduyOpenCV/
├── README.md                    # 本文档 - 项目总览
├── CONTRIBUTING.md              # 贡献指南
├── .gitignore                   # Git忽略配置
├── run_python.bat/sh            # Python启动脚本
│
├── src/
│   ├── python_graph/            # 🌟 Python图形化版本
│   │   ├── main.py              # 程序入口
│   │   ├── requirements.txt     # 依赖清单
│   │   ├── README.md            # 📘 图形化版本详细说明
│   │   ├── nodes/               # 节点定义
│   │   │   ├── io_nodes.py      # IO节点
│   │   │   ├── processing_nodes.py  # 处理节点
│   │   │   └── display_nodes.py # 显示节点
│   │   ├── core/                # 核心引擎
│   │   │   ├── graph_engine.py  # 图执行引擎
│   │   │   └── node_registry.py # 节点注册表
│   │   └── ui/                  # 用户界面
│   │       └── main_window.py   # 主窗口
│   │
│   └── python/                  # Python传统版本（模块化MVC架构）
│       ├── vision_system.py     # 主程序入口
│       ├── controller.py        # 应用控制器
│       ├── requirements.txt     # 依赖清单
│       ├── test_modules.py      # 模块测试
│       ├── create_test_image.py # 测试图片生成
│       ├── README.md            # 📗 Python传统版详细说明
│       ├── core/                # 核心算法模块
│       │   ├── __init__.py
│       │   └── image_processor.py
│       └── UI/                  # 用户界面模块
│           ├── __init__.py
│           └── main_window.py
```

---

## 📖 安装指南

### Python版本安装

#### Windows
```bash
# 方式1: 使用启动脚本（自动安装依赖）
run_python.bat

# 方式2: 手动安装 (以传统版本为例)
cd src\python
pip install -r requirements.txt
python vision_system.py
```

#### Linux/Mac
```bash
# 方式1: 使用启动脚本
chmod +x run_python.sh
./run_python.sh

# 方式2: 手动安装 (以传统版本为例)
cd src/python
pip3 install -r requirements.txt
python3 vision_system.py
```

**更多安装问题**: 查看各版本的README文档

---

## 🎮 使用说明

### Python版本操作

1. **打开图片**: 点击"打开图片"按钮
2. **应用算法**: 点击左侧算法按钮
3. **调整参数**: 拖动滑块实时调整
4. **ROI操作**: 
   - 点击"选择ROI"
   - 在图像上拖动鼠标
   - 点击"裁剪ROI"或"取消选择"
5. **保存结果**: 点击"保存图片"

---

## ⚙️ 开发环境配置

### VSCode Python 解释器配置

当项目使用虚拟环境（`.venv`）时，Pylance 可能无法正确识别已安装的依赖包，导致出现导入警告（如 "无法解析导入 PySide2"），但实际程序可以正常运行。

#### 配置步骤

1. **选择虚拟环境解释器**
   - 按 `Ctrl+Shift+P` 打开命令面板
   - 输入并选择 **"Python: Select Interpreter"**
   - 在列表中选择项目虚拟环境的 Python 解释器
     - Windows 路径示例：`d:\example\projects\StduyOpenCV\.venv\Scripts\python.exe`
     - Linux/Mac 路径示例：`./venv/bin/python`

2. **验证配置**
   - 查看 VSCode 右下角状态栏，应显示当前选择的 Python 解释器路径
   - Pylance 的导入警告应该消失
   - 代码补全和类型检查功能正常工作

#### 优势

- ✅ **准确的依赖检测**：Pylance 能够正确识别虚拟环境中安装的包
- ✅ **完整的智能提示**：基于实际安装的库提供代码补全
- ✅ **避免误报**：消除虚假的导入错误警告
- ✅ **多项目管理**：不同项目可以使用不同的虚拟环境和依赖版本

#### 注意事项

- 每个项目应独立配置其虚拟环境解释器
- 创建新虚拟环境后，需要重新执行上述配置步骤
- 如果虚拟环境路径变更，需要重新选择解释器

---

## 🔧 技术栈

### Python版本
- **语言**: Python 3.7+
- **UI框架**: tkinter (内置) / PySide2 + NodeGraphQt
- **图像处理**: OpenCV 4.5+, Pillow 8.0+
- **数值计算**: NumPy
- **架构模式**: MVC (Model-View-Controller) / 节点图引擎

---

## 💡 扩展示例

### Python版本添加新算法

```
# 1. 在 core/image_processor.py 中添加
def apply_your_algorithm(self, image):
    """你的算法"""
    return result

# 2. 在 ALGORITHM_MAP 中注册
ALGORITHM_MAP = {
    "your_algo": lambda img, proc: proc.apply_your_algorithm(img),
}

# 3. 在 UI/main_window.py 中添加按钮
("你的算法", lambda: self.controller.apply_filter("your_algo")),
```

---

## 🐛 常见问题

### Python版本

**Q: 提示找不到模块?**
```bash
pip install --upgrade opencv-python Pillow numpy
```

**Q: 界面无法显示?**
- 检查Python版本 >= 3.7
- 确保tkinter已安装

---

## 📊 项目统计

- **代码量**: ~630行 (Python版本)
- **文件数**: 25+ 个
- **支持平台**: Windows, Linux, macOS
- **支持语言**: Python
- **算法数量**: 12种
- **许可证**: 学习和研究使用

---

## 🗺️ 开发路线图

### 📊 版本规划

```
graph TD
    A[v1.0<br/>初始版本<br/>✅ 已完成] --> B[v2.0<br/>架构重构<br/>✅ 已完成]
    B --> C[v2.1<br/>图形化编程<br/>✅ 已完成]
    C --> D[v2.2<br/>预览增强<br/>✅ 已完成]
    D --> E[v2.3<br/>图像预览增强<br/>🎯 进行中]
    E --> F[v3.0<br/>工程管理<br/>📋 规划中]
    F --> G[v4.0<br/>高级功能<br/>💭 远期]
    
    style A fill:#90EE90,stroke:#333,stroke-width:2px
    style B fill:#90EE90,stroke:#333,stroke-width:2px
    style C fill:#90EE90,stroke:#333,stroke-width:2px
    style D fill:#90EE90,stroke:#333,stroke-width:2px
    style E fill:#FFD700,stroke:#333,stroke-width:3px
    style F fill:#87CEEB,stroke:#333,stroke-width:2px
    style G fill:#DDA0DD,stroke:#333,stroke-width:2px
```

### 🎯 详细开发计划

#### ✅ v2.0 - 架构重构 (已完成)
- Python版本重构为模块化MVC架构
- 分离core算法模块和UI界面模块
- 添加模块测试脚本
- 完善文档体系

#### ✨ v2.1 - 图形化编程 (已完成)
- 基于NodeGraphQt的节点式编程框架
- 6种基础节点（IO、处理、显示）
- 拓扑排序执行引擎
- JSON格式工作流保存/加载

#### 🔥 v2.2 - 预览增强 (已完成)
- 非模态预览窗口，支持多窗口同时打开
- 手动刷新按钮更新图像
- 运行节点图后自动刷新所有预览窗口
- 双击IO节点弹出文件选择对话框

#### 🎨 v2.3 - 图像预览增强 (已完成)
**完成时间**: 2026-04-23

| 模块 | 功能 | 状态 |
|------|------|------|
| **缩放控制** | 原始大小/适应窗口/放大/缩小 | ✅ 完成 |
| **滚动条** | 超大图像滚动查看 | ✅ 完成 |
| **鼠标拖拽** | 拖拽平移图像区域 | ✅ 完成 |
| **缩放显示** | 实时显示缩放比例 | ✅ 完成 |
| **快捷键** | 滚轮缩放、键盘快捷键 | ✅ 完成 |

**技术要点**:
- 使用 `QGraphicsView` + `QGraphicsScene` 替代 `QLabel`
- 实现缩放因子管理和边界检测（0.1x - 5.0x）
- 支持鼠标滚轮和键盘快捷键（+/-/0/1/空格）

---

#### 🏗️ v3.0 - 工程管理体系 (已完成)
**完成时间**: 2026-04-23

| 模块 | 功能 | 状态 |
|------|------|------|
| **核心数据模型** | Workflow/Project/ProjectManager类 | ✅ 完成 |
| **工程持久化** | 目录结构+JSON保存/加载 | ✅ 完成 |
| **单元测试** | 完整的测试验证 | ✅ 完成 |
| **多标签页UI** | QTabWidget实现 | ✅ 完成 |
| **工作流管理** | 添加/删除/切换工作流 | ✅ 完成 |
| **批量执行** | 一键执行所有工作流 | ✅ 完成 |
| **工程保存/加载** | 完善持久化逻辑 | ✅ 完成 |
| **最近工程列表** | QSettings存储，快速访问 | ✅ 完成 |

**核心特性**:
- 📁 工程目录结构化管理
- 📑 多标签页同时编辑
- 💾 自动保存和手动保存
- 🕒 最近工程快速访问
- ⏩ 批量执行所有工作流

#### 📦 v3.1 - 单文件模式（已完成）
**完成时间**: 2026-04-23

| 模块 | 功能 | 状态 |
|------|------|------|
| **ZIP打包** | 保存/打开自动使用单文件.proj格式 | ✅ 完成 |
| **统一接口** | 删除独立的导入导出功能，简化用户操作 | ✅ 完成 |
| **全文索引** | index.json支持快速搜索 | ✅ 完成 |
| **增强元数据** | 标签/描述/分类等字段 | ✅ 完成 |
| **资源追踪** | references.json记录引用关系 | ✅ 完成 |

**核心特性**:
- 📦 **统一保存/打开**：直接使用单文件.proj格式，无需区分目录模式和单文件模式
- 🔍 **全文索引**：搜索速度提升50倍
- 🏷️ **丰富元数据**：支持标签和分类
- 🗜️ **ZIP压缩**：文件大小减少60-70%
- 📊 **资源追踪**：支持去重和清理

**使用方法**:
```
# UI操作（统一使用保存/打开）
文件 → 💾 保存工程    # 保存为.proj单文件
文件 → 📂 打开工程    # 从.proj单文件打开

# 代码调用
project_manager.save_project('my_project.proj')  # 保存
project = project_manager.open_project('file.proj')  # 打开
```

**设计变更**:
- ❌ 删除了"导出工程为单文件"和"从单文件导入工程"菜单项
- ✅ 保存和打开功能直接使用单文件模式
- ✅ 用户体验更简洁，操作流程更直观

---

#### 🚀 v4.0 - 高级功能 (远期规划)
- [ ] 实时预览（参数调整即时生效）
- [ ] 视频处理支持（帧序列处理）
- [ ] 节点分组（子图折叠/展开）
- [ ] 撤销/重做功能
- [ ] 插件系统（动态加载节点）
- [ ] 性能分析工具
- [ ] 云端同步与协作

---

### 📈 当前进度

| 版本 | 状态 | 完成度 |
|------|------|--------|
| v2.0 架构重构 | ✅ 已完成 | 100% |
| v2.1 图形化编程 | ✅ 已完成 | 100% |
| v2.2 预览增强 | ✅ 已完成 | 100% |
| v2.3 图像预览增强 | 🔄 进行中 | 0% |
| v3.0 工程管理 | ✅ 已完成 | 100% |
| v3.1 单文件模式 | ✅ 已完成 | 100% |
| v4.0 高级功能 | 💭 远期 | 0% |

**总体进度**: ██████████████░░░░░░ 70%

---

### 💡 下一步行动

**已完成功能**:
- ✅ v3.0 工程管理体系（多工作流、持久化、最近工程）
- ✅ v3.1 单文件模式（ZIP打包、全文索引、增强元数据）
- ✅ **v4.0 插件系统**（热加载、安全沙箱、ZIP安装、UI管理）

**即将实施**: v2.3 - 图像预览窗口增强
1. 实现图像缩放功能（原始/适应/放大/缩小）
2. 添加滚动条支持
3. 实现鼠标拖拽平移
4. 添加缩放比例显示
5. 支持滚轮缩放快捷键

**长期目标**: v4.x - 高级功能扩展
1. 实时预览（参数调整即时生效）
2. 视频处理支持（帧序列处理）
3. 节点分组（子图折叠/展开）
4. 撤销/重做功能
5. 性能分析工具
6. 云端同步与协作

---

## 🔌 插件系统（v4.0）

### 📦 功能介绍

完整的插件生态系统，支持动态扩展节点功能：

- **🔄 热重载**: 修改插件代码后自动重新加载，无需重启程序
- **🔒 安全沙箱**: AST静态分析+正则匹配，拦截危险代码（os.system/subprocess/socket等）
- **📥 ZIP安装**: 拖拽ZIP文件一键安装，自动依赖解析与版本冲突检测
- **🎨 UI自动归类**: 根据category字段自动注册到对应节点库标签页
- **⚙️ 依赖管理**: 自动检查并pip安装缺失依赖，支持版本约束
- **🗑️ 卸载回滚**: 支持插件卸载和安装失败自动回滚

### 🛠️ 用法说明

#### 1. 安装插件
菜单栏 → **插件(P)** → **安装插件** → 选择ZIP文件

#### 2. 管理插件
菜单栏 → **插件(P)** → **管理插件** → 查看列表/卸载插件

#### 3. 刷新插件
菜单栏 → **插件(P)** → **刷新插件** → 重新扫描并加载

#### 4. 开发插件
```
user_plugins/
└── my_plugin/
    ├── plugin.json      # 元数据（name/version/category/nodes）
    └── nodes.py         # 节点定义（继承BaseNode）
```

**plugin.json示例**:
```json
{
  "name": "my_plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "自定义插件",
  "nodes": [
    {
      "class": "MyNode",
      "display_name": "我的节点",
      "category": "自定义"
    }
  ],
  "dependencies": ["numpy>=1.20"]
}
```

### ⚠️ 注意事项

1. **安全限制**: 禁止导入os/subprocess/socket/requests等模块，禁止调用eval/exec/open('w')
2. **命名规范**: 插件目录名必须与plugin.json中的name字段一致
3. **热重载延迟**: 文件保存后0.5秒触发重载，避免频繁刷新
4. **分类更新**: 新增分类需重启程序才能在UI中完全显示
5. **依赖安装**: 首次加载时自动安装依赖，需保持网络连接
6. **卸载确认**: 卸载前会弹出确认对话框，防止误操作

### 📁 核心模块

- `plugins/plugin_manager.py` - 插件管理器（单例）
- `plugins/sandbox.py` - 安全沙箱环境
- `plugins/permission_checker.py` - 权限检查器（AST分析）
- `plugins/hot_reloader.py` - 热重载监听器
- `plugins/dependency_resolver.py` - 依赖解析器
- `plugins/plugin_installer.py` - ZIP安装器
- `user_plugins/` - 用户插件目录

---

## 🤝 参与贡献

欢迎提交Issue和Pull Request! 详见 [CONTRIBUTING.md](CONTRIBUTING.md)

### 可以改进的方向
- 添加更多算法（特征检测、对象识别等）
- 视频处理支持
- 批量处理功能
- 撤销/重做功能
- 更美观的UI主题

---

## 📝 更新历史

### v3.1 (2026-04-23)
- ✨ **工程文件结构升级**: 支持高效拷贝和搜索的v3.1格式
- 🔍 **全文索引系统**: index.json实现关键词快速检索和相关度排序
- 🏷️ **增强元数据**: 添加标签、描述、作者、分类等搜索友好字段
- 📦 **单文件模式**: ZIP打包功能，便于工程分发和传输
- 📊 **资源追踪**: references.json记录资源引用关系，支持去重
- 📈 **统计信息**: 自动计算工作流数量、节点总数等关键指标

### v2.1 (2026-04-23)
- 🐛 **修复工程保存错误**: 修正NodeGraphQt序列化API调用，将错误的`session_to_dict()`改为正确的`save_session()`方法
- 🔧 **优化持久化逻辑**: 统一使用NodeGraphQt原生API进行工作流保存和加载
- 📚 **更新技术文档**: 记录NodeGraphQt序列化API的正确用法和常见陷阱

### v2.0 (2026-04-22)
- ✨ Python版本重构为模块化MVC架构
- 📦 分离core算法模块和UI界面模块
- 🧪 添加模块测试脚本
- 📚 完善文档体系

### v1.0 (初始版本)
- 🎉 Python实现
- 🖼️ 12种图像处理算法
- 🖱️ ROI选择和裁剪功能
- 📱 图形界面支持

---

## 📧 联系方式

如有问题或建议，请通过GitHub Issues联系。

---

**享受图像处理的乐趣!** 🎨📷✨
