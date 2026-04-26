"""
AI 节点性能基准测试

测试所有 YOLO 节点的性能指标：
- 推理速度（ms/帧）
- 内存占用（MB）
- GPU 显存使用（MB，如果可用）
- 缓存命中率

使用方法：
    python tests/benchmark_ai_nodes.py
"""

import sys
import os
import time
import numpy as np
from pathlib import Path

# 添加项目路径
project_root = os.path.join(os.path.dirname(__file__), '..', 'src', 'python')
sys.path.insert(0, project_root)


def test_inference_performance():
    """测试推理节点性能"""
    print("=" * 80)
    print("YOLO 推理节点性能基准测试")
    print("=" * 80)
    
    try:
        from user_plugins.yolo_vision.nodes.inference import (
            YOLODetectNode,
            YOLOClassifyNode,
            YOLOSegmentNode,
            YOLOPoseNode
        )
        
        print("\n✅ 所有推理节点导入成功\n")
        
        # 创建测试图像（640x640 RGB）
        test_image = np.random.randint(0, 255, (640, 640, 3), dtype=np.uint8)
        
        # 测试每个节点
        nodes_to_test = [
            ("YOLO 目标检测", YOLODetectNode),
            ("YOLO 图像分类", YOLOClassifyNode),
            ("YOLO 实例分割", YOLOSegmentNode),
            ("YOLO 姿态估计", YOLOPoseNode),
        ]
        
        results = []
        
        for node_name, node_class in nodes_to_test:
            print(f"\n{'─' * 80}")
            print(f"测试: {node_name}")
            print(f"{'─' * 80}")
            
            try:
                # 创建节点实例
                node = node_class()
                
                # 记录初始内存
                import psutil
                process = psutil.Process(os.getpid())
                memory_before = process.memory_info().rss / (1024 * 1024)
                
                # 预热运行（第一次加载模型较慢）
                print("  🔄 预热运行（加载模型）...")
                start_time = time.time()
                result = node.process({'输入图像': test_image})
                warmup_time = time.time() - start_time
                
                if result is None:
                    print(f"  ⚠️ 跳过测试（依赖未安装或硬件不满足）")
                    continue
                
                memory_after = process.memory_info().rss / (1024 * 1024)
                memory_used = memory_after - memory_before
                
                print(f"  ✅ 预热完成 (耗时: {warmup_time:.2f}s)")
                print(f"  📊 内存使用: {memory_used:.1f} MB")
                
                # 正式测试（10次取平均）
                print("  🚀 执行性能测试（10次迭代）...")
                times = []
                for i in range(10):
                    start_time = time.time()
                    result = node.process({'输入图像': test_image})
                    elapsed = (time.time() - start_time) * 1000  # 转换为毫秒
                    times.append(elapsed)
                
                avg_time = np.mean(times)
                min_time = np.min(times)
                max_time = np.max(times)
                std_time = np.std(times)
                
                # 获取性能报告
                perf_report = node.get_performance_report()
                cache_stats = node.get_cache_stats()
                
                print(f"\n  📈 性能指标:")
                print(f"     平均延迟: {avg_time:.2f} ms")
                print(f"     最小延迟: {min_time:.2f} ms")
                print(f"     最大延迟: {max_time:.2f} ms")
                print(f"     标准差:   {std_time:.2f} ms")
                print(f"     FPS:      {1000/avg_time:.1f}")
                
                if cache_stats:
                    print(f"\n  💾 缓存统计:")
                    print(f"     总条目数: {cache_stats['total_entries']}")
                    print(f"     有效条目: {cache_stats['valid_entries']}")
                
                # 保存结果
                results.append({
                    'node_name': node_name,
                    'avg_latency_ms': avg_time,
                    'min_latency_ms': min_time,
                    'max_latency_ms': max_time,
                    'fps': 1000 / avg_time,
                    'memory_mb': memory_used
                })
                
            except Exception as e:
                print(f"  ❌ 测试失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 汇总报告
        print(f"\n\n{'=' * 80}")
        print("性能测试汇总报告")
        print(f"{'=' * 80}\n")
        
        if results:
            print(f"{'节点名称':<20} {'平均延迟(ms)':<15} {'FPS':<10} {'内存(MB)':<10}")
            print(f"{'─' * 20} {'─' * 15} {'─' * 10} {'─' * 10}")
            
            for r in results:
                print(f"{r['node_name']:<20} {r['avg_latency_ms']:<15.2f} {r['fps']:<10.1f} {r['memory_mb']:<10.1f}")
            
            print(f"\n✅ 测试完成！共测试 {len(results)} 个节点")
        else:
            print("⚠️ 没有节点通过测试（可能缺少依赖）")
        
        return len(results) > 0
        
    except ImportError as e:
        print(f"\n❌ 导入失败: {e}")
        print("💡 请确保已安装 ultralytics: pip install ultralytics")
        return False


if __name__ == '__main__':
    success = test_inference_performance()
    sys.exit(0 if success else 1)
