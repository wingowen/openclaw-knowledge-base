# daily_stock_analysis 服务骨架

## 启动

```bash
cd /root/.openclaw/workspace/daily_stock_analysis
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

访问：
- 首页：http://127.0.0.1:8000/
- 健康检查：http://127.0.0.1:8000/health
- API 文档：http://127.0.0.1:8000/docs
- 看板聚合：http://127.0.0.1:8000/dashboard

## 说明

- 本骨架**只读**使用现有数据：
  - `/root/.openclaw/workspace/data/watchlist_tracker.db`
  - `/root/.openclaw/workspace/data/stock_analysis.db`
  - `/root/.openclaw/workspace/reports/`
- 不会删除、覆盖任何历史数据。
- 数据清理操作后续统一走“双确认”流程。
