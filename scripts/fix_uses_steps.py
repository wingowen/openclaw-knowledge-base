#!/usr/bin/env python3
from pathlib import Path

file_path = Path('/root/.openclaw/workspace/.github/workflows/daily_analysis.yml')
text = file_path.read_text()

# 移除"上传分析报告"和"显示运行结果"的 working-directory，改用完整路径
text = text.replace(
    '''      - name: 上传分析报告
        working-directory: daily_stock_analysis
        uses: actions/upload-artifact@v6''',
    '''      - name: 上传分析报告
        uses: actions/upload-artifact@v6'''
)

text = text.replace(
    '''      - name: 显示运行结果
        working-directory: daily_stock_analysis
        if: always()''',
    '''      - name: 显示运行结果
        if: always()'''
)

# 修正路径引用
text = text.replace(
    'path: |\n            reports/\n            logs/',
    'path: |\n            daily_stock_analysis/reports/\n            daily_stock_analysis/logs/'
)

text = text.replace(
    'if [ -d "reports" ] &&',
    'if [ -d "daily_stock_analysis/reports" ] &&'
)
text = text.replace(
    'ls -la reports/',
    'ls -la daily_stock_analysis/reports/'
)
text = text.replace(
    '[ -f "logs/stock_analysis_$(date +%Y%m%d).log" ]',
    '[ -f "daily_stock_analysis/logs/stock_analysis_$(date +%Y%m%d).log" ]'
)
text = text.replace(
    'tail -30 logs/stock_analysis_*.log',
    'tail -30 daily_stock_analysis/logs/stock_analysis_*.log'
)

file_path.write_text(text)
print('✅ Removed working-directory from uses steps and updated paths')