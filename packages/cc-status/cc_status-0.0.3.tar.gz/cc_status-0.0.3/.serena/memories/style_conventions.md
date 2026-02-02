# cc-statusline 代码风格和约定

## 语言规范

### 强制规则

- **所有交流必须使用中文**: 响应、解释、分析、建议、文档、注释都必须使用中文
- **代码注释优先使用中文**: 除非技术规范明确要求英文
- **变量名、函数名等标识符可以使用英文**: 遵循 Python 命名规范

## 代码风格

### 格式化配置 (black)

- **行长**: 100 字符
- **目标版本**: Python 3.9, 3.10, 3.11
- **配置位置**: `pyproject.toml` 的 `[tool.black]` 部分

```bash
# 格式化代码
black src/ tests/

# 检查格式
black --check src/ tests/
```

### 代码检查配置 (ruff)

- **行长**: 100 字符
- **目标版本**: Python 3.9
- **启用的规则集**:
  - E: pycodestyle errors
  - W: pycodestyle warnings
  - F: pyflakes
  - I: isort (导入排序)
  - C: flake8-comprehensions
  - B: flake8-bugbear
  - UP: pyupgrade

- **忽略规则**:
  - E501: line too long (由 black 处理)
  - B008: 不要在函数调用中执行函数调用作为默认参数

```bash
# 检查代码
ruff check src/ tests/

# 自动修复
ruff check --fix src/ tests/
```

### 类型检查配置 (mypy)

- **Python 版本**: 3.9
- **严格模式**: 启用
  - `warn_return_any`: true
  - `disallow_untyped_defs`: true
  - `disallow_incomplete_defs`: true
  - `no_implicit_optional`: true
  - `warn_redundant_casts`: true
  - `warn_unused_ignores`: true
  - `warn_no_return`: true
  - `strict_optional`: true

```bash
# 类型检查
mypy src/
```

## 命名约定

### Python 标识符

| 类型 | 约定 | 示例 |
|-----|------|------|
| 模块名 | snake_case | `status_manager.py` |
| 类名 | PascalCase | `StatusManager` |
| 函数名 | snake_case | `get_status()` |
| 变量名 | snake_case | `status_data` |
| 常量名 | UPPER_SNAKE_CASE | `DEFAULT_TIMEOUT` |
| 私有成员 | 前缀下划线 | `_private_method()` |

### 文件命名

- 使用小写字母、下划线和数字
- 遵循 snake_case 风格
- 测试文件以 `test_` 开头

## 文档字符串规范

### 公共函数和类

```python
def example_function(arg1: str, arg2: int) -> bool:
    """简要描述函数功能。

    详细描述函数的行为和用途。

    参数:
        arg1: 参数1的描述
        arg2: 参数2的描述

    返回:
        返回值的描述

    异常:
        ValueError: 何时抛出此异常
    """
    pass
```

### 私有方法

```python
def _private_method(self) -> None:
    """简短描述。"""
    pass
```

## 导入规范

### 导入顺序

1. 标准库导入
2. 第三方库导入
3. 本地应用程序导入

### 风格

```python
# 标准库
import os
import sys
from typing import Dict, List, Optional

# 第三方库
import requests
from pydantic import BaseModel

# 本地导入
from cc_statusline.core import StatusManager
from cc_statusline.config import Settings
```

## 测试规范

### 测试文件命名

- 文件名以 `test_` 开头
- 测试类以 `Test` 开头
- 测试函数以 `test_` 开头

### 测试风格

```python
import pytest
from cc_statusline.core.status import StatusManager


class TestStatusManager:
    """状态管理器测试类。"""

    def test_initial_state(self) -> None:
        """测试初始状态。"""
        manager = StatusManager()
        assert manager.state == "initialized"

    def test_status_update(self) -> None:
        """测试状态更新。"""
        manager = StatusManager()
        manager.update("active")
        assert manager.state == "active"
```

## 提交规范

### 提交信息格式

```
<类型>: <简短描述>

详细描述（可选）

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

### 类型标识

- `新增`: 新功能
- `修复`: Bug 修复
- `文档`: 文档更新
- `重构`: 代码重构
- `测试`: 测试相关
- `配置`: 配置或工具更新
- `性能`: 性能优化

## 文档命名规范

### 格式

```
YYYY-MM-DD_文档类型_文档名称_v版本号.扩展名
```

### 示例

```
2025-01-28_技术方案_用户认证_v1.0.md
2025-01-28_需求文档_订单管理_v2.1.md
2025-01-28_架构设计_微服务拆分_v1.0.md
```

### 文档类型

| 类型标识 | 适用场景 | 存放目录 |
|---------|---------|---------|
| `需求文档` | PRD、功能需求 | `.claude/docs/` |
| `技术方案` | 设计方案、实现方案 | `.claude/designs/` |
| `架构设计` | 系统架构、模块架构 | `.claude/architecture/` |
| `计划文档` | 开发计划、迭代计划 | `.claude/docs/` |
| `调研报告` | 技术调研、竞品分析 | `.claude/analysis/` |
| `数据模型` | ER图、表结构 | `.claude/model/` |
| `开发笔记` | 临时记录、备忘 | `.claude/notes/` |
| `问题日志` | Bug追踪、问题记录 | `.claude/logs/` |
