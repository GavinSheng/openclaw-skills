#!/usr/bin/env python3
# =============================================================================
# Nitter 实例可用性检测模块
# 功能：定期检测 Nitter 实例是否可用，不可用时自动切换到国内替代源
# =============================================================================

import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any

# Nitter 实例列表
NITTER_INSTANCES = [
    "https://nitter.net",
    "https://nitter.privacy.com.de",
    "https://nitter.lunar.icu",
    "https://nitter.dark.fail",
]

# 国内替代源（当 Nitter 不可用时）
DOMESTIC_ALTERNATIVES = {
    "财联社": {
        "url": "https://www.cls.cn",
        "type": "快讯",
        "priority": "HIGH",
        "domains": ["科技", "财经", "半导体", "新能源", "AI"],
    },
    "华尔街见闻": {
        "url": "https://www.wallstreetcn.com",
        "type": "财经",
        "priority": "HIGH",
        "domains": ["全球财经", "科技", "宏观"],
    },
    "彭博社中文网": {
        "url": "https://www.bloombergchina.com",
        "type": "财经",
        "priority": "HIGH",
        "domains": ["科技", "财经", "宏观"],
    },
    "36 氪": {
        "url": "https://36kr.com",
        "type": "科技媒体",
        "priority": "MEDIUM",
        "domains": ["科技", "AI", "创业", "投资"],
    },
    "晚点 LatePost": {
        "url": "https://www.latepost.com",
        "type": "深度报道",
        "priority": "MEDIUM",
        "domains": ["科技", "商业", "深度"],
    },
}

# 可用性状态文件
STATUS_FILE = Path(__file__).parent.parent / "data" / "nitter_status.json"

def check_nitter_instance(url: str, timeout: int = 10) -> Dict[str, Any]:
    """
    检测单个 Nitter 实例是否可用
    
    Returns:
        {
            "url": str,
            "available": bool,
            "response_time_ms": int,
            "error": str (if failed)
        }
    """
    result = {
        "url": url,
        "available": False,
        "response_time_ms": 0,
        "error": "",
    }
    
    try:
        # 使用 curl 检测（带超时）
        cmd = [
            "curl", "-s", "-o", "/dev/null", "-w", "%{time_total}",
            "--max-time", str(timeout),
            "-A", "Mozilla/5.0",
            url,
        ]
        
        start_time = datetime.now()
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, timeout=timeout + 5)
        end_time = datetime.now()
        
        if proc.returncode == 0:
            response_time = float(proc.stdout.strip()) if proc.stdout.strip() else (end_time - start_time).total_seconds()
            result["available"] = True
            result["response_time_ms"] = int(response_time * 1000)
        else:
            result["error"] = f"HTTP Error: {proc.returncode}"
            
    except subprocess.TimeoutExpired:
        result["error"] = "Timeout"
    except Exception as e:
        result["error"] = str(e)[:100]
    
    return result

def check_all_nitter_instances() -> Dict[str, Any]:
    """
    检测所有 Nitter 实例
    
    Returns:
        {
            "check_time": str,
            "total_instances": int,
            "available_instances": int,
            "instances": [...],
            "has_available": bool,
            "best_instance": str (fastest)
        }
    """
    results = []
    
    for url in NITTER_INSTANCES:
        result = check_nitter_instance(url)
        results.append(result)
        print(f"检测：{url} - {'✅ 可用' if result['available'] else '❌ 不可用'} ({result.get('error', '')})")
    
    available = [r for r in results if r["available"]]
    
    summary = {
        "check_time": datetime.now().isoformat(),
        "total_instances": len(NITTER_INSTANCES),
        "available_instances": len(available),
        "instances": results,
        "has_available": len(available) > 0,
        "best_instance": min(available, key=lambda x: x["response_time_ms"])["url"] if available else "",
        "use_domestic_fallback": len(available) == 0,
    }
    
    return summary

def save_status(summary: Dict):
    """保存检测结果"""
    STATUS_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    # 保留历史记录（最近 10 次）
    history = []
    if STATUS_FILE.exists():
        try:
            with open(STATUS_FILE, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []
    
    history.append(summary)
    history = history[-10:]  # 只保留最近 10 次
    
    with open(STATUS_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def load_status() -> Dict:
    """加载最新检测结果"""
    if not STATUS_FILE.exists():
        return {}
    
    try:
        with open(STATUS_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
            return history[-1] if history else {}
    except:
        return {}

def parse_iso_datetime(iso_string: str) -> datetime:
    """
    兼容的 ISO 时间字符串解析（支持 Python 3.6+）
    """
    try:
        # Python 3.7+ 支持 fromisoformat
        return datetime.fromisoformat(iso_string)
    except AttributeError:
        # Python 3.6 及以下：手动解析
        # 处理格式：2026-03-03T12:58:16 或 2026-03-03T12:58:16.123456
        clean_str = iso_string.split('.')[0].replace('Z', '')
        return datetime.strptime(clean_str, "%Y-%m-%dT%H:%M:%S")

def get_best_source() -> Dict[str, Any]:
    """
    获取最佳数据源（优先 Nitter，不可用时用国内替代）
    
    Returns:
        {
            "source_type": "nitter" | "domestic",
            "source_url": str,
            "sources": [...]
        }
    """
    # 加载最新检测结果
    status = load_status()
    
    # 如果没有检测结果或超过 1 小时，重新检测
    if not status or not status.get("check_time"):
        print("未找到检测结果，执行检测...")
        status = check_all_nitter_instances()
        save_status(status)
    else:
        check_time = parse_iso_datetime(status["check_time"])
        if datetime.now() - check_time > timedelta(hours=1):
            print("检测结果已过时，重新检测...")
            status = check_all_nitter_instances()
            save_status(status)
    
    # 返回最佳源
    if status.get("has_available"):
        return {
            "source_type": "nitter",
            "source_url": status.get("best_instance", ""),
            "sources": [i for i in status.get("instances", []) if i.get("available")],
        }
    else:
        return {
            "source_type": "domestic",
            "source_url": "",
            "sources": DOMESTIC_ALTERNATIVES,
        }

if __name__ == "__main__":
    print("=" * 60)
    print("Nitter 实例可用性检测")
    print("=" * 60)
    
    # 执行检测
    summary = check_all_nitter_instances()
    
    # 保存结果
    save_status(summary)
    
    # 输出摘要
    print("\n" + "=" * 60)
    print(f"检测完成：{summary['available_instances']}/{summary['total_instances']} 可用")
    
    if summary["has_available"]:
        print(f"最佳实例：{summary['best_instance']}")
        print("✅ 使用 Nitter 作为数据源")
    else:
        print("❌ 所有 Nitter 实例不可用")
        print("🔄 自动切换到国内替代源")
        print(f"替代源：{list(DOMESTIC_ALTERNATIVES.keys())}")
    
    print("=" * 60)
    print(f"状态已保存：{STATUS_FILE}")
