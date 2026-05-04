# 工业相机采集节点使用说明

## 概述

`CameraCaptureNode` 是一个用于从工业相机采集图像的节点，支持多相机同时工作、连续采集和实时预览。

## 功能特性

- ✅ **多相机支持**：通过 Seat 索引选择不同相机，可同时运行多个相机节点
- ✅ **双输出模式**：单帧图像（触发式）+ 连续图像流（后台采集）
- ✅ **实时预览**：双击节点打开预览窗口，显示实时画面
- ✅ **参数配置**：曝光时间、增益、白平衡、ROI 等
- ✅ **模拟相机**：无硬件时使用模拟相机测试工作流
- ✅ **快速控制**：预览窗口提供初始化、打开、开始/停止采集等按钮

## 使用方法

### 1. 添加节点到画布

从节点库 **"图像相机"** 标签页拖拽 **"工业相机采集"** 节点到画布。

### 2. 配置相机参数

在右侧属性面板中配置：

**基本配置标签页**：
- **Seat索引**：选择相机（0, 1, 2, 3...），对应 `plugin_camera.json` 中的 Seats 配置
- **相机序列号**：自动填充（只读）
- **镜头倍率**：默认 1.0，用于计算实际尺寸
- **采集模式**：连续采集 / 软件触发 / 外部触发

**图像参数标签页**：
- **曝光时间(μs)**：调节范围 100-100000，默认 10000
- **增益**：调节范围 0-100，默认 0
- **白平衡模式**：Auto / Manual / Once

### 3. 初始化相机

**方式1：通过预览窗口**
1. 双击节点打开预览窗口
2. 点击 "🔧 初始化" 按钮
3. 等待初始化完成提示

**方式2：通过代码**
```python
node.initialize_camera()
```

### 4. 打开相机

**方式1：通过预览窗口**
1. 点击 "📡 打开" 按钮
2. 等待打开成功提示

**方式2：通过代码**
```python
node.open_camera()
```

### 5. 开始采集

**方式1：通过预览窗口**
1. 点击 "▶️ 开始采集" 按钮
2. 预览窗口开始显示实时画面
3. 状态栏显示 FPS 和帧数

**方式2：通过代码**
```python
node.start_acquisition()
```

### 6. 连接下游节点

将节点的输出端口连接到其他节点：

- **单帧图像**：适合触发式处理（如质量检测）
- **连续图像流**：适合实时监控（如视频分析）

示例工作流：
```
[工业相机采集] → [Canny边缘检测] → [图像显示]
```

### 7. 停止采集

**方式1：通过预览窗口**
- 点击 "⏸️ 停止" 按钮

**方式2：通过代码**
```python
node.stop_acquisition()
```

### 8. 关闭相机

**方式1：通过预览窗口**
- 关闭预览窗口时自动停止采集
- 删除节点时自动关闭相机

**方式2：通过代码**
```python
node.close_camera()
```

## 配置文件

### plugin_camera.json

相机配置位于 `src/python/plugin_packages/builtin/io_camera/plugin_camera.json`

**Dictionary 段**：定义相机型号的技术参数
```json
{
  "CCameraMVC1000mf": {
    "sensor_type": "CMOS",
    "resolution": {"width": "1280", "height": "1024"},
    "exposure": {"min": "5", "max": "37000", "default": "10000"},
    "framerate": "27 fps",
    "image_params": {...},
    "trigger_params": {...},
    "roi_params": {...}
  }
}
```

**Seats 段**：定义运行时相机实例
```json
{
  "classname": "CCameraMVC1000mf",
  "mode": "continue",
  "Magnification": "1.0",
  "sn": "25081931"
}
```

**模拟相机配置**：
```json
{
  "classname": "CCameraMVC1000mf",
  "sn": "SIMULATED_001",
  "custom_params": {
    "simulation": {
      "enabled": true,
      "mode": "pattern",
      "frame_interval_ms": 33
    }
  }
}
```

## 预览窗口功能

### 顶部工具栏
- **🔧 初始化**：加载DLL驱动，枚举设备
- **📡 打开**：应用参数，启动相机流
- **▶️ 开始采集**：启动后台采集线程
- **⏸️ 停止**：暂停采集但保持连接
- **💾 保存当前帧**：保存当前显示的图像到文件
- **🔄 刷新**：手动刷新预览画面

