#!/usr/bin/env python3
# =============================================================================
# TechChain Insight - 科技链·热点透视
# 功能：科技热点分析 → 产业链拆解 → 资本市场映射
# 版本：1.0.0
# =============================================================================

import os
import sys
import json
import subprocess
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

# ==================== 配置区域 ====================
WORKSPACE = Path(os.environ.get("WORKSPACE", Path.home() / ".openclaw" / "workspace"))
SKILL_DIR = WORKSPACE / "skills" / "techchain-insight"
SEARXNG_DIR = WORKSPACE / "skills" / "searxng"
LOG_FILE = SKILL_DIR / "logs" / "techchain.log"

# 覆盖领域
DOMAINS = ["半导体", "人工智能", "AI", "新能源", "新能源汽车", "自动驾驶", "固态电池", "芯片", "光刻机"]

# 加载知识库
def load_knowledge_base():
    """加载产业链和公司知识库"""
    industry_file = SKILL_DIR / "knowledge_base" / "industry_chain.json"
    companies_file = SKILL_DIR / "knowledge_base" / "companies.json"
    
    industry_chain = {}
    companies = {}
    
    try:
        if industry_file.exists():
            with open(industry_file, 'r', encoding='utf-8') as f:
                industry_chain = json.load(f)
    except Exception as e:
        log(f"加载产业链知识库失败：{str(e)}")
    
    try:
        if companies_file.exists():
            with open(companies_file, 'r', encoding='utf-8') as f:
                companies = json.load(f)
    except Exception as e:
        log(f"加载公司知识库失败：{str(e)}")
    
    return industry_chain, companies

# 全局知识库
INDUSTRY_CHAIN_KNOWLEDGE = {}
COMPANY_KNOWLEDGE = {}

# 延迟加载
def get_knowledge():
    """获取知识库（延迟加载）"""
    global INDUSTRY_CHAIN_KNOWLEDGE, COMPANY_KNOWLEDGE
    if not INDUSTRY_CHAIN_KNOWLEDGE:
        INDUSTRY_CHAIN_KNOWLEDGE, COMPANY_KNOWLEDGE = load_knowledge_base()
    return INDUSTRY_CHAIN_KNOWLEDGE, COMPANY_KNOWLEDGE

# ==================== 日志函数 ====================
def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg, file=sys.stderr)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

# ==================== 搜索模块 ====================
def calculate_credibility_score(news: Dict[str, Any], keyword: str) -> int:
    """
    计算新闻可信度评分（0-100）
    考虑因素：来源权威性、时效性、内容质量、多源验证
    """
    score = 50  # 基础分
    
    url = news.get("url", "").lower()
    title = news.get("title", "").lower()
    content = news.get("content", "").lower()
    text = title + " " + content
    
    # 1. 来源权威性（+0 到 +30 分）
    authoritative_sources = {
        "gov.cn": 30, "sec.gov": 30,  # 政府/监管
        "bloomberg.com": 25, "reuters.com": 25, "wsj.com": 25,  # 顶级财经
        "cls.cn": 20, "stcn.com": 20, "cs.com.cn": 20,  # 国内权威
        "eastmoney.com": 15, "sina.com.cn": 15, "36kr.com": 15,  # 主流财经
        "zhihu.com": 5, "weibo.com": 3,  # 社交媒体（低分）
    }
    
    for domain, points in authoritative_sources.items():
        if domain in url:
            score += points
            break
    
    # 2. 时效性（+0 到 +20 分）
    time_keywords = ["今日", "今天", "刚刚", "最新", "2026", "3 月", "03 月"]
    if any(kw in text for kw in time_keywords):
        score += 20
    elif "2025" in text:
        score += 10
    
    # 3. 内容质量（+0 到 +20 分）
    # 有具体数据/数字加分
    if re.search(r'\d+', text):
        score += 10
    # 有公司名称加分
    if re.search(r'[公司厂集团股份]', text):
        score += 10
    # 标题长度适中（10-50 字）
    if 10 <= len(news.get("title", "")) <= 50:
        score += 5
    
    # 4. 关键词相关性（+0 到 +30 分）
    keyword_lower = keyword.lower()
    if keyword_lower in title:
        score += 20
    elif keyword_lower in content:
        score += 10
    
    # 5. 负面信号（减分）
    negative_signals = ["广告", "推广", "赞助", "营销", "点击", "分享", "收藏"]
    if any(kw in text for kw in negative_signals):
        score -= 20
    
    # 6. 可疑来源（减分）
    suspicious_domains = ["blogspot", "wordpress", "medium", "wattpad", "archiveofourown"]
    if any(domain in url for domain in suspicious_domains):
        score -= 30
    
    return max(0, min(100, score))

def verify_information(news_list: List[Dict[str, Any]], keyword: str) -> List[Dict[str, Any]]:
    """
    验证信息并添加可信度评分
    """
    verified_results = []
    
    for news in news_list:
        credibility = calculate_credibility_score(news, keyword)
        news["credibility_score"] = credibility
        
        # 标记可信度等级
        if credibility >= 80:
            news["credibility_level"] = "高"
        elif credibility >= 60:
            news["credibility_level"] = "中"
        elif credibility >= 40:
            news["credibility_level"] = "低"
        else:
            news["credibility_level"] = "可疑"
        
        verified_results.append(news)
    
    # 按可信度排序
    verified_results.sort(key=lambda x: x["credibility_score"], reverse=True)
    
    # 统计可信度分布
    high_cred = sum(1 for n in verified_results if n["credibility_score"] >= 80)
    low_cred = sum(1 for n in verified_results if n["credibility_score"] < 40)
    
    log(f"可信度验证：高={high_cred}, 中={len(verified_results)-high_cred-low_cred}, 低/可疑={low_cred}")
    
    return verified_results

def search_news(keyword: str, hours: int = 48) -> List[Dict[str, Any]]:
    """搜索最新新闻（带验证）"""
    log(f"正在搜索：{keyword}...")
    
    queries = [
        f"{keyword} 最新进展 2026",
        f"{keyword} 供应链 供应商",
        f"{keyword} 受益公司 龙头",
        f"{keyword} 产业链 影响",
    ]
    
    all_results = []
    
    for query in queries:
        try:
            cmd = ["uv", "run", "scripts/searxng.py", "search", query, "-n", "10", "--format", "json"]
            result = subprocess.run(cmd, cwd=SEARXNG_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=60)
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    for r in data.get("results", [])[:5]:
                        all_results.append({
                            "title": r.get("title", ""),
                            "url": r.get("url", ""),
                            "content": r.get("content", ""),
                            "source": extract_source(r.get("url", "")),
                        })
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            log(f"搜索失败：{str(e)[:50]}")
    
    # 去重
    seen_urls = set()
    unique_results = []
    for r in all_results:
        if r["url"] not in seen_urls:
            unique_results.append(r)
            seen_urls.add(r["url"])
    
    # 验证信息并添加可信度评分
    verified_results = verify_information(unique_results, keyword)
    
    log(f"找到 {len(verified_results)} 条相关新闻（已验证）")
    return verified_results[:15]

