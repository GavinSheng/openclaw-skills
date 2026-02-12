# OpenClaw Skills Collection

A collection of skills used during my personal experience with OpenClaw, including both self-developed and community-contributed ones.

这是我在 OpenClaw 个人使用体验过程中积累的一系列技能集合，包含自己开发的和社区贡献的技能。

## Claude Code Skills 规范

根据 Claude Code 官方规范，每个技能都是一个独立的目录（使用 kebab-case 命名），包含 `SKILL.md` 文件。技能存储在 `skills/` 目录下，Claude 可以自动发现和使用这些技能。

## 项目结构

```
openclaw-skills/
├── README.md                                    # 项目说明
├── __init__.py                                  # Python包初始化文件
└── skills/                                      # 所有技能目录
    ├── skill-creator/                           # 技能创建工具
    ├── web-info-search/                         # Web信息搜索技能
    ├── web-info-search-qwen/                    # Web信息搜索技能（Qwen优化版）
    ├── info-summarization-qwen/                 # 信息总结技能（Qwen版）
    ├── searxng-analyzer/                        # SearXNG分析器
    └── article-analyzer/                        # 文章分析器
```

## 当前已有的技能

- `web-info-search`: Web信息搜索技能，提供网络搜索和内容抓取功能
- `web-info-search-qwen`: Web信息搜索技能（Qwen优化版），针对中文环境优化
- `info-summarization-qwen`: 信息总结技能（Qwen版），使用Qwen3-Max模型进行内容总结
- `searxng-analyzer`: SearXNG分析器，分析SearXNG搜索结果并提取关键信息
- `article-analyzer`: 文章分析器，深度分析单篇文章并生成适合公众号发布的概要和详情
- `skill-creator`: 技能创建工具，用于快速创建和打包新的技能

## 安装依赖

```bash
# 为web-info-search技能安装依赖
pip install -r skills/web-info-search/requirements.txt

# 为web-info-search-qwen技能安装依赖
pip install -r skills/web-info-search-qwen/requirements.txt

# 为info-summarization-qwen技能安装依赖
pip install -r skills/info-summarization-qwen/requirements.txt

# 为searxng-analyzer技能安装依赖
pip install -r skills/searxng-analyzer/requirements.txt

# 为article-analyzer技能安装依赖
pip install -r skills/article-analyzer/requirements.txt
```

## 使用方法

将此仓库添加到 Claude Code 的插件市场后，可以使用以下命令：

1. 让 Claude 自动决定何时使用技能（基于 description 字段）
2. 通过 `/skill-name` 直接调用技能

## 阿里云MoltBot平台集成

所有技能都已更新以支持阿里云MoltBot平台的标准接口：

- 每个技能的 `main.py` 脚本都实现了 `handler(request, context)` 函数
- 使用 `context.llm.generate()` 调用大语言模型
- 支持标准的 `model`、`temperature`、`max_tokens` 参数
- 所有技能均使用 `qwen3-max-2026-01-23` 模型ID

## 项目目的

这个项目旨在集中管理和存放所有 OpenClaw 使用的技能，便于维护和复用。所有技能都已经适配阿里云MoltBot平台，可以在该平台上直接运行并利用大语言模型的强大能力。