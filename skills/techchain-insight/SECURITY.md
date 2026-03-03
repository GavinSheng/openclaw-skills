# 安全配置指南

## 敏感信息处理

为保护用户隐私和安全，TechChain Insight 技能不再使用硬编码的邮箱地址，而是通过环境变量进行配置。

## 环境变量配置

### 必需的环境变量

- `TECHCHAIN_REPORT_EMAIL`: 设置接收报告的邮箱地址

### 配置方法

#### 方法一：使用 .env 文件

在 `skills/techchain-insight/` 目录下创建 `.env` 文件：

```bash
# .env
TECHCHAIN_REPORT_EMAIL=your-email@example.com
```

#### 方法二：系统环境变量

在系统中设置环境变量：

```bash
export TECHCHAIN_REPORT_EMAIL=your-email@example.com
```

## 注意事项

1. 请勿在代码中硬编码敏感信息（如邮箱、密码等）
2. 确保 `.env` 文件不会被提交到 Git 仓库
3. 定期轮换敏感信息
4. 限制对敏感信息的访问权限

## 默认行为

如果未设置 `TECHCHAIN_REPORT_EMAIL` 环境变量，默认会使用 `recipient@example.com` 作为占位符，请务必在使用前配置正确的邮箱地址。