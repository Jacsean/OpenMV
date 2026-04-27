# 插件架构迁移计划

## 📋 概述

本文档描述了从当前插件结构迁移到统一插件体系架构的详细计划。

## 🎯 目标

将现有的插件结构重构为三层架构：
- `builtin/`: 预置节点
- `marketplace/`: 市场插件
- `user_custom/`: 用户自定义

## 📊 当前状态分析

### 现有插件包
```
src/python/user_plugins/
├── AI/                    ← 空壳插件
├── example_advanced_nodes/ ← 示例插件
├── feature_extraction/    ← OpenCV特征提取
├── integration/           ← 系统集成
├── io_camera/             ← 图像IO
├── match_location/        ← 匹配定位
├── measurement/           ← 测量分析
├── ocr_vision/            ← AI-OCR视觉
├── preprocessing/         ← OpenCV预处理
├── recognition/           ← 识别分类
└── yolo_vision/           ← AI-YOLO视觉
```

### 需要移动的文件
- `base_nodes.py` → `shared_libs/ai_base/`
- `performance_monitor.py` → `shared_libs/ai_base/`
- `ai_node_examples.py` → `shared_libs/ai_base/examples/`
- 文档文件 → `docs/plugins/`

## 🚀 迁移步骤

### Phase 1: 创建新目录结构（第1天）

1. **创建plugin_packages目录**
   ```bash
   mkdir -p src/python/plugin_packages/{builtin,marketplace/{installed,cache,binaries},user_custom}
   ```

2. **创建shared_libs目录**
   ```bash
   mkdir -p src/python/shared_libs/{ai_base,common_utils,cpp_wrappers}
   ```

3. **更新.gitignore**
   ```gitignore
   # 用户自定义插件
   src/python/plugin_packages/user_custom/
   
   # 市场插件缓存
   src/python/plugin_packages/marketplace/cache/
   ```

### Phase 2: 迁移预置插件（第2天）

