#!/usr/bin/env python3
# =============================================================================
# TechPulse Scout - 科技脉搏·侦察兵
# 功能：轻量级扫描、去重过滤、重要性评分、结构化输出
# 执行频率：每 1-2 小时
# 输出：JSON 事件列表（仅 High/Medium）
# =============================================================================

import os
import sys
import json
import hashlib
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from difflib import SequenceMatcher

# ==================== 配置区域 ====================
WORKSPACE = Path("/home/admin/.openclaw/workspace")
SKILL_DIR = WORKSPACE / "skills" / "techpulse-scout"
SEARXNG_DIR = WORKSPACE / "skills" / "searxng"
LOG_FILE = SKILL_DIR / "logs" / "scout.log"
DATA_DIR = SKILL_DIR / "data"
EVENTS_FILE = DATA_DIR / "known_events.json"
OUTPUT_FILE = SKILL_DIR / "events" / f"events-{datetime.now().strftime('%Y%m%d-%H%M')}.json"

# 监控领域和关键词
MONITORED_DOMAINS = {
    # ==================== 科技产业 ====================
    "半导体": ["半导体", "芯片", "IC", "晶圆", "光刻机", "ASML", "中芯国际", "华为", "先进制程", "封装"],
    "人工智能": ["AI", "人工智能", "大模型", "GPT", "NVIDIA", "GPU", "HBM", "CoWoS", "Rubin", "Blackwell"],
    "新能源": ["光伏", "风电", "储能", "氢能", "太阳能", "宁德时代", "隆基", "通威"],
    "固态电池": ["固态电池", "半固态", "电解质", "硫化物", "氧化物", "清陶", "卫蓝", "QuantumScape", "丰田"],
    "新能源汽车": ["新能源汽车", "电动车", "EV", "比亚迪", "特斯拉", "销量", "渗透率", "800V", "超充"],
    "自动驾驶": ["自动驾驶", "FSD", "NOA", "激光雷达", "华为智驾", "小鹏", "特斯拉 FSD", "Robotaxi"],
    "人形机器人": ["人形机器人", "Optimus", "Tesla 机器人", "傅利叶", "宇树", "减速器", "伺服系统", "Figure"],
    "6G 通信": ["6G", "太赫兹", "卫星互联网", "星链", "华为 6G", "空天地一体化", "Starlink"],
    "量子计算": ["量子计算", "量子比特", "量子霸权", "IBM", "谷歌", "本源量子", "超导量子", "IonQ"],
    "低空经济": ["低空经济", "eVTOL", "飞行汽车", "亿航", "小鹏汇天", "峰飞", "Joby", " Archer"],
    "商业航天": ["商业航天", "火箭", "卫星", "SpaceX", "星舰", "蓝箭", "星际荣耀", "Rocket Lab"],
    "钙钛矿电池": ["钙钛矿", "叠层电池", "协鑫", "纤纳", "极电光能", "MicroLED"],
    
    # ==================== 金融市场（新增） ====================
    "股市波动": ["股市", "暴跌", "大涨", "跳水", "崩盘", "牛市", "熊市", "纳指", "标普", "道指", "上证", "恒生", "科技股"],
    "宏观经济": ["GDP", "通胀", "CPI", "PPI", " recession", "衰退", "经济", "宏观", "美联储", "央行"],
    "央行政策": ["美联储", "加息", "降息", "量化宽松", "缩表", "利率决议", "鲍威尔", "央行"],
    "大宗商品": ["原油", "黄金", "白银", "铜", "锂", "钴", "镍", "大宗商品", "期货"],
    "汇率波动": ["美元", "人民币", "汇率", "USD", "CNY", "日元", "欧元", "外汇"],
}

# 权威性评分（优化：X 平台权威账号单独分类）
SOURCE_AUTHORITY_SCORES = {
    "官方公告": 100,  # SEC/巨潮/港交所/公司官网
    "顶级财经": 85,   # Bloomberg/Reuters/WSJ/财新
    "权威 X 账号": 80,  # 马斯克/OpenAI/特朗普/公司官方 X
    "科技媒体": 75,   # 36Kr/AnandTech/EE Times
    "主流财经": 65,   # 东方财富/同花顺/新浪财经
    "普通 X 账号": 50,  # 一般 X 用户
    "社交媒体": 35,   # 知乎/微博
    "未知来源": 50,
}

# 重要性阈值（优化后）
PRIORITY_THRESHOLDS = {
    "HIGH": 70,    # 官方公告/顶级财经 + 突破关键词
    "MEDIUM": 45,  # 权威媒体/科技媒体 + 一定影响
    "LOW": 0,      # 其他
}

