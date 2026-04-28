"""
Shape Context 性能对比测试脚本

测试缓存机制优化前后的性能差异
"""

import sys
import time
import numpy as np
import cv2


def generate_test_contours(num_contours=10, points_per_contour=200):
    """生成测试用的轮廓数据"""
    contours = []
    
    for i in range(num_contours):
        # 生成随机多边形轮廓
        angles = np.linspace(0, 2 * np.pi, points_per_contour, endpoint=False)
        radius = 50 + np.random.rand() * 30
        
        x = 100 + i * 80 + radius * np.cos(angles)
        y = 100 + radius * np.sin(angles)
        
        contour = np.column_stack([x, y]).astype(np.int32).reshape(-1, 1, 2)
        contours.append(contour)
    
    return contours


def test_without_cache(contours, n_iterations=5):
    """测试无缓存时的性能"""
    print("\n" + "="*60)
    print("测试1: 无缓存机制（基准测试）")
    print("="*60)
    
    total_time = 0
    
    for iteration in range(n_iterations):
        start_time = time.time()
        
        # 模拟Shape Context计算（简化版，仅采样）
        for contour in contours:
            n_points = 100
            indices = np.linspace(0, len(contour) - 1, n_points, dtype=int)
            sampled_points = contour[indices].reshape(-1, 2).astype(np.float32)
            
            # 模拟描述符构建
            descriptor = {
                'n_points': len(sampled_points),
                'sampled_points': sampled_points.tolist()
            }
        
        elapsed = time.time() - start_time
        total_time += elapsed
        print(f"  第{iteration + 1}次迭代: {elapsed:.4f}秒")
    
    avg_time = total_time / n_iterations
    print(f"\n  平均耗时: {avg_time:.4f}秒/次")
    print(f"  总耗时: {total_time:.4f}秒 ({n_iterations}次迭代)")
    
    return avg_time


def test_with_cache(contours, n_iterations=5):
    """测试有缓存时的性能"""
    print("\n" + "="*60)
    print("测试2: 有缓存机制（LRU策略）")
    print("="*60)
    
    cache = {}
    cache_hits = 0
    cache_misses = 0
    total_time = 0
    
    for iteration in range(n_iterations):
        start_time = time.time()
        
        for contour in contours:
            # 生成缓存键值
            contour_key = hash(contour.tobytes())
            param_key = "100_4_12_0.1_arc_length"
            cache_key = f"{contour_key}_{param_key}"
            
            # 检查缓存
            if cache_key in cache:
                # 缓存命中
                descriptor = cache[cache_key]
                cache_hits += 1
            else:
                # 缓存未命中，计算并缓存
                n_points = 100
                indices = np.linspace(0, len(contour) - 1, n_points, dtype=int)
                sampled_points = contour[indices].reshape(-1, 2).astype(np.float32)
                
                descriptor = {
                    'n_points': len(sampled_points),
                    'sampled_points': sampled_points.tolist()
                }
                
                # LRU淘汰
                if len(cache) >= 100:
                    oldest_key = next(iter(cache))
                    del cache[oldest_key]
                
                cache[cache_key] = descriptor
                cache_misses += 1
        
        elapsed = time.time() - start_time
        total_time += elapsed
        print(f"  第{iteration + 1}次迭代: {elapsed:.4f}秒 (命中:{cache_hits}, 未命中:{cache_misses})")
    
    avg_time = total_time / n_iterations
    hit_rate = cache_hits / (cache_hits + cache_misses) * 100 if (cache_hits + cache_misses) > 0 else 0
    
    print(f"\n  平均耗时: {avg_time:.4f}秒/次")
    print(f"  总耗时: {total_time:.4f}秒 ({n_iterations}次迭代)")
    print(f"  缓存命中率: {hit_rate:.1f}% ({cache_hits}/{cache_hits + cache_misses})")
    
    return avg_time, hit_rate


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("Shape Context 性能对比测试")
    print("="*60)
    
    # 生成测试数据
    num_contours = 10
    print(f"\n生成 {num_contours} 个测试轮廓...")
    contours = generate_test_contours(num_contours=num_contours, points_per_contour=200)
    print(f"✅ 测试数据准备完成")
    
    # 测试1: 无缓存
    avg_time_no_cache = test_without_cache(contours, n_iterations=5)
    
    # 测试2: 有缓存
    avg_time_with_cache, hit_rate = test_with_cache(contours, n_iterations=5)
    
    # 性能对比
    print("\n" + "="*60)
    print("性能对比结果")
    print("="*60)
    
    speedup = avg_time_no_cache / avg_time_with_cache if avg_time_with_cache > 0 else 0
    improvement = ((avg_time_no_cache - avg_time_with_cache) / avg_time_no_cache) * 100
    
    print(f"\n  无缓存平均耗时: {avg_time_no_cache:.4f}秒")
    print(f"  有缓存平均耗时: {avg_time_with_cache:.4f}秒")
    print(f"  加速比: {speedup:.2f}x")
    print(f"  性能提升: {improvement:.1f}%")
    print(f"  缓存命中率: {hit_rate:.1f}%")
    
    print("\n" + "="*60)
    print("结论")
    print("="*60)
    
    if speedup > 2:
        print(f"✅ 缓存机制效果显著！性能提升 {improvement:.1f}%")
        print("   推荐在生产环境中启用缓存功能")
    elif speedup > 1.2:
        print(f"⚠️ 缓存机制有一定效果，性能提升 {improvement:.1f}%")
        print("   建议在重复模板场景中使用")
    else:
        print(f"❌ 缓存机制效果不明显，性能提升 {improvement:.1f}%")
        print("   可能原因：测试数据量过小或缓存开销过大")
    
    print("\n" + "="*60)


if __name__ == '__main__':
    main()
