#!/usr/bin/env python3
# =============================================================================
# TechChain Insight - 定时报告任务
# 功能：每 4 小时自动分析科技热点并发送邮件
# 执行时间：00:00, 04:00, 08:00, 12:00, 16:00, 20:00
# 收件人：使用环境变量 TECHCHAIN_REPORT_EMAIL
# =============================================================================

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# ==================== 配置区域 ====================
WORKSPACE = Path("/home/admin/.openclaw/workspace")
SKILL_DIR = WORKSPACE / "skills" / "techchain-insight"
EMAIL_SENDER_DIR = WORKSPACE / "skills" / "email-sender"
LOG_FILE = SKILL_DIR / "logs" / "scheduled-report.log"
REPORT_DIR = SKILL_DIR / "reports" / "scheduled"

EMAIL_TO = os.getenv('TECHCHAIN_REPORT_EMAIL', 'recipient@example.com')  # 使用环境变量，带默认值

# 监控的热点主题（每次随机选择 3-5 个分析）
HOT_TOPICS = [
    "固态电池 最新进展",
    "人工智能 AI 芯片",
    "人形机器人 产业化",
    "半导体 国产替代",
    "新能源汽车 销量",
    "自动驾驶 FSD",
    "量子计算 突破",
    "6G 通信 技术",
    "低空经济 eVTOL",
    "商业航天 发射",
    "钙钛矿电池 量产",
    "合成生物 制造",
]

# ==================== 日志函数 ====================
def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

# ==================== 分析单个主题（完整版） ====================
def analyze_topic(topic: str) -> dict:
    """分析单个主题，返回完整报告"""
    log(f"  分析：{topic}...")
    
    try:
        cmd = ["python3", "scripts/main.py", topic]
        result = subprocess.run(
            cmd,
            cwd=SKILL_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            timeout=120
        )
        
        if result.returncode == 0:
            output = result.stdout
            
            # 提取关键信息
            summary = {
                "topic": topic,
                "success": True,
                "full_report": output,  # 完整报告
                "companies_count": 0,
                "high_cred_count": 0,
            }
            
            # 统计公司数量
            if "A 股" in output:
                summary["companies_count"] += output.count("| 代码 |")
            if "高可信度" in output:
                summary["high_cred_count"] = output.count("`可信度：")
            
            # 提取产业链亮点
            if "重大利好" in output:
                summary["highlight"] = "重大利好"
            elif "利好" in output:
                summary["highlight"] = "利好"
            else:
                summary["highlight"] = "中性"
            
            return summary
        else:
            log(f"    失败：{result.stderr[:100]}")
            return {"topic": topic, "success": False, "error": result.stderr[:200]}
    
    except Exception as e:
        log(f"    异常：{str(e)[:100]}")
        return {"topic": topic, "success": False, "error": str(e)[:200]}

# ==================== 生成完整报告 ====================
def generate_full_report(analyses: list) -> str:
    """生成完整产业链分析报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 统计
    total = len(analyses)
    success = sum(1 for a in analyses if a.get("success"))
    highlights = [a for a in analyses if a.get("highlight") in ["重大利好", "利好"]]
    
    report = f"""# 🔗 TechChain Insight - 深度分析报告

