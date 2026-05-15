# 调试命令指南

## 1. 激活虚拟环境

```PowerShell
.\.venv\Scripts\activate
```

## 2. 设置日志输出模式

```PowerShell
$env:LOG_LEVEL="NORMAL"
$env:LOG_LEVEL="DEBUG"
```

> $env:LOG\_LEVEL="NORMAL"
>
> - 启动正常日志输出模式：输出所有提示信息
>
> $env:LOG\_LEVEL="DEBUG"
>
> - 启动调试日志输出模式：不输出正常模式下的所有提示信息
>
## 3. 启动项目

```PowerShell
python src\python\main.py
```