def extract_source(url: str) -> str:
    """提取来源名称"""
    domain_map = {
        "bloomberg.com": "彭博社", "reuters.com": "路透社", "36kr.com": "36 氪",
        "eastmoney.com": "东方财富", "sina.com.cn": "新浪财经", "cls.cn": "财联社",
        "stcn.com": "证券时报", "cs.com.cn": "中国证券报", "anandtech.com": "AnandTech",
        "eetimes.com": "EE Times", "sec.gov": "SEC 公告",
    }
    for domain, name in domain_map.items():
        if domain in url.lower():
            return name
    try:
        from urllib.parse import urlparse
        return urlparse(url).netloc.replace("www.", "")
    except:
        return "未知来源"

# ==================== 增强分析模块导入 ====================
try:
    from enhanced_analysis import (
        classify_source,
        verify_with_multiple_sources,
        extract_entities,
        analyze_competition,
        format_with_citations,
        comprehensive_verification
    )
    ENHANCED_ANALYSIS_ENABLED = True
    log("增强分析模块已加载")
except Exception as e:
    log(f"增强分析模块加载失败：{str(e)[:100]}")
    ENHANCED_ANALYSIS_ENABLED = False

# ==================== 事件摘要模块导入 ====================
try:
    from event_summary import extract_event_summary, get_impact_priority, generate_segment_analysis
    EVENT_SUMMARY_ENABLED = True
    log("事件摘要模块已加载")
except Exception as e:
    log(f"事件摘要模块加载失败：{str(e)[:100]}")
    EVENT_SUMMARY_ENABLED = False

# ==================== 影响分析器导入 ====================
try:
    from impact_analyzer import analyze_chain_impact, detect_event_type, get_segment_impact
    IMPACT_ANALYZER_ENABLED = True
    log("影响分析器已加载")
except Exception as e:
    log(f"影响分析器加载失败：{str(e)[:100]}")
    IMPACT_ANALYZER_ENABLED = False

# ==================== 产业链分析模块 ====================
def match_domain(keyword: str) -> tuple:
    """
    匹配最相关的领域（优化版）
    返回：(领域名称，置信度 0-100)
    """
    # 确保知识库已加载
    get_knowledge()
    
    keyword_lower = keyword.lower()
    
    # 精确匹配（置信度 100）
    for domain in INDUSTRY_CHAIN_KNOWLEDGE.keys():
        if domain in keyword_lower:
            return (domain, 100)
    
    # 模糊匹配（按关键词匹配度评分）
    domain_keywords = {
        "半导体": {"芯片", "IC", "晶圆", "光刻", "刻蚀", "封装", "半导体", "制程", "纳米"},
        "人工智能": {"AI", "大模型", "GPT", "机器学习", "深度学习", "神经网络", "AIGC"},
        "新能源": {"光伏", "风电", "储能", "氢能", "太阳能", "风能"},
        "固态电池": {"固态", "电解质", "半固态", "凝聚态", "锂金属"},
        "新能源汽车": {"电动车", "EV", "新能源汽", "插混", "增程"},
        "自动驾驶": {"自动驾驶", "无人驾驶", "智能驾驶", "激光雷达", "NOA", "FSD"},
        "6G 通信": {"6G", "太赫兹", "通信", "卫星互联网"},
        "量子计算": {"量子", "量子比特", "qubit", "量子霸权"},
        "人形机器人": {"人形机器人", "机器人", "伺服", "减速器", "Optimus"},
        "商业航天": {"商业航天", "火箭", "卫星", "发射", "太空"},
        "合成生物": {"合成生物", "基因", "发酵", "菌种", "生物制造"},
        "低空经济": {"低空经济", "eVTOL", "无人机", "飞行汽车", "通航"},
        "脑机接口": {"脑机接口", "BCI", "神经", "脑电", "侵入式"},
        "核聚变": {"核聚变", "托卡马克", "人造太阳", "聚变"},
        "元宇宙": {"元宇宙", "VR", "AR", "虚拟", "NFT", "数字人"},
        "钙钛矿电池": {"钙钛矿", "叠层电池", "光伏电池"},
    }
    
    best_match = None
    best_score = 0
    
    for domain, keywords in domain_keywords.items():
        match_count = sum(1 for kw in keywords if kw in keyword_lower)
        score = match_count * 30  # 每个关键词匹配得 30 分
        
        if score > best_score:
            best_score = score
            best_match = domain
    
    # 置信度计算
    confidence = min(best_score, 100)
    
    if confidence >= 60:
        return (best_match, confidence)
    else:
        return (None, confidence)

def analyze_industry_chain(keyword: str, news_list: List[Dict]) -> List[Dict[str, str]]:
    """分析产业链影响（优化版）"""
    log("正在分析产业链...")
    
    chain_analysis = []
    matched_domain, confidence = match_domain(keyword)
    
    log(f"领域匹配：{matched_domain} (置信度：{confidence})")
    
    log(f"知识库内容：{list(INDUSTRY_CHAIN_KNOWLEDGE.keys())}")
    log(f"matched_domain={matched_domain}, in dict={matched_domain in INDUSTRY_CHAIN_KNOWLEDGE if matched_domain else False}")
    
    if matched_domain and matched_domain in INDUSTRY_CHAIN_KNOWLEDGE:
        knowledge = INDUSTRY_CHAIN_KNOWLEDGE[matched_domain]
        log(f"使用领域知识：{list(knowledge.keys())}")
        
        # 分析各环节影响
        for stage, segments in knowledge.items():
            if isinstance(segments, list):
                for segment in segments[:5]:  # 每个环节取前 5 个细分
                    impact = assess_impact(segment, news_list, keyword)
                    log(f"  {segment}: {impact}")
                    # 保留所有环节，包括推断结果
                    if impact:
                        chain_analysis.append({
                            "stage": stage,
                            "segment": segment,
                            "impact_description": impact,
                        })
    
    # 如果没有匹配到预设领域，生成通用分析
    if not chain_analysis:
        log("产业链分析结果为空，使用通用分析")
        chain_analysis = generate_generic_chain_analysis(keyword, news_list)
    
    return chain_analysis

