# cc-statusline 常用命令

## 环境初始化

```bash
# 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# 安装项目依赖
uv pip install -e ".[dev]"
```

## 依赖管理

```bash
# 安装项目（可编辑模式）
uv pip install -e .

# 安装开发依赖
uv pip install -e ".[dev]"

# 更新所有依赖
uv pip install --upgrade -e ".[dev]"

# 查看已安装
uv pip list

# 导出依赖
uv pip freeze
```

## 代码质量检查

```bash
# 代码格式化
black src/ tests/

# 检查格式（不修改）
black --check src/ tests/

# 代码检查
ruff check src/ tests/

# 自动修复问题
ruff check --fix src/ tests/

# 类型检查
mypy src/

# 运行所有质量检查
black src/ tests/ && ruff check src/ tests/ && mypy src/
```

## 测试命令

```bash
# 运行所有测试
pytest

# 详细输出
pytest -v

# 静默模式
pytest -q

# 显示测试执行时间
pytest --durations=10

# 运行特定文件
pytest tests/unit/test_status.py

# 运行特定测试函数
pytest tests/unit/test_status.py::test_import

# 运行匹配模式的测试
pytest -k "status"

# 带覆盖率报告
pytest --cov=cc_statusline

# 生成 HTML 报告
pytest --cov=cc_statusline --cov-report=html

# 查看缺失行
pytest --cov=cc_statusline --cov-report=term-missing

# 失败时立即停止
pytest -x

# 显示最慢的 N 个测试
pytest --durations=5

# 并行测试（需要 pytest-xdist）
pytest -n auto
```

## CLI 使用

```bash
# 运行模块
python -m cc_statusline

# 或使用安装的命令
cc-statusline

# 显示版本
python -c "import cc_statusline; print(cc_statusline.__version__)"
```

## 构建和发布

```bash
# 构建分发包
python -m build

# 检查分发包
twine check dist/*

# 发布到 PyPI（需配置凭证）
twine upload dist/*
```

## 常用 Git 命令

```bash
# 查看状态
git status

# 查看分支
git branch

# 创建功能分支
git checkout -b feature/your-feature

# 提交更改（使用中文）
git commit -m "新增: 实现功能描述"

# 推送
git push

# 创建标签
git tag -a v0.2.0 -m "版本 0.2.0"
```

## 验证命令

```bash
# 验证环境设置
./scripts/verify_setup.sh

# 验证包可导入
python -c "import cc_statusline; print(cc_statusline.__version__)"

# 清理缓存后测试
rm -rf .pytest_cache __pycache__ .coverage htmlcov
pytest
```

## 系统工具

```bash
# Darwin (macOS) 特定命令
# 查看 Python 版本
python3 --version

# 使用 uv 运行 Python
uv run python -c "..."

# 使用 uv 运行脚本
uv run pytest
```
