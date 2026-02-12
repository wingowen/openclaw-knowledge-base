#!/usr/bin/env python3
"""
量价策略库 - 综合回测
用真实数据验证多种策略，按胜率排序
"""

import pandas as pd
import numpy as np

# ========== 加载数据 ==========
DATA_PATH = "stock_data/600519.csv"
df = pd.read_csv(DATA_PATH)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

print("=" * 70)
print(f"📊 贵州茅台量价策略回测")
print(f"   数据量: {len(df)} 交易日")
print(f"   时间: {df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}")
print("=" * 70)

# ========== 预处理 ==========
# 计算基础指标
df['volume_ma5'] = df['volume'].rolling(5).mean()
df['volume_ma10'] = df['volume'].rolling(10).mean()
df['price_ma5'] = df['close'].rolling(5).mean()
df['price_ma20'] = df['close'].rolling(20).mean()

# 成交量变化率
df['vol_change'] = (df['volume'] - df['volume_ma5']) / df['volume_ma5']
df['vol_change10'] = (df['volume'] - df['volume_ma10']) / df['volume_ma10']

# 价格变化
df['return_d1'] = df['close'].pct_change(1)  # 当日涨幅
df['return_d5'] = df['close'].pct_change(5)  # 5日涨幅
df['return_future'] = df['close'].pct_change(-5)  # 未来5日涨幅

# 涨跌标记
df['is_up'] = df['return_d1'] > 0
df['is_down'] = df['return_d1'] < 0
df['is_big_up'] = df['return_d1'] > 0.02  # 大阳线 >2%
df['is_big_down'] = df['return_d1'] < -0.02  # 大阴线 >-2%

# 均线状态
df['above_ma5'] = df['close'] > df['price_ma5']
df['above_ma20'] = df['close'] > df['price_ma20']
df['ma5_above_ma20'] = df['price_ma5'] > df['price_ma20']  # 金叉状态

# ========== 策略定义 ==========
strategies = []

def add_strategy(name, signal_condition, hold_days=5):
    """添加策略"""
    strategies.append({
        'name': name,
        'signal': signal_condition,
        'hold_days': hold_days
    })

# ========== 策略库 ==========

# 1. 放量突破
add_strategy("1.放量突破(MA5+30%)", 
    (df['vol_change'] > 0.3) & (df['close'] > df['price_ma5']))

# 2. 放量+大阳线
add_strategy("2.放量+大阳线", 
    (df['vol_change'] > 0.3) & (df['is_big_up']))

# 3. 温和放量+上涨
add_strategy("3.温和放量+上涨", 
    (df['vol_change'] > 0.1) & (df['vol_change'] < 0.5) & (df['is_up']))

# 4. 缩量企稳
add_strategy("4.缩量企稳", 
    (df['vol_change'] < -0.3) & (df['close'] > df['price_ma20']))

# 5. 地量+底部
add_strategy("5.地量+MA20支撑", 
    (df['vol_change'] < -0.5) & (df['close'] > df['price_ma20']) & (df['close'] < df['price_ma5']))

# 6. 量价齐升
add_strategy("6.量价齐升", 
    (df['vol_change'] > 0.2) & (df['is_up']) & (df['ma5_above_ma20']))

# 7. 放量杀跌(抄底)
add_strategy("7.放量杀跌抄底", 
    (df['vol_change'] > 0.5) & (df['is_down']))

# 8. 高位放量(逃顶)
add_strategy("8.高位放量逃顶", 
    (df['vol_change'] > 0.5) & (df['close'] > df['price_ma20']) & (df['is_down']))

# 9. 均线金叉+放量
add_strategy("9.MA5金叉MA20+放量", 
    (df['ma5_above_ma20']) & (df.shift(1)['ma5_above_ma20'] == False) & (df['vol_change'] > 0.2))

# 10. 放量十字星
add_strategy("10.放量十字星", 
    (df['vol_change'] > 0.4) & (np.abs(df['return_d1']) < 0.005))

# 11. 强势股缩量
add_strategy("11.强势股缩量(MA20上方+缩量)", 
    (df['above_ma20']) & (df['vol_change'] < -0.2))

# 12. 放量过前高
add_strategy("12.放量过前高", 
    (df['vol_change'] > 0.3) & (df['close'] > df['close'].shift(20)))

# 13. 底部放量
add_strategy("13.底部放量反弹", 
    (df['vol_change'] > 0.5) & (df['close'] < df['price_ma20']) & (df['is_up']))

# 14. 价跌量缩(止跌)
add_strategy("14.价跌量缩(止跌信号)", 
    (df['is_down']) & (df['vol_change'] < -0.2))

# 15. 量价背离(上涨缩量)
add_strategy("15.量价背离(看跌)", 
    (df['is_up']) & (df['vol_change'] < -0.2))

