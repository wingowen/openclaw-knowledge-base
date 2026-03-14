"""
量价关系回测 - 腾讯财经API版
"""

import pandas as pd
import requests
import time

def get_tencent_data():
    """从腾讯财经获取贵州茅台日线数据"""
    
    # 腾讯财经API
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    
    params = {
        "_var": "kline_dayqfq",
        "param": "sh600519,day,,,500,qfq"  # 获取最近500个交易日
    }
    
    headers = {"User-Agent": "Mozilla/5.0"}
    
    for attempt in range(3):
        try:
            print(f"尝试 {attempt+1}/3: 腾讯财经...")
            response = requests.get(url, params=params, headers=headers, timeout=30)
            
            if response.status_code == 200:
                text = response.text
                # 解析返回数据
                if 'qfqday' in text:
                    # 提取JSON部分
                    json_str = text.split('=', 1)[1]
                    data = eval(json_str)
                    
                    if data.get('code') == 0:
                        klines = data['data']['sh600519']['qfqday']
                        print(f"✅ 获取到 {len(klines)} 条K线数据")
                        
                        # 解析K线 [日期, 开盘, 收盘, 最高, 最低, 成交量(手)]
                        records = []
                        for k in klines:
                            if len(k) >= 6:
                                records.append({
                                    'date': k[0],
                                    'open': float(k[1]),
                                    'close': float(k[2]),
                                    'high': float(k[3]),
                                    'low': float(k[4]),
                                    'volume': float(k[5]) * 100  # 手转股
                                })
                        
                        df = pd.DataFrame(records[::-1])  # 倒序（从早到晚）
                        return df
            else:
                print(f"   HTTP {response.status_code}")
        except Exception as e:
            print(f"   失败: {e}")
        
        time.sleep(2)
    
    return None

# ========== 获取数据 ==========
print("=" * 60)
print("获取贵州茅台真实数据...")
print("=" * 60)

df = get_tencent_data()

if df is None:
    print("\n❌ 所有数据源都失败")
    print("建议在本地环境运行，本脚本仅作参考")
    exit(1)

print(f"\n数据量: {len(df)} 行 (真实数据)")
print(f"日期范围: {df['date'].min()} ~ {df['date'].max()}")
print()

# ========== 参数扫描 ==========
print("=" * 60)
print("开始参数扫描...")
print("=" * 60)

all_results = []

for period in [3, 5, 10, 20]:
    for threshold in [0.05, 0.1, 0.2, 0.3, 0.5, 0.8]:
        vol_ma = df['volume'].rolling(period).mean()
        vol_change = (df['volume'] - vol_ma) / vol_ma
        future_return = df['close'].pct_change(-period)
        
        signal = vol_change > threshold
        profit = signal.shift(1) * future_return
        
        valid_idx = profit.dropna().index
        signal_series = signal.shift(1).loc[valid_idx]
        profit_series = profit.loc[valid_idx]
        
        signal_count = (signal_series > 0).sum()
        
        if signal_count >= 3:
            wins = (profit_series[signal_series > 0] > 0).sum()
            win_rate = wins / signal_count
            avg_return = profit_series[signal_series > 0].mean()
            avg_loss = profit_series[signal_series <= 0].mean()
            
            profit_loss_ratio = abs(avg_return / avg_loss) if avg_loss else None
            
            all_results.append({
                'period': period,
                'threshold': threshold,
                'signals': signal_count,
                'wins': wins,
                'losses': signal_count - wins,
                'win_rate': win_rate,
                'avg_return': avg_return,
                'profit_loss_ratio': profit_loss_ratio
            })

# ========== 输出结果 ==========
print("\n" + "=" * 70)
print("📊 参数扫描结果 (贵州茅台)")
print("=" * 70)

if all_results:
    sorted_results = sorted(all_results, key=lambda x: x['win_rate'], reverse=True)
    
    print(f"{'周期':^6} | {'阈值':^8} | {'信号':^5} | {'胜/负':^6} | {'胜率':^10} | {'盈亏比':^8}")
    print("-" * 70)
    
    for r in sorted_results[:15]:
        pl_ratio = f"{r['profit_loss_ratio']:.2f}" if r['profit_loss_ratio'] else "N/A"
        print(f"{r['period']:^6} | {r['threshold']:>6.0%} | {r['signals']:^5} | {r['wins']:>2}/{r['losses']:<3} | {r['win_rate']:>8.1%} | {pl_ratio}")
    
    best = sorted_results[0]
    print("=" * 70)
    print(f"\n✅ 最优正向参数:")
    print(f"   周期={best['period']}日, 阈值={best['threshold']:.0%}")
    print(f"   胜率={best['win_rate']:.1%} ({best['wins']}胜 {best['losses']}负)")
    if best['profit_loss_ratio']:
        print(f"   盈亏比={best['profit_loss_ratio']:.2f}")
    
    if best['win_rate'] > 0.55:
        print("   → 核心假设成立! 🎉")
    elif best['win_rate'] < 0.45:
        print("   → 核心假设不成立，需调整策略")
    else:
        print("   → 无明显预测能力")
else:
    print("⚠️ 信号不足，请降低阈值重试")

# ========== 反向策略 ==========
print("\n" + "=" * 70)
print("📊 反向策略 (放量+上涨=见顶信号，做空)")
print("=" * 70)

reverse_results = []

for period in [5, 10]:
    for threshold in [0.3, 0.5]:
        vol_ma = df['volume'].rolling(period).mean()
        vol_change = (df['volume'] - vol_ma) / vol_ma
        future_return = df['close'].pct_change(-period)
        today_return = df['close'].pct_change(1)
        
        # 放量+今日上涨 → 做空
        signal = (vol_change > threshold) & (today_return > 0)
        profit = signal.shift(1) * future_return  # 做空盈利=价格下跌
        
        valid_idx = profit.dropna().index
        signal_series = signal.shift(1).loc[valid_idx]
        profit_series = profit.loc[valid_idx]
        
        signal_count = (signal_series > 0).sum()
        if signal_count >= 3:
            wins = (profit_series[signal_series > 0] > 0).sum()
            win_rate = wins / signal_count
            
            reverse_results.append({
                'period': period,
                'threshold': threshold,
                'signals': signal_count,
                'wins': wins,
                'win_rate': win_rate
            })
            
            print(f"周期{period}日 放量>{threshold:.0%}+上涨 → 胜率{win_rate:.1%} ({signal_count}信号)")

if reverse_results:
    best_reverse = sorted(reverse_results, key=lambda x: x['win_rate'], reverse=True)[0]
    print(f"\n   最优反向: 周期={best_reverse['period']}日, 阈值={best_reverse['threshold']:.0%}")
    print(f"   反向胜率: {best_reverse['win_rate']:.1%}")