# 突破关键词（提升优先级）
BREAKTHROUGH_KEYWORDS = [
    "突破", "量产", "发布", "上市", "获批", "签约", "中标", "首发",
    "新一代", "革命性", "重大进展", "正式", "宣布", "启动", "确认",
]

# 权威 X 账号白名单（投资合伙人指定高价值信源）
# 分类：AI/大模型 | 半导体/硬件 | 新能源汽车/自动驾驶 | 宏观/创投
AUTHORITATIVE_X_ACCOUNTS = {
    # ==================== 1. 人工智能 (AI) & 大模型 ====================
    "sama": "Sam Altman (OpenAI CEO) - GPT 系列/算力合作",
    "elonmusk": "Elon Musk (xAI/Tesla AI/Optimus) - FSD/Dojo 超算",
    "ylecun": "Yann LeCun (Meta 首席 AI 科学家) - 开源派/技术瓶颈",
    "karpathy": "Andrej Karpathy (Eureka Labs) - LLM 原理/训练细节",
    "DarioAmodei": "Dario Amodei (Anthropic CEO) - AI 安全/Claude",
    "JensenHuang": "Jensen Huang (NVIDIA) - GPU 出货/新架构",
    "runwayml": "Runway ML - 视频生成/Sora 类技术",
    "OpenAI": "OpenAI 官方",
    "AnthropicAI": "Anthropic (Claude) 官方",
    "nvidia": "NVIDIA 官方",
    "MetaAI": "Meta AI 官方",
    
    # ==================== 2. 半导体 & 硬件制造 ====================
    "TSMC": "台积电官方 - 扩产计划/财报",
    "ASML": "ASML 官方 - EUV 设备交付",
    "patgelsinger": "Pat Gelsinger (Intel CEO) - IDM 2.0",
    "LisaSu": "Lisa Su (AMD CEO) - AI 芯片/数据中心",
    "SemiAnalysis": "SemiAnalysis (Dylan Patel) - 硬核半导体分析",
    "ICInsights": "IC Insights - 半导体市场数据",
    "AMD": "AMD 官方",
    "Intel": "Intel 官方",
    
    # ==================== 3. 新能源汽车 (EV) & 自动驾驶 ====================
    "Tesla": "Tesla 官方 - Battery Day/FSD",
    "TeslaAI": "Tesla AI 官方",
    "LiBin_CN": "李斌 (蔚来) - 换电联盟",
    "NIO": "蔚来汽车官方",
    "XPengMotors": "小鹏汽车 - 智驾/MONA 系列",
    "BYDCompany": "比亚迪 - 高端化/出海",
    "CathieDWood": "Cathie Wood (ARK Invest) - Tesla 估值/Big Ideas",
    "SawyerMerritt": "Sawyer Merritt - Tesla/EV 数据分析",
    
    # ==================== 4. 宏观、创投与深度分析 ====================
    "a16z": "a16z 官方 - AI/Crypto/Bio 布局",
    "bhorowitz": "Ben Horowitz (a16z) - 创投趋势",
    "msacks": "Marc Sacks (a16z) - 投资洞察",
    "benedictevans": "Benedict Evans - 科技趋势宏观分析",
    "mattlevine": "Matt Levine (Bloomberg) - 科技并购/资本运作",
    "theinformation": "The Information - 独家重磅爆料",
    "technology": "Bloomberg Tech - 实时财经科技新闻",
    
    # ==================== 5. 政治人物 ====================
    "realDonaldTrump": "特朗普 - 政策/关税",
    "POTUS": "美国总统官方",
    "WhiteHouse": "白宫官方",
    
    # ==================== 6. 科技媒体 ====================
    "BloombergTech": "彭博科技",
    "ReutersTech": "路透科技",
    "WSJ": "华尔街日报",
}

# 权威 X 账号域名模式
AUTHORITATIVE_X_PATTERNS = [
    "twitter.com/elonmusk",
    "twitter.com/OpenAI",
    "twitter.com/sama",
    "twitter.com/AnthropicAI",
    "twitter.com/DarioAmodei",
    "twitter.com/realDonaldTrump",
    "twitter.com/BloombergTech",
    "twitter.com/ReutersTech",
    "twitter.com/NVIDIA",
    "twitter.com/Tesla",
    "twitter.com/SpaceX",
    "x.com/elonmusk",
    "x.com/OpenAI",
    # Nitter 实例（X 的开源前端，无需 API）
    "nitter.net/elonmusk",
    "nitter.net/OpenAI",
    "nitter.net/sama",
    "nitter.net/realDonaldTrump",
    "nitter.net/NVIDIA",
    "nitter.net/Tesla",
    "nitter.net/SpaceX",
]

