# CLAUDE.md

本文件为 Claude Code (claude.ai/code) 在此仓库中工作时提供指导。

## 🔴 强制规则 (CRITICAL RULE)

**必须使用中文进行所有交流和回答**

- ✅ 所有响应、解释、分析、建议必须使用中文
- ✅ 文档、注释、说明必须使用中文
- ✅ Git 提交信息必须使用中文
- ✅ 代码注释优先使用中文（除非技术规范明确要求英文）
- ✅ 变量名、函数名等标识符可以使用英文（遵循编程规范）
- ❌ 严禁使用英文进行交流和解释
- ⚠️ 这是强制性规则，无任何例外情况

## 🔴 文档存储强制规则 (DOCUMENT STORAGE RULE)

**所有文档必须存放在 `.claude` 目录下**

### 目录结构

```
.claude/
├── docs/           # 需求文档
├── designs/        # 方案设计文档
├── readmes/        # README 相关文档
├── modao/          # 页面原型图片（墨刀等工具导出）
├── model/          # 数据库表模型设计
├── architecture/   # 系统架构分析文档
├── notes/          # 开发笔记和临时记录
├── analysis/       # 代码分析和调研报告
└── logs/           # 开发日志和问题追踪
```

### 跨平台路径说明

| 系统 | 项目根目录下的 .claude 路径 |
|------|---------------------------|
| macOS/Linux | `./. claude/` 或 `$PROJECT_ROOT/.claude/` |
| Windows | `.\.claude\` 或 `%PROJECT_ROOT%\.claude\` |

### 文档分类规则

| 文档类型 | 存放目录 | 示例 |
|---------|---------|------|
| 产品需求文档 (PRD) | `.claude/docs/` | `prd_v1.0.md` |
| 功能需求说明 | `.claude/docs/` | `feature_auth.md` |
| 技术方案设计 | `.claude/designs/` | `design_api.md` |
| 架构设计图 | `.claude/designs/` | `arch_diagram.png` |
| 项目 README | `.claude/readmes/` | `readme_dev.md` |
| UI 原型截图 | `.claude/modao/` | `page_login.png` |
| 数据库 ER 图 | `.claude/model/` | `er_diagram.md` |
| 表结构定义 | `.claude/model/` | `schema_user.sql` |
| 架构分析报告 | `.claude/architecture/` | `analysis_microservice.md` |
| 开发笔记 | `.claude/notes/` | `note_2024_01.md` |
| 代码调研报告 | `.claude/analysis/` | `research_lib.md` |
| 问题追踪日志 | `.claude/logs/` | `issue_tracker.md` |

### 强制执行

- ✅ 所有项目相关文档必须放在 `.claude/` 目录下
- ✅ 按照上述分类存放到对应子目录
- ✅ 文件命名使用小写字母、下划线和数字
- ❌ 禁止在项目根目录散落文档文件
- ❌ 禁止在 `src/` 或 `tests/` 目录下存放非代码文档
- ⚠️ 此规则适用于所有由 Claude 创建或管理的文档

## 🔴 Python 包管理强制规则 (PYTHON PACKAGE RULE)

**必须使用 uv 作为 Python 包管理工具**

### 为什么选择 uv？

- ⚡ **极速**: 比 pip 快 10-100 倍的依赖解析和安装速度
- 🔒 **可靠**: 确定性的依赖锁定，避免环境不一致
- 🔄 **兼容**: 与 pip 命令完全兼容，学习成本低
- 📦 **现代**: Rust 编写，现代化的依赖管理体验

### 强制命令规范

| 操作 | ✅ 正确命令 | ❌ 禁止命令 |
|-----|-----------|-----------|
| 创建虚拟环境 | `uv venv` | `python -m venv` |
| 安装依赖 | `uv pip install` | `pip install` |
| 安装项目 | `uv pip install -e .` | `pip install -e .` |
| 安装开发依赖 | `uv pip install -e ".[dev]"` | `pip install -e ".[dev]"` |
| 更新依赖 | `uv pip install --upgrade` | `pip install --upgrade` |
| 卸载包 | `uv pip uninstall` | `pip uninstall` |
| 查看已安装 | `uv pip list` | `pip list` |
| 导出依赖 | `uv pip freeze` | `pip freeze` |

### 环境初始化标准流程

```bash
# 1. 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# 或
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# 2. 创建虚拟环境
uv venv

