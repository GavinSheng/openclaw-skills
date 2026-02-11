# OpenClaw Skills Collection

这是一个用于存放所有 OpenClaw 项目中使用到的技能(Skills)的集合项目。

## Claude Code Skills 规范

根据 Claude Code 官方规范，每个技能都是一个独立的目录（使用 kebab-case 命名），包含 `SKILL.md` 文件。技能存储在 `skills/` 目录下，Claude 可以自动发现和使用这些技能。

## 项目结构

```
openclaw-skills/
├── README.md                                    # 项目说明
├── test_skill.py                               # 技能功能验证脚本
└── skills/web-info-search/                     # Web信息搜索技能（kebab-case命名）
    ├── SKILL.md                               # [核心] 包含YAML元数据和System Prompt
    ├── README.md                              # 给人看的安装与配置说明
    ├── requirements.txt                        # 依赖包列表
    ├── scripts/                               # [核心] 存放Claude实际运行的可执行脚本
    │   └── main.py                            # 核心逻辑：web_search和web_fetch实现
    ├── references/                            # [官方规范] 存放供Claude参考的静态文档
    │   └── api_spec.md                        # 搜索引擎的API参数定义参考
    └── assets/                                # [官方规范] 存放技能所需的静态资源
        └── selector_rules.json                # 不同网站的爬取规则定义
```

## 当前已有的技能

- `web-info-search`: Web信息搜索技能，提供网络搜索和内容抓取功能
  - `web_search`: 执行网络搜索，支持关键词检索（通过 `scripts/main.py --search "query"` 调用）
  - `web_fetch`: 从指定URL抓取网页内容（通过 `scripts/main.py --fetch "URL"` 调用）

## 安装依赖

```bash
pip install -r skills/web-info-search/requirements.txt
```

## 使用方法

将此仓库添加到 Claude Code 的插件市场后，可以使用以下命令：

1. 让 Claude 自动决定何时使用技能（基于 description 字段）
2. 通过 `/skill-name` 直接调用技能

## 功能验证

运行测试脚本以验证技能功能：

```bash
python3 test_skill.py
```

## 项目目的

这个项目旨在集中管理和存放所有 OpenClaw 使用的技能，便于维护和复用。