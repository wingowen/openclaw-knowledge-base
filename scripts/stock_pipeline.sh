#!/usr/bin/env bash
# ============================================
# 选股系统统一管道
# ============================================
# 用法:
#   ./stock_pipeline.sh preopen   # 盘前流程（生成候选票 + 入库 + 邮件）
#   ./stock_pipeline.sh daily     # 盘后流程（复盘报告 + Git push + 邮件）
#   ./stock_pipeline.sh dashboard # 启动看板服务
#   ./stock_pipeline.sh all       # 全流程（仅交易日）
# ============================================

set -euo pipefail

WORKSPACE="/root/.openclaw/workspace"
SCRIPTS="$WORKSPACE/scripts"
LOG_FILE="$WORKSPACE/stock_pipeline.log"

# 加载环境变量
if [ -f "$WORKSPACE/config/.env" ]; then
    set -a
    source "$WORKSPACE/config/.env"
    set +a
fi

log() {
    echo "[$(date '+%F %T')] $*" | tee -a "$LOG_FILE"
}

# 检查是否交易日
check_trading_day() {
    python3 "$SCRIPTS/check_trading_day.py" --quiet
}

# 盘前流程
run_preopen() {
    log "========== 盘前流程开始 =========="

    # 1) 生成候选票
    log "📊 生成候选观察名单..."
    REPORT_PATH=$(python3 "$SCRIPTS/generate_preopen_watchlist.py" | tail -n 1)

    if [[ ! -f "$REPORT_PATH" ]]; then
        REPORT_PATH="$WORKSPACE/reports/preopen_watchlist_$(date +%Y%m%d).md"
    fi

    # 2) 自动入库
    log "📥 候选票入库..."
    python3 "$SCRIPTS/watchlist_tracker.py ingest" --file "$REPORT_PATH"

    # 3) 同步情绪分
    log "🔄 同步情绪分..."
    python3 "$SCRIPTS/watchlist_tracker.py" sync-sentiment

    # 4) 发送邮件
    log "📧 发送邮件..."
    TO_ADDR="${QQ_MAIL_TO:-${QQ_MAIL:-1318263468@qq.com}}"
    SUBJECT="开盘前候选观察名单（放宽版） $(date +%Y%m%d)"
    python3 "$SCRIPTS/send_qq_mail.py" \
        --to "$TO_ADDR" \
        --subject "$SUBJECT" \
        --md "$REPORT_PATH"

    log "✅ 盘前流程完成"
}

# 盘后流程
run_daily() {
    log "========== 盘后流程开始 =========="

    DATE=$(date +%Y-%m-%d)

    # 1) 生成复盘报告
    log "📊 生成 $DATE 复盘报告..."
    QQ_MAIL_USER="$QQ_MAIL_USER" QQ_MAIL_AUTH_CODE="$QQ_MAIL_AUTH_CODE" QQ_MAIL_TO="$QQ_MAIL_TO" \
        python3 "$SCRIPTS/generate_daily_report.py" --date "$DATE"

    # 2) Git commit & push
    log "📤 Git push..."
    cd "$WORKSPACE"
    git add -A
    git commit -m "auto: stock daily report $DATE" || log "ℹ️ 无变更"
    git push || log "⚠️ Git push 失败"

    log "✅ 盘后流程完成"
}

# 启动看板服务
run_dashboard() {
    log "========== 启动看板服务 =========="

    # 检查是否已有进程运行
    if pgrep -f "watchlist_dashboard.py" > /dev/null; then
        log "⚠️ 看板服务已在运行"
        return 0
    fi

    # 后台启动
    nohup python3 "$SCRIPTS/watchlist_dashboard.py" >> "$WORKSPACE/logs/dashboard.log" 2>&1 &
    log "✅ 看板服务已启动 (http://localhost:5000)"
}

# 启动 daily_stock_analysis 服务
run_analysis_api() {
    log "========== 启动分析 API 服务 =========="

    # 检查是否已有进程运行
    if pgrep -f "uvicorn.*8000" > /dev/null; then
        log "⚠️ 分析 API 已在运行"
        return 0
    fi

    cd "$WORKSPACE/daily_stock_analysis"
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 >> "$WORKSPACE/logs/analysis_api.log" 2>&1 &
    log "✅ 分析 API 已启动 (http://localhost:8000)"
}

# 主入口
main() {
    mkdir -p "$WORKSPACE/logs"

    case "${1:-help}" in
        preopen)
            if check_trading_day; then
                run_preopen
            else
                log "非交易日，跳过盘前流程"
            fi
            ;;
        daily)
            if check_trading_day; then
                run_daily
            else
                log "非交易日，跳过盘后流程"
            fi
            ;;
        dashboard)
            run_dashboard
            ;;
        api)
            run_analysis_api
            ;;
        services)
            run_dashboard
            run_analysis_api
            ;;
        all)
            if check_trading_day; then
                run_preopen
                run_daily
            else
                log "非交易日，跳过全流程"
            fi
            ;;
        help|*)
            echo "用法: $0 {preopen|daily|dashboard|api|services|all}"
            echo ""
            echo "  preopen   - 盘前流程（生成候选票 + 入库 + 邮件）"
            echo "  daily     - 盘后流程（复盘报告 + Git push + 邮件）"
            echo "  dashboard - 启动看板服务 (localhost:5000)"
            echo "  api       - 启动分析 API 服务 (localhost:8000)"
            echo "  services  - 启动所有服务"
            echo "  all       - 全流程（仅交易日）"
            ;;
    esac
}

main "$@"
