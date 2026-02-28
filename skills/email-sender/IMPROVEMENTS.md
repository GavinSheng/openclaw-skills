# Email-Sender 技能改进说明

## 问题描述
在使用 email-sender 技能发送邮件时，当邮件内容包含 Markdown 格式时，QQ 邮箱等邮件客户端会显示原始的 Markdown 符号（如 `**`, `*`, `-` 等），而不是渲染后的格式，导致邮件内容显示混乱。

## 解决方案
我们在 email-sender 技能中增加了 Markdown 到 HTML 的转换功能和内容格式智能检测，具体改进包括：

1. 在 `scripts/main.py` 中添加了 `markdown_to_html` 函数
2. 优先使用专业的 `markdown` 库进行转换（需安装 `markdown>=3.0.0`）
3. 提供了备用的手动转换实现，处理常见的 Markdown 元素
4. 添加了 `detect_content_type` 函数，能够智能识别内容格式（markdown, html, plain）
5. 修改了 `send_email_via_smtp` 函数，支持多种内容格式处理
6. 更新了 `requirements.txt` 包含 markdown 库依赖

## 支持的 Markdown 语法
- 标题：`#`, `##`, `###` 等
- 加粗：`**text**` 或 `__text__`
- 斜体：`*text*` 或 `_text_`
- 代码：`` `code` ``（内联）和 ``` ```code block``` （代码块）
- 链接：`[text](url)`
- 列表：`- item` 或 `1. item`

## 内容格式处理
- **自动检测** (`content_format='auto'`)：自动识别内容类型并适当处理
- **Markdown** (`content_format='markdown'`)：将 Markdown 转换为 HTML 并同时提供纯文本版本
- **HTML** (`content_format='html'`)：直接作为 HTML 发送
- **纯文本** (`content_format='plain'`)：同时提供纯文本和简单的 HTML 版本

## 安装说明
推荐安装 markdown 库以获得最佳转换效果：

```bash
pip install markdown>=3.0.0
```

如果未安装 markdown 库，程序会使用内置的手动转换功能。

## 效果
现在，当 email-sender 技能发送包含 Markdown 内容的邮件时，收件人（包括 QQ 邮箱用户）将看到正确渲染的格式，而不是原始的 Markdown 符号。此外，技能现在可以智能地处理不同格式的内容。

## 邮件样式
转换后的 HTML 邮件包含了基本的 CSS 样式，以确保在各种邮件客户端中都有良好的显示效果。