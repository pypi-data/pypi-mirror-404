# Claude Code StatusLine 配置方法调研报告

## 📋 文档信息

- **文档类型**: 调研报告
- **创建日期**: 2026-01-28
- **版本**: v1.0
- **调研对象**: Claude Code CLI 工具的 StatusLine 功能
- **目标**: 了解如何在 Claude Code 中启用和配置自定义状态栏

---

## 🎯 调研目标

本次调研旨在明确以下问题：

1. Claude Code StatusLine 是什么？
2. 如何启用和配置 StatusLine？
3. 有哪些现成的 StatusLine 工具和插件？
4. 配置文件的位置和格式是什么？

---

## 📊 核心发现

### 1. StatusLine 功能概述

**StatusLine** 是 Claude Code CLI 工具提供的一个自定义状态栏功能，类似于终端提示符（PS1）在 Oh-my-zsh 等 Shell 中的作用。

**主要特性**：
- 显示在 Claude Code 界面底部
- 可展示上下文信息（模型、Git状态、使用量等）
- 通过命令动态生成内容
- 支持完全自定义

---

## 🔧 配置方法

### 方法一：使用 `/statusline` 命令（推荐）

这是最简单的配置方式，Claude Code 会自动帮你设置状态栏。

```bash
# 基础命令
/statusline

# 带自定义指令
/statusline show the model name in orange
/statusline 显示 Git 分支和 Token 使用量
```

**工作原理**：
- Claude Code 会尝试复制你的终端提示符样式
- 你可以提供额外的自定义需求
- 自动生成配置并写入 `settings.json`

### 方法二：手动编辑 `settings.json`

**配置文件位置**（按优先级）：
1. **Local 作用域**（最高优先级）：`.claude/*.local.*` - 仅本项目本人可见
2. **Project 作用域**：`.claude/settings.json` - 项目团队共享
3. **User 作用域**：`~/.claude/settings.json` 或 `~/.config/claude/settings.json` - 全局个人配置
4. **Managed 作用域**（系统级，无法覆盖）：
   - macOS: `/Library/Application Support/ClaudeCode/`
   - Linux/WSL: `/etc/claude-code/`
   - Windows: `C:\Program Files\ClaudeCode\`

**基础配置结构**：

```json
{
  "statusLine": {
    "type": "command",
    "command": "你的命令或脚本路径",
    "padding": 0
  }
}
```

**配置参数说明**：

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `type` | string | 是 | 固定为 `"command"` |
| `command` | string | 是 | 生成状态栏的命令或脚本路径 |
| `padding` | number | 否 | 左右边距，设为 0 可让状态栏延伸到边缘 |

---

## 🎨 StatusLine 命令工作原理

### JSON 输入结构

Claude Code 会通过 **stdin** 向你的命令传递 JSON 格式的上下文信息：

```json
{
  "cwd": "/path/to/current/directory",
  "gitBranch": "main",
  "gitStatus": {
    "ahead": 2,
    "behind": 0,
    "modified": 3,
    "staged": 1
  },
  "model": "claude-sonnet-4.5",
  "contextWindow": {
    "used": 15000,
    "total": 200000,
    "percentage": 7.5
  },
  "tokenUsage": {
    "input": 12000,
    "output": 3000
  }
}
```

### 命令要求

1. 从 **stdin** 读取 JSON 数据
2. 解析并提取所需信息
3. 将格式化后的状态栏输出到 **stdout**
4. 支持 ANSI 颜色代码

---

## 🛠️ 现成工具和插件

### 1. **ccusage** - 使用量追踪工具

**GitHub**: https://ccusage.com

**特性**：
- ✅ 实时 Token 使用量显示
- ✅ 成本追踪（基于 LiteLLM 定价）
- ✅ 日预算和警告
- ✅ 支持离线模式（缓存定价数据）

**安装配置**：

```json
{
  "statusLine": {
    "type": "command",
    "command": "bun x ccusage statusline",  // 或 "npx -y ccusage statusline"
    "padding": 0
  }
}
```

**在线模式**（可选，获取最新定价）：

```json
{
  "statusLine": {
    "type": "command",
    "command": "bun x ccusage statusline --online",
    "padding": 0
  }
}
```

**显示内容**：
```
💰 $2.45/day (24%) | 🪟 15K/200K (7%) | 🤖 claude-sonnet-4.5
```

---

### 2. **claude-code-usage-bar** - 实时使用栏

**GitHub**: https://github.com/leeguooooo/claude-code-usage-bar

**特性**：
- ✅ Token 使用量实时追踪
- ✅ 剩余预算显示
- ✅ 消耗速率计算
- ✅ 预估耗尽时间

**安装配置**：

```bash
# 安装
npm install -g claude-code-usage-bar

