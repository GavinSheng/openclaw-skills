#!/usr/bin/env python3
# =============================================================================
# TechChain Insight - 核心规则增强模块
# 实现：FR-02 多源验证 / FR-03 实体提取 / FR-05 竞争格局 / FR-10 引用标注
# =============================================================================

import re
from typing import Dict, List, Any, Optional

# ==================== FR-02: 多源交叉验证 ====================
def classify_source(url: str) -> str:
    """
    FR-02: 分类信息来源
    返回：来源类型（官方公告/科技媒体/财经媒体/券商研报/社交媒体/未知）
    """
    url_lower = url.lower()
    
    # 官方公告
    official = ["cninfo.com.cn", "sse.com.cn", "szse.cn", "sec.gov", "edgar-online.com", "hkexnews.hk"]
    for domain in official:
        if domain in url_lower:
            return "官方公告"
    
    # 科技媒体
    tech_media = ["36kr.com", "huxiu.com", "geekpark.net", "anandtech.com", "eetimes.com", "techcrunch.com"]
    for domain in tech_media:
        if domain in url_lower:
            return "科技媒体"
    
    # 财经媒体
    finance_media = ["cls.cn", "stcn.com", "cs.com.cn", "jjckb.cn", "bloomberg.com", "reuters.com", "wsj.com", "barrons.com", "caixin.com"]
    for domain in finance_media:
        if domain in url_lower:
            return "财经媒体"
    
    # 券商研报
    research = ["eastmoney.com", "10jqka.com.cn", "xueqiu.com", "sina.com.cn", "sohu.com"]
    for domain in research:
        if domain in url_lower:
            return "券商研报"
    
    # 社交媒体
    social = ["zhihu.com", "weibo.com", "twitter.com", "douyin.com"]
    for domain in social:
        if domain in url_lower:
            return "社交媒体"
    
    return "未知来源"

def detect_conflicts(news_list: List[Dict]) -> List[Dict]:
    """
    FR-02: 检测信息冲突
    返回：冲突信息列表
    """
    conflicts = []
    
    # 提取关键声明
    claims = {}
    for news in news_list:
        text = news.get("title", "") + " " + news.get("content", "")
        
        # 检测时间相关声明
        time_patterns = [
            (r"(202[0-9] 年 \d{1,2} 月 \d{1,2} 日|\d{1,2}月\d{1,2}日)", "时间"),
            (r"(量产 | 发布 | 上市 | 投产)", "事件"),
        ]
        
        for pattern, claim_type in time_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                key = f"{claim_type}:{match}"
                if key not in claims:
                    claims[key] = []
                claims[key].append(news.get("source", "未知"))
    
    # 检测冲突（同一事件有不同时间/来源说法）
    for claim, sources in claims.items():
        if len(set(sources)) > 1:
            conflicts.append({
                "claim": claim,
                "sources": list(set(sources)),
                "status": "待进一步验证"
            })
    
    return conflicts

def verify_with_multiple_sources(news_list: List[Dict]) -> Dict:
    """
    FR-02: 多源交叉验证汇总
    """
    # 按来源类型分组
    sources_by_type = {
        "官方公告": [],
        "科技媒体": [],
        "财经媒体": [],
        "券商研报": [],
        "社交媒体": [],
        "未知来源": [],
    }
    
    for news in news_list:
        source_type = classify_source(news.get("url", ""))
        sources_by_type[source_type].append(news)
    
    # 计算来源多样性评分
    active_sources = sum(1 for v in sources_by_type.values() if len(v) > 0)
    diversity_score = min(active_sources * 20, 100)  # 最多 5 种来源，100 分
    
    # 检测冲突
    conflicts = detect_conflicts(news_list)
    
    return {
        "sources_by_type": sources_by_type,
        "diversity_score": diversity_score,
        "conflicts": conflicts,
        "has_official": len(sources_by_type["官方公告"]) > 0,
        "has_tech_media": len(sources_by_type["科技媒体"]) > 0,
        "has_finance_media": len(sources_by_type["财经媒体"]) > 0,
    }

