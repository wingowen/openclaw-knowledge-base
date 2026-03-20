#!/usr/bin/env python3
"""优化 #4：历史池页面增加统计信息"""

from pathlib import Path
from datetime import datetime

file_path = Path("/root/.openclaw/workspace/scripts/watchlist_dashboard.py")
content = file_path.read_text(encoding="utf-8")

# 1. 修改 history_pool 函数，计算统计数据
# 找到 "return render_template_string(HISTORY_TEMPLATE, stale=page_items, days=days, latest_date=latest_date)" 这一行
old_return = '    return render_template_string(\n        HISTORY_TEMPLATE,\n        stale=page_items,\n        days=days,\n        latest_date=latest_date\n    )'

new_return = '''    # 计算统计信息
    stats = {}
    if stale:
        gap_days_list = [c['gap_days'] for c in stale]
        stats['avg_gap'] = round(sum(gap_days_list) / len(gap_days_list), 1)
        stats['max_gap'] = max(gap_days_list)
        stats['min_gap'] = min(gap_days_list)
        # 板块分布
        sector_counts = {}
        for c in stale:
            sector = c.get('sector', '未知')
            sector_counts[sector] = sector_counts.get(sector, 0) + 1
        stats['sector_counts'] = sector_counts
    else:
        stats = {'avg_gap': 0, 'max_gap': 0, 'min_gap': 0, 'sector_counts': {}}

    return render_template_string(
        HISTORY_TEMPLATE,
        stale=page_items,
        days=days,
        latest_date=latest_date,
        total=total,
        page=page,
        total_pages=total_pages,
        q=q,
        stats=stats
    )'''

content = content.replace(old_return, new_return)

# 2. 修改 HISTORY_TEMPLATE，在顶部添加统计卡片
# 找到统计卡片的开始部分
old_stats_block = '''  <div class="card">
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
  </div>'''

new_stats_block = '''  <div class="card">
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
  </div>'''

content = content.replace(old_stats_block, new_stats_block)

file_path.write_text(content, encoding="utf-8")
print("✅ 优化 #4 完成：历史池页面已添加统计信息（平均/最大/最小闲置天数 + 板块分布）")
