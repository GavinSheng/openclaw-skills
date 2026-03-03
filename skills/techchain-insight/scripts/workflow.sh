#!/bin/bash
# =============================================================================
# TechChain Workflow - 两阶段工作流
# 流程：Skill A (TechPulse Scout) → 决策 → Skill B (TechChain Insight)
# 执行频率：每 2 小时
# =============================================================================

set -e

WORKSPACE="/home/admin/.openclaw/workspace"
SCOUT_DIR="$WORKSPACE/skills/techpulse-scout"
INSIGHT_DIR="$WORKSPACE/skills/techchain-insight"
LOG_FILE="$WORKSPACE/logs/workflow-cron.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_no_event_notification() {
    # 发送无事件通知（Scout 未产出）
    local message="🔍 科技热点监控汇报

时间：$(date '+%Y-%m-%d %H:%M')
状态：Scout 未产出事件
原因：数据源可能暂时不可用

下次检查：2 小时后"
    
    # 通过 email-sender 技能发送
    cd "$WORKSPACE/skills/email-sender" && python3 scripts/send.py \
        --subject "【科技热点监控】无事件汇报 - $(date '+%m-%d %H:%M')" \
        --message "$message" \
        2>/dev/null || log "⚠️ 邮件发送失败（非致命）"
    
    log "📧 无事件通知已发送"
}

send_brief_notification() {
    # 发送简短汇报（无 High/Medium 事件）
    local events_file="$1"
    
    local event_count=$(python3 -c "
import json
with open('$events_file', 'r') as f:
    data = json.load(f)
events = data.get('events', [])
print(len(events))
" 2>/dev/null || echo "0")
    
    local message="🔍 科技热点监控汇报

时间：$(date '+%Y-%m-%d %H:%M')
扫描结果：发现 ${event_count} 个事件
评级：无 High/Medium 级别事件
操作：已跳过深度分析

说明：当前事件重要性不足，无需特别关注。
下次检查：2 小时后"
    
    # 通过 email-sender 技能发送
    cd "$WORKSPACE/skills/email-sender" && python3 scripts/send.py \
        --subject "【科技热点监控】简短汇报 - $(date '+%m-%d %H:%M')" \
        --message "$message" \
        2>/dev/null || log "⚠️ 邮件发送失败（非致命）"
    
    log "📧 简短汇报已发送（${event_count} 个事件）"
}

log "=========================================="
log "TechChain Workflow - 两阶段工作流启动"
log "=========================================="

# 阶段 1: TechPulse Scout (热点捕捉)
log "【阶段 1】运行 TechPulse Scout..."
cd "$SCOUT_DIR" && python3 scripts/scout.py

# 查找最新的 Scout 输出
LATEST_EVENTS=$(ls -t events/events-*.json 2>/dev/null | head -1)

if [ -z "$LATEST_EVENTS" ]; then
    log "❌ 未找到 Scout 输出，发送无事件通知"
    send_no_event_notification
    exit 0
fi

log "Scout 输出：$LATEST_EVENTS"

# 检查是否触发 Skill B
TRIGGER=$(python3 -c "
import json
with open('$LATEST_EVENTS', 'r') as f:
    data = json.load(f)
print('yes' if data.get('trigger_techchain') else 'no')
")

if [ "$TRIGGER" = "yes" ]; then
    log "✅ 发现 High/Medium 事件，触发 TechChain Insight..."
    cd "$INSIGHT_DIR" && python3 scripts/event-driven-analyzer.py
else
    log "❌ 无 High/Medium 事件，发送简短汇报"
    send_brief_notification "$LATEST_EVENTS"
fi

log "=========================================="
log "TechChain Workflow 完成"
log "=========================================="
