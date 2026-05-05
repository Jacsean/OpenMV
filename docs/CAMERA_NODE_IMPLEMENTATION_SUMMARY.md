# 工业相机采集节点实施总结

## 📋 项目概述

**分支名称**: `feature-camera-capture-node`  
**实施日期**: 2026-05-04  
**版本**: v1.0.0  

**目标**: 实现支持多相机同时工作的工业相机采集节点，包含配置文件管理、实时预览窗口、快速控制按钮等功能。

---

## ✅ 已完成功能

### 1. 核心组件

#### **CameraManager 单例** (`camera_manager.py`)
- ✅ 加载并解析 `plugin_camera.json` 配置
- ✅ 管理多相机实例字典 `{camera_id: camera_instance}`
- ✅ 支持真实相机和模拟相机
- ✅ 线程安全的相机访问
- ✅ 自动回退到模拟相机（无硬件时）

**关键类**:
- `CameraManager`: 单例管理器
- `SimulatedCamera`: 模拟相机（生成测试图案）
- `RealCamera`: 真实相机包装类（占位实现）

#### **CameraCaptureNode 节点** (`nodes/camera_capture.py`)
- ✅ 继承 `BaseNode`，符合节点规范
- ✅ 双输出端口：单帧图像 + 连续图像流
- ✅ 属性面板参数（Seat索引、曝光、增益、白平衡等）
- ✅ 后台线程持续采集，维护 `_latest_frame` 缓存
- ✅ `process()` 方法返回最新帧供下游节点使用
- ✅ 支持初始化、打开、关闭、开始/停止采集
- ✅ 双击节点打开预览窗口

**主要方法**:
```python
initialize_camera()  # 初始化相机设备
open_camera()        # 打开相机
close_camera()       # 关闭相机
start_acquisition()  # 启动后台采集线程
stop_acquisition()   # 停止采集
grab_once()          # 单次采集（软件触发）
get_cached_image()   # 获取缓存的最新图像
open_preview_window() # 打开预览窗口
process(inputs)      # 工作流执行时返回最新帧
```

#### **CameraPreviewDialog 预览窗口** (`camera_preview_dialog.py`)
- ✅ 非模态 QDialog，支持多窗口并存
- ✅ 顶部工具栏：初始化、打开、开始/停止采集、保存、刷新
- ✅ QGraphicsView 显示图像，支持滚轮缩放（Ctrl+滚轮）、拖拽平移
- ✅ 自动滚动条（图像超出视口时显示）
- ✅ 底部状态栏：连接状态、FPS、累计帧数
- ✅ 定时器每 100ms 刷新预览（10fps）
- ✅ 保存当前帧到文件（PNG/JPG/BMP）

**UI布局**:
```
┌──────────────────────────────────────┐
│ [🔧初始化] [📡打开] [▶️开始] [⏸️停止] │
│                  [💾保存] [🔄刷新]    │
├──────────────────────────────────────┤
│                                      │
│     [实时图像 - 可缩放/平移]          │
│                                      │
├──────────────────────────────────────┤
│ 🟢采集中 | FPS: 28.5 | 帧数: 15234   │
└──────────────────────────────────────┘
```

---

### 2. 配置文件扩展

#### **plugin_camera.json**
- ✅ Dictionary 段增加 `image_params`（白平衡、伽马、对比度等）
- ✅ Dictionary 段增加 `trigger_params`（触发模式、延迟等）
- ✅ Dictionary 段增加 `roi_params`（ROI支持、最小尺寸等）
- ✅ Seats 段增加模拟相机配置（SN: SIMULATED_001）
- ✅ Seats 段支持 `custom_params` 覆盖默认值

**配置示例**:
```json
{
  "CCameraMVC1000mf": {
    "resolution": {"width": "1280", "height": "1024"},
    "image_params": {
      "white_balance": {"mode": "auto", "red_gain": 1.5},
      "gamma": {"value": 1.0},
      "contrast": {"default": 128}
    },
    "trigger_params": {
      "trigger_mode": "software"
    }
  }
}
```

---

### 3. UI集成

#### **主窗口双击事件** (`main_window.py`)
- ✅ 在 `_on_node_double_clicked()` 中检测 CameraCaptureNode
- ✅ 调用 `node.open_preview_window()` 打开预览窗口
- ✅ 错误处理和日志记录

#### **节点注册** (`plugin.json`)
- ✅ 注册 CameraCaptureNode 到 nodes 数组
- ✅ category_group: "图像相机"
- ✅ category: "设备采集"
- ✅ resource_level: "light"
- ✅ 声明依赖：opencv-python, numpy

#### **模块导出** (`nodes/__init__.py`)
- ✅ 导出 CameraCaptureNode

---

### 4. 文档与测试

#### **README.md**
- ✅ 功能特性介绍
- ✅ 详细使用步骤（8个步骤）
- ✅ 配置文件说明
- ✅ 预览窗口功能详解
- ✅ 常见问题解答（5个Q&A）
- ✅ 技术架构说明
- ✅ 扩展开发指南

#### **测试脚本** (`tests/test_camera_node.py`)
- ✅ 测试1: 配置文件加载
- ✅ 测试2: 模拟相机图像生成
- ✅ 测试3: 相机初始化
- ✅ 测试4: 多相机并发
- ✅ 所有测试通过 ✅

