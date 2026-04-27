"""
YOLO 预训练模型注册表

提供常用 YOLO 模型的元数据和下载链接
"""

MODEL_REGISTRY = {
    # YOLOv8 目标检测模型
    'yolov8n': {
        'name': 'YOLOv8 Nano',
        'type': 'detection',
        'size_mb': 6.2,
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt',
        'description': '最小最快，适合实时应用',
        'recommended_use': '工厂现场部署、低配设备'
    },
    'yolov8s': {
        'name': 'YOLOv8 Small',
        'type': 'detection',
        'size_mb': 21.5,
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s.pt',
        'description': '平衡速度与精度',
        'recommended_use': '通用场景'
    },
    'yolov8m': {
        'name': 'YOLOv8 Medium',
        'type': 'detection',
        'size_mb': 49.7,
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8m.pt',
        'description': '精度较高',
        'recommended_use': '高精度需求场景'
    },
    'yolov8l': {
        'name': 'YOLOv8 Large',
        'type': 'detection',
        'size_mb': 83.7,
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8l.pt',
        'description': '高精度',
        'recommended_use': '工作站环境'
    },
    'yolov8x': {
        'name': 'YOLOv8 Xlarge',
        'type': 'detection',
        'size_mb': 130.0,
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8x.pt',
        'description': '最高精度',
        'recommended_use': '云端服务器'
    },
    
    # YOLOv8 分类模型
    'yolov8n-cls': {
        'name': 'YOLOv8 Nano Classification',
        'type': 'classification',
        'size_mb': 5.5,
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n-cls.pt',
        'description': '图像分类 Nano 模型',
        'recommended_use': '快速分类任务'
    },
    'yolov8s-cls': {
        'name': 'YOLOv8 Small Classification',
        'type': 'classification',
        'size_mb': 18.2,
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s-cls.pt',
        'description': '图像分类 Small 模型',
        'recommended_use': '通用分类任务'
    },
    
    # YOLOv8 分割模型
    'yolov8n-seg': {
        'name': 'YOLOv8 Nano Segmentation',
        'type': 'segmentation',
        'size_mb': 6.8,
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n-seg.pt',
        'description': '实例分割 Nano 模型',
        'recommended_use': '实时分割任务'
    },
    'yolov8s-seg': {
        'name': 'YOLOv8 Small Segmentation',
        'type': 'segmentation',
        'size_mb': 23.4,
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s-seg.pt',
        'description': '实例分割 Small 模型',
        'recommended_use': '通用分割任务'
    },
    
    # YOLOv8 姿态估计模型
    'yolov8n-pose': {
        'name': 'YOLOv8 Nano Pose',
        'type': 'pose',
        'size_mb': 6.5,
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n-pose.pt',
        'description': '姿态估计 Nano 模型',
        'recommended_use': '实时姿态检测'
    },
    'yolov8s-pose': {
        'name': 'YOLOv8 Small Pose',
        'type': 'pose',
        'size_mb': 22.1,
        'url': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8s-pose.pt',
        'description': '姿态估计 Small 模型',
        'recommended_use': '通用姿态检测'
    },
}


def get_model_info(model_name: str) -> dict:
    """
    获取模型信息
    
    Args:
        model_name: 模型名称（如 'yolov8n'）
        
    Returns:
        dict: 模型元数据，如果不存在返回 None
    """
    return MODEL_REGISTRY.get(model_name)


def list_models(model_type: str = None) -> list:
    """
    列出可用模型
    
    Args:
        model_type: 模型类型过滤（detection/classification/segmentation/pose）
        
    Returns:
        list: 模型名称列表
    """
    if model_type:
        return [name for name, info in MODEL_REGISTRY.items() 
                if info['type'] == model_type]
    return list(MODEL_REGISTRY.keys())


def get_default_model(model_type: str = 'detection') -> str:
    """
    获取默认模型推荐
    
    Args:
        model_type: 模型类型
        
    Returns:
        str: 推荐的默认模型名称
    """
    defaults = {
        'detection': 'yolov8n',
        'classification': 'yolov8n-cls',
        'segmentation': 'yolov8n-seg',
        'pose': 'yolov8n-pose'
    }
    return defaults.get(model_type, 'yolov8n')