# ========== 回测函数 ==========
def backtest(strategy, df):
    """回测单个策略"""
    signal = strategy['signal']
    hold_days = strategy['hold_days']
    
    # 计算未来收益
    future_return = df['close'].pct_change(-hold_days)
    
    # 信号次日生效
    valid_signal = signal.shift(1)
    profit = valid_signal * future_return
    
    # 统计
    valid_idx = profit.dropna().index
    signal_series = valid_signal.loc[valid_idx]
    profit_series = profit.loc[valid_idx]
    
    signal_count = (signal_series > 0).sum()
    
    if signal_count < 3:
        return None
    
    wins = (profit_series[signal_series > 0] > 0).sum()
    losses = signal_count - wins
    win_rate = wins / signal_count
    
    avg_return = profit_series[valid_signal > 0].mean()
    avg_win = profit_series[(valid_signal > 0) & (profit_series > 0)].mean()
    avg_loss = profit_series[(valid_signal > 0) & (profit_series <= 0)].mean()
    
    profit_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else None
    
    # 期望值
    expected_value = win_rate * avg_return + (1 - win_rate) * avg_loss if avg_loss != 0 else None
    
    return {
        'signals': signal_count,
        'wins': wins,
        'losses': losses,
        'win_rate': win_rate,
        'avg_return': avg_return,
        'avg_win': avg_win,
        'avg_loss': avg_loss,
        'profit_loss_ratio': profit_loss_ratio,
        'expected_value': expected_value
    }

# ========== 执行回测 ==========
print("\n🔍 正在回测 15 种策略...")
print("=" * 70)

results = []

for s in strategies:
    result = backtest(s, df)
    if result:
        result['name'] = s['name']
        results.append(result)

# ========== 排序输出 ==========
# 按胜率排序
results_sorted = sorted(results, key=lambda x: x['win_rate'], reverse=True)

print(f"\n{'策略名称':<28} | {'信号':^5} | {'胜/负':^6} | {'胜率':^10} | {'盈亏比':^8} | {'期望值':^10}")
print("-" * 100)

for r in results_sorted:
    pl_ratio = f"{r['profit_loss_ratio']:.2f}" if r['profit_loss_ratio'] else "N/A"
    ev = f"{r['expected_value']:.3%}" if r['expected_value'] else "N/A"
    print(f"{r['name']:<28} | {r['signals']:^5} | {r['wins']:>2}/{r['losses']:<3} | {r['win_rate']:>8.1%} | {pl_ratio:^8} | {ev}")

print("=" * 70)

# ========== 分析总结 ==========
print("\n📊 策略有效性排名")
print("=" * 70)

top3 = results_sorted[:3]
bottom3 = results_sorted[-3:]

print("\n🏆 TOP 3 最有效策略:")
for i, r in enumerate(top3, 1):
    print(f"   {i}. {r['name']}")
    print(f"      胜率: {r['win_rate']:.1%}, 盈亏比: {r['profit_loss_ratio'] or 'N/A'}")

print("\n⚠️ 需要避免的策略:")
for i, r in enumerate(bottom3, 1):
    print(f"   {i}. {r['name']}")
    print(f"      胜率: {r['win_rate']:.1%}")

# ========== 核心发现 ==========
print("\n💡 核心发现:")
print("-" * 70)

# 找有效策略特征
good_strategies = [r for r in results if r['win_rate'] > 0.55]
if good_strategies:
    print(f"✅ 有效策略: {len(good_strategies)} 个 (胜率>55%)")
else:
    print("⚠️ 无明显有效策略 (所有策略胜率<55%)")

avg_win_rate = sum(r['win_rate'] for r in results) / len(results)
print(f"   平均胜率: {avg_win_rate:.1%}")
print(f"   随机策略基准: 50%")
print(f"   超越基准的策略: {len([r for r in results if r['win_rate'] > 0.5])}/{len(results)}")

# ========== 保存结果 ==========
output_path = "strategy_ranking.txt"
with open(output_path, 'w', encoding='utf-8') as f:
    f.write("贵州茅台量价策略回测结果\n")
    f.write("=" * 70 + "\n")
    f.write(f"数据: {df['date'].min().strftime('%Y-%m-%d')} ~ {df['date'].max().strftime('%Y-%m-%d')}\n")
    f.write(f"样本量: {len(df)} 交易日\n\n")
    
    f.write("策略排名 (按胜率排序):\n")
    f.write("-" * 70 + "\n")
    
    for i, r in enumerate(results_sorted, 1):
        f.write(f"{i}. {r['name']}\n")
        f.write(f"   信号数: {r['signals']}, 胜率: {r['win_rate']:.1%}, 盈亏比: {r['profit_loss_ratio'] or 'N/A'}\n")
    
    f.write("\n结论: 见控制台输出\n")

print(f"\n💾 结果已保存到: {output_path}")