# 3. 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# 4. 安装项目依赖
uv pip install -e ".[dev]"
```

### 强制执行

- ✅ 所有 Python 依赖操作必须使用 `uv` 命令
- ✅ 项目文档中的安装说明必须使用 `uv` 命令
- ✅ CI/CD 脚本必须使用 `uv` 进行依赖安装
- ❌ 禁止直接使用 `pip` 命令
- ❌ 禁止使用 `python -m venv` 创建虚拟环境
- ❌ 禁止使用 `poetry`、`pipenv` 等其他包管理工具
- ⚠️ 此规则无任何例外情况

## 🔴 时间获取强制规则 (TIME RETRIEVAL RULE)

**需要时间信息时，必须使用 Time MCP 服务获取**

### 为什么强制使用 Time MCP？

- 🎯 **准确性**: 获取实时、准确的当前时间
- 🌍 **时区支持**: 正确处理不同时区的时间转换
- 🔄 **一致性**: 避免使用过期或假设的时间信息
- ⚠️ **避免幻觉**: 防止 AI 模型"猜测"当前时间

### 可用的 Time MCP 工具

| 工具 | 用途 | 示例 |
|-----|------|------|
| `mcp__time__get_current_time` | 获取指定时区的当前时间 | 获取北京时间 |
| `mcp__time__convert_time` | 时区之间的时间转换 | 北京时间转纽约时间 |

### 使用规范

```
# 获取当前时间（默认使用 Asia/Shanghai）
mcp__time__get_current_time(timezone="Asia/Shanghai")

# 获取其他时区时间
mcp__time__get_current_time(timezone="America/New_York")
mcp__time__get_current_time(timezone="Europe/London")

# 时区转换
mcp__time__convert_time(
    source_timezone="Asia/Shanghai",
    time="14:30",
    target_timezone="America/New_York"
)
```

### 常用时区标识

| 地区 | IANA 时区标识 |
|-----|--------------|
| 中国（北京/上海） | `Asia/Shanghai` |
| 日本（东京） | `Asia/Tokyo` |
| 美国东部 | `America/New_York` |
| 美国西部 | `America/Los_Angeles` |
| 英国（伦敦） | `Europe/London` |
| 德国（柏林） | `Europe/Berlin` |

### 强制执行

- ✅ 任何需要当前日期/时间的场景必须调用 Time MCP
- ✅ 涉及时区转换必须使用 `mcp__time__convert_time`
- ✅ 默认时区使用 `Asia/Shanghai`（中国用户）
- ❌ 禁止假设或"猜测"当前时间
- ❌ 禁止使用知识截止日期作为当前时间
- ❌ 禁止硬编码时间值
- ⚠️ 此规则无任何例外情况

## 🔴 代码检索强制规则 (CODE SEARCH RULE)

**代码检索时，必须优先使用 CCLSP MCP 服务**

### 为什么优先使用 CCLSP？

- 🎯 **精准性**: 基于 LSP 协议，提供语义级别的代码理解
- 🔍 **智能检索**: 支持符号定义、引用、实现等高级查询
- ⚡ **高效性**: 直接利用语言服务器的索引能力
- 🏗️ **结构化**: 返回结构化的代码信息，便于分析

### CCLSP 可用工具

| 工具 | 用途 | 优先级 |
|-----|------|-------|
| `mcp__cclsp__find_definition` | 查找符号定义 | 🥇 最高 |
| `mcp__cclsp__find_references` | 查找符号引用 | 🥇 最高 |
| `mcp__cclsp__find_workspace_symbols` | 工作区符号搜索 | 🥇 最高 |
| `mcp__cclsp__find_implementation` | 查找接口实现 | 🥇 最高 |
| `mcp__cclsp__get_hover` | 获取符号悬停信息 | 🥇 最高 |
| `mcp__cclsp__get_diagnostics` | 获取诊断信息 | 🥇 最高 |
| `mcp__cclsp__get_incoming_calls` | 查找调用者 | 🥇 最高 |
| `mcp__cclsp__get_outgoing_calls` | 查找被调用函数 | 🥇 最高 |
| `mcp__cclsp__rename_symbol` | 重命名符号 | 🥇 最高 |

### 检索优先级顺序

```
1️⃣ CCLSP MCP（最高优先级）
   ↓ 检索失败或不适用
