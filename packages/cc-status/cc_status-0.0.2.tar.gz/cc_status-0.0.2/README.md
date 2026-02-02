# cc-status

[![CI](https://img.shields.io/badge/CI-passing-brightgreen)]()
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Claude Code 状态栏功能模块 - 为 Claude Code 提供高效的状态栏显示和管理功能。

## ✨ 功能特性

🚧 **项目处于早期开发阶段**

计划功能：
- 🎯 状态管理：高效的状态获取和更新机制
- 🎨 格式化输出：美观的状态栏显示格式
- ⚙️ 配置管理：灵活的配置加载和管理
- 🖥️ CLI 接口：完整的命令行工具支持

## 📦 安装

### 方法 1: 一键安装（推荐）

使用 uvx 快速安装并配置：

```bash
# 一键安装到 Claude Code
uvx cc-status install

# 重启 Claude Code 即可看到状态栏
claude
```

### 方法 2: 从 PyPI 安装（尚未发布）

```bash
# 安装包
pip install cc-status

# 安装到 Claude Code
cc-status install

# 重启 Claude Code
claude
```

### 方法 3: 从源码安装（开发版本）

```bash
# 克隆仓库
git clone https://github.com/michaelche/cc-status.git
cd cc-status

# 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境并安装依赖
uv venv
source .venv/bin/activate  # macOS/Linux
uv pip install -e ".[dev]"

# 安装到 Claude Code
python -m cc_status install

# 重启 Claude Code
claude
```

## 🚀 快速开始

### 一键安装方式

```bash
# 安装并自动配置
uvx cc-status install

# 自定义主题和刷新间隔
uvx cc-status install --theme modern --interval 5000

# 验证配置
uvx cc-status verify

# 卸载
uvx cc-status uninstall
```

### 命令行用法

```bash
# 运行 CLI
python -m cc_status

# 或使用安装的命令
cc-status
```

### 开发示例

```python
import cc_status

# 查看版本信息
print(cc_status.__version__)
```

更多示例请查看 [examples/](examples/) 目录。

## 🛠️ 开发指南

### 快速设置开发环境

```bash
# 1. 克隆并进入项目
git clone https://github.com/michaelche/cc-status.git
cd cc-status

# 2. 安装 uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 3. 设置环境
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"

# 4. 验证设置
./scripts/verify_setup.sh
```

### 运行测试

```bash
# 运行所有测试
pytest

# 带覆盖率报告
pytest --cov=cc_status
```

### 代码质量检查

```bash
# 格式化代码
black src/ tests/

# 代码检查
ruff check src/ tests/

# 类型检查
mypy src/
```

详细的开发指南请参考 [CLAUDE.md](CLAUDE.md)。

## 📚 文档

- [开发指南](CLAUDE.md) - Claude Code 的详细开发指导
- [变更日志](CHANGELOG.md) - 项目版本历史
- [架构文档](docs/architecture.md) - 系统架构说明（待完善）
- [API 参考](docs/api.md) - API 使用文档（待完善）

## 🤝 贡献指南

欢迎贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m '新增: 添加某个很棒的功能'`)
   - 提交信息请使用中文
   - 遵循提交规范（见 [CLAUDE.md](CLAUDE.md#提交规范)）
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 打开 Pull Request

### 开发规范

- 使用中文编写所有文档和提交信息
- 遵循 Python PEP 8 编码规范
- 保持测试覆盖率 > 80%
- 确保所有质量检查通过（black、ruff、mypy）
- 为新功能添加对应的测试

## 📄 许可证

本项目采用 [Apache License 2.0](LICENSE) 许可证。

## 🙏 致谢

- 感谢 [Claude AI](https://claude.ai) 提供强大的 AI 辅助开发能力
- 感谢所有开源项目的贡献者

## 📮 联系方式

- 项目主页: [https://github.com/michaelche/cc-status](https://github.com/michaelche/cc-status)
- 问题反馈: [GitHub Issues](https://github.com/michaelche/cc-status/issues)

---

**注意**: 本项目处于活跃开发中，API 可能会有变动。建议关注 [CHANGELOG.md](CHANGELOG.md) 了解最新变更。
