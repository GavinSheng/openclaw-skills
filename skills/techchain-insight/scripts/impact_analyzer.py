#!/usr/bin/env python3
# =============================================================================
# 产业链影响分析器（优化版）
# 功能：根据事件类型生成有区分度的影响分析
# =============================================================================

from typing import Dict, List

# 事件类型定义
EVENT_TYPES = {
    "技术突破": ["突破", "攻克", "解决", "首创", "发布", "量产"],
    "负面冲击": ["暴跌", "崩盘", "跳水", "衰退", "制裁", "禁令", "限制", "泡沫破裂"],
    "正面催化": ["上涨", "牛市", "放量", "签约", "订单", "合作", "扩产"],
    "政策变化": ["政策", "补贴", "税收", "法规", "标准"],
}

# 产业链环节分类
SEGMENT_CATEGORIES = {
    "上游材料": ["硅片", "光刻胶", "电子气体", "靶材", "CMP 抛光材料", "湿电子化学品"],
    "上游设备": ["光刻机", "刻蚀机", "薄膜沉积", "离子注入", "清洗设备", "检测量测"],
    "中游设计": ["CPU", "GPU", "FPGA", "存储芯片", "模拟芯片", "功率半导体"],
    "中游制造": ["晶圆代工", "IDM", "特色工艺", "先进制程", "成熟制程"],
    "中游封测": ["封装", "测试", "先进封装", "CoWoS", "Chiplet"],
    "下游应用": ["消费电子", "汽车电子", "AI 服务器", "工业控制", "通信设备"],
}


def detect_event_type(keyword: str, news_list: List[Dict]) -> str:
    """
    检测事件类型
    """
    full_text = keyword
    for news in news_list[:3]:
        full_text += " " + news.get("title", "") + " " + news.get("content", "")
    
    # 检查负面冲击
    for kw in EVENT_TYPES["负面冲击"]:
        if kw in full_text:
            return "负面冲击"
    
    # 检查技术突破
    for kw in EVENT_TYPES["技术突破"]:
        if kw in full_text:
            return "技术突破"
    
    # 检查正面催化
    for kw in EVENT_TYPES["正面催化"]:
        if kw in full_text:
            return "正面催化"
    
    # 检查政策变化
    for kw in EVENT_TYPES["政策变化"]:
        if kw in full_text:
            return "政策变化"
    
    return "中性事件"


def get_segment_impact(segment: str, event_type: str, keyword: str) -> str:
    """
    根据事件类型和环节，返回有区分度的影响分析
    """
    # 确定环节大类
    segment_category = ""
    for category, segments in SEGMENT_CATEGORIES.items():
        if any(seg in segment for seg in segments):
            segment_category = category
            break
    
    # ==================== 负面冲击（股市暴跌等） ====================
    if event_type == "负面冲击":
        if "泡沫" in keyword or "AI" in keyword:
            # AI 泡沫破裂场景
            if segment_category == "上游材料":
                return "利空 - AI 投资放缓，上游材料需求短期承压，关注国产替代机会"
            elif segment_category == "上游设备":
                return "利空 - 资本开支缩减预期，设备订单可能下滑"
            elif segment_category == "中游设计":
                return "重大利空 - AI 芯片估值回调，GPU/CPU 需求预期下调"
            elif segment_category == "中游制造":
                return "中性偏空 - 产能利用率可能下滑，但成熟制程相对稳健"
            elif segment_category == "中游封测":
                return "中性 - 封测环节相对抗跌，先进封装仍有结构性机会"
            elif segment_category == "下游应用":
                if "AI 服务器" in segment:
                    return "重大利空 - AI 服务器需求预期下调，去库存压力"
                else:
                    return "中性 - 传统应用相对稳定"
        
        elif "股市" in keyword or "暴跌" in keyword:
            # 股市普跌场景
            if segment_category in ["上游材料", "上游设备"]:
                return "利空 - 市场情绪低迷，估值回调压力"
            elif segment_category in ["中游设计", "中游制造"]:
                return "利空 - 科技股普跌，但基本面未变，关注错杀机会"
            else:
                return "中性偏空 - 跟随大盘调整"
        
        elif "制裁" in keyword or "禁令" in keyword:
            # 制裁/禁令场景
            if "设备" in segment or "光刻" in segment:
                return "重大利空 - 出口限制直接影响设备销售"
            elif "材料" in segment:
                return "利空 - 供应链受限风险"
            elif "国产" in keyword or "自主" in keyword:
                return "利好 - 国产替代加速，自主可控逻辑强化"
            else:
                return "中性偏空 - 短期情绪冲击"
    
    # ==================== 技术突破 ====================
    elif event_type == "技术突破":
        if "材料" in keyword or "散热" in keyword:
            if segment_category == "上游材料":
                return "重大利好 - 核心技术突破，直接受益环节"
            elif segment_category == "上游设备":
                return "利好 - 间接带动设备需求"
            else:
                return "中性偏多 - 产业链传导受益"
        
        elif any(x in keyword for x in ["nm", "纳米", "制程", "工艺"]):
            if segment_category == "中游制造":
                return "重大利好 - 先进制程突破，护城河加深"
            elif segment_category == "上游设备":
                return "重大利好 - 设备需求增加，单机价值量提升"
            elif segment_category == "上游材料":
                return "利好 - 材料要求提升，高端产品渗透率提高"
            else:
                return "利好 - 产业链受益"
        
        else:
            # 通用技术突破
            if segment_category == "上游材料":
                return "利好 - 技术突破带动材料需求，国产替代加速"
            elif segment_category == "上游设备":
                return "利好 - 工艺升级带动设备需求"
            elif segment_category == "中游设计":
                return "利好 - 技术突破提升产品竞争力"
            else:
                return "利好 - 产业链受益"
    
    # ==================== 正面催化 ====================
    elif event_type == "正面催化":
        if "订单" in keyword or "签约" in keyword:
            return "重大利好 - 订单落地，业绩确定性增强"
        elif "扩产" in keyword:
            if segment_category == "上游设备":
                return "重大利好 - 扩产直接带动设备需求"
            else:
                return "利好 - 产能扩张，规模效应"
        else:
            return "利好 - 正面催化，产业链受益"
    
    # ==================== 政策变化 ====================
    elif event_type == "政策变化":
        if "补贴" in keyword or "支持" in keyword:
            return "利好 - 政策支持，行业发展加速"
        elif "限制" in keyword or "收紧" in keyword:
            return "利空 - 政策收紧，短期承压"
        else:
            return "中性 - 政策影响待观察"
    
    # ==================== 中性事件 ====================
    else:
        return "中性 - 事件影响有限，关注后续进展"


def analyze_chain_impact(keyword: str, news_list: List[Dict]) -> Dict[str, str]:
    """
    分析整个产业链的影响
    返回：{环节：影响描述}
    """
    event_type = detect_event_type(keyword, news_list)
    
    impacts = {}
    for category in SEGMENT_CATEGORIES:
        impacts[category] = get_segment_impact(category, event_type, keyword)
    
    return impacts, event_type
