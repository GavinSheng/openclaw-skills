# Email-Sender 技能改进说明

## 问题描述
在使用 email-sender 技能发送邮件时，当邮件内容包含 Markdown 格式时，QQ 邮箱等邮件客户端会显示原始的 Markdown 符号（如 `**`, `*`, `-` 等），而不是渲染后的格式，导致邮件内容显示混乱。

## 解决方案
我们在 email-sender 技能中增加了 Markdown 到 HTML 的转换功能和内容格式智能检测，具体改进包括：

1. 在 `scripts/main.py` 中添加了 `markdown_to_html` 函数
2. **优先使用专业的 `markdown` 库进行转换**（推荐安装 `markdown>=3.0.0`），支持丰富的扩展功能
3. 提供了备用的手动转换实现，处理常见的 Markdown 元素
4. 添加了 `detect_content_type` 函数，能够智能识别内容格式（markdown, html, plain）
5. 修改了 `send_email_via_smtp` 函数，支持多种内容格式处理
6. **仅对Markdown内容发送HTML版本**，避免邮件客户端显示原始Markdown符号
7. 更新了 `requirements.txt` 包含 markdown 库依赖

## 推荐安装
为获得最佳转换效果，建议安装专业的Markdown库：

```bash
pip install markdown>=3.0.0
```

库包含的扩展功能：
- `extra`: 表格、围栏代码块、脚注等
- `codehilite`: 代码高亮
- `fenced_code`: 围栏代码块
- `toc`: 目录
- `attr_list`: 属性列表
- `def_list`: 定义列表
- `abbr`: 缩写
- `md_in_html`: HTML块中的Markdown

## 支持的 Markdown 语法
- 标题：`#`, `##`, `###` 等
- 加粗：`**text**` 或 `__text__`
- 斜体：`*text*` 或 `_text_`
- 代码：`` `code` ``（内联）和 ``` ```code block``` （代码块）
- 链接：`[text](url)`
- 列表：`- item` 或 `1. item`
- 表格、块引用、定义列表等（需安装markdown库）

## 内容格式处理
- **自动检测** (`content_format='auto'`)：自动识别内容类型并适当处理
- **Markdown** (`content_format='markdown'`)：将 Markdown 转换为 HTML
- **HTML** (`content_format='html'`)：直接作为 HTML 发送
- **纯文本** (`content_format='plain'`)：转换为带基本HTML格式的邮件

## 效果
现在，当 email-sender 技能发送包含 Markdown 内容的邮件时，收件人（包括 QQ 邮箱用户）将看到正确渲染的格式，而不是原始的 Markdown 符号。使用专业markdown库可以获得更丰富的格式支持。

## 邮件样式
转换后的 HTML 邮件包含了基本的 CSS 样式，以确保在各种邮件客户端中都有良好的显示效果。