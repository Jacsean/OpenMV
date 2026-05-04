"""
发布-订阅机制模块

实现相机图像流的发布-订阅模式，支持多路并行消费。
订阅者注册回调函数，帧到达时异步推送给所有订阅者。
"""

import threading
from typing import Callable, Dict, List, Optional
import numpy as np
import time


class FrameSubscriber:
    """
    帧订阅者
    
    封装订阅者的回调函数和元数据
    """
    
    def __init__(self, subscriber_id: str, callback: Callable[[np.ndarray], None], 
                 max_fps: float = 30.0):
        """
        初始化订阅者
        
        Args:
            subscriber_id: 订阅者唯一标识
            callback: 回调函数，接收一帧图像
            max_fps: 最大处理帧率（限流）
        """
        self.subscriber_id = subscriber_id
        self.callback = callback
        self.max_fps = max_fps
        self.min_interval = 1.0 / max_fps if max_fps > 0 else 0
        
        # 状态信息
        self.last_call_time = 0
        self.frame_count = 0
        self.error_count = 0
        self.is_active = True
    
    def notify(self, frame: np.ndarray) -> bool:
        """
        通知订阅者有新帧
        
        Args:
            frame: 图像帧
            
        Returns:
            bool: 是否成功调用
        """
        if not self.is_active:
            return False
        
        # 限流检查
        current_time = time.time()
        elapsed = current_time - self.last_call_time
        if elapsed < self.min_interval:
            return False  # 跳过，频率太高
        
        try:
            # 调用回调函数
            self.callback(frame)
            self.last_call_time = current_time
            self.frame_count += 1
            return True
        except Exception as e:
            print(f"[Subscriber {self.subscriber_id}] 回调错误: {e}")
            self.error_count += 1
            return False
    
    def get_stats(self) -> dict:
        """获取订阅者统计信息"""
        return {
            'subscriber_id': self.subscriber_id,
            'frame_count': self.frame_count,
            'error_count': self.error_count,
            'max_fps': self.max_fps,
            'is_active': self.is_active
        }


class PubSubManager:
    """
    发布-订阅管理器
    
    管理多个订阅者，帧到达时异步推送给所有活跃的订阅者。
    每个订阅者在独立线程中处理，互不阻塞。
    """
    
    def __init__(self):
        """初始化发布-订阅管理器"""
        self._subscribers: Dict[str, FrameSubscriber] = {}
        self._lock = threading.RLock()
        
        # 统计信息
        self.total_published = 0
        self.total_notifications = 0
    
    def subscribe(self, subscriber_id: str, callback: Callable[[np.ndarray], None],
                  max_fps: float = 30.0) -> bool:
        """
        注册订阅者
        
        Args:
            subscriber_id: 订阅者唯一标识
            callback: 回调函数
            max_fps: 最大处理帧率
            
        Returns:
            bool: 是否成功注册
        """
        with self._lock:
            if subscriber_id in self._subscribers:
                print(f"[PubSub] 警告: 订阅者已存在: {subscriber_id}")
                return False
            
            subscriber = FrameSubscriber(subscriber_id, callback, max_fps)
            self._subscribers[subscriber_id] = subscriber
            print(f"[PubSub] 订阅者注册成功: {subscriber_id} (max_fps={max_fps})")
            return True
    
    def unsubscribe(self, subscriber_id: str) -> bool:
        """
        取消订阅
        
        Args:
            subscriber_id: 订阅者标识
            
        Returns:
            bool: 是否成功取消
        """
        with self._lock:
            if subscriber_id not in self._subscribers:
                print(f"[PubSub] 警告: 订阅者不存在: {subscriber_id}")
                return False
            
            subscriber = self._subscribers.pop(subscriber_id)
            subscriber.is_active = False
            print(f"[PubSub] 订阅者已取消: {subscriber_id}")
            return True
    
    def publish(self, frame: np.ndarray) -> int:
        """
        发布帧给所有订阅者
        
        Args:
            frame: 图像帧
            
        Returns:
            int: 成功通知的订阅者数量
        """
        if frame is None:
            return 0
        
        with self._lock:
            active_subscribers = [
                sub for sub in self._subscribers.values() 
                if sub.is_active
            ]
        
        if not active_subscribers:
            return 0
        
        # 异步通知所有订阅者（避免阻塞生产者）
        success_count = 0
        for subscriber in active_subscribers:
            # 在独立线程中调用回调（非阻塞）
            thread = threading.Thread(
                target=subscriber.notify,
                args=(frame,),
                daemon=True,
                name=f"Subscriber_{subscriber.subscriber_id}"
            )
            thread.start()
            success_count += 1
        
        self.total_published += 1
        self.total_notifications += success_count
        
        return success_count
    
    def get_subscriber_count(self) -> int:
        """获取活跃订阅者数量"""
        with self._lock:
            return len([sub for sub in self._subscribers.values() if sub.is_active])
    
    def get_all_stats(self) -> dict:
        """获取所有订阅者的统计信息"""
        with self._lock:
            return {
                'total_subscribers': len(self._subscribers),
                'active_subscribers': self.get_subscriber_count(),
                'total_published': self.total_published,
                'total_notifications': self.total_notifications,
                'subscribers': {
                    sid: sub.get_stats() 
                    for sid, sub in self._subscribers.items()
                }
            }
    
    def clear_all(self):
        """清空所有订阅者"""
        with self._lock:
            for subscriber in self._subscribers.values():
                subscriber.is_active = False
            self._subscribers.clear()
            print("[PubSub] 所有订阅者已清除")


# 导出类
__all__ = ['FrameSubscriber', 'PubSubManager']
