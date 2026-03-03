#!/usr/bin/env python3
# =============================================================================
# Nitter RSS 监控模块
# 功能：直接从 Nitter RSS 获取权威 X 账号的最新推文
# 无需 API 密钥，实时获取马斯克/OpenAI/特朗普等关键人物推文
# =============================================================================

import hashlib
import re
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any
from pathlib import Path

# Nitter 实例列表
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacy.com.de",
    "https://nitter.lunar.icu",
]

# 权威 X 账号 RSS 订阅列表（投资合伙人指定高价值信源）
AUTHORITATIVE_X_RSS = {
    # ==================== AI & 大模型 (最高优先级) ====================
    "sama": {
        "name": "Sam Altman (OpenAI CEO)",
        "rss_urls": [f"{instance}/sama/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["OpenAI", "AI", "GPT", "算力"],
        "category": "AI/大模型",
    },
    "elonmusk": {
        "name": "Elon Musk (xAI/Tesla AI)",
        "rss_urls": [f"{instance}/elonmusk/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["Tesla", "SpaceX", "xAI", "FSD", "Optimus"],
        "category": "AI/大模型",
    },
    "karpathy": {
        "name": "Andrej Karpathy (LLM 专家)",
        "rss_urls": [f"{instance}/karpathy/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["LLM", "AI", "训练"],
        "category": "AI/大模型",
    },
    "DarioAmodei": {
        "name": "Dario Amodei (Anthropic CEO)",
        "rss_urls": [f"{instance}/DarioAmodei/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["Claude", "AI 安全"],
        "category": "AI/大模型",
    },
    "ylecun": {
        "name": "Yann LeCun (Meta AI)",
        "rss_urls": [f"{instance}/ylecun/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["AI", "开源", "技术"],
        "category": "AI/大模型",
    },
    "OpenAI": {
        "name": "OpenAI 官方",
        "rss_urls": [f"{instance}/OpenAI/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["GPT", "AI"],
        "category": "AI/大模型",
    },
    "AnthropicAI": {
        "name": "Anthropic (Claude) 官方",
        "rss_urls": [f"{instance}/AnthropicAI/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["Claude", "AI"],
        "category": "AI/大模型",
    },
    "nvidia": {
        "name": "NVIDIA 官方",
        "rss_urls": [f"{instance}/nvidia/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["GPU", "AI 芯片", "HBM", "Blackwell"],
        "category": "AI/大模型",
    },
    
    # ==================== 半导体 & 硬件 ====================
    "TSMC": {
        "name": "台积电官方",
        "rss_urls": [f"{instance}/TSMC/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["晶圆代工", "扩产", "财报"],
        "category": "半导体",
    },
    "ASML": {
        "name": "ASML 官方",
        "rss_urls": [f"{instance}/ASML/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["光刻机", "EUV"],
        "category": "半导体",
    },
    "SemiAnalysis": {
        "name": "SemiAnalysis (硬核半导体分析)",
        "rss_urls": [f"{instance}/SemiAnalysis/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["半导体", "良率", "成本"],
        "category": "半导体",
    },
    "AMD": {
        "name": "AMD 官方",
        "rss_urls": [f"{instance}/AMD/rss" for instance in NITTER_INSTANCES],
        "priority": "MEDIUM",
        "domains": ["AI 芯片", "数据中心"],
        "category": "半导体",
    },
    "Intel": {
        "name": "Intel 官方",
        "rss_urls": [f"{instance}/Intel/rss" for instance in NITTER_INSTANCES],
        "priority": "MEDIUM",
        "domains": ["IDM", "芯片法案"],
        "category": "半导体",
    },
    
    # ==================== 新能源汽车 & 自动驾驶 ====================
    "Tesla": {
        "name": "Tesla 官方",
        "rss_urls": [f"{instance}/Tesla/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["电动车", "FSD", "电池"],
        "category": "新能源汽车",
    },
    "SawyerMerritt": {
        "name": "Sawyer Merritt (Tesla 数据分析)",
        "rss_urls": [f"{instance}/SawyerMerritt/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["Tesla", "销量", "FSD"],
        "category": "新能源汽车",
    },
    "BYDCompany": {
        "name": "比亚迪官方",
        "rss_urls": [f"{instance}/BYDCompany/rss" for instance in NITTER_INSTANCES],
        "priority": "MEDIUM",
        "domains": ["电动车", "高端化", "出海"],
        "category": "新能源汽车",
    },
    "NIO": {
        "name": "蔚来汽车官方",
        "rss_urls": [f"{instance}/NIO/rss" for instance in NITTER_INSTANCES],
        "priority": "MEDIUM",
        "domains": ["电动车", "换电"],
        "category": "新能源汽车",
    },
    "XPengMotors": {
        "name": "小鹏汽车官方",
        "rss_urls": [f"{instance}/XPengMotors/rss" for instance in NITTER_INSTANCES],
        "priority": "MEDIUM",
        "domains": ["智驾", "MONA"],
        "category": "新能源汽车",
    },
    
    # ==================== 宏观 & 创投 ====================
    "a16z": {
        "name": "a16z 官方",
        "rss_urls": [f"{instance}/a16z/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["AI", "Crypto", "Bio", "创投"],
        "category": "宏观/创投",
    },
    "benedictevans": {
        "name": "Benedict Evans (科技趋势分析)",
        "rss_urls": [f"{instance}/benedictevans/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["科技趋势", "宏观"],
        "category": "宏观/创投",
    },
    "mattlevine": {
        "name": "Matt Levine (Bloomberg 并购)",
        "rss_urls": [f"{instance}/mattlevine/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["并购", "资本运作"],
        "category": "宏观/创投",
    },
    "theinformation": {
        "name": "The Information (独家爆料)",
        "rss_urls": [f"{instance}/theinformation/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["独家", "爆料"],
        "category": "宏观/创投",
    },
    "BloombergTech": {
        "name": "Bloomberg Tech",
        "rss_urls": [f"{instance}/BloombergTech/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["科技新闻", "财经"],
        "category": "宏观/创投",
    },
    
    # ==================== 政治人物 ====================
    "realDonaldTrump": {
        "name": "特朗普",
        "rss_urls": [f"{instance}/realDonaldTrump/rss" for instance in NITTER_INSTANCES],
        "priority": "HIGH",
        "domains": ["政策", "关税", "政治"],
        "category": "政治",
    },
}

def fetch_nitter_rss(account: str, max_entries: int = 5) -> List[Dict[str, Any]]:
    """
    获取某个 X 账号的最新推文（使用 curl + 正则解析 RSS）
    
    Args:
        account: X 账号用户名（如 elonmusk）
        max_entries: 最多获取多少条推文
    
    Returns:
        推文列表
    """
    if account not in AUTHORITATIVE_X_RSS:
        return []
    
    account_info = AUTHORITATIVE_X_RSS[account]
    all_entries = []
    
    # 尝试多个 Nitter 实例
    for rss_url in account_info["rss_urls"]:
        try:
            # 使用 curl 获取 RSS
            cmd = ["curl", "-s", "-L", "-A", "Mozilla/5.0", "--max-time", "15", rss_url]
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=20)
            
            if result.returncode == 0 and result.stdout:
                rss_content = result.stdout
                
                # 解析 RSS item（简化版）
                items = re.findall(r'<item>(.*?)</item>', rss_content, re.DOTALL)
                
                for item in items[:max_entries]:
                    # 提取标题
                    title_match = re.search(r'<title>(.*?)</title>', item)
                    title = title_match.group(1) if title_match else "无标题"
                    
                    # 提取链接
                    link_match = re.search(r'<link>(.*?)</link>', item)
                    link = link_match.group(1) if link_match else ""
                    
                    # 提取描述
                    desc_match = re.search(r'<description>(.*?)</description>', item, re.DOTALL)
                    desc = desc_match.group(1) if desc_match else ""
                    # 清理 HTML 标签
                    desc = re.sub(r'<[^>]+>', '', desc)
                    
                    # 提取发布时间
                    pub_match = re.search(r'<pubDate>(.*?)</pubDate>', item)
                    pub_date = pub_match.group(1) if pub_match else ""
                    
                    tweet = {
                        "id": generate_tweet_id(link),
                        "title": title,
                        "summary": desc[:200],
                        "url": link,
                        "published": pub_date,
                        "author": account,
                        "author_name": account_info["name"],
                        "priority": account_info["priority"],
                        "domains": account_info["domains"],
                        "source_type": "权威 X 账号",
                        "source_url": rss_url,
                    }
                    
                    # 去重
                    if not any(e["id"] == tweet["id"] for e in all_entries):
                        all_entries.append(tweet)
                
                # 成功获取就停止尝试其他实例
                if all_entries:
                    break
                    
        except Exception as e:
            # 尝试下一个实例
            continue
    
    return all_entries

def generate_tweet_id(url: str) -> str:
    """生成推文唯一 ID"""
    hash_md5 = hashlib.md5(url.encode()).hexdigest()[:12]
    date_str = datetime.now().strftime("%Y%m%d")
    return f"x_{date_str}_{hash_md5}"

def convert_tweet_to_event(tweet: Dict) -> Dict:
    """将推文转换为事件格式"""
    return {
        "id": tweet["id"],
        "priority": tweet["priority"],
        "title": f"[X:{tweet['author_name']}] {tweet['title']}",
        "summary": tweet["summary"][:200] if tweet.get("summary") else tweet["title"],
        "tags": tweet.get("domains", []) + [f"X:{tweet['author']}"],
        "source_url": tweet["url"],
        "source_type": tweet["source_type"],
        "timestamp": datetime.now().isoformat() + "Z",
        "companies": tweet.get("domains", []),
        "trigger_next": tweet["priority"] == "HIGH",
        "x_account": tweet["author"],
        "x_account_name": tweet["author_name"],
    }

def scan_all_accounts() -> List[Dict]:
    """
    扫描所有权威 X 账号
    
    Returns:
        事件列表
    """
    all_events = []
    
    for account in AUTHORITATIVE_X_RSS.keys():
        tweets = fetch_nitter_rss(account, max_entries=3)
        
        for tweet in tweets:
            event = convert_tweet_to_event(tweet)
            all_events.append(event)
    
    return all_events

if __name__ == "__main__":
    # 测试
    print("测试 Nitter RSS 监控...")
    
    # 测试获取马斯克的推文
    tweets = fetch_nitter_rss("elonmusk", max_entries=3)
    
    if tweets:
        print(f"\n✅ 成功获取 {len(tweets)} 条推文:")
        for i, tweet in enumerate(tweets, 1):
            print(f"\n{i}. {tweet['title'][:100]}")
            print(f"   作者：{tweet['author_name']}")
            print(f"   链接：{tweet['url']}")
            print(f"   时间：{tweet['published']}")
    else:
        print("\n❌ 未能获取推文，可能是 Nitter 实例不可用")
    
    # 扫描所有账号
    print("\n\n扫描所有权威 X 账号...")
    events = scan_all_accounts()
    print(f"共获取 {len(events)} 个事件")
    
    high_priority = [e for e in events if e["priority"] == "HIGH"]
    print(f"High 优先级：{len(high_priority)}个")
    
    if high_priority:
        print("\nHigh 优先级事件:")
        for e in high_priority[:5]:
            print(f"  - {e['title'][:80]}...")
