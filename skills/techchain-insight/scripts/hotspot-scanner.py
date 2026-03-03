#!/usr/bin/env python3
# =============================================================================
# TechChain Hotspot Scanner - 科技热点捕捉技能
# 功能：快速扫描全球科技热点，识别突发事件和重大进展
# 执行频率：每 2 小时
# 输出：热点列表（供 TechChain Insight 深度分析）
# =============================================================================

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# ==================== 配置区域 ====================
WORKSPACE = Path("/home/admin/.openclaw/workspace")
SKILL_DIR = WORKSPACE / "skills" / "techchain-insight"
SEARXNG_DIR = WORKSPACE / "skills" / "searxng"
LOG_FILE = SKILL_DIR / "logs" / "hotspot-scanner.log"
OUTPUT_FILE = SKILL_DIR / "hotspots" / f"hotspots-{datetime.now().strftime('%Y%m%d-%H%M')}.json"

# 监控领域和关键词
MONITORED_TOPICS = {
    "固态电池": ["固态电池", "半固态", "电解质", "硫化物", "氧化物", "清陶", "卫蓝", "QuantumScape", "丰田"],
    "AI 芯片": ["AI 芯片", "GPU", "HBM", "CoWoS", "Blackwell", "NVIDIA", "AMD", "寒武纪", "海光"],
    "人形机器人": ["人形机器人", "Optimus", "Tesla 机器人", "傅利叶", "宇树", "减速器", "伺服系统"],
    "半导体": ["半导体", "光刻机", "ASML", "EUV", "国产替代", "中芯国际", "华为", "先进制程"],
    "新能源汽车": ["新能源汽车", "电动车", "比亚迪", "特斯拉", "销量", "渗透率", "800V"],
    "自动驾驶": ["自动驾驶", "FSD", "NOA", "激光雷达", "华为智驾", "小鹏", "特斯拉 FSD"],
    "量子计算": ["量子计算", "量子比特", "量子霸权", "IBM", "谷歌", "本源量子", "超导量子"],
    "6G 通信": ["6G", "太赫兹", "卫星互联网", "星链", "华为 6G", "空天地一体化"],
    "低空经济": ["低空经济", "eVTOL", "飞行汽车", "亿航", "小鹏汇天", "峰飞", "Joby"],
    "商业航天": ["商业航天", "火箭", "卫星", "SpaceX", "星舰", "蓝箭", "星际荣耀"],
    "钙钛矿电池": ["钙钛矿", "叠层电池", "协鑫", "纤纳", "极电光能"],
    "合成生物": ["合成生物", "基因编辑", "CRISPR", "凯赛生物", "华恒生物", "生物制造"],
}

# 热点判定阈值
HOTSPOT_THRESHOLDS = {
    "min_news_count": 3,  # 最少新闻数量
    "has_breakthrough": False,  # 是否有突破关键词
    "has_official": False,  # 是否有官方公告
    "time_window_hours": 48,  # 时间窗口（小时）
}

# 突破关键词（触发深度分析）
BREAKTHROUGH_KEYWORDS = [
    "突破", "量产", "发布", "上市", "获批", "签约", "中标", "首发",
    "新一代", "革命性", "重大进展", "正式", "宣布", "启动",
]

# ==================== 日志函数 ====================
def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

# ==================== 搜索新闻 ====================
def search_topic_news(topic: str, keywords: List[str], hours: int = 48) -> List[Dict]:
    """搜索某个主题的新闻"""
    all_results = []
    
    # 构建搜索查询
    queries = []
    for kw in keywords[:3]:  # 取前 3 个关键词
        queries.append(f"{kw} 最新进展 2026")
        queries.append(f"{kw} 突破 量产 发布")
    
    for query in queries[:4]:  # 最多 4 个查询
        try:
            cmd = ["uv", "run", "scripts/searxng.py", "search", query, "-n", "5", "--format", "json"]
            result = subprocess.run(cmd, cwd=SEARXNG_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=60)
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    for r in data.get("results", [])[:3]:
                        news = {
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "content": r.get("content", ""),
                            "source": r.get("url", "").split("/")[2] if r.get("url") else "未知",
                            "query": query,
                        }
                        # 去重
                        if news["url"] not in [n["url"] for n in all_results]:
                            all_results.append(news)
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            log(f"  搜索失败：{str(e)[:50]}")
        
        if len(all_results) >= 10:  # 最多 10 条
            break
    
    return all_results[:10]

