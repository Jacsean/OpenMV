# 许可证与贡献

## 📋 文档导航

在参与贡献前，建议先阅读以下文档：

- 📘 [主项目文档](README.md) - 项目总览、快速开始、功能说明
- 📗 [Python版本详解](src/python/README.md) - Python模块化架构和扩展指南
- 📕 [C++版本详解](src/CPP/README.md) - C++版本编译和使用说明
- 📝 **本文档**: 贡献指南和开发规范

---

## 📜 许可证

本项目仅供学习和研究使用。您可以自由地:
- ✅ 学习项目代码
- ✅ 修改和扩展功能
- ✅ 用于个人或教学项目
- ✅ 分享和传播

**限制:**
- ❌ 不得用于商业目的
- ❌ 不得声称是原创作品
- ❌ 必须保留原作者信息

---

## 🤝 贡献指南

欢迎贡献代码、报告问题或提出建议!

### 如何贡献

#### 1. 报告问题 (Issues)
- 描述清楚问题现象
- 提供复现步骤
- 说明运行环境(系统版本、Python版本等)
- 附上截图或日志(如有)

#### 2. 提交代码 (Pull Requests)

**步骤:**
1. Fork本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

**代码规范:**
- Python: 遵循PEP 8规范
- C++: 遵循Google C++ Style Guide
- 添加必要的注释
- 保持代码整洁
- 测试通过

#### 3. 改进文档
- 修正拼写/语法错误
- 补充使用说明
- 添加示例代码
- 翻译文档

---

## 💡 贡献建议

### 可以改进的方向

**功能增强:**
- 添加更多图像处理算法
- 支持视频处理
- 批量处理功能
- 撤销/重做功能

**UI优化:**
- 更美观的界面设计
- 深色主题
- 图像对比功能
- 历史记录面板

**性能优化:**
- 算法加速
- 多线程处理
- GPU加速
- 内存优化

**新特性:**
- 插件系统
- 脚本支持
- API接口
- 云同步(可选)

---

## 👥 开发者

### 主要技术栈
- **Python**: OpenCV, Pillow, tkinter
- **C++**: OpenCV, CMake
- **平台**: Windows, Linux, macOS

### 开发环境推荐
- **IDE**: VS Code / PyCharm / CLion
- **Python版本**: 3.7+
- **OpenCV版本**: 4.5+
- **CMake版本**: 3.10+

### Python版本架构
Python版本采用 **MVC (Model-View-Controller)** 架构：
- **Model (`src/python/core/`)**: 核心图像处理算法
- **View (`src/python/UI/`)**: 用户界面组件
- **Controller (`src/python/controller.py`)**: 应用控制器

详见 [Python版本文档](src/python/README.md)

---

## 📞 联系方式

- 📧 Email: [your-email@example.com]
- 🐙 GitHub: [repository-url]
- 📝 Blog: [optional]

---

## 🙏 致谢

感谢以下开源项目:
- [OpenCV](https://opencv.org/) - 计算机视觉库
- [Python](https://www.python.org/) - 编程语言
- [CMake](https://cmake.org/) - 构建系统

---

## 📊 项目统计

![Languages](https://img.shields.io/badge/languages-Python%20%2B%20C++-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux%20%7C%20macOS-orange)

---

**感谢您的使用和贡献!** ❤️