def extract_event_summary(news_list: List[Dict], keyword: str) -> Dict:
    """
    提取事件核心摘要（先读懂新闻在说什么）
    """
    summary = {
        "what": "",  # 发生了什么
        "tech": "",  # 什么技术
        "problem": "",  # 解决了什么问题
        "impact": "",  # 可能的影响
    }
    
    for news in news_list[:3]:  # 分析前 3 条新闻
        title = news.get("title", "")
        content = news.get("content", "")
        # 优先从标题提取（标题更精炼）
        title_text = title
        
        # 提取事件类型
        if any(kw in title_text for kw in ["攻克", "突破", "解决", "首创"]):
            summary["what"] = "技术突破"
        elif any(kw in title_text for kw in ["量产", "发布", "投产", "上线"]):
            summary["what"] = "量产/发布"
        elif any(kw in title_text for kw in ["签约", "订单", "合同", "采购"]):
            summary["what"] = "订单/合同"
        
        # 从标题提取技术点（更准确）
        tech_patterns = [
            r'(\d{1,2}[0-9.]*nm)',  # 2nm, 3nm, 5nm
            r'(GAA|FinFET|EUV|DUV|High-NA)',
            r'(固态电池 | 半固态 | 凝聚态)',
            r'(钙钛矿 | 叠层电池)',
            r'(HBM\d*|CoWoS|Chiplet)',
            r'(激光雷达 | 毫米波雷达)',
            r'(大模型 | 多模态)',
            r'(射频 | 微波 | 毫米波)',  # 射频芯片相关
            r'(功率 | 散热 | 热管理)',  # 功率/散热相关
        ]
        
        for pattern in tech_patterns:
            matches = re.findall(pattern, title_text)
            if matches:
                summary["tech"] = matches[0]
                break
        
        # 如果标题没有，从内容提取（但过滤定义性文本）
        if not summary["tech"]:
            content_tech_patterns = [
                r'(\d{1,2}[0-9.]*nm 工艺)',
                r'(固态电池 | 钙钛矿电池)',
                r'(HBM\d*|CoWoS)',
            ]
            for pattern in content_tech_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    summary["tech"] = matches[0]
                    break
        
        # 提取解决的问题
        problem_patterns = [
            r'攻克 (.{5,40}?) 难题',
            r'解决 (.{5,40}?) 问题',
            r'突破 (.{5,40}?) 瓶颈',
            r'(.{5,30}?) 成为瓶颈',
            r'(.{5,30}?) 世界难题',
        ]
        for pattern in problem_patterns:
            matches = re.findall(pattern, title_text + " " + content[:200])  # 只看标题和前 200 字
            if matches:
                summary["problem"] = matches[0][:40]
                break
        
        # 如果已经提取到关键信息，提前返回
        if summary["what"] and summary["tech"]:
            break
        elif summary["what"] and summary["problem"]:
            break
    
    # 如果还是没提取到技术词，使用原始关键词
    if not summary["tech"]:
        summary["tech"] = keyword.split()[0] if keyword else "半导体"
    
    return summary

def extract_tech_keywords(news_list: List[Dict], keyword: str) -> List[str]:
    """
    从新闻中提取关键技术点
    """
    tech_keywords = []
    
    # 1. 添加原始关键词（核心）
    tech_keywords.append(keyword)
    
    # 2. 从新闻标题/内容提取技术关键词
    tech_patterns = [
        r'(\d[0-9.]*[nmNM]+ 工艺)',  # 2nm 工艺
        r'(\d[0-9.]*[nmNM]+)',  # 2nm, 3nm, 5nm, 2.5nm
        r'(GAA|FinFET|EUV|DUV|High-NA)',  # 技术架构
        r'(固态 | 半固态 | 凝聚态)',  # 电池技术
        r'(钙钛矿 | 叠层)',  # 光伏技术
        r'(HBM\d*|CoWoS|Chiplet|3D 封装)',  # 封装技术
        r'(激光雷达 | 毫米波雷达 | 摄像头)',  # 自动驾驶
        r'(大模型 | 多模态 | AIGC|LLM)',  # AI 技术
        r'([^\s]{2,8} 材料)',  # XX 材料
        r'([^\s]{2,8} 芯片)',  # XX 芯片
    ]
    
    for news in news_list:
        text = news.get("title", "") + " " + news.get("content", "")
        for pattern in tech_patterns:
            matches = re.findall(pattern, text)
            tech_keywords.extend(matches)
    
    # 过滤掉太短或无意义的词
    tech_keywords = [kw for kw in tech_keywords if len(kw) >= 2 and kw not in ['nm', 'NM']]
    
    # 去重
    return list(set(tech_keywords))

def assess_impact(segment: str, news_list: List[Dict], keyword: str = "") -> str:
    """
    评估某个细分环节的影响（基于联网搜索的分析）
    
    投资分析原则：
    1. 优先提取事实依据（数据/合同/签约等）
    2. 无事实时，针对技术点 + 环节进行联网搜索
    3. 搜索无果时才使用推断
    4. 区分"事实"和"推断"，推断需标注"待确认"
    
    返回：影响描述
    """
    if not news_list:
        return f"暂无公开数据 - 需确认：订单/合同/产能/客户等具体信息"
    
    # 1. 尝试提取事实依据
    facts = extract_facts_from_news(news_list, segment, keyword)
    if facts:
        return format_fact_based_analysis(facts)
    
    # 2. 先理解事件核心内容
    event_summary = extract_event_summary(news_list, keyword)
    log(f"    事件摘要：what={event_summary['what']}, tech={event_summary['tech']}, problem={event_summary['problem']}")
    
    # 3. 提取关键技术点
    tech_keywords = extract_tech_keywords(news_list, keyword)
    
    # 4. 针对技术点 + 环节进行联网搜索
    # 构建更具体的搜索查询
    search_queries = []
    
    # 优先使用完整关键词 + 环节（如"半导体材料突破 硅片 受益"）
    search_queries.append(f"{keyword} {segment} 受益")
    search_queries.append(f"{keyword} {segment} 利好")
    
    # 其次使用事件类型 + 环节
    if event_summary["what"] == "技术突破":
        search_queries.append(f"{keyword} {segment} 国产替代")
    
    # 再使用具体技术词（如果有）
    if event_summary["tech"] and len(event_summary["tech"]) >= 3 and event_summary["tech"] not in keyword:
        search_queries.append(f"{event_summary['tech']} {segment} 影响")
    
    for search_query in search_queries[:5]:  # 最多搜索 5 次
        log(f"    搜索：{search_query}")
        
        try:
            cmd = ["uv", "run", "scripts/searxng.py", "search", search_query, "-n", "5", "--format", "json"]
            result = subprocess.run(cmd, cwd=SEARXNG_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=30)
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    results = data.get("results", [])[:3]
                    
                    if results:
                        # 从搜索结果提取影响分析
                        # 提取搜索词用于描述
                        query_tech = search_query.split()[0] if search_query else keyword
                        analysis = extract_impact_from_search(results, segment, query_tech, event_summary)
                        if analysis:
                            return analysis
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            log(f"    搜索异常：{str(e)[:50]}")
    
    # 4. 搜索无果时使用事件摘要推断（更精准）
    log(f"    搜索无结果，使用事件摘要推断")
    
    if EVENT_SUMMARY_ENABLED and event_summary:
        # 使用事件摘要进行精准推断
        analysis = generate_segment_analysis(segment, event_summary, None)
        if analysis:
            log(f"    事件摘要推断：{analysis[:50]}...")
            return analysis
    
    # 5. 使用影响分析器（基于事件类型）
    if IMPACT_ANALYZER_ENABLED:
        from impact_analyzer import detect_event_type, get_segment_impact as get_impact_direct
        event_type = detect_event_type(keyword, news_list)
        log(f"    事件类型：{event_type}")
        
        # 直接调用 get_segment_impact 获取具体环节的影响
        impact = get_impact_direct(segment, event_type, keyword)
        log(f"    {segment}: {impact[:60]}...")
        return impact
    
    # 6. 退回到通用推断
    inferred_impact = infer_impact_from_keyword(segment, keyword)
    if inferred_impact and "待进一步观察" not in inferred_impact:
        return inferred_impact
    
    # 7. 基于环节类型的通用分析
    return f"中性 - {segment}环节，事件影响待观察"