# 或使用 npx 运行
npx claude-code-usage-bar
```

**配置示例**：

```json
{
  "statusLine": {
    "type": "command",
    "command": "npx -y claude-code-usage-bar",
    "padding": 0
  }
}
```

---

### 3. **claude-powerline** - Vim 风格状态栏

**GitHub**: https://github.com/Owloops/claude-powerline

**特性**：
- ✅ Vim Powerline 风格设计
- ✅ Git 集成（分支、提交、状态）
- ✅ 使用量追踪
- ✅ 多主题支持（Dark/Light）
- ✅ 自定义配置

**安装配置**：

```bash
# 安装
npm install -g claude-powerline

# 配置
claude-powerline init
```

**配置示例**：

```json
{
  "statusLine": {
    "type": "command",
    "command": "claude-powerline",
    "padding": 0
  }
}
```

**功能亮点**：
- 分支状态显示
- 领先/落后提交数
- 工作树变更
- 仓库信息
- 滚动窗口和日预算百分比警报

---

### 4. **pyccsl** - Python 实现的状态栏

**GitHub**: https://github.com/wolfdenpublishing/pyccsl

**特性**：
- ✅ Python 编写（无依赖）
- ✅ 实时指标显示
- ✅ 成本追踪
- ✅ Git 状态
- ✅ Token 使用量
- ✅ 9 种主题
- ✅ PowerLine 字体支持

**安装配置**：

```bash
# 下载脚本
curl -o ~/.claude/pyccsl.py https://raw.githubusercontent.com/wolfdenpublishing/pyccsl/main/pyccsl.py
chmod +x ~/.claude/pyccsl.py

# 配置环境变量（可选）
cp pyccsl.env.example pyccsl.env
# 编辑 pyccsl.env 文件
```

**配置示例**：

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude/pyccsl.py",
    "padding": 0
  }
}
```

---

### 5. **CCometixLine** - Rust 高性能状态栏

**GitHub**: https://github.com/Haleclipse/CCometixLine

**特性**：
- ✅ Rust 编写（高性能）
- ✅ Git 集成（分支、状态、追踪信息）
- ✅ 使用量追踪（基于 transcript 分析）
- ✅ 交互式 TUI 配置
- ✅ 段落自定义
- ✅ 配置管理（init、check、edit）
- ✅ Claude Code 增强工具

**安装配置**：

```bash
# 通过 npm 安装
npm install -g ccometixline

# 初始化配置
ccometixline init
```

**配置示例**：

```json
{
  "statusLine": {
    "type": "command",
    "command": "ccometixline",
    "padding": 0
  }
}
```

**显示内容**：
```
Model | Directory | Git Branch Status | Context Window Information
```

---

## 📝 自定义脚本示例

### 简单状态栏（Bash）

```bash
#!/bin/bash
# 文件: ~/.claude/statusline.sh

# 读取 JSON 输入
read -r input

# 解析 JSON（需要 jq）
cwd=$(echo "$input" | jq -r '.cwd')
branch=$(echo "$input" | jq -r '.gitBranch')
model=$(echo "$input" | jq -r '.model')

# 输出状态栏
echo "📁 $(basename "$cwd") | 🔀 $branch | 🤖 $model"
```

**配置**：

```json
{
  "statusLine": {
    "type": "command",
    "command": "~/.claude/statusline.sh",
    "padding": 0
  }
}
```

---

### Git 感知状态栏（Bash）

```bash
#!/bin/bash
# 文件: ~/.claude/git-statusline.sh

read -r input

cwd=$(echo "$input" | jq -r '.cwd')
branch=$(echo "$input" | jq -r '.gitBranch // "no-git"')
modified=$(echo "$input" | jq -r '.gitStatus.modified // 0')
staged=$(echo "$input" | jq -r '.gitStatus.staged // 0')

# 颜色代码
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

status=""
if [ "$modified" -gt 0 ]; then
  status="${YELLOW}M:$modified${NC}"
fi
if [ "$staged" -gt 0 ]; then
  status="$status ${GREEN}S:$staged${NC}"
fi

echo -e "📁 $(basename "$cwd") | 🔀 $branch $status"
```

---

### Python 示例

