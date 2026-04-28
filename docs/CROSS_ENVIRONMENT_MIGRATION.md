# 跨环境迁移与记忆持久化指南

本文档说明如何在重装操作系统、更换设备或迁移项目时，保留 AI 助手的记忆和项目配置。

## 📋 目录

- [记忆系统的三个层级](#记忆系统的三个层级)
- [迁移前准备](#迁移前准备)
- [迁移步骤](#迁移步骤)
- [新环境恢复](#新环境恢复)
- [验证清单](#验证清单)
- [常见问题](#常见问题)

---

## 记忆系统的三个层级

### 1. 会话记忆（Session）
- **作用范围**：当前对话窗口
- **持久性**：❌ 关闭即消失
- **迁移策略**：重要内容应主动转化为项目文档

### 2. 项目记忆（Workspace）
- **作用范围**：当前项目（StduyOpenCV）
- **持久性**：⚠️ 依赖存储机制
- **迁移策略**：文档化 + Git 管理（最可靠）

### 3. 全局记忆（Global）
- **作用范围**：所有项目
- **持久性**：✅ 通常较稳定
- **迁移策略**：云端同步或配置文件备份

---

## 迁移前准备

### ✅ 步骤 1：检查项目文档完整性

确保 `docs/` 目录包含以下核心文档：

```bash
# 在项目根目录执行
ls docs/
```

**必需文档清单**：
- ✅ `ARCHITECTURE_EVOLUTION.md` - 架构演进方案
- ✅ `AI_MODULE_RESOURCE_ISOLATION.md` - AI 模块设计规范
- ✅ `UNIFIED_NODE_DEVELOPMENT_GUIDE.md` - 节点开发指南
- ✅ `PLUGIN_MIGRATION_TUTORIAL.md` - 插件迁移教程
- ✅ `Unified_Plugin_System.md` - 统一插件系统说明

**如果缺少关键文档**，应先补充：
```
"帮我创建 ARCHITECTURE_DECISIONS.md，记录项目的核心架构决策"
```

### ✅ 步骤 2：导出项目记忆（如果系统支持）

在 AI 助手中执行：
```
"导出 StduyOpenCV 项目的所有记忆到 migration/project_memories.json"
```

如果系统不支持导出，手动记录关键规范：
```markdown
# migration/PROJECT_MEMORIES_MANUAL.md

## 项目特定规范

### 插件系统
- user_plugins 目录仅包含插件包
- 共享库放在 shared_libs/ 目录
- 使用下划线前缀命名内部模块

### 节点开发
- 所有节点继承 AIBaseNode
- process() 方法必须包含 try-except
- 输入端口命名"输入XXX"，输出"输出XXX"

### UI 规范
- 日志同时输出到终端和 UI 面板
- 节点库标签页使用 category_group 字段
- 修改 __identifier__ 后需重启应用

...（根据实际记忆补充）
```

### ✅ 步骤 3：备份全局记忆

#### 方案 A：云端同步（推荐）
```
确认已登录 AI 助手账户
记忆会自动同步到云端
```

#### 方案 B：手动备份配置文件

**Windows**：
```powershell
# 备份全局记忆
copy $env:APPDATA\LingMA\global_memories.json D:\backup\

# 或者查找其他可能的位置
dir $env:APPDATA\*lingma* /s
dir $env:LOCALAPPDATA\*lingma* /s
```

**Linux/macOS**：
```bash
# 备份全局记忆
cp ~/.config/lingma/global_memories.json ~/backup/
# 或
cp ~/.lingma/config.json ~/backup/
```

#### 方案 C：导出为通用格式
```
"导出所有全局记忆为 Markdown 格式到 GLOBAL_PREFERENCES.md"
```

### ✅ 步骤 4：创建个人编程习惯文档

创建 `migration/PERSONAL_CODING_PREFERENCES.md`：

```markdown
# 个人编程习惯与偏好

## 代码风格
- 函数命名：snake_case
- 类名：PascalCase
- 常量：UPPER_CASE
- 注释语言：中文（技术术语保留英文）

## 日志规范
- 常规流程日志精简
- 保留关键错误信息
- 同时输出到终端和 UI

## 协作模式
- 复杂任务分解为多个步骤
- 每步完成后等待确认
- 功能改进总结使用简洁清单

## 调试习惯
- 优先使用本地 Ollama 运行模型
- 避免依赖云端服务
- 静默执行代码修改，无需确认

## 文档化偏好
- 设计理念和奇思妙想及时文档化
- 方案讨论后立即记录
- 形成知识库降低沟通成本
```

### ✅ 步骤 5：打包迁移文件

```bash
# 创建迁移目录
mkdir migration

# 复制关键文件
cp -r docs/ migration/docs/
cp README.md migration/
cp CONTRIBUTING.md migration/

# 添加导出的记忆文件（如果有）
# cp project_memories.json migration/
# cp global_memories.json migration/
cp PERSONAL_CODING_PREFERENCES.md migration/

# 打包
tar czf StduyOpenCV_migration_$(date +%Y%m%d).tar.gz migration/

# Windows PowerShell
Compress-Archive -Path migration -DestinationPath "StduyOpenCV_migration_$(Get-Date -Format 'yyyyMMdd').zip"
```

---

## 迁移步骤

### 场景 A：重装同一台电脑的操作系统

1. **备份阶段**（重装前）
   ```bash
   # 1. 推送所有 Git 更改
   git add .
   git commit -m "chore: 保存迁移前的状态"
   git push
   
   # 2. 执行上述"迁移前准备"的所有步骤
   
   # 3. 备份整个项目目录（可选）
   tar czf StduyOpenCV_full_backup.tar.gz ../StduyOpenCV/
   ```

2. **恢复阶段**（重装后）
   ```bash
   # 1. 安装基础软件
   # - Python 3.8+
   # - Git
   # - VSCode
   # - AI 助手插件
   
   # 2. 克隆项目
   git clone <your_repo_url>
   cd StduyOpenCV
   
   # 3. 恢复全局记忆
   # 方案A：登录 AI 助手账户自动同步
   # 方案B：复制备份的配置文件
   
   # 4. 导入项目记忆（如果导出了）
   # 在 AI 助手中执行：
   # "从 migration/project_memories.json 导入项目记忆"
   
   # 5. 验证文档
   ls docs/
   ```

### 场景 B：迁移到新电脑/新操作系统

1. **原系统准备**
   - 执行"迁移前准备"的所有步骤
   - 将迁移包复制到外部存储或云盘

2. **新系统恢复**
   ```bash
   # 1. 安装相同的基础软件栈
   
   # 2. 解压迁移包
   tar xzf StduyOpenCV_migration_*.tar.gz
   
   # 3. 克隆或复制项目
   git clone <your_repo_url>
   # 或
   cp -r backup/StduyOpenCV/ ./
   
   # 4. 恢复全局和项目记忆
   
   # 5. 安装项目依赖
   cd StduyOpenCV
   pip install -r requirements.txt  # 如果有
   ```

### 场景 C：团队协作（分享给其他人）

**不需要迁移记忆**，只需：
```bash
# 1. 确保文档完整
git push

# 2. 团队成员克隆
git clone <repo_url>

# 3. 阅读文档
cat docs/*.md
```

**优势**：文档化的规范对所有人都可见，不依赖个人记忆。

---

## 新环境恢复

### 步骤 1：验证基础环境

```bash
# 检查 Python 版本
python --version  # 应 >= 3.8

# 检查 Git
git --version

# 检查 IDE 插件
# 在 VSCode 中确认 AI 助手已安装并启用
```

### 步骤 2：恢复全局记忆

#### 优先级 1：云端同步
```
1. 打开 VSCode
2. 登录 AI 助手账户
3. 等待同步完成（通常几秒）
4. 测试："显示我的全局编程习惯"
```

#### 优先级 2：手动导入
```
1. 复制备份的 global_memories.json 到正确位置
2. 重启 VSCode
3. 测试记忆是否生效
```

#### 优先级 3：通过文档重建
```
打开 PERSONAL_CODING_PREFERENCES.md
逐条告诉 AI 助手：
"记住这个全局偏好：[具体内容]"
```

### 步骤 3：恢复项目记忆

#### 如果导出了记忆文件
```
在 AI 助手中执行：
"从 migration/project_memories.json 导入 StduyOpenCV 项目记忆"
```

#### 如果没有导出文件
```
基于 docs/ 目录的文档，AI 助手会自动学习项目规范

你可以主动引导：
"这个项目使用插件化架构，查看 docs/Unified_Plugin_System.md"
"节点开发遵循 docs/UNIFIED_NODE_DEVELOPMENT_GUIDE.md 的规范"
```

### 步骤 4：验证项目结构

```bash
# 检查关键目录
ls src/python/user_plugins/
ls src/python/shared_libs/
ls docs/
ls workspace/

# 检查 Git 状态
git status
git log --oneline -5
```

---

## 验证清单

### ✅ 全局记忆验证

在 AI 助手中测试：
```
"显示我的全局编程习惯"
"我有哪些跨项目的偏好？"
```

**预期结果**：
- 能看到代码风格偏好
- 能看到协作模式设置
- 能看到调试习惯

### ✅ 项目记忆验证

```
"显示 StduyOpenCV 项目的开发规范"
"这个项目的插件系统有什么特点？"
"节点开发需要遵循哪些规则？"
```

**预期结果**：
- 能回答插件目录组织规范
- 能回答节点继承关系
- 能回答 UI 显示规范

### ✅ 文档完整性验证

```bash
# 检查核心文档是否存在
test -f docs/ARCHITECTURE_EVOLUTION.md && echo "✅ 架构文档存在"
test -f docs/UNIFIED_NODE_DEVELOPMENT_GUIDE.md && echo "✅ 节点开发指南存在"
test -f docs/Unified_Plugin_System.md && echo "✅ 插件系统文档存在"
test -f README.md && echo "✅ 项目说明存在"
```

### ✅ 功能验证

```bash
# 运行项目
cd src/python
python main.py

# 测试基本功能
# 1. 能否加载插件？
# 2. 节点库是否正常显示？
# 3. 工作流能否创建？
```

---

## 常见问题

### Q1: 重装系统后，项目记忆完全丢失怎么办？

**解决方案**：
1. 不要惊慌，文档还在 Git 中
2. 打开项目，让 AI 助手重新学习：
   ```
   "阅读 docs/ 目录下的所有文档，了解这个项目"
   "根据 UNIFIED_NODE_DEVELOPMENT_GUIDE.md，总结节点开发规范"
   ```
3. 逐步重建关键记忆（优先项目特定的）

### Q2: 不同操作系统的配置文件路径不同怎么办？

**解决方案**：
- Windows: `%APPDATA%\LingMA\`
- Linux: `~/.config/lingma/`
- macOS: `~/Library/Application Support/LingMA/`

迁移时注意调整路径，或使用云端同步避免此问题。

### Q3: 记忆系统不支持导出/导入功能怎么办？

**解决方案**：
1. **短期**：手动记录关键规范到 `migration/MEMORY_NOTES.md`
2. **长期**：推动记忆系统增加导出功能
3. **根本解决**：加强文档化，减少对记忆系统的依赖

### Q4: 团队成员如何共享项目规范？

**最佳实践**：
```
❌ 不要：依赖个人的 AI 助手记忆
✅ 应该：将所有规范写入 docs/ 并纳入 Git

团队新成员：
1. git clone 项目
2. 阅读 docs/README.md（文档索引）
3. 按需阅读具体文档
```

### Q5: 如何定期备份记忆？

**建议频率**：每月一次

**自动化脚本示例**（`tools/backup_memories.sh`）：
```bash
#!/bin/bash
# 备份记忆的简单脚本

BACKUP_DIR=~/memory_backups/$(date +%Y%m)
mkdir -p $BACKUP_DIR

# 备份全局记忆（路径根据实际情况调整）
cp ~/.config/lingma/global_memories.json $BACKUP_DIR/ 2>/dev/null

# 导出项目记忆（如果支持命令行）
# lingma-cli export workspace --output $BACKUP_DIR/project_memories.json

echo "记忆备份完成: $BACKUP_DIR"
```

---

## 最佳实践总结

### 🎯 核心原则

1. **文档优于记忆**：关键规范必须写入 `docs/` 目录
2. **Git 是终极备份**：所有文档纳入版本控制
3. **云端同步最可靠**：全局记忆优先使用账户同步
4. **定期验证**：每季度检查一次记忆系统的可用性

### 📊 可靠性对比

| 方式 | 可靠性 | 维护成本 | 团队协作 | 推荐度 |
|------|--------|---------|---------|--------|
| **文档 + Git** | ⭐⭐⭐⭐⭐ | 低 | ✅ 完美 | 🔥 强烈推荐 |
| **云端同步** | ⭐⭐⭐⭐ | 极低 | ❌ 个人 | ✅ 推荐 |
| **配置文件备份** | ⭐⭐⭐ | 中 | ❌ 困难 | ⚠️ 备选 |
| **纯记忆系统** | ⭐⭐ | 低 | ❌ 不可能 | ❌ 不推荐 |

### 🚀 行动建议

**立即执行**：
1. ✅ 检查 `docs/` 目录完整性
2. ✅ 创建 `PERSONAL_CODING_PREFERENCES.md`
3. ✅ 确认 Git 远程仓库可访问

**近期计划**：
1. 📅 本月内：导出一次记忆备份
2. 📅 下月前：测试一次完整迁移流程
3. 📅 季度：审查并更新文档

**长期目标**：
- 建立标准化的迁移工具
- 实现记忆自动备份
- 完善团队知识共享机制

---

## 附录：快速参考

### 关键文件位置

```
StduyOpenCV/
├── docs/                    # 项目文档（最重要）
│   ├── ARCHITECTURE_EVOLUTION.md
│   ├── UNIFIED_NODE_DEVELOPMENT_GUIDE.md
│   └── ...
├── migration/               # 迁移临时目录（可选）
│   ├── project_memories.json
│   ├── global_memories.json
│   └── PERSONAL_CODING_PREFERENCES.md
├── README.md                # 项目总览
└── CONTRIBUTING.md          # 贡献指南
```

### 常用命令速查

```bash
# 检查文档完整性
ls docs/*.md

# 打包迁移文件
tar czf migration_$(date +%Y%m%d).tar.gz docs/ README.md

# Git 操作
git status
git add .
git commit -m "docs: 更新迁移指南"
git push

# 验证 Python 环境
python --version
pip list | grep opencv
```

### 联系与支持

如遇到迁移问题：
1. 首先检查 `docs/` 目录是否有相关说明
2. 查看 Git 历史记录寻找线索
3. 在项目中创建 Issue 记录问题

---

**最后更新**: 2026-04-28  
**维护者**: 项目开发团队  
**版本**: 1.0
