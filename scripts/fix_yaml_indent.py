#!/usr/bin/env python3
from pathlib import Path

file_path = Path('/root/.openclaw/workspace/.github/workflows/daily_analysis.yml')
text = file_path.read_text()

# 修复 "上传分析报告" 步骤的缩进
text = text.replace(
    '''      - name: 上传分析报告
        working-directory: daily_stock_analysis
        uses: actions/upload-artifact@v6
        if: always()
        with:''',
    '''      - name: 上传分析报告
        uses: actions/upload-artifact@v6
        if: always()
        with:'''
)

# 修复 "显示运行结果" 步骤的缩进
text = text.replace(
    '''      - name: 显示运行结果
        working-directory: daily_stock_analysis
        if: always()
        run: |''',
    '''      - name: 显示运行结果
        if: always()
        run: |'''
)

file_path.write_text(text)
print('✅ Fixed YAML indentation for upload-artifact and display steps')