```python
#!/usr/bin/env python3
# 文件: ~/.claude/statusline.py

import sys
import json
import os

# 读取 JSON 输入
input_data = json.load(sys.stdin)

# 提取信息
cwd = os.path.basename(input_data.get('cwd', ''))
branch = input_data.get('gitBranch', 'no-git')
model = input_data.get('model', 'unknown')
ctx = input_data.get('contextWindow', {})

# 计算使用百分比
used = ctx.get('used', 0)
total = ctx.get('total', 1)
percentage = (used / total) * 100 if total > 0 else 0

# ANSI 颜色
GREEN = '\033[0;32m'
YELLOW = '\033[1;33m'
RED = '\033[0;31m'
NC = '\033[0m'

# 根据使用率选择颜色
if percentage < 50:
    color = GREEN
elif percentage < 75:
    color = YELLOW
else:
    color = RED

# 输出状态栏
print(f"📁 {cwd} | 🔀 {branch} | 🪟 {color}{percentage:.1f}%{NC} | 🤖 {model}")
```

---

### Node.js 示例

```javascript
#!/usr/bin/env node
// 文件: ~/.claude/statusline.js

const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
  terminal: false
});

rl.on('line', (line) => {
  const data = JSON.parse(line);

  const cwd = data.cwd.split('/').pop();
  const branch = data.gitBranch || 'no-git';
  const model = data.model || 'unknown';
  const ctx = data.contextWindow || {};

  const percentage = ctx.total > 0
    ? ((ctx.used / ctx.total) * 100).toFixed(1)
    : 0;

  // ANSI 颜色
  const GREEN = '\x1b[32m';
  const YELLOW = '\x1b[33m';
  const RED = '\x1b[31m';
  const RESET = '\x1b[0m';

  let color = GREEN;
  if (percentage >= 75) color = RED;
  else if (percentage >= 50) color = YELLOW;

  console.log(`📁 ${cwd} | 🔀 ${branch} | 🪟 ${color}${percentage}%${RESET} | 🤖 ${model}`);
});
```

---

## 🎨 Helper 函数方法

为了简化开发，可以创建辅助函数来解析输入：

```bash
# 文件: ~/.claude/statusline-helpers.sh

parse_statusline_input() {
  local input="$1"

  export CWD=$(echo "$input" | jq -r '.cwd')
  export GIT_BRANCH=$(echo "$input" | jq -r '.gitBranch // "no-git"')
  export MODEL=$(echo "$input" | jq -r '.model')
  export CTX_USED=$(echo "$input" | jq -r '.contextWindow.used // 0')
  export CTX_TOTAL=$(echo "$input" | jq -r '.contextWindow.total // 1')
}

# 使用示例
read -r input
parse_statusline_input "$input"
echo "📁 $(basename "$CWD") | 🔀 $GIT_BRANCH | 🤖 $MODEL"
```

---

## 📊 工具对比表

| 工具 | 语言 | 特性 | 依赖 | 推荐度 |
|------|------|------|------|--------|
| **ccusage** | TypeScript | 成本追踪、离线模式、日预算 | Node.js | ⭐⭐⭐⭐⭐ |
| **claude-code-usage-bar** | JavaScript | 使用量追踪、速率计算 | Node.js | ⭐⭐⭐⭐ |
| **claude-powerline** | TypeScript | Powerline 风格、多主题 | Node.js | ⭐⭐⭐⭐⭐ |
| **pyccsl** | Python | 零依赖、9 主题、PowerLine 字体 | Python 3.8+ | ⭐⭐⭐⭐ |
| **CCometixLine** | Rust | 高性能、TUI 配置、增强工具 | Rust（编译后无依赖） | ⭐⭐⭐⭐⭐ |

---

## 🔍 上下文窗口使用量显示

### 为什么重要？

- **避免超出限制**：及时了解 Token 使用情况
- **优化成本**：监控 API 消耗
- **改进提示**：根据使用量调整上下文

### 配置示例

```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude/ctx-monitor.py",
    "padding": 0
  }
}
```

**ctx-monitor.py**：

```python
#!/usr/bin/env python3
import sys, json

data = json.load(sys.stdin)
ctx = data.get('contextWindow', {})
used, total = ctx.get('used', 0), ctx.get('total', 1)
pct = (used / total) * 100 if total > 0 else 0

color = '\033[32m' if pct < 50 else '\033[33m' if pct < 75 else '\033[31m'
print(f"🪟 {color}{used:,}/{total:,} ({pct:.1f}%)\033[0m")
```

---

## 🐛 常见问题排查

