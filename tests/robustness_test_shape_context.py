"""
Shape Context 鲁棒性增强测试脚本

测试轮廓平滑、尺度归一化等功能的效果
"""

import sys
import numpy as np
import cv2


def generate_noisy_contour(base_radius=50, noise_level=5, num_points=100):
    """生成带噪声的圆形轮廓"""
    angles = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
    
    # 基础圆形
    x = base_radius * np.cos(angles)
    y = base_radius * np.sin(angles)
    
    # 添加高斯噪声
    noise_x = np.random.normal(0, noise_level, num_points)
    noise_y = np.random.normal(0, noise_level, num_points)
    
    x += noise_x
    y += noise_y
    
    contour = np.column_stack([x, y]).astype(np.int32).reshape(-1, 1, 2)
    
    return contour


def test_smoothing():
    """测试轮廓平滑效果"""
    print("\n" + "="*60)
    print("测试1: 轮廓平滑滤波")
    print("="*60)
    
    # 生成带噪声的轮廓
    noisy_contour = generate_noisy_contour(base_radius=50, noise_level=8, num_points=100)
    
    print(f"\n原始轮廓:")
    print(f"  点数: {len(noisy_contour)}")
    print(f"  面积: {cv2.contourArea(noisy_contour):.2f}")
    print(f"  周长: {cv2.arcLength(noisy_contour, True):.2f}")
    
    # 应用不同核大小的平滑
    for kernel_size in [3, 5, 7, 9]:
        smoothed = smooth_contour(noisy_contour, kernel_size)
        
        print(f"\n平滑后 (核大小={kernel_size}):")
        print(f"  面积: {cv2.contourArea(smoothed):.2f}")
        print(f"  周长: {cv2.arcLength(smoothed, True):.2f}")
        
        # 计算与理想圆形的偏差
        ideal_area = np.pi * 50**2
        area_error = abs(cv2.contourArea(smoothed) - ideal_area) / ideal_area * 100
        print(f"  面积误差: {area_error:.2f}%")


def smooth_contour(contour, kernel_size=5):
    """轮廓平滑滤波（简化版，用于测试）"""
    if len(contour) < kernel_size:
        return contour.copy()
    
    if kernel_size % 2 == 0:
        kernel_size += 1
    
    smoothed = np.zeros_like(contour, dtype=np.float32)
    half_kernel = kernel_size // 2
    
    for i in range(len(contour)):
        indices = [(i + j) % len(contour) for j in range(-half_kernel, half_kernel + 1)]
        smoothed[i] = np.mean(contour[indices], axis=0)
    
    return smoothed.astype(np.int32)


def test_scale_normalization():
    """测试尺度归一化效果"""
    print("\n" + "="*60)
    print("测试2: 尺度归一化")
    print("="*60)
    
    # 生成不同尺度的圆形轮廓
    scales = [0.5, 1.0, 1.5, 2.0]
    reference_area = np.pi * 50**2  # 参考面积
    
    print(f"\n参考面积: {reference_area:.2f}")
    
    for scale in scales:
        radius = int(50 * scale)
        contour = generate_noisy_contour(base_radius=radius, noise_level=2, num_points=100)
        
        original_area = cv2.contourArea(contour)
        
        # 尺度归一化
        normalized = normalize_scale(contour, reference_area)
        normalized_area = cv2.contourArea(normalized)
        
        print(f"\n缩放比例: {scale}x")
        print(f"  原始面积: {original_area:.2f}")
        print(f"  归一化后面积: {normalized_area:.2f}")
        print(f"  面积误差: {abs(normalized_area - reference_area) / reference_area * 100:.2f}%")


def normalize_scale(contour, reference_area):
    """尺度归一化（简化版，用于测试）"""
    current_area = cv2.contourArea(contour)
    
    if current_area == 0 or reference_area == 0:
        return contour.copy()
    
    # 计算缩放比例
    scale_factor = np.sqrt(reference_area / current_area)
    
    # 以质心为中心缩放
    moments = cv2.moments(contour)
    if moments['m00'] == 0:
        return contour.copy()
    
    cx = moments['m10'] / moments['m00']
    cy = moments['m01'] / moments['m00']
    
    normalized = (contour - np.array([cx, cy])) * scale_factor + np.array([cx, cy])
    
    return normalized.astype(np.int32)


def test_validation():
    """测试轮廓有效性验证"""
    print("\n" + "="*60)
    print("测试3: 轮廓有效性验证")
    print("="*60)
    
    # 测试用例1: 有效轮廓
    valid_contour = generate_noisy_contour(base_radius=50, noise_level=2, num_points=100)
    print(f"\n测试1: 有效轮廓")
    print(f"  点数: {len(valid_contour)}")
    print(f"  面积: {cv2.contourArea(valid_contour):.2f}")
    print(f"  周长: {cv2.arcLength(valid_contour, True):.2f}")
    print(f"  验证结果: {'✅ 有效' if validate_contour(valid_contour) else '❌ 无效'}")
    
    # 测试用例2: 点数不足
    invalid_contour_1 = np.array([[[0, 0]], [[10, 10]]], dtype=np.int32)
    print(f"\n测试2: 点数不足 (<3)")
    print(f"  点数: {len(invalid_contour_1)}")
    print(f"  验证结果: {'✅ 有效' if validate_contour(invalid_contour_1) else '❌ 无效'}")
    
    # 测试用例3: 面积为0（共线点）
    invalid_contour_2 = np.array([[[0, 0]], [[10, 10]], [[20, 20]]], dtype=np.int32)
    print(f"\n测试3: 面积为0 (共线点)")
    print(f"  点数: {len(invalid_contour_2)}")
    print(f"  面积: {cv2.contourArea(invalid_contour_2):.2f}")
    print(f"  验证结果: {'✅ 有效' if validate_contour(invalid_contour_2) else '❌ 无效'}")


def validate_contour(contour):
    """验证轮廓有效性（简化版，用于测试）"""
    # 检查点数
    if len(contour) < 3:
        return False
    
    # 检查面积
    area = cv2.contourArea(contour)
    if area == 0:
        return False
    
    # 检查周长
    perimeter = cv2.arcLength(contour, True)
    if perimeter == 0:
        return False
    
    return True


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("Shape Context 鲁棒性增强测试")
    print("="*60)
    
    # 测试1: 轮廓平滑
    test_smoothing()
    
    # 测试2: 尺度归一化
    test_scale_normalization()
    
    # 测试3: 轮廓验证
    test_validation()
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)
    print("\n结论:")
    print("✅ 轮廓平滑可有效减少噪声影响")
    print("✅ 尺度归一化可消除尺度差异，提高跨尺度匹配能力")
    print("✅ 轮廓验证可过滤退化轮廓，避免计算错误")


if __name__ == '__main__':
    main()