def extract_impact_from_search(results: List[Dict], segment: str, tech: str, event_summary: Dict = None) -> str:
    """
    从搜索结果中提取产业链影响分析
    """
    for r in results:
        title = r.get("title", "")
        content = r.get("content", "")
        text = title + " " + content
        
        # 正面影响关键词
        positive_keywords = ["受益", "利好", "增长", "提升", "突破", "加速", "机会", "空间", "国产替代", "渗透率", "价值量提升", "需求旺盛"]
        
        # 检查是否有正面影响
        has_positive = any(kw in text for kw in positive_keywords)
        
        # 提取具体数据
        numbers = re.findall(r'\d+(?:\.\d+)?[亿万%]?', text)
        
        # 优先提取具体影响描述（从标题或开头）
        impact_patterns = [
            r'(.{20,80}?) 受益',
            r'(.{20,80}?) 利好',
            r'(.{20,80}?) 增长',
            r'(.{20,80}?) 提升',
            r'(.{20,80}?) 突破',
            r'(.{20,80}?) 加速',
            r'(.{20,80}?) 国产替代',
        ]
        
        for pattern in impact_patterns:
            matches = re.findall(pattern, text)
            if matches:
                desc = matches[0][:80].strip()
                # 严格过滤：必须是有意义的完整描述
                if len(desc) > 20 and not any(desc.startswith(x) for x in ["的", "是", "在", "于", "和", "与", "或"]):
                    # 确保包含关键词
                    if any(kw in desc for kw in [segment, tech, "需求", "市场", "技术", "产能"]):
                        return f"{desc}（基于搜索）"
        
        # 构建简洁的影响描述
        if has_positive:
            if numbers:
                return f"{tech}带动{segment}需求增长，数据：{', '.join(numbers[:2])}（基于搜索）"
            else:
                return f"{tech}带动{segment}环节受益（基于搜索）"
    
    # 搜索不到好结果时返回空，让上层使用推断
    return ""

def extract_facts_from_news(news_list: List[Dict], segment: str, keyword: str) -> List[Dict]:
    """
    从新闻中提取事实依据（数据/合同/签约等）
    """
    import re
    facts = []
    
    for news in news_list:
        title = news.get("title", "")
        content = news.get("content", "")
        text = title + " " + content
        
        # 提取具体数据
        numbers = re.findall(r'\d+(?:\.\d+)?[亿万]?[美元人民币]?元？', text)
        companies = re.findall(r'[A-Za-z\u4e00-\u9fa5]{2,20}(?:公司 | 集团 | 厂 | 大学 | 研究院)', text)
        contracts = re.findall(r'(签约 | 合同 | 订单 | 采购 | 中标 | 攻克 | 突破 | 发布 | 量产)', text)
        capacity = re.findall(r'(产能 | 产量 | 出货量 | 效率 | 性能).{0,30}\d+', text)
        
        # 提取技术进展关键词
        tech_progress = re.findall(r'(攻克 | 突破 | 首创 | 领先 | 填补空白 | 世界难题)', text)
        
        # 提取人物/机构引用
        quotes = re.findall(r'[""](.*?)[""]', text)[:2]
        
        if numbers or contracts or tech_progress:
            facts.append({
                "source": news.get("source", "未知"),
                "title": title,
                "data": numbers,
                "companies": companies,
                "contracts": contracts,
                "capacity": capacity,
                "tech_progress": tech_progress,
                "quotes": quotes,
            })
    
    return facts

def format_fact_based_analysis(facts: List[Dict]) -> str:
    """
    格式化基于事实的分析
    """
    if not facts:
        return "暂无公开数据"
    
    fact = facts[0]  # 取第一个事实
    parts = []
    
    # 技术进展优先展示
    if fact.get("tech_progress"):
        parts.append(f"技术进展：{', '.join(fact['tech_progress'])}")
    
    if fact.get("contracts"):
        # 过滤掉非合同类词汇
        contract_types = [c for c in fact['contracts'] if c in ['签约', '合同', '订单', '采购', '中标']]
        if contract_types:
            parts.append(f"合同类型：{', '.join(contract_types)}")
    
    if fact.get("data"):
        parts.append(f"金额/数据：{', '.join(fact['data'])}")
    if fact.get("companies"):
        # 过滤掉非公司类词汇
        company_list = [c for c in fact['companies'] if any(x in c for x in ['公司', '集团', '厂'])]
        if company_list:
            parts.append(f"涉及公司：{', '.join(company_list[:3])}")
    if fact.get("capacity"):
        parts.append(f"产能/性能数据：{fact['capacity'][0]}")
    if fact.get("quotes"):
        parts.append(f"关键信息：{fact['quotes'][0][:50]}...")
    
    if parts:
        return "有事实依据 - " + " | ".join(parts)
    else:
        return "暂无具体数据"

