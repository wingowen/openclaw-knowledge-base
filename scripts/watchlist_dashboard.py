#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""候选票追踪系统 Web 看板 - 增强版

用法：
  python3 scripts/watchlist_dashboard.py

访问：http://localhost:5000
"""

from datetime import datetime, timedelta
from pathlib import Path

from flask import Flask, jsonify, request, render_template_string

import sqlite3

DB_PATH = Path("/root/.openclaw/workspace/data/watchlist_tracker.db")

app = Flask(__name__)


def conn_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# 新增：历史池视图（一周无信号自动归档）
# ---------------------------------------------------------------------------
@app.route("/history")
def history_pool():
    """显示历史池股票（连续超过指定天数未出现）"""
    days = request.args.get("days", 7, type=int)
    q = request.args.get("q", "").strip()  # 搜索关键词
    page = request.args.get("page", 1, type=int)
    per_page = 20

    conn = conn_db()
    cur = conn.cursor()

    # 获取最新日期
    cur.execute("SELECT MAX(report_date) as latest FROM watchlist_records")
    latest_row = cur.fetchone()
    if not latest_row or not latest_row['latest']:
        conn.close()
        return "<h1>暂无候选票数据</h1>"
    latest_date = datetime.strptime(latest_row['latest'], '%Y-%m-%d').date()

    # 获取所有活跃股票（未标记为'失效'的）及其最后出现日期
    # 支持搜索过滤
    if q:
        cur.execute("""
            SELECT code, name, sector, MAX(report_date) as last_date
            FROM watchlist_records
            WHERE status != '失效' AND (code LIKE ? OR name LIKE ?)
            GROUP BY code, name, sector
        """, (f"%{q}%", f"%{q}%"))
    else:
        cur.execute("""
            SELECT code, name, sector, MAX(report_date) as last_date
            FROM watchlist_records
            WHERE status != '失效'
            GROUP BY code, name, sector
        """)
    candidates = [dict(r) for r in cur.fetchall()]
    conn.close()

    # 筛选出超过阈值未出现的
    stale = []
    for cand in candidates:
        last_dt = datetime.strptime(cand['last_date'], '%Y-%m-%d').date()
        gap = (latest_date - last_dt).days
        if gap >= days:
            cand['gap_days'] = gap
            stale.append(cand)

    # 按最后出现日期倒序
    stale.sort(key=lambda x: x['last_date'], reverse=True)

    # 分页
    total = len(stale)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = stale[start:end]
    total_pages = (total + per_page - 1) // per_page

    return render_template_string(
        HISTORY_TEMPLATE,
        stale=page_items,
        days=days,
        latest_date=latest_date,
        total=total,
        page=page,
        total_pages=total_pages,
        q=q
    )



# ---------------------------------------------------------------------------
# 新增：提供深度分析数据（从 daily_stock_analysis 数据库读取）
# ---------------------------------------------------------------------------
@app.route("/api/stock-details")
def stock_details_api():
    """返回单个股票的深度分析历史（JSON格式，供前端聚合页使用）"""
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "missing code parameter"}), 400

    # daily_stock_analysis 的数据库路径
    SX|    db_path = Path("/root/.openclaw/workspace/data/stock_analysis.db")
    if not db_path.exists():
        return jsonify({"error": "daily_stock_analysis database not found"}), 404

    conn = sqlite3.connect(db_path)
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
        conn.close()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

    if not rows:
        return jsonify({"total": 0, "records": []})

    total = len(rows)
    buy_count = sum(1 for r in rows if r['operation_advice'] in ['买入', '加仓'])
    sell_count = sum(1 for r in rows if r['operation_advice'] in ['卖出', '减仓'])
    avg_sentiment = round(sum(r['sentiment_score'] or 0 for r in rows) / total, 1) if total else 0

    dates = []
    sentiment_scores = []
    ideal_buys = []
    secondary_buys = []
    stop_losses = []
    take_profits = []

    for r in rows:
        dates.append(r['created_at'][:10] if r['created_at'] else '-')
        sentiment_scores.append(r['sentiment_score'])
        ideal_buys.append(r['ideal_buy'])
        secondary_buys.append(r['secondary_buy'])
        stop_losses.append(r['stop_loss'])
        take_profits.append(r['take_profit'])

    return jsonify({
        "total": total,
        "buy_count": buy_count,
        "sell_count": sell_count,
        "avg_sentiment": avg_sentiment,
        "dates": dates,
        "sentiment_scores": sentiment_scores,
        "ideal_buys": ideal_buys,
        "secondary_buys": secondary_buys,
        "stop_losses": stop_losses,
        "take_profits": take_profits,
        "records": rows
    })


# ---------------------------------------------------------------------------
# 主页：当日三仓看板 + 昨日胜率
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    today = datetime.now().strftime("%Y-%m-%d")
    date = request.args.get("date", today)

    conn = conn_db()
    cur = conn.cursor()

    # 计算每只股票的最后出现日期（用于剩余天数）
    cur.execute("""
        SELECT code, MAX(report_date) as last_date
        FROM watchlist_records
        GROUP BY code
    """)
    last_date_map = {r['code']: r['last_date'] for r in cur.fetchall()}

    # 最新数据日期
    cur.execute("SELECT MAX(report_date) as latest FROM watchlist_records")
    latest_row = cur.fetchone()
    latest_date = datetime.strptime(latest_row['latest'], '%Y-%m-%d').date() if latest_row['latest'] else datetime.strptime(date, '%Y-%m-%d').date()

    # 获取当日数据
    buckets = ["进攻", "确认", "观察"]
    data = {}
    for b in buckets:
        cur.execute(
            """
            SELECT code, name, sector, chg_pct, status, note, target_range, ideal_buy, secondary_buy, stop_loss
            FROM watchlist_records
            WHERE report_date=? AND bucket=?
            ORDER BY chg_pct DESC
            """,
            (date, b),
        )
        rows = [dict(r) for r in cur.fetchall()]
        # 为每条记录计算剩余天数
        for r in rows:
            last_dt = datetime.strptime(last_date_map.get(r['code'], date), '%Y-%m-%d').date()
            gap = (latest_date - last_dt).days
            r['remaining_days'] = max(0, 7 - gap)  # 剩余天数（小于等于2表示即将归档）
        data[b] = rows


    # 获取昨日胜率（若有）
    yesterday_stats = None
    try:
        yesterday = (datetime.strptime(date, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        cur.execute(
            """
            SELECT status, COUNT(*) as cnt
            FROM watchlist_records
            WHERE report_date=?
            GROUP BY status
            """,
            (yesterday,),
        )
        status_counts = {r["status"]: r["cnt"] for r in cur.fetchall()}
        cur.execute("SELECT COUNT(*) as total FROM watchlist_records WHERE report_date=?", (yesterday,))
        total = cur.fetchone()["total"]
        settled = status_counts.get("已止盈", 0) + status_counts.get("已止损", 0) + status_counts.get("失效", 0)
        if settled > 0 and total >= 3:
            hit_rate = round(status_counts.get("已止盈", 0) / settled * 100, 1)
            profit_rate = round(status_counts.get("已止盈", 0) / total * 100, 1)
            loss_rate = round(status_counts.get("已止损", 0) / total * 100, 1)
            yesterday_stats = {
                "date": yesterday,
                "total": total,
                "settled": settled,
                "hit_rate": f"{hit_rate}%",
                "profit_rate": f"{profit_rate}%",
                "loss_rate": f"{loss_rate}%",
            }
    except Exception:
        yesterday_stats = None

    conn.close()
    return render_template_string(INDEX_TEMPLATE, date=date, data=data, today=today, yesterday_stats=yesterday_stats)


# ---------------------------------------------------------------------------
# 股票聚合分析页面
# ---------------------------------------------------------------------------
@app.route("/stock/<code>")
def stock_detail(code):
    """展示单只股票的历史追溯分析"""
    conn = conn_db()
    cur = conn.cursor()

    # 获取该股票所有历史记录
    cur.execute(
        """
        SELECT * FROM watchlist_records
        WHERE code = ?
        ORDER BY report_date DESC
        """,
        (code,),
    )
    records = [dict(r) for r in cur.fetchall()]

    if not records:
        conn.close()
        return f"<h1>未找到股票代码 {code} 的记录</h1><p><a href='/'>返回首页</a></p>"

    # 基本信息
    name = records[0]["name"]
    sector = records[0]["sector"]

    # 统计数据
    total_appearances = len(records)
    status_counts = {}
    bucket_counts = {}
    for r in records:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
        bucket_counts[r["bucket"]] = bucket_counts.get(r["bucket"], 0) + 1

    settled = status_counts.get("已止盈", 0) + status_counts.get("已止损", 0) + status_counts.get("失效", 0)
    hit_rate = round(status_counts.get("已止盈", 0) / settled * 100, 1) if settled > 0 else None
    profit_rate = round(status_counts.get("已止盈", 0) / total_appearances * 100, 1) if total_appearances > 0 else None

    # 同板块关联分析
    cur.execute(
        """
        SELECT code, name, COUNT(*) as appearances, MAX(report_date) as latest
        FROM watchlist_records
        WHERE sector = ? AND code != ?
        GROUP BY code, name
        ORDER BY appearances DESC, latest DESC
        LIMIT 5
        """,
        (sector, code),
    )
    related_stocks = [dict(r) for r in cur.fetchall()]

    # 准备图表数据（按日期序列）
    dates = []
    chg_pcts = []
    ideal_buys = []
    secondary_buys = []
    stop_losses = []
    status_sequence = []
    bucket_sequence = []

    for r in reversed(records):  # 时间正序
        dates.append(r["report_date"])
        chg_pcts.append(r["chg_pct"] if r["chg_pct"] is not None else None)
        ideal_buys.append(r["ideal_buy"] if r["ideal_buy"] is not None else None)
        secondary_buys.append(r["secondary_buy"] if r["secondary_buy"] is not None else None)
        stop_losses.append(r["stop_loss"] if r["stop_loss"] is not None else None)
        status_sequence.append(r["status"])
        bucket_sequence.append(r["bucket"])

    conn.close()

    return render_template_string(
        STOCK_DETAIL_TEMPLATE,
        code=code,
        name=name,
        sector=sector,
        records=records,
        total_appearances=total_appearances,
        status_counts=status_counts,
        bucket_counts=bucket_counts,
        hit_rate=hit_rate,
        profit_rate=profit_rate,
        related_stocks=related_stocks,
        dates=dates,
        chg_pcts=chg_pcts,
        ideal_buys=ideal_buys,
        secondary_buys=secondary_buys,
        stop_losses=stop_losses,
        status_sequence=status_sequence,
        bucket_sequence=bucket_sequence,
    )


# ---------------------------------------------------------------------------
# /records 接口
# ---------------------------------------------------------------------------
@app.route("/records")
def records():
    date = request.args.get("date")
    code = request.args.get("code")
    status = request.args.get("status")

    conn = conn_db()
    cur = conn.cursor()

    q = "SELECT * FROM watchlist_records WHERE 1=1"
    params = []
    if date:
        q += " AND report_date=?"
        params.append(date)
    if code:
        q += " AND code LIKE ?"
        params.append(f"%{code}%")
    if status:
        q += " AND status=?"
        params.append(status)

    q += " ORDER BY report_date DESC, CASE bucket WHEN '进攻' THEN 1 WHEN '确认' THEN 2 ELSE 3 END"
    cur.execute(q, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    return jsonify({"total": len(rows), "records": rows})


# ---------------------------------------------------------------------------
# /stats 接口
# ---------------------------------------------------------------------------
@app.route("/stats")
def stats():
    conn = conn_db()
    cur = conn.cursor()

    # 各状态计数
    cur.execute(
        """
        SELECT status, COUNT(*) as cnt
        FROM watchlist_records
        GROUP BY status
        """,
    )
    status_counts = {r["status"]: r["cnt"] for r in cur.fetchall()}

    # 总记录数
    cur.execute("SELECT COUNT(*) as total FROM watchlist_records")
    total = cur.fetchone()["total"]

    # 按仓分组统计
    cur.execute(
        """
        SELECT bucket, status, COUNT(*) as cnt
        FROM watchlist_records
        GROUP BY bucket, status
        """,
    )
    bucket_stats = {}
    for r in cur.fetchall():
        bucket_stats.setdefault(r["bucket"], {})[r["status"]] = r["cnt"]

    conn.close()

    # 计算比率（样本不足显示 N/A）
    def pct(part, whole):
        if whole < 3:
            return "N/A"
        return f"{round(part / whole * 100, 1)}%"

    settled = (
        status_counts.get("已止盈", 0)
        + status_counts.get("已止损", 0)
        + status_counts.get("失效", 0)
    )
    if total < 3:
        hit_rate = "N/A"
        profit_rate = "N/A"
        loss_rate = "N/A"
    else:
        hit_rate = (
            pct(status_counts.get("已止盈", 0), settled) if settled > 0 else "N/A"
        )
        profit_rate = pct(status_counts.get("已止盈", 0), total)
        loss_rate = pct(status_counts.get("已止损", 0), total)

    return jsonify(
        {
            "total": total,
            "settled": settled,
            "status_counts": status_counts,
            "bucket_stats": bucket_stats,
            "hit_rate": hit_rate,  # 命中率（止盈/已结算）
            "profit_rate": profit_rate,  # 止盈率
            "loss_rate": loss_rate,  # 止损率
        }
    )


# ---------------------------------------------------------------------------
# HTML 模板
# ---------------------------------------------------------------------------

INDEX_TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>候选票看板</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, sans-serif; background: #f5f5f5; color: #333; }
  .header { background: #2c3e50; color: #fff; padding: 16px 24px; display: flex; align-items: center; justify-content: space-between; }
  .header h1 { font-size: 18px; }
  .header .date-info { font-size: 14px; opacity: 0.8; }
  .container { max-width: 1200px; margin: 0 auto; padding: 16px; }
  .date-nav { margin-bottom: 16px; display: flex; gap: 8px; align-items: center; }
  .date-nav input { padding: 6px 12px; border: 1px solid #ccc; border-radius: 4px; }
  .date-nav button { padding: 6px 16px; background: #3498db; color: #fff; border: none; border-radius: 4px; cursor: pointer; }
  .stats-row { display: flex; gap: 16px; margin-bottom: 16px; }
  .stat-card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); flex: 1; }
  .stat-card h3 { font-size: 14px; margin-bottom: 8px; color: #666; }
  .stat-card .value { font-size: 24px; font-weight: 700; }
  .stat-card .desc { font-size: 12px; color: #999; margin-top: 4px; }
  .buckets { display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; }
  .bucket { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .bucket h2 { font-size: 16px; margin-bottom: 12px; padding-bottom: 8px; border-bottom: 2px solid #3498db; }
  .bucket.attack h2 { border-color: #e74c3c; }
  .bucket.confirm h2 { border-color: #f39c12; }
  .bucket.observe h2 { border-color: #27ae60; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { padding: 6px 8px; text-align: left; border-bottom: 1px solid #eee; }
  th { background: #f8f9fa; font-weight: 600; }
  .status { display: inline-block; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; }
  .status-待观察 { background: #e8f5e9; color: #2e7d32; }
  .status-已入场 { background: #e3f2fd; color: #1565c0; }
  .status-已止盈 { background: #fff3e0; color: #e65100; }
  .status-已止损 { background: #ffebee; color: #c62828; }
  .status-失效 { background: #f5f5f5; color: #757575; }
  .note { font-size: 11px; color: #888; margin-top: 2px; }
  .empty { text-align: center; padding: 24px; color: #999; }
  .api-links { margin-top: 24px; background: #fff; padding: 16px; border-radius: 8px; }
  .api-links h3 { font-size: 14px; margin-bottom: 8px; }
  .api-links pre { background: #2c3e50; color: #ecf0f1; padding: 12px; border-radius: 4px; font-size: 12px; overflow-x: auto; }
  .code-link { color: #3498db; text-decoration: none; }
  .code-link:hover { text-decoration: underline; }
</style>
</head>
<body>
<div class="header">
  <h1>📈 候选票追踪看板</h1>
  <div class="date-info">查看日期：<strong>{{ date }}</strong></div>
</div>
<div class="container">
  <form class="date-nav" onsubmit="location.href='/?date='+this.date.value;return false">
    <label>切换日期：</label>
    <input type="date" name="date" value="{{ date }}">
    <button type="submit">查看</button>
    <a href="/history" style="margin-left: 12px; padding: 6px 16px; background: #7f8c8d; color: white; text-decoration: none; border-radius: 4px; font-size: 14px;">📋 历史池</a>
  </form>

  {% if yesterday_stats %}
  <div class="stats-row">
    <div class="stat-card" style="border-left: 4px solid #3498db;">
      <h3>昨日总票数</h3>
      <div class="value">{{ yesterday_stats.total }}</div>
    </div>
    <div class="stat-card" style="border-left: 4px solid #27ae60;">
      <h3>昨日命中率</h3>
      <div class="value">{{ yesterday_stats.hit_rate }}</div>
      <div class="desc">止盈 / 已结算</div>
    </div>
    <div class="stat-card" style="border-left: 4px solid #e74c3c;">
      <h3>昨日止损率</h3>
      <div class="value">{{ yesterday_stats.loss_rate }}</div>
      <div class="desc">止损 / 总票数</div>
    </div>
  </div>
  {% endif %}

  <div class="buckets">
    {% for bucket, label in [('进攻', 'attack'), ('确认', 'confirm'), ('观察', 'observe')] %}
    <div class="bucket {{ label }}">
      <h2>{% if bucket == '进攻' %}🔥{% elif bucket == '确认' %}⚡{% else %}👁️{% endif %} {{ bucket }}仓</h2>
      {% if data[bucket] %}
      <table>
        <thead><tr><th>代码</th><th>名称</th><th>涨幅</th><th>状态</th><th>剩余</th><th>目标</th></tr></thead>
        <tbody>
        {% for r in data[bucket] %}
        <tr>
          <td><a href="/stock/{{ r.code }}" class="code-link">{{ r.code }}</a></td>
          <td>{{ r.name }}</td>
          <td>{% if r.chg_pct %}{{ r.chg_pct }}%{% else %}-{% endif %}</td>
          <td>
            <span class="status status-{{ r.status }}">{{ r.status }}</span>
            {% if r.note %}<div class="note">{{ r.note }}</div>{% endif %}
          </td>
          <td style="color: {% if r.remaining_days is defined and r.remaining_days <= 2 %}#e74c3c;{% endif %}; font-weight: {% if r.remaining_days is defined and r.remaining_days <= 2 %}bold;{% endif %}">
            {% if r.remaining_days is defined %}{{ r.remaining_days }}{% else %}-{% endif %}
          </td>
          <td>{{ r.target_range or '-' }}</td>
        </tr>
        {% endfor %}
        </tbody>
      </table>
      {% else %}
      <div class="empty">当日无记录</div>
      {% endif %}
    </div>
    {% endfor %}
  </div>

  <div class="api-links">
    <h3>📡 API 接口</h3>
    <pre>
# 查询记录（支持筛选）
GET /records?date=2026-03-20&code=600&status=已入场

# 统计数据
GET /stats
    </pre>
  </div>
</div>
</body>
</html>"""


