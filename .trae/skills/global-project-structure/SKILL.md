---


---
name: global-project-structure
description: 全局项目结构规范（Python/JS/Java通用）
scope: global
-------------

# 全局项目结构

## 1.通用根目录（必选）

project-root/
├─ .trae/skills       # 项目级 Skill
├─ src/                 # 源码
├─ tests/               # 测试
├─ config/              # 环境配置（dev/prod/test）
├─ docs/                # 文档
├─ assets/              # 静态资源
├─ scripts/             # 构建/部署脚本d
├─ .gitignore
└─ README.md

## 2.Python项目（src/）

src/
├─ main.py
├─ core/
│  ├─ service/
│  ├─ model/
│  └─ util/
├─ api/
│  ├─ routes/
│  └─ schemas/
└─ common/
   ├─ logger.py
   ├─ exception.py
   └─ config.py


## 3. JavaScript/TypeScript 项目（src/）

src/
├─ index.js
├─ components/
├─ pages/
├─ services/
├─ utils/
└─ assets/


## 4. Java 项目（src/main/java）

com.company.project/
├─ Application.java       # 入口
├─ controller/            # 接口
├─ service/               # 业务
├─ model/                 # 实体
├─ repository/            # 数据访问
│    └─ common/                # 公共
├─ config/             	# 配置
├─ exception/          # 异常
└─ util/               		# 工具


## 5. 配置文件规范 
- 配置分环境：`dev.json`、`prod.json`、`test.json` 
- 敏感配置：**不提交到代码库**，用环境变量或本地配置  
- 配置项：数据库、缓存、日志、端口、密钥、第三方服务 

## 6. 入口文件规范 、
- 单一入口：`main.py` / `index.js` 
- 入口只做：**初始化、配置加载、服务启动、异常捕获** 
- 业务逻辑全部放到 `core` / `service` 

## 7. 测试规范 
- 测试目录：`tests/`，与 `src/` 结构对应 
- 单元测试覆盖：**核心函数、边界case、异常**
- 测试命名：`test_xxx.py` / `xxx.test.js` 

## 8. 禁止项 
- 禁止：代码与配置混放
- 禁止：根目录堆满文件-
- 禁止：测试代码与业务代码混放 
- 禁止：静态资源乱放