2️⃣ Serena MCP（语义代码理解）
   ↓ 检索失败或不适用
3️⃣ Grep / Glob（文本模式匹配）
   ↓ 检索失败或不适用
4️⃣ Task Agent（复杂探索任务）
```

### 使用场景对照

| 场景 | 首选工具 | 备选工具 |
|-----|---------|---------|
| 查找函数/类定义 | `mcp__cclsp__find_definition` | `mcp__serena__find_symbol` |
| 查找符号引用 | `mcp__cclsp__find_references` | `mcp__serena__find_referencing_symbols` |
| 搜索工作区符号 | `mcp__cclsp__find_workspace_symbols` | `mcp__serena__search_for_pattern` |
| 查找接口实现 | `mcp__cclsp__find_implementation` | `mcp__serena__find_symbol` |
| 获取类型信息 | `mcp__cclsp__get_hover` | `mcp__serena__find_symbol` (include_info) |
| 查看调用关系 | `mcp__cclsp__get_incoming_calls` | `mcp__serena__find_referencing_symbols` |
| 文本模式搜索 | - | `Grep` / `mcp__serena__search_for_pattern` |

### 强制执行

- ✅ 代码检索必须首先尝试 CCLSP MCP 工具
- ✅ CCLSP 失败后，按优先级顺序尝试其他工具
- ✅ 记录检索路径，说明为何使用备选工具
- ❌ 禁止跳过 CCLSP 直接使用其他检索工具
- ❌ 禁止在 CCLSP 可用时使用低效的文本搜索
- ⚠️ 仅当 CCLSP 明确不支持该语言或返回空结果时，才可使用备选工具

## 🔴 文档命名强制规则 (DOCUMENT NAMING RULE)

**所有文档必须遵循统一命名规范**

### 命名格式标准

| 文档类型 | 命名格式 | 说明 |
|---------|---------|------|
| **标准文档** | `YYYY-MM-DD_文档类型_文档名称_v版本号.扩展名` | 通用格式 |
| **计划文档** | `YYYY-MM-DD_计划文档_计划类型_具体内容_v版本号.md` | Plan 专用 |
| **临时笔记** | `YYYY-MM-DD_简短描述.md` | 简化格式 |

### 命名示例

```
# 标准文档示例
2025-01-28_技术方案_用户认证_v1.0.md
2025-01-28_需求文档_订单管理_v2.1.md
2025-01-28_架构设计_微服务拆分_v1.0.md
2025-01-28_调研报告_前端框架选型_v1.0.md

# 计划文档示例
2025-01-28_计划文档_项目开发_用户认证模块_v1.0.md
2025-01-28_计划文档_迭代计划_Sprint3_v1.0.md
2025-01-28_计划文档_发布计划_v2.0上线_v1.0.md

