#!/usr/bin/env python3
# =============================================================================
# TechChain Insight - 事件驱动触发器（简化版）
# 功能：接收 TechPulse Scout 的事件列表，触发深度分析
# =============================================================================

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

# ==================== 配置区域 ====================
WORKSPACE = Path("/home/admin/.openclaw/workspace")
SKILL_DIR = WORKSPACE / "skills" / "techchain-insight"
SCOUT_DIR = WORKSPACE / "skills" / "techpulse-scout"
EMAIL_SENDER_DIR = WORKSPACE / "skills" / "email-sender"
LOG_FILE = SKILL_DIR / "logs" / "event-driven.log"
REPORT_DIR = SKILL_DIR / "reports" / "event-driven"

EMAIL_TO = os.getenv('TECHCHAIN_REPORT_EMAIL', 'recipient@example.com')  # 使用环境变量，带默认值

# ==================== 日志函数 ====================
def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

# ==================== 分析事件 ====================
def analyze_event(event: Dict) -> Dict:
    """分析单个事件"""
    log(f"  深度分析：{event['title'][:60]}...")
    
    # 构建分析输入：标题 + 摘要 + tags
    analysis_input = {
        "title": event["title"],
        "summary": event.get("summary", ""),
        "tags": event.get("tags", []),
        "companies": event.get("companies", []),
    }
    
    # 保存输入供 main.py 读取
    input_file = SKILL_DIR / "logs" / "current_event.json"
    input_file.parent.mkdir(parents=True, exist_ok=True)
    with open(input_file, "w", encoding="utf-8") as f:
        json.dump(analysis_input, f, ensure_ascii=False, indent=2)
    
    # 使用标题作为搜索词（简短）
    search_query = event["title"][:30]  # 截断到 30 字
    
    try:
        cmd = ["python3", "scripts/main.py", search_query, "--event-input", str(input_file)]
        result = subprocess.run(cmd, cwd=SKILL_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=120)
        
        if result.returncode == 0:
            output = result.stdout
            return {
                "event_id": event["id"],
                "event_title": event["title"],
                "success": True,
                "full_report": output,
                "priority": event["priority"],
            }
        else:
            log(f"    失败：{result.stderr[:100]}")
            return {
                "event_id": event["id"],
                "event_title": event["title"],
                "success": False,
                "error": result.stderr[:200],
            }
    
    except Exception as e:
        log(f"    异常：{str(e)[:100]}")
        return {
            "event_id": event["id"],
            "event_title": event["title"],
            "success": False,
            "error": str(e)[:200],
        }

# ==================== 生成报告 ====================
def generate_event_report(scout_output: Dict, analyses: List[Dict]) -> str:
    """生成事件驱动报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    events = scout_output.get("events", [])
    analyzed_success = [a for a in analyses if a.get("success")]
    
    total_events = len(events)
    analyzed_count = len(analyses)
    truncated_note = f"\n\n> ⚠️ **注**: 共发现 {total_events} 个事件，仅分析最重要的 {analyzed_count} 个" if total_events > analyzed_count else ""
    
    report = f"""# 🔗 TechChain Insight - 事件驱动深度报告

**报告时间**: {now}  
**触发方式**: TechPulse Scout 事件驱动  
**扫描时间**: {scout_output.get('scan_time', 'N/A')}  
**发现事件**: {total_events}个{truncated_note}  
**深度分析**: {len(analyzed_success)}个  

---

## 📊 事件概览

| # | 优先级 | 标题 |
|---|--------|------|
"""
    
    for i, analysis in enumerate(analyses, 1):
        title = analysis.get('event_title', 'Unknown')[:60]
        priority = analysis.get('priority', 'LOW')
        report += f"| {i} | {priority} | {title}... |\n"
    
    report += f"""
---

## 🎯 深度分析结果

