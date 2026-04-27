# 日志系统迭代总结 (v5.1-dev)

## 📅 迭代时间
2026-04-28

## 🎯 迭代目标
实现可控的日志输出系统，支持NORMAL/DEBUG两种模式，并在UI中添加实时日志面板。

---

## ✅ 完成的工作

### 1. 统一日志管理系统 (Commit: cb9158f)

**新增文件**:
- `src/python/utils/logger.py` - 核心日志管理器
- `src/python/utils/__init__.py` - 工具包初始化
- `docs/LOGGER_USAGE.md` - 使用文档

**核心功能**:
```python
from utils.logger import logger

# 正常日志（始终输出）
logger.info("应用启动")
logger.success("插件加载成功")
logger.warning("警告信息")
logger.error("错误信息")

# 调试日志（仅DEBUG模式输出）
logger.debug("调试信息")
logger.debug_trace("详细追踪", param=value)
```

**特性**:
- ✅ 通过环境变量 `LOG_LEVEL` 控制输出级别
- ✅ 支持多Handler架构（控制台、UI等）
- ✅ 自动添加时间戳和彩色输出
- ✅ DEBUG模式支持携带上下文信息

---

### 2. 多Handler架构 (Commit: ed31e2c)

**新增文件**:
- `src/python/utils/qt_log_handler.py` - Qt UI日志处理器

**架构设计**:
```
Logger (统一入口)
    ↓
    ├─→ ConsoleHandler → 终端输出
    └─→ QtLogHandler   → UI面板显示
```

**QtLogHandler特性**:
- ✅ 线程安全：使用QMetaObject.invokeMethod
- ✅ 彩色HTML显示：INFO绿色/WARNING橙色/ERROR红色/DEBUG蓝色
- ✅ 自动滚动到底部
- ✅ 内存管理：限制最大1000行
- ✅ 深色主题：适合长时间查看

---

### 3. UI日志面板集成 (Commit: 276a281)

**修改文件**:
- `src/python/ui/main_window.py`

**UI布局**:
```
┌─────────────────────────────────────┐
│ 📋 运行日志          [🗑️清空] [▼折叠] │
├─────────────────────────────────────┤
│  [深色背景日志显示区域]               │
│  (150-300px高度，可折叠)             │
├─────────────────────────────────────┤
│ ✅ 就绪              日志级别: NORMAL │
└─────────────────────────────────────┘
```

**交互功能**:
- ✅ 点击"▼折叠"/"▶展开"切换显示状态
- ✅ 点击"🗑️清空"清除所有历史日志
- ✅ 状态栏实时显示应用状态
- ✅ 集成QtLogHandler到Logger系统

---

## 📊 当前状态

### 已完成
- ✅ 日志系统基础框架搭建完成
- ✅ 多Handler架构实现
- ✅ UI日志面板集成
- ✅ 双重输出机制（终端 + UI）

### 待完成
- ⏸️ **日志迁移**: 将现有代码中的print语句替换为logger调用
  - main_window.py
  - plugin_ui_manager.py
  - project_ui_manager.py
  - 各插件节点文件
  
- ⏸️ **日志输出问题**: UI面板和控制台目前均无日志输出
  - 原因：现有代码仍使用print语句，未迁移到logger系统
  - 解决方案：后续逐步替换print为logger调用

---

## 🔧 使用方法

### 控制日志级别

**Windows PowerShell**:
```powershell
# NORMAL模式（默认）
$env:LOG_LEVEL="NORMAL"
python src\python\main.py

# DEBUG模式
$env:LOG_LEVEL="DEBUG"
python src\python\main.py
```

**Linux/macOS**:
```bash
# NORMAL模式
export LOG_LEVEL=NORMAL
python src/python/main.py

# DEBUG模式
export LOG_LEVEL=DEBUG
python src/python/main.py
```

---

## 📝 下一步计划

### Phase 1: 日志迁移（优先级：高）
1. 替换 main_window.py 中的print语句
2. 替换 plugin_ui_manager.py 中的print语句
3. 替换 project_ui_manager.py 中的print语句
4. 测试验证双重输出是否正常工作

### Phase 2: 日志优化（优先级：中）
1. 精简启动流程输出
2. 移除冗余的诊断日志
3. 优化日志格式和可读性

### Phase 3: 高级功能（优先级：低）
1. 日志级别动态切换（UI中提供开关）
2. 日志搜索和过滤功能
3. 日志导出到文件

---

## 🎨 技术亮点

### 1. 多Handler架构
- 解耦日志输出与业务逻辑
- 易于扩展新的输出目标（文件、网络等）
- 支持同时输出到多个目标

### 2. 线程安全的UI更新
- 使用QMetaObject.invokeMethod确保主线程更新UI
- 避免跨线程访问Qt组件导致的崩溃

### 3. 内存管理
- 自动限制最大日志行数
- 定期清理旧日志，防止内存泄漏

### 4. 用户体验优化
- 深色主题，减少视觉疲劳
- 可折叠设计，节省屏幕空间
- 一键清空，快速清理历史记录

---

## 📚 相关文档
- [日志系统使用指南](./LOGGER_USAGE.md)
- [项目README](../README.md)

---

## 🔄 版本历史
- **v5.1-dev** (2026-04-28): 日志系统基础框架 + UI面板集成
- **v5.0.0** (2026-04-27): 插件系统架构重构完成
