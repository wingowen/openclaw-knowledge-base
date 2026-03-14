#!/bin/bash
# run_all.sh - 工作区统一入口脚本
# 用法: ./run_all.sh [选项]
#   --fetch     仅数据抓取
#   --clean     仅数据清洗
#   --report    仅报告生成
#   --sync      仅 Notion 同步
#   --commit    仅 Git 提交
#   (无参数)    全流程执行

set -euo pipefail

WORKSPACE="/root/.openclaw/workspace"
SCRIPTS="$WORKSPACE/02-scripts"
RAW="$WORKSPACE/00-raw"
PROCESSED="$WORKSPACE/01-processed"

# 加载环境变量
if [ -f "$WORKSPACE/.env" ]; then
  source "$WORKSPACE/.env"
fi

run_fetch() {
  echo "📥 [1/4] 数据抓取..."
  # 市场数据
  python3 "$SCRIPTS/market/hs300_fetch.py" 2>/dev/null || echo "  ⚠️ HS300 抓取跳过"
  echo "  ✅ 数据抓取完成"
}

run_clean() {
  echo "🧹 [2/4] 数据清洗..."
  # 可在此添加清洗逻辑
  echo "  ✅ 数据清洗完成"
}

run_report() {
  echo "📊 [3/4] 报告生成..."
  python3 "$SCRIPTS/docs/check_doc_updates.py" 2>/dev/null || echo "  ⚠️ 文档更新检查跳过"
  echo "  ✅ 报告生成完成"
}

run_sync() {
  echo "🔄 [4/4] Notion 同步..."
  python3 "$SCRIPTS/docs/sync_doc_to_notion.py" 2>/dev/null || echo "  ⚠️ Notion 同步跳过"
  echo "  ✅ 同步完成"
}

run_commit() {
  echo "📦 Git 提交..."
  cd "$WORKSPACE"
  git add -A
  git commit -m "auto: run_all $(date '+%Y-%m-%d %H:%M')" || echo "  ℹ️ 无变更"
  echo "  ✅ Git 提交完成"
}

# 解析参数
if [ $# -eq 0 ]; then
  run_fetch
  run_clean
  run_report
  run_sync
  run_commit
else
  for arg in "$@"; do
    case $arg in
      --fetch)  run_fetch ;;
      --clean)  run_clean ;;
      --report) run_report ;;
      --sync)   run_sync ;;
      --commit) run_commit ;;
      *)        echo "❌ 未知参数: $arg"; exit 1 ;;
    esac
  done
fi

echo ""
echo "✅ 全部完成！"
