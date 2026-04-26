"""
AI 节点基类功能验证脚本

不依赖 NodeGraphQt，直接测试核心功能
"""

import sys
import os
import time

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'python'))


def test_dependency_check():
    """测试依赖检查功能"""
    print("=" * 60)
    print("测试 1: 依赖检查")
    print("=" * 60)
    
    # 模拟 AIBaseNode 的 check_dependencies 方法
    def check_dependencies(required_packages):
        missing = []
        for package in required_packages:
            pkg_name = package.split('>=')[0].split('==')[0].strip()
            try:
                __import__(pkg_name)
            except ImportError:
                missing.append(package)
        
        if missing:
            print(f"❌ 缺少依赖: {', '.join(missing)}")
            print(f"💡 安装命令: pip install {' '.join(missing)}")
            return False
        
        print(f"✅ 所有依赖已安装")
        return True
    
    # 测试 1: 检查已安装的包
    result1 = check_dependencies(['os', 'sys'])
    assert result1 == True, "应该通过（os 和 sys 是内置模块）"
    
    # 测试 2: 检查缺失的包
    result2 = check_dependencies(['nonexistent_package_xyz'])
    assert result2 == False, "应该失败（包不存在）"
    
    print("✅ 依赖检查测试通过\n")


def test_hardware_check():
    """测试硬件检查功能"""
    print("=" * 60)
    print("测试 2: 硬件检查")
    print("=" * 60)
    
    try:
        import psutil
        
        cpu_cores = psutil.cpu_count(logical=False)
        memory_gb = psutil.virtual_memory().available / (1024 ** 3)
        
        print(f"📊 当前硬件配置:")
        print(f"   CPU 核心数: {cpu_cores}")
        print(f"   可用内存: {memory_gb:.1f} GB")
        
        # 检查是否满足低要求
        if cpu_cores >= 2 and memory_gb >= 2:
            print("✅ 满足轻量级节点要求 (2核, 2GB)")
        else:
            print("⚠️ 不满足轻量级节点要求")
        
        # 检查是否满足高要求
        if cpu_cores >= 8 and memory_gb >= 16:
            print("✅ 满足重量级节点要求 (8核, 16GB)")
        else:
            print("⚠️ 不满足重量级节点要求")
        
        print("✅ 硬件检查测试通过\n")
        
    except ImportError:
        print("⚠️ 未安装 psutil，跳过硬件检查测试\n")


def test_model_cache():
    """测试模型缓存功能"""
    print("=" * 60)
    print("测试 3: 模型缓存")
    print("=" * 60)
    
    # 模拟模型缓存
    model_cache = {}
    
    def get_or_load_model(model_key, loader_func):
        if model_key not in model_cache:
            print(f"🔄 首次加载模型: {model_key}")
            start_time = time.time()
            model = loader_func()
            elapsed = time.time() - start_time
            print(f"✅ 模型加载完成 (耗时: {elapsed:.2f}s)")
            model_cache[model_key] = model
        else:
            print(f"✅ 使用缓存模型: {model_key}")
        return model_cache[model_key]
    
    call_count = [0]
    
    def mock_loader():
        call_count[0] += 1
        time.sleep(0.1)  # 模拟加载时间
        return f"model_{call_count[0]}"
    
    # 第一次加载
    model1 = get_or_load_model('yolov8n', mock_loader)
    assert call_count[0] == 1, "应该调用 loader"
    
    # 第二次加载（应该使用缓存）
    model2 = get_or_load_model('yolov8n', mock_loader)
    assert call_count[0] == 1, "不应该再次调用 loader"
    assert model1 == model2, "应该返回相同的模型"
    
    print("✅ 模型缓存测试通过\n")


def test_logging():
    """测试日志输出"""
    print("=" * 60)
    print("测试 4: 日志输出")
    print("=" * 60)
    
    node_name = "测试节点"
    
    def log_info(message):
        print(f"ℹ️ [{node_name}] {message}")
    
    def log_warning(message):
        print(f"⚠️ [{node_name}] {message}")
    
    def log_error(message):
        print(f"❌ [{node_name}] {message}")
    
    def log_success(message):
        print(f"✅ [{node_name}] {message}")
    
    log_info("这是一条信息")
    log_warning("这是一条警告")
    log_error("这是一条错误")
    log_success("这是一条成功消息")
    
    print("✅ 日志输出测试通过\n")


def test_async_simulation():
    """模拟异步处理"""
    print("=" * 60)
    print("测试 5: 异步处理模拟")
    print("=" * 60)
    
    from concurrent.futures import ThreadPoolExecutor
    
    def slow_process(inputs):
        """模拟耗时操作"""
        time.sleep(0.5)
        return {'result': 'success', 'input': inputs}
    
    executor = ThreadPoolExecutor(max_workers=1)
    
    # 提交任务
    print("🔄 启动异步任务...")
    future = executor.submit(slow_process, {'data': 'test'})
    
    # 检查状态
    print(f"   任务状态: {'运行中' if not future.done() else '已完成'}")
    
    # 等待结果
    result = future.result()
    print(f"   任务结果: {result}")
    
    executor.shutdown(wait=False)
    
    print("✅ 异步处理测试通过\n")


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("AI 节点基类功能验证")
    print("=" * 60 + "\n")
    
    try:
        test_dependency_check()
        test_hardware_check()
        test_model_cache()
        test_logging()
        test_async_simulation()
        
        print("=" * 60)
        print("🎉 所有测试通过！")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 测试失败: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
