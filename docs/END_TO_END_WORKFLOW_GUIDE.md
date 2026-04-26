# 端到端示例工作流使用指南

本文档提供完整的端到端示例工作流，展示从图像采集到 AI 推理的完整流程。

---

## 📋 目录

1. [示例 1：图像采集 → 预处理 → AI 推理](#示例-1图像采集--预处理--ai-推理)
2. [示例 2：YOLO 训练 → 量化 → 推理](#示例-2yolo-训练--量化--推理)
3. [如何加载工作流](#如何加载工作流)
4. [常见问题解答](#常见问题解答)

---

## 示例 1：图像采集 → 预处理 → AI 推理

**文件位置**: `src/python/workspace/workflows/end_to_end_yolo_detection.json`

### 🎯 适用场景
- 快速验证 YOLO 目标检测效果
- 测试不同预处理对检测结果的影响
- 工厂现场的实时检测部署

### 📊 工作流结构

```
[图像加载] → [灰度化] → [高斯模糊] → [YOLO 目标检测] → [图像显示]
```

### 🔧 节点说明

| 步骤 | 节点名称 | 插件包 | 功能 | 资源等级 |
|------|---------|--------|------|---------|
| 1 | 图像加载 | io_camera | 从文件加载图像 | light |
| 2 | 灰度化 | preprocessing | 彩色转灰度，减少计算量 | light |
| 3 | 高斯模糊 | preprocessing | 降噪，提升检测精度 | light |
| 4 | YOLO 目标检测 | yolo_vision | 实时目标检测 | light |
| 5 | 图像显示 | io_camera | 可视化检测结果 | light |

### ⚙️ 配置参数

#### 图像加载节点
```json
{
  "file_path": "path/to/your/image.jpg"  // 修改为你的图像路径
}
```

#### 高斯模糊节点
```json
{
  "kernel_size": "5",   // 核大小（3-15，奇数）
  "sigma_x": "0"        // 标准差（0 表示自动计算）
}
```

#### YOLO 目标检测节点
```json
{
  "model_name": "yolov8n",              // 模型选择：yolov8n/s/m/l/x
  "confidence_threshold": "0.5",        // 置信度阈值（0.3-0.7）
  "iou_threshold": "0.45",              // NMS IoU 阈值
  "classes": "person,car,bicycle"       // 要检测的类别
}
```

### 💡 使用技巧

1. **调整预处理参数**：
   - 如果检测效果不佳，尝试调整高斯模糊的 `kernel_size`
   - 对于低光照图像，可以先添加亮度对比度调整节点

2. **选择合适的 YOLO 模型**：
   - `yolov8n`: 最快，适合实时检测（推荐）
   - `yolov8s`: 平衡速度和精度
   - `yolov8m/l/x`: 更高精度，但速度较慢

3. **优化检测性能**：
   - 降低 `confidence_threshold` 可以检测到更多小目标
   - 提高 `iou_threshold` 可以减少重复检测框

### 📈 性能预期

| 硬件配置 | 推理速度 | 总延迟 |
|---------|---------|--------|
| CPU (i5/i7) | ~100ms/帧 | ~150ms |
| GPU (RTX 3060) | ~20ms/帧 | ~70ms |

---

## 示例 2：YOLO 训练 → 量化 → 推理

**文件位置**: `src/python/workspace/workflows/end_to_end_yolo_training_pipeline.json`

### 🎯 适用场景
- 自定义数据集的模型训练
- 模型优化和量化部署
- 从开发到生产的完整生命周期管理

### 📊 工作流结构

```
[数据集路径] → [YOLO 模型训练] → [训练好的模型]
                                    ↓
                              [YOLO 模型量化] → [量化后的模型]
                                                    ↓
[测试图像] → [YOLO 推理（量化模型）] → [结果可视化]
```

### 🔧 节点说明

| 步骤 | 节点名称 | 插件包 | 功能 | 资源等级 |
|------|---------|--------|------|---------|
| 1 | 数据集路径 | io_camera | 指定数据集和配置文件 | light |
| 2 | YOLO 模型训练 | yolo_vision | 训练自定义模型 | **heavy** |
| 3 | 训练好的模型 | yolo_vision | 查看训练结果 | light |
| 4 | YOLO 模型量化 | yolo_vision | 导出为 ONNX/TensorRT | **heavy** |
| 5 | 量化后的模型 | yolo_vision | 查看量化报告 | light |
| 6 | YOLO 推理 | yolo_vision | 使用量化模型检测 | light |
| 7 | 结果可视化 | io_camera | 显示检测结果 | light |

### ⚙️ 配置参数

#### 数据集路径节点
```json
{
  "dataset_path": "path/to/annotated_dataset",
  "dataset_yaml": "path/to/dataset.yaml"
}
```

**数据集格式要求**：
```
annotated_dataset/
├── dataset.yaml
├── images/
│   ├── train/
│   ├── val/
│   └── test/
└── labels/
    ├── train/
    ├── val/
    └── test/
```

#### YOLO 模型训练节点
```json
{
  "model_name": "yolov8n",      // 基础模型
  "epochs": "100",              // 训练轮数
  "batch_size": "16",           // 批次大小
  "img_size": "640",            // 输入图像尺寸
  "learning_rate": "0.01",      // 学习率
  "output_dir": "./trained_models"
}
```

#### YOLO 模型量化节点
```json
{
  "export_format": "onnx",      // 导出格式：onnx/tensorrt/openvino
  "precision": "fp16",          // 精度：fp32/fp16/int8
  "opset_version": "11",        // ONNX Opset 版本
  "dynamic_axes": "true",       // 支持动态输入尺寸
  "output_dir": "./quantized_models"
}
```

### 💡 使用技巧

1. **训练前准备**：
   - 确保数据集已正确标注（使用 YOLOAnnotatorNode）
   - 检查 `dataset.yaml` 中的类别名称和数量
   - 建议至少准备 100+ 张标注图像

2. **训练参数调优**：
   - `epochs`: 小数据集 50-100，大数据集 200-300
   - `batch_size`: 根据显存调整（RTX 3060: 16, RTX 4090: 32+）
   - `img_size`: 640 是默认值，高分辨率可设为 1280

3. **量化策略选择**：
   - **ONNX + FP16**: 通用性好，跨平台兼容（推荐）
   - **TensorRT + FP16**: NVIDIA GPU 极致优化
   - **INT8**: 需要校准数据，速度最快但精度略降

4. **部署建议**：
   - **办公室工作站**: 执行步骤 1-5（训练和量化）
   - **工厂现场**: 执行步骤 6-7（使用量化模型推理）

### 📈 性能预期

| 阶段 | 耗时 | 硬件要求 |
|------|------|---------|
| 模型训练（100 epochs） | 2-4 小时 | GPU RTX 3060+ |
| 模型量化 | 5-10 分钟 | GPU RTX 3060+ |
| 推理（FP16 量化后） | ~30ms/帧 | CPU/GPU 均可 |
| 加速比 | 1.5-2x | 相比原始 PyTorch |

---

## 如何加载工作流

### 方法 1：通过主菜单加载

1. 启动应用程序
2. 点击菜单栏 **文件** → **打开工作流**
3. 选择工作流 JSON 文件
4. 点击 **确定**

### 方法 2：拖拽加载

1. 打开文件资源管理器
2. 找到工作流 JSON 文件
3. 拖拽到应用程序窗口

### 方法 3：通过最近工程列表

1. 点击菜单栏 **文件** → **最近工程**
2. 选择之前打开过的工作流

---

## 常见问题解答

### Q1: 为什么 YOLO 节点显示为灰色（禁用状态）？

**A**: 可能原因：
1. 缺少依赖库 `ultralytics`，请运行：
   ```bash
   pip install ultralytics
   ```
2. 硬件不满足要求（训练/量化节点需要 GPU）
3. 模型文件未下载，运行以下脚本下载：
   ```bash
   python src/python/user_plugins/yolo_vision/models/download_models.py
   ```

### Q2: 如何修改图像路径？

**A**: 
1. 双击节点打开属性面板
2. 找到 `file_path` 或 `dataset_path` 字段
3. 修改为你的实际路径
4. 点击 **应用** 保存

### Q3: 训练时显存不足怎么办？

**A**: 可以尝试：
1. 减小 `batch_size`（例如从 16 改为 8）
2. 减小 `img_size`（例如从 640 改为 416）
3. 使用更小的模型（yolov8n 而不是 yolov8m）
4. 关闭其他占用显存的程序

### Q4: 量化后精度下降太多怎么办？

**A**: 
1. 尝试使用 FP16 而不是 INT8
2. 如果使用 INT8，增加校准数据数量（至少 100 张）
3. 确保校准数据覆盖各种场景（不同角度、光照等）
4. 检查原始模型的 mAP 是否足够高（>0.8）

### Q5: 如何在工厂现场部署？

**A**: 
1. 在办公室工作站完成训练和量化（步骤 1-5）
2. 将量化后的模型文件（.onnx）复制到工厂工控机
3. 在工厂机器上只加载推理节点（步骤 6-7）
4. 确保工厂机器安装了 `ultralytics` 和 `opencv-python`

---

## 📚 相关文档

- [AI 模块资源隔离设计规范](../../docs/AI_MODULE_RESOURCE_ISOLATION.md)
- [AI 节点开发指南](../../user_plugins/AI_NODE_DEVELOPMENT_GUIDE.md)
- [YOLO 插件 README](../../user_plugins/yolo_vision/README.md)

---

## 🚀 下一步

- 尝试修改工作流，添加更多预处理节点（如边缘检测、形态学操作）
- 创建自己的自定义数据集并训练模型
- 探索其他 AI 插件（OCR、人脸识别等）

祝你使用愉快！🎉
