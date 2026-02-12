# SearXNG Article Analyzer Skill

这是一个专门用于深度分析单篇文章的技能，可生成适合公众号发布的概要和详情，通常配合SearXNG搜索结果使用。

## 功能

- 从指定URL获取文章内容
- 提供不超过300字的概要，突出核心观点和价值
- 提供详细分析，避免原文照抄，适合公众号发布
- 格式化输出适合社交媒体发布
- 具备反反爬虫能力，自动检测并绕过常见防护机制（如401/403/429错误、Datadome、CloudFront等）
- 自动选择HTTP请求或Playwright浏览器自动化方法，提高抓取成功率

## 安装依赖

```bash
pip install httpx
pip install playwright
playwright install
```

## 使用方法

```bash
# 通过命令行使用
python3 scripts/main.py --url "https://example.com/article"
```

## API 调用

在阿里云MoltBot平台中，可通过以下方式调用：

```python
result = handler({"url": "https://example.com/article"}, context)
```

## 输出格式

返回包含以下字段的JSON对象：

- `success`: 操作是否成功
- `url`: 分析的文章URL
- `title`: 文章标题
- `summary`: 不超过300字的概要
- `detail`: 详细分析，适合公众号发布
- `processing_duration`: 处理耗时
- `model_used`: 使用的模型名称
- `error`: 错误信息（如果操作失败）

## 配置要求

- 环境需支持asyncio
- 需要网络访问权限以获取文章内容
- 需要接入阿里云大模型服务（qwen3-max-2026-01-23）