"""
环形缓冲区模块

提供线程安全的固定大小队列，用于高速图像流缓冲。
当生产者速度快于消费者时，自动覆盖最旧的帧。
"""

import threading
from collections import deque
from typing import Optional, List
import numpy as np


class CircularBuffer:
    """
    线程安全的环形缓冲区
    
    特性：
    - 固定容量，满时自动覆盖最旧数据
    - 支持多生产者、多消费者
    - 零拷贝设计（存储引用而非深拷贝）
    - 可选的最大年龄限制（自动清理过期帧）
    
    使用场景：
    - 高速相机采集缓冲
    - 实时视频流处理
    - 多路并行消费
    """
    
    def __init__(self, capacity: int = 10, max_age_seconds: float = 5.0):
        """
        初始化环形缓冲区
        
        Args:
            capacity: 缓冲区容量（最大帧数）
            max_age_seconds: 帧的最大存活时间（秒），超时自动丢弃
        """
        self.capacity = capacity
        self.max_age_seconds = max_age_seconds
        
        # 使用 deque 实现环形缓冲
        self._buffer = deque(maxlen=capacity)
        
        # 线程锁
        self._lock = threading.RLock()
        
        # 统计信息
        self.total_produced = 0
        self.total_consumed = 0
        self.total_dropped = 0
        
        # 时间戳队列（与帧对应）
        self._timestamps = deque(maxlen=capacity)
    
    def put(self, frame: np.ndarray) -> bool:
        """
        放入一帧（生产者调用）
        
        Args:
            frame: 图像帧（NumPy数组）
            
        Returns:
            bool: 是否成功放入
        """
        if frame is None:
            return False
        
        import time
        timestamp = time.time()
        
        with self._lock:
            # 如果缓冲区已满，记录丢帧
            if len(self._buffer) >= self.capacity:
                self.total_dropped += 1
            
            # 放入新帧和时间戳
            self._buffer.append(frame)
            self._timestamps.append(timestamp)
            self.total_produced += 1
        
        return True
    
    def get_latest(self) -> Optional[np.ndarray]:
        """
        获取最新的一帧（消费者调用）
        
        Returns:
            numpy.ndarray or None: 最新帧
        """
        with self._lock:
            if not self._buffer:
                return None
            
            # 清理过期帧
            self._cleanup_expired()
            
            if not self._buffer:
                return None
            
            # 返回最新帧的引用（零拷贝）
            frame = self._buffer[-1]
            self.total_consumed += 1
            return frame
    
    def get_oldest(self) -> Optional[np.ndarray]:
        """
        获取最旧的一帧（FIFO模式）
        
        Returns:
            numpy.ndarray or None: 最旧帧
        """
        with self._lock:
            if not self._buffer:
                return None
            
            # 清理过期帧
            self._cleanup_expired()
            
            if not self._buffer:
                return None
            
            # 弹出最旧帧
            frame = self._buffer.popleft()
            self._timestamps.popleft()
            self.total_consumed += 1
            return frame
    
    def get_all(self) -> List[np.ndarray]:
        """
        获取所有可用帧（批量消费）
        
        Returns:
            list: 帧列表（从旧到新）
        """
        with self._lock:
            # 清理过期帧
            self._cleanup_expired()
            
            frames = list(self._buffer)
            self.total_consumed += len(frames)
            
            # 清空缓冲区
            self._buffer.clear()
            self._timestamps.clear()
            
            return frames
    
    def size(self) -> int:
        """获取当前缓冲区中的帧数"""
        with self._lock:
            return len(self._buffer)
    
    def is_empty(self) -> bool:
        """检查缓冲区是否为空"""
        with self._lock:
            return len(self._buffer) == 0
    
    def is_full(self) -> bool:
        """检查缓冲区是否已满"""
        with self._lock:
            return len(self._buffer) >= self.capacity
    
    def clear(self):
        """清空缓冲区"""
        with self._lock:
            self._buffer.clear()
            self._timestamps.clear()
    
    def get_stats(self) -> dict:
        """
        获取统计信息
        
        Returns:
            dict: 包含生产/消费/丢帧统计
        """
        with self._lock:
            return {
                'capacity': self.capacity,
                'current_size': len(self._buffer),
                'total_produced': self.total_produced,
                'total_consumed': self.total_consumed,
                'total_dropped': self.total_dropped,
                'drop_rate': self.total_dropped / max(self.total_produced, 1) * 100
            }
    
    def _cleanup_expired(self):
        """清理过期的帧（内部调用，需持有锁）"""
        import time
        current_time = time.time()
        
        while self._buffer and self._timestamps:
            oldest_timestamp = self._timestamps[0]
            age = current_time - oldest_timestamp
            
            if age > self.max_age_seconds:
                # 移除过期帧
                self._buffer.popleft()
                self._timestamps.popleft()
                self.total_dropped += 1
            else:
                # 后续帧都未过期
                break


# 导出类
__all__ = ['CircularBuffer']
