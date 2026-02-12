#!/usr/bin/env python3
"""
多股票策略回测 - 汇总5只股票结果
"""

import pandas as pd
import numpy as np
import os

DATA_DIR = "stock_data"
STOCKS = {"600519": "贵州茅台", "600036": "招商银行", "601398": "工商银行", "600887": "伊利股份", "000001": "上证指数"}

def load_and_prepare(code):
    """加载并准备数据"""
    path = f"{DATA_DIR}/{code}.csv"
    if not os.path.exists(path): return None
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    df = df.sort_values('date').reset_index(drop=True)
    
    df['v_ma5'] = df['volume'].rolling(5).mean()
    df['v_ma10'] = df['volume'].rolling(10).mean()
    df['p_ma5'] = df['close'].rolling(5).mean()
    df['p_ma20'] = df['close'].rolling(20).mean()
    
    df['vc'] = (df['volume'] - df['v_ma5']) / df['v_ma5']
    df['ret_d1'] = df['close'].pct_change(1)
    df['ret_f5'] = df['close'].pct_change(-5)
    
    df['up'] = df['ret_d1'] > 0
    df['dup'] = df['ret_d1'] > 0.02
    df['down'] = df['ret_d1'] < 0
    df['ddn'] = df['ret_d1'] < -0.02
    df['a_ma5'] = df['close'] > df['p_ma5']
    df['a_ma20'] = df['close'] > df['p_ma20']
    df['ma5_20'] = df['p_ma5'] > df['p_ma20']
    
    return df

def backtest(df, sig_func):
    """回测"""
    sig = sig_func(df)
    profit = sig.shift(1) * df['ret_f5']
    sig_c = sig.shift(1).dropna()
    p = profit.dropna()
    idx = p.index.intersection(sig_c.index)
    sc = (sig_c.loc[idx] > 0).sum()
    if sc < 3: return None
    wins = (p.loc[idx[sig_c.loc[idx] > 0]] > 0).sum()
    return {'signals': sc, 'wins': wins, 'losses': sc-wins, 'wr': wins/sc}

# 策略定义
STRATEGIES = [
    ("1.放量突破", lambda d: (d['vc'] > 0.3) & (d['close'] > d['p_ma5'])),
    ("2.放量+大阳线", lambda d: (d['vc'] > 0.3) & (d['dup'])),
    ("3.温和放量+上涨", lambda d: (d['vc'] > 0.1) & (d['vc'] < 0.5) & (d['up'])),
    ("4.缩量企稳", lambda d: (d['vc'] < -0.3) & (d['close'] > d['p_ma20'])),
    ("5.地量+MA20支撑", lambda d: (d['vc'] < -0.5) & (d['close'] > d['p_ma20']) & (d['close'] < d['p_ma5'])),
    ("6.量价齐升", lambda d: (d['vc'] > 0.2) & (d['up']) & (d['ma5_20'])),
    ("7.放量杀跌抄底", lambda d: (d['vc'] > 0.5) & (d['down'])),
    ("8.高位放量逃顶", lambda d: (d['vc'] > 0.5) & (d['close'] > d['p_ma20']) & (d['down'])),
    ("9.MA5金叉MA20+放量", lambda d: (d['ma5_20']) & (d.shift(1)['ma5_20']==False) & (d['vc'] > 0.2)),
    ("10.放量十字星", lambda d: (d['vc'] > 0.4) & (np.abs(d['ret_d1']) < 0.005)),
    ("11.强势股缩量", lambda d: (d['a_ma20']) & (d['vc'] < -0.2)),
    ("12.放量过前高", lambda d: (d['vc'] > 0.3) & (d['close'] > d['close'].shift(20))),
    ("13.底部放量反弹", lambda d: (d['vc'] > 0.5) & (d['close'] < d['p_ma20']) & (d['up'])),
    ("14.价跌量缩", lambda d: (d['down']) & (d['vc'] < -0.2)),
    ("15.量价背离(看跌)", lambda d: (d['up']) & (d['vc'] < -0.2)),
]

print("=" * 75)
print("🔥 多股票策略回测 (5只股票)")
print("=" * 75)

all_results = {}

for code, name in STOCKS.items():
    print(f"\n📊 {code} {name}...", end=" ")
    df = load_and_prepare(code)
    if df is None: continue
    print(f"{len(df)}行")
    
    for sname, sfunc in STRATEGIES:
        r = backtest(df, sfunc)
        if r:
            if sname not in all_results:
                all_results[sname] = {'s': 0, 'w': 0}
            all_results[sname]['s'] += r['signals']
            all_results[sname]['w'] += r['wins']

# 汇总
print("\n" + "=" * 75)
print("📊 汇总结果 (按胜率排序)")
print("=" * 75)

summary = [{'n': k, 's': v['s'], 'w': v['w'], 'wr': v['w']/v['s']} for k,v in all_results.items()]
summary = sorted(summary, key=lambda x: x['wr'], reverse=True)

print(f"\n{'策略':<26} | {'信号':^6} | {'胜/负':^8} | {'胜率':^10}")
print("-" * 60)

for r in summary:
    print(f"{r['n']:<26} | {r['s']:^6} | {r['w']:>3}/{r['s']-r['w']:<4} | {r['wr']:>8.1%}")

print("=" * 75)

# 分析
valid = [r for r in summary if r['s'] >= 20]
good = [r for r in valid if r['wr'] > 0.55]
bad = [r for r in valid if r['wr'] < 0.45]

print(f"\n🏆 TOP 3:")
for i, r in enumerate(summary[:3], 1):
    print(f"   {i}. {r['n']} - 胜率{r['wr']:.1%} ({r['s']}信号)")

print(f"\n⚠️ 避免:")
for i, r in enumerate(summary[-3:], 1):
    print(f"   {i}. {r['n']} - 胜率{r['wr']:.1%} ({r['s']}信号)")

print(f"\n💡 结论:")
print(f"   测试: {len(STOCKS)}只股票")
print(f"   有效(胜率>55%): {len(good)}个")
print(f"   无效(胜率<45%): {len(bad)}个")
print(f"   平均胜率: {sum(r['wr'] for r in summary)/len(summary):.1%}")
