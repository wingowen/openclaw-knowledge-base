#!/usr/bin/env python3
"""
「点灯+举烛」右侧交易策略回测 - 简化版

点灯：缩量企稳（不再涨的缩量横盘）
举烛：放量上涨（开始涨的放量突破）

逻辑：点灯后N日内出现举烛信号则买入
"""

import pandas as pd
import numpy as np
import os

# ========== 配置 ==========
STOCK_CODE = "600021"  # 上海电力
STOCK_NAME = "上海电力"
DATA_FILE = f"stock_data/{STOCK_CODE}.csv"

# ========== 加载数据 ==========
df = pd.read_csv(DATA_FILE)
df['date'] = pd.to_datetime(df['date'])
df = df.sort_values('date').reset_index(drop=True)

# ========== 计算指标 ==========
df['volume_ma5'] = df['volume'].rolling(5).mean()
df['volume_ma20'] = df['volume'].rolling(20).mean()
df['price_ma5'] = df['close'].rolling(5).mean()
df['price_ma20'] = df['close'].rolling(20).mean()
df['vol_change'] = (df['volume'] - df['volume_ma5']) / df['volume_ma5']
df['vol_change20'] = (df['volume'] - df['volume_ma20']) / df['volume_ma20']
df['return_d1'] = df['close'].pct_change(1)
df['return_future'] = df['close'].pct_change(-5)  # 未来5日

# ========== 策略信号 ==========

# 点灯：缩量企稳
# 连续3日缩量 + 横盘震荡
df['light_3day'] = (df['vol_change'] < -0.2) & (df.shift(1)['vol_change'] < -0.2) & (df.shift(2)['vol_change'] < -0.2)
df['light_stable'] = df['close'].pct_change(10).abs() < 0.15  # 10日内波动<15%
df['signal_light'] = df['light_3day'] & df['light_stable']

# 举烛：放量上涨
# 放量 + 大阳线/突破
df['signal_candle'] = (df['vol_change'] > 0.3) & (df['return_d1'] > 0.01) & (df['close'] > df['price_ma5'])

# ========== 二阶段信号 ==========
# 找点灯后N日内举烛
OBS_DAYS = 10

df['light_date'] = None
for i in range(len(df)):
    if df.iloc[i]['signal_light']:
        # 标记为点灯日
        df.iloc[i, df.columns.get_loc('light_date')] = df.iloc[i]['date']

# 填充light_date
df['light_date'] = df['light_date'].ffill()

# 判断举烛是否在点灯后的OBS_DAYS日内
df['days_from_light'] = None
for i in range(len(df)):
    if df.iloc[i]['signal_candle'] and pd.notna(df.iloc[i]['light_date']):
        light_date = pd.to_datetime(df.iloc[i]['light_date'])
        days = (df.iloc[i]['date'] - light_date).days
        if 1 <= days <= OBS_DAYS:
            df.iloc[i, df.columns.get_loc('days_from_light')] = days

df['signal_combined'] = df['days_from_light'].notna()

# ========== 回测 ==========
print("=" * 70)
print(f"「点灯+举烛」策略回测 - {STOCK_NAME}({STOCK_CODE})")
print("=" * 70)

# 点灯单独统计
lights = df[df['signal_light']]
print(f"\n📊 点灯信号: {len(lights)} 次")

# 举烛单独统计
candles = df[df['signal_candle']]
print(f"\n📊 举烛信号: {len(candles)} 次")

# 二阶段统计
combined = df[df['signal_combined']]
print(f"\n🔥 二阶段「点灯+举烛」信号: {len(combined)} 次")

if len(combined) > 0:
    profits = []
    for idx in combined.index:
        future_ret = df.iloc[idx]['return_future']
        if not np.isnan(future_ret):
            profits.append({
                'date': df.iloc[idx]['date'],
                'entry': df.iloc[idx]['close'],
                'wait': df.iloc[idx]['days_from_light'],
                'ret': future_ret
            })
    
    if profits:
        rets = [p['ret'] for p in profits]
        wins = sum(1 for r in rets if r > 0)
        losses = len(rets) - wins
        win_rate = wins / len(rets)
        avg_ret = np.mean(rets)
        
        print(f"\n📋 交易详情 (共{len(profits)}笔):")
        print("-" * 50)
        for p in sorted(profits, key=lambda x: x['ret'], reverse=True):
            mark = '✓' if p['ret'] > 0 else '✗'
            print(f"  {mark} {p['date'].strftime('%Y-%m-%d')} | 买入:{p['entry']:.2f} | 等待:{int(p['wait'])}日 | 收益:{p['ret']:+.2%}")
        
        print("\n" + "=" * 70)
        print("📊 回测结果")
        print("=" * 70)
        print(f"交易次数: {len(profits)}")
        print(f"胜率: {win_rate:.1%} ({wins}胜 {losses}负)")
        print(f"平均收益: {avg_ret:.3%}")
        print(f"最大盈利: {max(rets):.2%}")
        print(f"最大亏损: {min(rets):.2%}")
        
        # 结论
        if win_rate > 0.55:
            print("\n✅ 策略有效！胜率超过55%")
        elif win_rate > 0.50:
            print("\n⚠️ 策略勉强有效")
        else:
            print("\n❌ 策略无效，需要调整")
else:
    print("\n⚠️ 二阶段信号为0，说明上海电力不符合「先缩量后放量」模式")
    
    # 统计单独的放量上涨信号
    print("\n📊 单独「放量上涨」信号回测:")
    candle_profits = []
    for idx in candles.index:
        ret = df.iloc[idx]['return_future']
        if not np.isnan(ret):
            candle_profits.append(ret)
    
    if candle_profits:
        wins = sum(1 for r in candle_profits if r > 0)
        wr = wins / len(candle_profits)
        avg = np.mean(candle_profits)
        print(f"   胜率: {wr:.1%}")
        print(f"   平均收益: {avg:.3%}")
