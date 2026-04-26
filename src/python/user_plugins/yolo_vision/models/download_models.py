"""
YOLO 预训练模型下载工具

用法：
    python download_models.py                    # 下载默认模型（yolov8n）
    python download_models.py --all              # 下载所有检测模型
    python download_models.py --model yolov8s    # 下载指定模型
    python download_models.py --list             # 列出可用模型
"""

import os
import sys
import argparse
from pathlib import Path

# 添加项目路径
project_root = os.path.join(os.path.dirname(__file__), '..', '..', '..')
sys.path.insert(0, project_root)

from user_plugins.yolo_vision.models.model_registry import MODEL_REGISTRY, get_model_info, list_models


def download_model(model_name: str, output_dir: str = None) -> str:
    """
    下载单个模型
    
    Args:
        model_name: 模型名称
        output_dir: 输出目录，默认为当前目录的 models/
        
    Returns:
        str: 下载的模型文件路径
    """
    try:
        import urllib.request
    except ImportError:
        print("❌ 缺少依赖：urllib")
        return None
    
    # 获取模型信息
    model_info = get_model_info(model_name)
    if not model_info:
        print(f"❌ 未知模型: {model_name}")
        print(f"💡 可用模型: {', '.join(list_models())}")
        return None
    
    # 设置输出目录
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(__file__), 'models')
    
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, f'{model_name}.pt')
    
    # 检查是否已存在
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / (1024 * 1024)  # MB
        print(f"✅ 模型已存在: {output_path} ({file_size:.1f}MB)")
        return output_path
    
    # 下载模型
    url = model_info['url']
    print(f"🔄 下载模型: {model_info['name']}")
    print(f"   URL: {url}")
    print(f"   大小: {model_info['size_mb']}MB")
    print(f"   保存至: {output_path}")
    
    try:
        def report_progress(block_num, block_size, total_size):
            downloaded = block_num * block_size
            percent = min(100, downloaded * 100 / total_size)
            mb_downloaded = downloaded / (1024 * 1024)
            mb_total = total_size / (1024 * 1024)
            print(f"\r   进度: {percent:.1f}% ({mb_downloaded:.1f}/{mb_total:.1f}MB)", end='')
        
        urllib.request.urlretrieve(url, output_path, reporthook=report_progress)
        print()  # 换行
        
        # 验证文件大小
        actual_size = os.path.getsize(output_path) / (1024 * 1024)
        print(f"✅ 下载完成: {output_path} ({actual_size:.1f}MB)")
        
        return output_path
        
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        if os.path.exists(output_path):
            os.remove(output_path)  # 清理不完整的文件
        return None


def download_all_models(model_type: str = 'detection'):
    """
    下载指定类型的所有模型
    
    Args:
        model_type: 模型类型
    """
    models = list_models(model_type)
    print(f"📦 准备下载 {len(models)} 个 {model_type} 模型\n")
    
    success_count = 0
    for model_name in models:
        print(f"\n[{success_count + 1}/{len(models)}] ", end='')
        result = download_model(model_name)
        if result:
            success_count += 1
    
    print(f"\n✅ 下载完成: {success_count}/{len(models)} 个模型成功")


def main():
    parser = argparse.ArgumentParser(description='YOLO 预训练模型下载工具')
    parser.add_argument('--model', type=str, help='指定模型名称')
    parser.add_argument('--all', action='store_true', help='下载所有检测模型')
    parser.add_argument('--list', action='store_true', help='列出可用模型')
    parser.add_argument('--type', type=str, default='detection',
                       choices=['detection', 'classification', 'segmentation', 'pose'],
                       help='模型类型（与 --all 配合使用）')
    parser.add_argument('--output', type=str, help='输出目录')
    
    args = parser.parse_args()
    
    if args.list:
        print("📋 可用模型列表:\n")
        for model_name in list_models():
            info = get_model_info(model_name)
            print(f"  {model_name:20s} - {info['name']:30s} ({info['size_mb']}MB)")
            print(f"{'':23s}类型: {info['type']:15s} | {info['description']}")
            print()
        return
    
    if args.all:
        download_all_models(args.type)
        return
    
    if args.model:
        download_model(args.model, args.output)
        return
    
    # 默认下载 yolov8n
    print("💡 未指定模型，下载默认模型 yolov8n\n")
    download_model('yolov8n', args.output)


if __name__ == '__main__':
    main()
