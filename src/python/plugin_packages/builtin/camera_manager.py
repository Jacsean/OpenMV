import json
import os
import threading
import numpy as np
import cv2

class SimulatedCamera:
    def __init__(self, config):
        self.config = config
        self.width = int(config.get('resolution', {}).get('width', '640'))
        self.height = int(config.get('resolution', {}).get('height', '480'))
        self.framerate = float(config.get('framerate', '30').split()[0])
        self._pattern_mode = config.get('simulation', {}).get('mode', 'pattern')
        self._frame_count = 0

    def open(self):
        return True

    def close(self):
        return True

    def grab_frame(self):
        self._frame_count += 1
        
        if self._pattern_mode == 'pattern':
            frame = self._generate_pattern()
        elif self._pattern_mode == 'gradient':
            frame = self._generate_gradient()
        else:
            frame = self._generate_random()
        
        return frame

    def _generate_pattern(self):
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        
        cv2.putText(frame, f"Frame: {self._frame_count}", (20, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        
        colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (0, 255, 255)]
        grid_size = 8
        cell_w = self.width // grid_size
        cell_h = self.height // grid_size
        
        for i in range(grid_size):
            for j in range(grid_size):
                color = colors[(i + j + self._frame_count // 10) % len(colors)]
                cv2.rectangle(frame, (i * cell_w, j * cell_h),
                              ((i + 1) * cell_w, (j + 1) * cell_h), color, -1)
        
        return frame

    def _generate_gradient(self):
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        for y in range(self.height):
            for x in range(self.width):
                r = (x + self._frame_count * 2) % 256
                g = (y + self._frame_count * 2) % 256
                b = ((x + y) // 2 + self._frame_count) % 256
                frame[y, x] = (b, g, r)
        return frame

    def _generate_random(self):
        return np.random.randint(0, 255, (self.height, self.width, 3), dtype=np.uint8)

class RealCamera:
    def __init__(self, config):
        self.config = config
        self._is_open = False

    def open(self):
        self._is_open = True
        return True

    def close(self):
        self._is_open = False
        return True

    def grab_frame(self):
        width = int(self.config.get('resolution', {}).get('width', '640'))
        height = int(self.config.get('resolution', {}).get('height', '480'))
        return np.zeros((height, width, 3), dtype=np.uint8)

class CameraManager:
    _instance = None
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = CameraManager()
            return cls._instance

    def __init__(self):
        if CameraManager._instance is not None:
            raise Exception("CameraManager is a singleton!")
        
        self._cameras = {}
        self._camera_id_counter = 0
        self._lock = threading.Lock()
        self._load_config()

    def _load_config(self):
        self.dictionary = {}
        self.seats = []
        
        config_path = os.path.join(
            os.path.dirname(__file__),
            'plugin_camera.json'
        )
        
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.dictionary = config.get('Dictionary', {})
                    self.seats = config.get('Seats', [])
            except Exception as e:
                print(f"[CameraManager] 加载配置文件失败: {e}")
                self._create_default_config()
        else:
            self._create_default_config()

    def _create_default_config(self):
        self.dictionary = {
            "SimulatedCamera": {
                "resolution": {"width": "640", "height": "480"},
                "framerate": "30 fps",
                "simulation": {"mode": "pattern", "frame_interval_ms": 33}
            }
        }
        
        self.seats = [
            {"sn": "SIMULATED_001", "classname": "SimulatedCamera", "seat_index": 0},
            {"sn": "SIMULATED_002", "classname": "SimulatedCamera", "seat_index": 1},
            {"sn": "SIMULATED_003", "classname": "SimulatedCamera", "seat_index": 2},
            {"sn": "SIMULATED_004", "classname": "SimulatedCamera", "seat_index": 3},
            {"sn": "SIMULATED_005", "classname": "SimulatedCamera", "seat_index": 4}
        ]

    def get_seat_count(self):
        return len(self.seats)

    def get_seat_info(self, seat_index):
        if 0 <= seat_index < len(self.seats):
            return self.seats[seat_index]
        return None

    def initialize_camera(self, seat_index):
        with self._lock:
            if seat_index < 0 or seat_index >= len(self.seats):
                return None
            
            seat_info = self.seats[seat_index]
            classname = seat_info.get('classname', 'SimulatedCamera')
            sn = seat_info.get('sn', '')
            
            camera_config = self.dictionary.get(classname, {})
            camera_config['sn'] = sn
            
            if sn.startswith('SIMULATED'):
                camera = SimulatedCamera(camera_config)
            else:
                camera = RealCamera(camera_config)
            
            if camera.open():
                camera_id = f"camera_{self._camera_id_counter}"
                self._camera_id_counter += 1
                self._cameras[camera_id] = camera
                return camera_id
        
        return None

    def get_camera(self, camera_id):
        with self._lock:
            return self._cameras.get(camera_id)

    def release_camera(self, camera_id):
        with self._lock:
            camera = self._cameras.pop(camera_id, None)
            if camera:
                camera.close()

    def release_all(self):
        with self._lock:
            for camera in self._cameras.values():
                camera.close()
            self._cameras.clear()
