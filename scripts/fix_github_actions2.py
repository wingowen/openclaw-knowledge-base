#!/usr/bin/env python3
from pathlib import Path

file_path = Path('/root/.openclaw/workspace/.github/workflows/daily_analysis.yml')
text = file_path.read_text()

# 为上传报告和显示结果步骤也添加 working-directory
text = text.replace(
    '      - name: 上传分析报告\n        uses: actions/upload-artifact@v6',
    '      - name: 上传分析报告\n        working-directory: daily_stock_analysis\n        uses: actions/upload-artifact@v6'
)
text = text.replace(
    '      - name: 显示运行结果\n        if: always()\n        run: |',
    '      - name: 显示运行结果\n        working-directory: daily_stock_analysis\n        if: always()\n        run: |'
)

file_path.write_text(text)
print('✅ Added working-directory to 上传分析报告 and 显示运行结果 steps')