def infer_impact_from_keyword(segment: str, keyword: str) -> str:
    """
    基于关键词推断产业链影响（当无实际新闻内容时）- 增强版
    """
    keyword_lower = keyword.lower()
    segment_lower = segment.lower()
    
    # 预设的产业链影响逻辑（增强版）
    impact_rules = {
        # ==================== NVIDIA 相关 ====================
        "nvidia": {
            "GPU": "重大利好 - AI 芯片需求爆发",
            "HBM": "重大利好 - HBM4 成为瓶颈，需求激增",
            "CoWoS": "重大利好 - 先进封装产能紧张",
            "Chiplet": "利好 - Chiplet 技术受益",
            "光刻机": "利好 - 高端制程需求增加",
            "刻蚀机": "利好 - 先进制程需求",
            "薄膜沉积": "利好 - 制程升级需求",
            "晶圆代工": "重大利好 - 台积电受益",
            "先进制程": "重大利好 - 需求爆发",
            "AI 服务器": "重大利好 - 下游需求爆发",
            "数据中心": "利好 - AI 基建需求",
            "消费电子": "中性 - 主要影响数据中心",
        },
        "rubin": {
            "GPU": "重大利好",
            "HBM": "重大利好",
            "CoWoS": "重大利好",
            "先进制程": "重大利好",
        },
        
        # ==================== Tesla/FSD 相关 ====================
        "tesla": {
            "激光雷达": "中性 - Tesla 坚持纯视觉方案",
            "摄像头": "利好 - 纯视觉方案受益",
            "毫米波雷达": "中性",
            "AI 芯片": "重大利好 - FSD 芯片需求",
            "算法": "重大利好 - FSD 进步",
            "操作系统": "利好",
            "线控底盘": "利好 - 自动驾驶需求",
            "线控制动": "利好",
            "线控转向": "利好",
            "高精地图": "中性 - Tesla 不用高精地图",
            "FSD": "重大利好",
            "自动驾驶": "重大利好",
        },
        "fsd": {
            "摄像头": "利好",
            "AI 芯片": "重大利好",
            "算法": "重大利好",
            "操作系统": "利好",
            "线控底盘": "利好",
            "高精地图": "中性",
        },
        
        # ==================== 台积电相关 ====================
        "tsmc": {
            "晶圆代工": "重大利好 - 全球龙头受益",
            "先进制程": "重大利好 - 2nm 技术领先",
            "成熟制程": "利好 - 产能利用率提升",
            "光刻机": "重大利好 - ASML 受益",
            "封装": "重大利好 - CoWoS 需求",
            "测试": "利好",
            "Chiplet": "利好",
        },
        "2nm": {
            "晶圆代工": "重大利好",
            "先进制程": "重大利好",
            "光刻机": "重大利好",
            "EUV": "重大利好",
        },
        
        # ==================== OpenAI/GPT 相关 ====================
        "openai": {
            "AI 芯片": "重大利好 - 算力需求爆发",
            "GPU": "重大利好 - NVIDIA 独家受益",
            "大模型": "重大利好 - 技术进步",
            "AI 服务器": "重大利好 - 下游需求",
            "HBM": "利好 - 内存需求",
            "数据中心": "重大利好",
            "云计算": "重大利好 - 微软 Azure 受益",
        },
        "gpt": {
            "AI 芯片": "重大利好",
            "GPU": "重大利好",
            "大模型": "重大利好",
            "AI 服务器": "重大利好",
        },
        "100M": {
            "HBM": "重大利好 - 大上下文需要大内存",
            "AI 芯片": "重大利好",
        },
        
        # ==================== 特朗普/关税相关 ====================
        "trump": {
            "半导体": "利空 - 关税影响出口",
            "晶圆代工": "中性偏空 - 可能转移产能",
            "设备": "利空 - 出口限制",
            "材料": "利空",
            "封装": "中性",
        },
        "关税": {
            "半导体": "利空",
            "出口": "利空",
            "设备": "利空",
            "材料": "利空",
        },
        "100%": {
            "半导体": "重大利空",
            "出口": "重大利空",
        },
        
        # ==================== 通用规则 ====================
        "量产": {
            "GPU": "利好",
            "芯片": "利好",
            "电池": "利好",
        },
        "突破": {
            "技术": "利好",
            "制程": "利好",
            "材料": "利好",
        },
    }
    
    # 多级匹配策略
    # 1. 精确匹配关键词
    for rule_keyword, impacts in impact_rules.items():
        if rule_keyword in keyword_lower:
            for seg_key, impact_desc in impacts.items():
                if seg_key.lower() in segment_lower or segment_lower in seg_key.lower():
                    return impact_desc
    
    # 2. 基于事件类型推断（当无精确匹配时）
    event_type_keywords = {
        "重大利好": ["量产", "发布", "突破", "提前", "确认", "宣布"],
        "利好": ["增长", "扩张", "升级", "合作", "签约"],
        "利空": ["关税", "制裁", "限制", "禁令", "下滑"],
        "中性": ["报告", "技术", "研究", "分析"],
    }
    
    for impact_type, keywords in event_type_keywords.items():
        if any(kw in keyword_lower for kw in keywords):
            # 基于环节类型给出具体描述
            if any(x in segment_lower for x in ["芯片", "GPU", "AI", "算力"]):
                return f"{impact_type} - 半导体/AI 产业链受益" if impact_type in ["重大利好", "利好"] else f"{impact_type} - 出口受限"
            elif any(x in segment_lower for x in ["电池", "新能源", "电动车"]):
                return f"{impact_type} - 新能源产业链" if impact_type in ["重大利好", "利好"] else f"{impact_type}"
            elif any(x in segment_lower for x in ["设备", "光刻", "刻蚀"]):
                return f"{impact_type} - 设备需求变化" if impact_type in ["重大利好", "利好"] else f"{impact_type} - 出口管制"
            else:
                return f"{impact_type}"
    
    # 3. 默认推断（基于事件类型）
    if any(kw in keyword_lower for kw in ["量产", "发布", "突破", "提前", "攻克"]):
        # 基于环节类型给出更具体的描述
        if any(x in segment_lower for x in ["材料", "硅片", "光刻胶", "气体", "靶材", "抛光"]):
            return "利好 - 半导体材料国产替代加速，上游材料环节受益（待确认具体订单/合同）"
        elif any(x in segment_lower for x in ["设备", "光刻", "刻蚀", "沉积", "清洗", "检测"]):
            return "利好 - 半导体设备需求增加，国产设备环节受益（待确认具体订单/合同）"
        elif any(x in segment_lower for x in ["芯片", "GPU", "CPU", "存储", "模拟"]):
            return "利好 - 技术突破提升芯片性能，设计环节受益（待确认具体订单/合同）"
        elif any(x in segment_lower for x in ["制造", "晶圆", "代工", "制程"]):
            return "利好 - 制造工艺改进，晶圆代工环节受益（待确认具体订单/合同）"
        elif any(x in segment_lower for x in ["封装", "测试", "CoWoS", "Chiplet"]):
            return "利好 - 先进封装需求增加，封测环节受益（待确认具体订单/合同）"
        elif any(x in segment_lower for x in ["消费电子", "汽车", "服务器", "通信", "工业"]):
            return "利好 - 下游应用需求增长，终端应用环节受益（待确认具体订单/合同）"
        else:
            return "利好 - 技术进步/产能释放，全产业链受益（待确认具体订单/合同）"
    elif any(kw in keyword_lower for kw in ["关税", "制裁", "限制", "禁令"]):
        return "利空 - 政策影响，出口受限"
    elif any(kw in keyword_lower for kw in ["报告", "技术", "研究"]):
        return "中性偏多 - 技术发展"
    
    return "待进一步观察"

