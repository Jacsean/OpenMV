# Phase 2 实施报告：真实相机 SDK 集成

## 📋 概述

**阶段**: Phase 2 - 真实相机驱动框架  
**状态**: ✅ **框架完成，待集成真实SDK**  
**分支**: `feature-camera-capture-node`  

---

## ✅ 已完成工作

### 1. 相机驱动抽象层

#### **BaseCameraDriver 抽象基类** (`camera_drivers/base_driver.py`)

定义了所有相机驱动必须实现的统一接口：

```python
class BaseCameraDriver(ABC):
    @abstractmethod
    def load_driver(self) -> bool: ...
    
    @abstractmethod
    def enumerate_devices(self) -> list: ...
    
    @abstractmethod
    def initialize(self) -> bool: ...
    
    @abstractmethod
    def open(self) -> bool: ...
    
    @abstractmethod
    def close(self): ...
    
    @abstractmethod
    def grab_frame(self) -> Optional[np.ndarray]: ...
    
    @abstractmethod
    def set_exposure(self, exposure_us: int) -> bool: ...
    
    @abstractmethod
    def set_gain(self, gain: float) -> bool: ...
```

**设计优势**：
- ✅ 统一的 API，上层代码无需关心具体品牌
- ✅ 易于扩展新品牌（只需继承并实现接口）
- ✅ 强制契约，避免遗漏关键方法

---

### 2. 海康威视 MVS SDK 驱动

#### **HikRobotDriver** (`camera_drivers/hikrobot_driver.py`)

实现了海康威视相机的驱动框架：

**功能清单**：
- ✅ DLL 动态加载（`MvCameraControl.dll`）
- ✅ 设备枚举接口（待实现真实 SDK 调用）
- ✅ 相机初始化和打开
- ✅ 图像采集（当前返回占位数据）
- ✅ 曝光时间设置
- ✅ 增益设置
- ✅ 完整的错误处理和日志

**配置示例**：
```json
{
  "classname": "CCameraMVCA05010GM",
  "path": "./plugins/camera/HIKROBOT/",
  "filename": "MVCA05010.dll",
  "supplier": "HIKROBOT(www.hikrobotics.com)"
}
```

**待实现部分**（需要真实 SDK）：
- ⏳ `enumerate_devices()`: 调用 `MV_CC_EnumDevices`
- ⏳ `initialize()`: 调用 `MV_CC_CreateHandle` + `MV_CC_OpenDevice`
- ⏳ `grab_frame()`: 调用 `MV_CC_GetOneFrameTimeout`
- ⏳ 参数设置：调用 `MV_CC_SetFloatValue`

---

### 3. 驱动自动检测与加载

#### **RealCamera 升级** (`camera_manager.py`)

实现了智能驱动选择逻辑：

```python
def _load_driver(self):
    """根据配置自动加载合适的相机驱动"""
    classname = self.config.get('classname', '')
    
    # 海康威视
    if 'HIKROBOT' in supplier or 'MVC' in classname:
        self.driver = HikRobotDriver(...)
    
    # 巴斯勒
    elif 'BASLER' in supplier or 'acA' in classname:
        self.driver = BaslerDriver(...)
    
    # 未知品牌
    else:
        print("警告: 使用占位实现")
```

**特性**：
- ✅ 根据 `supplier` 字段或 `classname` 前缀自动识别品牌
- ✅ 条件导入，驱动不存在时不影响系统运行
- ✅ 详细的日志记录加载过程
- ✅ 未知品牌时使用占位实现（返回黑色图像）

---

## 📊 技术架构

### 驱动加载流程

