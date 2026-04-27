# 统一插件体系架构设计规范（改进版）

## 1. 架构概述

### 1.1 目标
- 实现插件系统的统一管理
- 支持多种插件类型（Python源码、ZIP打包、二进制DLL/SO）
- 提供完整的可视化管理界面
- 保证系统安全性和稳定性
- **简化架构**：采用两层结构，降低复杂度

### 1.2 整体架构图（改进版）
```
StduyOpenCV/
├── src/python/
│   ├── plugins/                    ← 插件系统核心（已存在）
│   │   ├── plugin_manager.py       ← 插件管理器
│   │   ├── hot_reloader.py         ← 热重载
│   │   └── sandbox.py              ← 安全沙箱
│   │
│   ├── plugin_packages/            ← 🆕 统一插件目录（两层结构）
│   │   ├── builtin/                ← 内置节点（官方发布，需编译）
│   │   │   ├── io_camera/          ← 图像IO
│   │   │   ├── preprocessing/      ← 预处理
│   │   │   ├── feature_extraction/ ← 特征提取
│   │   │   ├── measurement/        ← 测量分析
│   │   │   ├── recognition/        ← 识别分类
│   │   │   ├── integration/        ← 系统集成
│   │   │   └── match_location/     ← 匹配定位
│   │   │
│   │   └── marketplace/            ← 市场插件（动态加载，可分享）
│   │       ├── installed/          ← 已安装的插件
│   │       │   ├── yolo_vision/    ← YOLO目标检测
│   │       │   ├── ocr_pro/        ← 高级OCR识别
│   │       │   └── gpu_accel/      ← GPU加速计算
│   │       │
│   │       ├── cache/              ← ZIP缓存（待安装）
│   │       │   ├── yolo_vision_v1.2.zip
│   │       │   └── ocr_pro_v2.0.zip
│   │       │
│   │       └── binaries/           ← 二进制插件（DLL/SO）
│   │           ├── Windows/
│   │           │   ├── opencv_cuda.dll
│   │           │   └── tensorrt_inference.dll
│   │           ├── Linux/
│   │           │   ├── opencv_cuda.so
│   │           │   └── tensorrt_inference.so
│   │           └── MacOS/
│   │               ├── opencv_cuda.dylib
│   │               └── tensorrt_inference.dylib
│   │
│   ├── shared_libs/                ← 🆕 共享库（通用）
│   │   ├── node_base/              ← 🆕 通用节点基类（原ai_base）
│   │   │   ├── __init__.py
│   │   │   ├── base_node.py        ← 统一节点基类
│   │   │   ├── performance_monitor.py
│   │   │   └── resource_manager.py
│   │   │
│   │   ├── common_utils/           ← 通用工具
│   │   │   ├── image_utils.py
│   │   │   ├── file_utils.py
│   │   │   └── logging_utils.py
│   │   │
│   │   └── cpp_wrappers/           ← C++封装层
│   │       ├── opencv_wrapper/
│   │       └── ai_inference/
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

### 2.1 两层插件目录结构（改进）
- **builtin/**: 内置节点（官方发布，需编译），随应用发布
  - 以OpenCV算法为主
  - 项目迭代中，新的通用算法固化在此
  - 不可卸载，稳定性高
  
- **marketplace/**: 市场插件（动态加载，可分享）
  - 互联网节点市场，实现节点共享
  - 专用或用户定制节点
  - 可通过在线市场下载安装
  - 支持ZIP/DLL/SO格式
  - 可卸载，灵活性高

**设计理由：**
- ✅ **取消user_custom/**：简化架构，减少认知负担
- ✅ **统一管理**：用户开发的插件直接在marketplace/中创建
- ✅ **灵活迁移**：实验性插件可随时升级为正式市场插件

### 2.2 插件包结构规范
每个插件包必须包含以下文件：
- `plugin.json`: 插件元数据
- `nodes.py` 或 `nodes/`: 节点实现
- `README.md`: 插件说明（可选）
- `models/`: 模型文件（如需要）
- `icons/`: 图标文件（如需要）

### 2.3 共享库目录规范（改进）
- **shared_libs/node_base/**: 🆕 通用节点基类和工具（原ai_base）
  - 适用于所有类型的节点（OpenCV + AI）
  - 避免"仅用于AI"的误解
  - 强调"统一节点"理念
  
- **shared_libs/common_utils/**: 通用工具函数
- **shared_libs/cpp_wrappers/**: C++封装层

**重命名理由：**
- ✅ `node_base` 更通用，符合统一插件体系理念
- ✅ 避免OpenCV节点开发者的困惑
- ✅ 强调所有节点共享同一基类

## 3. 插件加载策略

### 3.1 三种加载模式
| 模式 | 适用场景 | 加载方式 | 示例 |
|------|----------|----------|------|
| Python源码 | 预置节点、市场插件 | 动态import | `io_camera/` |
| ZIP打包 | 市场分发、离线安装 | 解压后按Python加载 | `yolo_pack.zip` |
| 二进制DLL/SO | 高性能算法、商业插件 | ctypes/cffi加载 | `opencv_accel.dll` |

### 3.2 加载优先级（改进）
1. `builtin/` 目录（内置节点）- 优先级最高
2. `marketplace/` 目录（市场插件）- 优先级中等

**移除user_custom/后的简化逻辑**

## 4. builtin与marketplace的定位对比

| 维度 | builtin/ | marketplace/ |
|------|----------|--------------|
| **定位** | 官方内置节点 | 市场共享节点 |
| **内容** | OpenCV基础算法 | AI模型、专用算法、用户定制 |
| **维护者** | 核心团队 | 第三方开发者/社区/用户 |
| **更新方式** | 随应用发布 | 在线下载安装 |
| **稳定性** | 高（充分测试） | 中等（依赖作者质量） |
| **可卸载** | ❌ 不可卸载 | ✅ 可卸载 |
| **编译需求** | 需要（C++扩展） | 可选（Python/DLL） |
| **典型示例** | io_camera, preprocessing | yolo_vision, ocr_pro |

### 4.1 builtin/ 详细说明
**用途：**
- 存储官方发布的内置节点
- 以OpenCV算法为主的基础功能
- 项目迭代过程中，新的通用算法固化在此

**特点：**
- ✅ 高稳定性：经过充分测试
- ✅ 随应用分发：用户无需额外安装
- ✅ 不可卸载：保证核心功能完整
- ✅ 需要编译：可能包含C++扩展

**典型内容：**
- 图像IO操作（相机、文件、视频）
- 图像预处理（滤波、增强、校正）
- 特征提取（边缘、角点、Blob分析）
- 测量分析（尺寸、角度、位置）
- 系统集成（PLC、数据库、文件系统）

### 4.2 marketplace/ 详细说明
**用途：**
- 互联网节点市场，实现节点共享
- 专用或用户定制节点的集散地
- 支持在线分享和下载

**特点：**
- ✅ 灵活性高：可随时安装/卸载
- ✅ 生态丰富：第三方开发者贡献
- ✅ 更新频繁：独立于应用版本
- ✅ 多格式支持：Python/ZIP/DLL/SO

**子目录结构：**
- `installed/`: 已安装并解压的插件
- `cache/`: ZIP格式的插件缓存（待安装）
- `binaries/`: 二进制插件（按平台分类）

**典型内容：**
- AI推理节点（YOLO、OCR、分类）
- 行业专用算法（医疗、工业检测）
- GPU加速插件
- 用户实验性节点

## 5. UI节点库功能规范

### 5.1 节点操作
- 增加节点
- 编辑节点属性
- 删除节点
- 移动节点到指定节点包（builtin ↔ marketplace）

### 5.2 节点包操作
- 重新排序
- 更名
- 导出
- 删除（仅marketplace/中的插件）

### 5.3 注意事项
- 修改后需提示用户重启应用生效
- 操作前需备份重要数据
- builtin/中的插件不可删除

## 6. 配置文件统一管理

### 6.1 plugin_registry.json
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
      "source": "builtin",
      "installed_at": "2026-04-27T10:00:00Z"
    },
    {
      "name": "yolo_vision",
      "path": "marketplace/installed/yolo_vision",
      "type": "python",
      "priority": 2,
      "enabled": true,
      "category_group": "AI视觉",
      "source": "marketplace",
      "installed_at": "2026-04-25T15:30:00Z"
    }
  ],
  "tab_order": ["图像相机", "预处理", "AI视觉", "加速计算"],
  "last_updated": "2026-04-27T14:30:00Z"
}
```

