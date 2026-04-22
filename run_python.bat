@echo off
chcp 65001 >nul
echo ========================================
echo    OpenCV视觉系统 - Python版本
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到Python,请先安装Python 3.7+
    pause
    exit /b 1
)

echo [提示] 正在检查依赖...
pip list 2>nul | findstr opencv-python >nul
if errorlevel 1 (
    echo [提示] 正在安装依赖包...
    pip install -r src\python\requirements.txt
    if errorlevel 1 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo [成功] 依赖已安装
)

echo.
echo [提示] 正在启动程序...
echo.

cd src\python
python vision_system.py

if errorlevel 1 (
    echo.
    echo [错误] 程序运行出错
    pause
)
