# 日志系统使用指南（双模式版本）

## 📖 概述

本项目采用统一的日志管理系统，支持两种工作模式：
- **NORMAL模式**：日常运行，仅输出关键信息
- **DEBUG模式**：问题诊断，关闭正常日志，仅输出指定模块的调试信息

## 🎯 两种日志模式详解

### 1. NORMAL 模式（默认）

**用途**: 日常使用、生产环境

**输出内容**:
- ✅ INFO级别：应用启动、插件加载等关键状态
- ⚠️ WARNING级别：警告信息
- ❌ ERROR级别：错误信息  
- 🎉 SUCCESS级别：重要操作完成

**不输出**: DEBUG级别的调试信息

**示例输出**:
```
[14:23:45] [INFO] 应用启动成功
[14:23:46] [INFO] ✅ 共扫描到 10 个插件
[14:23:47] [WARNING] ⚠️ 未找到节点类: DataOutputNode
[14:23:48] [ERROR] 节点注册失败
```

### 2. DEBUG 模式

**用途**: 问题诊断、开发调试

**输出内容**:
- 🔍 DEBUG级别：**仅输出指定模块**的调试信息
- ⚠️ WARNING级别：始终输出（便于发现问题）
- ❌ ERROR级别：始终输出（便于发现错误）

**不输出**: 
- NORMAL模式下的INFO/SUCCESS日志（避免干扰调试）
- 未在`DEBUG_MODULES`中指定的模块的DEBUG日志

**示例输出**（`DEBUG_MODULES="plugin_loader"`）:
```
[14:23:45] [WARNING] ⚠️ 未找到节点类: DataOutputNode
[14:23:46] [DEBUG] [plugin_loader] 🔍 开始扫描插件目录 | path=user_plugins
[14:23:46] [DEBUG] [plugin_loader] 发现插件文件: example/plugin.json
[14:23:47] [DEBUG] [plugin_loader] 解析插件元数据: name=example, version=1.0.0
```

## 🚀 使用方法

### 方法1: 环境变量（推荐）

**Windows PowerShell:**
```powershell
# NORMAL模式（默认）
python src\python\main.py

# DEBUG模式 - 调试所有模块
$env:LOG_LEVEL="DEBUG"
python src\python\main.py

# DEBUG模式 - 仅调试指定模块（逗号分隔）
$env:LOG_LEVEL="DEBUG"
$env:DEBUG_MODULES="plugin_loader,ui_manager"
python src\python\main.py
```

**Linux/macOS:**
```bash
# NORMAL模式（默认）
python src/python/main.py

# DEBUG模式 - 调试所有模块
export LOG_LEVEL=DEBUG
python src/python/main.py

# DEBUG模式 - 仅调试指定模块
export LOG_LEVEL=DEBUG
export DEBUG_MODULES=plugin_loader,ui_manager
python src/python/main.py
```

### 方法2: 代码中动态设置

```python
from utils import set_log_level

# NORMAL模式
set_log_level('NORMAL')

# DEBUG模式 - 调试所有模块
set_log_level('DEBUG', [])

# DEBUG模式 - 仅调试指定模块
set_log_level('DEBUG', ['plugin_loader', 'ui_manager'])
```

## 💻 代码中使用

### 基础用法

```python
import utils
from utils import logger

# NORMAL模式输出的日志
logger.info("应用启动")                    # [14:23:45] [INFO] 应用启动
logger.success("插件加载完成")              # [14:23:46] [INFO] ✅ 插件加载完成
logger.warning("缺少可选依赖")              # [14:23:47] [WARNING] 缺少可选依赖
logger.error("节点注册失败")                # [14:23:48] [ERROR] 节点注册失败

# DEBUG模式输出的日志（需指定module）
logger.debug("开始加载插件", module="plugin_loader")
logger.debug_trace("事件过滤器安装", module="ui_manager", widget_count=10)
```

### 带模块标识的日志

```python
# 在特定模块中使用
logger.info("初始化完成", module="image_processor")
logger.debug("处理图像参数", module="image_processor", width=1920, height=1080)
logger.warning("图像格式异常", module="image_processor")
logger.error("处理失败", module="image_processor")
```

### 实际应用场景

