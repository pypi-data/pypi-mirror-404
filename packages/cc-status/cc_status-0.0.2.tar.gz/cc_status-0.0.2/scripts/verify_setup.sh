#!/bin/bash
set -e

echo "=== cc-status 初始化验证 ==="
echo ""

# 1. 检查目录结构
if [ -d "src/cc_status" ]; then
    echo "✅ 目录结构正确"
else
    echo "❌ 目录结构错误"
    exit 1
fi

# 2. 检查虚拟环境
if [ -d ".venv" ]; then
    echo "✅ 虚拟环境已创建"
else
    echo "❌ 虚拟环境未创建"
    exit 1
fi

# 3. 激活虚拟环境并检查依赖安装
source .venv/bin/activate

if python -c "import pytest, black, ruff" 2>/dev/null; then
    echo "✅ 依赖已安装"
else
    echo "❌ 依赖未安装"
    exit 1
fi

# 4. 检查包导入
VERSION=$(python -c "import cc_status; print(cc_status.__version__)" 2>/dev/null)
if [ "$VERSION" = "0.1.0" ]; then
    echo "✅ 包可导入（版本：$VERSION）"
else
    echo "❌ 包无法导入或版本错误"
    exit 1
fi

# 5. 运行测试
if pytest -q --no-cov >/dev/null 2>&1; then
    echo "✅ 测试通过"
else
    echo "❌ 测试失败"
    pytest -q --no-cov
    exit 1
fi

# 6. 代码质量检查
if black --check src/ tests/ >/dev/null 2>&1 && ruff check src/ tests/ >/dev/null 2>&1; then
    echo "✅ 代码质量通过"
else
    echo "❌ 代码质量检查失败"
    exit 1
fi

echo ""
echo "=== ✅ 初始化验证完成 ==="
