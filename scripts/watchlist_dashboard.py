#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""候选票追踪系统 Web 看板

用法：
  python3 scripts/watchlist_dashboard.py

访问：http://localhost:5000
"""

from datetime import datetime
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
# 主页：当日三仓看板 + 昨日胜率
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    today = datetime.now().strftime("%Y-%m-%d")
    date = request.args.get("date", today)

    conn = conn_db()
    cur = conn.cursor()

    # 获取当日数据
    buckets = ["进攻", "确认", "观察"]
    data = {}
    for b in buckets:
        cur.execute(
            """
            SELECT code, name, sector, chg_pct, status, note, target_range
            FROM watchlist_records
            WHERE report_date=? AND bucket=?
            ORDER BY chg_pct DESC
            """,
            (date, b),
        )
        data[b] = [dict(r) for r in cur.fetchall()]

    # 获取昨日胜率（若有）
    yesterday_stats = None
    try:
        from datetime import timedelta
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
    return render_template_string(TEMPLATE, date=date, data=data, today=today, yesterday_stats=yesterday_stats)


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
# HTML 模板（单文件内嵌）
# ---------------------------------------------------------------------------

TEMPLATE = """<!DOCTYPE html>
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
  .date-nav button { padding: 6px 16px; background: #3498db; color: #fff; border: none; border-radius: 4px; cursor: button; }
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
        <thead><tr><th>代码</th><th>名称</th><th>涨幅</th><th>状态</th><th>目标</th></tr></thead>
        <tbody>
        {% for r in data[bucket] %}
        <tr>
          <td>{{ r.code }}</td>
          <td>{{ r.name }}</td>
          <td>{% if r.chg_pct %}{{ r.chg_pct }}%{% else %}-{% endif %}</td>
          <td>
            <span class="status status-{{ r.status }}">{{ r.status }}</span>
            {% if r.note %}<div class="note">{{ r.note }}</div>{% endif %}
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


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)