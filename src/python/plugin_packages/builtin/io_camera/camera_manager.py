"""
相机管理器模块

提供统一的相机管理接口，支持：
- 加载 plugin_camera.json 配置
- 管理多相机实例（真实相机 + 模拟相机）
- 线程安全的相机访问
- 自动回退到模拟相机（无硬件时）
"""

import os
import json
import threading
from typing import Dict, Optional, Any
import numpy as np


class SimulatedCamera:
    """
    模拟相机类（用于测试和无硬件环境）
    
    生成标准测试图案，支持多种模拟模式
    """
    
    def __init__(self, config: dict):
        """
        初始化模拟相机
        
        Args:
            config: 相机配置字典（来自 Dictionary 段）
        """
        self.resolution = (
            int(config['resolution']['width']),
            int(config['resolution']['height'])
        )
        self.framerate = float(config.get('framerate', '30 fps').split()[0])
        self.frame_count = 0
        self.config = config
        
        # 模拟模式配置
        sim_config = config.get('simulation', {})
        self.simulation_mode = sim_config.get('mode', 'pattern')
        self.frame_interval_ms = sim_config.get('frame_interval_ms', 33)
        
    def grab_frame(self) -> np.ndarray:
        """
        抓取一帧图像（生成模拟数据）
        
        Returns:
            numpy.ndarray: BGR格式图像
        """
        self.frame_count += 1
        
        if self.simulation_mode == 'pattern':
            return self._generate_test_pattern()
        elif self.simulation_mode == 'noise':
            return self._generate_noise_image()
        elif self.simulation_mode == 'gradient':
            return self._generate_gradient()
        else:
            return self._generate_test_pattern()
    
    def _generate_test_pattern(self) -> np.ndarray:
        """生成彩色条纹测试图（类似电视测试卡）"""
        width, height = self.resolution  # 注意：resolution是(width, height)
        frame = np.zeros((height, width, 3), dtype=np.uint8)  # NumPy形状是(height, width, channels)
        
        # 定义8种标准颜色（BGR格式）
        colors = [
            (255, 255, 255),  # 白
            (255, 255, 0),    # 黄
            (0, 255, 255),    # 青
            (0, 255, 0),      # 绿
            (255, 0, 255),    # 品红
            (255, 0, 0),      # 红
            (0, 0, 255),      # 蓝
            (0, 0, 0),        # 黑
        ]
        
        block_width = width // len(colors)
        for i, color in enumerate(colors):
            x_start = i * block_width
            x_end = (i + 1) * block_width
            frame[:, x_start:x_end] = color
        
        # 添加帧计数文本
        import cv2
        cv2.putText(frame, f"Frame: {self.frame_count}", 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Simulated", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        
        return frame
    
    def _generate_noise_image(self) -> np.ndarray:
        """生成随机噪声图像"""
        width, height = self.resolution
        return np.random.randint(0, 256, (height, width, 3), dtype=np.uint8)
    
    def _generate_gradient(self) -> np.ndarray:
        """生成灰度渐变图像"""
        width, height = self.resolution
        gradient = np.linspace(0, 255, width, dtype=np.uint8)
        frame = np.tile(gradient, (height, 1))
        import cv2
        return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
    
    def get_info(self) -> dict:
        """获取相机信息"""
        return {
            'type': 'simulated',
            'resolution': self.resolution,
            'framerate': self.framerate,
            'frame_count': self.frame_count,
            'mode': self.simulation_mode
        }


class RealCamera:
    """
    真实相机包装类
    
    封装DLL驱动调用，提供统一的相机接口
    （当前为占位实现，待集成实际SDK）
    """
    
    def __init__(self, config: dict, seat_config: dict):
        """
        初始化真实相机
        
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
        
    def initialize(self) -> bool:
        """
        初始化相机设备（加载DLL、枚举设备）
        
        Returns:
            bool: 是否成功
        """
        # TODO: 实现真实的DLL加载和设备枚举
        # 当前返回True作为占位
        self.is_initialized = True
        return True
    
    def open(self) -> bool:
        """
        打开相机（应用参数、启动流）
        
        Returns:
            bool: 是否成功
        """
        if not self.is_initialized:
            return False
        
        # TODO: 实现真实的相机打开逻辑
        self.is_opened = True
        return True
    
    def close(self):
        """关闭相机，释放资源"""
        self.is_opened = False
        # TODO: 释放相机句柄
    
    def grab_frame(self) -> Optional[np.ndarray]:
        """
        抓取一帧图像
        
        Returns:
            numpy.ndarray or None: BGR格式图像
        """
        if not self.is_opened:
            return None
        
        # TODO: 实现真实的图像采集
        # 临时返回黑色图像
        resolution = self.config.get('resolution', {'width': '640', 'height': '480'})
        width = int(resolution['width'])
        height = int(resolution['height'])
        return np.zeros((height, width, 3), dtype=np.uint8)
    
    def get_info(self) -> dict:
        """获取相机信息"""
        return {
            'type': 'real',
            'serial_number': self.serial_number,
            'model': self.config.get('classname', ''),
            'is_initialized': self.is_initialized,
            'is_opened': self.is_opened
        }


class CameraManager:
    """
    相机管理器单例类
    
    职责：
    - 加载并解析 plugin_camera.json 配置
    - 管理所有相机实例（真实 + 模拟）
    - 提供线程安全的相机访问接口
    - 自动检测并回退到模拟相机
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """单例模式实现"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """初始化（仅执行一次）"""
        if self._initialized:
            return
        
        self.cameras: Dict[str, Any] = {}  # {camera_id: camera_instance}
        self.config: dict = {}
        self.dictionary: dict = {}  # {classname: config}
        self.seats: list = []
        self._load_config()
        self._initialized = True
    
    def _load_config(self):
        """加载 plugin_camera.json 配置文件"""
        try:
            # 获取配置文件路径（相对于当前文件）
            config_path = os.path.join(
                os.path.dirname(__file__),
                'plugin_camera.json'
            )
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            # 解析 Dictionary 段
            for item in self.config.get('Dictionary', []):
                for classname, params in item.items():
                    self.dictionary[classname] = params
            
            # 解析 Seats 段
            self.seats = self.config.get('Seats', [])
            
            print(f"[CameraManager] 配置加载成功: {len(self.dictionary)} 种型号, {len(self.seats)} 个Seat")
            
        except Exception as e:
            print(f"[CameraManager] 配置加载失败: {e}")
            self.config = {}
            self.dictionary = {}
            self.seats = []
    
    def get_seat_count(self) -> int:
        """获取可用的Seat数量"""
        return len(self.seats)
    
    def get_seat_info(self, seat_index: int) -> Optional[dict]:
        """
        获取指定Seat的信息
        
        Args:
            seat_index: Seat索引（0-based）
            
        Returns:
            dict: Seat配置信息，包含classname、sn、Magnification等
        """
        if 0 <= seat_index < len(self.seats):
            return self.seats[seat_index]
        return None
    
    def get_dictionary_info(self, classname: str) -> Optional[dict]:
        """
        获取指定型号的Dictionary配置
        
        Args:
            classname: 相机型号类名
            
        Returns:
            dict: 技术参数配置
        """
        return self.dictionary.get(classname)
    
    def initialize_camera(self, seat_index: int) -> Optional[str]:
        """
        初始化指定Seat的相机
        
        Args:
            seat_index: Seat索引
            
        Returns:
            str: camera_id（成功）或 None（失败）
        """
        seat_info = self.get_seat_info(seat_index)
        if not seat_info:
            print(f"[CameraManager] Seat索引无效: {seat_index}")
            return None
        
        classname = seat_info.get('classname', '')
        serial_number = seat_info.get('sn', '')
        camera_id = f"cam_{seat_index}"
        
        # 检查是否已初始化
        if camera_id in self.cameras:
            print(f"[CameraManager] 相机已初始化: {camera_id}")
            return camera_id
        
        # 获取Dictionary配置
        dict_config = self.get_dictionary_info(classname)
        if not dict_config:
            print(f"[CameraManager] 未找到型号配置: {classname}")
            return None
        
        # 判断是否为模拟相机
        is_simulated = serial_number.startswith('SIMULATED') or \
                      seat_info.get('custom_params', {}).get('simulation', {}).get('enabled', False)
        
        if is_simulated:
            # 创建模拟相机
            sim_config = dict_config.copy()
            sim_config['simulation'] = seat_info.get('custom_params', {}).get('simulation', {})
            camera = SimulatedCamera(sim_config)
            print(f"[CameraManager] 创建模拟相机: {camera_id} (SN: {serial_number})")
        else:
            # 创建真实相机（占位）
            camera = RealCamera(dict_config, seat_info)
            print(f"[CameraManager] 创建真实相机: {camera_id} (SN: {serial_number})")
            
            # 尝试初始化真实相机
            if not camera.initialize():
                print(f"[CameraManager] 真实相机初始化失败，回退到模拟模式")
                camera = SimulatedCamera(dict_config)
        
        # 存储相机实例
        self.cameras[camera_id] = camera
        return camera_id
    
    def get_camera(self, camera_id: str) -> Optional[Any]:
        """
        获取相机实例
        
        Args:
            camera_id: 相机ID（如 "cam_0"）
            
        Returns:
            相机实例或 None
        """
        return self.cameras.get(camera_id)
    
    def release_camera(self, camera_id: str):
        """
        释放相机资源
        
        Args:
            camera_id: 相机ID
        """
        camera = self.cameras.get(camera_id)
        if camera:
            if hasattr(camera, 'close'):
                camera.close()
            del self.cameras[camera_id]
            print(f"[CameraManager] 相机已释放: {camera_id}")
    
    def release_all(self):
        """释放所有相机资源"""
        for camera_id in list(self.cameras.keys()):
            self.release_camera(camera_id)
        print("[CameraManager] 所有相机已释放")
    
    @classmethod
    def get_instance(cls) -> 'CameraManager':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    @classmethod
    def reset_instance(cls):
        """重置单例（用于测试）"""
        with cls._lock:
            if cls._instance:
                cls._instance.release_all()
            cls._instance = None
