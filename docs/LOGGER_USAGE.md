# 日志系统使用指南

## 📖 概述

本项目采用统一的日志管理系统，通过环境变量控制输出级别，实现日志的可控输出。

## 🎯 两种日志模式

### 1. NORMAL 模式（默认）
仅输出关键信息：
- ✅ 应用启动/关闭
- ✅ 插件加载成功/失败
- ⚠️ 警告信息
- ❌ 错误信息

**适用场景**: 日常使用、生产环境

### 2. DEBUG 模式
输出所有信息，包括：
- 🔍 详细的执行流程
- 📊 变量状态追踪
- 🛠️ UI交互细节
- 📦 插件加载过程

**适用场景**: 问题诊断、开发调试

## 🚀 使用方法

### 方法1: 环境变量（推荐）

**Windows PowerShell:**
```powershell
# 设置为DEBUG模式
$env:LOG_LEVEL="DEBUG"
python src\python\main.py

# 设置为NORMAL模式（默认）
$env:LOG_LEVEL="NORMAL"
python src\python\main.py
```

**Linux/macOS:**
```bash
# 设置为DEBUG模式
export LOG_LEVEL=DEBUG
python src/python/main.py

# 设置为NORMAL模式（默认）
export LOG_LEVEL=NORMAL
python src/python/main.py
```

**临时设置（单条命令）:**
```bash
# Windows
set LOG_LEVEL=DEBUG && python src\python\main.py

# Linux/macOS
LOG_LEVEL=DEBUG python src/python/main.py
```

### 方法2: 代码中动态设置

```python
from utils.logger import set_log_level

# 在应用启动时设置
set_log_level('DEBUG')  # 或 'NORMAL'
```

## 💻 代码中使用

### 替换旧的print语句

**旧代码:**
```python
print("✅ 插件加载成功")
print(f"⚠️ 警告: {message}")
print(f"🔍 调试: widget_count={count}")
```

**新代码:**
```python
from utils.logger import logger

logger.success("插件加载成功")
logger.warning(f"警告: {message}")
logger.debug("调试信息", widget_count=count)
```

### 日志方法对照表

| 旧方式 | 新方式 | 说明 |
|--------|--------|------|
| `print("info")` | `logger.info("info")` | 正常信息 |
| `print("✅ success")` | `logger.success("success")` | 成功信息 |
| `print("⚠️ warning")` | `logger.warning("warning")` | 警告信息 |
| `print("❌ error")` | `logger.error("error")` | 错误信息 |
| `print("🔍 debug")` | `logger.debug("debug")` | 调试信息（仅DEBUG模式） |
| `print("="*60)` | `logger.separator()` | 分隔线 |
| `print("\n标题\n" + "="*60)` | `logger.section("标题")` | 章节标题 |

### 高级用法

**携带上下文信息的调试日志:**
```python
logger.debug_trace("事件过滤器安装", 
                   tab_count=10, 
                   widget_type="NodesGridView")
```

输出（DEBUG模式）:
```
[14:23:45] [DEBUG] 🔍 事件过滤器安装 | tab_count=10, widget_type=NodesGridView
```

**彩色输出:**
日志自动支持彩色终端（Windows 10+、Linux、macOS）:
- 🟢 INFO/SUCCESS: 绿色
- 🟡 WARNING: 黄色
- 🔴 ERROR: 红色
- 🔵 DEBUG: 青色

## 📋 迁移计划

### 第一阶段：核心模块（本次完成）
- [x] 创建 `utils/logger.py`
- [ ] 替换 `main_window.py` 中的print
- [ ] 替换 `plugin_ui_manager.py` 中的print
- [ ] 替换 `project_ui_manager.py` 中的print

### 第二阶段：插件模块（后续迭代）
- [ ] 替换各插件节点中的print
- [ ] 统一插件日志格式

### 第三阶段：清理冗余日志
- [ ] 移除所有临时诊断日志
- [ ] 精简启动流程输出

## 🎨 输出效果对比

### NORMAL模式
```
[14:23:45] [INFO] 应用启动成功
[14:23:46] [INFO] ✅ 共扫描到 10 个插件
[14:23:47] [WARNING] ⚠️ 未找到节点类: DataOutputNode
[14:23:48] [INFO] ✅ 插件加载完成
```

### DEBUG模式
```
[14:23:45] [INFO] 应用启动成功
[14:23:45] [DEBUG] 🔍 [_connect_node_selection_signal] 开始安装事件过滤器 | tab_count=10
[14:23:45] [DEBUG] 🔍 Tab 0 [图像相机]: widget类型=NodesGridView | child_count=5
[14:23:46] [INFO] ✅ 共扫描到 10 个插件
[14:23:46] [DEBUG] 🔍 [eventFilter] 捕获到节点库点击事件: NodesGridView
[14:23:47] [WARNING] ⚠️ 未找到节点类: DataOutputNode
[14:23:48] [INFO] ✅ 插件加载完成
```

## ⚙️ 配置建议

### 开发环境
```powershell
# PowerShell profile (Microsoft.PowerShell_profile.ps1)
$env:LOG_LEVEL = "DEBUG"
```

### 生产环境
```powershell
# 保持默认NORMAL模式，无需额外配置
```

### 临时调试
```powershell
# 仅本次运行启用DEBUG
$env:LOG_LEVEL="DEBUG"; python src\python\main.py
```

## 📝 注意事项

1. **性能影响**: DEBUG模式会输出大量日志，可能影响启动速度，建议仅在需要时使用
2. **日志清理**: 问题解决后应及时移除临时诊断日志，恢复简洁输出
3. **向后兼容**: 保留了 `log_info()`, `log_warning()` 等便捷函数，旧代码可逐步迁移
4. **颜色支持**: Windows用户需使用Windows Terminal或PowerShell 7+以获得最佳彩色体验
