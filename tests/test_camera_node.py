"""
相机节点功能测试脚本

测试内容：
1. CameraManager 配置加载
2. 模拟相机图像生成
3. 相机实例管理
4. 多相机并发
"""

import sys
import os

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.dirname(__file__))
src_path = os.path.join(project_root, 'src', 'python')
sys.path.insert(0, src_path)

from plugin_packages.builtin.io_camera.camera_manager import CameraManager, SimulatedCamera


def test_config_loading():
    """测试配置文件加载"""
    print("=" * 60)
    print("测试1: 配置文件加载")
    print("=" * 60)
    
    manager = CameraManager.get_instance()
    
    print(f"✓ Seat数量: {manager.get_seat_count()}")
    print(f"✓ Dictionary型号数量: {len(manager.dictionary)}")
    
    # 测试获取Seat信息
    for i in range(min(3, manager.get_seat_count())):
        seat_info = manager.get_seat_info(i)
        if seat_info:
            print(f"  Seat {i}: SN={seat_info.get('sn')}, Model={seat_info.get('classname')}")
    
    print("✅ 配置加载测试通过\n")


def test_simulated_camera():
    """测试模拟相机"""
    print("=" * 60)
    print("测试2: 模拟相机图像生成")
    print("=" * 60)
    
    # 创建模拟相机配置
    config = {
        'resolution': {'width': '640', 'height': '480'},
        'framerate': '30 fps',
        'simulation': {
            'mode': 'pattern',
            'frame_interval_ms': 33
        }
    }
    
    camera = SimulatedCamera(config)
    
    # 抓取几帧测试
    for i in range(3):
        frame = camera.grab_frame()
        print(f"  帧 {i+1}: 形状={frame.shape}, 数据类型={frame.dtype}")
        
        # 验证图像有效性（NumPy形状是(height, width, channels)）
        assert frame.shape == (480, 640, 3), f"图像形状错误: {frame.shape}"
        assert frame.dtype == 'uint8', f"数据类型错误: {frame.dtype}"
        assert frame.min() >= 0 and frame.max() <= 255, "像素值超出范围"
    
    print("✅ 模拟相机测试通过\n")


def test_camera_initialization():
    """测试相机初始化"""
    print("=" * 60)
    print("测试3: 相机初始化（使用模拟相机）")
    print("=" * 60)
    
    manager = CameraManager.get_instance()
    
    # 找到模拟相机Seat
    sim_seat_index = None
    for i in range(manager.get_seat_count()):
        seat_info = manager.get_seat_info(i)
        if seat_info and seat_info.get('sn', '').startswith('SIMULATED'):
            sim_seat_index = i
            break
    
    if sim_seat_index is None:
        print("⚠️ 未找到模拟相机Seat，跳过此测试")
        return
    
    print(f"使用 Seat {sim_seat_index} 进行测试")
    
    # 初始化相机
    camera_id = manager.initialize_camera(sim_seat_index)
    print(f"✓ 相机ID: {camera_id}")
    
    # 获取相机实例
    camera = manager.get_camera(camera_id)
    assert camera is not None, "相机实例为空"
    print(f"✓ 相机类型: {type(camera).__name__}")
    
    # 测试采集
    frame = camera.grab_frame()
    assert frame is not None, "采集失败"
    print(f"✓ 采集成功: 形状={frame.shape}")
    
    # 释放相机
    manager.release_camera(camera_id)
    print("✓ 相机已释放")
    
    print("✅ 相机初始化测试通过\n")


def test_multiple_cameras():
    """测试多相机并发"""
    print("=" * 60)
    print("测试4: 多相机并发")
    print("=" * 60)
    
    manager = CameraManager.get_instance()
    
    # 初始化前2个Seat
    camera_ids = []
    for i in range(min(2, manager.get_seat_count())):
        camera_id = manager.initialize_camera(i)
        if camera_id:
            camera_ids.append(camera_id)
            print(f"✓ 初始化相机 {i}: {camera_id}")
    
    # 同时从多个相机采集
    for idx, camera_id in enumerate(camera_ids):
        camera = manager.get_camera(camera_id)
        if camera:
            frame = camera.grab_frame()
            print(f"  相机 {idx} ({camera_id}): 形状={frame.shape if frame is not None else 'None'}")
    
    # 释放所有相机
    manager.release_all()
    print("✓ 所有相机已释放")
    
    print("✅ 多相机并发测试通过\n")


def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("工业相机节点功能测试")
    print("=" * 60 + "\n")
    
    try:
        test_config_loading()
        test_simulated_camera()
        test_camera_initialization()
        test_multiple_cameras()
        
        print("=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