### 6.2 配置文件作用
- 集中管理所有插件元数据
- 支持快速查询和过滤
- 便于备份和迁移
- 记录插件来源（builtin/marketplace）

## 7. 安全机制

### 7.1 沙箱保护
- 对Python插件进行权限限制
- 阻止危险操作（文件系统、网络访问等）

### 7.2 二进制插件安全
- 签名验证：市场插件必须数字签名
- 进程隔离：二进制插件运行在独立进程
- 权限控制：限制文件系统访问

## 8. 实施路线图

### Phase 1: 目录重构（1-2天）
1. 创建 `plugin_packages/` 两层结构（builtin + marketplace）
2. 创建 `shared_libs/node_base/` 目录（而非ai_base）
3. 迁移现有插件到 `builtin/`
4. 移动共享库文件到 `shared_libs/node_base/`
5. 更新导入路径
6. 更新.gitignore配置

### Phase 2: PluginManager增强（2-3天）
1. 支持两层目录扫描（移除user_custom逻辑）
2. 实现 `node_base` 的统一基类
3. 实现二进制插件加载器
4. 实现ZIP插件解压逻辑
5. 添加 `plugin_registry.json` 管理
6. 区分builtin/marketplace的加载策略

### Phase 3: UI增强（3-5天）
1. 节点包重命名功能
2. 节点移动功能（builtin ↔ marketplace）
3. 节点包排序持久化
4. 插件市场UI框架
5. 插件安装/卸载功能

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

