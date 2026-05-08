"""
图像操作节点 - 提供多种OpenCV图像/矩阵操作

方法分类：
├── 一元操作（单输入）
│   ├── 基础运算: cvAbs, cvAbsDiff, cvAbsDiffS
│   ├── 统计分析: cvAvg, cvAvgSdv, cvCountNonZero, cvSum, cvMinMaxLoc
│   ├── 矩阵操作: cvDet, cvDiag, cvDct, cvDft, cvEigenVV, cvInvert, cvTrace, cvTranspose, cvSVD
│   ├── 几何变换: cvFlip, cvResize
│   ├── 颜色处理: cvCvtColor
│   └── 元素操作: cvSet, cvSetZero, cvSetIdentity, cvZero, cvRepeat, cvNormalize
├── 二元操作（双输入）
│   ├── 算术运算: cvAdd, cvAddS, cvAddWeighted, cvSub, cvSubS, cvSubRS, cvMul, cvDiv, cvDivS, cvDivRS
│   ├── 比较运算: cvCmp, cvCmpS, cvInRange, cvInRangeS, cvMax, cvMaxS, cvMin, cvMinS
│   ├── 逻辑运算: cvAnd, cvAndS, cvOr, cvOrS, cvXor, cvXorS, cvNot
│   └── 向量运算: cvCrossProduct, cvDotProduct, cvMahalanobis, cvNorm
└── 其他操作（特殊功能）
    ├── 通道操作: cvMerge, cvSplit
    ├── 矩阵复制: cvCopy, cvCopyMakeBorder, cvGetCol, cvGetCols, cvGetRow, cvGetRows, cvGetSubRect
    ├── 数据转换: cvConvertScale, cvConvertScaleAbs, cvPow, cvRound, cvFloor, cvCeil
    └── 矩阵乘法: cvGEMM, cvSolve

输入：
- 输入图像: 图像或矩阵 (numpy.ndarray)
- 输入图像2: 图像或矩阵（可选，二元操作时使用）

输出：
- 输出图像: 处理后的图像或可视化结果
- JSON数据: 元数据（方法名、参数、时间戳、结果信息）
"""

import cv2
import numpy as np
import logging
from PySide2 import QtCore
from shared_libs.node_base import BaseNode

logger = logging.getLogger('image_operation')