def generate_generic_chain_analysis(keyword: str, news_list: List[Dict]) -> List[Dict[str, str]]:
    """通用产业链分析"""
    return [
        {"stage": "上游", "segment": "原材料/核心部件", "impact_description": "根据新闻内容判断影响"},
        {"stage": "中游", "segment": "制造/集成", "impact_description": "根据新闻内容判断影响"},
        {"stage": "下游", "segment": "应用/终端", "impact_description": "根据新闻内容判断影响"},
    ]

# ==================== 资本市场映射模块 ====================
def map_to_stocks(keyword: str, chain_analysis: List[Dict]) -> Dict[str, List[Dict]]:
    """映射到资本市场标的（联网搜索版）"""
    log("正在映射资本市场标的...")
    
    market_mapping = {"A_shares": [], "HK_shares": [], "US_stocks": []}
    keyword_lower = keyword.lower()
    
    # 1. 先从知识库匹配公司
    matched_companies = []
    
    for tech_keyword, companies in COMPANY_KNOWLEDGE.items():
        matched = False
        
        if tech_keyword in keyword:
            matched = True
        elif keyword in tech_keyword:
            matched = True
        else:
            common_words = ["半导体", "AI", "芯片", "电池", "新能源", "自动驾驶", "光伏", "风电", "储能", "机器人", "量子", "6G", "通信", "航天", "低空"]
            for word in common_words:
                if word in tech_keyword and word in keyword_lower:
                    matched = True
                    break
        
        if matched:
            for market, company_list in companies.items():
                for company_info in company_list:
                    matched_companies.append({
                        "market": market,
                        "code": company_info["code"],
                        "name": company_info["name"],
                        "business": company_info["business"],
                        "position": company_info["position"],
                        "tech_keyword": tech_keyword,
                    })
    
    # 2. 针对每个公司联网搜索具体受益逻辑
    log(f"  知识库匹配到 {len(matched_companies)} 家公司，开始搜索受益逻辑...")
    
    for company in matched_companies[:15]:  # 最多处理 15 家公司
        # 构建搜索查询
        search_query = f"{company['name']} {company['code']} {keyword} 受益 逻辑"
        log(f"    搜索：{search_query}")
        
        try:
            cmd = ["uv", "run", "scripts/searxng.py", "search", search_query, "-n", "3", "--format", "json"]
            result = subprocess.run(cmd, cwd=SEARXNG_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=20)
            
            logic = ""
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    results = data.get("results", [])[:2]
                    
                    for r in results:
                        text = r.get("title", "") + " " + r.get("content", "")
                        
                        # 提取具体受益逻辑
                        if any(kw in text for kw in ["供应链", "客户", "订单", "技术", "独家", "领先", "龙头", "受益"]):
                            # 尝试提取具体描述
                            if "台积电" in text and "供应链" in text:
                                logic = f"进入台积电供应链，{company['business']}领域间接受益"
                            elif "独家" in text or "唯一" in text:
                                logic = f"国内{company['business']}独家/唯一供应商，直接受益"
                            elif "龙头" in text or "领先" in text:
                                logic = f"{company['position']}，{keyword}领域核心受益标的"
                            elif "订单" in text or "合同" in text:
                                logic = f"有相关订单/合同，{company['business']}业务直接受益"
                            break
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass
        
        # 如果没有搜索到具体逻辑，使用默认逻辑
        if not logic:
            logic = f"{company['position']}，{company['tech_keyword']}领域受益"
        
        # 添加到结果
        stock_info = {
            "code": company["code"],
            "name": company["name"],
            "business_relevance": company["business"],
            "logic": logic,
        }
        
        if company["market"] == "A 股":
            market_mapping["A_shares"].append(stock_info)
        elif company["market"] == "港股":
            market_mapping["HK_shares"].append(stock_info)
        elif company["market"] == "美股":
            market_mapping["US_stocks"].append(stock_info)
    
    # 3. 如果知识库没有匹配，直接搜索相关公司
    if not any(market_mapping.values()):
        log("  知识库无匹配，直接搜索相关公司...")
        market_mapping = search_related_stocks_with_logic(keyword)
    
    # 4. 去重并限制数量
    for market in market_mapping:
        seen = set()
        unique = []
        for item in market_mapping[market]:
            if item["code"] not in seen:
                unique.append(item)
                seen.add(item["code"])
        market_mapping[market] = unique[:8]
    
    return market_mapping

def search_related_stocks_with_logic(keyword: str) -> Dict[str, List[Dict]]:
    """搜索相关股票并提取受益逻辑"""
    market_mapping = {"A_shares": [], "HK_shares": [], "US_stocks": []}
    
    queries = [
        (f"{keyword} A 股 龙头 受益 股票", "A_shares"),
        (f"{keyword} 港股 上市公司 受益", "HK_shares"),
        (f"{keyword} 美股 概念股 受益", "US_stocks"),
    ]
    
    for query, market in queries:
        try:
            cmd = ["uv", "run", "scripts/searxng.py", "search", query, "-n", "5", "--format", "json"]
            result = subprocess.run(cmd, cwd=SEARXNG_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=45)
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    for r in data.get("results", [])[:5]:
                        title = r.get("title", "")
                        content = r.get("content", "")
                        text = title + " " + content
                        
                        # 提取股票代码
                        cn_match = re.search(r'([63]\d{5})', text)
                        hk_match = re.search(r'(0\d{4})\.HK', text)
                        us_match = re.search(r'\b([A-Z]{2,5})\b', text)
                        
                        code = ""
                        name = title[:40]
                        
                        if cn_match and market == "A_shares":
                            code = cn_match.group(1)
                        elif hk_match and market == "HK_shares":
                            code = hk_match.group(1) + ".HK"
                        elif us_match and market == "US_stocks":
                            code = us_match.group(1)
                        
                        if code:
                            # 提取受益逻辑
                            logic = f"{keyword}领域受益标的"
                            if "龙头" in text:
                                logic = f"{keyword}龙头，核心受益标的"
                            elif "独家" in text or "唯一" in text:
                                logic = f"国内{keyword}独家/唯一供应商"
                            elif "供应链" in text:
                                logic = f"进入{keyword}供应链，间接受益"
                            
                            market_mapping[market].append({
                                "code": code,
                                "name": name,
                                "business_relevance": f"涉及{keyword}业务",
                                "logic": logic,
                            })
                except json.JSONDecodeError:
                    pass
        except Exception as e:
            log(f"搜索失败：{str(e)[:50]}")
    
    return market_mapping