# Nitter 实例列表（X 的开源前端，无需 API 密钥）
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacy.com.de",
    "https://nitter.lunar.icu",
    "https://nitter.dark.fail",
]

# ==================== 日志函数 ====================
def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

# ==================== 工具函数 ====================
def generate_event_id(title: str, source: str, timestamp: str) -> str:
    """生成事件唯一 ID"""
    content = f"{title}:{source}:{timestamp}"
    hash_md5 = hashlib.md5(content.encode()).hexdigest()[:12]
    date_str = datetime.now().strftime("%Y%m%d")
    return f"evt_{date_str}_{hash_md5}"

def classify_source(url: str) -> str:
    """分类信息来源（优化：识别 Nitter/X 账号）"""
    url_lower = url.lower()
    
    # 官方公告
    if any(d in url_lower for d in ["cninfo.com.cn", "sec.gov", "hkexnews.hk", "sse.com.cn", "szse.cn"]):
        return "官方公告"
    
    # 顶级财经
    if any(d in url_lower for d in ["bloomberg.com", "reuters.com", "wsj.com", "caixin.com"]):
        return "顶级财经"
    
    # 权威 X 账号（包括 Nitter）
    if any("twitter.com/" in url_lower or "x.com/" in url_lower or "nitter.net/" in url_lower for _ in [1]):
        for pattern in AUTHORITATIVE_X_PATTERNS:
            if pattern in url_lower:
                return "权威 X 账号"
        # 检查是否在白名单中
        for account in AUTHORITATIVE_X_ACCOUNTS.keys():
            if any(f"{domain}/{account.lower()}" in url_lower for domain in ["twitter.com", "x.com", "nitter.net"]):
                return "权威 X 账号"
        # 普通 X 账号
        return "普通 X 账号"
    
    # 科技媒体
    if any(d in url_lower for d in ["36kr.com", "anandtech.com", "eetimes.com", "techcrunch.com"]):
        return "科技媒体"
    
    # 主流财经
    if any(d in url_lower for d in ["eastmoney.com", "10jqka.com.cn", "sina.com.cn", "cls.cn", "stcn.com"]):
        return "主流财经"
    
    # 社交媒体
    if any(d in url_lower for d in ["zhihu.com", "weibo.com"]):
        return "社交媒体"
    
    return "未知来源"

def calculate_priority_score(news: Dict, domain: str) -> int:
    """计算重要性评分（优化后）"""
    score = 0
    
    # 1. 来源权威性 (0-60 分) - 提高权重
    source_type = classify_source(news.get("url", ""))
    base_score = SOURCE_AUTHORITY_SCORES.get(source_type, 50)
    
    if source_type == "官方公告":
        score += 60  # 官方公告直接高分
    elif source_type == "顶级财经":
        score += 50
    elif source_type == "科技媒体":
        score += 40
    elif source_type == "主流财经":
        score += 35
    else:
        score += 20
    
    # 2. 突破关键词 (0-30 分)
    text = (news.get("title", "") + " " + news.get("content", "")).lower()
    breakthrough_count = sum(1 for kw in BREAKTHROUGH_KEYWORDS if kw.lower() in text)
    score += min(breakthrough_count * 10, 30)
    
    # 3. 领域相关性 (0-10 分)
    domain_keywords = MONITORED_DOMAINS.get(domain, [])
    relevance = sum(1 for kw in domain_keywords if kw.lower() in text)
    score += min(relevance * 2, 10)
    
    return int(min(score, 100))

def get_priority(score: int) -> str:
    """根据评分确定优先级"""
    if score >= PRIORITY_THRESHOLDS["HIGH"]:
        return "HIGH"
    elif score >= PRIORITY_THRESHOLDS["MEDIUM"]:
        return "MEDIUM"
    else:
        return "LOW"