# ==================== FR-03: 关键实体提取 ====================
def extract_entities(text: str) -> Dict:
    """
    FR-03: 从非结构化文本中提取关键实体
    返回：技术参数/公司/时间/产能数据
    """
    entities = {
        "companies": [],
        "technologies": [],
        "time_points": [],
        "capacity_data": [],
        "financial_data": [],
    }
    
    # 提取公司名称（简化版，可扩展）
    company_patterns = [
        r'([A -zA-Z 股 ]{2,10} 公司)',
        r'([A -zA-Z]{3,10}Inc)',
        r'([A -zA-Z]{3,10}Corp)',
        r'([A -zA-Z]{3,10}Limited)',
    ]
    for pattern in company_patterns:
        matches = re.findall(pattern, text)
        entities["companies"].extend(matches)
    
    # 提取技术参数
    tech_patterns = [
        r'(\d{1,3}nm)',  # 制程
        r'(\d{1,3}Wh/kg)',  # 能量密度
        r'(\d{1,3}\.?\d*%)',  # 百分比
        r'(GAA|FinFET|CMOS)',  # 技术架构
    ]
    for pattern in tech_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities["technologies"].extend(matches)
    
    # 提取时间节点
    time_patterns = [
        r'(202[0-9] 年 \d{1,2} 月)',
        r'(202[0-9] 年 Q[1-4])',
        r'(H1|H2)202[0-9]',
    ]
    for pattern in time_patterns:
        matches = re.findall(pattern, text)
        entities["time_points"].extend(matches)
    
    # 提取产能数据
    capacity_patterns = [
        r'(\d{1,3}(\.\d+)?[G M]W)',  # GW/MW
        r'(\d{1,3}(\.\d+)? 万辆)',  # 万辆
        r'(\d{1,3}(\.\d+)? 万吨)',  # 万吨
        r'(\d{1,3}(\.\d+)? 亿 kWh)',  # 亿 kWh
    ]
    for pattern in capacity_patterns:
        matches = re.findall(pattern, text)
        if matches:
            entities["capacity_data"].extend([m[0] for m in matches])
    
    # 提取财务数据
    financial_patterns = [
        r'(\d{1,3}(\.\d+)? 亿元)',
        r'(\$ \d{1,3}(\.\d+)? 亿)',
        r'(营收 | 利润 | 净利润).{0,20}(\d{1,3}(\.\d+)?[亿万])',
    ]
    for pattern in financial_patterns:
        matches = re.findall(pattern, text)
        if matches:
            entities["financial_data"].extend([m[0] for m in matches])
    
    # 去重
    for key in entities:
        entities[key] = list(set(entities[key]))
    
    return entities

# ==================== FR-05: 横向竞争格局分析 ====================
def analyze_competition(segment: str, news_list: List[Dict], company_knowledge: Dict) -> Dict:
    """
    FR-05: 分析竞争格局
    返回：龙头/黑马/市占率信息
    """
    competition = {
        "leaders": [],  # 龙头
        "challengers": [],  # 挑战者
        "dark_horses": [],  # 黑马
        "market_share": {},  # 市占率
    }
    
    # 从知识库提取龙头信息
    for tech_keyword, companies in company_knowledge.items():
        if tech_keyword in segment or segment in tech_keyword:
            for market, company_list in companies.items():
                for company_info in company_list:
                    position = company_info.get("position", "")
                    if "龙头" in position or "领先" in position:
                        competition["leaders"].append({
                            "name": company_info["name"],
                            "code": company_info["code"],
                            "market": market,
                            "position": position,
                        })
                    elif "新兴" in position or "潜力" in position:
                        competition["dark_horses"].append({
                            "name": company_info["name"],
                            "code": company_info["code"],
                            "market": market,
                            "position": position,
                        })
                    else:
                        competition["challengers"].append({
                            "name": company_info["name"],
                            "code": company_info["code"],
                            "market": market,
                            "position": position,
                        })
    
    # 从新闻中提取市占率信息
    for news in news_list:
        text = news.get("content", "") + " " + news.get("title", "")
        
        # 提取市占率
        market_share_patterns = [
            r'([A -Za-z]{2,20}).{0,30}(市占率 | 市场份额).{0,20}(\d{1,3}(\.\d+)?)%',
            r'([A -Za-z]{2,20}).{0,30}(占比 | 份额).{0,20}(\d{1,3}(\.\d+)?)%',
        ]
        for pattern in market_share_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                company_name = match[0]
                share = match[2]
                competition["market_share"][company_name] = f"{share}%"
    
    return competition

