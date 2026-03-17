#!/bin/bash
# A股每日复盘 - 完整流程 wrapper
set -euo pipefail

# Load env
[ -f /root/.openclaw/.env ] && export $(grep -v '^#' /root/.openclaw/.env | xargs)

# Load env
[ -f /root/.openclaw/.env ] && export $(grep -v '^#' /root/.openclaw/.env | xargs)

SCRIPTS_DIR="/root/.openclaw/workspace/scripts"
LOG_FILE="/root/.openclaw/workspace/cron_daily_report.log"
DATE=$(date +%Y-%m-%d)

echo "====== $DATE $(date +%H:%M:%S) ======" >> "$LOG_FILE"

# 1) 检查是否为交易日
if ! /usr/bin/python3 "$SCRIPTS_DIR/check_trading_day.py" --date "$DATE" --quiet 2>> "$LOG_FILE"; then
    echo "[$DATE] 非交易日，跳过" >> "$LOG_FILE"
    exit 0
fi

echo "[$DATE] 交易日，开始生成报告..." >> "$LOG_FILE"

# 2) 生成报告 + 保存到 Obsidian + QQ邮件
QQ_MAIL_USER="$QQ_MAIL_USER" QQ_MAIL_AUTH_CODE="$QQ_MAIL_AUTH_CODE" QQ_MAIL_TO="$QQ_MAIL_TO" \
  /usr/bin/python3 "$SCRIPTS_DIR/generate_daily_report.py" --date "$DATE" >> "$LOG_FILE" 2>&1

echo "[$DATE] 流程完成" >> "$LOG_FILE"