def extract_tags(domain: str, text: str) -> List[str]:
    """提取标签（优化：识别 X 账号）"""
    tags = [domain]
    
    # 提取公司名
    companies = ["NVIDIA", "特斯拉", "比亚迪", "宁德时代", "华为", "ASML", "台积电", "英特尔", "AMD", "OpenAI", "Anthropic", "SpaceX"]
    for company in companies:
        if company.lower() in text.lower():
            tags.append(company)
    
    # 提取技术关键词
    tech_keywords = ["HBM", "CoWoS", "GAA", "EUV", "FSD", "eVTOL", "6G", "量子"]
    for kw in tech_keywords:
        if kw.lower() in text.lower():
            tags.append(kw)
    
    # 识别 X 账号（关键人物）
    x_accounts = {
        "elonmusk": "马斯克",
        "OpenAI": "OpenAI",
        "sama": "Sam Altman",
        "AnthropicAI": "Anthropic",
        "realDonaldTrump": "特朗普",
        "NVIDIA": "NVIDIA 官方",
        "Tesla": "Tesla 官方",
        "SpaceX": "SpaceX 官方",
    }
    for account, name in x_accounts.items():
        if f"twitter.com/{account}" in text.lower() or f"x.com/{account}" in text.lower():
            tags.append(f"X:{name}")
    
    return list(set(tags))[:8]  # 最多 8 个标签

def is_duplicate(new_event: Dict, known_events: List[Dict], hours: int = 24) -> bool:
    """检查是否重复"""
    cutoff_time = datetime.now() - timedelta(hours=hours)
    
    for event in known_events:
        # 时间检查
        try:
            event_time = datetime.fromisoformat(event.get("timestamp", "").replace("Z", "+00:00"))
            if event_time < cutoff_time:
                continue
        except:
            continue
        
        # 标题相似度检查
        similarity = SequenceMatcher(None, new_event["title"], event["title"]).ratio()
        if similarity > 0.8:
            return True
        
        # URL 相同检查
        if new_event.get("source_url") == event.get("source_url"):
            return True
    
    return False