# 临时笔记示例
2025-01-28_会议记录.md
2025-01-28_问题排查.md
2025-01-28_想法草稿.md
```

### 命名组成说明

| 组成部分 | 格式要求 | 示例 |
|---------|---------|------|
| 日期 | `YYYY-MM-DD` | `2025-01-28` |
| 文档类型 | 中文，2-4字 | `技术方案`、`需求文档`、`架构设计` |
| 文档名称 | 中文，简明扼要 | `用户认证`、`订单管理` |
| 版本号 | `v主版本.次版本` | `v1.0`、`v2.1` |
| 扩展名 | 小写 | `.md`、`.png`、`.sql` |

### 常用文档类型

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

### 版本号规则

| 变更类型 | 版本变化 | 示例 |
|---------|---------|------|
| 重大修改/重写 | 主版本号 +1 | `v1.0` → `v2.0` |
| 内容更新/补充 | 次版本号 +1 | `v1.0` → `v1.1` |
| 初始版本 | 从 `v1.0` 开始 | `v1.0` |

### 强制执行

- ✅ 所有新建文档必须遵循命名规范
- ✅ 日期必须使用 Time MCP 获取当前真实日期
- ✅ 版本号必须从 `v1.0` 开始，按规则递增
- ✅ 文档类型必须使用中文标识
- ❌ 禁止使用随意命名（如 `doc1.md`、`新建文档.md`）
- ❌ 禁止省略日期前缀
- ❌ 禁止使用英文文档类型标识
- ⚠️ 此规则适用于 `.claude/` 目录下的所有文档

## 项目概述

**cc-status** - Claude Code 状态栏功能相关的仓库

**当前状态**: ✅ 项目已完成初始化，基础架构就绪

**许可证**: Apache License 2.0

## 项目初始化指南

当开始实施代码时，需要确定并建立以下内容：

### 1. 技术栈决策

需要明确的技术选型：
- 编程语言（TypeScript/JavaScript/Python 等）
- 运行时环境（Node.js/Deno/Bun 等）
- 构建工具（Vite/Rollup/esbuild 等）
- 测试框架（Jest/Vitest/Pytest 等）
- 包管理器（npm/pnpm/yarn 等）

### 2. 项目结构规划

建议的标准目录结构：

```
cc-status/
├── src/              # 源代码目录
├── tests/            # 测试文件目录
├── docs/             # 文档目录
├── examples/         # 示例代码
├── scripts/          # 构建和工具脚本
└── dist/             # 构建输出目录（.gitignore）
```

### 3. 必要的配置文件

根据选定的技术栈，需要创建：

**JavaScript/TypeScript 项目**:
- `package.json` - 依赖管理
- `tsconfig.json` - TypeScript 配置
- `.gitignore` - Git 忽略规则
- `eslint.config.js` - 代码规范
- `vitest.config.ts` - 测试配置

**Python 项目**:
- `pyproject.toml` - 项目配置
- `requirements.txt` 或 `poetry.lock` - 依赖管理
- `.gitignore` - Git 忽略规则
- `pytest.ini` - 测试配置

### 4. 开发流程约定

需要建立的开发规范：
- 分支管理策略（Git Flow/GitHub Flow）
- 提交信息规范（使用中文，格式统一）
- 代码审查流程
- CI/CD 配置（GitHub Actions/GitLab CI）

## 待完成事项

✅ 项目已完成初始化！以下内容已添加。

---

## 项目配置

### 技术栈

- **语言**: Python 3.9+（推荐 3.11）
- **包管理器**: uv
- **项目布局**: Src Layout（源码位于 `src/` 目录）
- **测试框架**: pytest + pytest-cov
- **代码格式化**: black（行长 100）
- **代码检查**: ruff
- **类型检查**: mypy
- **构建工具**: hatchling

### 项目结构

```
cc-status/
├── src/cc_status/      # 源代码（Src Layout）
│   ├── __init__.py         # 包初始化和版本信息
│   ├── __main__.py         # CLI 入口点
│   ├── core/               # 核心业务逻辑
│   │   ├── status.py       # 状态管理（待实现）
│   │   └── formatter.py    # 格式化输出（待实现）
│   ├── config/             # 配置管理
│   │   └── settings.py     # 配置加载（待实现）
│   └── cli/                # 命令行接口
│       └── commands.py     # CLI 命令（待实现）
├── tests/                  # 测试文件
│   ├── conftest.py         # pytest 配置
│   ├── unit/               # 单元测试
│   └── integration/        # 集成测试
├── docs/                   # 文档目录
├── scripts/                # 工具脚本
│   └── verify_setup.sh     # 环境验证脚本
├── examples/               # 使用示例
├── pyproject.toml          # 项目配置和依赖
├── .python-version         # Python 版本（3.11）
└── .gitignore              # Git 忽略规则
```

## 构建命令

### 环境初始化

```bash
# 安装 uv（如未安装）
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境
uv venv