"""
    
    for i, analysis in enumerate(analyses, 1):
        if analysis.get("success") and analysis.get("full_report"):
            full = analysis["full_report"]
            report += f"\n---\n\n### {i}. {analysis['event_title']}\n\n"
            
            # 提取产业链部分
            chain_start = full.find("## 🔗 产业链")
            if chain_start > 0:
                chain_end = full.find("## 📈 核心受益")
                if chain_end < 0:
                    chain_end = full.find("## ⚠️ 风险")
                if chain_end > 0:
                    report += full[chain_start:chain_end] + "\n"
            
            # 提取公司映射部分
            companies_start = full.find("## 📈 核心受益")
            if companies_start > 0:
                companies_end = full.find("## ⚠️ 风险")
                if companies_end < 0:
                    companies_end = full.find("## 📚 参考")
                if companies_end > 0:
                    report += "\n" + full[companies_start:companies_end] + "\n"
    
    if not events:
        report += "TechPulse Scout 未发现 High/Medium 优先级事件。\n"
    
    report += f"""
---

## ⚠️ 风险提示

- 本报告基于公开信息整理，不构成投资建议
- 投资有风险，决策需谨慎

---

*TechChain Insight Event-Driven Report v2.0*
"""
    
    return report

# ==================== 发送邮件 ====================
def send_email(content: str):
    """发送邮件"""
    log("正在发送邮件...")
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject = f"🔗 TechChain Insight 事件驱动报告 - {now}"
    
    MAX_CONTENT_SIZE = 100 * 1024
    if len(content.encode('utf-8')) > MAX_CONTENT_SIZE:
        content = content.encode('utf-8')[:MAX_CONTENT_SIZE].decode('utf-8', errors='ignore')
        content += "\n\n---\n\n⚠️ **报告因大小限制被截断。**"
    
    try:
        cmd = [
            "python3", "scripts/main.py",
            "--to-email", EMAIL_TO,
            "--subject", subject,
            "--content-format", "markdown"
        ]
        
        result = subprocess.run(
            cmd,
            cwd=EMAIL_SENDER_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=120,
            input=content
        )
        
        if result.returncode == 0:
            log("✅ 邮件发送成功")
            return True
        else:
            log(f"❌ 邮件发送失败：{result.stderr[:500]}")
            return False
    except Exception as e:
        log(f"❌ 邮件发送异常：{str(e)[:200]}")
        return False

# ==================== 主流程 ====================
def main():
    """主入口"""
    log("=" * 60)
    log("TechChain Insight - 事件驱动分析启动")
    log("=" * 60)
    
    try:
        scout_files = list(SCOUT_DIR.glob("events/events-*.json"))
        if not scout_files:
            log("❌ 未找到 Scout 输出文件")
            return
        
        latest_scout = max(scout_files, key=lambda p: p.stat().st_mtime)
        log(f"Scout 输出：{latest_scout}")
        
        with open(latest_scout, 'r', encoding='utf-8') as f:
            scout_output = json.load(f)
        
        events = scout_output.get("events", [])
        
        if not events:
            log("✅ 无 High/Medium 事件，跳过深度分析")
            return
        
        log(f"发现 {len(events)} 个待分析事件")
        
        # 按优先级排序，选最重要的 8 个
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        events_sorted = sorted(events, key=lambda x: (
            priority_order.get(x.get("priority", "LOW"), 2),
            -len(x.get("companies", [])),
            -len(x.get("tags", []))
        ))
        
        MAX_EVENTS = 8
        events_to_analyze = events_sorted[:MAX_EVENTS]
        
        if len(events_sorted) > MAX_EVENTS:
            log(f"⚠️ 事件过多 ({len(events_sorted)}个)，仅分析最重要的 {MAX_EVENTS} 个")
        
        # 深度分析每个事件
        analyses = []
        for event in events_to_analyze:
            if event.get("trigger_next"):
                result = analyze_event(event)
                analyses.append(result)
        
        # 生成报告
        report_content = generate_event_report(scout_output, analyses)
        
        # 保存报告
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        report_file = REPORT_DIR / f"event-driven-{datetime.now().strftime('%Y%m%d-%H%M')}.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)
        log(f"报告已保存：{report_file}")
        
        # 发送邮件
        send_email(report_content)
        
        log("=" * 60)
        log("事件驱动分析完成")
        log("=" * 60)
        
    except Exception as e:
        log(f"❌ 执行异常：{str(e)}")
        import traceback
        log(traceback.format_exc())

if __name__ == "__main__":
    main()
