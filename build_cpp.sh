#!/bin/bash

echo "========================================"
echo "    OpenCV视觉系统 - C++版本编译脚本"
echo "========================================"
echo ""

# 检查CMake是否安装
if ! command -v cmake &> /dev/null; then
    echo "[错误] 未检测到CMake,请先安装CMake 3.10+"
    exit 1
fi

echo "[提示] CMake版本: $(cmake --version | head -n 1)"
echo ""

cd src/CPP

# 创建build目录
if [ -d "build" ]; then
    echo "[提示] 清理旧的build目录..."
    rm -rf build
fi

echo "[提示] 创建build目录..."
mkdir build
cd build

echo ""
echo "[提示] 正在配置CMake..."
cmake ..
if [ $? -ne 0 ]; then
    echo "[错误] CMake配置失败"
    exit 1
fi

echo ""
echo "[提示] 正在编译..."
make -j$(nproc)
if [ $? -ne 0 ]; then
    echo "[错误] 编译失败"
    exit 1
fi

echo ""
echo "========================================"
echo "    编译成功!"
echo "========================================"
echo ""
echo "可执行文件位置: build/bin/vision_system"
echo ""
echo "使用方法:"
echo "  ./build/bin/vision_system <图片路径>"
echo ""