## 9. 关键设计决策

### 9.1 为什么取消user_custom/？
**理由：**
1. ✅ **简化架构**：两层结构比三层更清晰
2. ✅ **减少认知负担**：用户不需要理解三层区别
3. ✅ **统一管理**：所有非内置插件都在marketplace/
4. ✅ **灵活迁移**：实验性插件可随时升级为正式插件

**替代方案：**
- 用户在开发阶段直接在 `marketplace/` 目录下创建插件
- 通过Git的 `.gitignore` 规则排除未提交的插件
- 或者提供一个 `development/` 目录作为临时工作区（可选）

### 9.2 为什么重命名ai_base为node_base？
**理由：**
1. ✅ **通用性**：适用于所有类型的节点（OpenCV + AI）
2. ✅ **避免误解**：不会让人误以为只用于AI节点
3. ✅ **统一理念**：符合"统一插件体系"的设计目标
4. ✅ **降低困惑**：OpenCV节点开发者不会感到排斥

### 9.3 builtin与marketplace的核心差异
**builtin/（内置节点）：**
- 官方发布，核心团队维护
- 以OpenCV算法为主
- 随应用分发，不可卸载
- 高稳定性，低更新频率

**marketplace/（市场插件）：**
- 第三方/社区/用户贡献
- AI模型、专用算法、定制功能
- 在线下载安装，可卸载
- 灵活性高，更新频繁

## 10. 迁移指南

### 10.1 从旧结构迁移到新结构
1. 备份当前插件
2. 创建新的两层目录结构
3. 迁移插件到builtin/或marketplace/
4. 重命名ai_base为node_base
5. 更新配置文件
6. 测试功能完整性

### 10.2 用户数据保护
- 保留用户的工作流不受影响
- 提供插件迁移向导
- 支持回滚到旧版本