### 1. StatusLine 不显示

**可能原因**：
- 命令路径错误
- 脚本没有执行权限
- JSON 解析失败

**解决方法**：

```bash
# 检查脚本权限
ls -l ~/.claude/statusline.sh

# 添加执行权限
chmod +x ~/.claude/statusline.sh

# 测试脚本（手动传入 JSON）
echo '{"cwd":"/test","gitBranch":"main","model":"claude-sonnet-4.5"}' | ~/.claude/statusline.sh
```

---

### 2. 颜色显示异常

**可能原因**：
- 终端不支持 ANSI 颜色
- 颜色代码格式错误

**解决方法**：

```bash
# 测试终端颜色支持
echo -e "\033[32mGreen\033[0m \033[33mYellow\033[0m \033[31mRed\033[0m"

# 简化颜色使用或禁用颜色
```

---

### 3. JSON 解析错误

**可能原因**：
- 缺少 `jq` 工具
- JSON 格式不正确

**解决方法**：

```bash
# 安装 jq
# macOS
brew install jq

# Ubuntu/Debian
sudo apt install jq

# 测试 JSON 解析
echo '{"test":"value"}' | jq '.test'
```

---

### 4. 性能问题

**可能原因**：
- 脚本执行时间过长
- 过多的外部命令调用

**解决方法**：

1. **缓存数据**：避免每次都重新计算
2. **使用编译语言**：Rust > Python > Bash
3. **减少外部调用**：尽量使用内置功能
4. **异步更新**：后台更新缓存

---

## 💡 最佳实践

### 1. 保持简洁

状态栏应该简洁明了，避免过多信息：

✅ **推荐**：
```
📁 my-project | 🔀 main | 🪟 7.5% | 🤖 sonnet-4.5
```

❌ **不推荐**：
```
Directory: /home/user/projects/my-project | Git Branch: main (2 commits ahead, 3 modified files) | Context: 15000/200000 tokens (7.5%) | Model: claude-sonnet-4.5-20250929 | Cost: $2.45
```

---

### 2. 使用颜色编码

通过颜色快速传达状态：

- 🟢 **绿色**：正常（< 50% 使用率）
- 🟡 **黄色**：警告（50-75% 使用率）
- 🔴 **红色**：危险（> 75% 使用率）

---

### 3. 错误处理

确保脚本能处理缺失或异常数据：

```python
# 安全的 JSON 解析
try:
    data = json.load(sys.stdin)
except json.JSONDecodeError:
    print("❌ StatusLine Error")
    sys.exit(0)

# 提供默认值
cwd = data.get('cwd', 'unknown')
branch = data.get('gitBranch', 'no-git')
```

---

### 4. 版本控制

将配置纳入版本控制（项目作用域）：

```bash
# 提交到 Git
git add .claude/settings.json
git commit -m "配置: 添加自定义 StatusLine"

# 或忽略本地配置
echo ".claude/*.local.*" >> .gitignore
```

---

### 5. 文档说明

在项目 README 中说明 StatusLine 配置：

```markdown
## StatusLine 配置

本项目使用自定义 StatusLine 显示：
- 📁 当前目录
- 🔀 Git 分支
- 🪟 上下文窗口使用率
- 🤖 当前模型

配置文件：`.claude/settings.json`
脚本位置：`.claude/scripts/statusline.sh`
```

---

## 🎓 学习资源

### 官方文档

- **StatusLine 配置文档**：https://code.claude.com/docs/en/statusline
- **Settings 配置文档**：https://docs.anthropic.com/zh-CN/docs/claude-code/settings
- **插件系统文档**：https://code.claude.com/docs/zh-CN/plugins

### 开源项目

- **awesome-claude-code**：https://github.com/hesreallyhim/awesome-claude-code
  - 精选的命令、文件和工作流列表

- **Claude Code 生态指南**：https://blog.csdn.net/weixin_42616808/article/details/150706512
  - GitHub 上最热门的 17 个开源项目

### 社区资源

