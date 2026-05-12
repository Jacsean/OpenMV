# 版本发布说明 - v5.5.7

**发布日期**: 2026-05-12  
**上一版本**: v5.5.6  
**版本号**: v5.5.7（修订版本升级）

---

## 📋 版本概览

v5.5.7 是一次日志文件功能改进更新，主要变更包括：
- 每次启动软件时自动创建新的日志文件
- 文件大小限制调整为 5MB
- 超过限制后自动创建带序号的新文件

---

## ✨ 功能改进

### 日志文件功能变更

**1. 新文件命名规则**
- 每次启动软件时自动创建新的日志文件
- 文件命名格式：`Record-yyyymmddhhmmss.log`
- 示例：`Record-20260512164106.log`

**2. 文件大小限制**
- 单文件最大：**5MB**（之前为 10MB）
- 超过限制后自动轮转

**3. 轮转策略**
- 超过 5MB 后创建带序号的新文件
- 序号格式：`Record-yyyymmddhhmmss-1.log`、`Record-yyyymmddhhmmss-2.log`...
- 无数量限制（之前最多保留 5 个备份）

**技术实现**:
```python
def _create_new_log_file(self) -> Path:
    """创建新的日志文件，文件名格式：Record-yyyymmddhhmmss.log"""
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    base_name = f"Record-{timestamp}"
    filename = f"{base_name}.log"
    file_path = self.log_dir / filename
    return file_path

def _rotate(self):
    """执行日志轮转，创建新的带序号文件"""
    self._current_file = self._get_next_log_file()
```

---

## 📁 文件变更清单

### 修改文件 (2个)
- `src/python/__version__.py` - 版本号更新到 5.5.7
- `src/python/utils/logger.py` - FileHandler 重构

### 新增文档 (1个)
- `docs/RELEASE_NOTES_v5.5.7.md` - 本发布说明文档

---

## 🎯 功能特性总结

| 功能 | 状态 | 说明 |
|-----|------|------|
| 启动时创建新文件 | ✅ | Record-yyyymmddhhmmss.log |
| 文件大小限制 | ✅ | 5MB |
| 自动轮转 | ✅ | 创建带序号文件 |
| 异步写入 | ✅ | 不阻塞主线程 |

---

## 🧪 测试建议

### 功能测试
1. **启动测试**:
   - 多次启动软件，检查是否每次创建新文件
   - 文件名格式是否正确

2. **大小限制测试**:
   - 生成超过 5MB 的日志
   - 检查是否自动创建带序号的新文件

3. **轮转测试**:
   - 继续生成日志，检查序号是否正确递增

---

## 📊 性能影响

- **内存占用**: 无变化
- **CPU 占用**: 无变化
- **磁盘空间**: 日志文件按时间分割，便于管理和清理

---

## 🚀 升级指南

### 兼容性
- ✅ 完全向后兼容
- ✅ 不影响现有日志文件

---

**完整变更详情**: 查看 Git 提交记录获取详细代码变更。