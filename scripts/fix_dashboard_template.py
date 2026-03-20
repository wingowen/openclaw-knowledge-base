#!/usr/bin/env python3
"""
修复 daily_stock_analysis API 的 dashboard 函数

将 _generate_dashboard_html 重写为独立实现，不依赖 _DASHBOARD_TEMPLATE
"""

from pathlib import Path
import re

file_path = Path('/root/.openclaw/workspace/daily_stock_analysis/api/app.py')
text = file_path.read_text()

# 删除旧的 _generate_dashboard_html 函数（错误的版本）
pattern_old_func = r'def _generate_dashboard_html\(records: List\[Dict\]\) -> str:.*?return _DASHBOARD_TEMPLATE\.format\([^)]+\)'
text = re.sub(pattern_old_func, '', text, flags=re.DOTALL)

# 插入新的 _generate_dashboard_html 函数（完整的 HTML 生成）
new_func = '''
def _generate_dashboard_html(records: List[Dict]) -> str:
    """生成仪表盘 HTML"""
    total = len(records)
    buy_count = sum(1 for r in records if r['operation_advice'] in ['买入', '加仓'])
    sell_count = sum(1 for r in records if r['operation_advice'] in ['卖出', '减仓'])
    hold_count = sum(1 for r in records if r['operation_advice'] in ['持有'])
    
    # 生成表格行
    rows_html = ""
    for r in records:
        op = r['operation_advice']
        if op in ['买入', '加仓']:
            badge = '<span class="badge badge-buy">买入</span>'
        elif op in ['卖出', '减仓']:
            badge = '<span class="badge badge-sell">卖出</span>'
        else:
            badge = '<span class="badge badge-hold">持有</span>'
        
        sentiment = r['sentiment_score'] or '-'
        created = r['created_at'][:10] if r['created_at'] else '-'
        summary = (r['analysis_summary'] or '-')
        if summary and len(summary) > 80:
            summary = summary[:80] + '...'
        
        rows_html += f'''
        <tr>
            <td>{r['code']}</td>
            <td>{r['name']}</td>
            <td>{badge}</td>
            <td>{sentiment}</td>
            <td>{created}</td>
            <td>{summary}</td>
        </tr>
        '''
    
    html = f'''
    <!DOCTYPE html>
    <html lang="zh">
    <head>
        <meta charset="utf-8">
        <title>每日股票分析 - 仪表盘</title>
        <style>
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ font-family: -apple-system, sans-serif; background: #f5f5f5; color: #333; }}
            .header {{ background: #2c3e50; color: #fff; padding: 16px 24px; }}
            .header h1 {{ font-size: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 20px; }}
            .stats {{ display: flex; gap: 16px; margin-bottom: 20px; }}
            .stat-card {{ background: white; padding: 16px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); flex: 1; text-align: center; }}
            .stat-value {{ font-size: 24px; font-weight: bold; color: #2c3e50; }}
            .stat-label {{ font-size: 12px; color: #666; margin-top: 4px; }}
            table {{ width: 100%; background: white; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border-collapse: collapse; }}
            th, td {{ padding: 12px 16px; text-align: left; border-bottom: 1px solid #f0f0f0; }}
            th {{ background: #f8f9fa; font-weight: 600; color: #666; font-size: 13px; }}
            td {{ font-size: 14px; }}
            .badge {{ padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }}
            .badge-buy {{ background: #e8f5e9; color: #2e7d32; }}
            .badge-sell {{ background: #ffebee; color: #c62828; }}
            .badge-hold {{ background: #fff3e0; color: #ef6c00; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <h1>每日股票分析 · 仪表盘</h1>
            </div>
        </div>
        <div class="container">
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">{total}</div>
                    <div class="stat-label">总记录数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color:#2e7d32;">{buy_count}</div>
                    <div class="stat-label">买入/加仓</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color:#c62828;">{sell_count}</div>
                    <div class="stat-label">卖出/减仓</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color:#ef6c00;">{hold_count}</div>
                    <div class="stat-label">持有</div>
                </div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>代码</th>
                        <th>名称</th>
                        <th>操作</th>
                        <th>情绪分</th>
                        <th>分析时间</th>
                        <th>摘要</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
    </body>
    </html>
    '''
    return html
'''

text = text.replace(
    'def _generate_dashboard_html(records: List[Dict]) -> str:\n    """生成仪表盘 HTML（原逻辑保持不变）"""\n    # 这里保留原有的 dashboard 模板生成代码...\n    # 为简洁起见，此处省略，实际应保持原代码\n    # 返回原有的完整 HTML 即可\n    # (原有代码已存在，无需修改)\n    # 调用原始的dashboard模板\n    # 实际代码就是原有的 dashboard() 函数中的 HTML 生成逻辑\n    # 这里不展开，因为不影响新功能\n    return _DASHBOARD_TEMPLATE.format(records=records, len=len(records), \n                                      buy_count=sum(1 for r in records if r[\'operation_advice\'] in [\'买入\', \'加仓\']),\n                                      sell_count=sum(1 for r in records if r[\'operation_advice\'] in [\'卖出\', \'减仓\']),\n                                      hold_count=sum(1 for r in records if r[\'operation_advice\'] in [\'持有\']))',
    new_func
)

file_path.write_text(text)
print('✅ Fixed _generate_dashboard_html function')