- **CSDN 博客系列**：
  - [Claude Code 入门指南](https://blog.csdn.net/qq_38628046/article/details/149632014)
  - [Claude Code 使用及配置智能体](https://blog.csdn.net/2401_85252837/article/details/150793888)

- **B站视频教程**：
  - [【2026最新版】Claude Code 从入门到精通](https://www.bilibili.com/video/BV1aWqZBkEYR/)

---

## 🚀 快速开始推荐

### 新手推荐：使用 `/statusline` 命令

```bash
# 启动 Claude Code
claude

# 在交互界面运行
/statusline 显示目录、Git分支和上下文使用率
```

### 进阶推荐：安装 ccusage

```bash
# 编辑配置文件
vim ~/.claude/settings.json

# 添加配置
{
  "statusLine": {
    "type": "command",
    "command": "bun x ccusage statusline",
    "padding": 0
  }
}

# 重启 Claude Code 查看效果
```

### 高级推荐：自定义 Python 脚本

```bash
# 创建脚本目录
mkdir -p ~/.claude/scripts

# 下载示例脚本（见上文 Python 示例）
vim ~/.claude/scripts/statusline.py
chmod +x ~/.claude/scripts/statusline.py

# 配置
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.claude/scripts/statusline.py",
    "padding": 0
  }
}
```

---

## 📌 总结

### 核心要点

1. **StatusLine 是 Claude Code 的自定义状态栏功能**
   - 显示在界面底部
   - 通过命令动态生成
   - 支持完全自定义

2. **两种配置方式**
   - `/statusline` 命令（简单快速）
   - 手动编辑 `settings.json`（灵活控制）

3. **丰富的生态系统**
   - ccusage：成本追踪
   - claude-powerline：Powerline 风格
   - pyccsl：Python 零依赖
   - CCometixLine：Rust 高性能

4. **配置文件作用域**
   - Managed（系统级，不可覆盖）
   - User（全局个人配置）
   - Project（项目团队共享）
   - Local（本地覆盖）

### 推荐方案

| 场景 | 推荐工具 | 理由 |
|------|---------|------|
| **快速开始** | `/statusline` 命令 | 零配置，自动生成 |
| **成本监控** | ccusage | 实时成本追踪、日预算 |
| **美观定制** | claude-powerline | Powerline 风格、多主题 |
| **高性能** | CCometixLine | Rust 编写，交互式配置 |
| **零依赖** | pyccsl | Python 脚本，无外部依赖 |
| **完全自定义** | 自定义脚本 | 按需定制所有功能 |

### 下一步行动

1. **选择工具**：根据需求选择上述工具之一
2. **安装配置**：按照本文档的步骤进行配置
3. **测试验证**：重启 Claude Code 查看效果
4. **持续优化**：根据使用体验调整配置

---

## 📚 附录

### A. 配置文件完整示例

```json
{
  "statusLine": {
    "type": "command",
    "command": "bun x ccusage statusline",
    "padding": 0
  },
  "permissions": {
    "bash": "allow"
  },
  "theme": "dark",
  "model": "claude-sonnet-4.5"
}
```

### B. 常用 ANSI 颜色代码

| 颜色 | Bash 代码 | Python 代码 | 效果 |
|------|-----------|-------------|------|
| 重置 | `\033[0m` | `'\033[0m'` | 恢复默认 |
| 黑色 | `\033[30m` | `'\033[30m'` | 黑色文本 |
| 红色 | `\033[31m` | `'\033[31m'` | 红色文本 |
| 绿色 | `\033[32m` | `'\033[32m'` | 绿色文本 |
| 黄色 | `\033[33m` | `'\033[33m'` | 黄色文本 |
| 蓝色 | `\033[34m` | `'\033[34m'` | 蓝色文本 |
| 品红 | `\033[35m` | `'\033[35m'` | 品红文本 |
| 青色 | `\033[36m` | `'\033[36m'` | 青色文本 |
| 白色 | `\033[37m` | `'\033[37m'` | 白色文本 |
| 加粗 | `\033[1m` | `'\033[1m'` | 粗体文本 |

### C. 调试技巧

```bash
# 查看 Claude Code 配置
cat ~/.claude/settings.json

# 测试脚本输出
echo '{"cwd":"/test","gitBranch":"main","model":"claude-sonnet-4.5","contextWindow":{"used":15000,"total":200000}}' | ~/.claude/scripts/statusline.py

# 检查脚本权限
ls -l ~/.claude/scripts/

# 查看 Claude Code 日志
tail -f ~/.claude/logs/claude-code.log
```

---

## 🔗 相关链接

- **Claude Code 官网**：https://claude.ai/code
- **Claude Code 文档**：https://docs.anthropic.com/zh-CN/docs/claude-code
- **Anthropic 官网**：https://www.anthropic.com
- **GitHub 搜索**：https://github.com/search?q=claude-code-statusline

---

## 📝 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|---------|
| v1.0 | 2026-01-28 | 初始版本，完成 StatusLine 配置方法调研 |

---

**文档结束**
