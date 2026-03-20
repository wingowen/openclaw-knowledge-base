#!/usr/bin/env python3
"""为 INDEX_TEMPLATE 添加剩余天数列"""

from pathlib import Path

file_path = Path("/root/.openclaw/workspace/scripts/watchlist_dashboard.py")
content = file_path.read_text(encoding="utf-8")

# 替换表头：在"状态"后添加"剩余"列
old_thead = '        <thead><tr><th>代码</th><th>名称</th><th>涨幅</th><th>状态</th><th>目标</th></tr></thead>'
new_thead = '        <thead><tr><th>代码</th><th>名称</th><th>涨幅</th><th>状态</th><th>剩余</th><th>目标</th></tr></thead>'

content = content.replace(old_thead, new_thead)

# 替换表格体：在 status 的 <td> 后面插入剩余天数的 <td>
old_td_block = '''          <td>
            <span class="status status-{{ r.status }}">{{ r.status }}</span>
            {% if r.note %}<div class="note">{{ r.note }}</div>{% endif %}
          </td>'''

new_td_block = '''          <td>
            <span class="status status-{{ r.status }}">{{ r.status }}</span>
            {% if r.note %}<div class="note">{{ r.note }}</div>{% endif %}
          </td>
          <td style="color: {% if r.remaining_days is defined and r.remaining_days <= 2 %}#e74c3c;{% endif %}; font-weight: {% if r.remaining_days is defined and r.remaining_days <= 2 %}bold;{% endif %}">
            {% if r.remaining_days is defined %}{{ r.remaining_days }}{% else %}-{% endif %}
          </td>'''

content = content.replace(old_td_block, new_td_block)

file_path.write_text(content, encoding="utf-8")
print("✅ 优化 #2 完成：候选票主页表格已添加剩余天数列，≤2 天显示红色高亮")
