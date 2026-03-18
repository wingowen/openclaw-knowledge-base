from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import sqlite3
import json
import os

app = FastAPI(title="Daily Stock Analysis", version="1.0.0")

@app.get("/", response_class=HTMLResponse)
def dashboard():
    """分析仪表盘"""
    db_path = "./data/stock_analysis.db"
    records = []
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute("""
                SELECT id, code, name, operation_advice, sentiment_score, 
                       trend_prediction, analysis_summary, ideal_buy, secondary_buy,
                       stop_loss, take_profit, created_at, raw_result
                FROM analysis_history
                ORDER BY created_at DESC
                LIMIT 20
            """)
            records = [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"DB error: {e}")
        conn.close()
    
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>股票分析系统 - 决策仪表盘</title>
        <meta charset="utf-8">
        <style>
            * { box-sizing: border-box; margin: 0; padding: 0; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background: #f0f2f5; color: #333; }
            .header { background: linear-gradient(135deg, #1a237e 0%, #283593 100%); color: white; padding: 24px; }
            .header h1 { font-size: 24px; margin-bottom: 8px; }
            .header p { opacity: 0.8; font-size: 14px; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin: 20px 0; }
            .stat-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
            .stat-value { font-size: 28px; font-weight: bold; color: #1a237e; }
            .stat-label { font-size: 14px; color: #666; margin-top: 4px; }
            .card { background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.1); margin-bottom: 20px; overflow: hidden; }
            .card-header { background: #f8f9fa; padding: 16px 20px; border-bottom: 1px solid #eee; font-weight: 600; }
            .card-body { padding: 20px; }
            .stock-item { border-bottom: 1px solid #f0f0f0; padding: 16px 0; }
            .stock-item:last-child { border-bottom: none; }
            .stock-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
            .stock-name { font-size: 18px; font-weight: 600; }
            .stock-code { color: #666; font-size: 14px; }
            .badge { padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: 600; }
            .badge-buy { background: #e8f5e9; color: #2e7d32; }
            .badge-sell { background: #ffebee; color: #c62828; }
            .badge-hold { background: #fff3e0; color: #ef6c00; }
            .badge-wait { background: #f5f5f5; color: #757575; }
            .analysis-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 16px; margin-top: 12px; }
            .analysis-section { background: #fafafa; padding: 12px; border-radius: 8px; }
            .analysis-title { font-size: 14px; font-weight: 600; color: #1a237e; margin-bottom: 8px; }
            .analysis-content { font-size: 13px; line-height: 1.6; }
            .checklist { list-style: none; }
            .checklist li { padding: 4px 0; font-size: 13px; }
            .sniper-points { display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; }
            .sniper-item { background: #f5f5f5; padding: 8px; border-radius: 6px; text-align: center; }
            .sniper-label { font-size: 11px; color: #666; }
            .sniper-value { font-size: 16px; font-weight: 600; color: #333; }
            .score { display: inline-flex; align-items: center; justify-content: center; width: 36px; height: 36px; border-radius: 50%; font-weight: bold; font-size: 14px; }
            .score-high { background: #e8f5e9; color: #2e7d32; }
            .score-medium { background: #fff3e0; color: #ef6c00; }
            .score-low { background: #ffebee; color: #c62828; }
            .expand-btn { background: none; border: 1px solid #ddd; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; color: #666; }
            .expand-btn:hover { background: #f5f5f5; }
            .detail-panel { display: none; margin-top: 12px; padding: 16px; background: #f8f9fa; border-radius: 8px; }
            .detail-panel.show { display: block; }
            .links { display: flex; gap: 16px; margin-top: 20px; }
            .links a { color: #1a237e; text-decoration: none; padding: 8px 16px; border: 1px solid #1a237e; border-radius: 6px; font-size: 14px; }
            .links a:hover { background: #1a237e; color: white; }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <h1>📈 股票智能分析系统</h1>
                <p>基于趋势交易理念的AI决策仪表盘 | 数据驱动，风险优先</p>
            </div>
        </div>
        
        <div class="container">
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-value">""" + str(len(records)) + """</div>
                    <div class="stat-label">分析记录总数</div>
                </div>
    """
    
    # 统计各种建议的数量
    buy_count = sum(1 for r in records if r['operation_advice'] in ['买入', '加仓'])
    sell_count = sum(1 for r in records if r['operation_advice'] in ['卖出', '减仓'])
    hold_count = sum(1 for r in records if r['operation_advice'] in ['持有'])
    
    html += f"""
                <div class="stat-card">
                    <div class="stat-value" style="color: #2e7d32;">{buy_count}</div>
                    <div class="stat-label">买入/加仓建议</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: #c62828;">{sell_count}</div>
                    <div class="stat-label">卖出/减仓建议</div>
                </div>
                <div class="stat-card">
                    <div class="stat-value" style="color: #ef6c00;">{hold_count}</div>
                    <div class="stat-label">持有建议</div>
                </div>
            </div>
            
            <div class="links">
                <a href="/docs">📚 API 文档</a>
                <a href="/health">💚 健康检查</a>
                <a href="/api/v1/analysis/analyze">🔍 分析接口</a>
            </div>
            
            <div class="card" style="margin-top: 20px;">
                <div class="card-header">📊 最近分析记录 - 决策仪表盘</div>
                <div class="card-body">
    """
    
    for r in records:
        # 解析 raw_result 获取详细分析
        dashboard_data = {}
        battle_plan = {}
        core_conclusion = {}
        data_perspective = {}
        intelligence = {}
        
        if r['raw_result']:
            try:
                raw = json.loads(r['raw_result'])
                dashboard_data = raw.get('dashboard', {})
                core_conclusion = dashboard_data.get('core_conclusion', {})
                data_perspective = dashboard_data.get('data_perspective', {})
                intelligence = dashboard_data.get('intelligence', {})
                battle_plan = dashboard_data.get('battle_plan', {})
            except:
                pass
        
        # 确定建议的样式
        advice = r['operation_advice'] or '未知'
        badge_class = 'badge-wait'
        if advice in ['买入', '加仓']:
            badge_class = 'badge-buy'
        elif advice in ['卖出', '减仓']:
            badge_class = 'badge-sell'
        elif advice in ['持有']:
            badge_class = 'badge-hold'
        
        # 评分样式
        score = r['sentiment_score'] or 0
        score_class = 'score-low'
        if score >= 70:
            score_class = 'score-high'
        elif score >= 50:
            score_class = 'score-medium'
        
        # 核心结论
        one_sentence = core_conclusion.get('one_sentence', r['analysis_summary'] or '暂无分析摘要')
        signal_type = core_conclusion.get('signal_type', '')
        
        # 狙击点位
        sniper_points = battle_plan.get('sniper_points', {})
        ideal_buy = sniper_points.get('ideal_buy', f"理想买点: {r['ideal_buy'] or '-'}")
        secondary_buy = sniper_points.get('secondary_buy', f"次优买点: {r['secondary_buy'] or '-'}")
        stop_loss = sniper_points.get('stop_loss', f"止损位: {r['stop_loss'] or '-'}")
        take_profit = sniper_points.get('take_profit', f"目标位: {r['take_profit'] or '-'}")
        
        # 检查清单
        action_checklist = battle_plan.get('action_checklist', [])
        
        # 趋势数据
        trend_status = data_perspective.get('trend_status', {})
        price_position = data_perspective.get('price_position', {})
        volume_analysis = data_perspective.get('volume_analysis', {})
        chip_structure = data_perspective.get('chip_structure', {})
        
        # 情报数据
        risk_alerts = intelligence.get('risk_alerts', [])
        positive_catalysts = intelligence.get('positive_catalysts', [])
        
        html += f"""
                    <div class="stock-item">
                        <div class="stock-header">
                            <div>
                                <span class="stock-name">{r['name'] or '未知'}</span>
                                <span class="stock-code">({r['code']})</span>
                                <span class="badge {badge_class}">{advice}</span>
                                <span class="score {score_class}">{score}</span>
                            </div>
                            <div style="font-size: 12px; color: #666;">
                                {r['created_at'][:16] if r['created_at'] else '-'}
                            </div>
                        </div>
                        
                        <div style="margin-bottom: 12px; font-size: 15px; font-weight: 500;">
                            {one_sentence}
                        </div>
                        
                        <div class="sniper-points">
                            <div class="sniper-item">
                                <div class="sniper-label">理想买点</div>
                                <div class="sniper-value">{r['ideal_buy'] or '-'}</div>
                            </div>
                            <div class="sniper-item">
                                <div class="sniper-label">次优买点</div>
                                <div class="sniper-value">{r['secondary_buy'] or '-'}</div>
                            </div>
                            <div class="sniper-item">
                                <div class="sniper-label">止损位</div>
                                <div class="sniper-value">{r['stop_loss'] or '-'}</div>
                            </div>
                            <div class="sniper-item">
                                <div class="sniper-label">目标位</div>
                                <div class="sniper-value">{r['take_profit'] or '-'}</div>
                            </div>
                        </div>
                        
                        <button class="expand-btn" onclick="toggleDetail('detail-{r['id']}')">展开详细分析</button>
                        
                        <div id="detail-{r['id']}" class="detail-panel">
                            <div class="analysis-grid">
        """
        
        # 趋势分析
        if trend_status:
            html += f"""
                                <div class="analysis-section">
                                    <div class="analysis-title">📈 趋势分析</div>
                                    <div class="analysis-content">
                                        <div>均线排列: {trend_status.get('ma_alignment', '-')}</div>
                                        <div>趋势强度: {trend_status.get('trend_score', '-')}/100</div>
                                        <div>多头排列: {'✅ 是' if trend_status.get('is_bullish') else '❌ 否'}</div>
                                    </div>
                                </div>
            """
        
        # 价格位置
        if price_position:
            html += f"""
                                <div class="analysis-section">
                                    <div class="analysis-title">💰 价格位置</div>
                                    <div class="analysis-content">
                                        <div>当前价: {price_position.get('current_price', '-')}</div>
                                        <div>MA5: {price_position.get('ma5', '-')} (乖离: {price_position.get('bias_ma5', '-')}%)</div>
                                        <div>MA10: {price_position.get('ma10', '-')}</div>
                                        <div>MA20: {price_position.get('ma20', '-')}</div>
                                        <div>支撑位: {price_position.get('support_level', '-')}</div>
                                        <div>压力位: {price_position.get('resistance_level', '-')}</div>
                                    </div>
                                </div>
            """
        
        # 量能分析
        if volume_analysis:
            html += f"""
                                <div class="analysis-section">
                                    <div class="analysis-title">📊 量能分析</div>
                                    <div class="analysis-content">
                                        <div>量比: {volume_analysis.get('volume_ratio', '-')}</div>
                                        <div>状态: {volume_analysis.get('volume_status', '-')}</div>
                                        <div>换手率: {volume_analysis.get('turnover_rate', '-')}%</div>
                                        <div>解读: {volume_analysis.get('volume_meaning', '-')}</div>
                                    </div>
                                </div>
            """
        
        # 筹码结构
        if chip_structure:
            html += f"""
                                <div class="analysis-section">
                                    <div class="analysis-title">🎯 筹码结构</div>
                                    <div class="analysis-content">
                                        <div>获利比例: {chip_structure.get('profit_ratio', '-')}%</div>
                                        <div>平均成本: {chip_structure.get('avg_cost', '-')}</div>
                                        <div>集中度: {chip_structure.get('concentration', '-')}%</div>
                                        <div>健康度: {chip_structure.get('chip_health', '-')}</div>
                                    </div>
                                </div>
            """
        
        # 检查清单
        if action_checklist:
            html += """
                                <div class="analysis-section">
                                    <div class="analysis-title">✅ 检查清单</div>
                                    <div class="analysis-content">
                                        <ul class="checklist">
            """
            for item in action_checklist:
                html += f"<li>{item}</li>"
            html += """
                                        </ul>
                                    </div>
                                </div>
            """
        
        # 风险提示
        if risk_alerts:
            html += """
                                <div class="analysis-section">
                                    <div class="analysis-title">⚠️ 风险提示</div>
                                    <div class="analysis-content">
            """
            for risk in risk_alerts:
                html += f"<div>• {risk}</div>"
            html += """
                                    </div>
                                </div>
            """
        
        # 利好催化
        if positive_catalysts:
            html += """
                                <div class="analysis-section">
                                    <div class="analysis-title">🚀 利好催化</div>
                                    <div class="analysis-content">
            """
            for catalyst in positive_catalysts:
                html += f"<div>• {catalyst}</div>"
            html += """
                                    </div>
                                </div>
            """
        
        html += """
                            </div>
                        </div>
                    </div>
        """
    
    html += """
                </div>
            </div>
        </div>
        
        <script>
        function toggleDetail(id) {
            const panel = document.getElementById(id);
            panel.classList.toggle('show');
        }
        </script>
    </body>
    </html>
    """
    return html

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "daily_stock_analysis"}

@app.get("/api/v1/analysis/analyze")
def analyze_stock():
    return {"message": "Analysis endpoint", "available": True}