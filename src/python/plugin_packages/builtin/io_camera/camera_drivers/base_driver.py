"""
相机驱动抽象基类模块

定义统一的相机接口，所有具体相机驱动必须实现此接口。
"""

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class BaseCameraDriver(ABC):
    """
    相机驱动抽象基类
    
    所有具体的相机驱动（海康威视、巴斯勒等）都必须继承此类
    并实现所有抽象方法。
    """
    
    def __init__(self, config: dict, seat_config: dict):
        """
        初始化相机驱动
        
        Args:
            config: Dictionary段的相机技术参数
            seat_config: Seats段的运行时配置
        """
        self.config = config
        self.seat_config = seat_config
        self.serial_number = seat_config.get('sn', '')
        self.is_initialized = False
        self.is_opened = False
        self.handle = None
        
    @abstractmethod
    def load_driver(self) -> bool:
        """
        加载相机驱动（DLL/SO）
        
        Returns:
            bool: 是否成功加载
        """
        pass
    
    @abstractmethod
    def enumerate_devices(self) -> list:
        """
        枚举可用的相机设备
        
        Returns:
            list: 设备信息列表，每个元素包含 {'sn': ..., 'model': ...}
        """
        pass
    
    @abstractmethod
    def initialize(self) -> bool:
        """
        初始化相机设备
        
        Returns:
            bool: 是否成功初始化
        """
        pass
    
    @abstractmethod
    def open(self) -> bool:
        """
        打开相机（应用参数、启动流）
        
        Returns:
            bool: 是否成功打开
        """
        pass
    
    @abstractmethod
    def close(self):
        """关闭相机，释放资源"""
        pass
    
    @abstractmethod
    def grab_frame(self) -> Optional[np.ndarray]:
        """
        抓取一帧图像
        
        Returns:
            numpy.ndarray or None: BGR格式图像
        """
        pass
    
    @abstractmethod
    def set_exposure(self, exposure_us: int) -> bool:
        """
        设置曝光时间
        
        Args:
            exposure_us: 曝光时间（微秒）
            
        Returns:
            bool: 是否成功设置
        """
        pass
    
    @abstractmethod
    def set_gain(self, gain: float) -> bool:
        """
        设置增益
        
        Args:
            gain: 增益值
            
        Returns:
            bool: 是否成功设置
        """
        pass
    
    def get_info(self) -> dict:
        """
        获取相机信息
        
        Returns:
            dict: 相机状态和信息
        """
        return {
            'type': 'real',
            'driver': self.__class__.__name__,
            'serial_number': self.serial_number,
            'model': self.config.get('classname', ''),
            'is_initialized': self.is_initialized,
            'is_opened': self.is_opened
        }
