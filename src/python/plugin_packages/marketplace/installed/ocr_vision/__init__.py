"""
OCR 视觉模块 - 文字检测与识别

基于 PaddleOCR 实现高精度的中文/英文文字识别，支持：
- 通用文字检测与识别
- 表格结构识别
- 版面分析
- 多语言支持（80+ 语言）

硬件要求：
- 轻量级推理：CPU 2核+ / 4GB 内存
- 重量级训练：GPU 必需（CUDA 11.0+，6GB+ 显存）
"""

from .nodes.inference import *
from .nodes.training import *
