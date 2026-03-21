from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import sqlite3
from typing import Any

BASE = Path('/root/.openclaw/workspace')
WATCHLIST_DB = BASE / 'data' / 'watchlist_tracker.db'
STOCK_DB = BASE / 'data' / 'stock_analysis.db'
REPORTS_DIR = BASE / 'reports'

templates = Jinja2Templates(directory=str(Path(__file__).parent / 'templates'))

app = FastAPI(title='daily_stock_analysis skeleton', version='0.1.0')


def _query(db_path: Path, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql, params)
        return [dict(r) for r in cur.fetchall()]
    finally:
        conn.close()


@app.get('/health')
def health():
    return {
        'ok': True,
        'watchlist_db_exists': WATCHLIST_DB.exists(),
        'stock_db_exists': STOCK_DB.exists(),
        'reports_dir_exists': REPORTS_DIR.exists(),
    }


@app.get('/')
def index():
    return {
        'service': 'daily_stock_analysis skeleton',
        'endpoints': ['/health', '/dashboard', '/reports/latest'],
    }


@app.get('/api/stats')
def api_stats():
    """JSON: 统计信息（用于图表）"""
    latest = _query(
        WATCHLIST_DB,
        """
        SELECT bucket, COUNT(*) as cnt
        FROM watchlist_records
        WHERE report_date = (SELECT MAX(report_date) FROM watchlist_records)
        GROUP BY bucket
        """,
    )
    sentiment = _query(
        STOCK_DB,
        """
        SELECT sentiment_score FROM analysis_history
        WHERE sentiment_score IS NOT NULL
        """
    )
    scores = [r['sentiment_score'] for r in sentiment if r['sentiment_score'] is not None]
    avg_sentiment = round(sum(scores) / len(scores), 1) if scores else 0
    # 情绪分分布 (0-10，每1分为一档)
    dist = [0]*11
    for s in scores:
        idx = int(min(max(s, 0), 10))
        dist[idx] += 1
    return {
        'watchlist_by_bucket': {r['bucket']: r['cnt'] for r in latest},
        'analysis_count': len(scores),
        'avg_sentiment': avg_sentiment,
        'sentiment_distribution': dist,
    }


@app.get('/ui', response_class=HTMLResponse)
async def dashboard_ui(request: Request):
    """可视化看板页面"""
    return templates.TemplateResponse('dashboard.html', {'request': request})


@app.get('/api/dashboard')
def api_dashboard():
    """JSON: 最新候选池 + 报表统计"""
    latest = _query(
        WATCHLIST_DB,
        """
        SELECT report_date, bucket, code, name, sector, chg_pct, status
        FROM watchlist_records
        WHERE report_date = (SELECT MAX(report_date) FROM watchlist_records)
        ORDER BY bucket, chg_pct DESC
        """,
    )
    tables = _query(
        STOCK_DB,
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    return {
        'latest_watchlist_count': len(latest),
        'latest_watchlist': latest[:200],
        'stock_db_tables': [t['name'] for t in tables],
    }


@app.get('/api/stock-details')
def api_stock_details(code: str):
    """JSON: 单股票深度分析历史"""
    if not code or not STOCK_DB.exists():
        return {'error': 'not found'}
    conn = sqlite3.connect(STOCK_DB)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    try:
        cur.execute("""
            SELECT id, code, name, operation_advice, sentiment_score,
                   ideal_buy, secondary_buy, stop_loss, take_profit,
                   created_at
            FROM analysis_history
            WHERE code = ?
            ORDER BY created_at ASC
        """, (code,))
        rows = [dict(r) for r in cur.fetchall()]
    except Exception as e:
        return {'error': str(e)}
    finally:
        conn.close()
    if not rows:
        return {'total': 0, 'records': []}
    total = len(rows)
    buy_count = sum(1 for r in rows if r['operation_advice'] in ['买入', '加仓'])
    sell_count = sum(1 for r in rows if r['operation_advice'] in ['卖出', '减仓'])
    avg_sentiment = round(
        sum(r['sentiment_score'] or 0 for r in rows) / total, 1
    ) if total else 0
    records = []
    for r in rows:
        records.append({
            'created_at': r['created_at'],
            'operation_advice': r['operation_advice'],
            'sentiment_score': r['sentiment_score'],
            'ideal_buy': r['ideal_buy'],
            'secondary_buy': r['secondary_buy'],
            'stop_loss': r['stop_loss'],
            'take_profit': r['take_profit'],
        })
    return {
        'total': total,
        'buy_count': buy_count,
        'sell_count': sell_count,
        'avg_sentiment': avg_sentiment,
        'records': records,
    }