---

## 📊 技术架构

### 数据流图

```
┌─────────────┐
│ Camera HW   │ 或 SimulatedCamera
└──────┬──────┘
       │ grab_frame()
       ↓
┌─────────────┐
│ Acquisition │ 后台线程 (daemon=True)
│   Thread    │ while is_acquiring:
└──────┬──────┘   frame = camera.grab_frame()
       │          _latest_frame = frame.copy()
       ↓          time.sleep(1/framerate)
┌─────────────┐
│ _latest_frame│ 缓存（threading.Lock保护）
└──────┬──────┘
       │
       ├→ process() → 输出端口（单帧/连续）
       │
       └→ get_cached_image() → 预览窗口
```

### 线程安全

- **锁机制**: `threading.Lock` 保护 `_latest_frame`
- **深拷贝**: `frame.copy()` 避免竞争条件
- **守护线程**: `daemon=True`，主程序退出时自动终止

---

## 🎯 设计决策

### 1. 输出模式选择

**决策**: 采用**端口轮询模式**（第一阶段）

**理由**:
- ✅ 兼容现有 NodeGraphQt 架构
- ✅ 无需修改工作流引擎
- ✅ 易于理解和调试
- ✅ 适合 5-10fps 工业场景

**局限性**:
- ⚠️ 不是真正的"流式处理"
- ⚠️ 下游处理速度慢于采集速度时会丢帧

**未来扩展**: 可扩展"订阅回调模式"支持 >15fps 高速实时处理

---

### 2. 多相机管理

**决策**: CameraManager 单例模式

**理由**:
- ✅ 集中管理资源，避免冲突
- ✅ 线程安全的相机访问
- ✅ 支持动态添加/移除相机

**实现**:
```python
manager = CameraManager.get_instance()
camera_id = manager.initialize_camera(seat_index)
camera = manager.get_camera(camera_id)
```

---

### 3. 配置文件结构

**决策**: 沿用现有 Dictionary + Seats 双段结构

**理由**:
- ✅ 分离型号定义和运行时实例
- ✅ 支持同一型号多个相机（不同SN）
- ✅ Seats 可覆盖 Dictionary 默认值

---

### 4. 模拟相机

**决策**: 内置支持，通过特殊 SN 标识

**理由**:
- ✅ 无需硬件即可测试工作流
- ✅ 可控制帧率、分辨率、图像内容
- ✅ 支持注入故障用于鲁棒性测试

**启用方式**: SN 以 "SIMULATED_" 开头

---

## 📝 Git 提交历史

```
f7f2994 feat: 添加相机节点测试脚本并修复分辨率问题
a36fdce feat: UI集成相机节点及添加使用文档
73747e2 feat: 实现CameraCaptureNode工业相机采集节点及预览窗口
bbd74e3 feat: 扩展相机配置文件并实现CameraManager单例
```

**总计**:
- 4 次提交
- 新增文件: 5 个
- 修改文件: 3 个
- 代码行数: ~1500 行

---

## 🔍 测试结果

### 测试环境
- Python 3.x
- OpenCV 4.5+
- NumPy
- PySide2

### 测试用例

| 测试项 | 状态 | 说明 |
|--------|------|------|
| 配置加载 | ✅ | 5种型号，5个Seat |
| 模拟相机 | ✅ | 图像形状正确 (480, 640, 3) |
| 相机初始化 | ✅ | Seat 4 (SIMULATED_001) |
| 多相机并发 | ✅ | 同时初始化2个相机 |

**结论**: 🎉 所有测试通过！

---

## 🚀 下一步计划

### 短期（Phase 2）
1. **集成真实相机SDK**
   - 替换 RealCamera 占位实现
   - 支持海康威视、巴斯勒等品牌
   - DLL 驱动加载和设备枚举

2. **性能优化**
   - 环形缓冲区替代简单缓存
   - GPU 加速图像转换
   - 零拷贝数据传输

3. **高级功能**
   - ROI 动态调整
   - 外部触发支持
   - 多路同步采集

### 中期（Phase 3）
1. **订阅回调模式**
   - 实现发布-订阅机制
   - 支持 >15fps 高速实时处理
   - 多订阅者并行处理

2. **图像预处理**
   - 白平衡校正
   - 暗电流校正
   - 镜头畸变校正

3. **数据录制**
   - 视频录制（AVI/MP4）
   - 图像序列保存
   - 元数据记录

### 长期（Phase 4）
1. **相机校准工具**
   - 内参标定
   - 外参标定
   - 手眼标定

2. **3D视觉支持**
   - 双目相机
   - 结构光
   - 点云处理

3. **AI集成**
   - 实时目标检测
   - 缺陷分类
   - 质量预测

---

## 📚 相关文档

- [README.md](src/python/plugin_packages/builtin/io_camera/README.md) - 使用说明
- [plugin_camera.json](src/python/plugin_packages/builtin/io_camera/plugin_camera.json) - 相机配置
- [test_camera_node.py](tests/test_camera_node.py) - 测试脚本

---

## 👥 贡献者

- 开发: AI Assistant
- 审核: Pending
- 测试: Passed

---

## 📄 许可证

本项目遵循 MIT 许可证。

---

**实施完成日期**: 2026-05-04  
**状态**: ✅ 已完成核心功能，待集成真实相机SDK