def load_known_events() -> List[Dict]:
    """加载已知事件"""
    if EVENTS_FILE.exists():
        try:
            with open(EVENTS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return []
    return []

def save_known_events(events: List[Dict]):
    """保存已知事件"""
    EVENTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    # 只保留最近 7 天的事件
    cutoff = datetime.now() - timedelta(days=7)
    filtered = []
    for event in events:
        try:
            event_time = datetime.fromisoformat(event.get("timestamp", "").replace("Z", "+00:00"))
            if event_time > cutoff:
                filtered.append(event)
        except:
            filtered.append(event)
    
    with open(EVENTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(filtered, f, ensure_ascii=False, indent=2)

# ==================== 核心功能 ====================
def scan_domain(domain: str, keywords: List[str]) -> List[Dict]:
    """扫描某个领域的新闻（优化：自动选择最佳数据源）"""
    all_results = []
    
    # 获取最佳数据源（Nitter 或国内替代）
    from nitter_health_check import get_best_source
    best_source = get_best_source()
    
    log(f"  数据源：{best_source['source_type']} ({'Nitter' if best_source['source_type'] == 'nitter' else '国内替代'})")
    
    # 构建搜索查询
    queries = []
    
    for kw in keywords[:4]:
        # 权威财经媒体（始终包含）
        queries.append(f"{kw} site:cls.cn")  # 财联社
        queries.append(f"{kw} site:stcn.com")  # 证券时报
        queries.append(f"{kw} site:bloomberg.com")  # 彭博
        
        # 根据数据源类型添加特定查询
        if best_source["source_type"] == "nitter" and best_source.get("source_url"):
            # Nitter 可用，添加 X 平台查询
            nitter_domain = best_source["source_url"].replace("https://", "")
            queries.append(f"{kw} site:{nitter_domain}/elonmusk")
            queries.append(f"{kw} site:{nitter_domain}/OpenAI")
        else:
            # Nitter 不可用，使用国内替代源
            queries.append(f"{kw} site:wallstreetcn.com")  # 华尔街见闻
            queries.append(f"{kw} site:36kr.com")  # 36 氪
        
        # 通用搜索（备选）
        queries.append(f"{kw} 最新进展 2026")
    
    for query in queries[:15]:
        try:
            cmd = ["uv", "run", "scripts/searxng.py", "search", query, "-n", "3", "--format", "json"]
            result = subprocess.run(cmd, cwd=SEARXNG_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=60)
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    for r in data.get("results", [])[:2]:
                        news = {
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "content": r.get("content", ""),
                            "domain": domain,
                        }
                        # 去重 + 过滤低质
                        if news["url"] not in [n["url"] for n in all_results]:
                            # 过滤知乎问答/维基/百度百科
                            if any(x in news["url"].lower() for x in ["zhihu.com/question", "wikipedia", "baike.baidu.com"]):
                                continue
                            all_results.append(news)
                except:
                    pass
        except Exception as e:
            log(f"  搜索失败：{str(e)[:50]}")
        
        if len(all_results) >= 12:
            break
    
    return all_results[:12]

def process_news(news: Dict, known_events: List[Dict]) -> Optional[Dict]:
    """处理单条新闻，生成事件"""
    domain = news.get("domain", "未知")
    
    # 计算评分
    score = calculate_priority_score(news, domain)
    priority = get_priority(score)
    
    # 生成事件
    event = {
        "id": generate_event_id(news["title"], news["url"], datetime.now().isoformat()),
        "priority": priority,
        "title": news["title"],
        "summary": news["content"][:200] if news.get("content") else news["title"],
        "tags": extract_tags(domain, news["title"] + " " + news.get("content", "")),
        "source_url": news["url"],
        "source_type": classify_source(news["url"]),
        "timestamp": datetime.now().isoformat() + "Z",
        "companies": [t for t in extract_tags(domain, news["title"] + " " + news.get("content", "")) if t not in MONITORED_DOMAINS],
        "score": score,
        "trigger_next": priority in ["HIGH", "MEDIUM"],
    }
    
    # 去重检查
    if is_duplicate(event, known_events):
        log(f"  跳过重复：{event['title'][:50]}...")
        return None
    
    return event

# ==================== 主流程 ====================
def main():
    """主入口"""
    log("=" * 60)
    log("TechPulse Scout - 科技脉搏·侦察兵启动")
    log("=" * 60)
    
    try:
        # 先检测 Nitter 实例可用性
        log("检测数据源可用性...")
        from nitter_health_check import check_all_nitter_instances, save_status, get_best_source
        
        nitter_status = check_all_nitter_instances()
        save_status(nitter_status)
        
        best_source = get_best_source()
        if best_source["source_type"] == "nitter":
            log(f"✅ 使用 Nitter: {best_source['source_url']}")
        else:
            log(f"🔄 使用国内替代源：财联社/华尔街见闻/36 氪")
        
        # 加载已知事件
        known_events = load_known_events()
        log(f"已知事件库：{len(known_events)}条")
        
        # 扫描所有领域
        all_events = []
        for domain, keywords in MONITORED_DOMAINS.items():
            log(f"扫描：{domain}...")
            news_list = scan_domain(domain, keywords)
            
            for news in news_list:
                event = process_news(news, known_events)
                if event:
                    all_events.append(event)
                    log(f"  + {event['priority']}: {event['title'][:50]}...")
        
        # 按优先级排序
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        all_events.sort(key=lambda x: (priority_order.get(x["priority"], 3), -x["score"]))
        
        # 分离 High/Medium 和 Low
        high_medium_events = [e for e in all_events if e["priority"] in ["HIGH", "MEDIUM"]]
        low_events = [e for e in all_events if e["priority"] == "LOW"]
        
        # 保存已知事件
        all_known = known_events + all_events
        save_known_events(all_known)
        
        # 生成输出
        output = {
            "scan_time": datetime.now().isoformat() + "Z",
            "next_scan": (datetime.now() + timedelta(hours=2)).isoformat() + "Z",
            "total_scanned": len(MONITORED_DOMAINS),
            "total_events": len(all_events),
            "high_priority": len([e for e in all_events if e["priority"] == "HIGH"]),
            "medium_priority": len([e for e in all_events if e["priority"] == "MEDIUM"]),
            "low_priority": len(low_events),
            "events": high_medium_events,  # 只输出 High/Medium
            "trigger_techchain": len(high_medium_events) > 0,
            "events_for_analysis": [e["id"] for e in high_medium_events if e.get("trigger_next")],
        }
        
        # 保存输出
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        log(f"输出已保存：{OUTPUT_FILE}")
        
        # 输出摘要
        log("=" * 60)
        log(f"扫描完成：{len(MONITORED_DOMAINS)}个领域，发现{len(all_events)}个事件")
        log(f"High: {output['high_priority']}, Medium: {output['medium_priority']}, Low: {output['low_priority']}")
        
        if high_medium_events:
            log(f"\n触发 TechChain Insight: ✅")
            log(f"待分析事件：{len(high_medium_events)}个")
            for e in high_medium_events[:5]:
                log(f"  - [{e['priority']}] {e['title'][:60]}...")
        else:
            log(f"\n触发 TechChain Insight: ❌")
            log(f"无 High/Medium 事件，流程结束")
        
        log("=" * 60)
        
    except Exception as e:
        log(f"❌ 执行异常：{str(e)}")
        import traceback
        log(traceback.format_exc())

if __name__ == "__main__":
    main()
