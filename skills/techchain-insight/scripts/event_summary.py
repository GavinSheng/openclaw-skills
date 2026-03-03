#!/usr/bin/env python3
# =============================================================================
# 事件摘要提取（简单直接版）
# =============================================================================

import re
from typing import Dict, List

def extract_event_summary(news_list: List[Dict], keyword: str, event_input: Dict = None) -> Dict:
    """
    提取事件核心摘要 - 简单直接版
    """
    summary = {
        "what": "技术突破",
        "tech": "半导体材料",
        "problem": "",
        "application": "",
        "stage": "",
    }
    
    # 1. 优先使用 event_input（来自 Scout 事件）
    if event_input:
        title = event_input.get("title", "")
        summary_text = event_input.get("summary", "")
        tags = event_input.get("tags", [])
        full_text = title + " " + summary_text
        
        # 提取技术关键词
        if "射频" in full_text or "5G" in full_text or "通信" in full_text:
            summary["application"] = "射频芯片"
        if "散热" in full_text or "热" in full_text:
            summary["tech"] = "散热材料"
            summary["problem"] = "芯片散热瓶颈"
        if "成核层" in full_text or "晶体" in full_text:
            summary["tech"] = "晶体成核层"
            summary["problem"] = "表面平整度影响散热"
        if tags:
            summary["tech"] = tags[0]  # 使用第一个 tag
        
        return summary
    
    # 2. 从新闻列表提取
    for news in news_list[:3]:
        title = news.get("title", "")
        content = news.get("content", "")
        full_text = title + " " + content
        
        # 提取事件类型
        if any(kw in title for kw in ["攻克", "突破", "解决"]):
            summary["what"] = "技术突破"
        elif any(kw in title for kw in ["量产", "发布"]):
            summary["what"] = "量产/发布"
        
        # 提取技术
        if "射频" in full_text:
            summary["application"] = "射频芯片"
        if "散热" in full_text:
            summary["tech"] = "散热材料"
            summary["problem"] = "芯片散热"
        if "电池" in full_text:
            summary["tech"] = "电池材料"
        if "nm" in full_text or "纳米" in full_text:
            match = re.search(r'(\d+nm)', full_text)
            if match:
                summary["tech"] = match.group(1)
                summary["problem"] = "先进制程"
        
        if summary["tech"] != "半导体材料":
            break
    
    return summary


def get_segment_impact(segment: str, event_summary: Dict) -> str:
    """
    根据事件摘要和环节，返回影响分析
    """
    tech = event_summary.get("tech", "")
    application = event_summary.get("application", "")
    problem = event_summary.get("problem", "")
    
    # 如果是散热/热管理相关
    if "散热" in tech or "散热" in problem or "热" in problem:
        if "材料" in segment or "硅片" in segment or "衬底" in segment:
            return "重大利好 - 散热材料核心受益，解决芯片热瓶颈"
        elif "射频" in application and ("芯片" in segment or "设计" in segment):
            return "重大利好 - 射频芯片性能提升，5G 通信直接受益"
        elif "设备" in segment:
            return "利好 - 间接带动设备需求"
        else:
            return "利好 - 产业链传导受益"
    
    # 如果是晶体/成核层相关
    if "晶体" in tech or "成核层" in tech:
        if "材料" in segment or "硅片" in segment:
            return "重大利好 - 晶体材料技术突破，国产替代加速"
        elif "设备" in segment:
            return "利好 - 带动相关设备需求"
        else:
            return "中性偏多 - 产业链传导"
    
    # 如果是先进制程（nm）
    if re.search(r'\d+nm', tech):
        if "先进制程" in segment or "晶圆代工" in segment:
            return "重大利好 - 先进制程突破"
        elif "设备" in segment:
            return "重大利好 - 设备需求增加"
        elif "材料" in segment:
            return "利好 - 材料要求提升"
        else:
            return "利好 - 产业链受益"
    
    # 默认：根据环节类型判断
    if "材料" in segment or "硅片" in segment or "光刻胶" in segment:
        return "利好 - 上游材料环节受益，国产替代逻辑"
    elif "设备" in segment:
        return "利好 - 上游设备需求增长"
    elif "芯片" in segment or "设计" in segment:
        return "中性偏多 - 中游设计环节"
    elif "制造" in segment or "晶圆" in segment:
        return "利好 - 中游制造受益"
    elif "封装" in segment or "测试" in segment:
        return "中性偏多 - 封测环节"
    else:
        return "利好 - 产业链受益"


def get_relevant_companies(event_summary: Dict, company_knowledge: Dict) -> List[Dict]:
    """
    根据事件摘要获取相关公司
    """
    tech = event_summary.get("tech", "")
    application = event_summary.get("application", "")
    
    relevant = []
    
    # 1. 散热/热管理相关
    if "散热" in tech or "散热" in event_summary.get("problem", ""):
        # 找有散热、材料业务的公司
        for keyword, companies in company_knowledge.items():
            if "半导体设备" in keyword:
                for market, list_ in companies.items():
                    for co in list_:
                        if any(kw in co.get("business", "") for kw in ["散热", "热管理", "材料"]):
                            relevant.append({
                                "market": market,
                                "code": co["code"],
                                "name": co["name"],
                                "business": co["business"],
                                "logic": f"散热材料/设备供应商，直接受益于芯片散热技术突破",
                            })
    
    # 2. 射频相关
    if "射频" in application:
        for keyword, companies in company_knowledge.items():
            if "半导体设备" in keyword:
                for market, list_ in companies.items():
                    for co in list_:
                        relevant.append({
                            "market": market,
                            "code": co["code"],
                            "name": co["name"],
                            "business": co["business"],
                            "logic": f"半导体设备供应商，射频芯片产能扩张受益",
                        })
    
    # 3. 默认：返回半导体设备公司
    if not relevant:
        for keyword, companies in company_knowledge.items():
            if "半导体设备" in keyword or "芯片" in keyword:
                for market, list_ in companies.items():
                    for co in list_[:3]:  # 每个市场最多 3 家
                        relevant.append({
                            "market": market,
                            "code": co["code"],
                            "name": co["name"],
                            "business": co["business"],
                            "logic": f"{co['position']}，半导体领域核心标的",
                        })
    
    # 去重
    seen = set()
    unique = []
    for co in relevant:
        if co["code"] not in seen:
            unique.append(co)
            seen.add(co["code"])
    
    return unique[:10]  # 最多 10 家
