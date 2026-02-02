# MCP 状态检测问题修复 - 2026-01-29

## 问题描述
MCP 模块显示"无 MCP 服务器"，实际配置了多个 MCP 服务器。

## 根因分析
1. 配置文件路径错误：查找 `~/.claude/mcp.json`，实际是 `~/.claude.json`
2. 未读取用户级别的 `mcpServers` 配置

## 修复方案

### 代码变更
1. **修改 `_get_from_config()` 方法**
   - 读取 `~/.claude.json` 
   - 解析用户级别 `mcpServers`
   - 解析 `projects` 中当前项目的 `mcpServers`

2. **添加异步执行机制**
   - `ThreadPoolExecutor` 后台执行 `claude mcp list`
   - 初始显示 `?/N`，命令完成后更新实际状态
   - 1分钟缓存避免频繁命令执行

3. **修复状态显示逻辑**
   - 错误时显示 `<errors> 错误`
   - 部分运行时显示 `running/total 运行中`
   - 全部运行时显示 `total/total 运行中`

### 测试更新
- 更新 15 个测试用例
- 添加 `_parse_mcp_config_for_test` 辅助方法
- mock 异步更新避免读取真实配置

## 验证结果
- 测试通过: 15/15
- 覆盖率达: 95%
- 显示结果: 7/8 运行中 (7 个命令返回，8 个配置读取)

## 技术决策
- 配置文件: `~/.claude.json` (Claude Code 标准位置)
- 异步执行: 命令可能超时，不阻塞状态栏
- 缓存策略: 1分钟缓存平衡实时性和性能
- 数据源: 配置保证数量，命令保证运行状态