1. **移动OpenCV相关插件到builtin/**
   ```bash
   mv src/python/user_plugins/io_camera src/python/plugin_packages/builtin/
   mv src/python/user_plugins/preprocessing src/python/plugin_packages/builtin/
   mv src/python/user_plugins/feature_extraction src/python/plugin_packages/builtin/
   mv src/python/user_plugins/measurement src/python/plugin_packages/builtin/
   mv src/python/user_plugins/recognition src/python/plugin_packages/builtin/
   mv src/python/user_plugins/match_location src/python/plugin_packages/builtin/
   mv src/python/user_plugins/integration src/python/plugin_packages/builtin/
   ```

2. **合并AI相关插件**
   ```bash
   # 创建统一的AI视觉插件包
   mkdir -p src/python/plugin_packages/builtin/ai_vision/{nodes,models}
   
   # 移动YOLO和OCR节点
   cp -r src/python/user_plugins/yolo_vision/nodes/* src/python/plugin_packages/builtin/ai_vision/nodes/
   cp -r src/python/user_plugins/ocr_vision/nodes/* src/python/plugin_packages/builtin/ai_vision/nodes/
   
   # 合并plugin.json配置
   # 需要手动编辑合并后的plugin.json
   ```

3. **处理示例和空壳插件**
   ```bash
   # 移动示例插件
   mv src/python/user_plugins/example_advanced_nodes src/python/plugin_packages/builtin/
   
   # 删除空壳AI插件
   rm -rf src/python/user_plugins/AI/
   ```

### Phase 3: 迁移共享库（第3天）

1. **移动AI基类和工具**
   ```bash
   mv src/python/user_plugins/base_nodes.py src/python/shared_libs/ai_base/
   mv src/python/user_plugins/performance_monitor.py src/python/shared_libs/ai_base/
   mkdir -p src/python/shared_libs/ai_base/examples
   mv src/python/user_plugins/ai_node_examples.py src/python/shared_libs/ai_base/examples/
   ```

2. **创建__init__.py文件**
   ```python
   # src/python/shared_libs/ai_base/__init__.py
   from .base_nodes import AIBaseNode
   from .performance_monitor import PerformanceMonitor
   
   __all__ = ['AIBaseNode', 'PerformanceMonitor']
   ```

3. **更新导入路径**
   - 在所有AI插件中更新导入语句
   - 从 `from user_plugins.base_nodes import AIBaseNode` 
   - 改为 `from shared_libs.ai_base import AIBaseNode`

### Phase 4: 迁移文档（第4天）

1. **移动文档到docs/plugins/**
   ```bash
   mkdir -p docs/plugins
   mv src/python/user_plugins/NODE_DEVELOPMENT_GUIDE.md docs/plugins/
   mv src/python/user_plugins/NODE_API_REFERENCE.md docs/plugins/
   mv src/python/user_plugins/AI_NODE_DEVELOPMENT_GUIDE.md docs/plugins/
   ```

2. **更新文档中的路径引用**
   - 检查所有.md文件中的相对路径
   - 更新为新的目录结构

### Phase 5: 更新PluginManager（第5天）

1. **修改扫描逻辑**
   ```python
   # plugin_manager.py
   def scan_plugins(self):
       # 扫描builtin目录
       self._scan_directory(self.builtin_dir, priority=1)
       
       # 扫描marketplace目录
       self._scan_directory(self.marketplace_dir, priority=2)
       
       # 扫描user_custom目录
       self._scan_directory(self.user_dir, priority=3)
   ```

2. **添加plugin_registry.json支持**
   ```python
   def load_plugin_registry(self):
       registry_path = self.plugins_dir.parent / "plugin_registry.json"
       if registry_path.exists():
           with open(registry_path, 'r') as f:
               return json.load(f)
       return {"version": "1.0", "packages": []}
   ```

### Phase 6: 测试验证（第6-7天）

1. **功能测试**
   - 验证所有预置插件正常加载
   - 测试节点库显示正确
   - 验证工作流可以正常运行

2. **兼容性测试**
   - 测试现有工作流的兼容性
   - 验证插件热重载功能
   - 测试ZIP插件安装

3. **性能测试**
   - 测量插件加载时间
   - 验证内存使用情况
   - 测试二进制插件加载

## ⚠️ 注意事项

### 备份策略
1. **完整备份**：迁移前备份整个user_plugins目录
2. **版本控制**：在Git中创建迁移分支
3. **回滚计划**：准备回滚脚本

### 兼容性考虑
1. **工作流兼容**：确保现有工作流不受影响
2. **API兼容**：保持插件API向后兼容
3. **配置迁移**：自动迁移用户配置

### 用户通知
1. **发布公告**：提前通知用户架构变更
2. **迁移指南**：提供详细的迁移说明
3. **技术支持**：设立专门的技术支持渠道

## 📅 时间表

| 阶段 | 任务 | 预计时间 | 负责人 |
|------|------|----------|--------|
| Phase 1 | 创建新目录结构 | 1天 | 开发团队 |
| Phase 2 | 迁移预置插件 | 1天 | 开发团队 |
| Phase 3 | 迁移共享库 | 1天 | 开发团队 |
| Phase 4 | 迁移文档 | 1天 | 文档团队 |
| Phase 5 | 更新PluginManager | 1天 | 核心开发 |
| Phase 6 | 测试验证 | 2天 | QA团队 |
| **总计** | | **7天** | |

## ✅ 验收标准

1. **所有预置插件正常加载**
2. **节点库显示正确分类**
3. **现有工作流可以正常运行**
4. **插件热重载功能正常**
5. **文档完整且路径正确**
6. **性能指标符合要求**

## 🔄 回滚计划

如果迁移过程中出现严重问题：

1. **立即停止迁移**
2. **恢复备份的user_plugins目录**
3. **回退代码更改**
4. **分析失败原因**
5. **重新制定迁移计划**