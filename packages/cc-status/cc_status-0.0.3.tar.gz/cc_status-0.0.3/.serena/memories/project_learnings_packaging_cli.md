# cc-statusline 项目学习和发现

## 项目架构模式

### Src Layout 设计
- **优势**: 强制使用安装后的包，避免开发环境污染
- **实践**: 所有源码位于 `src/cc_statusline/`
- **测试隔离**: 测试必须通过正确的包导入

### 模块化架构
```
cc-statusline/
├── config/       # 配置管理（installer, interactive）
├── engine/       # 核心引擎（statusline_engine, scheduler）
├── modules/      # 功能模块（mcp_status, session_time, registry）
├── render/       # 渲染系统（terminal_renderer）
├── theme/        # 主题系统（loader, builtins）
└── cli/          # 命令行接口（commands）
```

---

## Python 包发布流程

### 准备阶段
1. **���本号统一**: `pyproject.toml` 和 `__init__.py` 必须一致
2. **元数据完善**: classifiers, URLs, description
3. **依赖声明**: dependencies 和 optional-dependencies

### 构建阶段
```bash
# 安装构建工具
uv pip install build twine

# 清理旧构建
rm -rf dist/ build/

# 构建分发包
python -m build

# 检查质量
twine check dist/*
```

### 发布阶段
```bash
# TestPyPI 测试
twine upload --repository testpypi dist/*

# 正式发布
twine upload dist/*
```

---

## 交互式 CLI 开发

### prompt_toolkit 使用
```python
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.validation import Validator

# Tab 补全
completer = WordCompleter(choices, ignore_case=True)
user_input = prompt("提示: ", completer=completer)

# 输入验证
class CustomValidator(Validator):
    def validate(self, document):
        # 验证逻辑
        raise ValueError("错误信息") from None
```

### 最佳实践
1. **提供默认值**: 用户可直接回车使用
2. **支持取消**: 允许 'q' 或 Ctrl+C 退出
3. **即时反馈**: 错误提示要清晰
4. **预览功能**: 让用户看到效果再确认

---

## 配置文件设计

### YAML vs JSON
- **YAML**: 
  - ✅ 人类可读性强
  - ✅ 支持注释
  - ✅ 更简洁的语法
  - ❌ 解析速度稍慢

- **JSON**:
  - ✅ 解析速度快
  - ✅ 广泛支持
  - ❌ 不支持注释
  - ❌ 语法严格

### 配置迁移模式
```python
# 导出配置
export_data = {
    "version": __version__,
    "exported_at": datetime.now().isoformat(),
    "statusLine": config["statusLine"],
}

# 导入配置
if not force and "statusLine" in config:
    # 提示覆盖
    backup_config()  # 先备份
```

---

## 代码质量工具链

### 格式化：black
```bash
black src/ tests/
# 零配置，一致的代码风格
```

### 检查：ruff
```bash
ruff check src/ tests/
# 极快的 linter，合并多种工具
```

### 类型检查：mypy
```bash
mypy src/
# 静态类型检查，提前发现错误
```

### 复杂度控制
- 函数复杂度 > 10: 考虑拆分或添加 `# noqa: C901`
- 合理的复杂度可以接受（如验证函数）

---

## 类型注解技巧

### 类型守卫
```python
# 方法 1: assert isinstance
value = config["key"]
assert isinstance(value, str)
# 现在 mypy 知道 value 是 str

# 方法 2: cast
from typing import cast
value = cast(str, config["key"])
```

### 字典类型
```python
# 明确类型
config: dict[str, Any] = {"key": "value"}

# 类型不确定时
from typing import Any
result: dict[str, Any]
```

---

## Git 工作流规范

### 提交分类
- **feat**: 新功能（版本升级、新模块）
- **bugfix**: 缺陷修复
- **comment**: 文档、注释、格式化

### 提交信息格式
```
<类型>: <简短描述>

1. 功能模块 A
   - 详细说明 1
   - 详细说明 2

2. 功能模块 B
   - 详细说明 1

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```

---

## CI/CD 最佳实践

### GitHub Actions 工作流
```yaml
on:
  release:
    types: [published]  # Release 触发
  workflow_dispatch:     # 手动触发
    inputs:
      environment:       # 参数选择
```

### 安全性
- 使用 GitHub Secrets 存储 API Token
- Token 命名: `PYPI_API_TOKEN`, `TEST_PYPI_API_TOKEN`
- 永远不要提交 Token 到代码

---

## 测试策略

### 单元测试
```python
# 测试安装器
def test_install_success():
    assert ClaudeConfigInstaller.install(force=True)

# 测试验证功能
def test_verify_verbose():
    assert ClaudeConfigInstaller.verify(verbose=True)
```

### 测试组织
```
tests/
├── unit/          # 单元测试
│   ├── test_installer.py
│   └── test_status.py
└── integration/   # 集成测试
    └── test_cli.py
```

---

## 文档编写原则

### 实施报告
- ✅ 记录所有变更
- ✅ 包含验证结果
- ✅ 提供文件清单
- ✅ 列出下一步计划

### 使用指南
- ✅ 场景驱动的示例
- ✅ 故障排查指导
- ✅ 命令速查表
- ✅ 常见问题解答

---

## 性能优化技巧

### uv 包管理器
- **速度**: 比 pip 快 10-100 倍
- **确定性**: 依赖锁定更可靠
- **兼容性**: 与 pip 命令完全兼容

### 并行操作
```python
# 不好
for file in files:
    process(file)

# 好
import concurrent.futures
with ThreadPoolExecutor() as executor:
    executor.map(process, files)
```

---

## 项目管理技巧

### 版本控制
- **语义化版本**: MAJOR.MINOR.PATCH
- **0.2.0**: 标志性功能版本
- **版本一致性**: 所有地方保持同步

### 里程碑规划
- v0.1.0: 基础功能
- v0.2.0: 四项核心增强
- v0.3.0: 插件系统和主题扩展

---

## 关键收获

1. **Src Layout 是最佳实践**: 避免导入污染
2. **先测试再正式发布**: TestPyPI 非常重要
3. **交互式体验很重要**: prompt_toolkit 值得投入
4. **代码质量工具链**: black + ruff + mypy 三件套
5. **文档完整性**: 实施报告 + 使用指南缺一不可
6. **类型注解严格模式**: 使用 assert 和 cast 满足 mypy
7. **配置备份机制**: 任何修改前都先备份
8. **Git 提交规范**: 清晰的分类和详细的说明
