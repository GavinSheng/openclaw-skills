#!/usr/bin/env python3
# =============================================================================
# TechChain Insight - 基于热点的智能报告
# 流程：热点捕捉 → 只对热点进行深度分析 → 发送邮件
# 执行频率：每 4 小时（先运行热点捕捉，再分析热点）
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
EMAIL_SENDER_DIR = WORKSPACE / "skills" / "email-sender"
LOG_FILE = SKILL_DIR / "logs" / "smart-report.log"
REPORT_DIR = SKILL_DIR / "reports" / "smart"
HOTSPOTS_DIR = SKILL_DIR / "hotspots"

EMAIL_TO = os.getenv('TECHCHAIN_REPORT_EMAIL', 'recipient@example.com')  # 使用环境变量，带默认值

# ==================== 日志函数 ====================
def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] {message}"
    print(log_msg)
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_msg + "\n")

# ==================== 运行热点捕捉 ====================
def run_hotspot_scanner() -> Dict:
    """运行热点捕捉技能"""
    log("正在运行热点捕捉技能...")
    
    try:
        cmd = ["python3", "scripts/hotspot-scanner.py"]
        result = subprocess.run(cmd, cwd=SKILL_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=300)
        
        if result.returncode == 0:
            # 查找最新的热点文件
            hotspots_files = list(HOTSPOTS_DIR.glob("hotspots-*.json"))
            if hotspots_files:
                latest = max(hotspots_files, key=lambda p: p.stat().st_mtime)
                with open(latest, 'r', encoding='utf-8') as f:
                    hotspot_data = json.load(f)
                log(f"热点捕捉完成：发现{hotspot_data.get('hotspots_found', 0)}个热点")
                return hotspot_data
            else:
                log("未找到热点文件")
                return {"hotspots_found": 0, "hotspots": []}
        else:
            log(f"热点捕捉失败：{result.stderr[:200]}")
            return {"hotspots_found": 0, "hotspots": []}
    
    except Exception as e:
        log(f"热点捕捉异常：{str(e)}")
        return {"hotspots_found": 0, "hotspots": []}

# ==================== 分析热点 ====================
def analyze_hotspot(topic: str) -> Dict:
    """分析单个热点"""
    log(f"  深度分析：{topic}...")
    
    try:
        cmd = ["python3", "scripts/main.py", topic]
        result = subprocess.run(cmd, cwd=SKILL_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=120)
        
        if result.returncode == 0:
            output = result.stdout
            
            # 提取关键信息
            summary = {
                "topic": topic,
                "success": True,
                "full_report": output,
                "highlight": "中性",
            }
            
            if "重大利好" in output:
                summary["highlight"] = "重大利好"
            elif "利好" in output:
                summary["highlight"] = "利好"
            
            return summary
        else:
            log(f"    失败：{result.stderr[:100]}")
            return {"topic": topic, "success": False, "error": result.stderr[:200]}
    
    except Exception as e:
        log(f"    异常：{str(e)[:100]}")
        return {"topic": topic, "success": False, "error": str(e)[:200]}

# ==================== 生成报告 ====================
def generate_smart_report(hotspot_data: Dict, analyses: List[Dict]) -> str:
    """生成智能报告"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    hotspots = hotspot_data.get("hotspots", [])
    total_hotspots = len(hotspots)
    analyzed = len([a for a in analyses if a.get("success")])
    
    report = f"""# 🔗 TechChain Insight - 智能热点报告

**报告时间**: {now}  
**扫描主题**: {hotspot_data.get('total_topics_scanned', 0)} 个  
**发现热点**: {total_hotspots} 个  
**深度分析**: {analyzed} 个  
**下次报告**: {(datetime.now() + timedelta(hours=4)).strftime("%Y-%m-%d %H:%M")}

---

## 📊 热点概览