# ==================== 热点判定 ====================
def is_hotspot(topic: str, news_list: List[Dict]) -> Dict:
    """
    判定是否为热点
    返回：{is_hot: bool, score: 0-100, reason: str}
    """
    if not news_list:
        return {"is_hot": False, "score": 0, "reason": "无相关新闻"}
    
    score = 0
    reasons = []
    
    # 1. 新闻数量评分（0-40 分）
    news_count = len(news_list)
    if news_count >= 10:
        score += 40
        reasons.append(f"新闻数量多 ({news_count}条)")
    elif news_count >= 5:
        score += 25
        reasons.append(f"新闻数量中等 ({news_count}条)")
    elif news_count >= 3:
        score += 15
        reasons.append(f"新闻数量较少 ({news_count}条)")
    else:
        return {"is_hot": False, "score": score, "reason": "新闻数量不足"}
    
    # 2. 突破关键词评分（0-30 分）
    has_breakthrough = False
    for news in news_list:
        text = (news["title"] + " " + news["content"]).lower()
        for kw in BREAKTHROUGH_KEYWORDS:
            if kw.lower() in text:
                has_breakthrough = True
                break
        if has_breakthrough:
            break
    
    if has_breakthrough:
        score += 30
        reasons.append("含突破关键词")
    
    # 3. 来源权威性评分（0-30 分）
    authoritative_domains = ["cninfo.com.cn", "sec.gov", "cls.cn", "stcn.com", "bloomberg.com", "reuters.com"]
    has_authoritative = any(any(domain in news["url"].lower() for domain in authoritative_domains) for news in news_list)
    
    if has_authoritative:
        score += 30
        reasons.append("含权威来源")
    else:
        score += 15
        reasons.append("来源一般")
    
    # 判定是否为热点
    is_hot = score >= 50
    
    return {
        "is_hot": is_hot,
        "score": score,
        "reason": ", ".join(reasons),
        "news_count": news_count,
        "has_breakthrough": has_breakthrough,
        "has_authoritative": has_authoritative,
    }

# ==================== 生成热点报告 ====================
def generate_hotspot_report(hotspots: List[Dict]) -> Dict:
    """生成热点报告"""
    report = {
        "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "next_scan": (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%d %H:%M"),
        "total_topics_scanned": len(MONITORED_TOPICS),
        "hotspots_found": len(hotspots),
        "hotspots": hotspots,
        "recommended_for_analysis": [h["topic"] for h in hotspots if h["score"] >= 70],
    }
    return report

# ==================== 主流程 ====================
def main():
    """主入口"""
    log("=" * 60)
    log("TechChain Hotspot Scanner - 热点捕捉启动")
    log("=" * 60)
    
    try:
        hotspots = []
        
        # 扫描所有主题
        for topic, keywords in MONITORED_TOPICS.items():
            log(f"扫描：{topic}...")
            
            # 搜索新闻
            news_list = search_topic_news(topic, keywords)
            
            # 判定热点
            hotspot_result = is_hotspot(topic, news_list)
            
            log(f"  评分：{hotspot_result['score']} - {hotspot_result['reason']}")
            
            if hotspot_result["is_hot"]:
                hotspots.append({
                    "topic": topic,
                    "score": hotspot_result["score"],
                    "reason": hotspot_result["reason"],
                    "news_count": hotspot_result["news_count"],
                    "has_breakthrough": hotspot_result["has_breakthrough"],
                    "news_samples": news_list[:3],  # 前 3 条新闻摘要
                })
        
        # 按评分排序
        hotspots.sort(key=lambda x: x["score"], reverse=True)
        
        # 生成报告
        report = generate_hotspot_report(hotspots)
        
        # 保存报告
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        log(f"报告已保存：{OUTPUT_FILE}")
        
        # 输出摘要
        log("=" * 60)
        log(f"扫描完成：共扫描{len(MONITORED_TOPICS)}个主题，发现{len(hotspots)}个热点")
        if hotspots:
            log("热点列表（按评分排序）:")
            for h in hotspots[:5]:
                log(f"  - {h['topic']}: {h['score']}分 ({h['reason']})")
            log(f"\n推荐深度分析：{report['recommended_for_analysis']}")
        else:
            log("本次扫描未发现热点，暂无需深度分析")
        log("=" * 60)
        
    except Exception as e:
        log(f"❌ 执行异常：{str(e)}")
        import traceback
        log(traceback.format_exc())

if __name__ == "__main__":
    main()
