# YOLO 视觉算法插件

> **版本**: 1.0.0  
> **分类**: 识别分类  
> **资源等级**: 轻量级/中量级/重量级（按节点分级）

---

## 📋 目录

- [1. 功能概述](#1-功能概述)
- [2. 节点列表](#2-节点列表)
- [3. 硬件要求](#3-硬件要求)
- [4. 安装指南](#4-安装指南)
- [5. 使用示例](#5-使用示例)
- [6. 部署场景](#6-部署场景)
- [7. 常见问题](#7-常见问题)

---

## 1. 功能概述

本插件提供完整的 YOLO 视觉算法套件，支持：
- ✅ **目标检测**：识别图像中的物体并标注位置
- ✅ **图像分类**：对图像进行分类
- ✅ **实例分割**：像素级物体分割
- ✅ **姿态估计**：人体关键点检测
- ✅ **标注辅助**：半自动标注工具
- ✅ **模型训练**：自定义数据集训练
- ✅ **模型量化**：INT8 量化优化
- ✅ **格式导出**：ONNX/TensorRT/OpenVINO

---

## 2. 节点列表

### 2.1 AI 推理节点（轻量级 Light）

| 节点名称 | 功能 | 硬件要求 |
|---------|------|---------|
| YOLO 目标检测 | 检测图像中的物体 | CPU 2核, 2GB, GPU 可选 |
| YOLO 图像分类 | 图像分类识别 | CPU 2核, 2GB, GPU 可选 |
| YOLO 实例分割 | 像素级物体分割 | CPU 2核, 2GB, GPU 可选 |
| YOLO 姿态估计 | 人体关键点检测 | CPU 2核, 2GB, GPU 可选 |

**依赖大小**: ~500MB  
**典型耗时**: < 1s/帧

### 2.2 标注工具（中量级 Medium）

| 节点名称 | 功能 | 硬件要求 |
|---------|------|---------|
| YOLO 标注辅助 | 半自动标注工具 | CPU 4核, 8GB, GPU 可选 |

**依赖大小**: ~600MB  
**典型耗时**: 1-10s

### 2.3 训练与优化（重量级 Heavy）

| 节点名称 | 功能 | 硬件要求 |
|---------|------|---------|
| YOLO 模型训练 | 自定义数据集训练 | CPU 8+核, 16GB+, GPU 必需 |
| YOLO 模型量化 | INT8 量化优化 | CPU 8+核, 16GB+, GPU 必需 |
| YOLO 格式导出 | ONNX/TensorRT 导出 | CPU 4核, 8GB, GPU 可选 |

**依赖大小**: ~2GB + CUDA  
**典型耗时**: 分钟~小时

---

## 3. 硬件要求

### 3.1 推理节点（工厂现场可用）

```
最低配置：
- CPU: Intel i5 (2核心)
- 内存: 2GB
- GPU: 无或集成显卡
- 存储: 100MB（模型文件）

推荐配置：
- CPU: Intel i7 (4核心)
- 内存: 8GB
- GPU: NVIDIA GTX 1650 (4GB)
- 存储: 500MB
```

### 3.2 训练节点（需要高性能工作站）

```
最低配置：
- CPU: Intel i7 (8核心)
- 内存: 16GB
- GPU: NVIDIA RTX 3060 (8GB)
- 存储: 10GB（数据集 + 模型）

推荐配置：
- CPU: AMD Ryzen 9 (16核心)
- 内存: 32GB
- GPU: NVIDIA RTX 4090 (24GB)
- 存储: 100GB NVMe
```

---

## 4. 安装指南

### 4.1 快速安装

**方式一：仅安装推理依赖（推荐工厂现场）**
```bash
cd src/python/user_plugins/yolo_vision
pip install -r requirements_inference.txt
```

**方式二：安装完整套件（推荐开发工作站）**
```bash
cd src/python/user_plugins/yolo_vision
pip install -r requirements_training.txt
```

### 4.2 GPU 加速安装

如果使用 NVIDIA GPU，建议安装 CUDA 版本的 PyTorch：

```bash
# CUDA 11.8 版本
pip install torch --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1 版本（最新）
pip install torch --index-url https://download.pytorch.org/whl/cu121
```

**检查 GPU 是否可用**：
```python
import torch
print(torch.cuda.is_available())  # 应输出 True
print(torch.cuda.get_device_name(0))  # 显示 GPU 型号
```

### 4.3 预训练模型下载

首次使用节点时，模型会自动下载到 `models/` 目录。也可以手动下载：

```bash
# 下载 YOLOv8n 模型（最小最快，6.2MB）
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt -O models/yolov8n.pt

# 下载 YOLOv8s 模型（平衡速度与精度，21.5MB）
wget https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt -O models/yolov8s.pt
```

**支持的模型**：
- `yolov8n.pt` - Nano (6.2MB) - 最快，精度较低
- `yolov8s.pt` - Small (21.5MB) - 平衡
- `yolov8m.pt` - Medium (49.7MB) - 精度较高
- `yolov8l.pt` - Large (83.7MB) - 高精度
- `yolov8x.pt` - Xlarge (130MB) - 最高精度

---

## 5. 使用示例

### 5.1 目标检测工作流

```
[图像加载] → [YOLO 目标检测] → [图像显示]
```

**步骤**：
1. 从"识别分类"标签页拖拽"YOLO 目标检测"节点
2. 连接"图像加载"节点的输出到 YOLO 节点的"输入图像"端口
3. 在属性面板设置：
   - 模型类型：yolov8n（默认）
   - 置信度阈值：0.5
   - IOU 阈值：0.45
   - 计算设备：cpu（或 cuda）
4. 点击"▶ 运行"按钮
5. 双击 YOLO 节点查看标注结果

### 5.2 模型训练工作流

```
[数据集配置] → [YOLO 模型训练] → [模型保存]
```

**步骤**：
1. 准备数据集（Yolo 格式）
2. 创建 `dataset.yaml` 配置文件
3. 拖拽"YOLO 模型训练"节点
4. 设置训练参数：
   - 基础模型：yolov8n
   - 训练轮数：100
   - 批处理大小：16
   - 图像尺寸：640
5. 运行训练（需要 GPU）
6. 训练完成后，模型保存到 `trained_models/` 目录

---

## 6. 部署场景

### 6.1 工厂现场（低配工控机）

**硬件**：Intel i5, 8GB 内存, 无 GPU  
**安装**：仅推理依赖  
**节点**：YOLO 目标检测、YOLO 图像分类  
**性能**：yolov8n ~50ms/帧（CPU）

### 6.2 办公室工作站（中高配）

**硬件**：Intel i7, 32GB 内存, RTX 3060  
**安装**：完整套件  
**节点**：所有节点  
**性能**：训练 yolov8n ~10分钟/100 epochs（GPU）

### 6.3 云端训练（高性能）

**硬件**：AMD EPYC, 128GB 内存, A100 x4  
**用途**：大规模数据集训练、超参数搜索

---

## 7. 常见问题

### Q1: 缺少依赖怎么办？

**A**: 根据错误提示安装：
```
❌ 缺少依赖: ultralytics
💡 安装命令: pip install ultralytics
```

### Q2: GPU 不可用怎么办？

**A**: 节点会自动切换到 CPU 模式（速度较慢）：
```
⚠️ CUDA 不可用，已切换到 CPU 模式（速度较慢）
```

如需 GPU 加速，请安装 CUDA 版本的 PyTorch。

### Q3: 模型文件在哪里？

**A**: 首次使用时自动下载到 `models/` 目录，也可手动下载。

### Q4: 如何提高推理速度？

**A**: 
1. 使用更小的模型（yolov8n）
2. 降低图像分辨率
3. 使用 GPU 加速
4. 启用 INT8 量化

### Q5: 训练时显存不足怎么办？

**A**: 
1. 减小批处理大小（batch_size）
2. 降低图像尺寸（img_size）
3. 使用梯度累积
4. 升级 GPU

---

## 📚 相关文档

- [AI 模块资源隔离设计规范](../../../docs/AI_MODULE_RESOURCE_ISOLATION.md)
- [AI 节点开发指南](../AI_NODE_DEVELOPMENT_GUIDE.md)
- [项目 README](../../../../README.md)

---

**最后更新**: 2026-04-26  
**维护者**: OpenCV视觉系统开发团队
