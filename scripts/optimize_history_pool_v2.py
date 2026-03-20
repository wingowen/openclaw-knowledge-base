#!/usr/bin/env python3
"""优化历史池：添加搜索和分页功能（简化版）"""

from pathlib import Path

file_path = Path("/root/.openclaw/workspace/scripts/watchlist_dashboard.py")
lines = file_path.read_text(encoding="utf-8").splitlines(keepends=True)

# 找到 history_pool 函数的起始和结束行
start_idx = None
end_idx = None
for i, line in enumerate(lines):
    if '@app.route("/history")' in line:
        start_idx = i
    if start_idx is not None and line.strip() == 'return render_template_string(HISTORY_TEMPLATE, stale=stale, days=days, latest_date=latest_date)':
        end_idx = i
        break

if start_idx is None or end_idx is None:
    print("❌ 未找到 history_pool 函数")
    exit(1)

print(f"✅ 找到函数：行 {start_idx+1} - {end_idx+1}")

# 新函数内容
new_func = '''@app.route("/history")
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

'''

# 替换函数
new_lines = lines[:start_idx] + [new_func] + lines[end_idx+1:]
content = ''.join(new_lines)

# 更新 HISTORY_TEMPLATE 模板（添加搜索和分页）
old_template = '''<div class="header">
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
        <div class="stat-value">{{ stale|length }}</div>
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
      <td><span class="gap-days">{{ s.gap_days }} 天</span></td>
    </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
  <div class="empty">暂无符合条件的股票（所有候选票都在阈值内）</div>
  {% endif %}

</div>'''

new_template = '''<div class="header">
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
      <td><span class="gap-days">{{ s.gap_days }} 天</span></td>
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

</div>'''

content = content.replace(old_template, new_template)

file_path.write_text(content, encoding="utf-8")
print("✅ 历史池优化完成：搜索 + 分页")