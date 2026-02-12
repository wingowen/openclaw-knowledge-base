"""
最小化量价关系回测Demo
目标：验证「成交量变化率能否预测未来5日涨跌」
"""

import pandas as pd
import akshare as ak

# ========== 1. 获取数据 (约60交易日，1000行内) ==========
print("正在获取贵州茅台日线数据...")
df = ak.stock_zh_a_hist(symbol="600519", period="daily", start_date="20230101", end_date="20230331")
df = df.rename(columns={'成交量': 'volume', '收盘': 'close'})
df['volume'] = df['volume'].astype(float)
df['close'] = df['close'].astype(float)
print(f"数据量: {len(df)} 行")

# ========== 2. 计算核心指标 ==========
# 成交量变化率 = (当日成交量 - 5日均成交量) / 5日均成交量
df['vol_ma5'] = df['volume'].rolling(5).mean()
df['vol_change'] = (df['volume'] - df['vol_ma5']) / df['vol_ma5']

# 未来5日涨跌幅
df['future_return'] = df['close'].pct_change(-5)

# ========== 3. 策略逻辑 (阈值: 0.3 = 30%) ==========
df['signal'] = df['vol_change'] > 0.3
df['profit'] = df['signal'].shift(1) * df['future_return']  # 信号次日生效

# ========== 4. 输出关键指标 ==========
valid_signals = df.dropna(subset=['profit'])
signal_count = (valid_signals['signal'].shift(1) > 0).sum()

if signal_count > 0:
    profits = valid_signals['profit']
    wins = (profits > 0).sum()
    total = len(profits)
    win_rate = wins / total
    
    avg_win = profits[profits > 0].mean() if wins > 0 else 0
    avg_loss = abs(profits[profits < 0].mean()) if (total - wins) > 0 else 0
    profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else float('inf')
    
    print("\n" + "=" * 50)
    print("📊 回测结果")
    print("=" * 50)
    print(f"标的: 贵州茅台(600519.SH)")
    print(f"时间: 2023-01-01 ~ 2023-03-31")
    print(f"样本量: {total} 个交易日")
    print(f"触发信号次数: {signal_count} 次")
    print(f"胜率: {win_rate:.1%} ({wins}胜 {total-wins}负)")
    print(f"盈亏比: {profit_loss_ratio:.2f}" if avg_loss > 0 else "盈亏比: N/A")
    print("=" * 50)
    
    # 结论
    if win_rate > 0.55:
        conclusion = "✅ 成交量放大30%时，未来5日上涨概率高于55%，核心假设成立"
    elif win_rate < 0.45:
        conclusion = "❌ 胜率低于45%，核心假设不成立，需重新设计指标"
    else:
        conclusion = "⚠️ 胜率在45%-55%之间，无明显预测能力"
    
    print(conclusion)
    
    # 保存结果
    with open('results.txt', 'w', encoding='utf-8') as f:
        f.write(f"贵州茅台(600519.SH) 量价关系回测\n")
        f.write(f"时间范围: 2023-01-01 ~ 2023-03-31\n")
        f.write(f"样本量: {total} 个交易日\n")
        f.write(f"触发信号: {signal_count} 次\n")
        f.write(f"胜率: {win_rate:.1%}\n")
        f.write(f"盈亏比: {profit_loss_ratio:.2f}\n")
        f.write(f"结论: {conclusion}\n")
else:
    print("⚠️ 期间无符合买入条件的信号，尝试降低阈值重试")
