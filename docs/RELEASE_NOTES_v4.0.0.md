# StduyOpenCV v4.0.0 发布说明

**发布日期**: 2026-04-27  
**版本类型**: Major Release（重大更新）  
**Git Tag**: `v4.0.0`  
**Commit**: `fc74fa6`

---

## 🎉 概述

StduyOpenCV v4.0.0 是一个里程碑式的版本，完成了插件系统的全面重构。所有节点统一架构，建立了完整的资源隔离机制，为后续 AI 功能扩展奠定了坚实基础。

---

## ✨ 核心改进

### 1. 统一节点架构

- ✅ **37 个节点**全部继承自 `AIBaseNode` 或 `BaseNode` 基类
- ✅ 统一的日志输出方法（`log_info/warning/error/success`）
- ✅ 统一的错误处理机制
- ✅ 统一的资源声明规范

### 2. 新体系目录结构

所有插件包采用标准化的目录结构：

```
plugin_name/
├── __init__.py           # 插件入口
├── plugin.json           # 元数据配置
└── nodes/                # 节点目录
    ├── __init__.py       # 导出所有节点
    ├── node1.py          # 节点文件 1
    ├── node2.py          # 节点文件 2
    └── subfolder/        # 可选：子目录分组
        ├── __init__.py
        └── node3.py
```

### 3. 资源隔离机制

根据《AI 模块资源隔离设计规范》实现三级资源分级：

| 等级 | CPU | 内存 | GPU | 典型场景 |
|------|-----|------|-----|---------|
| **light** | 1-2 核 | 1-2 GB | 不需要 | 图像处理、轻量推理 |
| **medium** | 4 核 | 4-8 GB | 可选 | 中等模型推理、标注辅助 |
| **heavy** | 8+ 核 | 16+ GB | 必需 | 模型训练、量化优化 |

每个节点必须声明：
```python
resource_level = "light"
hardware_requirements = {
    'cpu_cores': 2,
    'memory_gb': 2,
    'gpu_required': False,
    'gpu_memory_gb': 0
}
```

### 4. 依赖分离管理

- 推理依赖与训练依赖使用独立配置文件
- 支持按需安装（工厂现场仅需推理依赖）
- 自动依赖检查与错误提示

---

## 📦 已迁移插件（10个）

| 插件名称 | 节点数 | 资源等级 | 功能描述 |
|---------|--------|---------|---------|
| **preprocessing** | 8 | light | 图像预处理（灰度化、滤波、缩放等） |
| **io_camera** | 3 | light | 图像输入输出（加载、保存、显示） |
| **feature_extraction** | 6 | light | 特征提取（边缘检测、角点检测等） |
| **measurement** | 2 | light | 测量分析（轮廓分析、边界框） |
| **recognition** | 1 | light | 模式识别（模板匹配） |
| **integration** | 1 | light | 数据融合（多图像混合） |
| **example_advanced_nodes** | 3 | light | 高级示例（多输入输出、复杂参数） |
| **match_location** | 3 | light | 匹配定位（灰度匹配、形状匹配） |
| **ocr_vision** | 3 | light-medium | OCR 文字识别（文本、表格、版面） |
| **yolo_vision** | 7 | light-heavy | YOLO 视觉算法（检测、分类、分割、训练） |

**总计**: 37 个节点

---

## 🛠️ 新增工具

### 1. create_node.py - 节点脚手架工具

**位置**: `tools/create_node.py`

**功能**:
- 交互式引导创建新节点
- 支持 3 种节点类型（BaseNode/AIBaseNode/AsyncAINode）
- 自动生成节点文件、更新 `__init__.py` 和 `plugin.json`

**使用方式**:
```bash
python tools/create_node.py
```

### 2. verify_all_plugins_migration.py - 迁移验证工具

**位置**: `tests/verify_all_plugins_migration.py`

**功能**:
- JSON 结构完整性检查
- nodes/ 目录结构验证
- 节点类导出声明检查（递归扫描）
- 生成详细汇总报告

**使用方式**:
```bash
python tests/verify_all_plugins_migration.py
```

### 3. fix_import_paths.py - 导入路径修复工具

**位置**: `tools/fix_import_paths.py`

**功能**:
- 批量修正相对导入路径
- 智能计算导入层级（3点 vs 4点）
- 保持文件编码不变

**使用方式**:
```bash
python tools/fix_import_paths.py
```

---

## 📚 新增文档

### 1. 《统一节点开发指南》