STOCK_DETAIL_TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>{{ code }} {{ name }} - 股票聚合分析</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, sans-serif; background: #f5f5f5; color: #333; }
  .header { background: #2c3e50; color: #fff; padding: 16px 24px; display: flex; align-items: center; gap: 16px; }
  .header h1 { font-size: 20px; }
  .header .meta { font-size: 14px; opacity: 0.8; }
  .container { max-width: 1200px; margin: 0 auto; padding: 16px; }
  .summary-cards { display: flex; gap: 16px; margin-bottom: 16px; flex-wrap: wrap; }
  .card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); min-width: 160px; }
  .card h3 { font-size: 13px; color: #666; margin-bottom: 8px; }
  .card .value { font-size: 24px; font-weight: 700; }
  .card .desc { font-size: 12px; color: #999; margin-top: 4px; }
  .section { background: #fff; border-radius: 8px; padding: 16px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  .section h2 { font-size: 16px; margin-bottom: 12px; color: #333; border-bottom: 2px solid #3498db; padding-bottom: 8px; }
  table { width: 100%; border-collapse: collapse; font-size: 13px; }
  th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }
  th { background: #f8f9fa; font-weight: 600; }
  .status { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }
  .status-待观察 { background: #e8f5e9; color: #2e7d32; }
  .status-已入场 { background: #e3f2fd; color: #1565c0; }
  .status-已止盈 { background: #fff3e0; color: #e65100; }
  .status-已止损 { background: #ffebee; color: #c62828; }
  .status-失效 { background: #f5f5f5; color: #757575; }
  /* 深度分析状态样式 */
  .status-buy { background: #e8f5e9; color: #2e7d32; }
  .status-sell { background: #ffebee; color: #c62828; }
  .status-hold { background: #fff3e0; color: #ef6c00; }
  .chart-container { height: 300px; margin-top: 12px; }
  .back-link { display: inline-block; margin-bottom: 12px; color: #3498db; text-decoration: none; }
  .back-link:hover { text-decoration: underline; }
  .related-table { width: 100%; }
</style>
</head>
<body>
<div class="header">
  <a href="/" class="back-link">← 返回看板</a>
  <div>
    <h1>{{ code }} {{ name }}</h1>
    <div class="meta">板块：{{ sector }} | 出现次数：{{ total_appearances }}次</div>
  </div>
</div>
<div class="container">

  <div class="summary-cards">
    <div class="card" style="border-left: 4px solid #3498db;">
      <h3>总出现次数</h3>
      <div class="value">{{ total_appearances }}</div>
    </div>
    <div class="card" style="border-left: 4px solid #27ae60;">
      <h3>止盈次数</h3>
      <div class="value">{{ status_counts.get('已止盈', 0) }}</div>
    </div>
    <div class="card" style="border-left: 4px solid #e74c3c;">
      <h3>止损次数</h3>
      <div class="value">{{ status_counts.get('已止损', 0) }}</div>
    </div>
    {% if hit_rate is not none %}
    <div class="card" style="border-left: 4px solid #f39c12;">
      <h3>命中率</h3>
      <div class="value">{{ hit_rate }}%</div>
      <div class="desc">止盈/已结算</div>
    </div>
    {% endif %}
  </div>

  <div class="section">
    <h2>📊 技术指标趋势</h2>
    <div class="chart-container">
      <canvas id="techChart"></canvas>
    </div>
  </div>

  <div class="section">
    <h2>📋 历史记录明细</h2>
    <table>
      <thead><tr><th>日期</th><th>仓位</th><th>涨幅</th><th>状态</th><th>理想买点</th><th>次优买点</th><th>止损位</th><th>目标位</th></tr></thead>
      <tbody>
      {% for r in records %}
      <tr>
        <td>{{ r.report_date }}</td>
        <td>{{ r.bucket }}仓</td>
        <td>{{ r.chg_pct if r.chg_pct is not none else '-' }}%</td>
        <td><span class="status status-{{ r.status }}">{{ r.status }}</span></td>
        <td>{{ r.ideal_buy if r.ideal_buy is not none else '-' }}</td>
        <td>{{ r.secondary_buy if r.secondary_buy is not none else '-' }}</td>
        <td>{{ r.stop_loss if r.stop_loss is not none else '-' }}</td>
        <td>{{ r.target_range or '-' }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>

  {% if related_stocks %}
  <div class="section">
    <h2>🔗 同板块关联股票</h2>
    <table class="related-table">
      <thead><tr><th>代码</th><th>名称</th><th>出现次数</th><th>最近日期</th></tr></thead>
      <tbody>
      {% for s in related_stocks %}
      <tr>
        <td><a href="/stock/{{ s.code }}" class="code-link">{{ s.code }}</a></td>
        <td>{{ s.name }}</td>
        <td>{{ s.appearances }}</td>
        <td>{{ s.latest }}</td>
      </tr>
      {% endfor %}
      </tbody>
    </table>
  </div>
  {% endif %}

  <!-- 深度分析模块：从 daily_stock_analysis 同步数据 -->
  <div class="section" id="deep-analysis-section">
    <h2>🤖 AI 深度分析历史 <span style="font-size:12px; color:#999; font-weight:normal;">（数据来源：每日股票决策系统）</span></h2>
    <div id="deep-analysis-loading" style="text-align:center; padding:20px; color:#666;">
      正在加载分析数据...
    </div>
    <div id="deep-analysis-content" style="display:none;">
      <!-- 统计卡片 -->
      <div class="summary-cards" style="margin-bottom:16px;">
        <div class="card" style="border-left:4px solid #1a237e;">
          <h3>分析次数</h3>
          <div class="value" id="da-total">-</div>
        </div>
        <div class="card" style="border-left:4px solid #2e7d32;">
          <h3>买入/加仓</h3>
          <div class="value" id="da-buy">-</div>
        </div>
        <div class="card" style="border-left:4px solid #c62828;">
          <h3>卖出/减仓</h3>
          <div class="value" id="da-sell">-</div>
        </div>
        <div class="card" style="border-left:4px solid #ef6c00;">
          <h3>平均情绪分</h3>
          <div class="value" id="da-sentiment">-</div>
        </div>
      </div>

      <!-- 图表 -->
      <div class="chart-container" style="height:300px; margin-bottom:16px;">
        <canvas id="daChart"></canvas>
      </div>

      <!-- 明细表格 -->
      <div style="overflow-x:auto;">
        <table>
          <thead><tr><th>日期</th><th>操作建议</th><th>情绪分</th><th>理想买点</th><th>次优买点</th><th>止损位</th><th>目标位</th></tr></thead>
          <tbody id="da-table-body">
          </tbody>
        </table>
      </div>
    </div>
    <div id="deep-analysis-empty" class="empty" style="display:none;">
      暂无深度分析记录
    </div>
  </div>

</div>
<script>
  // 现有技术图标的渲染代码保持不变...

  // 新增：从 daily_stock_analysis 拉取深度分析数据
  (function() {
    const code = '{{ code }}';
    fetch('/api/stock-details?code=' + code)
      .then(r => r.json())
      .then(data => {
        document.getElementById('deep-analysis-loading').style.display = 'none';
        if (!data.records || data.records.length === 0) {
          document.getElementById('deep-analysis-empty').style.display = 'block';
          return;
        }
        const content = document.getElementById('deep-analysis-content');
        content.style.display = 'block';

        // 填充统计卡片
        document.getElementById('da-total').textContent = data.total;
        document.getElementById('da-buy').textContent = data.buy_count;
        document.getElementById('da-sell').textContent = data.sell_count;
        document.getElementById('da-sentiment').textContent = data.avg_sentiment || '-';

        // 填充表格
        const tbody = document.getElementById('da-table-body');
        data.records.forEach(r => {
          const tr = document.createElement('tr');
          tr.innerHTML = `
            <td>${r.created_at ? r.created_at.substring(0,10) : '-'}</td>
            <td><span class="status status-${r.operation_advice === '买入' || r.operation_advice === '加仓' ? 'buy' : r.operation_advice === '卖出' || r.operation_advice === '减仓' ? 'sell' : 'hold'}">${r.operation_advice || '-'}</span></td>
            <td>${r.sentiment_score || '-'}</td>
            <td>${r.ideal_buy || '-'}</td>
            <td>${r.secondary_buy || '-'}</td>
            <td>${r.stop_loss || '-'}</td>
            <td>${r.take_profit || '-'}</td>
          `;
          tbody.appendChild(tr);
        });

        // 渲染 Chart.js 图表
        const ctx = document.getElementById('daChart').getContext('2d');
        if (window.daChart) window.daChart.destroy();
        window.daChart = new Chart(ctx, {
          type: 'line',
          data: {
            labels: data.dates,
            datasets: [
              {
                label: '情绪分',
                data: data.sentiment_scores,
                borderColor: '#1a237e',
                backgroundColor: 'rgba(26,35,126,0.1)',
                fill: true,
                tension: 0.3,
                yAxisID: 'y'
              },
              {
                label: '理想买点',
                data: data.ideal_buys,
                borderColor: '#27ae60',
                borderDash: [5,5],
                fill: false,
                pointRadius: 3,
                yAxisID: 'y1'
              },
              {
                label: '次优买点',
                data: data.secondary_buys,
                borderColor: '#f39c12',
                borderDash: [5,5],
                fill: false,
                pointRadius: 3,
                yAxisID: 'y1'
              },
              {
                label: '止损位',
                data: data.stop_losses,
                borderColor: '#c62828',
                borderDash: [5,5],
                fill: false,
                pointRadius: 3,
                yAxisID: 'y1'
              }
            ]
          },
          options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            scales: {
              y: { type: 'linear', display: true, position: 'left', title: { display: true, text: '情绪分 (0-100)' } },
              y1: { type: 'linear', display: true, position: 'right', title: { display: true, text: '价格 (元)' }, grid: { drawOnChartArea: false } }
            }
          }
        });
      })
      .catch(err => {
        console.error('Failed to fetch deep analysis:', err);
        document.getElementById('deep-analysis-loading').textContent = '加载失败：' + err.message;
      });
  })();
</script>
</body>
</html>"""


HISTORY_TEMPLATE = """<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="utf-8">
<title>历史候选池 - 股票聚合分析</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: -apple-system, sans-serif; background: #f5f5f5; color: #333; }
  .header { background: #2c3e50; color: #fff; padding: 16px 24px; display: flex; align-items: center; gap: 16px; }
  .header h1 { font-size: 20px; }
  .header .meta { font-size: 14px; opacity: 0.8; }
  .container { max-width: 1200px; margin: 0 auto; padding: 16px; }
  .back-link { display: inline-block; margin-bottom: 12px; color: #fff; text-decoration: none; }
  .back-link:hover { text-decoration: underline; }
  .card { background: #fff; border-radius: 8px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin-bottom: 16px; }
  .stat-row { display: flex; gap: 16px; margin-bottom: 16px; }
  .stat { flex: 1; text-align: center; padding: 12px; background: #f8f9fa; border-radius: 6px; }
  .stat-value { font-size: 24px; font-weight: bold; color: #1a237e; }
  .stat-label { font-size: 13px; color: #666; margin-top: 4px; }
  table { width: 100%; border-collapse: collapse; background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
  th, td { padding: 12px 16px; text-align: left; }
  th { background: #f8f9fa; font-weight: 600; color: #666; font-size: 13px; }
  tr:hover { background: #fafafa; }
  .empty { text-align: center; padding: 40px; color: #999; }
  .badge { padding: 4px 12px; border-radius: 12px; font-size: 11px; font-weight: 600; background: #e8f5e9; color: #2e7d32; text-decoration: none; }
  .gap-days { font-weight: 600; }
</style>
</head>
<body>
<div class="header">
  <a href="/" class="back-link">← 返回看板</a>
  <div>
    <h1>📋 历史候选池</h1>
    <div class="meta">超过 {{ days }} 天未出现信号的股票</div>
  </div>
</div>
<div class="container">

  <div class="card">
    <div class="stat-row">
      <div class="stat">
        <div class="stat-value">{{ total }}</div>
        <div class="stat-label">历史股票总数</div>
      </div>
      <div class="stat">
        <div class="stat-value">{{ days }}</div>
        <div class="stat-label">阈值（天）</div>
      </div>
      <div class="stat">
        <div class="stat-value">{{ latest_date }}</div>
        <div class="stat-label">最新数据日期</div>
      </div>
    </div>
    <div class="stat-row" style="margin-top: 12px; border-top: 1px solid #eee; padding-top: 12px;">
      <div class="stat">
        <div class="stat-value">{{ stats.avg_gap|default(0) }}</div>
        <div class="stat-label">平均闲置天数</div>
      </div>
      <div class="stat">
        <div class="stat-value">{{ stats.max_gap|default(0) }}</div>
        <div class="stat-label">最长闲置(天)</div>
      </div>
      <div class="stat">
        <div class="stat-value">{{ stats.min_gap|default(0) }}</div>
        <div class="stat-label">最短闲置(天)</div>
      </div>
    </div>
    {% if stats.sector_counts %}
    <div style="margin-top: 12px; border-top: 1px solid #eee; padding-top: 12px;">
      <div style="font-size: 13px; color: #666; margin-bottom: 8px;">板块分布：</div>
      <div style="display: flex; flex-wrap: wrap; gap: 8px;">
        {% for sector, count in stats.sector_counts.items() %}
        <span style="padding: 4px 12px; background: #e8f5e9; border-radius: 12px; font-size: 12px; color: #2e7d32;">
          {{ sector }} ({{ count }})
        </span>
        {% endfor %}
      </div>
    </div>
    {% endif %}
  </div>

  <!-- 搜索框 -->
  <div class="card" style="padding: 12px 16px; margin-bottom: 16px;">
    <form method="get" action="/history" style="display: flex; gap: 8px; align-items: center;">
      <input type="text" name="q" placeholder="搜索代码或名称..." value="{{ q or '' }}"
             style="flex: 1; padding: 6px 12px; border: 1px solid #ddd; border-radius: 4px;">
      <input type="hidden" name="days" value="{{ days }}">
      <button type="submit" style="padding: 6px 16px; background: #3498db; color: #fff; border: none; border-radius: 4px; cursor: pointer;">搜索</button>
      {% if q %}
      <a href="/history?days={{ days }}" style="padding: 6px 16px; background: #95a5a6; color: #fff; text-decoration: none; border-radius: 4px;">清除</a>
      {% endif %}
    </form>
  </div>

  {% if stale %}
  <table>
    <thead><tr><th>代码</th><th>名称</th><th>板块</th><th>最后出现</th><th>间隔天数</th></tr></thead>
    <tbody>
    {% for s in stale %}
    <tr>
      <td><a href="/stock/{{ s.code }}" class="badge">{{ s.code }}</a></td>
      <td>{{ s.name }}</td>
      <td>{{ s.sector }}</td>
      <td>{{ s.last_date }}</td>
      <td>
      <span class="gap-days" style="color: {% if s.gap_days >= days-2 %}#e74c3c; font-weight: 800;{% else %}#666;{% endif %}">
        {{ s.gap_days }} 天
      </span>
      {% if s.gap_days >= days-2 %}<span style="font-size:11px; color:#e74c3c; margin-left:4px;">⚠️ 即将归档</span>{% endif %}
    </td>
    </tr>
    {% endfor %}
    </tbody>
  </table>

  <!-- 分页 -->
  {% if total_pages > 1 %}
  <div class="card" style="margin-top: 16px; text-align: center;">
    <div class="pagination" style="display: flex; justify-content: center; gap: 8px; align-items: center;">
      {% if page > 1 %}
        <a href="/history?page={{ page-1 }}&days={{ days }}{% if q %}&q={{ q }}{% endif %}" style="padding: 6px 12px; background: #ecf0f1; border-radius: 4px; text-decoration: none; color: #333;">上一页</a>
      {% endif %}

      <span style="font-size: 14px; color: #666;">
        第 {{ page }} / {{ total_pages }} 页（共 {{ total }} 条）
      </span>

      {% if page < total_pages %}
        <a href="/history?page={{ page+1 }}&days={{ days }}{% if q %}&q={{ q }}{% endif %}" style="padding: 6px 12px; background: #ecf0f1; border-radius: 4px; text-decoration: none; color: #333;">下一页</a>
      {% endif %}
    </div>
  </div>
  {% endif %}

  {% else %}
  <div class="empty">暂无符合条件的股票（所有候选票都在阈值内）</div>
  {% endif %}

</div>
</body>
</html>"""


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
