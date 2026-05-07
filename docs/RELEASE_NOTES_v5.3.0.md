# Release Notes v5.3.0

## 📋 版本信息

| 项目 | 说明 |
|------|------|
| **版本号** | v5.3.0 |
| **发布日期** | 2026-05-07 |
| **分支** | master |
| **提交哈希** | accb95b |

---

## ✨ 新增功能

### 1. 节点库标签排序功能

- **功能描述**：支持通过 `plugin.json` 的 `group` 字段自定义节点库标签的显示顺序
- **实现方式**：在 `plugin.json` 中添加 `group` 数组字段，定义分组标识符的顺序
- **使用示例**：
  ```json
  "group": ["Image_Source", "Image_Analysis", "Image_Transform", "Image_Process", "Integration", "OCR", "YOLO"]
  ```

### 2. 节点库标签中文显示

- 更新了节点库标签的中文名称映射：
  | 原始名称 | 中文名称 |
  |----------|----------|
  | Image_Source | 图像源 |
  | Image_Analysis | 图像分析 |
  | Image_Transform | 图像变换 |
  | Image_Process | 图像处理 |
  | Integration | 系统集成 |
  | ocr_vision | OCR |
  | yolo_vision | YOLO |

### 3. 标签顺序优化

- 节点库标签现在按照以下顺序显示：
  1. 🖼️ 图像源
  2. 🔍 图像分析
  3. 🔄 图像变换
  4. ⚙️ 图像处理
  5. 🔗 系统集成
  6. 📝 OCR
  7. 🎯 YOLO

---

## 🛠️ 改进内容

### 插件系统改进

- 优化了插件加载流程，支持从 `plugin.json` 读取 `group` 配置
- 增强了节点分类的灵活性，允许自定义标签顺序
- 改进了标签重命名和排序的逻辑，确保顺序正确

### UI 体验提升

- 节点库面板的标签页现在按照知识结构逻辑排列
- 标签名称更加直观，便于用户快速定位所需节点
- 标签排序支持动态配置，无需修改代码即可调整顺序

---

## 🐛 修复的问题

1. **修复**：节点库标签 `Image_Source` 和 `Integration` 未正确显示为中文名称的问题
2. **修复**：OCR 和 YOLO 插件标签名称未按配置显示的问题
3. **修复**：节点库标签顺序未按照 `group` 配置排列的问题

---

## 🔄 API 变更

### 新增配置字段

**plugin.json** 新增字段：

| 字段名 | 类型 | 说明 |
|--------|------|------|
| `group` | array | 定义节点分组的显示顺序 |

**示例**：
```json
{
  "name": "builtin",
  "version": "3.0.0",
  "group": ["Image_Source", "Image_Analysis", "Image_Transform", "Image_Process", "Integration", "OCR", "YOLO"],
  "nodes": [...]
}
```

### 模型类变更

**PluginInfo** 类新增字段：
```python
group: List[str] = field(default_factory=list)  # 分组顺序（用于节点库标签页排序）
```

---

## 📦 兼容性

- **最低应用版本**：v3.1.0
- **向后兼容**：完全兼容之前的版本
- **迁移说明**：无需迁移，升级后自动使用新的标签排序功能

---

## 🚀 安装/升级说明

### 升级步骤

1. **拉取最新代码**：
   ```bash
   git pull origin master
   ```

2. **切换到版本标签**：
   ```bash
   git checkout v5.3.0
   ```

3. **安装依赖**（如需要）：
   ```bash
   pip install -r requirements.txt
   ```

4. **启动应用**：
   ```bash
   python src/python/main.py
   ```

---

## 📝 更新日志

### 提交历史

| 提交 | 描述 |
|------|------|
| accb95b | Merge feature-camera-capture-node into master for v5.3.0 |
| c4bf57d | feat(插件管理): 添加节点库标签分组排序功能 |
| e3a2705 | refactor(plugin): 重构插件包结构，合并节点模块到统一目录 |

---

## 📄 许可证

本项目遵循 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。

---

**© 2026 StudyOpenCV Team**

*如有问题或建议，请提交 Issue 或联系开发团队。*