### 图像操作
- **滚轮缩放**：Ctrl + 滚轮上下滚动
- **拖拽平移**：按住空格键 + 鼠标拖拽
- **自动滚动条**：图像超出视口时自动显示

### 底部状态栏
- **连接状态**：⚪未连接 / 🟡已连接 / 🟢采集中
- **FPS**：实时帧率统计
- **帧数**：累计采集帧数

## 模拟相机

当没有真实相机硬件时，可以使用模拟相机测试工作流。

**启用方式**：
1. 在 `plugin_camera.json` 的 Seats 段添加模拟相机配置（SN 以 "SIMULATED_" 开头）
2. 在节点属性中选择对应的 Seat 索引
3. 初始化和打开后，模拟相机会自动生成测试图案

**模拟模式**：
- **pattern**：彩色条纹测试图（默认）
- **noise**：随机噪声图像
- **gradient**：灰度渐变图像

## 常见问题

### Q1: 双击节点没有反应？
**A**: 确保节点已正确注册。检查控制台是否有加载错误。重启应用使新节点生效。

### Q2: 预览窗口显示黑色画面？
**A**: 
1. 确认相机已初始化并打开
2. 点击 "▶️ 开始采集" 按钮
3. 检查 Seat 索引是否正确

### Q3: 如何同时使用多个相机？
**A**: 
1. 在 `plugin_camera.json` 的 Seats 段配置多个相机（不同 SN）
2. 拖拽多个 "工业相机采集" 节点到画布
3. 每个节点选择不同的 Seat 索引
4. 分别初始化和打开

### Q4: 采集帧率低怎么办？
**A**: 
1. 降低分辨率（使用 ROI）
2. 减少曝光时间
3. 检查 USB/GigE 连接带宽
4. 关闭不必要的后台程序

### Q5: 如何保存采集的图像？
**A**: 
1. 在预览窗口点击 "💾 保存当前帧"
2. 或连接 "保存图像" 节点到输出端口
3. 或在代码中调用 `cv2.imwrite()`

## 技术架构

### 后台采集线程
```python
 Acquisition Thread
        ↓
  while is_acquiring:
    frame = camera.grab_frame()
    _latest_frame = frame.copy()  # 深拷贝
    time.sleep(1/framerate)
```

### 数据流
```
 Camera Hardware/Simulator
        ↓
  _latest_frame (缓存)
        ↓
   process() 方法
        ↓
  输出端口 (单帧/连续)
        ↓
   下游节点
```

### 线程安全
- 使用 `threading.Lock` 保护 `_latest_frame`
- 深拷贝避免竞争条件
- 后台线程 daemon=True，主程序退出时自动终止

## 性能优化

- **帧率控制**：通过 `time.sleep()` 精确控制采集频率
- **内存管理**：环形缓冲区，自动清理旧帧
- **延迟最小化**：直接返回最新帧，无额外拷贝

## 扩展开发

### 集成真实相机SDK

修改 `RealCamera` 类，替换占位实现：

```python
def initialize(self):
    # 加载DLL
    self.dll = ctypes.CDLL(dll_path)
    # 枚举设备
    device_list = self.dll.enumerate_devices()
    # 打开指定SN的设备
    self.handle = self.dll.open_device(self.serial_number)
    return True

def grab_frame(self):
    # 分配缓冲区
    buffer = np.zeros((height, width, 3), dtype=np.uint8)
    # 调用DLL采集
    self.dll.grab_frame(self.handle, buffer.ctypes.data)
    return buffer
```

### 添加新的模拟模式

在 `SimulatedCamera` 类中添加新方法：

```python
def _generate_custom_pattern(self):
    # 自定义测试图案生成逻辑
    pass
```

## 更新日志

### v1.0.0 (2026-05-04)
- ✅ 初始版本发布
- ✅ 支持多相机管理
- ✅ 实时预览窗口
- ✅ 模拟相机支持
- ✅ 后台采集线程

## 许可证

本项目遵循 MIT 许可证。

## 联系方式

如有问题或建议，请联系开发团队。
