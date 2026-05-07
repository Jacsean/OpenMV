import threading
import time
from collections import deque
from typing import Any, Optional


class CircularBuffer:
    def __init__(self, capacity: int = 10, max_age_seconds: float = 5.0):
        self._capacity = capacity
        self._max_age = max_age_seconds
        self._buffer = deque(maxlen=capacity)
        self._lock = threading.Lock()
        self._total_produced = 0
        self._total_consumed = 0
        self._total_dropped = 0

    def put(self, item: Any):
        with self._lock:
            self._clean_old_items()
            if len(self._buffer) >= self._capacity:
                self._total_dropped += 1
            self._buffer.append((time.time(), item))
            self._total_produced += 1

    def get(self) -> Optional[Any]:
        with self._lock:
            self._clean_old_items()
            if self._buffer:
                _, item = self._buffer.popleft()
                self._total_consumed += 1
                return item
            return None

    def peek(self) -> Optional[Any]:
        with self._lock:
            self._clean_old_items()
            if self._buffer:
                return self._buffer[0][1]
            return None

    def _clean_old_items(self):
        now = time.time()
        while self._buffer and (now - self._buffer[0][0]) > self._max_age:
            self._buffer.popleft()
            self._total_dropped += 1

    def get_stats(self) -> dict:
        with self._lock:
            return {
                'capacity': self._capacity,
                'current_size': len(self._buffer),
                'total_produced': self._total_produced,
                'total_consumed': self._total_consumed,
                'total_dropped': self._total_dropped,
                'drop_rate': (self._total_dropped / max(self._total_produced, 1)) * 100
            }

    def clear(self):
        with self._lock:
            self._buffer.clear()

    def is_empty(self) -> bool:
        with self._lock:
            self._clean_old_items()
            return len(self._buffer) == 0

    def is_full(self) -> bool:
        with self._lock:
            return len(self._buffer) >= self._capacity
