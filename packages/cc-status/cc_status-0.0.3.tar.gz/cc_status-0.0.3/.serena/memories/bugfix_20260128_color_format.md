# 问题修复记录 - 颜色格式错误

**日期**: 2026-01-28  
**问题**: `Wrong color format '<prompt_toolkit.styles.style.Style'`

## 问题分析

### 错误原因
在 `src/cc_statusline/render/terminal_renderer.py` 文件的第 166 行，`Window` 构造函数的 `style` 参数错误地传入了 `Style` 对象。

根据 prompt_toolkit 的 API 文档，`Window.__init__` 的 `style` 参数类型应为：
```python
style: str | Callable[[], str]
```

但代码传入了：
```python
style=self._get_theme_style()  # 返回 Style 对象
```

### 错误位置
```python
# terminal_renderer.py:153-168
def _create_bottom_toolbar(self) -> Window:
    """创建底部工具栏窗口。"""
    control = FormattedTextControl(
        self._create_toolbar_content,
        focusable=False,
    )
    return Window(
        control,
        height=1,
        style=self._get_theme_style(),  # ❌ 错误：传入了 Style 对象
        char=" ",
    )
```

## 解决方案

### 修复方法
将 `style` 参数改为字符串形式的样式类引用：

```python
def _create_bottom_toolbar(self) -> Window:
    """创建底部工具栏窗口。"""
    control = FormattedTextControl(
        self._create_toolbar_content,
        focusable=False,
    )
    return Window(
        control,
        height=1,
        style="class:statusline.default",  # ✅ 正确：使用样式类字符串
        char=" ",
    )
```

### 工作原理
1. `_get_theme_style()` 方法返回一个 `Style` 对象，其中定义了 `statusline.default` 等样式类
2. `Window` 的 `style` 参数使用 `"class:statusline.default"` 引用这些样式类
3. Application 层级传入的 `style=self._get_theme_style()` 会解析这些样式类引用

## 验证结果

### 代码质量检查
```bash
✅ black --check: 通过
✅ ruff check: 通过  
✅ mypy: 通过
```

### 功能测试
```bash
✅ python -m cc_statusline --once
   输出: 🔌 无 MCP 服务器 │ ⏱️ 2h 43m

✅ python -m cc_statusline --list-themes
   列出 8 个主题

✅ python -m cc_statusline --list-modules  
   列出 2 个模块

✅ python -m cc_statusline --once --theme cyberpunk
   成功使用 cyberpunk 主题输出
```

## 相关知识

### prompt_toolkit 样式系统
- `Style.from_dict()` 创建样式定义（在 Application 层级应用）
- `Window` 的 `style` 参数使用字符串引用样式类
- 格式: `"class:your.style.class"` 或简单的 CSS 样式字符串

### 正确的架构
```
Application(style=Style.from_dict({...}))  # 定义样式
  └─ Window(style="class:statusline.default")  # 引用样式
```

## 教训
1. 仔细检查库的 API 文档和类型签名
2. `type: ignore` 注释往往是代码问题的警告信号
3. 在添加 type ignore 时应该先质疑代码是否正确
