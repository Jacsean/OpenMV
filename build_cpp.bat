@echo off
chcp 65001 >nul
echo ========================================
echo    OpenCV视觉系统 - C++版本编译脚本
echo ========================================
echo.

REM 检查CMake是否安装
cmake --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未检测到CMake,请先安装CMake 3.10+
    pause
    exit /b 1
)

echo [提示] CMake版本信息:
cmake --version | findstr version
echo.

cd src\CPP

REM 创建build目录
if exist build (
    echo [提示] 清理旧的build目录...
    rmdir /s /q build
)

echo [提示] 创建build目录...
mkdir build
cd build

echo.
echo [提示] 正在配置CMake...
cmake ..
if errorlevel 1 (
    echo [错误] CMake配置失败
    pause
    exit /b 1
)

echo.
echo [提示] 正在编译...
cmake --build . --config Release
if errorlevel 1 (
    echo [错误] 编译失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo    编译成功!
echo ========================================
echo.
echo 可执行文件位置: build\bin\Release\vision_system.exe
echo.
echo 使用方法:
echo   vision_system.exe ^<图片路径^>
echo.

pause