def search_related_stocks(keyword: str) -> Dict[str, List[Dict]]:
    """搜索相关股票（简化版）"""
    market_mapping = {"A_shares": [], "HK_shares": [], "US_stocks": []}
    
    queries = [
        f"{keyword} A 股 龙头 股票代码",
        f"{keyword} 港股 上市公司",
        f"{keyword} 美股 概念股",
    ]
    
    for query in queries:
        try:
            cmd = ["uv", "run", "scripts/searxng.py", "search", query, "-n", "5", "--format", "json"]
            result = subprocess.run(cmd, cwd=SEARXNG_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=60)
            
            if result.returncode == 0:
                try:
                    data = json.loads(result.stdout)
                    for r in data.get("results", [])[:3]:
                        title = r.get("title", "")
                        url = r.get("url", "")
                        
                        # 简单提取股票代码（正则匹配）
                        cn_stock_match = re.search(r'([63]\d{5})', title)
                        hk_stock_match = re.search(r'(0\d{4})\.HK', title)
                        us_stock_match = re.search(r'\b([A-Z]{2,5})\b', title)
                        
                        if cn_stock_match and "A 股" in query:
                            market_mapping["A_shares"].append({
                                "code": cn_stock_match.group(1),
                                "name": title[:30],
                                "business_relevance": f"涉及{keyword}业务",
                                "logic": "搜索结果显示相关",
                            })
                        elif hk_stock_match and "港股" in query:
                            market_mapping["HK_shares"].append({
                                "code": hk_stock_match.group(1) + ".HK",
                                "name": title[:30],
                                "business_relevance": f"涉及{keyword}业务",
                                "logic": "搜索结果显示相关",
                            })
                        elif us_stock_match and "美股" in query:
                            market_mapping["US_stocks"].append({
                                "code": us_stock_match.group(1),
                                "name": title[:30],
                                "business_relevance": f"涉及{keyword}业务",
                                "logic": "搜索结果显示相关",
                            })
                except json.JSONDecodeError:
                    pass
        except Exception:
            pass
    
    return market_mapping

# ==================== 风险分析模块 ====================
def analyze_risks(keyword: str, news_list: List[Dict]) -> List[str]:
    """分析风险因素"""
    risk_keywords = {
        "技术风险": ["技术路线", "良率", "研发失败", "技术壁垒"],
        "市场风险": ["产能过剩", "需求下滑", "价格战", "竞争加剧"],
        "政策风险": ["制裁", "出口限制", "政策变化", "监管"],
        "财务风险": ["亏损", "债务", "现金流", "商誉"],
    }
    
    risks = []
    
    for category, keywords in risk_keywords.items():
        for news in news_list:
            text = (news["title"] + " " + news["content"]).lower()
            if any(kw in text for kw in keywords):
                risk_desc = f"{category}: 需关注相关新闻提及的风险因素"
                if risk_desc not in risks:
                    risks.append(risk_desc)
    
    # 添加通用风险
    if not risks:
        risks = [
            "技术路线风险：新技术可能存在不确定性",
            "市场竞争风险：行业竞争可能加剧",
            "政策风险：相关政策可能发生变化",
        ]
    
    return risks[:5]

