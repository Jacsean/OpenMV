# 快速开始指南

## 🚀 5分钟上手OpenCV视觉系统

### Python版本 (推荐新手)

#### Windows用户
```bash
# 1. 双击运行启动脚本
run_python.bat

# 或者手动运行
cd src\python
pip install -r requirements.txt
python vision_system.py
```

#### Linux/Mac用户
```bash
# 1. 赋予执行权限
chmod +x run_python.sh

# 2. 运行
./run_python.sh
```

#### 使用程序
1. **打开图片**: 点击左上角"打开图片"按钮
2. **尝试滤镜**: 点击左侧的各种算法按钮
3. **选择ROI**: 点击"选择ROI",然后在图片上拖动鼠标
4. **保存结果**: 点击"保存图片"

---

### C++版本 (推荐高性能需求)

#### 编译 (首次使用)

**Windows:**
```bash
build_cpp.bat
```

**Linux/Mac:**
```bash
chmod +x build_cpp.sh
./build_cpp.sh
```

#### 运行

**需要一张测试图片:**
```bash
# 先用Python创建测试图片
cd src/python
python create_test_image.py

# 然后运行C++程序
cd ../CPP/build/bin
./vision_system test_image.png  # Linux/Mac
# 或
vision_system.exe test_image.png  # Windows
```

#### 快捷键
- `2` - 灰度化
- `3` - 高斯模糊
- `5` - Canny边缘检测
- `r` - 选择ROI
- `c` - 裁剪ROI
- `ESC` - 退出

---

## 📸 测试所有功能

### 1. 创建测试图片
```bash
cd src/python
python create_test_image.py
```

会生成 `test_image.png`,包含各种几何图形和渐变效果。

### 2. 测试Python版本
```bash
python vision_system.py
```

**测试清单:**
- [ ] 打开test_image.png
- [ ] 点击"灰度化"
- [ ] 点击"Canny边缘检测"
- [ ] 拖动Canny阈值滑块
- [ ] 点击"选择ROI"并框选区域
- [ ] 点击"裁剪ROI"
- [ ] 点击"保存图片"

### 3. 测试C++版本
```bash
cd ../CPP/build/bin
./vision_system test_image.png
```

**测试清单:**
- [ ] 按`2`灰度化
- [ ] 按`5`Canny边缘检测
- [ ] 按`r`选择ROI
- [ ] 用鼠标框选区域
- [ ] 按`c`裁剪
- [ ] 按`ESC`退出

---

## 🎯 常见问题速查

### Python版本无法启动?
```bash
# 检查Python版本
python --version  # 需要 3.7+

# 重新安装依赖
pip install --upgrade opencv-python Pillow numpy
```

### C++版本编译失败?
```bash
# 检查是否安装了OpenCV
# Ubuntu/Debian
dpkg -l | grep opencv

# macOS
brew list | grep opencv

# Windows (vcpkg)
.\vcpkg list
```

### ROI选择后无法裁剪?
- **Python**: 确保已拖动鼠标选择了区域
- **C++**: 按`r`选择,然后按`c`裁剪

---

## 📚 更多帮助

- 详细文档: 查看 `README.md`
- 安装问题: 查看 `INSTALL.md`
- 功能说明: 查看各版本的 `README.md`

---

## 💡 小贴士

1. **调整参数**: Python版本可以拖动滑块实时调整Canny和二值化参数
2. **撤销操作**: 点击"原图"按钮恢复原始图像
3. **批量测试**: 准备多张不同格式的图片测试兼容性
4. **查看代码**: 代码有详细注释,适合学习

---

**开始你的图像处理之旅!** 🎨📷
