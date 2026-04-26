# AI 模块资源隔离设计规范

> **文档说明**: 本文档定义在工业自动化场景下，AI/深度学习功能模块的设计规范和最佳实践。旨在平衡功能完整性与硬件资源限制，确保系统能在不同配置的环境中稳定运行。

---

## 📋 目录

- [1. 设计背景与目标](#1-设计背景与目标)
- [2. 核心设计原则](#2-核心设计原则)
- [3. 功能分级体系](#3-功能分级体系)
- [4. 插件包结构设计](#4-插件包结构设计)
- [5. 依赖管理策略](#5-依赖管理策略)
- [6. 部署场景适配](#6-部署场景适配)
- [7. 实施指南](#7-实施指南)
- [8. 示例：YOLO 视觉插件](#8-示例yolo-视觉插件)

---

## 1. 设计背景与目标

### 1.1 工业现场挑战

**硬件限制**：
- 工厂工控机配置普遍较低（CPU i5、8GB 内存、无独立 GPU）
- 训练和量化需要高性能工作站（GPU RTX 3060+、32GB 内存）
- 云端训练需要顶级配置（A100、128GB 内存）

**业务需求**：
- 现场需要实时推理（检测/分类/分割）
- 办公室需要模型训练和优化
- 云端需要大规模数据处理

### 1.2 设计目标

| 维度 | 目标描述 | 衡量指标 |
|------|---------|---------|
| **资源隔离** | 轻量级与重量级功能物理分离 | 低配机器仅安装推理节点即可运行 |
| **灵活部署** | 根据硬件条件选择性安装组件 | 提供安装向导自动推荐 |
| **职责清晰** | 每个节点专注单一功能 | 代码可维护性提升 50% |
| **依赖精简** | 避免不必要的重型库 | 推理依赖控制在 500MB 以内 |
| **用户体验** | 清晰的错误提示和引导 | 用户能快速定位问题 |

---

## 2. 核心设计原则

### 2.1 功能分级隔离原则

**核心理念**：按资源消耗将 AI 功能分为三级，实现物理隔离

```
轻量级 (Light)        中量级 (Medium)       重量级 (Heavy)
├── 模型推理          ├── 标注辅助           ├── 模型训练
├── 数据预处理        ├── 数据增强           ├── 模型量化
└── 结果后处理        └── 可视化分析         └── 格式导出
```

**分级标准**：

| 等级 | CPU | 内存 | GPU | 存储 | 典型耗时 |
|------|-----|------|-----|------|---------|
| **Light** | 2 核心 | 2GB | 可选 | 100MB | < 1s |
| **Medium** | 4 核心 | 8GB | 可选 | 1GB | 1-10s |
| **Heavy** | 8+ 核心 | 16GB+ | 必需 | 10GB+ | 分钟~小时 |

### 2.2 依赖分离管理原则

**核心理念**：不同等级的功能使用独立的依赖文件

```
plugin_package/
├── requirements_inference.txt   # 推理依赖 (~500MB)
├── requirements_training.txt    # 训练依赖 (~2GB + CUDA)
└── requirements_annotation.txt  # 标注依赖 (~100MB)
```

**优势**：
- ✅ 按需安装，节省磁盘空间
- ✅ 避免依赖冲突
- ✅ 清晰的版本管理

### 2.3 部署适配原则

**核心理念**：根据目标硬件自动推荐安装组件

```python
def recommend_installation():
    """根据硬件条件推荐安装方案"""
    if has_gpu() and get_gpu_memory() >= 8:
        return "full_suite"  # 完整套件
    elif get_memory() >= 8:
        return "inference_only"  # 仅推理
    else:
        return "minimal"  # 最小化安装
```

---

## 3. 功能分级体系

### 3.1 轻量级功能 (Light)

**适用场景**：工厂现场、边缘设备、低配工控机

**典型功能**：
- 模型推理（分类/检测/分割/姿态估计）
- 图像预处理（缩放、归一化、增强）
- 结果后处理（NMS、过滤、格式化）

**硬件要求**：
- CPU: 2 核心
- 内存: 2GB
- GPU: 可选（有则更快）
- 存储: 100MB（模型文件）

**依赖示例**：
```txt
ultralytics>=8.0.0
opencv-python>=4.5.0
numpy>=1.19.0,<2.0.0
```

**节点设计要点**：
- 使用预训练模型，无需训练环境
- 支持 CPU 推理，GPU 为可选项
- 模型自动缓存，避免重复加载
- 异步执行，不阻塞 UI

### 3.2 中量级功能 (Medium)

**适用场景**：办公室工作站、中等配置电脑

**典型功能**：
- 半自动标注辅助
- 数据增强与清洗
- 可视化分析与统计

**硬件要求**：
- CPU: 4 核心
- 内存: 8GB
- GPU: 可选
- 存储: 1GB（数据集缓存）

**依赖示例**：
```txt
ultralytics>=8.0.0
labelme>=5.0.0
matplotlib>=3.5.0
```

**节点设计要点**：
- 提供交互式界面
- 支持批量处理
- 结果可视化展示

### 3.3 重量级功能 (Heavy)

**适用场景**：高性能工作站、云端服务器

**典型功能**：
- 模型训练（从头训练/微调）
- 模型量化（FP32 → INT8）
- 格式导出（ONNX/TensorRT/OpenVINO）
- 超参数搜索

**硬件要求**：
- CPU: 8+ 核心
- 内存: 16GB+
- GPU: 必需（CUDA 11.8+，8GB+ 显存）
- 存储: 10GB+（数据集 + 模型检查点）

**依赖示例**：
```txt
ultralytics>=8.0.0
torch>=2.0.0
torchvision>=0.15.0
# GPU 版本（可选）
# torch --index-url https://download.pytorch.org/whl/cu118
```

**节点设计要点**：
- 启动前进行硬件检查
- 提供详细的进度反馈
- 支持断点续训
- 训练完成后自动清理临时文件

---

## 4. 插件包结构设计

### 4.1 标准目录结构

```
user_plugins/{plugin_name}/
├── plugin.json                    # 元数据（含资源等级声明）
├── nodes/
│   ├── inference/                 # 【轻量级】推理节点
│   │   ├── __init__.py
│   │   ├── yolo_detect.py
│   │   ├── yolo_classify.py
│   │   └── ...
│   │
│   ├── annotation/                # 【中量级】标注工具
│   │   ├── __init__.py
│   │   └── yolo_annotator.py
│   │
│   └── training/                  # 【重量级】训练与优化
│       ├── __init__.py
│       ├── yolo_trainer.py
│       ├── yolo_quantizer.py
│       └── yolo_exporter.py
│
├── requirements_inference.txt     # 推理依赖
├── requirements_training.txt      # 训练依赖
├── models/                        # 预训练模型（可选）
│   ├── yolov8n.pt
│   └── yolov8s.pt
├── README.md                      # 使用说明（含硬件要求）
└── examples/                      # 示例工程（可选）
    └── demo_workflow.proj
```

### 4.2 plugin.json 规范

```json
{
  "name": "yolo_vision",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "YOLO 视觉算法套件（支持检测/分类/分割/姿态）",
  "category_group": "识别分类",
  
  "nodes": [
    {
      "class": "YOLODetectNode",
      "display_name": "YOLO 目标检测",
      "category": "AI推理",
      "resource_level": "light",
      "dependencies": ["ultralytics>=8.0.0"],
      "hardware_requirements": {
        "cpu": "2 cores",
        "memory": "2GB",
        "gpu": "optional"
      }
    },
    {
      "class": "YOLOTrainerNode",
      "display_name": "YOLO 模型训练",
      "category": "模型训练",
      "resource_level": "heavy",
      "dependencies": ["ultralytics>=8.0.0", "torch>=2.0.0"],
      "optional_dependencies": {
        "gpu": ["torch-cuda==11.8"]
      },
      "hardware_requirements": {
        "cpu": "8+ cores",
        "memory": "16GB+",
        "gpu": "required (CUDA 11.8+, 8GB+ VRAM)"
      }
    }
  ],
  
  "min_app_version": "4.0.0",
  
  "installation_guide": {
    "inference_only": "pip install -r requirements_inference.txt",
    "full_suite": "pip install -r requirements_training.txt"
  }
}
```

**关键字段说明**：
- `resource_level`: 资源等级（light/medium/heavy）
- `hardware_requirements`: 硬件要求（用于安装向导）
- `optional_dependencies`: 可选依赖（如 GPU 加速）
- `installation_guide`: 安装指南

---

## 5. 依赖管理策略

### 5.1 分离依赖文件

**requirements_inference.txt**（推理依赖）
```txt
# 核心依赖
ultralytics>=8.0.0
opencv-python>=4.5.0
numpy>=1.19.0,<2.0.0

# 可选优化
# onnxruntime-gpu>=1.15.0  # GPU 加速推理
```

**requirements_training.txt**（训练依赖）
```txt
# 包含推理依赖
-r requirements_inference.txt

# 训练框架
torch>=2.0.0
torchvision>=0.15.0
torchaudio>=2.0.0

# 数据增强
albumentations>=1.3.0

# GPU 支持（二选一）
# CPU 版本
# torch --index-url https://download.pytorch.org/whl/cpu

# GPU 版本（推荐）
# torch --index-url https://download.pytorch.org/whl/cu118
```

### 5.2 智能安装脚本

```python
#!/usr/bin/env python3
"""
AI 插件智能安装脚本

用法：
    python install_plugin.py                    # 仅安装推理依赖
    python install_plugin.py --full             # 安装完整套件
    python install_plugin.py --check            # 检查硬件兼容性
"""

import sys
import subprocess
import platform

def check_hardware():
    """检查硬件配置"""
    import psutil
    
    cpu_cores = psutil.cpu_count(logical=False)
    memory_gb = psutil.virtual_memory().total / (1024**3)
    
    print(f"🖥️  硬件检测结果:")
    print(f"   CPU 核心数: {cpu_cores}")
    print(f"   内存大小: {memory_gb:.1f} GB")
    
    # 检查 GPU
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / (1024**3)
            print(f"   GPU: {gpu_name} ({gpu_memory:.1f} GB)")
            return "high_end" if gpu_memory >= 8 else "mid_range"
        else:
            print(f"   GPU: 未检测到 CUDA 设备")
            return "cpu_only"
    except ImportError:
        print(f"   GPU: 未安装 PyTorch")
        return "cpu_only"

def install_dependencies(mode="inference"):
    """安装依赖"""
    if mode == "inference":
        req_file = "requirements_inference.txt"
        print("📦 安装推理依赖（约 500MB）...")
    elif mode == "full":
        req_file = "requirements_training.txt"
        print("📦 安装完整套件（约 2GB + CUDA）...")
    else:
        print(f"❌ 未知模式: {mode}")
        return False
    
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', 
            '-r', req_file,
            '--no-cache-dir'  # 避免缓存占用空间
        ])
        print("✅ 安装完成！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装失败: {e}")
        return False

def recommend_mode():
    """根据硬件推荐安装模式"""
    hardware_level = check_hardware()
    
    if hardware_level == "high_end":
        print("\n💡 推荐：完整套件（支持训练和量化）")
        return "full"
    elif hardware_level == "mid_range":
        print("\n💡 推荐：仅推理（训练建议使用云端或高性能工作站）")
        return "inference"
    else:
        print("\n💡 推荐：仅推理（CPU 模式）")
        return "inference"

if __name__ == '__main__':
    if '--check' in sys.argv:
        check_hardware()
    elif '--full' in sys.argv:
        install_dependencies("full")
    else:
        mode = recommend_mode()
        install_dependencies(mode)
```

### 5.3 运行时依赖检查

```python
class AIBaseNode(BaseNode):
    """AI 节点基类，提供依赖检查"""
    
    def check_dependencies(self, required_packages):
        """检查依赖是否已安装"""
        missing = []
        for package in required_packages:
            try:
                __import__(package.split('>=')[0].split('==')[0])
            except ImportError:
                missing.append(package)
        
        if missing:
            print(f"⚠️ 缺少依赖: {', '.join(missing)}")
            print(f"💡 安装命令: pip install {' '.join(missing)}")
            return False
        return True
    
    def check_hardware(self, min_requirements):
        """检查硬件是否满足要求"""
        import psutil
        
        # 检查内存
        memory_gb = psutil.virtual_memory().available / (1024**3)
        if memory_gb < min_requirements.get('memory_gb', 0):
            print(f"⚠️ 可用内存不足 ({memory_gb:.1f}GB < {min_requirements['memory_gb']}GB)")
            return False
        
        # 检查 GPU
        if min_requirements.get('gpu_required', False):
            try:
                import torch
                if not torch.cuda.is_available():
                    print("⚠️ 未检测到 CUDA 设备")
                    return False
            except ImportError:
                print("⚠️ 未安装 PyTorch")
                return False
        
        return True
```

---

## 6. 部署场景适配

### 6.1 场景一：工厂现场（低配工控机）

**硬件配置**：
- CPU: Intel i5 (4 核心)
- 内存: 8GB
- GPU: 无或集成显卡
- 存储: 128GB SSD

**安装内容**：
- ✅ YOLO 推理节点（yolov8n.pt 模型）
- ❌ 训练节点
- ❌ 量化节点

**工作流示例**：
```
图像采集 → YOLO检测 → 结果输出到PLC
```

**性能预期**：
- 推理速度：yolov8n ~50ms/帧（CPU）
- 内存占用：< 2GB
- 磁盘占用：< 500MB

### 6.2 场景二：办公室工作站（中高配）

**硬件配置**：
- CPU: Intel i7 (8 核心)
- 内存: 32GB
- GPU: RTX 3060 (12GB)
- 存储: 1TB NVMe

**安装内容**：
- ✅ YOLO 推理节点
- ✅ YOLO 标注节点
- ✅ YOLO 训练节点
- ✅ YOLO 量化节点

**工作流示例**：
```
数据采集 → 标注 → 训练 → 量化 → 导出到现场
```

**性能预期**：
- 训练速度：yolov8n ~10分钟/100 epochs（GPU）
- 量化加速：INT8 比 FP32 快 2-4x

### 6.3 场景三：云端训练（高性能）

**硬件配置**：
- CPU: AMD EPYC (32 核心)
- 内存: 128GB
- GPU: A100 (80GB) x 4
- 存储: 10TB NVMe

**用途**：
- 大规模数据集训练（10万+ 图片）
- 超参数搜索（网格搜索/贝叶斯优化）
- 模型 Ensemble（多模型融合）

---

## 7. 实施指南

### 7.1 开发流程

**Step 1: 需求分析**
- 确定功能属于哪个等级（light/medium/heavy）
- 评估硬件要求
- 列出依赖清单

**Step 2: 插件结构设计**
- 创建目录结构
- 编写 plugin.json（含资源等级声明）
- 准备分离的依赖文件

**Step 3: 节点实现**
- 继承 BaseNode
- 实现 process() 方法
- 添加依赖检查和硬件检查
- 编写完整的 docstring

**Step 4: 测试验证**
- 在低配机器上测试轻量级节点
- 在高配机器上测试重量级节点
- 验证依赖分离是否正确

**Step 5: 文档编写**
- README.md 包含硬件要求
- 提供安装指南
- 提供示例工作流

### 7.2 代码模板

**轻量级节点模板**
```python
"""
{节点名称}（轻量级）

硬件要求：
- CPU: 2 核心
- 内存: 2GB
- GPU: 可选

使用方法：
1. 拖拽节点到画布
2. 连接输入
3. 设置参数
4. 运行查看结果
"""

from NodeGraphQt import BaseNode


class {ClassName}Node(BaseNode):
    """{节点名称}节点"""
    
    __identifier__ = '{plugin_name}'
    NODE_NAME = '{显示名称}'
    
    def __init__(self):
        super().__init__()
        
        # 输入端口
        self.add_input('输入图像')
        
        # 输出端口
        self.add_output('输出结果')
        
        # 参数配置
        # TODO: 添加参数
    
    def process(self, inputs):
        """执行处理"""
        try:
            # 检查依赖
            if not self.check_dependencies(['package_name']):
                return None
            
            # 获取输入
            image = inputs.get('输入图像')
            
            # TODO: 实现处理逻辑
            
            return {'输出结果': result}
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            return None
```

**重量级节点模板**
```python
"""
{节点名称}（重量级）

硬件要求：
- CPU: 8+ 核心
- 内存: 16GB+
- GPU: 必需（CUDA 11.8+，8GB+ 显存）

警告：
- 此节点仅在配备高性能 GPU 的工作站上使用
- 工厂现场的低配工控机不应安装此节点
"""

from NodeGraphQt import BaseNode


class {ClassName}Node(BaseNode):
    """{节点名称}节点"""
    
    __identifier__ = '{plugin_name}'
    NODE_NAME = '{显示名称}'
    
    def __init__(self):
        super().__init__()
        
        # 输入端口
        self.add_input('输入数据')
        
        # 输出端口
        self.add_output('输出结果')
        
        # 硬件检查提示
        self.add_text_input('_hardware_note', '硬件要求', 
                           '⚠️ 需要 GPU (CUDA 11.8+, 8GB+ VRAM)')
    
    def check_hardware(self):
        """检查硬件是否满足要求"""
        # TODO: 实现硬件检查
        pass
    
    def process(self, inputs):
        """执行处理"""
        try:
            # 硬件检查
            if not self.check_hardware():
                print("💡 建议：在配备 GPU 的工作站上运行")
                return None
            
            # 检查依赖
            if not self.check_dependencies(['torch', 'package_name']):
                return None
            
            # TODO: 实现处理逻辑
            
            return {'输出结果': result}
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
            return None
```

### 7.3 测试清单

**轻量级节点测试**：
- [ ] 在仅有 CPU 的机器上能正常运行
- [ ] 内存占用 < 2GB
- [ ] 推理速度符合预期
- [ ] 依赖文件大小 < 500MB

**重量级节点测试**：
- [ ] 硬件检查能正确识别 GPU
- [ ] 缺少 GPU 时给出友好提示
- [ ] 训练过程有进度反馈
- [ ] 支持断点续训

---

## 8. 示例：YOLO 视觉插件

### 8.1 插件概览

**插件名称**: yolo_vision  
**版本**: 1.0.0  
**分类**: 识别分类  

**功能模块**：
- **推理模块**（轻量级）：目标检测、图像分类、实例分割、姿态估计
- **标注模块**（中量级）：半自动标注辅助
- **训练模块**（重量级）：模型训练、超参数调优
- **优化模块**（重量级）：模型量化、格式导出

### 8.2 节点列表

| 节点名称 | 资源等级 | 硬件要求 | 依赖大小 |
|---------|---------|---------|---------|
| YOLO 目标检测 | Light | CPU 2核, 2GB | 500MB |
| YOLO 图像分类 | Light | CPU 2核, 2GB | 500MB |
| YOLO 标注辅助 | Medium | CPU 4核, 8GB | 600MB |
| YOLO 模型训练 | Heavy | GPU 8GB+, 16GB | 2GB+ |
| YOLO 模型量化 | Heavy | GPU 8GB+, 16GB | 2GB+ |

### 8.3 部署建议

**工厂现场**：
```bash
# 仅安装推理依赖
python install_plugin.py

# 或使用 pip
pip install -r requirements_inference.txt
```

**办公室工作站**：
```bash
# 安装完整套件
python install_plugin.py --full

# 或使用 pip
pip install -r requirements_training.txt
```

---

## 📝 变更记录

| 版本 | 日期 | 变更内容 | 作者 |
|------|------|---------|------|
| v1.0 | 2026-04-26 | 初始版本，定义 AI 模块资源隔离设计规范 | Lingma |

---

## 🔗 相关文档

- [节点系统与UI开发规范](../src/python/user_plugins/NODE_DEVELOPMENT_GUIDE.md)
- [插件开发指南](../src/python/user_plugins/NODE_API_REFERENCE.md)
- [架构演进方案](./ARCHITECTURE_EVOLUTION.md)
- [项目 README](../README.md)

---

**最后更新**: 2026-04-26  
**维护者**: 项目开发团队