| 排名 | 热点主题 | 评分 | 原因 | 状态 |
|------|----------|------|------|------|
"""
    
    for i, h in enumerate(hotspots[:10], 1):
        status = "✅ 已分析" if any(a["topic"] == h["topic"] and a.get("success") for a in analyses) else "❌ 分析失败"
        report += f"| {i} | {h['topic']} | {h['score']} | {h['reason']} | {status} |\n"
    
    report += f"""
---

## 🎯 深度分析结果

"""
    
    # 添加分析结果
    for i, analysis in enumerate(analyses, 1):
        if analysis.get("success") and analysis.get("full_report"):
            full = analysis["full_report"]
            
            report += f"\n---\n\n### {i}. {analysis['topic']} - {analysis.get('highlight', '中性')}\n\n"
            
            # 提取产业链
            chain_start = full.find("## 🔗 产业链")
            if chain_start > 0:
                chain_end = full.find("## 📈 核心受益")
                if chain_end < 0:
                    chain_end = full.find("## ⚠️ 风险")
                if chain_end > 0:
                    report += full[chain_start:chain_end] + "\n"
            
            # 提取公司映射
            companies_start = full.find("## 📈 核心受益")
            if companies_start > 0:
                companies_end = full.find("## ⚠️ 风险")
                if companies_end < 0:
                    companies_end = full.find("## 📚 参考")
                if companies_end > 0:
                    report += "\n" + full[companies_start:companies_end] + "\n"
    
    # 无热点时的说明
    if not hotspots:
        report += "本次扫描未发现热点，市场整体平稳，暂无需深度分析。\n"
    
    report += f"""

---

## ⚠️ 风险提示

- 本报告基于公开信息整理，不构成投资建议
- 热点捕捉基于关键词匹配，可能存在遗漏
- 投资有风险，决策需谨慎

---

## 📧 报告说明

- **扫描频率**: 每 4 小时一次
- **热点捕捉**: 12 个科技领域实时扫描
- **深度分析**: 仅对热点主题进行产业链 + 公司映射分析
- **节省资源**: 相比固定 12 主题分析，节省约 70% token

---

*TechChain Insight Smart Report v2.0 | 科技链·热点透视*
"""
    
    return report

# ==================== 发送邮件 ====================
def send_email(content: str):
    """发送邮件"""
    log("正在发送邮件...")
    
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    subject = f"🔗 TechChain Insight 智能热点报告 - {now}"
    
    cmd = [
        "python3", "scripts/main.py",
        "--to-email", EMAIL_TO,
        "--subject", subject,
        "--content", content,
        "--content-format", "markdown"
    ]
    
    result = subprocess.run(cmd, cwd=EMAIL_SENDER_DIR, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=120)
    
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
    log("TechChain Insight - 智能热点报告启动")
    log("=" * 60)
    
    try:
        # 确保目录存在
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        HOTSPOTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # 1. 运行热点捕捉
        hotspot_data = run_hotspot_scanner()
        
        # 2. 对热点进行深度分析
        hotspots = hotspot_data.get("hotspots", [])
        analyses = []
        
        if hotspots:
            log(f"开始深度分析 {len(hotspots)} 个热点...")
            for h in hotspots:
                result = analyze_hotspot(h["topic"])
                analyses.append(result)
        else:
            log("无热点，跳过深度分析")
        
        # 3. 生成报告
        report_content = generate_smart_report(hotspot_data, analyses)
        
        # 4. 保存报告
        report_file = REPORT_DIR / f"smart-report-{datetime.now().strftime('%Y%m%d-%H%M')}.md"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report_content)
        log(f"报告已保存：{report_file}")
        
        # 5. 发送邮件
        send_email(report_content)
        
        log("=" * 60)
        log("智能热点报告完成")
        log("=" * 60)
        
    except Exception as e:
        log(f"❌ 执行异常：{str(e)}")
        import traceback
        log(traceback.format_exc())

if __name__ == "__main__":
    main()