**报告时间**: {now}  
**分析主题**: {success}/{total} 个  
**下次报告**: {(datetime.now() + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M")}  
**报告类型**: 完整产业链 + 公司映射

---

## 📊 本次分析概览

| 指标 | 数值 |
|------|------|
| 分析主题数 | {total} |
| 成功分析 | {success} |
| 发现利好 | {len(highlights)} |
| 覆盖领域 | 半导体/AI/新能源/机器人/6G/量子计算等 |

---

## 🎯 重点关注（利好主题）

"""
    
    # 添加所有主题完整分析（一个都不少）
    report += "## 🎯 全部主题深度分析\n\n"
    for i, analysis in enumerate(analyses, 1):
        if analysis.get("success") and analysis.get("full_report"):
            full = analysis["full_report"]
            
            # 添加主题标题
            report += f"\n---\n\n### {i}. {analysis['topic']} - {analysis.get('highlight', '中性')}\n\n"
            
            # 提取产业链分析部分
            chain_start = full.find("## 🔗 产业链")
            if chain_start > 0:
                chain_end = full.find("## 📈 核心受益")
                if chain_end < 0:
                    chain_end = full.find("## ⚠️ 风险")
                if chain_end > 0:
                    chain_section = full[chain_start:chain_end]
                    report += f"{chain_section}\n"
            
            # 提取公司映射部分
            companies_start = full.find("## 📈 核心受益")
            if companies_start > 0:
                companies_end = full.find("## ⚠️ 风险")
                if companies_end < 0:
                    companies_end = full.find("## 📚 参考")
                if companies_end > 0:
                    companies_section = full[companies_start:companies_end]
                    report += f"\n{companies_section}\n"
            
            # 提取竞争格局（如有）
            competition_start = full.find("### 📊 竞争格局")
            if competition_start > 0:
                competition_end = full.find("###", competition_start + 10)
                if competition_end > 0:
                    competition_section = full[competition_start:competition_end]
                    report += f"\n{competition_section}\n"
            
            # 提取关键数据（如有）
            entities_start = full.find("### 📋 关键数据")
            if entities_start > 0:
                entities_end = full.find("###", entities_start + 10)
                if entities_end > 0:
                    entities_section = full[entities_start:entities_end]
                    report += f"\n{entities_section}\n"
        else:
            report += f"\n---\n\n### {i}. {analysis['topic']} - ❌ 分析失败\n"
            if analysis.get("error"):
                report += f"错误：{analysis['error'][:200]}\n"
    
    # 添加所有主题摘要
    report += "## 📋 全部主题分析摘要\n\n"
    for i, analysis in enumerate(analyses, 1):
        if analysis.get("success"):
            report += f"{i}. **{analysis['topic']}** - {analysis.get('highlight', '中性')}\n"
        else:
            report += f"{i}. **{analysis['topic']}** - ❌ 分析失败\n"
    
    report += "\n"
    
    # 添加完整报告附件说明
    report += f"""
---

## 📎 完整报告附件

以下是各主题的完整分析报告链接（已保存至服务器）：

"""
    for i, analysis in enumerate(analyses, 1):
        if analysis.get("success"):
            report += f"{i}. {analysis['topic']} - ✅ 已生成完整产业链 + 公司映射报告\n"
    
    # 添加免责声明
    report += f"""

---

## ⚠️ 风险提示

- 本报告基于公开信息整理，不构成投资建议
- 科技行业变化快速，信息可能存在滞后
- 投资有风险，决策需谨慎

---

## 📧 报告说明

- **发送频率**: 每 4 小时一次（00:00/04:00/08:00/12:00/16:00/20:00）
- **覆盖领域**: 半导体、AI、新能源、机器人、6G、量子计算等 16 个科技领域
- **数据来源**: SearXNG 聚合搜索 + 可信度验证
- **报告内容**: 完整产业链分析 + 全球公司映射（A 股/港股/美股）

---

*TechChain Insight Deep Analysis Report v1.0 | 科技链·热点透视*
"""
    
    return report

# ==================== 发送邮件 ====================
def send_email(content: str):
    """发送邮件"""
    log("正在发送邮件...")
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject = f"🔗 TechChain Insight 定期报告 - {now}"
    
    cmd = [
        "python3", "scripts/main.py",
        "--to-email", EMAIL_TO,
        "--subject", subject,
        "--content", content,
        "--content-format", "markdown"
    ]
    
    result = subprocess.run(
        cmd,
        cwd=EMAIL_SENDER_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        timeout=120
    )
    
    if result.returncode == 0:
        log("✅ 邮件发送成功")
        return True
    else:
        log(f"❌ 邮件发送失败：{result.stderr[:500]}")
        return False

# ==================== 主流程 ====================
def main():
    """主入口"""
    log("=" * 60)
    log("TechChain Insight - 定时报告任务启动")
    log("=" * 60)
    
    try:
        # 确保目录存在
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        
        # 选择本次分析的主题（全部 12 个热点，一个都不漏）
        selected_topics = HOT_TOPICS  # 分析全部主题
        log(f"本次分析主题：{len(selected_topics)} 个热点（全覆盖）")
        
        # 分析每个主题
        analyses = []
        for topic in selected_topics:
            result = analyze_topic(topic)
            analyses.append(result)
        
        # 生成完整报告
        report_content = generate_full_report(analyses)
        
        # 保存报告
        report_file = REPORT_DIR / f"report-{datetime.now().strftime('%Y%m%d-%H%M')}.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)
        log(f"报告已保存：{report_file}")
        
        # 发送邮件
        send_email(report_content)
        
        log("=" * 60)
        log("定时报告任务完成")
        log("=" * 60)
        
    except Exception as e:
        log(f"❌ 执行异常：{str(e)}")
        import traceback
        log(traceback.format_exc())

if __name__ == "__main__":
    main()
