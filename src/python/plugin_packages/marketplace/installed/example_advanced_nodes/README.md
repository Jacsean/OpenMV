# 高级节点示例包

> 演示节点开发的最佳实践和高级技巧

## 📦 包含节点

### 1. 多图像混合 (MultiInputBlendNode)

**功能**: 支持2-4张图像的加权混合

**学习要点**:
- ✅ 多输入端口处理
- ✅ 动态参数归一化
- ✅ 图像尺寸自动对齐
- ✅ 完整的异常处理

**使用场景**:
- 图像融合
- 透明度混合
- 多曝光合成

**示例工作流**:
```
[加载图像1] ──┐
[加载图像2] ──┼── [多图像混合] ── [保存图像]
[加载图像3] ──┘
```

---

## 🎯 学习路径

### 初学者
1. 阅读每个节点的docstring
2. 在节点编辑器中查看代码
3. 拖拽节点到画布测试效果
4. 修改参数观察变化

### 进阶开发者
1. 分析多输入处理逻辑
2. 学习参数验证技巧
3. 理解异常处理模式
4. 参考性能优化方法

### 高级用户
1. 扩展为新节点类型
2. 集成自定义算法
3. 优化内存管理
4. 添加单元测试

---

## 💡 最佳实践总结

### 1. 输入验证
```python
if inputs and len(inputs) > 0 and inputs[0] is not None:
    image = inputs[0][0] if isinstance(inputs[0], list) else inputs[0]
```

### 2. 参数范围限制
```python
value = max(min_value, min(max_value, float(self.get_property('param'))))
```

### 3. 异常安全
```python
try:
    # 处理逻辑
    return {'输出': result}
except Exception as e:
    print(f"错误: {e}")
    return {'输出': None}
```

### 4. 图像尺寸统一
```python
if img.shape[:2] != (base_h, base_w):
    img = cv2.resize(img, (base_w, base_h))
```

### 5. 彩色图像处理
```python
# 转换到LAB空间处理亮度通道
lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB)
l, a, b = cv2.split(lab)
# 处理l通道
l_eq = process(l)
lab_eq = cv2.merge([l_eq, a, b])
result = cv2.cvtColor(lab_eq, cv2.COLOR_LAB2BGR)
```

---

## 🔧 调试技巧

### 启用详细日志
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def process(self, inputs=None):
    logger.debug(f"输入: {inputs}")
    logger.debug(f"参数: alpha={self.get_property('alpha')}")
```

### 性能分析
```python
import time

def process(self, inputs=None):
    start = time.time()
    # 处理逻辑
    elapsed = time.time() - start
    print(f"处理耗时: {elapsed*1000:.2f}ms")
```

---

## 📚 相关文档

- [节点开发完全指南](../NODE_DEVELOPMENT_GUIDE.md)
- [API参考手册](../NODE_API_REFERENCE.md)
- [插件系统介绍](../../../README.md#插件系统)

---

**版本**: 1.0.0  
**作者**: OpenCV Team  
**最后更新**: 2026-05-03