**位置**: `docs/UNIFIED_NODE_DEVELOPMENT_GUIDE.md`

**内容**:
- 三种节点基类详细介绍（BaseNode/AIBaseNode/AsyncAINode）
- 完整的代码示例和最佳实践
- plugin.json 配置规范详解
- 常见问题解答（Q&A）
- 迁移指南

### 2. 《插件迁移教程》

**位置**: `docs/PLUGIN_MIGRATION_TUTORIAL.md`

**内容**:
- 迁移前后对比
- 6 步迁移流程详解
- 自动化迁移工具使用方法
- 迁移验证方法
- 6 个常见问题解决方案
- 3 个实际迁移案例

### 3. 《架构演进文档》

**位置**: `docs/ARCHITECTURE_EVOLUTION.md`

**内容**:
- 插件系统架构演进历程
- 设计决策与权衡
- 经验教训总结

---

## 🔧 技术改进

### 1. PluginManager 增强

- ✅ 支持动态模块加载与相对导入
- ✅ 正确设置包层次结构
- ✅ 注册父包到 `sys.modules`
- ✅ 热重载功能完善

### 2. PermissionChecker 优化

- ✅ 更精确的安全检查规则
- ✅ 支持新体系插件结构
- ✅ 详细的错误提示

### 3. 模型缓存机制

- ✅ 跨实例模型缓存
- ✅ 本地优先加载策略
- ✅ 自动清理过期缓存

### 4. 硬件检测

- ✅ CPU 核心数检测
- ✅ 内存大小检测
- ✅ GPU 显存及 CUDA 版本检测
- ✅ 不满足要求时提供明确警告

---

## 🐛 Bug 修复

### 1. 相对导入路径问题

**问题**: 所有节点使用 `....base_nodes`（4点），导致 `ImportError: attempted relative import beyond top-level package`

**修复**: 
- 修改 PluginManager 加载逻辑
- 批量修正 19 个文件的导入路径（4点 → 3点）
- 创建自动化修复脚本

**影响**: 所有 10 个插件现在能正常加载

### 2. 文件编码问题

**问题**: PowerShell 的 `Set-Content` 破坏 UTF-8 编码

**修复**: 使用 Python 脚本安全地修改文件，保持编码不变

### 3. 节点类缺失问题

**问题**: match_location 插件的 `nodes.py` 为空，但 `plugin.json` 定义了 3 个节点

**修复**: 从零实现 3 个节点类，修复重复类名问题

---

## 📊 性能指标

### 加载时间

| 插件数量 | 节点数量 | 加载耗时 |
|---------|---------|---------|
| 10 | 37 | < 2s |

### 内存占用

| 场景 | 内存占用 |
|------|---------|
| 仅加载插件 | ~50 MB |
| 加载 + 初始化节点 | ~100 MB |
| 运行工作流 | 视具体节点而定 |

---

## ✅ 兼容性

### 向后兼容

- ✅ 现有工作流文件可正常打开
- ✅ 节点标识符保持不变
- ✅ 节点名称保持不变
- ✅ 端口名称保持不变
- ✅ 参数配置保持不变

### 升级建议

1. **备份工作流文件**（虽然兼容，但建议备份）
2. **重启应用**以加载新架构
3. **验证工作流**能正常执行
4. **更新自定义插件**遵循新规范

---

## 🚀 下一步计划

### v4.1.0（计划中）

- [ ] 添加更多 AI 插件（人脸识别、语义分割等）
- [ ] 优化节点性能（并行处理、GPU 加速）
- [ ] 完善 GUI 界面（节点搜索、快捷键）
- [ ] 添加单元测试覆盖率至 80%

### v4.2.0（计划中）

- [ ] 支持云端模型管理
- [ ] 添加插件市场功能
- [ ] 完善社区贡献指南
- [ ] 国际化支持（中英文切换）

---

## 🙏 致谢

感谢所有参与本次重构的开发者和测试者！

特别感谢：
- OpenCV 社区提供的优秀图像处理库
- Ultralytics 团队开发的 YOLO 系列模型
- NodeGraphQt 提供的节点编辑器框架

---

## 📞 联系方式

- **项目地址**: https://gitee.com/myduty_45/study-open-cv
- **问题反馈**: https://gitee.com/myduty_45/study-open-cv/issues
- **文档中心**: `docs/` 目录

---

**最后更新**: 2026-04-27  
**维护者**: StduyOpenCV 开发团队
