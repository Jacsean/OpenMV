# 统一插件体系架构设计规范

## 1. 架构概述

### 1.1 目标
- 实现插件系统的统一管理
- 支持多种插件类型（Python源码、ZIP打包、二进制DLL/SO）
- 提供完整的可视化管理界面
- 保证系统安全性和稳定性

### 1.2 整体架构图
```
StduyOpenCV/
├── src/python/
│   ├── plugins/                    ← 插件系统核心（已存在）
│   │   ├── plugin_manager.py       ← 插件管理器
│   │   ├── hot_reloader.py         ← 热重载
│   │   └── sandbox.py              ← 安全沙箱
│   │
│   ├── plugin_packages/            ← 🆕 统一插件目录
│   │   ├── builtin/                ← 预置节点（需编译）
│   │   │   ├── io_camera/
│   │   │   ├── preprocessing/
│   │   │   └── ...
│   │   │
│   │   ├── marketplace/            ← 市场插件（动态加载）
│   │   │   ├── yolo_vision_v1.2.zip
│   │   │   ├── ocr_pro_v2.0.dll    ← Windows DLL插件
│   │   │   └── feature_pack.so     ← Linux SO插件
│   │   │
│   │   └── user_custom/            ← 用户自定义
│   │       └── my_nodes/
│   │
│   ├── shared_libs/                ← 🆕 共享库
│   │   ├── ai_base/                ← AI节点基类
│   │   ├── common_utils/           ← 通用工具
│   │   └── cpp_wrappers/           ← C++封装层
│   │
│   └── ui/
│       ├── node_editor.py          ← 节点编辑器（增强版）
│       └── plugin_marketplace.py   ← 🆕 插件市场UI
│
└── docs/
    └── plugins/
        └── PLUGIN_ARCHITECTURE.md  ← 🆕 架构文档
```

## 2. 插件目录结构规范

### 2.1 三层插件目录结构
- **builtin/**: 预置节点（需编译），随应用发布
- **marketplace/**: 市场插件（动态加载），支持ZIP/DLL/SO格式
- **user_custom/**: 用户自定义（git忽略）

### 2.2 插件包结构规范
每个插件包必须包含以下文件：
- `plugin.json`: 插件元数据
- `nodes.py` 或 `nodes/`: 节点实现
- `README.md`: 插件说明（可选）
- `models/`: 模型文件（如需要）
- `icons/`: 图标文件（如需要）

### 2.3 共享库目录规范
- **shared_libs/ai_base/**: AI节点基类和工具
- **shared_libs/common_utils/**: 通用工具函数
- **shared_libs/cpp_wrappers/**: C++封装层

## 3. 插件加载策略

### 3.1 三种加载模式
| 模式 | 适用场景 | 加载方式 | 示例 |
|------|----------|----------|------|
| Python源码 | 预置节点、用户自定义 | 动态import | `io_camera/` |
| ZIP打包 | 市场分发、离线安装 | 解压后按Python加载 | `yolo_pack.zip` |
| 二进制DLL/SO | 高性能算法、商业插件 | ctypes/cffi加载 | `opencv_accel.dll` |

### 3.2 加载优先级
1. `builtin/` 目录（预置节点）- 优先级最高
2. `marketplace/` 目录（市场插件）- 优先级中等
3. `user_custom/` 目录（用户插件）- 优先级最低

## 4. UI节点库功能规范

### 4.1 节点操作
- 增加节点
- 编辑节点属性
- 删除节点
- 移动节点到指定节点包

### 4.2 节点包操作
- 重新排序
- 更名
- 导出
- 删除

### 4.3 注意事项
- 修改后需提示用户重启应用生效
- 操作前需备份重要数据

## 5. 配置文件统一管理

### 5.1 plugin_registry.json
```json
{
  "version": "1.0",
  "packages": [
    {
      "name": "io_camera",
      "path": "builtin/io_camera",
      "type": "python",
      "priority": 1,
      "enabled": true,
      "category_group": "图像相机",
      "installed_at": "2026-04-27T10:00:00Z"
    },
    {
      "name": "gpu_accel",
      "path": "marketplace/binaries/opencv_cuda.dll",
      "type": "binary",
      "priority": 2,
      "enabled": true,
      "category_group": "加速计算",
      "installed_at": "2026-04-25T15:30:00Z"
    }
  ],
  "tab_order": ["图像相机", "预处理", "AI视觉", "加速计算"],
  "last_updated": "2026-04-27T14:30:00Z"
}
```

### 5.2 配置文件作用
- 集中管理所有插件元数据
- 支持快速查询和过滤
- 便于备份和迁移

## 6. 安全机制

### 6.1 沙箱保护
- 对Python插件进行权限限制
- 阻止危险操作（文件系统、网络访问等）

### 6.2 二进制插件安全
- 签名验证：市场插件必须数字签名
- 进程隔离：二进制插件运行在独立进程
- 权限控制：限制文件系统访问

## 7. 实施路线图

### Phase 1: 目录重构（1-2天）
1. 创建 `plugin_packages/` 三层结构
2. 迁移现有插件到 `builtin/`
3. 移动共享库到 `shared_libs/`
4. 更新导入路径

### Phase 2: PluginManager增强（2-3天）
1. 支持多目录扫描
2. 实现二进制插件加载器
3. 实现ZIP插件解压逻辑
4. 添加 `plugin_registry.json` 管理

### Phase 3: UI增强（3-5天）
1. 节点包重命名功能
2. 节点移动功能
3. 节点包排序持久化
4. 插件市场UI框架

### Phase 4: 二进制插件支持（5-7天）
1. 定义C接口规范
2. 实现ctypes加载器
3. 编写示例DLL插件
4. 测试跨平台兼容性

### Phase 5: 插件市场（未来）
1. 在线插件浏览
2. 一键安装/卸载
3. 评分和评论系统
4. 开发者上传工具

## 8. 关键设计决策

### 8.1 运行时节点移动策略
采用"修改后重启生效"策略：
- 实现简单可靠
- 符合NodeGraphQt的设计哲学
- 在UI中明确提示用户重启

### 8.2 依赖关系管理
插件可声明依赖关系，系统按拓扑排序加载：
- 先加载被依赖的插件
- 检测循环依赖并报错
- 支持内部依赖引用

## 9. 迁移指南

### 9.1 从旧结构迁移到新结构
1. 备份当前插件
2. 创建新的目录结构
3. 迁移插件到对应目录
4. 更新配置文件
5. 测试功能完整性

### 9.2 用户数据保护
- 保留用户的工作流不受影响
- 提供插件迁移向导
- 支持回滚到旧版本