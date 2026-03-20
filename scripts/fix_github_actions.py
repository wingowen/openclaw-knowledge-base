#!/usr/bin/env python3
from pathlib import Path

file_path = Path('/root/.openclaw/workspace/.github/workflows/daily_analysis.yml')
text = file_path.read_text()

# 在 "执行股票分析" 步骤中添加 working-directory
old = '      - name: 执行股票分析\n        env:'
new = '      - name: 执行股票分析\n        working-directory: daily_stock_analysis\n        env:'

text = text.replace(old, new)

file_path.write_text(text)
print('✅ Added working-directory to 执行股票分析 step')