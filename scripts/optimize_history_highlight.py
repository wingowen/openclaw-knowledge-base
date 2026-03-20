#!/usr/bin/env python3
"""优化 #2：历史池高亮即将归档的股票"""

from pathlib import Path

file_path = Path("/root/.openclaw/workspace/scripts/watchlist_dashboard.py")
content = file_path.read_text(encoding="utf-8")

# 查找并替换 HISTORY_TEMPLATE 中的 gap-days 样式部分
old_td = '''<td><span class="gap-days">{{ s.gap_days }} 天</span></td>'''

new_td = '''<td>
      <span class="gap-days" style="color: {% if s.gap_days >= days-2 %}#e74c3c; font-weight: 800;{% else %}#666;{% endif %}">
        {{ s.gap_days }} 天
      </span>
      {% if s.gap_days >= days-2 %}<span style="font-size:11px; color:#e74c3c; margin-left:4px;">⚠️ 即将归档</span>{% endif %}
    </td>'''

content = content.replace(old_td, new_td)

# 在 HISTORY_TEMPLATE 的 table 样式中增加 gap-days 的基础颜色
old_style = '.gap-days { color: #e74c3c; font-weight: 600; }'
new_style = '.gap-days { font-weight: 600; }'

content = content.replace(old_style, new_style)

file_path.write_text(content, encoding="utf-8")
print("✅ 历史池高亮优化完成：即将归档的股票会显示 ⚠️ 标记")
