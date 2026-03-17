#!/bin/bash
# Download ZhuLinsen/daily_stock_analysis core files via raw.githubusercontent.com
set -e

BASE="/root/.openclaw/workspace/daily_stock_analysis"
REPO="https://raw.githubusercontent.com/ZhuLinsen/daily_stock_analysis/main"
mkdir -p "$BASE"

download() {
    local url="$REPO/$1"
    local dest="$BASE/$1"
    mkdir -p "$(dirname "$dest")"
    curl -sL --connect-timeout 10 --max-time 30 "$url" -o "$dest"
    echo "✓ $1"
}

# Root files
for f in .env.example .gitignore .dockerignore AGENTS.md README.md SKILL.md LICENSE \
          main.py server.py analyzer_service.py pyproject.toml requirements.txt test_env.py \
          litellm_config.example.yaml; do
    download "$f"
done

# Core modules
for f in src/__init__.py src/config.py src/analyzer.py src/stock_analyzer.py src/market_analyzer.py \
          src/notification.py src/formatters.py src/scheduler.py src/storage.py src/search_service.py \
          src/auth.py src/logging_config.py src/md2img.py src/feishu_doc.py src/enums.py \
          src/webui_frontend.py; do
    download "$f"
done

# Core subdirs
for f in src/core/pipeline.py src/core/config_manager.py src/core/config_registry.py \
          src/core/market_profile.py src/core/market_review.py src/core/market_strategy.py \
          src/core/backtest_engine.py src/core/trading_calendar.py; do
    download "$f"
done

# Data providers
for f in data_provider/__init__.py data_provider/base.py data_provider/akshare_fetcher.py \
          data_provider/efinance_fetcher.py data_provider/baostock_fetcher.py \
          data_provider/fundamental_adapter.py data_provider/realtime_types.py \
          data_provider/us_index_mapping.py data_provider/yfinance_fetcher.py \
          data_provider/tushare_fetcher.py data_provider/pytdx_fetcher.py; do
    download "$f"
done

# Data module
for f in src/data/__init__.py src/data/stock_mapping.py; do
    download "$f"
done

# Notification senders
for f in src/notification_sender/__init__.py src/notification_sender/feishu_sender.py \
          src/notification_sender/wechat_sender.py src/notification_sender/telegram_sender.py \
          src/notification_sender/email_sender.py src/notification_sender/discord_sender.py \
          src/notification_sender/custom_webhook_sender.py src/notification_sender/pushplus_sender.py \
          src/notification_sender/serverchan3_sender.py src/notification_sender/pushover_sender.py \
          src/notification_sender/astrbot_sender.py; do
    download "$f"
done

# Services
for f in src/services/__init__.py src/services/analysis_service.py src/services/stock_service.py \
          src/services/portfolio_service.py src/services/backtest_service.py \
          src/services/report_renderer.py src/services/history_service.py \
          src/services/history_comparison_service.py src/services/task_service.py \
          src/services/task_queue.py src/services/system_config_service.py \
          src/services/stock_code_utils.py src/services/name_to_code_resolver.py \
          src/services/portfolio_import_service.py src/services/portfolio_risk_service.py \
          src/services/import_parser.py src/services/image_stock_extractor.py \
          src/services/social_sentiment_service.py src/services/agent_model_service.py; do
    download "$f"
done

# Repositories
for f in src/repositories/__init__.py src/repositories/analysis_repo.py \
          src/repositories/backtest_repo.py src/repositories/portfolio_repo.py \
          src/repositories/stock_repo.py; do
    download "$f"
done

# Schemas
for f in src/schemas/__init__.py src/schemas/report_schema.py; do
    download "$f"
done

# Bot
for f in bot/__init__.py bot/dispatcher.py bot/handler.py bot/models.py \
          bot/commands/__init__.py bot/commands/base.py bot/commands/analyze.py \
          bot/commands/ask.py bot/commands/batch.py bot/commands/chat.py \
          bot/commands/help.py bot/commands/market.py bot/commands/status.py \
          bot/platforms/__init__.py bot/platforms/base.py bot/platforms/feishu_stream.py \
          bot/platforms/discord.py bot/platforms/dingtalk.py bot/platforms/dingtalk_stream.py; do
    download "$f"
done

# Agent system
for f in src/agent/__init__.py src/agent/conversation.py src/agent/executor.py \
          src/agent/factory.py src/agent/llm_adapter.py src/agent/memory.py \
          src/agent/orchestrator.py src/agent/protocols.py src/agent/runner.py \
          src/agent/agents/__init__.py src/agent/agents/base_agent.py \
          src/agent/agents/decision_agent.py src/agent/agents/intel_agent.py \
          src/agent/agents/portfolio_agent.py src/agent/agents/risk_agent.py \
          src/agent/agents/technical_agent.py \
          src/agent/skills/__init__.py src/agent/skills/base.py \
          src/agent/strategies/__init__.py src/agent/strategies/aggregator.py \
          src/agent/strategies/router.py src/agent/strategies/strategy_agent.py \
          src/agent/tools/__init__.py src/agent/tools/analysis_tools.py \
          src/agent/tools/backtest_tools.py src/agent/tools/data_tools.py \
          src/agent/tools/market_tools.py src/agent/tools/registry.py \
          src/agent/tools/search_tools.py; do
    download "$f"
done

# Utils
for f in src/utils/__init__.py src/utils/data_processing.py; do
    download "$f"
done

# Patch
for f in patch/__init__.py patch/eastmoney_patch.py; do
    download "$f"
done

# Strategies
for f in strategies/bottom_volume.yaml strategies/box_oscillation.yaml \
          strategies/bull_trend.yaml strategies/chan_theory.yaml \
          strategies/dragon_head.yaml strategies/emotion_cycle.yaml \
          strategies/ma_golden_cross.yaml strategies/one_yang_three_yin.yaml \
          strategies/shrink_pullback.yaml strategies/volume_breakout.yaml \
          strategies/wave_theory.yaml strategies/README.md; do
    download "$f"
done

# Workflows (just the daily_analysis one)
download ".github/workflows/daily_analysis.yml"

# Docker
download "docker/docker-compose.yml"

echo ""
echo "✅ All core files downloaded to $BASE"
