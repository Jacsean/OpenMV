# AI 记忆系统使用指南

> **目的**：说明如何使用 `.ai_memories/` 目录管理三层记忆系统。
> **适用对象**：项目开发者、AI 助手
> **最后更新**：2026-04-28

---

## 📁 目录结构

```
.ai_memories/
├── global/           # 全局记忆（跨项目通用）
│   └── coding_preferences.md
├── workspace/        # 项目记忆（当前项目特定）
│   └── project_specifications.md
└── sessions/         # 会话记录（开发历史）
    ├── README.md
    └── YYYY-MM-DD_topic.md
```

---

## 🎯 三层记忆详解

### 1. 全局记忆（Global Memories）

**位置**：`.ai_memories/global/`

**用途**：存储跨项目通用的编程习惯和偏好

**示例内容**：
- 代码风格规范
- 日志输出原则
- 协作模式
- 调试习惯
- 文档化偏好

**如何同步到多个项目**：

#### 方案 A：Git 子模块（推荐用于多项目）

```bash
# 1. 创建独立的全局记忆仓库
mkdir ~/ai-global-memories
cd ~/ai-global-memories
git init
# 添加你的全局记忆文件
git add .
git commit -m "init: 全局编程偏好"
git remote add origin git@github.com:yourname/ai-global-memories.git
git push -u origin main

# 2. 在每个项目中添加为子模块
cd StduyOpenCV
git submodule add git@github.com:yourname/ai-global-memories.git .ai_memories/global

# 3. 更新全局记忆后，在所有项目中同步
git submodule update --remote .ai_memories/global
```

**优势**：
- ✅ 一处修改，所有项目自动更新
- ✅ 版本控制清晰
- ✅ 团队可共享同一套全局偏好

#### 方案 B：符号链接（单机多项目）

```bash
# Windows (需要管理员权限)
mklink /D .ai_memories\global C:\Users\YourName\.ai_memories_global

# Linux/macOS
ln -s ~/.ai_memories_global .ai_memories/global
```

**优势**：
- ✅ 简单易用
- ✅ 实时同步
- ❌ 仅适用于单机

---

### 2. 项目记忆（Workspace Memories）

**位置**：`.ai_memories/workspace/`

**用途**：存储当前项目特有的规范和架构决策

**示例内容**：
- 插件系统规范
- 节点开发规则
- UI 显示标准
- 启动顺序要求
- API 使用禁忌

**如何管理**：

```bash
# 直接编辑
code .ai_memories/workspace/project_specifications.md

# 提交到 Git
git add .ai_memories/workspace/
git commit -m "docs: 更新项目规范 - 添加节点开发规则"
git push
```

**特点**：
- ✅ 随代码一起版本控制
- ✅ 团队成员克隆后即可见
- ✅ 历史记录完整可追溯

---

### 3. 会话记录（Session Logs）

**位置**：`.ai_memories/sessions/`

**用途**：记录重要的开发对话和决策过程

**何时记录**：
- ✅ 重要的架构决策讨论
- ✅ 复杂问题的排查过程
- ✅ 新功能的方案设计
- ✅ 遇到的坑及解决方案
- ❌ 日常琐碎对话无需记录

**如何记录**：

#### 方式 1：主动请求

```
用户："请记录这次关于插件迁移的讨论"

AI 助手：
1. 生成 Markdown 文件
2. 保存到 .ai_memories/sessions/YYYY-MM-DD_topic.md
3. 询问是否提交到 Git
```

#### 方式 2：自动提议

```
AI 助手："这次讨论涉及重要的架构决策，是否需要保存到会话记录中？"

用户："是的，保存"

AI 助手：生成文件并提交
```

**文件格式**：

```markdown
# 会话记录：YYYY-MM-DD 主题

## 背景
...

## 讨论要点
...

## 决策结果
...

## 实施步骤
...

## 经验教训
...

## 相关文件
...
```

**浏览和搜索**：

```bash
# 按日期查看
ls -lt .ai_memories/sessions/

# 搜索特定主题
grep -r "插件迁移" .ai_memories/sessions/

# 查看具体内容
cat .ai_memories/sessions/2026-04-28_migration_guide.md
```

---

## 🤖 AI 助手如何使用这些记忆

### 读取记忆

AI 助手通过 `read_file` 工具读取记忆文件：

```python
# 读取全局记忆
read_file(".ai_memories/global/coding_preferences.md")

# 读取项目记忆
read_file(".ai_memories/workspace/project_specifications.md")

# 读取会话记录
read_file(".ai_memories/sessions/2026-04-28_migration_guide.md")
```

### 更新记忆

当发现新的规范或决策时，AI 助手会：

1. **提议更新**：
   ```
   "我注意到我们讨论了新的日志规范，是否需要更新 
   .ai_memories/global/coding_preferences.md？"
   ```

2. **执行更新**（用户确认后）：
   ```python
   edit_file(".ai_memories/global/coding_preferences.md", ...)
   ```

3. **提交到 Git**：
   ```bash
   git add .ai_memories/
   git commit -m "docs: 更新全局记忆 - 添加日志规范"
   ```