# ==================== 报告生成模块 ====================
def generate_report(keyword: str, news_list: List[Dict], chain_analysis: List[Dict], 
                   market_mapping: Dict, risks: List[str]) -> str:
    """生成结构化报告（增强版：FR-02/03/05/10）"""
    log("正在生成报告...")
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 增强分析（如果可用）
    enhanced_data = None
    if ENHANCED_ANALYSIS_ENABLED and news_list:
        try:
            enhanced_data = comprehensive_verification(news_list, COMPANY_KNOWLEDGE)
            log(f"增强分析完成：来源多样性={enhanced_data['verification']['diversity_score']}分")
        except Exception as e:
            log(f"增强分析失败：{str(e)[:100]}")
    
    # 新闻摘要
    if news_list:
        event_title = news_list[0]["title"] if news_list else keyword
        event_source = news_list[0]["source"] if news_list else "综合搜索"
    else:
        event_title = keyword
        event_source = "综合搜索"
    
    # 增强分析数据
    source_verification = ""
    if enhanced_data:
        ver = enhanced_data["verification"]
        source_verification = f"""
**信息来源验证**:
- 来源多样性：{ver['diversity_score']}分
- 官方公告：{'✅' if ver['has_official'] else '❌'}
- 科技媒体：{'✅' if ver['has_tech_media'] else '❌'}
- 财经媒体：{'✅' if ver['has_finance_media'] else '❌'}
"""
        if ver['conflicts']:
            source_verification += "\n⚠️ **存在争议**:\n"
            for c in ver['conflicts'][:3]:
                source_verification += f"- {c['claim']}: 来源不一致\n"
    
    report = f"""# 🔗 TechChain Insight - 科技链·热点透视

**分析主题**: {keyword}  
**报告时间**: {now}  
**信息来源**: {event_source}
{source_verification}
---

## 📰 事件摘要

**标题**: {event_title}

**核心内容**: 基于最新搜索信息，对"{keyword}"相关事件进行产业链分析和资本市场映射。

---

## 🔗 产业链利益链条分析

"""
    
    # 竞争格局分析（增强功能）
    if enhanced_data and enhanced_data.get("competition"):
        report += "### 📊 竞争格局分析\n\n"
        for segment, comp in enhanced_data["competition"].items():
            if comp["leaders"] or comp["dark_horses"]:
                report += f"**{segment}**:\n"
                if comp["leaders"]:
                    leaders = ", ".join([f"{c['name']}({c['code']})" for c in comp["leaders"][:3]])
                    report += f"- 🏆 龙头：{leaders}\n"
                if comp["dark_horses"]:
                    horses = ", ".join([f"{c['name']}({c['code']})" for c in comp["dark_horses"][:2]])
                    report += f"- 🐴 黑马：{horses}\n"
                if comp["market_share"]:
                    share_list = []
                    for k, v in list(comp["market_share"].items())[:3]:
                        share_list.append(f"{k}:{v}")
                    report += "- 📈 市占率：" + ", ".join(share_list) + "\n"
                report += "\n"
    
    # 产业链分析
    if chain_analysis:
        current_stage = ""
        for item in chain_analysis:
            if item["stage"] != current_stage:
                current_stage = item["stage"]
                stage_emoji = {"上游": "⛏️", "中游": "🏭", "下游": "📱", "设备": "🔧"}.get(current_stage, "📊")
                report += f"\n### {stage_emoji} {current_stage}\n\n"
            report += f"- **{item['segment']}**: {item['impact_description']}\n"
    else:
        report += "*暂无详细产业链数据*\n"
    
    # 资本市场映射
    report += f"""
---

## 📈 核心受益公司映射

"""
    
    has_stocks = False
    
    if market_mapping["A_shares"]:
        has_stocks = True
        report += "### 🇨🇳 A 股\n\n"
        report += "| 代码 | 公司 | 涉及业务 | 受益逻辑 |\n"
        report += "|------|------|----------|----------|\n"
        for stock in market_mapping["A_shares"]:
            report += f"| {stock['code']} | {stock['name']} | {stock['business_relevance']} | {stock['logic']} |\n"
        report += "\n"
    
    if market_mapping["HK_shares"]:
        has_stocks = True
        report += "### 🇭🇰 港股\n\n"
        report += "| 代码 | 公司 | 涉及业务 | 受益逻辑 |\n"
        report += "|------|------|----------|----------|\n"
        for stock in market_mapping["HK_shares"]:
            report += f"| {stock['code']} | {stock['name']} | {stock['business_relevance']} | {stock['logic']} |\n"
        report += "\n"
    
    if market_mapping["US_stocks"]:
        has_stocks = True
        report += "### 🇺🇸 美股\n\n"
        report += "| 代码 | 公司 | 涉及业务 | 受益逻辑 |\n"
        report += "|------|------|----------|----------|\n"
        for stock in market_mapping["US_stocks"]:
            report += f"| {stock['code']} | {stock['name']} | {stock['business_relevance']} | {stock['logic']} |\n"
        report += "\n"
    
    if not has_stocks:
        report += "*暂无相关上市公司数据*\n"
    
    # 风险提示
    report += f"""
---

## ⚠️ 风险提示

"""
    for risk in risks:
        report += f"- {risk}\n"
    
    # 参考来源（带可信度）
    report += f"""
---

## 📚 参考来源

"""
    if news_list:
        # 按可信度分组显示
        high_cred = [n for n in news_list if n.get("credibility_score", 0) >= 80]
        mid_cred = [n for n in news_list if 60 <= n.get("credibility_score", 0) < 80]
        low_cred = [n for n in news_list if n.get("credibility_score", 0) < 60]
        
        if high_cred:
            report += "### ✅ 高可信度来源\n\n"
            for i, news in enumerate(high_cred[:5], 1):
                cred_score = news.get("credibility_score", 0)
                report += f"{i}. [{news['title']}]({news['url']}) - {news['source']} `可信度：{cred_score}`\n"
            report += "\n"
        
        if mid_cred:
            report += "### ⚠️ 中等可信度来源\n\n"
            for i, news in enumerate(mid_cred[:3], 1):
                cred_score = news.get("credibility_score", 0)
                report += f"{i}. [{news['title']}]({news['url']}) - {news['source']} `可信度：{cred_score}`\n"
            report += "\n"
        
        if low_cred:
            report += "### ❗ 低可信度来源（仅供参考）\n\n"
            for i, news in enumerate(low_cred[:2], 1):
                cred_score = news.get("credibility_score", 0)
                report += f"{i}. [{news['title']}]({news['url']}) - {news['source']} `可信度：{cred_score}`\n"
            report += "\n"
    else:
        report += "*暂无参考来源*\n"
    
    # 免责声明
    report += f"""
---

## ⚖️ 免责声明

**本分析报告基于公开网络搜索整理，仅供参考，不构成任何投资建议。**

- 信息准确性：部分信息可能来自市场传闻，标注"待证实"的内容需谨慎对待
- 时效性：信息截止时间为报告生成时间，后续可能发生变化
- 投资风险：市场有风险，投资需谨慎，请独立判断并自行承担风险

---

*TechChain Insight v1.0.0 | 科技链·热点透视*
"""
    
    return report

# ==================== 主流程 ====================
def main():
    """主入口"""
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword", nargs="?", default="", help="关键词或新闻标题")
    parser.add_argument("--event-input", help="事件输入文件路径（来自 Scout）")
    args = parser.parse_args()
    
    keyword = args.keyword if args.keyword else "半导体"
    
    # 读取事件输入（如果有）
    event_input = None
    if args.event_input:
        try:
            with open(args.event_input, "r", encoding="utf-8") as f:
                event_input = json.load(f)
            log(f"已加载事件输入：{event_input.get('title', '')[:50]}...")
        except Exception as e:
            log(f"加载事件输入失败：{e}")
    
    # 确保知识库加载
    global INDUSTRY_CHAIN_KNOWLEDGE, COMPANY_KNOWLEDGE
    INDUSTRY_CHAIN_KNOWLEDGE, COMPANY_KNOWLEDGE = load_knowledge_base()
    log(f"知识库已加载：{len(INDUSTRY_CHAIN_KNOWLEDGE)} 个领域，{len(COMPANY_KNOWLEDGE)} 个公司分类")
    
    log("=" * 50)
    log(f"TechChain Insight - 科技链·热点透视")
    log(f"分析主题：{keyword}")
    log("=" * 50)
    
    try:
        # 1. 搜索新闻
        news_list = search_news(keyword)
        
        # 2. 分析产业链（使用事件摘要）
        chain_analysis = analyze_industry_chain(keyword, news_list)
        
        # 3. 映射资本市场（使用事件摘要）
        market_mapping = map_to_stocks(keyword, chain_analysis)
        
        # 4. 分析风险
        risks = analyze_risks(keyword, news_list)
        
        # 5. 生成报告
        report = generate_report(keyword, news_list, chain_analysis, market_mapping, risks)
        
        # 6. 输出报告
        print("\n" + report)
        
        # 7. 保存报告
        report_file = SKILL_DIR / "reports" / f"techchain-{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
        report_file.parent.mkdir(parents=True, exist_ok=True)
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        log(f"报告已保存：{report_file}")
        
        log("=" * 50)
        log("分析完成")
        log("=" * 50)
        
    except Exception as e:
        log(f"执行异常：{str(e)}")
        import traceback
        log(traceback.format_exc())
        print(f"错误：{str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