# 激活虚拟环境
source .venv/bin/activate  # macOS/Linux
# 或
.venv\Scripts\activate     # Windows

# 安装依赖
uv pip install -e ".[dev]"
```

### 依赖管理

```bash
# 安装项目（可编辑模式）
uv pip install -e .

# 安装开发依赖
uv pip install -e ".[dev]"

# 更新所有依赖
uv pip install --upgrade -e ".[dev]"
```

### 构建和发布

```bash
# 构建分发包
python -m build

# 检查分发包
twine check dist/*

# 发布到 PyPI（需配置凭证）
twine upload dist/*
```

## 开发命令

### 代码质量检���

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

### 基础测试

```bash
# 运行所有测试
pytest

# 详细输出
pytest -v

# 静默模式
pytest -q

# 显示测试执行时间
pytest --durations=10
```

### 特定测试

```bash
# 运行特定文件
pytest tests/unit/test_status.py

# 运行特定测试函数
pytest tests/unit/test_status.py::test_import

# 运行匹配模式的测试
pytest -k "status"
```

### 覆盖率测试

```bash
# 带覆盖率报告
pytest --cov=cc_status

# 生成 HTML 报告
pytest --cov=cc_status --cov-report=html

# 查看缺失行
pytest --cov=cc_status --cov-report=term-missing
```

### 其他测试选项

```bash
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
python -m cc_status

# 或使用安装的命令
cc-status

# 显示版本
python -c "import cc_status; print(cc_status.__version__)"
```

## 代码架构说明

### 模块划分

1. **cc_status（根包）**
   - 提供版本信息和包级导出
   - `__version__`、`__author__`、`__license__` 等元数据

2. **cc_status.core（核心模块）**
   - `status.py`：状态管理核心逻辑（待实现）
   - `formatter.py`：格式化输出工具（待实现）
   - 职责：业务逻辑和数据处理

3. **cc_status.config（配置模块）**
   - `settings.py`：配置加载和管理（待实现）
   - 职责：配置文件读取、环境变量处理

4. **cc_status.cli（命令行接口）**
   - `commands.py`：CLI 命令实现（待实现）
   - 职责：用户交互和命令调度

### 依赖关系

```
cli.commands → core.status → core.formatter
             ↘ config.settings ↗
```

- CLI 层调用核心业务逻辑
- 配置模块被核心和 CLI 共同使用
- 核心模块之间可以相互调用
- 避免循环依赖

### 设计模式

- **Src Layout**: 源码隔离，避免导入污染
- **模块化设计**: 单一职责原则，清晰的模块边界
- **依赖注入**: 配置通过参数传递，便于测试
- **类型提示**: 使用 Python 类型注解，mypy 静态检查

## 技术决策记录

### 为什么选择 Python？

- **原因**:
  - 简洁易读，适合 CLI 工具开发
  - 丰富的生态系统和库支持
  - 跨平台兼容性好
  - 与 Claude Code 集成友好

### 为什么选择 uv？

- **原因**:
  - 极快的依赖解析和安装速度
  - 与 pip 兼容的接口
  - 现代化的依赖管理体验
  - 项目隔离和版本锁定

### 为什么选择 Src Layout？

- **原因**:
  - 避免测试时导入开发版本的污染
  - 强制使用安装后的包进行测试
  - 更接近用户实际使用场景
  - 清晰的源码和测试边界

### 为什么选择这些工具？

- **black**: 零配置，一致的代码风格，社区标准
- **ruff**: 极快的检查速度，合并多种 linter 功能
- **mypy**: 静态类型检查，提前发现类型错误
- **pytest**: 简洁的测试语法，强大的 fixture 系统

### 已知限制

- **Python 版本**: 需要 >= 3.9（使用了 dict[str, Any] 等现代语法）
- **依赖管理**: 依赖 uv，用户需要预先安装
- **跨平台**: 脚本需要针对 Windows 进行适配

### 性能优化策略

- **延迟导入**: 减少启动时间
- **类型缓存**: 使用 mypy cache 加速重复检查
- **测试并行**: 可使用 pytest-xdist 并行测试
- **依赖最小化**: 核心功能零依赖，可选功能独立

## 开发工作流

### 初次设置

1. 克隆仓库并进入目录
2. 安装 uv：`curl -LsSf https://astral.sh/uv/install.sh | sh`
3. 创建虚拟环境：`uv venv`
4. 激活虚拟环境：`source .venv/bin/activate`
5. 安装依赖：`uv pip install -e ".[dev]"`
6. 验证设置：`./scripts/verify_setup.sh`

### 日常开发

1. 激活虚拟环境
2. 创建功能分支：`git checkout -b feature/your-feature`
3. 编写代码和测试
4. 运行质量检查：`black src/ tests/ && ruff check src/ tests/ && mypy src/`
5. 运行测试：`pytest`
6. 提交更改（使用中文）

### 提交规范

格式：`<类型>: <简短描述>`

类型：
- `新增`: 新功能
- `修复`: Bug 修复
- `文档`: 文档更新
- `重构`: 代码重构
- `测试`: 测试相关
- `配置`: 配置或工具更新
- `性能`: 性能优化

示例：
```bash
git commit -m "新增: 实现状态管理核心功能

- 添加 StatusManager 类
- 实现状态获取和更新方法
- 添加对应的单元测试

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
"
```

### 发布流程

1. 更新 CHANGELOG.md
2. 更新版本号（pyproject.toml 和 __init__.py）
3. 运行完整测试套件
4. 创建 Git 标签：`git tag -a v0.2.0 -m "版本 0.2.0"`
5. 构建分发包：`python -m build`
6. 推送到仓库：`git push && git push --tags`
7. 发布到 PyPI：`twine upload dist/*`

## 常见问题解决

### 虚拟环境问题

```bash
# 删除并重建虚拟环境
rm -rf .venv
uv venv
source .venv/bin/activate
uv pip install -e ".[dev]"
```

### 导入错误

```bash
# 确保以可编辑模式安装
uv pip install -e .

# 检查 PYTHONPATH
echo $PYTHONPATH

# 验证包可导入
python -c "import cc_status; print(cc_status.__version__)"
```

### 测试失败

```bash
# 查看详细错误
pytest -vv

# 清理缓存
rm -rf .pytest_cache __pycache__ .coverage htmlcov
pytest
```

### 类型检查错误

```bash
# 清理 mypy 缓存
rm -rf .mypy_cache
mypy src/

# 忽略特定文件（在 pyproject.toml 中配置）
```

## 开发建议

在实施代码之前，建议：

1. 阅读 README.md，明确项目目标
2. 确定目标用户和使用场景
3. 设计 API 接口和数据结构
4. 编写技术设计文档
5. 创建项目里程碑和任务清单

---

**注意**: 本文件应在项目实施的第一时间进行更新，反映实际的架构和开发实践。
