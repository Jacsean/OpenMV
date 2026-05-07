import threading
import time
from typing import Callable, Any, Dict, Optional


class PubSubManager:
    def __init__(self):
        self._subscribers: Dict[str, dict] = {}
        self._lock = threading.Lock()
        self._message_count = 0

    def subscribe(self, subscriber_id: str, callback: Callable[[Any], None], 
                  max_fps: float = 30.0) -> bool:
        with self._lock:
            if subscriber_id in self._subscribers:
                return False
            
            self._subscribers[subscriber_id] = {
                'callback': callback,
                'max_fps': max_fps,
                'last_call_time': 0.0,
                'frame_count': 0,
                'dropped_count': 0
            }
            return True

    def unsubscribe(self, subscriber_id: str) -> bool:
        with self._lock:
            if subscriber_id in self._subscribers:
                del self._subscribers[subscriber_id]
                return True
            return False

    def publish(self, message: Any) -> int:
        self._message_count += 1
        now = time.time()
        delivered_count = 0

        with self._lock:
            for sub_id, info in list(self._subscribers.items()):
                if info['max_fps'] > 0:
                    min_interval = 1.0 / info['max_fps']
                    if now - info['last_call_time'] < min_interval:
                        info['dropped_count'] += 1
                        continue
                
                info['last_call_time'] = now
                info['frame_count'] += 1
                delivered_count += 1

                try:
                    info['callback'](message)
                except Exception:
                    pass

        return delivered_count

    def get_all_stats(self) -> dict:
        with self._lock:
            return {
                'active_subscribers': len(self._subscribers),
                'total_messages': self._message_count,
                'subscribers': {
                    sub_id: {
                        'max_fps': info['max_fps'],
                        'frame_count': info['frame_count'],
                        'dropped_count': info['dropped_count']
                    }
                    for sub_id, info in self._subscribers.items()
                }
            }

    def get_subscriber_count(self) -> int:
        with self._lock:
            return len(self._subscribers)

    def clear_all(self):
        with self._lock:
            self._subscribers.clear()
            self._message_count = 0