**场景1: 插件加载器**
```python
# plugin_loader.py
import utils
from utils import logger

class PluginLoader:
    def load_plugins(self):
        logger.info("开始加载插件", module="plugin_loader")
        
        for plugin_path in self.plugin_paths:
            logger.debug(f"扫描插件: {plugin_path}", module="plugin_loader")
            
            try:
                plugin = self._load_plugin(plugin_path)
                logger.success(f"插件加载成功: {plugin.name}", module="plugin_loader")
            except Exception as e:
                logger.error(f"插件加载失败: {e}", module="plugin_loader")
```

**场景2: UI管理器**
```python
# ui_manager.py
import utils
from utils import logger

class UIManager:
    def initialize(self):
        logger.info("初始化UI组件", module="ui_manager")
        
        logger.debug("创建主窗口", module="ui_manager", width=1920, height=1080)
        logger.debug("安装事件过滤器", module="ui_manager", widget_count=10)
        
        logger.success("UI初始化完成", module="ui_manager")
```

## 📋 常见使用场景

### 场景1: 排查插件加载问题

```powershell
# 仅查看plugin_loader模块的调试信息
$env:LOG_LEVEL="DEBUG"
$env:DEBUG_MODULES="plugin_loader"
python src\python\main.py
```

**输出**:
```
[14:23:45] [DEBUG] [plugin_loader] 🔍 开始扫描插件目录
[14:23:46] [DEBUG] [plugin_loader] 发现插件: example
[14:23:46] [DEBUG] [plugin_loader] 解析plugin.json
[14:23:47] [WARNING] ⚠️ 插件example缺少version字段
```

### 场景2: 排查UI交互问题

```powershell
# 同时查看ui_manager和event_handler模块
$env:LOG_LEVEL="DEBUG"
$env:DEBUG_MODULES="ui_manager,event_handler"
python src\python\main.py
```

### 场景3: 全面调试

```powershell
# 查看所有模块的调试信息
$env:LOG_LEVEL="DEBUG"
python src\python\main.py
```

### 场景4: 生产环境运行

```powershell
# 使用默认的NORMAL模式
python src\python\main.py
```

## ⚙️ 配置建议

### 开发环境

在PowerShell profile中添加：
```powershell
# Microsoft.PowerShell_profile.ps1
$env:LOG_LEVEL = "DEBUG"
$env:DEBUG_MODULES = "plugin_loader,ui_manager,node_executor"
```

### 生产环境

保持默认NORMAL模式，无需额外配置。

### 临时调试

```powershell
# 仅本次运行启用DEBUG
$env:LOG_LEVEL="DEBUG"; $env:DEBUG_MODULES="plugin_loader"; python src\python\main.py
```

## 📝 注意事项

1. **模块命名规范**: 使用有意义的模块名，如`plugin_loader`、`ui_manager`、`node_executor`
2. **调试粒度**: DEBUG模式下可指定多个模块，用逗号分隔
3. **日志清理**: 问题解决后及时移除临时debug日志，恢复简洁输出
4. **性能影响**: DEBUG模式会输出大量日志，可能影响性能，建议仅在需要时使用
5. **引用更新**: 使用`utils.logger`而非`from utils import logger`，确保动态切换时引用正确
6. **向后兼容**: 保留了`log_info()`, `log_warning()`等便捷函数，旧代码可逐步迁移

## 🎨 输出效果对比

### NORMAL模式
```
[14:23:45] [INFO] 应用启动成功
[14:23:46] [INFO] ✅ 共扫描到 10 个插件
[14:23:47] [WARNING] ⚠️ 未找到节点类: DataOutputNode
[14:23:48] [INFO] ✅ 插件加载完成
```

### DEBUG模式 (DEBUG_MODULES="plugin_loader")
```
[14:23:45] [WARNING] ⚠️ 未找到节点类: DataOutputNode
[14:23:45] [DEBUG] [plugin_loader] 🔍 开始扫描插件目录 | path=user_plugins
[14:23:45] [DEBUG] [plugin_loader] 发现插件文件: example/plugin.json
[14:23:46] [DEBUG] [plugin_loader] 解析插件元数据: name=example, version=1.0.0
[14:23:46] [DEBUG] [plugin_loader] 注册节点: ExampleNode -> category=预处理
[14:23:47] [DEBUG] [plugin_loader] 插件加载完成: 共10个节点
```

## 🔄 版本历史

- **v5.2.0** (2026-04-29): 重构为双模式系统，支持模块过滤
- **v5.1.0** (2026-04-28): 初始日志系统 + UI面板集成
