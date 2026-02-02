# 变更日志

所有重要的项目变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 计划中
- 状态管理核心功能
- 格式化输出工具
- 配置加载机制
- 完整的 CLI 命令接口

## [0.1.0] - 2026-01-27

### 新增
- 初始化项目结构（Src Layout）
- 配置 uv 包管理器和 pyproject.toml
- 创建源码目录结构（src/cc_statusline）
- 配置开发工具链（pytest、black、ruff、mypy）
- 实现基础 CLI 入口点（__main__.py）
- 建立测试框架和基础测试
- 添加 .gitignore 和 .python-version
- 创建项目文档（CLAUDE.md、README.md）
- 添加自动化验证脚本（verify_setup.sh）

### 配置
- Python 版本要求：>= 3.9
- 开发工具：black（代码格式化）、ruff（代码检查）、mypy（类型检查）
- 测试工具：pytest、pytest-cov
- 构建工具：hatchling
