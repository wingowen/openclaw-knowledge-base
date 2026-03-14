#!/usr/bin/env python3
"""
「缩量后的放量」二阶段策略回测
核心逻辑：先缩量，再放量买入
"""

import pandas as pd
import numpy as np
import os

DATA_DIR = "stock_data"

# 已获取的股票
STOCKS = [
    ("600519", "贵州茅台"),
    ("600887", "伊利股份"),
    ("600036", "招商银行"),
    ("601398", "工商银行"),
    ("600276", "恒瑞医药"),
    ("603259", "药明康德"),
    ("002415", "海康威视"),
    ("601857", "中国石油"),
    ("601899", "紫金矿业"),
    ("600021", "上海电力"),
]

def load_data(code):
    """加载数据"""
    path = f"{DATA_DIR}/{code}.csv"
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    df['date'] = pd.to_datetime(df['date'])
    return df.sort_values('date').reset_index(drop=True)

def add_indicators(df):
    """添加技术指标"""
    df['volume_ma5'] = df['volume'].rolling(5).mean()
    df['volume_ma20'] = df['volume'].rolling(20).mean()
    df['price_ma5'] = df['close'].rolling(5).mean()
    df['price_ma20'] = df['close'].rolling(20).mean()
    df['vol_change'] = (df['volume'] - df['volume_ma5']) / df['volume_ma5']
    df['vol_change20'] = (df['volume'] - df['volume_ma20']) / df['volume_ma20']
    df['return_d1'] = df['close'].pct_change(1)
    df['return_future'] = df['close'].pct_change(-5)
    df['price_stable'] = df['close'].pct_change(10).abs() < 0.15  # 10日波动<15%
    return df

def test_strategy(code, name, light_thresh, candle_thresh, obs_days):
    """
    测试缩量后的放量策略
    
    Args:
        light_thresh: 缩量阈值 (如 -0.2 表示缩量20%)
        candle_thresh: 放量阈值 (如 0.3 表示放量30%)
        obs_days: 观察期（缩量后多少天内放量有效）
    """
    df = load_data(code)
    if df is None:
        return None
    
    df = add_indicators(df)
    
    # ===== 点灯：缩量企稳 =====
    # 连续N日缩量 + 价格横盘
    df['light_2day'] = (df['vol_change'] < light_thresh) & (df.shift(1)['vol_change'] < light_thresh)
    df['light_stable'] = df['price_stable']
    df['signal_light'] = df['light_2day'] & df['light_stable']
    
    # ===== 举烛：放量上涨 =====
    df['signal_candle'] = (df['vol_change'] > candle_thresh) & (df['return_d1'] > 0)
    
    # ===== 二阶段：点灯后N日内举烛 =====
    df['light_date'] = None
    for i in range(len(df)):
        if df.iloc[i]['signal_light']:
            df.iloc[i, df.columns.get_loc('light_date')] = df.iloc[i]['date']
    
    df['light_date'] = pd.to_datetime(df['light_date'], errors='coerce')
    df['light_date'] = df['light_date'].ffill()
    
    df['days_from_light'] = None
    for i in range(len(df)):
        if df.iloc[i]['signal_candle'] and pd.notna(df.iloc[i]['light_date']):
            light_date = df.iloc[i]['light_date']
            days = (df.iloc[i]['date'] - light_date).days
            if 1 <= days <= obs_days:
                df.iloc[i, df.columns.get_loc('days_from_light')] = days
    
    df['signal_combined'] = df['days_from_light'].notna()
    
    # ===== 回测 =====
    combined = df[df['signal_combined']]
    if len(combined) == 0:
        return {'trades': 0}
    
    profits = []
    for idx in combined.index:
        ret = df.iloc[idx]['return_future']
        if not np.isnan(ret):
            profits.append(ret)
    
    if len(profits) == 0:
        return {'trades': 0}
    
    wins = sum(1 for p in profits if p > 0)
    return {
        'trades': len(profits),
        'wins': wins,
        'losses': len(profits) - wins,
        'win_rate': wins / len(profits),
        'avg_return': np.mean(profits)
    }

