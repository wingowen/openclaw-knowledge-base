#!/bin/bash
set -euo pipefail

REPO="wingowen/daily_stock_analysis"
WORKFLOW="每日股票分析"
ROOT="/root/.openclaw/workspace/daily_stock_analysis"

# 可传入日期：YYYYMMDD；默认今天(Asia/Shanghai)
DATE_YMD="${1:-$(TZ=Asia/Shanghai date +%Y%m%d)}"
DATE_ISO="${DATE_YMD:0:4}-${DATE_YMD:4:2}-${DATE_YMD:6:2}"

LOCAL_REPORT="$ROOT/reports/report_${DATE_YMD}.md"
LOCAL_MARKET="$ROOT/reports/market_review_${DATE_YMD}.md"

ok=true

echo "=== 双端校验开始 ${DATE_ISO} ==="

# 1) 本地报告校验
if [[ -f "$LOCAL_REPORT" ]]; then
  echo "[OK] 本地个股报告存在: $LOCAL_REPORT"
else
  echo "[FAIL] 本地个股报告缺失: $LOCAL_REPORT"
  ok=false
fi

if [[ -f "$LOCAL_MARKET" ]]; then
  echo "[OK] 本地大盘报告存在: $LOCAL_MARKET"
else
  echo "[WARN] 本地大盘报告缺失(可能是仅个股模式): $LOCAL_MARKET"
fi

# 2) 本地数据库最新记录校验
python3 - <<'PY' "$ROOT/data/stock_analysis.db" "$DATE_ISO"
import sqlite3, sys
p = sys.argv[1]
d = sys.argv[2]
conn = sqlite3.connect(p)
cur = conn.cursor()
try:
    cur.execute("SELECT COUNT(*) FROM analysis_history WHERE substr(created_at,1,10)=?", (d,))
    c = cur.fetchone()[0]
    print(f"[INFO] 本地 analysis_history 当天记录数: {c}")
except Exception as e:
    print(f"[WARN] analysis_history 当天计数失败: {e}")
try:
    cur.execute("SELECT MAX(created_at) FROM analysis_history")
    m = cur.fetchone()[0]
    print(f"[INFO] 本地 analysis_history 最新时间: {m}")
except Exception as e:
    print(f"[WARN] analysis_history 最新时间查询失败: {e}")
conn.close()
PY

# 2.5) 简单数据有效性校验（报告内容 + 当天记录）
if python3 - <<'PY' "$ROOT/data/stock_analysis.db" "$DATE_ISO" "$LOCAL_REPORT" "$LOCAL_MARKET"
import re, sqlite3, sys
from pathlib import Path

db_path, date_iso, local_report, local_market = sys.argv[1:5]
errs = []

# A) 当天至少有 1 条分析记录
try:
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM analysis_history WHERE substr(created_at,1,10)=?", (date_iso,))
    today_cnt = cur.fetchone()[0]
    conn.close()
    if today_cnt <= 0:
        errs.append(f"analysis_history 当天记录为 0（{date_iso}）")
    else:
        print(f"[OK] 数据校验: 当天 analysis_history 记录 {today_cnt} 条")
except Exception as e:
    errs.append(f"analysis_history 校验失败: {e}")

# B) 个股报告应至少包含 1 个股票代码 + 1 个评分字段
try:
    txt = Path(local_report).read_text(encoding='utf-8', errors='ignore')
    codes = set(re.findall(r"\((\d{6})\)", txt))
    scores = re.findall(r"评分\s*\d+", txt)
    if len(codes) == 0:
        errs.append("个股报告未识别到 6 位股票代码")
    else:
        print(f"[OK] 数据校验: 个股报告识别股票代码 {len(codes)} 个")
    if len(scores) == 0:
        errs.append("个股报告未识别到评分字段")
    else:
        print(f"[OK] 数据校验: 个股报告识别评分字段 {len(scores)} 处")
except Exception as e:
    errs.append(f"个股报告内容校验失败: {e}")

# C) 大盘报告存在时，校验关键指数关键词
mkt = Path(local_market)
if mkt.exists():
    try:
        mtxt = mkt.read_text(encoding='utf-8', errors='ignore')
        required = ["上证指数", "创业板指"]
        miss = [k for k in required if k not in mtxt]
        if miss:
            errs.append("大盘报告缺少关键指数字段: " + ",".join(miss))
        else:
            print("[OK] 数据校验: 大盘报告包含关键指数字段")
    except Exception as e:
        errs.append(f"大盘报告内容校验失败: {e}")

if errs:
    print("[FAIL] 数据校验未通过：")
    for e in errs:
        print("  -", e)
    sys.exit(2)
else:
    print("[OK] 简单数据校验通过")
PY
then
  :
else
  ok=false
fi

# 3) GitHub Action 最近 schedule run 校验
RUN_INFO=$(gh run list --repo "$REPO" --workflow "$WORKFLOW" --limit 20 --json databaseId,event,status,conclusion,createdAt,url --jq 'map(select(.event=="schedule")) | first')
if [[ -z "$RUN_INFO" || "$RUN_INFO" == "null" ]]; then
  echo "[FAIL] 未找到 GitHub schedule run"
  ok=false
else
  echo "[INFO] 最近 schedule run: $RUN_INFO"
  RUN_ID=$(echo "$RUN_INFO" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("databaseId",""))')
  RUN_STATUS=$(echo "$RUN_INFO" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("status",""))')
  RUN_CONCLUSION=$(echo "$RUN_INFO" | python3 -c 'import sys,json; print(json.load(sys.stdin).get("conclusion",""))')
  if [[ "$RUN_STATUS" != "completed" || "$RUN_CONCLUSION" != "success" ]]; then
    echo "[FAIL] GitHub schedule run 非成功状态: status=$RUN_STATUS conclusion=$RUN_CONCLUSION"
    ok=false
  else
    echo "[OK] GitHub schedule run 成功"
  fi

  # 4) 尝试下载该 run 的 artifact 并检查当天报告文件
  TMP_DIR=$(mktemp -d)
  if gh run download "$RUN_ID" --repo "$REPO" -D "$TMP_DIR" >/dev/null 2>&1; then
    if find "$TMP_DIR" -type f -name "report_${DATE_YMD}.md" | grep -q .; then
      echo "[OK] GitHub artifact 含当天个股报告 report_${DATE_YMD}.md"
    else
      echo "[WARN] GitHub artifact 未发现 report_${DATE_YMD}.md（可能命名或日期差异）"
    fi
    if find "$TMP_DIR" -type f -name "market_review_${DATE_YMD}.md" | grep -q .; then
      echo "[OK] GitHub artifact 含当天大盘报告 market_review_${DATE_YMD}.md"
    else
      echo "[WARN] GitHub artifact 未发现 market_review_${DATE_YMD}.md（可能模式为 stocks-only）"
    fi
  else
    echo "[WARN] GitHub artifact 下载失败（不影响 run 成功性判断）"
  fi
  rm -rf "$TMP_DIR"
fi

if [[ "$ok" == "true" ]]; then
  echo "=== 校验结果：PASS ==="
  exit 0
else
  echo "=== 校验结果：FAIL ==="
  exit 1
fi

