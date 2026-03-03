---
name: techpulse-scout
description: 科技脉搏·侦察兵 - 轻量级、高频次、广覆盖的信息过滤器。全网扫描科技热点，去重过滤，重要性评分，结构化输出 High/Medium 级别事件。
author: Investment Partner
version: 1.0.0
triggers:
  - "科技热点扫描"
  - "热点侦察"
  - "TechPulse"
metadata: {
  "type": "scanner",
  "frequency": "每 1-2 小时",
  "output": "JSON 结构化事件列表",
  "next_skill": "TechChain Insight"
}
---

# TechPulse Scout - 科技脉搏·侦察兵

## 核心定位

轻量级、高频次、广覆盖的**信息过滤器**。

## 触发方式

- **定时任务**: 每 1-2 小时执行一次
- **美股盘前/盘后**: 03:00/21:00 执行
- **手动触发**: 随时扫描

## 核心任务

### 1. 全网扫描
针对预设关键词在权威信源快速检索

### 2. 去重与过滤
对比过去 24 小时已知新闻，剔除重复和噪音

### 3. 重要性评分
- **High**: 官方公告 + 重大影响
- **Medium**: 权威媒体 + 中等影响
- **Low**: 一般媒体 + 轻微影响

### 4. 结构化输出
仅输出 High/Medium 级别事件列表

## 输出格式 (JSON)

```json
[
  {
    "id": "evt_20260303_001",
    "priority": "HIGH",
    "title": "NVIDIA 宣布新一代 Rubin 架构提前量产",
    "summary": "黄仁勋确认 Rubin 架构将于 Q3 量产，HBM4 内存成为瓶颈。",
    "tags": ["AI", "半导体", "存储"],
    "source_url": "https://nvidianews.nvidia.com/...",
    "source_type": "官方公告",
    "timestamp": "2026-03-03T02:00:00Z",
    "companies": ["NVIDIA", "SK Hynix"],
    "trigger_next": true
  }
]
```

## 决策逻辑

```
IF 结果为空 OR 仅有 Low 优先级
  → 结束流程（不消耗后续 Token）
  
IF 存在 High/Medium 优先级事件
  → 触发 Skill B (TechChain Insight)
  → 传递事件列表作为参数
```

## 监控领域

### 科技产业
- 🖥️ 半导体
- 🤖 人工智能
- 🔋 新能源
- 🚗 新能源汽车
- 🚙 自动驾驶
- 🔋 固态电池
- 🤖 人形机器人
- 📡 6G 通信
- ⚛️ 量子计算
- 🛸 低空经济
- 🚀 商业航天
- 🔆 钙钛矿电池

### 金融市场（新增）
- 📉 股市波动
- 💰 宏观经济
- 🏦 央行政策
- 📊 大宗商品
- 💱 汇率波动

## 权威性排序

1. **官方公告** (SEC/巨潮/港交所/公司官网)
2. **顶级财经** (Bloomberg/Reuters/WSJ/财新)
3. **科技媒体** (36Kr/AnandTech/EE Times)
4. **主流财经** (东方财富/同花顺/新浪财经)
5. **社交媒体** (知乎/微博 - 仅参考)

## 去重逻辑

- 对比过去 24 小时事件 ID
- 标题相似度 > 80% 视为重复
- 同一事件不同报道合并

---

**版本**: 1.0.0  
**创建日期**: 2026-03-03  
**下一技能**: TechChain Insight
