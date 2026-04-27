# 用户插件目录

本目录包含所有用户自定义和第三方插件包。

## 📁 目录结构

根据新的统一插件体系架构，本目录将重构为以下结构：

```
user_plugins/
├── builtin/                ← 预置节点（随应用发布）
│   ├── io_camera/          ← 图像IO
│   ├── preprocessing/      ← 预处理
│   ├── feature_extraction/ ← 特征提取
│   ├── measurement/        ← 测量分析
│   ├── recognition/        ← 识别分类
│   ├── integration/        ← 系统集成
│   └── ai_vision/          ← AI视觉
│
├── marketplace/            ← 市场插件（动态加载）
│   ├── installed/          ← 已解压的插件
│   ├── cache/              ← ZIP缓存
│   └── binaries/           ← 二进制插件
│
└── user_custom/            ← 用户自定义（git忽略）
    └── my_nodes/
```

## 📋 插件开发规范

每个插件包必须包含：
- `plugin.json`: 插件元数据
- `nodes.py` 或 `nodes/`: 节点实现
- `README.md`: 插件说明（可选）

详细规范请参考：[PLUGIN_ARCHITECTURE.md](../../../docs/plugins/PLUGIN_ARCHITECTURE.md)

## ⚠️ 注意事项

1. **禁止在根目录放置非插件文件**：如.py脚本、.md文档等
2. **共享库应放在shared_libs/目录**：AI基类、工具模块等
3. **内部模块使用下划线前缀**：如 `_common_utils/`