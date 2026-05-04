# io_camera 插件UI显示问题诊断报告

## 📋 问题描述

用户反馈：UI中丢失了图像相机节点包，看不到图像相机节点标签。

---

## ✅ 诊断结果

### 1. 配置文件检查 - ✅ 正常

```
✅ plugin.json 格式正确
✅ category_group: "图像相机"
✅ 节点数量: 8个
✅ 所有节点类已正确注册
```

### 2. 文件结构检查 - ✅ 正常

```
✅ nodes/ 目录存在
✅ 8个节点文件全部存在
✅ __init__.py 正确导出所有节点类
✅ 所有文件语法正确（无编译错误）
```

### 3. 插件扫描测试 - ✅ 正常

```
✅ PluginManager 成功扫描到 io_camera
✅ category_group: "图像相机"
✅ 节点列表完整:
   • 加载图像 (ImageLoadNode)
   • 保存图像 (ImageSaveNode)
   • 图像显示 (ImageViewNode)
   • 数据显示 (JsonDisplayNode)
   • 工业相机采集 (CameraCaptureNode)
   • 实时预览 (RealTimePreviewNode)
   • 快速检测 (FastDetectionNode)
   • 视频录制 (VideoRecorderNode)
```

### 4. 标签页映射检查 - ✅ 正常

```
✅ "图像相机" 分类组存在于映射表中
✅ io_camera 正确归类到"图像相机"
```

---

## 🔍 根本原因分析

根据诊断结果，**配置和后端逻辑完全正常**。问题出在 **UI 显示层面**，可能的原因：

### 原因 1：应用未重启 ⭐⭐⭐⭐⭐ (最可能)

**现象**：
- 修改代码后直接运行，未重启应用
- NodeGraphQt 的 NodesPaletteWidget 缓存了旧的插件列表

**解决方案**：
```bash
# 完全关闭应用
# 重新启动应用
python src/python/main.py
```

---

### 原因 2：启动时异常中断 ⭐⭐⭐⭐

**现象**：
- 应用启动日志中有错误信息
- 插件加载过程中抛出异常
- _pending_plugins 未被正确设置

**诊断方法**：
```python
# 查看应用启动日志
# 搜索关键词：
# - "io_camera"
# - "PluginUIManager.load_plugins_to_graph"
# - "刷新节点库事件过滤器"
# - "异常"、"Error"、"Exception"
```

**解决方案**：
1. 检查启动日志
2. 修复任何导入错误或运行时异常
3. 重新启动应用

---

### 原因 3：NodesPaletteWidget 刷新失败 ⭐⭐⭐

**现象**：
- load_plugins_to_graph 被调用
- 但 refresh_node_info_event_filters 未执行或失败
- 新标签页未安装事件过滤器

**相关代码位置**：
- `plugins/plugin_ui_manager.py:L143-L145`
- `ui/main_window.py:L453-L470`

**解决方案**：
手动触发刷新（在应用运行时）：
```python
# 在Python控制台执行
main_window.refresh_node_info_event_filters()
```

---

### 原因 4：标签页名称冲突 ⭐⭐

**现象**：
- 多个插件使用相同的 category_group
- NodesPaletteWidget 合并了标签页
- 某些节点被覆盖

**检查结果**：
```
✅ 当前无冲突
✅ "图像相机" 仅被 io_camera 使用
```

---

## 🛠️ 推荐解决步骤

### 步骤 1：完全重启应用（必做）

```bash
# 1. 关闭当前运行的应用
# 2. 清除Python缓存
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true

# 3. 重新启动
python src/python/main.py
```

---

### 步骤 2：检查启动日志

启动应用后，查看日志输出，确认：

```
✅ [plugin_manager] ✅ io_camera (source: builtin)
✅ [plugin_ui_manager] 📦 待加载插件数: X
✅ [plugin_ui_manager] ✅ 节点库Graph加载完成
✅ [plugin_ui_manager] 🔄 刷新节点库事件过滤器
✅ [plugin_ui_manager] ✅ load_plugins_to_graph执行完成
```

如果看到 ❌ 或 ⚠️，请记录错误信息。

---

### 步骤 3：验证节点库显示

应用启动后：

1. 查看左侧节点库面板
2. 应该看到 **"图像相机"** 标签页
3. 点击标签页，应该看到8个节点：
   - 加载图像
   - 保存图像
   - 图像显示
   - 数据显示
   - 工业相机采集
   - 实时预览
   - 快速检测
   - 视频录制

---

### 步骤 4：如果仍然不显示

#### 方案 A：手动调试

在 `plugins/plugin_ui_manager.py:L143` 添加日志：

```python
# 刷新节点库的事件过滤器
if hasattr(self.main_window, 'refresh_node_info_event_filters'):
    utils.logger.info(f"🔄 刷新节点库事件过滤器", module="plugin_ui_manager")
    
    # 添加调试日志
    tab_widget = self.main_window.nodes_palette.tab_widget()
    if tab_widget:
        utils.logger.info(f"   标签页数量: {tab_widget.count()}", module="plugin_ui_manager")
        for i in range(tab_widget.count()):
            tab_name = tab_widget.tabText(i)
            utils.logger.info(f"   标签页 {i}: {tab_name}", module="plugin_ui_manager")
    
    self.main_window.refresh_node_info_event_filters()
```

#### 方案 B：强制重新加载

在主窗口初始化后，手动调用：

```python
# 在 main_window.py 的 __init__ 末尾添加
self.plugin_ui.load_plugins_to_graph(self.node_graph)
```

---

## 📊 诊断脚本总结

已创建以下诊断脚本：

| 脚本 | 用途 | 状态 |
|------|------|------|
| `verify_io_camera_simple.py` | 验证配置和文件结构 | ✅ 通过 |
| `test_plugin_scanning.py` | 测试插件扫描机制 | ✅ 通过 |
| `check_tab_mapping.py` | 检查标签页名称映射 | ✅ 通过 |
| `diagnose_io_camera_plugin.py` | 综合诊断 | ✅ 通过 |

**结论**：后端逻辑完全正常，问题在 UI 显示层。

---

## ✅ 最终建议

1. **立即执行**：完全重启应用（清除缓存）
2. **观察日志**：确认插件加载过程无异常
3. **验证显示**：检查"图像相机"标签页是否出现
4. **如仍失败**：使用方案A添加调试日志定位问题

---

**更新日期**: 2026-05-04  
**诊断工具**: AI Assistant
