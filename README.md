# OpenClaw Skills Collection

这是一个用于存放所有 OpenClaw 项目中使用到的技能(Skills)的集合项目。

## Claude Code Skills 规范

根据 Claude Code 官方规范，每个技能都是一个独立的目录（使用 kebab-case 命名），包含 `SKILL.md` 文件。技能存储在 `skills/` 目录下，Claude 可以自动发现和使用这些技能。

## 项目结构

```
openclaw-skills/
├── README.md                                    # 项目说明
├── __init__.py                                  # Python包初始化文件
└── skills/
    ├── skill-creator/                           # 技能创建工具
    │   ├── SKILL.md                             # [核心] 包含YAML元数据和System Prompt
    │   ├── scripts/                             # [核心] 存放技能创建相关脚本
    │   │   ├── init_skill.py                    # 初始化新技能
    │   │   ├── package_skill.py                 # 打包技能为分发格式
    │   │   └── quick_validate.py                # 验证技能完整性
    │   ├── references/                          # [官方规范] 存放供Claude参考的静态文档
    │   │   ├── output-patterns.md               # 输出模式参考
    │   │   └── workflows.md                     # 工作流参考
    │   └── LICENSE.txt                          # 许可证文件
    ├── web-info-search/                         # Web信息搜索技能（kebab-case命名）
    │   ├── SKILL.md                             # [核心] 包含YAML元数据和System Prompt
    │   ├── README.md                            # 给人看的安装与配置说明
    │   ├── requirements.txt                     # 依赖包列表
    │   ├── scripts/                             # [核心] 存放Claude实际运行的可执行脚本
    │   │   └── main.py                          # 核心逻辑：web_search和web_fetch实现
    │   ├── references/                          # [官方规范] 存放供Claude参考的静态文档
    │   │   └── api_spec.md                      # 搜索引擎的API参数定义参考
    │   └── assets/                              # [官方规范] 存放技能所需的静态资源
    │       └── selector_rules.json              # 不同网站的爬取规则定义
    ├── web-info-search-qwen/                    # Web信息搜索技能（Qwen优化版）
    │   ├── SKILL.md                             # [核心] 包含YAML元数据和System Prompt
    │   ├── README.md                            # 给人看的安装与配置说明
    │   ├── requirements.txt                     # 依赖包列表
    │   ├── scripts/                             # [核心] 存放Claude实际运行的可执行脚本
    │   │   └── main.py                          # 核心逻辑：web_search和web_fetch实现（Qwen优化）
    │   ├── references/                          # [官方规范] 存放供Claude参考的静态文档
    │   │   └── api_spec.md                      # 搜索引擎的API参数定义参考
    │   └── assets/                              # [官方规范] 存放技能所需的静态资源
    │       └── selector_rules.json              # 不同网站的爬取规则定义
    ├── info-summarization-qwen/                 # 信息总结技能（Qwen版）
    │   ├── SKILL.md                             # [核心] 包含YAML元数据和System Prompt
    │   ├── README.md                            # 给人看的安装与配置说明
    │   ├── requirements.txt                     # 依赖包列表
    │   ├── scripts/                             # [核心] 存放Claude实际运行的可执行脚本
    │   │   └── main.py                          # 核心逻辑：内容总结、关键点提取、内容分析
    │   ├── references/                          # [官方规范] 存放供Claude参考的静态文档
    │   │   └── api_spec.md                      # API参数定义参考
    │   └── assets/                              # [官方规范] 存放技能所需的静态资源
    │       └── config.json                      # 配置文件
    └── searxng-analyzer/                        # SearXNG分析器
        ├── SKILL.md                             # [核心] 包含YAML元数据和System Prompt
        ├── README.md                            # 给人看的安装与配置说明
        ├── requirements.txt                     # 依赖包列表
        ├── scripts/                             # [核心] 存放Claude实际运行的可执行脚本
        │   └── main.py                          # 核心逻辑：分析SearXNG搜索结果并总结
        ├── references/                          # [官方规范] 存放供Claude参考的静态文档
        │   └── specification.md                 # 规格说明
        └── assets/                              # [官方规范] 存放技能所需的静态资源
            └── config.json                      # 配置文件
```

## 当前已有的技能

- `web-info-search`: Web信息搜索技能，提供网络搜索和内容抓取功能
  - `web_search`: 执行网络搜索，支持关键词检索（通过 `scripts/main.py --search "query"` 调用）
  - `web_fetch`: 从指定URL抓取网页内容（通过 `scripts/main.py --fetch "URL"` 调用）

- `web-info-search-qwen`: Web信息搜索技能（Qwen优化版），针对中文环境优化，提供网络搜索和内容抓取功能
  - `web_search`: 执行网络搜索，优先使用适合中国用户的搜索引擎（如Sogou、360搜索）
  - `web_fetch`: 从指定URL抓取网页内容

- `info-summarization-qwen`: 信息总结技能（Qwen版），使用Qwen3-Max模型进行内容总结
  - `summarize`: 创建内容的简洁摘要
  - `extract`: 从文本中提取关键点和要点
  - `analyze`: 对内容进行深入分析并提供见解

- `searxng-analyzer`: SearXNG分析器，分析SearXNG搜索结果并提取关键信息
  - 分析SearXNG搜索结果表格和详细列表
  - 从结果中的URL获取内容
  - 提取相关信息并使用Qwen3-Max进行总结
  - 以Markdown格式输出分析结果

- `skill-creator`: 技能创建工具，用于快速创建和打包新的技能
  - `init_skill.py`: 初始化新技能的脚手架
  - `package_skill.py`: 验证和打包技能为分发格式
  - `quick_validate.py`: 快速验证技能的完整性

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