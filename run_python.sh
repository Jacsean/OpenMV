#!/bin/bash

echo "========================================"
echo "    OpenCV视觉系统 - Python版本"
echo "========================================"
echo ""

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到Python3,请先安装Python 3.7+"
    exit 1
fi

echo "[提示] Python版本: $(python3 --version)"

# 检查依赖
if ! python3 -c "import cv2" 2>/dev/null; then
    echo "[提示] 正在安装依赖包..."
    pip3 install -r src/python/requirements.txt
    if [ $? -ne 0 ]; then
        echo "[错误] 依赖安装失败"
        exit 1
    fi
else
    echo "[成功] 依赖已安装"
fi

echo ""
echo "[提示] 正在启动程序..."
echo ""

cd src/python
python3 vision_system.py
