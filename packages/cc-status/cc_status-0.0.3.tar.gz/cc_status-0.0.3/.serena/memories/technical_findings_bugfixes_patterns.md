# cc-statusline 三项问题修复 - 技术发现

**日期**: 2026-01-29
**类型**: Bug修复技术发现

---

## 🔍 问题模式识别

### 模式1: 全局状态污染
**症状**: 多个实例/窗口共享状态，导致相互干扰
**根因**: 使用固定的全局文件路径存储状态
**解决方案**: 基于进程ID/会话ID创建独立的状态文件
**预防**: 设计时考虑多实例场景，使用唯一标识符

### 模式2: 输出格式依赖
**症状**: 功能突然失效，因为外部工具的输出格式变了
**根因**: 解析逻辑硬编码特定的输出格式
**解决方案**: 
1. 编写灵活的解析逻辑
2. 支持多种格式版本
3. 添加格式版本检测
**预防**: 依赖外部命令时，考虑版本兼容性

### 模式3: 导入时副作用
**症状**: 导入模块就产生副作用（如网络请求、文件操作）
**根因**: 在模块级别的 `__init__()` 或全局作用域执行副作用代码
**解决方案**: 延迟初始化（Lazy Initialization）
**预防**: 模块导入应该是幂等的，不应该有副作用

---

## 💡 最佳实践

### 1. 延迟初始化模式

```python
# ❌ 不好：立即初始化
class Module:
    def initialize(self):
        self._load_data()  # 立即执行

# ✅ 好：延迟初始化
class Module:
    def initialize(self):
        pass  # 不做任何事
    
    def get_output(self):
        if not self._data:  # 第一次使用时才加载
            self._load_data()
        return self._data
```

### 2. 进程隔离的状态管理

```python
# ❌ 不好：共享状态文件
STATE_FILE = "~/.claude/session_state.json"

# ✅ 好：进程隔离
def get_state_file(self):
    pid = os.getpid()
    return f"~/.claude/session_state_{pid}.json"
```

### 3. 健壮的解析逻辑

```python
# ❌ 不好：硬编码格式
if "(running)" in line:
    status = "running"

# ✅ 好：支持多种格式
if "✓ Connected" in line or "(running)" in line:
    status = "running"
elif "✗ Error" in line or "(error)" in line:
    status = "error"
```

---

## 🛠️ 调试技巧

### 技巧1: 追踪副作用
```bash
# 使用 strace 追踪系统调用
strace -f -e trace=process,read,write python -m cc_statusline --once

# 检查文件访问
opensnoop | grep cc-statusline
```

### 技巧2: 隔离问题
```python
# 单独测试某个功能
from cc_statusline.modules.mcp_status import MCPStatusModule

module = MCPStatusModule()
servers = module._parse_mcp_list_output(test_output)
print(f"解析到 {len(servers)} 个服务器")
```

### 技巧3: Mock外部依赖
```python
# 在测试中mock subprocess
@patch("subprocess.run")
def test_mcp_detection(mock_run):
    mock_run.return_value = MagicMock(stdout="test output")
    # 测试代码
```

---

## 📊 性能考虑

### subprocess.run() 性能
- 超时设置要合理：太短会超时，太长会阻塞
- 考虑使用 `timeout` 参数，避免永久挂起
- 捕获 `TimeoutExpired` 异常

### print() 性能
- 频繁的 print() 有性能开销
- `flush=True` 增加开销，但确保及时输出
- 考虑使用日志系统代替 print

### 文件 I/O 性能
- 避免频繁的小文件写入
- 考虑批量更新
- 定期清理旧的状态文件

---

## 🧪 测试策略

### 单元测试要点
1. **Mock外部依赖**: subprocess, 文件系统, 网络
2. **测试边界情况**: 空输出, 超时, 格式错误
3. **测试并发**: 多线程, 多进程场景

### 集成测试要点
1. **真实环境测试**: 使用真实的 claude mcp list 命令
2. **多窗口测试**: 验证状态隔离
3. **长时间运行**: 验证内存泄漏, 文件累积

### 手动验证清单
- [ ] 打开新窗口，时间是否从0开始
- [ ] 执行命令，MCP数量是否正确
- [ ] 观察是否有MCP重连现象
- [ ] 检查临时文件是否累积

---

## 🔄 代码审查检查点

### 状态管理
- [ ] 多实例场景是否考虑
- [ ] 状态文件路径是否唯一
- [ ] 状态清理机制是否存在

### 外部依赖
- [ ] 是否有导入时副作用
- [ ] 是否使用了延迟初始化
- [ ] 超时设置是否合理

### 解析逻辑
- [ ] 是否支持多种格式
- [ ] 错误处理是否完善
- [ ] 是否有fallback机制

---

## 📝 经验教训

1. **永远不要假设单实例场景**
   - 用户可能同时打开多个窗口
   - 可能有多个进程同时运行

2. **外部命令的输出格式会变**
   - 今天是 `server (running)`
   - 明天可能是 `server: ✓ Connected`
   - 编写灵活的解析逻辑

3. **导入时不应该有副作用**
   - 导入模块应该是幂等的
   - 使用延迟初始化模式
   - 让用户决定何时初始化

4. **测试要覆盖真实场景**
   - 单元测试不能发现所有问题
   - 必须进行手动验证
   - 多窗口测试很重要

5. **性能问题往往被忽视**
   - 每秒2次的小操作累积起来很可观
   - print() 语句可能成为瓶颈
   - 频繁的 subprocess 调用要谨慎

---

**下次遇到类似问题时，参考这份技术发现。**
