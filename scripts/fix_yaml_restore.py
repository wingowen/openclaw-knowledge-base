#!/usr/bin/env python3
from pathlib import Path

file_path = Path('/root/.openclaw/workspace/.github/workflows/daily_analysis.yml')
text = file_path.read_text()

# 恢复并修正"上传分析报告"步骤
old_upload = '''      - name: 上传分析报告
        uses: actions/upload-artifact@v6
        if: always()
        with:
          name: analysis-reports-${{ github.run_number }}
          path: |
            reports/
            logs/
          retention-days: 30'''

new_upload = '''      - name: 上传分析报告
        working-directory: daily_stock_analysis
        uses: actions/upload-artifact@v6
        if: always()
        with:
          name: analysis-reports-${{ github.run_number }}
          path: |
            reports/
            logs/
          retention-days: 30'''

text = text.replace(old_upload, new_upload)

# 恢复"显示运行结果"步骤
old_display = '''      - name: 显示运行结果
        if: always()
        run: |
          echo ""
          echo "=========================================="
          echo "📊 分析完成"
          echo "=========================================="
          if [ -d "reports" ] && [ "$(ls -A reports 2>/dev/null)" ]; then
            echo "生成的报告:"
            ls -la reports/
          else
            echo "⚠️ 未生成报告文件"
          fi
          echo ""
          if [ -f "logs/stock_analysis_$(date +%Y%m%d).log" ]; then
            echo "📜 最近日志（最后 30 行）:"
            tail -30 logs/stock_analysis_*.log 2>/dev/null || echo "无日志"
          fi'''

new_display = '''      - name: 显示运行结果
        working-directory: daily_stock_analysis
        if: always()
        run: |
          echo ""
          echo "=========================================="
          echo "📊 分析完成"
          echo "=========================================="
          if [ -d "reports" ] && [ "$(ls -A reports 2>/dev/null)" ]; then
            echo "生成的报告:"
            ls -la reports/
          else
            echo "⚠️ 未生成报告文件"
          fi
          echo ""
          if [ -f "logs/stock_analysis_$(date +%Y%m%d).log" ]; then
            echo "📜 最近日志（最后 30 行）:"
            tail -30 logs/stock_analysis_*.log 2>/dev/null || echo "无日志"
          fi'''

text = text.replace(old_display, new_display)

file_path.write_text(text)
print('✅ Restored working-directory and fixed paths')