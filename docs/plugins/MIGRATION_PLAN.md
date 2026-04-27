# 插件架构迁移计划（改进版）

## 📋 概述

本文档描述了从当前插件结构迁移到**两层架构**统一插件体系的详细计划。

**核心改进：**
- ✅ 简化为两层结构：`builtin/` + `marketplace/`（取消 `user_custom/`）
- ✅ 重命名 `ai_base` 为 `node_base`（通用节点基类）
- ✅ 明确 `builtin`/`marketplace` 的定位

## 🎯 目标

将现有的插件结构重构为两层架构：
- `builtin/`: 内置节点（官方发布，需编译）
- `marketplace/`: 市场插件（动态加载，可分享）

## 📊 当前状态分析

### 现有插件包
```
src/python/user_plugins/
├── AI/                    ← 空壳插件（需删除）
├── example_advanced_nodes/ ← 示例插件
├── feature_extraction/    ← OpenCV特征提取 → builtin/
├── integration/           ← 系统集成 → builtin/
├── io_camera/             ← 图像IO → builtin/
├── match_location/        ← 匹配定位 → builtin/
├── measurement/           ← 测量分析 → builtin/
├── ocr_vision/            ← AI-OCR视觉 → marketplace/
├── preprocessing/         ← OpenCV预处理 → builtin/
├── recognition/           ← 识别分类 → builtin/
└── yolo_vision/           ← AI-YOLO视觉 → marketplace/
```

### 需要移动的文件
- `base_nodes.py` → `shared_libs/node_base/base_node.py`（重命名）
- `performance_monitor.py` → `shared_libs/node_base/performance_monitor.py`
- `ai_node_examples.py` → `shared_libs/node_base/examples/`
- 文档文件 → `docs/plugins/`（已存在）

## 🚀 迁移步骤

### Phase 1: 创建新目录结构（第1天）

1. **创建plugin_packages两层目录**
   ```bash
   mkdir -p src/python/plugin_packages/{builtin,marketplace/{installed,cache,binaries/{Windows,Linux,MacOS}}}
   ```

2. **创建shared_libs目录（使用node_base而非ai_base）**
   ```bash
   mkdir -p src/python/shared_libs/{node_base,common_utils,cpp_wrappers}
   ```

3. **更新.gitignore**
   ```gitignore
   # 市场插件缓存
   src/python/plugin_packages/marketplace/cache/
   
   # 用户未提交的实验性插件（可选）
   src/python/plugin_packages/marketplace/installed/my_*
   ```

### Phase 2: 迁移预置插件到builtin/（第2天）

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

2. **处理示例插件**
   ```bash
   # 移动示例插件到marketplace作为参考
   mv src/python/user_plugins/example_advanced_nodes src/python/plugin_packages/marketplace/installed/
   ```

3. **删除空壳AI插件**
   ```bash
   rm -rf src/python/user_plugins/AI/
   ```

### Phase 3: 迁移AI插件到marketplace/（第3天）

1. **移动YOLO和OCR插件到marketplace**
   ```bash
   mv src/python/user_plugins/yolo_vision src/python/plugin_packages/marketplace/installed/
   mv src/python/user_plugins/ocr_vision src/python/plugin_packages/marketplace/installed/
   ```

2. **更新plugin.json中的source字段**
   ```json
   {
     "name": "yolo_vision",
     "source": "marketplace",  // ← 添加此字段
     ...
   }
   ```

### Phase 4: 迁移共享库并重命名（第4天）

1. **创建node_base目录（而非ai_base）**
   ```bash
   mkdir -p src/python/shared_libs/node_base/examples
   ```

2. **移动并重命名文件**
   ```bash
   # 移动base_nodes.py并重命名为base_node.py
   mv src/python/user_plugins/base_nodes.py src/python/shared_libs/node_base/base_node.py
   
   # 移动performance_monitor.py
   mv src/python/user_plugins/performance_monitor.py src/python/shared_libs/node_base/
   
   # 移动示例代码
   mv src/python/user_plugins/ai_node_examples.py src/python/shared_libs/node_base/examples/
   ```

3. **创建__init__.py文件**
   ```python
   # src/python/shared_libs/node_base/__init__.py
   from .base_node import BaseNode
   from .performance_monitor import PerformanceMonitor
   from .resource_manager import ResourceManager
   
   __all__ = ['BaseNode', 'PerformanceMonitor', 'ResourceManager']
   ```

4. **更新导入路径**
   - 在所有插件中更新导入语句
   - 从 `from user_plugins.base_nodes import AIBaseNode` 
   - 改为 `from shared_libs.node_base import BaseNode`

5. **重命名类名**
   - 在base_node.py中，将 `AIBaseNode` 重命名为 `BaseNode`
   - 更新所有子类引用

### Phase 5: 迁移文档（第5天）

1. **文档已在docs/plugins/目录**（无需移动）
   - PLUGIN_ARCHITECTURE.md ✅
   - DEVELOPER_GUIDE.md ✅
   - MIGRATION_PLAN.md ✅