```
CameraManager.initialize_camera(seat_index)
    ↓
RealCamera.__init__(config, seat_config)
    ↓
RealCamera._load_driver()
    ├→ 检测品牌（HIKROBOT/BASLER/...）
    ├→ 尝试导入对应驱动类
    └→ 创建驱动实例
    
RealCamera.initialize()
    ↓
driver.initialize()
    ├→ driver.load_driver()  # 加载DLL
    ├→ driver.enumerate_devices()  # 枚举设备
    └→ 创建设备句柄
    
RealCamera.open()
    ↓
driver.open()
    ├→ 连接设备
    ├→ 应用参数（曝光、增益）
    └→ 启动图像流
    
RealCamera.grab_frame()
    ↓
driver.grab_frame()
    ├→ 分配缓冲区
    ├→ 调用SDK采集
    └→ 转换为NumPy数组 (BGR)
```

---

## 🔧 下一步工作（待完成）

### 短期任务

1. **集成真实 MVS SDK**
   - [ ] 安装海康威视 MVS 软件包
   - [ ] 获取 SDK 头文件和库文件
   - [ ] 实现 `enumerate_devices()` 真实调用
   - [ ] 实现 `initialize()` 设备连接
   - [ ] 实现 `grab_frame()` 图像采集
   - [ ] 测试真实相机硬件

2. **完善错误处理**
   - [ ] SDK 错误码映射到友好消息
   - [ ] 连接超时重试机制
   - [ ] 断线重连支持

3. **性能优化**
   - [ ] 使用回调模式替代轮询
   - [ ] 零拷贝数据传输
   - [ ] 多线程采集

### 中期任务

4. **巴斯勒 pylon SDK 支持**
   - [ ] 实现 `BaslerDriver` 类
   - [ ] 加载 `pylonC.dll`
   - [ ] 设备枚举和连接
   - [ ] 图像采集

5. **多相机同步**
   - [ ] 硬件触发同步
   - [ ] 时间戳对齐
   - [ ] 帧率匹配

---

## 📝 代码统计

| 文件 | 行数 | 说明 |
|------|------|------|
| `base_driver.py` | 95 | 抽象基类 |
| `hikrobot_driver.py` | 180 | 海康威视驱动框架 |
| `__init__.py` | 15 | 模块导出 |
| `camera_manager.py` (修改) | +80 | RealCamera 升级 |

**总计**: ~370 行新增代码

---

## 🧪 测试计划

### 单元测试（待实现）

```python
def test_driver_loading():
    """测试驱动加载"""
    config = {...}
    seat_config = {...}
    
    camera = RealCamera(config, seat_config)
    assert camera.driver is not None
    assert isinstance(camera.driver, HikRobotDriver)

def test_dll_loading():
    """测试DLL加载"""
    driver = HikRobotDriver(config, seat_config)
    success = driver.load_driver()
    assert success == True  # 如果DLL存在

def test_frame_capture():
    """测试图像采集"""
    driver.initialize()
    driver.open()
    frame = driver.grab_frame()
    assert frame.shape == (height, width, 3)
    assert frame.dtype == np.uint8
```

### 集成测试（需要硬件）

1. **单相机测试**
   - 连接海康威视相机
   - 初始化、打开、采集
   - 验证图像质量

2. **多相机测试**
   - 同时连接 2-4 个相机
   - 并发采集
   - 验证帧率稳定性

3. **压力测试**
   - 连续采集 1 小时
   - 监控内存泄漏
   - 验证稳定性

---

## 📚 相关文档

- [MVS SDK 文档](https://www.hikrobotics.com/cn/machinevision/service/download?module=0)
- [pylon SDK 文档](https://www.baslerweb.com/en/sales-support/downloads/software-downloads/pylon-6-2-0-camera-software-suite-linux-x86-64-bit/)
- [ctypes 官方文档](https://docs.python.org/3/library/ctypes.html)

---

## 🎯 总结

✅ **Phase 2 框架完成**：
- 建立了清晰的驱动抽象层
- 实现了海康威视驱动框架
- 支持自动检测和加载
- 保留了模拟相机回退机制

⏳ **待完成**：
- 集成真实 SDK 调用
- 补充巴斯勒驱动
- 完善错误处理和性能优化

**预计完成时间**：取决于 SDK 获取和硬件测试进度

---

**更新日期**: 2026-05-04  
**作者**: AI Assistant
