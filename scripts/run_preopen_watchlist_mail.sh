#!/usr/bin/env bash
set -euo pipefail

WORKDIR="/root/.openclaw/workspace"
cd "$WORKDIR"

# load env for QQ SMTP
set -a
source /root/.openclaw/workspace/daily_stock_analysis/.env
set +a

DATE="$(date +%Y%m%d)"

# 1) 生成放宽版候选观察名单
REPORT_PATH="$(python3 /root/.openclaw/workspace/scripts/generate_preopen_watchlist.py | tail -n 1)"

if [[ ! -f "$REPORT_PATH" ]]; then
  REPORT_PATH="/root/.openclaw/workspace/reports/preopen_watchlist_${DATE}.md"
fi

# 2) 自动入库候选票
python3 /root/.openclaw/workspace/scripts/watchlist_tracker.py ingest --file "$REPORT_PATH"

# 3) 发送邮件
TO_ADDR="${QQ_MAIL_TO:-${QQ_MAIL:-1318263468@qq.com}}"
SUBJECT="开盘前候选观察名单（放宽版） ${DATE}"

python3 /root/.openclaw/workspace/scripts/send_qq_mail.py \
  --to "$TO_ADDR" \
  --subject "$SUBJECT" \
  --md "$REPORT_PATH"

echo "[$(date '+%F %T')] sent preopen watchlist: $REPORT_PATH -> $TO_ADDR"