### 记忆优先级

当不同层级的记忆冲突时，优先级为：

1. **会话记录**（最新讨论）> 
2. **项目记忆**（项目特定）> 
3. **全局记忆**（通用偏好）

**示例**：
- 全局记忆说"使用英文注释"
- 项目记忆说"使用中文注释"
- **最终采用**：中文注释（项目记忆优先）

---

## 👤 用户如何管理记忆

### 浏览记忆

```bash
# 查看所有记忆文件
tree .ai_memories/

# 快速查看全局偏好
cat .ai_memories/global/coding_preferences.md

# 查看项目规范
code .ai_memories/workspace/project_specifications.md

# 浏览会话历史
ls .ai_memories/sessions/
```

### 编辑记忆

直接用你喜欢的编辑器打开 [.md](file://d:\example\projects\StduyOpenCV\README.md) 文件编辑：

```bash
# VSCode
code .ai_memories/global/coding_preferences.md

# Vim
vim .ai_memories/workspace/project_specifications.md

# Notepad++
notepad++ .ai_memories/sessions/2026-04-28_migration_guide.md
```

### 添加新记忆

#### 添加全局记忆

```bash
# 创建新文件
code .ai_memories/global/new_preference.md

# 编辑内容
# 提交到独立的全局记忆仓库（如果使用子模块）
cd .ai_memories/global
git add new_preference.md
git commit -m "feat: 添加新的编程偏好"
git push
```

#### 添加项目记忆

```bash
# 直接在项目中创建
code .ai_memories/workspace/new_spec.md

# 提交到项目 Git
git add .ai_memories/workspace/new_spec.md
git commit -m "docs: 添加新项目规范"
git push
```

#### 记录新会话

```bash
# 手动创建
code .ai_memories/sessions/2026-04-29_new_feature.md

# 或者让 AI 助手自动生成
"请记录今天关于新功能的讨论"
```

---

## 🔄 迁移到新设备

### 步骤 1：克隆项目

```bash
git clone <repo_url>
cd StduyOpenCV
```

### 步骤 2：初始化子模块（如果使用）

```bash
git submodule init
git submodule update
```

### 步骤 3：验证记忆文件

```bash
# 检查文件是否存在
ls .ai_memories/global/
ls .ai_memories/workspace/
ls .ai_memories/sessions/

# 运行检查工具
python tools/check_migration_readiness.py
```

### 步骤 4：告知 AI 助手

```
"请阅读 .ai_memories/ 目录下的所有文件，了解项目规范和个人偏好"
```

AI 助手会自动加载这些文件作为"记忆"。

---

## 🛠️ 维护建议

### 定期整理

**频率**：每月一次

**任务清单**：
- [ ] 审查会话记录，删除无价值的内容
- [ ] 将重要的会话转化为正式文档（放入 `docs/`）
- [ ] 更新过时的规范
- [ ] 添加标签便于分类

### 添加标签

在会话记录文件头部添加标签：

```markdown
# 会话记录：2026-04-28 主题

**标签**：#架构 #调试 #新功能
```

便于搜索：

```bash
grep -r "#架构" .ai_memories/sessions/
```

### 备份策略

虽然 Git 已经提供版本控制，但建议：

```bash
# 每月导出一次备份
tar czf ai_memories_backup_$(date +%Y%m).tar.gz .ai_memories/

# 存储到云盘或外部硬盘
cp ai_memories_backup_*.tar.gz /backup/
```

---

## ❓ 常见问题

### Q1: 全局记忆和项目记忆冲突怎么办？

**A**: 项目记忆优先。如果全局偏好说"使用英文注释"，但项目规范要求"使用中文注释"，则遵循项目规范。

### Q2: 会话记录应该保存多久？

**A**: 建议保留所有有价值的记录。如果文件太多，可以：
- 按季度归档到 `sessions/archive/2026-Q1/`
- 删除明显无价值的草稿式对话
- 将重要内容提炼后放入正式文档

### Q3: 团队成员如何共享全局记忆？

**A**: 
- 方案 1：创建团队共享的全局记忆仓库
- 方案 2：每个成员维护自己的全局记忆
- 方案 3：将团队通用规范放入项目记忆中

### Q4: AI 助手会自动更新记忆吗？

**A**: 不会自动更新，但会主动提议。你可以：
- 接受提议，让 AI 助手执行更新
- 拒绝提议，手动编辑
- 要求 AI 助手只读不写

### Q5: 如何防止记忆文件过大？

**A**: 
- 定期清理过时内容
- 将会话记录归档
- 使用外部链接引用大型资源
- 拆分大文件为多个小文件

---

## 📚 相关文档

- [跨环境迁移指南](../docs/CROSS_ENVIRONMENT_MIGRATION.md)
- [项目开发规范](../docs/UNIFIED_NODE_DEVELOPMENT_GUIDE.md)
- [插件系统说明](../docs/Unified_Plugin_System.md)

---

**维护者**：StduyOpenCV 开发团队  
**版本**：1.0  
**最后更新**：2026-04-28