# ==================== FR-10: 引用标注 ====================
def add_citations(text: str, news_list: List[Dict]) -> str:
    """
    FR-10: 为关键数据添加引用标注
    """
    if not news_list:
        return text
    
    # 为每个新闻来源创建引用标记
    citations = []
    for i, news in enumerate(news_list, 1):
        source = news.get("source", "未知")
        url = news.get("url", "#")
        citations.append(f"[{i}] {source} - {url}")
    
    # 在文本末尾添加引用列表
    citation_text = "\n\n**参考来源**:\n" + "\n".join(citations)
    
    return text + citation_text

def format_with_citations(data: Dict, news_list: List[Dict]) -> str:
    """
    FR-10: 格式化输出并添加引用
    """
    output = []
    
    # 添加数据来源说明
    if news_list:
        official_count = sum(1 for n in news_list if classify_source(n.get("url", "")) == "官方公告")
        tech_media_count = sum(1 for n in news_list if classify_source(n.get("url", "")) == "科技媒体")
        finance_media_count = sum(1 for n in news_list if classify_source(n.get("url", "")) == "财经媒体")
        
        output.append(f"**数据来源**: 官方公告 ({official_count}) | 科技媒体 ({tech_media_count}) | 财经媒体 ({finance_media_count})")
        output.append("")
    
    # 添加争议标注（如有）
    conflicts = detect_conflicts(news_list)
    if conflicts:
        output.append("⚠️ **存在争议的信息**:")
        for conflict in conflicts:
            output.append(f"- {conflict['claim']}: 来源不一致 ({', '.join(conflict['sources'])})")
        output.append("")
    
    return "\n".join(output)

# ==================== 综合验证函数 ====================
def comprehensive_verification(news_list: List[Dict], company_knowledge: Dict) -> Dict:
    """
    综合验证：FR-02/03/05/10
    """
    # FR-02: 多源验证
    verification = verify_with_multiple_sources(news_list)
    
    # FR-03: 实体提取
    all_entities = []
    for news in news_list:
        text = news.get("title", "") + " " + news.get("content", "")
        entities = extract_entities(text)
        all_entities.append({
            "source": news.get("source", "未知"),
            "entities": entities,
        })
    
    # FR-05: 竞争格局（动态匹配相关领域）
    # 从新闻内容提取相关领域
    all_text = " ".join([n.get("title", "") + " " + n.get("content", "") for n in news_list])
    
    # 领域关键词映射
    domain_keywords = {
        "半导体": ["半导体", "芯片", "晶圆", "光刻", "刻蚀", "封装", "IC", "制程"],
        "人工智能": ["AI", "人工智能", "大模型", "GPT", "机器学习", "深度学习"],
        "新能源": ["新能源", "光伏", "风电", "储能", "氢能"],
        "固态电池": ["固态电池", "固态", "电解质", "半固态"],
        "新能源汽车": ["新能源汽车", "电动车", "EV", "比亚迪", "特斯拉"],
        "自动驾驶": ["自动驾驶", "无人驾驶", "激光雷达", "FSD", "智驾"],
        "人形机器人": ["人形机器人", "机器人", "Optimus", "伺服", "减速器"],
        "6G 通信": ["6G", "通信", "太赫兹", "卫星互联网"],
        "量子计算": ["量子", "量子计算", "量子比特"],
        "商业航天": ["商业航天", "火箭", "卫星", "发射"],
    }
    
    # 匹配相关领域（至少 2 个关键词匹配）
    matched_domains = []
    for domain, keywords in domain_keywords.items():
        match_count = sum(1 for kw in keywords if kw in all_text)
        if match_count >= 2:
            matched_domains.append(domain)
    
    # 如果没有匹配到，使用默认领域
    if not matched_domains:
        matched_domains = ["半导体"]
    
    # 只分析匹配到的领域
    competition_analysis = {}
    for segment in matched_domains[:3]:  # 最多 3 个领域
        competition_analysis[segment] = analyze_competition(segment, news_list, company_knowledge)
    
    # FR-10: 引用标注
    citations = format_with_citations({}, news_list)
    
    return {
        "verification": verification,
        "entities": all_entities,
        "competition": competition_analysis,
        "citations": citations,
    }