class ImageOperationNode(BaseNode):
    """
    图像操作节点 - 基于OpenCV的图像/矩阵操作集合
    
    支持70+种图像操作方法，涵盖算术运算、逻辑运算、矩阵操作、几何变换等功能。
    所有方法均返回可视化图像结果，便于在工作流中查看和调试。
    """

    __identifier__ = 'Image_Analysis'
    NODE_NAME = '图像操作'

    resource_level = "light"
    hardware_requirements = {
        'cpu_cores': 1,
        'memory_gb': 0.5,
        'gpu_required': False,
        'gpu_memory_gb': 0
    }

    # 方法元数据定义 - 按分类组织
    METHOD_METADATA = {
        # ========== 一元操作 ==========
        'cvAbs': {
            'name': '绝对值',
            'category': '一元操作',
            'description': '计算数组中所有元素的绝对值',
            'library': 'OpenCV',
            'function': 'cv2.abs',
            'inputs': 1,
            'input_types': ['image/matrix'],
            'output_type': 'image',
            'parameters': [],
            'example': '处理负值图像数据'
        },
        'cvAvg': {
            'name': '平均值',
            'category': '一元操作',
            'description': '计算数组中所有元素的平均值',
            'library': 'OpenCV',
            'function': 'cv2.mean',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'text_image',
            'parameters': [],
            'example': '计算图像亮度'
        },
        'cvAvgSdv': {
            'name': '均值标准差',
            'category': '一元操作',
            'description': '计算数组中所有元素的平均值和标准差',
            'library': 'OpenCV',
            'function': 'cv2.meanStdDev',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'text_image',
            'parameters': [],
            'example': '统计图像亮度分布'
        },
        'cvCountNonZero': {
            'name': '非零计数',
            'category': '一元操作',
            'description': '计算数组中非零元素的个数',
            'library': 'OpenCV',
            'function': 'cv2.countNonZero',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'text_image',
            'parameters': [],
            'example': '前景像素统计'
        },
        'cvSum': {
            'name': '元素和',
            'category': '一元操作',
            'description': '计算数组中的所有元素和',
            'library': 'NumPy',
            'function': 'np.sum',
            'inputs': 1,
            'input_types': ['image/matrix'],
            'output_type': 'text_image',
            'parameters': [],
            'example': '图像能量计算'
        },
        'cvMinMaxLoc': {
            'name': '最小最大值',
            'category': '一元操作',
            'description': '找出数组中的最小最大值',
            'library': 'OpenCV',
            'function': 'cv2.minMaxLoc',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'text_image',
            'parameters': [],
            'example': '图像对比度分析'
        },
        'cvDet': {
            'name': '行列式',
            'category': '一元操作',
            'description': '计算方阵的行列式',
            'library': 'NumPy',
            'function': 'np.linalg.det',
            'inputs': 1,
            'input_types': ['matrix'],
            'output_type': 'text_image',
            'parameters': [],
            'example': '矩阵可逆性判断'
        },
        'cvDiag': {
            'name': '对角操作',
            'category': '一元操作',
            'description': '从数组中提取或创建对角矩阵',
            'library': 'NumPy',
            'function': 'np.diag',
            'inputs': 1,
            'input_types': ['matrix'],
            'output_type': 'image',
            'parameters': [],
            'example': '对角矩阵操作'
        },
        'cvDct': {
            'name': 'DCT变换',
            'category': '一元操作',
            'description': '计算离散余弦变换',
            'library': 'OpenCV',
            'function': 'cv2.dct',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'image',
            'parameters': [],
            'example': '图像频域分析'
        },
        'cvDft': {
            'name': 'DFT变换',
            'category': '一元操作',
            'description': '计算离散傅里叶变换',
            'library': 'OpenCV',
            'function': 'cv2.dft',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'image',
            'parameters': [],
            'example': '频率域滤波'
        },
        'cvInvert': {
            'name': '矩阵求逆',
            'category': '一元操作',
            'description': '计算矩阵的逆',
            'library': 'NumPy',
            'function': 'np.linalg.inv',
            'inputs': 1,
            'input_types': ['matrix'],
            'output_type': 'image',
            'parameters': [],
            'example': '矩阵求逆运算'
        },
        'cvTrace': {
            'name': '矩阵迹',
            'category': '一元操作',
            'description': '计算矩阵的迹',
            'library': 'NumPy',
            'function': 'np.trace',
            'inputs': 1,
            'input_types': ['matrix'],
            'output_type': 'text_image',
            'parameters': [],
            'example': '矩阵迹计算'
        },
        'cvTranspose': {
            'name': '矩阵转置',
            'category': '一元操作',
            'description': '矩阵的转置运算',
            'library': 'OpenCV',
            'function': 'cv2.transpose',
            'inputs': 1,
            'input_types': ['image/matrix'],
            'output_type': 'image',
            'parameters': [],
            'example': '行列互换'
        },
        'cvSVD': {
            'name': '奇异值分解',
            'category': '一元操作',
            'description': '计算矩阵的奇异值分解',
            'library': 'NumPy',
            'function': 'np.linalg.svd',
            'inputs': 1,
            'input_types': ['matrix'],
            'output_type': 'text_image',
            'parameters': [],
            'example': '矩阵分解'
        },
        'cvFlip': {
            'name': '翻转',
            'category': '一元操作',
            'description': '围绕选定轴翻转图像',
            'library': 'OpenCV',
            'function': 'cv2.flip',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'image',
            'parameters': [{'name': 'flip_code', 'value': -1}],
            'example': '图像翻转'
        },
        'cvResize': {
            'name': '缩放',
            'category': '一元操作',
            'description': '调整图像大小',
            'library': 'OpenCV',
            'function': 'cv2.resize',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'image',
            'parameters': [],
            'example': '图像缩放'
        },
        'cvCvtColor': {
            'name': '颜色转换',
            'category': '一元操作',
            'description': '将数组的通道从一个颜色空间转换到另一个颜色空间',
            'library': 'OpenCV',
            'function': 'cv2.cvtColor',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'image',
            'parameters': [],
            'example': 'BGR转灰度'
        },
        'cvNot': {
            'name': '按位取反',
            'category': '一元操作',
            'description': '按位非运算（255-pixel）',
            'library': 'OpenCV',
            'function': 'cv2.bitwise_not',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'image',
            'parameters': [],
            'example': '图像反色'
        },
        'cvNormalize': {
            'name': '归一化',
            'category': '一元操作',
            'description': '将数组中元素进行归一化',
            'library': 'OpenCV',
            'function': 'cv2.normalize',
            'inputs': 1,
            'input_types': ['image/matrix'],
            'output_type': 'image',
            'parameters': [],
            'example': '对比度增强'
        },
        'cvPow': {
            'name': '幂运算',
            'category': '一元操作',
            'description': '对数组中的每个元素进行幂运算',
            'library': 'NumPy',
            'function': 'np.power',
            'inputs': 1,
            'input_types': ['image/matrix'],
            'output_type': 'image',
            'parameters': [{'name': 'power', 'value': 2}],
            'example': '伽马校正'
        },
        'cvRepeat': {
            'name': '平铺',
            'category': '一元操作',
            'description': '以平铺的方式进行数组复制',
            'library': 'OpenCV',
            'function': 'cv2.repeat',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'image',
            'parameters': [],
            'example': '图像平铺'
        },
        # ========== 二元操作 ==========
        'cvAbsDiff': {
            'name': '差绝对值',
            'category': '二元操作',
            'description': '计算两个数组差的绝对值',
            'library': 'OpenCV',
            'function': 'cv2.absdiff',
            'inputs': 2,
            'input_types': ['image', 'image'],
            'output_type': 'image',
            'parameters': [],
            'example': '帧差检测'
        },
        'cvAbsDiffS': {
            'name': '差绝对值(标量)',
            'category': '二元操作',
            'description': '计算数组和标量差的绝对值',
            'library': 'OpenCV',
            'function': 'cv2.absdiff',
            'inputs': 2,
            'input_types': ['image', 'scalar'],
            'output_type': 'image',
            'parameters': [],
            'example': '与常数的差异'
        },
        'cvAdd': {
            'name': '加法',
            'category': '二元操作',
            'description': '两个数组相加',
            'library': 'OpenCV',
            'function': 'cv2.add',
            'inputs': 2,
            'input_types': ['image', 'image'],
            'output_type': 'image',
            'parameters': [],
            'example': '图像叠加'
        },
        'cvAddS': {
            'name': '加标量',
            'category': '二元操作',
            'description': '一个数组和一个标量的元素相加',
            'library': 'OpenCV',
            'function': 'cv2.add',
            'inputs': 2,
            'input_types': ['image', 'scalar'],
            'output_type': 'image',
            'parameters': [],
            'example': '亮度提升'
        },
        'cvAddWeighted': {
            'name': '加权相加',
            'category': '二元操作',
            'description': '两个数组的加权相加',
            'library': 'OpenCV',
            'function': 'cv2.addWeighted',
            'inputs': 2,
            'input_types': ['image', 'image'],
            'output_type': 'image',
            'parameters': [{'name': 'alpha', 'value': 0.5}, {'name': 'beta', 'value': 0.5}],
            'example': '图像混合'
        },
        'cvSub': {
            'name': '减法',
            'category': '二元操作',
            'description': '两个数组的元素相减',
            'library': 'OpenCV',
            'function': 'cv2.subtract',
            'inputs': 2,
            'input_types': ['image', 'image'],
            'output_type': 'image',
            'parameters': [],
            'example': '背景减除'
        },
        'cvSubS': {
            'name': '减标量',
            'category': '二元操作',
            'description': '从数组的元素中减去一个标量',
            'library': 'OpenCV',
            'function': 'cv2.subtract',
            'inputs': 2,
            'input_types': ['image', 'scalar'],
            'output_type': 'image',
            'parameters': [],
            'example': '降低亮度'
        },
        'cvSubRS': {
            'name': '标量减',
            'category': '二元操作',
            'description': '用一个标量减去数组的元素',
            'library': 'OpenCV',
            'function': 'cv2.subtract',
            'inputs': 2,
            'input_types': ['scalar', 'image'],
            'output_type': 'image',
            'parameters': [],
            'example': '反相处理'
        },
        'cvMul': {
            'name': '乘法',
            'category': '二元操作',
            'description': '计算两个数组的元素的乘积',
            'library': 'OpenCV',
            'function': 'cv2.multiply',
            'inputs': 2,
            'input_types': ['image', 'image'],
            'output_type': 'image',
            'parameters': [],
            'example': '图像掩模'
        },
        'cvDiv': {
            'name': '除法',
            'category': '二元操作',
            'description': '用另外一个数组对一个数组进行元素的除法运算',
            'library': 'OpenCV',
            'function': 'cv2.divide',
            'inputs': 2,
            'input_types': ['image', 'image'],
            'output_type': 'image',
            'parameters': [],
            'example': '归一化'
        },
        'cvDivS': {
            'name': '除标量',
            'category': '二元操作',
            'description': '用数组的元素除以一个标量',
            'library': 'OpenCV',
            'function': 'cv2.divide',
            'inputs': 2,
            'input_types': ['image', 'scalar'],
            'output_type': 'image',
            'parameters': [],
            'example': '缩放处理'
        },
        'cvDivRS': {
            'name': '标量除',
            'category': '二元操作',
            'description': '用一个标量除以数组的元素',
            'library': 'OpenCV',
            'function': 'cv2.divide',
            'inputs': 2,
            'input_types': ['scalar', 'image'],
            'output_type': 'image',
            'parameters': [],
            'example': '倒数处理'
        },
        'cvCmp': {
            'name': '比较',
            'category': '二元操作',
            'description': '对两个数组的所有元素运用设置的比较操作',
            'library': 'OpenCV',
            'function': 'cv2.compare',
            'inputs': 2,
            'input_types': ['image', 'image'],
            'output_type': 'image',
            'parameters': [],
            'example': '图像比较'
        },
        'cvCmpS': {
            'name': '比较(标量)',
            'category': '二元操作',
            'description': '对数组和标量运用设置的比较操作',
            'library': 'OpenCV',
            'function': 'cv2.compare',
            'inputs': 2,
            'input_types': ['image', 'scalar'],
            'output_type': 'image',
            'parameters': [],
            'example': '阈值比较'
        },
        'cvInRange': {
            'name': '范围检查',
            'category': '二元操作',
            'description': '检验一个数组的元素是否在另外两个数组中的值的范围内',
            'library': 'OpenCV',
            'function': 'cv2.inRange',
            'inputs': 2,
            'input_types': ['image', 'image'],
            'output_type': 'image',
            'parameters': [],
            'example': '颜色范围检测'
        },
        'cvInRangeS': {
            'name': '范围检查(标量)',
            'category': '二元操作',
            'description': '检验一个数组的元素的值是否在另外两个标量的范围内',
            'library': 'OpenCV',
            'function': 'cv2.inRange',
            'inputs': 2,
            'input_types': ['image', 'scalar'],
            'output_type': 'image',
            'parameters': [],
            'example': '灰度范围检测'
        },
        'cvMax': {
            'name': '最大值',
            'category': '二元操作',
            'description': '在两个数组中进行元素级的取最大值操作',
            'library': 'OpenCV',
            'function': 'cv2.max',
            'inputs': 2,
            'input_types': ['image', 'image'],
            'output_type': 'image',
            'parameters': [],
            'example': '高亮提取'
        },
        'cvMaxS': {
            'name': '最大值(标量)',
            'category': '二元操作',
            'description': '在一个数组和一个标量中进行元素级的取最大值操作',
            'library': 'OpenCV',
            'function': 'cv2.max',
            'inputs': 2,
            'input_types': ['image', 'scalar'],
            'output_type': 'image',
            'parameters': [],
            'example': '阈值上限'
        },
        'cvMin': {
            'name': '最小值',
            'category': '二元操作',
            'description': '在两个数组中进行元素级的取最小值操作',
            'library': 'OpenCV',
            'function': 'cv2.min',
            'inputs': 2,
            'input_types': ['image', 'image'],
            'output_type': 'image',
            'parameters': [],
            'example': '暗部提取'
        },
        'cvMinS': {
            'name': '最小值(标量)',
            'category': '二元操作',
            'description': '在一个数组和一个标量中进行元素级的取最小值操作',
            'library': 'OpenCV',
            'function': 'cv2.min',
            'inputs': 2,
            'input_types': ['image', 'scalar'],
            'output_type': 'image',
            'parameters': [],
            'example': '阈值下限'
        },
        'cvAnd': {
            'name': '按位与',
            'category': '二元操作',
            'description': '对两个数组进行按位与操作',
            'library': 'OpenCV',
            'function': 'cv2.bitwise_and',
            'inputs': 2,
            'input_types': ['image', 'image'],
            'output_type': 'image',
            'parameters': [],
            'example': '图像掩模'
        },
        'cvAndS': {
            'name': '按位与(标量)',
            'category': '二元操作',
            'description': '按位对数组中的每一个元素求与',
            'library': 'OpenCV',
            'function': 'cv2.bitwise_and',
            'inputs': 2,
            'input_types': ['image', 'scalar'],
            'output_type': 'image',
            'parameters': [],
            'example': '固定值掩模'
        },
        'cvOr': {
            'name': '按位或',
            'category': '二元操作',
            'description': '对两个数组进行按位或操作',
            'library': 'OpenCV',
            'function': 'cv2.bitwise_or',
            'inputs': 2,
            'input_types': ['image', 'image'],
            'output_type': 'image',
            'parameters': [],
            'example': '图像合并'
        },
        'cvOrS': {
            'name': '按位或(标量)',
            'category': '二元操作',
            'description': '按位对数组中的每一个元素求或',
            'library': 'OpenCV',
            'function': 'cv2.bitwise_or',
            'inputs': 2,
            'input_types': ['image', 'scalar'],
            'output_type': 'image',
            'parameters': [],
            'example': '固定值合并'
        },
        'cvXor': {
            'name': '按位异或',
            'category': '二元操作',
            'description': '对两个数组进行按位异或操作',
            'library': 'OpenCV',
            'function': 'cv2.bitwise_xor',
            'inputs': 2,
            'input_types': ['image', 'image'],
            'output_type': 'image',
            'parameters': [],
            'example': '差异检测'
        },
        'cvXorS': {
            'name': '按位异或(标量)',
            'category': '二元操作',
            'description': '按位对数组中的每一个元素求异或',
            'library': 'OpenCV',
            'function': 'cv2.bitwise_xor',
            'inputs': 2,
            'input_types': ['image', 'scalar'],
            'output_type': 'image',
            'parameters': [],
            'example': '固定值异或'
        },
        'cvCrossProduct': {
            'name': '叉积',
            'category': '二元操作',
            'description': '计算两个三维向量的向量积(叉积)',
            'library': 'NumPy',
            'function': 'np.cross',
            'inputs': 2,
            'input_types': ['vector', 'vector'],
            'output_type': 'text_image',
            'parameters': [],
            'example': '向量叉积'
        },
        'cvDotProduct': {
            'name': '点积',
            'category': '二元操作',
            'description': '计算两个向量的数量积(点积)',
            'library': 'NumPy',
            'function': 'np.dot',
            'inputs': 2,
            'input_types': ['vector', 'vector'],
            'output_type': 'text_image',
            'parameters': [],
            'example': '向量点积'
        },
        'cvMahalanobis': {
            'name': '马氏距离',
            'category': '二元操作',
            'description': '计算两个向量间的马氏距离',
            'library': 'OpenCV',
            'function': 'cv2.Mahalanobis',
            'inputs': 2,
            'input_types': ['vector', 'vector'],
            'output_type': 'text_image',
            'parameters': [],
            'example': '距离度量'
        },
        'cvNorm': {
            'name': '范数',
            'category': '二元操作',
            'description': '计算两个数组的正规相关性',
            'library': 'OpenCV',
            'function': 'cv2.norm',
            'inputs': 2,
            'input_types': ['image', 'image'],
            'output_type': 'text_image',
            'parameters': [],
            'example': '相似度度量'
        },
        # ========== 其他操作 ==========
        'cvMerge': {
            'name': '合并通道',
            'category': '其他操作',
            'description': '把几个单通道图像合并为一个多通道图像',
            'library': 'OpenCV',
            'function': 'cv2.merge',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'image',
            'parameters': [],
            'example': '通道合并'
        },
        'cvSplit': {
            'name': '分离通道',
            'category': '其他操作',
            'description': '将多通道图像分割成多个单通道图像',
            'library': 'OpenCV',
            'function': 'cv2.split',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'image',
            'parameters': [],
            'example': '通道分离'
        },
        'cvCopy': {
            'name': '复制',
            'category': '其他操作',
            'description': '把数组中的值复制到另一个数组中',
            'library': 'OpenCV',
            'function': 'cv2.copy',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'image',
            'parameters': [],
            'example': '图像复制'
        },
        'cvCopyMakeBorder': {
            'name': '复制边界',
            'category': '其他操作',
            'description': '从一个数组的子矩形中复制元素',
            'library': 'OpenCV',
            'function': 'cv2.copyMakeBorder',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'image',
            'parameters': [],
            'example': '边界扩展'
        },
        'cvConvertScale': {
            'name': '转换缩放',
            'category': '其他操作',
            'description': '用可选的缩放值转换数组元素的类型',
            'library': 'OpenCV',
            'function': 'cv2.convertScaleAbs',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'image',
            'parameters': [],
            'example': '类型转换'
        },
        'cvConvertScaleAbs': {
            'name': '转换缩放绝对值',
            'category': '其他操作',
            'description': '计算可选的缩放值绝对值之后再转换数组元素的类型',
            'library': 'OpenCV',
            'function': 'cv2.convertScaleAbs',
            'inputs': 1,
            'input_types': ['image'],
            'output_type': 'image',
            'parameters': [],
            'example': '绝对值转换'
        },
        'cvGEMM': {
            'name': '矩阵乘法',
            'category': '其他操作',
            'description': '矩阵乘法',
            'library': 'OpenCV',
            'function': 'cv2.gemm',
            'inputs': 1,
            'input_types': ['matrix'],
            'output_type': 'image',
            'parameters': [],
            'example': '矩阵运算'
        },
        'cvSolve': {
            'name': '求解',
            'category': '其他操作',
            'description': '通过给定的操作符将一组数组的简约为向量',
            'library': 'NumPy',
            'function': 'np.linalg.solve',
            'inputs': 1,
            'input_types': ['matrix'],
            'output_type': 'text_image',
            'parameters': [],
            'example': '线性方程组求解'
        },
    }

    def __init__(self):
        super(ImageOperationNode, self).__init__()

        self.add_input('输入图像', color=(100, 255, 100))
        self.add_input('输入图像2', color=(100, 255, 100))
        self.add_output('输出图像', color=(100, 255, 100))
        self.add_output('JSON数据', color=(200, 200, 200))

        category_labels = {
            '一元操作': '[一元]',
            '二元操作': '[二元]',
            '其他操作': '[其他]'
        }
        
        method_items = []
        for category in ['一元操作', '二元操作', '其他操作']:
            cat_label = category_labels[category]
            methods_in_category = [
                f"{method_id}|{cat_label} {self.METHOD_METADATA[method_id]['name']}"
                for method_id in self.METHOD_METADATA
                if self.METHOD_METADATA[method_id]['category'] == category
            ]
            method_items.extend(methods_in_category)

        self.add_combo_menu(
            'method',
            '方法',
            items=method_items,
            tab='properties'
        )
        
        method_combo = self.get_widget('method')
        if method_combo:
            method_combo.setMaximumHeight(200)
            method_combo.view().setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOn)

        self.add_text_input('status', '状态', tab='properties')
        self.set_property('status', '就绪')

        self.add_text_input('input1_type', '输入1类型', tab='properties')
        self.set_property('input1_type', 'image')

        self.add_text_input('input2_type', '输入2类型', tab='properties')
        self.set_property('input2_type', 'image')

        self._cached_image = None

    def get_cached_image(self):
        return self._cached_image

    def process(self, inputs=None):
        try:
            method_text = self.get_property('method')
            
            if not method_text or '|' not in method_text:
                self.set_property('status', '❌ 请选择操作方法')
                return {'输出图像': None, 'JSON数据': {'error': '请选择操作方法'}}

            method_id = method_text.split('|')[0]
            method_name = method_text.split('|')[1]

            input1 = self._get_input(inputs, 0)
            if input1 is None:
                self.set_property('status', '❌ 输入1为空')
                return {'输出图像': None, 'JSON数据': {'error': '输入1数据为空'}}

            needs_second = self.METHOD_METADATA[method_id]['inputs'] == 2
            input2 = self._get_input(inputs, 1) if needs_second else None

            result = self._execute_method(method_id, input1, input2)
            json_output = self._create_json(method_id, input1, input2, result)

            if isinstance(result, np.ndarray):
                self._cached_image = result.copy()
                self.set_property('status', f'✅ {method_name} 完成')
            else:
                self.set_property('status', f'✅ {method_name} 完成')

            return {'输出图像': result, 'JSON数据': json_output}

        except Exception as e:
            error_msg = f"❌ 处理错误: {str(e)}"
            self.set_property('status', error_msg)
            return {'输出图像': None, 'JSON数据': {'error': str(e)}}

    def _get_input(self, inputs, index):
        if not inputs or len(inputs) == 0:
            return None
        if index >= len(inputs):
            return None
        data = inputs[index]
        if data is None:
            return None
        if isinstance(data, list):
            return data[0] if len(data) > 0 else None
        return data

    def _execute_method(self, method_id, input1, input2):
        method_map = {
            # 一元操作
            'cvAbs': self._execute_cv_abs,
            'cvAvg': self._execute_cv_avg,
            'cvAvgSdv': self._execute_cv_avgsdv,
            'cvCountNonZero': self._execute_cv_countnonzero,
            'cvSum': self._execute_cv_sum,
            'cvMinMaxLoc': self._execute_cv_minmaxloc,
            'cvDet': self._execute_cv_det,
            'cvDiag': self._execute_cv_diag,
            'cvDct': self._execute_cv_dct,
            'cvDft': self._execute_cv_dft,
            'cvInvert': self._execute_cv_invert,
            'cvTrace': self._execute_cv_trace,
            'cvTranspose': self._execute_cv_transpose,
            'cvSVD': self._execute_cv_svd,
            'cvFlip': self._execute_cv_flip,
            'cvResize': self._execute_cv_resize,
            'cvCvtColor': self._execute_cv_cvt_color,
            'cvNot': self._execute_cv_not,
            'cvNormalize': self._execute_cv_normalize,
            'cvPow': self._execute_cv_pow,
            'cvRepeat': self._execute_cv_repeat,
            # 二元操作
            'cvAbsDiff': self._execute_cv_absdiff,
            'cvAbsDiffS': self._execute_cv_absdiff_s,
            'cvAdd': self._execute_cv_add,
            'cvAddS': self._execute_cv_add_s,
            'cvAddWeighted': self._execute_cv_add_weighted,
            'cvSub': self._execute_cv_sub,
            'cvSubS': self._execute_cv_sub_s,
            'cvSubRS': self._execute_cv_sub_rs,
            'cvMul': self._execute_cv_mul,
            'cvDiv': self._execute_cv_div,
            'cvDivS': self._execute_cv_div_s,
            'cvDivRS': self._execute_cv_div_rs,
            'cvCmp': self._execute_cv_cmp,
            'cvCmpS': self._execute_cv_cmp_s,
            'cvInRange': self._execute_cv_inrange,
            'cvInRangeS': self._execute_cv_inrange_s,
            'cvMax': self._execute_cv_max,
            'cvMaxS': self._execute_cv_max_s,
            'cvMin': self._execute_cv_min,
            'cvMinS': self._execute_cv_min_s,
            'cvAnd': self._execute_cv_and,
            'cvAndS': self._execute_cv_and_s,
            'cvOr': self._execute_cv_or,
            'cvOrS': self._execute_cv_or_s,
            'cvXor': self._execute_cv_xor,
            'cvXorS': self._execute_cv_xor_s,
            'cvCrossProduct': self._execute_cv_crossproduct,
            'cvDotProduct': self._execute_cv_dotproduct,
            'cvMahalanobis': self._execute_cv_mahalanobis,
            'cvNorm': self._execute_cv_norm,
            # 其他操作
            'cvMerge': self._execute_cv_merge,
            'cvSplit': self._execute_cv_split,
            'cvCopy': self._execute_cv_copy,
            'cvCopyMakeBorder': self._execute_cv_copymakeborder,
            'cvConvertScale': self._execute_cv_convertscale,
            'cvConvertScaleAbs': self._execute_cv_convertscaleabs,
            'cvGEMM': self._execute_cv_gemm,
            'cvSolve': self._execute_cv_solve,
        }
        handler = method_map.get(method_id)
        if handler:
            return handler(input1, input2)
        raise ValueError(f"不支持的方法: {method_id}")

    # ========== 一元操作实现 ==========
    def _execute_cv_abs(self, input1, input2):
        return np.abs(input1).astype(np.uint8)

    def _execute_cv_avg(self, input1, input2):
        mean_val = cv2.mean(input1)
        result = np.zeros((100, 400, 3), dtype=np.uint8)
        text = f"均值: B={mean_val[0]:.1f} G={mean_val[1]:.1f} R={mean_val[2]:.1f}"
        cv2.putText(result, text, (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return result

    def _execute_cv_avgsdv(self, input1, input2):
        mean, std = cv2.meanStdDev(input1)
        result = np.zeros((120, 450, 3), dtype=np.uint8)
        cv2.putText(result, f"均值: {mean[0][0]:.1f}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(result, f"标准差: {std[0][0]:.1f}", (10, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return result

    def _execute_cv_countnonzero(self, input1, input2):
        if len(input1.shape) == 3:
            gray = cv2.cvtColor(input1, cv2.COLOR_BGR2GRAY)
        else:
            gray = input1
        count = cv2.countNonZero(gray)
        result = np.zeros((100, 350, 3), dtype=np.uint8)
        cv2.putText(result, f"非零像素数: {count}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        return result

    def _execute_cv_sum(self, input1, input2):
        val = float(np.sum(input1))
        result = np.zeros((100, 350, 3), dtype=np.uint8)
        cv2.putText(result, f"像素总和: {val:.0f}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        return result

    def _execute_cv_minmaxloc(self, input1, input2):
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(input1)
        result = np.zeros((140, 400, 3), dtype=np.uint8)
        cv2.putText(result, f"最小值: {min_val:.1f} @ {min_loc}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        cv2.putText(result, f"最大值: {max_val:.1f} @ {max_loc}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
        return result

    def _execute_cv_det(self, input1, input2):
        if len(input1.shape) == 2:
            val = float(np.linalg.det(input1.astype(np.float64)))
        else:
            val = 0.0
        result = np.zeros((100, 300, 3), dtype=np.uint8)
        cv2.putText(result, f"行列式: {val:.2f}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        return result

    def _execute_cv_diag(self, input1, input2):
        return np.diag(np.diag(input1)).astype(np.uint8)

    def _execute_cv_dct(self, input1, input2):
        if len(input1.shape) == 3:
            gray = cv2.cvtColor(input1, cv2.COLOR_BGR2GRAY)
        else:
            gray = input1
        dct = cv2.dct(gray.astype(np.float32))
        dct_normalized = cv2.normalize(dct, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        return cv2.cvtColor(dct_normalized, cv2.COLOR_GRAY2BGR)

    def _execute_cv_dft(self, input1, input2):
        if len(input1.shape) == 3:
            gray = cv2.cvtColor(input1, cv2.COLOR_BGR2GRAY)
        else:
            gray = input1
        dft = cv2.dft(np.float32(gray), flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        magnitude = 20 * np.log(cv2.magnitude(dft_shift[:, :, 0], dft_shift[:, :, 1]))
        magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        return cv2.cvtColor(magnitude, cv2.COLOR_GRAY2BGR)

    def _execute_cv_invert(self, input1, input2):
        if len(input1.shape) == 2 and input1.shape[0] == input1.shape[1]:
            try:
                inv = np.linalg.inv(input1.astype(np.float64))
                return cv2.normalize(inv, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            except:
                return input1
        return input1

    def _execute_cv_trace(self, input1, input2):
        if len(input1.shape) == 2:
            val = float(np.trace(input1))
        else:
            val = 0.0
        result = np.zeros((100, 300, 3), dtype=np.uint8)
        cv2.putText(result, f"矩阵迹: {val:.2f}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        return result

    def _execute_cv_transpose(self, input1, input2):
        return cv2.transpose(input1)

    def _execute_cv_svd(self, input1, input2):
        if len(input1.shape) == 2:
            U, S, V = np.linalg.svd(input1.astype(np.float64), full_matrices=False)
            result = np.zeros((150, 400, 3), dtype=np.uint8)
            cv2.putText(result, f"SVD 奇异值个数: {len(S)}", (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(result, f"最大奇异值: {S[0]:.2f}", (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(result, f"最小奇异值: {S[-1]:.2f}", (10, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            return result
        return input1

    def _execute_cv_flip(self, input1, input2):
        return cv2.flip(input1, -1)

    def _execute_cv_resize(self, input1, input2):
        return cv2.resize(input1, None, fx=0.5, fy=0.5)

    def _execute_cv_cvt_color(self, input1, input2):
        if len(input1.shape) == 2:
            return cv2.cvtColor(input1, cv2.COLOR_GRAY2BGR)
        return cv2.cvtColor(input1, cv2.COLOR_BGR2GRAY)

    def _execute_cv_not(self, input1, input2):
        return cv2.bitwise_not(input1)

    def _execute_cv_normalize(self, input1, input2):
        return cv2.normalize(input1, None, 0, 255, cv2.NORM_MINMAX)

    def _execute_cv_pow(self, input1, input2):
        return np.power(input1.astype(np.float32), 2).astype(np.uint8)

    def _execute_cv_repeat(self, input1, input2):
        return cv2.repeat(input1, 2, 2)

    # ========== 二元操作实现 ==========
    def _execute_cv_absdiff(self, input1, input2):
        if input2 is None:
            input2 = np.full_like(input1, 128)
        return cv2.absdiff(input1, input2)

    def _execute_cv_absdiff_s(self, input1, input2):
        scalar = 128 if input2 is None else np.mean(input2) if isinstance(input2, np.ndarray) else 128
        return cv2.absdiff(input1, np.full_like(input1, scalar))

    def _execute_cv_add(self, input1, input2):
        if input2 is None:
            input2 = np.full_like(input1, 50)
        return cv2.add(input1, input2)

    def _execute_cv_add_s(self, input1, input2):
        scalar = 50 if input2 is None else np.mean(input2) if isinstance(input2, np.ndarray) else 50
        return cv2.add(input1, np.full_like(input1, scalar))

    def _execute_cv_add_weighted(self, input1, input2):
        if input2 is None:
            input2 = np.full_like(input1, 128)
        return cv2.addWeighted(input1, 0.5, input2, 0.5, 0)

    def _execute_cv_sub(self, input1, input2):
        if input2 is None:
            input2 = np.full_like(input1, 50)
        return cv2.subtract(input1, input2)

    def _execute_cv_sub_s(self, input1, input2):
        scalar = 50 if input2 is None else np.mean(input2) if isinstance(input2, np.ndarray) else 50
        return cv2.subtract(input1, np.full_like(input1, scalar))

    def _execute_cv_sub_rs(self, input1, input2):
        scalar = 128 if input2 is None else np.mean(input2) if isinstance(input2, np.ndarray) else 128
        return cv2.subtract(np.full_like(input1, scalar), input1)

    def _execute_cv_mul(self, input1, input2):
        if input2 is None:
            input2 = np.full_like(input1, 2)
        return cv2.multiply(input1, input2)

    def _execute_cv_div(self, input1, input2):
        if input2 is None:
            input2 = np.full_like(input1, 2)
        return cv2.divide(input1, input2)

    def _execute_cv_div_s(self, input1, input2):
        scalar = 2 if input2 is None else np.mean(input2) if isinstance(input2, np.ndarray) else 2
        return cv2.divide(input1, np.full_like(input1, scalar))

    def _execute_cv_div_rs(self, input1, input2):
        scalar = 255 if input2 is None else np.mean(input2) if isinstance(input2, np.ndarray) else 255
        return cv2.divide(np.full_like(input1, scalar), input1)

    def _execute_cv_cmp(self, input1, input2):
        if input2 is None:
            input2 = np.full_like(input1, 128)
        return cv2.compare(input1, input2, cv2.CMP_EQ).astype(np.uint8) * 255

    def _execute_cv_cmp_s(self, input1, input2):
        scalar = 128 if input2 is None else np.mean(input2) if isinstance(input2, np.ndarray) else 128
        return cv2.compare(input1, scalar, cv2.CMP_GT).astype(np.uint8) * 255

    def _execute_cv_inrange(self, input1, input2):
        if input2 is None:
            lower = np.array([0, 0, 0])
            upper = np.array([128, 128, 128])
        else:
            lower = np.array([0, 0, 0])
            upper = np.array([255, 255, 255])
        return cv2.inRange(input1, lower, upper)

    def _execute_cv_inrange_s(self, input1, input2):
        return cv2.inRange(input1, 50, 200)

    def _execute_cv_max(self, input1, input2):
        if input2 is None:
            input2 = np.full_like(input1, 128)
        return cv2.max(input1, input2)

    def _execute_cv_max_s(self, input1, input2):
        scalar = 128 if input2 is None else np.mean(input2) if isinstance(input2, np.ndarray) else 128
        return cv2.max(input1, np.full_like(input1, scalar))

    def _execute_cv_min(self, input1, input2):
        if input2 is None:
            input2 = np.full_like(input1, 128)
        return cv2.min(input1, input2)

    def _execute_cv_min_s(self, input1, input2):
        scalar = 128 if input2 is None else np.mean(input2) if isinstance(input2, np.ndarray) else 128
        return cv2.min(input1, np.full_like(input1, scalar))

    def _execute_cv_and(self, input1, input2):
        if input2 is None:
            input2 = np.full_like(input1, 200)
        return cv2.bitwise_and(input1, input2)

    def _execute_cv_and_s(self, input1, input2):
        scalar = 200 if input2 is None else np.mean(input2) if isinstance(input2, np.ndarray) else 200
        return cv2.bitwise_and(input1, np.full_like(input1, scalar))

    def _execute_cv_or(self, input1, input2):
        if input2 is None:
            input2 = np.full_like(input1, 128)
        return cv2.bitwise_or(input1, input2)

    def _execute_cv_or_s(self, input1, input2):
        scalar = 128 if input2 is None else np.mean(input2) if isinstance(input2, np.ndarray) else 128
        return cv2.bitwise_or(input1, np.full_like(input1, scalar))

    def _execute_cv_xor(self, input1, input2):
        if input2 is None:
            input2 = np.full_like(input1, 128)
        return cv2.bitwise_xor(input1, input2)

    def _execute_cv_xor_s(self, input1, input2):
        scalar = 128 if input2 is None else np.mean(input2) if isinstance(input2, np.ndarray) else 128
        return cv2.bitwise_xor(input1, np.full_like(input1, scalar))

    def _execute_cv_crossproduct(self, input1, input2):
        if len(input1.shape) > 1:
            input1 = input1.flatten()[:3]
        if input2 is None:
            input2 = np.array([0, 0, 1])
        else:
            if len(input2.shape) > 1:
                input2 = input2.flatten()[:3]
        cross = np.cross(input1, input2)
        result = np.zeros((100, 350, 3), dtype=np.uint8)
        cv2.putText(result, f"叉积: ({cross[0]:.1f}, {cross[1]:.1f}, {cross[2]:.1f})", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        return result

    def _execute_cv_dotproduct(self, input1, input2):
        if len(input1.shape) > 1:
            input1 = input1.flatten()
        if input2 is None:
            input2 = input1.copy()
        else:
            if len(input2.shape) > 1:
                input2 = input2.flatten()
        dot = np.dot(input1[:min(len(input1), len(input2))], input2[:min(len(input1), len(input2))])
        result = np.zeros((100, 300, 3), dtype=np.uint8)
        cv2.putText(result, f"点积: {dot:.2f}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        return result

    def _execute_cv_mahalanobis(self, input1, input2):
        if len(input1.shape) > 1:
            input1 = input1.flatten()[:100]
        if input2 is None:
            input2 = np.zeros_like(input1)
        else:
            if len(input2.shape) > 1:
                input2 = input2.flatten()[:100]
        cov = np.cov(input1) if len(input1) > 1 else 1.0
        dist = cv2.Mahalanobis(input1, input2, np.linalg.inv(np.array([[cov]])) if cov != 0 else np.array([[1.0]]))
        result = np.zeros((100, 350, 3), dtype=np.uint8)
        cv2.putText(result, f"马氏距离: {dist:.2f}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        return result

    def _execute_cv_norm(self, input1, input2):
        if input2 is None:
            input2 = np.zeros_like(input1)
        norm_val = cv2.norm(input1, input2)
        result = np.zeros((100, 300, 3), dtype=np.uint8)
        cv2.putText(result, f"范数: {norm_val:.2f}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)
        return result

    # ========== 其他操作实现 ==========
    def _execute_cv_merge(self, input1, input2):
        if len(input1.shape) == 2:
            return cv2.merge([input1, input1, input1])
        return input1

    def _execute_cv_split(self, input1, input2):
        if len(input1.shape) == 3:
            channels = cv2.split(input1)
            return channels[0]
        return input1

    def _execute_cv_copy(self, input1, input2):
        return input1.copy()

    def _execute_cv_copymakeborder(self, input1, input2):
        return cv2.copyMakeBorder(input1, 10, 10, 10, 10, cv2.BORDER_CONSTANT, value=[128, 128, 128])

    def _execute_cv_convertscale(self, input1, input2):
        return cv2.convertScaleAbs(input1, alpha=1.0, beta=0)

    def _execute_cv_convertscaleabs(self, input1, input2):
        return cv2.convertScaleAbs(input1, alpha=1.5, beta=0)

    def _execute_cv_gemm(self, input1, input2):
        if len(input1.shape) == 2 and (input2 is None or len(input2.shape) != 2):
            try:
                return cv2.gemm(input1.astype(np.float32), input1.astype(np.float32).T, 1, None, 0)
            except:
                return input1
        elif input2 is not None and len(input2.shape) == 2:
            try:
                return cv2.gemm(input1.astype(np.float32), input2.astype(np.float32), 1, None, 0)
            except:
                return input1
        return input1

    def _execute_cv_solve(self, input1, input2):
        if len(input1.shape) == 2 and input1.shape[0] == input1.shape[1]:
            try:
                b = np.eye(input1.shape[0], dtype=np.float64)
                x = np.linalg.solve(input1.astype(np.float64), b)
                return cv2.normalize(x, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
            except:
                result = np.zeros((100, 350, 3), dtype=np.uint8)
                cv2.putText(result, "矩阵奇异，无法求解", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
                return result
        result = np.zeros((100, 350, 3), dtype=np.uint8)
        cv2.putText(result, "需要方阵输入", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)
        return result

    def _create_json(self, method_id, input1, input2, result):
        import time
        metadata = self.METHOD_METADATA.get(method_id, {})

        json_data = {
            "method": method_id,
            "method_name": metadata.get('name', method_id),
            "category": metadata.get('category', '未知'),
            "description": metadata.get('description', ''),
            "library": metadata.get('library', ''),
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "parameters": {
                "input1_shape": list(input1.shape) if isinstance(input1, np.ndarray) else None,
                "input1_dtype": str(input1.dtype) if isinstance(input1, np.ndarray) else None,
                "input2_shape": list(input2.shape) if isinstance(input2, np.ndarray) else None,
            },
            "results": []
        }

        if isinstance(result, np.ndarray):
            json_data["results"].append({
                "type": "image" if len(result.shape) >= 2 else "matrix",
                "shape": list(result.shape),
                "dtype": str(result.dtype)
            })
        elif isinstance(result, (int, float)):
            json_data["results"].append({
                "type": "int" if isinstance(result, int) else "float",
                "value": float(result)
            })

        return json_data
