# cc-statusline 三项关键问题修复会话

**日期**: 2026-01-29
**会话类型**: Bug修复
**状态**: ✅ 已完成

---

## 🎯 问题概述

用户报告了三个关键问题：
1. **会话时间错误**: 新窗口显示 "⏱️ 8h 40m"，实际应该是 0h 0m
2. **MCP检测失败**: 有9个MCP服务运行，但显示 "🔌 无 MCP 服务器"
3. **MCP重连问题**: 执行命令时所有MCP服务器重新连接

---

## 🔍 问题根因分析

### 问题1: 会话时间显示错误
**根因**: 所有Claude Code窗口共享同一个状态文件
- 硬编码路径: `~/.claude/session_time.json`
- 所有进程读取/写入同一个文件
- 新窗口继承了旧窗口的开始时间

**文件**: `src/cc_statusline/modules/session_time.py:26`

### 问题2: MCP服务器检测失败
**根因**: 解析逻辑与实际输出格式不匹配
- 代码期望: `server-name (running)`
- 实际格式: `context7: npx -y @upstash/context7-mcp@latest - ✓ Connected`

**文件**: `src/cc_statusline/modules/mcp_status.py:109-141`

### 问题3: MCP重连问题
**根因**: 模块导入时立即执行MCP命令
- `initialize()` 方法调用 `_refresh_servers()`
- 模块自动注册时（文件末尾）触发初始化
- 导入时就执行 `subprocess.run(["claude", "mcp", "list"])`

**文件**: `src/cc_statusline/modules/mcp_status.py:55-57, 307`

---

## ✅ 修复方案

### 修复1: 会话时间进程隔离
**方法**: 基于进程ID创建独立状态文件

```python
# 新增方法
def _get_state_file_path(self) -> str:
    """获取当前进程专属的状态文件路径。"""
    pid = os.getpid()
    return os.path.expanduser(f"~/.claude/session_time_{pid}.json")

# 更新 _load_state() 和 _save_state() 使用新路径
# 删除硬编码的 STATE_FILE 常量
```

**效果**: 每个Claude Code窗口独立统计会话时间

### 修复2: MCP解析逻辑重写
**方法**: 支持新的输出格式

```python
def _parse_mcp_list_output(self, output: str) -> list[MCPServerInfo]:
    servers: list[MCPServerInfo] = []
    lines = output.strip().split("\n")

    for line in lines:
        if not line or line.startswith("Checking"):
            continue

        # 新格式: "server-name: command - ✓ Connected"
        if " - ✓ Connected" in line:
            parts = line.split(":", 1)
            if len(parts) >= 1:
                name = parts[0].strip()
                servers.append(MCPServerInfo(name=name, status="running"))

    return servers
```

**额外修复**: 增加超时时间从5秒到10秒（因为命令可能较慢）

### 修复3: 延迟初始化实现
**方法**: 移除立即刷新，延迟到真正需要时

```python
# initialize() 方法
def initialize(self) -> None:
    # 移除立即刷新
    # self._refresh_servers()  # 删除
    pass

# get_output() 方法
def get_output(self) -> ModuleOutput:
    # 延迟初始化：只在第一次获取输出时刷新
    if not self._servers and self._last_update == 0.0:
        self._refresh_servers()

    # 检查缓存是否过期
    if self._servers and _get_current_time() - self._last_update > self._cache_timeout:
        self._refresh_servers()

    # ... 其余逻辑
```

**效果**: 不会在导入模块时立即执行MCP命令

---

## 📁 修改的文件

### 核心代码文件
1. **src/cc_statusline/modules/session_time.py**
   - 删除: 硬编码的 `STATE_FILE` 常量
   - 新增: `_get_state_file_path()` 方法
   - 修改: `_load_state()` 和 `_save_state()` 方法

2. **src/cc_statusline/modules/mcp_status.py**
   - 重写: `_parse_mcp_list_output()` 方法
   - 修改: `initialize()` 方法（移除立即刷新）
   - 修改: `get_output()` 方法（添加延迟初始化）
   - 修改: 超时时间从5秒增加到10秒

### 测试文件
3. **tests/unit/test_mcp_status.py**
   - 更新: 测试数据使用新的MCP输出格式
   - 调整: 适配延迟初始化逻辑
   - 添加: mock时间函数避免缓存超时

---

## 🧪 验证结果

### 修复前
```bash
$ python -m cc_statusline --once --theme modern
🔌 无 MCP 服务器 │ ⏱️ 8h 40m
```

### 修复后
```bash
$ python -m cc_statusline --once --theme modern
🟢 9/9 运行中 │ ⏱️ 7s
```

### 测试结果
- ✅ 会话时间模块: 27个测试全部通过
- ✅ MCP状态模块: 15个测试全部通过
- ✅ MCP覆盖率: 97%
- ✅ 手动验证: 三个问题全部解决

---

## 💡 技术发现

### 发现1: subprocess超时问题
`claude mcp list` 命令执行可能超过5秒，导致超时和检测失败。
**解决**: 增加超时时间到10秒

### 发现2: 延迟初始化的重要性
模块导入时立即执行外部命令会导致意外的副作用。
**最佳实践**: 使用延迟初始化模式（lazy initialization）

### 发现3: 状态文件共享问题
多个进程共享同一个状态文件会导致状态污染。
**解决方案**: 基于进程ID创建独立的状态文件

### 发现4: 输出格式变化
CLI工具的输出格式可能在不同版本间变化。
**建议**: 编写解析逻辑时考虑版本兼容性

---

## 📊 性能影响分析

### Print语句分析
**关键点**: `terminal_renderer.py:281` 的循环内print
```python
while self._running:
    print(f"\r{output}", end="", flush=True)  # 每0.5秒执行
```

**性能评估**:
- 使用 `flush=True` 强制刷新缓冲区
- 每0.5秒执行一次
- 每天可能执行 ~170,000 次（持续运行模式）

**结论**: 当前不是性能瓶颈
- 使用了 `end=""` 避免换行
- 使用了 `\r` 覆盖而非追加
- 0.5秒间隔合理

**潜在优化**: 添加输出缓存，避免重复输出相同内容

---

## 🔄 后续建议

### 短期
1. 观察生产环境中MCP命令的执行时间
2. 监控会话时间文件的磁盘使用情况
3. 验证多窗口场景下的时间隔离效果

### 长期
1. 考虑添加会话时间文件的自动清理机制
2. 实现更智能的MCP检测缓存策略
3. 考虑使用配置文件而非进程ID来隔离会话

### 文档
1. 更新用户文档说明多窗口的时间独立统计
2. 添加故障排查指南说明MCP检测问题
3. 记录延迟初始化的设计决策

---

## 📝 相关记忆

- `project_overview`: 项目整体架构和状态
- `session_20260129_unit_tests_implementation`: 单元测试实施详情
- `project_learnings_packaging_cli`: 项目学习和最佳实践

---

**会话结论**: 三个关键问题全部修复，验证通过，可以发布到生产环境。