def run_parameter_scan():
    """参数扫描"""
    
    print("=" * 80)
    print("🔥 「缩量后的放量」策略参数扫描")
    print("=" * 80)
    
    # 参数组合
    param_combos = [
        # (缩量阈值, 放量阈值, 观察期)
        (-0.15, 0.20, 10),  # 温和缩量15%+温和放量20%
        (-0.20, 0.25, 10),  # 缩量20%+放量25%
        (-0.20, 0.30, 10),  # 缩量20%+放量30%
        (-0.25, 0.30, 10),  # 明显缩量25%+放量30%
        (-0.30, 0.40, 10),  # 深度缩量30%+放量40%
        (-0.20, 0.25, 5),   # 缩短观察期
        (-0.30, 0.30, 15),  # 延长观察期
    ]
    
    all_results = {}
    
    for light_thresh, candle_thresh, obs_days in param_combos:
        param_name = f"缩量>{abs(light_thresh):.0%} 放量>{candle_thresh:.0%} 观察{obs_days}日"
        
        print(f"\n📊 参数: {param_name}")
        print("-" * 60)
        
        param_results = []
        
        for code, name in STOCKS:
            result = test_strategy(code, name, light_thresh, candle_thresh, obs_days)
            if result and result['trades'] > 0:
                param_results.append(result)
        
        if not param_results:
            print("   无有效信号")
            continue
        
        # 汇总
        total_trades = sum(r['trades'] for r in param_results)
        total_wins = sum(r['wins'] for r in param_results)
        avg_return = sum(r['avg_return'] * r['trades'] for r in param_results) / total_trades
        win_rate = total_wins / total_trades if total_trades > 0 else 0
        
        all_results[param_name] = {
            'trades': total_trades,
            'wins': total_wins,
            'win_rate': win_rate,
            'avg_return': avg_return,
            'details': param_results
        }
        
        print(f"   总信号: {total_trades}笔")
        print(f"   胜率: {win_rate:.1%}")
        print(f"   均收益: {avg_return:+.2%}")
    
    # 排序输出
    print("\n" + "=" * 80)
    print("📊 参数扫描结果 (按胜率排序)")
    print("=" * 80)
    
    sorted_results = sorted(all_results.items(), key=lambda x: x[1]['win_rate'], reverse=True)
    
    for i, (param_name, data) in enumerate(sorted_results, 1):
        print(f"\n{i}. {param_name}")
        print(f"   信号: {data['trades']}笔 | 胜率: {data['win_rate']:.1%} | 均收益: {data['avg_return']:+.2%}")
        
        # 显示各股票详情
        for d in data['details'][:3]:
            code = [c for c,n in STOCKS][list([r['trades'] for r in data['details']]).index(d['trades'])]
            print(f"      {code}: {d['trades']}笔 {d['win_rate']:.1%}")
    
    return all_results

def run_best_param_test():
    """用最优参数测试各股票"""
    
    print("\n" + "=" * 80)
    print("🔥 最优参数详细测试")
    print("=" * 80)
    
    # 最优参数：缩量20%+放量25%+观察10日
    light_thresh = -0.20
    candle_thresh = 0.25
    obs_days = 10
    
    print(f"\n参数: 缩量>{abs(light_thresh):.0%} 放量>{candle_thresh:.0%} 观察{obs_days}日")
    print("-" * 60)
    
    results = []
    
    for code, name in STOCKS:
        result = test_strategy(code, name, light_thresh, candle_thresh, obs_days)
        if result and result['trades'] > 0:
            result['code'] = code
            result['name'] = name
            results.append(result)
    
    # 按胜率排序
    results.sort(key=lambda x: x['win_rate'], reverse=True)
    
    print(f"\n{'代码':<8} {'名称':<10} {'信号':>4} {'胜/负':>8} {'胜率':>8} {'均收益':>10}")
    print("-" * 55)
    
    for r in results:
        print(f"{r['code']:<8} {r['name']:<10} {r['trades']:>4} {r['wins']:>3}/{r['losses']:<4} {r['win_rate']:>7.1%} {r['avg_return']:>+9.2%}")
    
    # 汇总
    total = sum(r['trades'] for r in results)
    wins = sum(r['wins'] for r in results)
    avg = sum(r['avg_return'] * r['trades'] for r in results) / total
    wr = wins / total if total > 0 else 0
    
    print("-" * 55)
    print(f"{'合计':<18} {total:>4} {wins:>3}/{total-wins:<4} {wr:>7.1%} {avg:>+9.2%}")
    
    return results

def main():
    """主函数"""
    
    print("=" * 80)
    print("🔥 「缩量后的放量」二阶段策略回测")
    print("=" * 80)
    
    # 1. 参数扫描
    all_results = run_parameter_scan()
    
    # 2. 最优参数测试
    best_results = run_best_param_test()
    
    # 3. 核心结论
    print("\n" + "=" * 80)
    print("💡 核心结论")
    print("=" * 80)
    
    # 计算整体统计
    total_trades = sum(r['trades'] for r in best_results)
    if total_trades > 0:
        total_wins = sum(r['wins'] for r in best_results)
        overall_wr = total_wins / total_trades
        
        print(f"\n📊 总体统计:")
        print(f"   测试股票: {len(best_results)}只")
        print(f"   总交易数: {total_trades}笔")
        print(f"   整体胜率: {overall_wr:.1%}")
        
        # 有效股票
        good = [r for r in best_results if r['win_rate'] > 0.55]
        bad = [r for r in best_results if r['win_rate'] < 0.45]
        
        print(f"\n✅ 策略有效 (胜率>55%):")
        for r in good:
            print(f"   {r['code']} {r['name']}: {r['win_rate']:.1%} ({r['trades']}笔)")
        
        print(f"\n❌ 策略无效 (胜率<45%):")
        for r in bad:
            print(f"   {r['code']} {r['name']}: {r['win_rate']:.1%} ({r['trades']}笔)")
        
        if overall_wr > 0.55:
            print(f"\n🎉 策略有效！整体胜率{overall_wr:.1%}超过55%")
        elif overall_wr > 0.50:
            print(f"\n⚠️ 策略勉强有效，整体胜率{overall_wr:.1%}")
        else:
            print(f"\n❌ 策略无效，整体胜率{overall_wr:.1%}")

if __name__ == "__main__":
    main()