2. **更新文档中的路径引用**
   - 检查所有.md文件中的相对路径
   - 更新为新的两层目录结构
   - 更新ai_base为node_base的引用

### Phase 6: 更新PluginManager（第6天）

1. **修改扫描逻辑（移除user_custom）**
   ```python
   # plugin_manager.py
   def scan_plugins(self):
       # 扫描builtin目录（优先级最高）
       self._scan_directory(self.builtin_dir, priority=1, source='builtin')
       
       # 扫描marketplace目录（优先级中等）
       self._scan_directory(self.marketplace_dir, priority=2, source='marketplace')
       
       # ❌ 移除user_custom扫描逻辑
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

3. **区分builtin/marketplace的卸载策略**
   ```python
   def uninstall_plugin(self, plugin_name):
       plugin_info = self.get_plugin(plugin_name)
       
       # builtin/中的插件不可卸载
       if plugin_info.source == 'builtin':
           raise PermissionError("内置插件不可卸载")
       
       # marketplace/中的插件可卸载
       if plugin_info.source == 'marketplace':
           self._remove_marketplace_plugin(plugin_name)
   ```

### Phase 7: 测试验证（第7天）

1. **功能测试**
   - ✅ 验证所有builtin插件正常加载
   - ✅ 验证所有marketplace插件正常加载
   - ✅ 测试节点库显示正确分类
   - ✅ 验证工作流可以正常运行

2. **兼容性测试**
   - ✅ 测试现有工作流的兼容性
   - ✅ 验证插件热重载功能
   - ✅ 测试ZIP插件安装
   - ✅ 测试二进制插件加载

3. **性能测试**
   - ✅ 测量插件加载时间
   - ✅ 验证内存使用情况
   - ✅ 对比新旧架构性能差异

4. **UI测试**
   - ✅ 测试节点包重命名功能
   - ✅ 测试节点移动功能（builtin ↔ marketplace）
   - ✅ 测试插件安装/卸载功能

## ⚠️ 注意事项

### 备份策略
1. **完整备份**：迁移前备份整个user_plugins目录
2. **版本控制**：在Git中创建迁移分支
3. **回滚计划**：准备回滚脚本

### 兼容性考虑
1. **工作流兼容**：确保现有工作流不受影响
2. **API兼容**：保持插件API向后兼容
3. **配置迁移**：自动迁移用户配置

### 关键变更点
1. **取消user_custom/**：简化为两层结构
2. **重命名ai_base为node_base**：强调通用性
3. **明确builtin/marketplace定位**：官方内置 vs 市场共享

### 用户通知
1. **发布公告**：提前通知用户架构变更
2. **迁移指南**：提供详细的迁移说明
3. **技术支持**：设立专门的技术支持渠道

## 📅 时间表

| 阶段 | 任务 | 预计时间 | 负责人 |
|------|------|----------|--------|
| Phase 1 | 创建新目录结构 | 1天 | 开发团队 |
| Phase 2 | 迁移预置插件到builtin/ | 1天 | 开发团队 |
| Phase 3 | 迁移AI插件到marketplace/ | 1天 | 开发团队 |
| Phase 4 | 迁移共享库并重命名 | 1天 | 开发团队 |
| Phase 5 | 迁移文档 | 0.5天 | 文档团队 |
| Phase 6 | 更新PluginManager | 1天 | 核心开发 |
| Phase 7 | 测试验证 | 1.5天 | QA团队 |
| **总计** | | **7天** | |

## ✅ 验收标准

1. **所有预置插件正常加载**
2. **节点库显示正确分类（builtin vs marketplace）**
3. **现有工作流可以正常运行**
4. **插件热重载功能正常**
5. **文档完整且路径正确**
6. **性能指标符合要求**
7. **node_base基类正常工作**
8. **builtin插件不可卸载，marketplace插件可卸载**

## 🔄 回滚计划

如果迁移过程中出现严重问题：

1. **立即停止迁移**
2. **恢复备份的user_plugins目录**
3. **回退代码更改**
4. **分析失败原因**
5. **重新制定迁移计划**

## 📝 迁移检查清单

### 目录结构
- [ ] 创建plugin_packages/builtin/
- [ ] 创建plugin_packages/marketplace/{installed,cache,binaries}
- [ ] 创建shared_libs/node_base/
- [ ] 删除user_custom/相关代码

### 插件迁移
- [ ] OpenCV插件迁移到builtin/
- [ ] AI插件迁移到marketplace/
- [ ] 更新所有plugin.json的source字段

### 共享库
- [ ] 重命名ai_base为node_base
- [ ] 重命名AIBaseNode为BaseNode
- [ ] 更新所有导入路径

### PluginManager
- [ ] 移除user_custom扫描逻辑
- [ ] 添加source字段支持
- [ ] 实现builtin/marketplace差异化策略

### 测试
- [ ] 功能测试通过
- [ ] 兼容性测试通过
- [ ] 性能测试通过
- [ ] UI测试通过