# 安装指南

## Python版本安装

### Windows

1. **安装Python** (如果尚未安装)
   - 访问 https://www.python.org/downloads/
   - 下载并安装Python 3.7或更高版本
   - 安装时勾选"Add Python to PATH"

2. **运行程序**
   ```bash
   # 方式1: 使用启动脚本
   run_python.bat
   
   # 方式2: 手动安装和运行
   cd src\python
   pip install -r requirements.txt
   python vision_system.py
   ```

### Linux/Mac

```bash
# 方式1: 使用启动脚本
chmod +x run_python.sh
./run_python.sh

# 方式2: 手动安装和运行
cd src/python
pip3 install -r requirements.txt
python3 vision_system.py
```

---

## C++版本安装

### Windows

#### 方法1: 使用vcpkg (推荐)

1. **安装vcpkg**
   ```powershell
   git clone https://github.com/Microsoft/vcpkg.git
   cd vcpkg
   .\bootstrap-vcpkg.bat
   ```

2. **安装OpenCV**
   ```powershell
   .\vcpkg install opencv:x64-windows
   .\vcpkg integrate install
   ```

3. **编译项目**
   ```powershell
   build_cpp.bat
   ```

4. **运行程序**
   ```powershell
   src\CPP\build\bin\Release\vision_system.exe <图片路径>
   ```

#### 方法2: 使用预编译的OpenCV

1. **下载OpenCV**
   - 访问 https://opencv.org/releases/
   - 下载Windows版本安装包
   - 运行安装程序

2. **设置环境变量**
   - 添加OpenCV的bin目录到PATH
   - 例如: `C:\opencv\build\x64\vc15\bin`

3. **编译项目**
   ```powershell
   cd src\CPP
   mkdir build
   cd build
   cmake -DOpenCV_DIR=C:\opencv\build ..
   cmake --build . --config Release
   ```

---

### Linux (Ubuntu/Debian)

1. **安装依赖**
   ```bash
   sudo apt-get update
   sudo apt-get install -y libopencv-dev cmake build-essential
   ```

2. **编译项目**
   ```bash
   chmod +x build_cpp.sh
   ./build_cpp.sh
   ```

3. **运行程序**
   ```bash
   src/CPP/build/bin/vision_system <图片路径>
   ```

---

### macOS

1. **安装Homebrew** (如果尚未安装)
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. **安装OpenCV和CMake**
   ```bash
   brew install opencv cmake
   ```

3. **编译项目**
   ```bash
   chmod +x build_cpp.sh
   ./build_cpp.sh
   ```

4. **运行程序**
   ```bash
   src/CPP/build/bin/vision_system <图片路径>
   ```

---

## 验证安装

### 测试Python版本

```bash
cd src/python
python create_test_image.py  # 创建测试图片
python vision_system.py      # 启动程序
```

在程序中:
1. 点击"打开图片"
2. 选择生成的test_image.png
3. 尝试各种滤镜和ROI功能

### 测试C++版本

```bash
# 先创建测试图片(使用Python版本)
cd src/python
python create_test_image.py

# 然后运行C++版本
cd ../CPP/build/bin
./vision_system ../../../test_image.png
```

在程序中:
1. 按数字键2-9尝试不同滤镜
2. 按'r'开始ROI选择
3. 按ESC退出

---

## 常见问题解决

### Python版本问题

**Q: 提示"No module named 'cv2'"**
```bash
pip install opencv-python
```

**Q: 提示"No module named 'PIL'"**
```bash
pip install Pillow
```

**Q: 界面无法显示**
- 检查Python版本: `python --version` (需要3.7+)
- 更新tkinter: 通常随Python一起安装

---

### C++版本问题

**Q: CMake找不到OpenCV**

Windows:
```bash
cmake -DOpenCV_DIR=C:/path/to/opencv/build ..
```

Linux:
```bash
sudo apt-get install pkg-config
cmake .. `pkg-config --cflags --libs opencv4`
```

**Q: 编译时找不到头文件**
- 确保已正确安装OpenCV开发包
- 检查include路径是否正确

**Q: 运行时找不到动态库**

Linux:
```bash
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/local/lib
```

或在 `/etc/ld.so.conf.d/opencv.conf` 中添加:
```
/usr/local/lib
```

然后执行:
```bash
sudo ldconfig
```

---

## 卸载

### Python版本
```bash
pip uninstall opencv-python Pillow numpy
```

### C++版本

Linux:
```bash
sudo apt-get remove libopencv-dev
```

macOS:
```bash
brew uninstall opencv
```

Windows (vcpkg):
```powershell
.\vcpkg remove opencv:x64-windows
```

---

## 获取帮助

如遇到其他问题:
1. 查看各版本的README.md文件
2. 检查OpenCV官方文档: https://docs.opencv.org/
3. 提交Issue到项目仓库
