#!/usr/bin/env python3
"""
多行业股票策略回测
选取不同行业股票，验证「点灯+举烛」策略
"""

import pandas as pd
import numpy as np
import requests
import time
import os
from datetime import datetime
from typing import Optional

# ========== 配置 ==========
DATA_DIR = "stock_data"
os.makedirs(DATA_DIR, exist_ok=True)

# 选取不同行业代表性股票
STOCKS = {
    "消费": [
        ("600519", "贵州茅台"),
        ("600887", "伊利股份"),
    ],
    "金融": [
        ("600036", "招商银行"),
        ("601398", "工商银行"),
    ],
    "医药": [
        ("600276", "恒瑞医药"),
        ("603259", "药明康德"),
    ],
    "科技": [
        ("688981", "中芯国际"),
        ("002415", "海康威视"),
    ],
    "周期": [
        ("601857", "中国石油"),
        ("601899", "紫金矿业"),
    ],
    "电力": [
        ("600021", "上海电力"),
    ],
}

# 策略参数
OBS_DAYS = 10  # 观察期
HOLD_DAYS = 5  # 持有期

def get_stock_data(code: str) -> Optional[pd.DataFrame]:
    """获取单只股票数据"""
    # 确定市场前缀
    if code.startswith('6') or code.startswith('688'):
        market_code = f"sh{code}"
    else:
        market_code = f"sz{code}"
    
    try:
        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        params = {"_var": "kline_dayqfq", "param": f"{market_code},day,,,250,qfq"}
        headers = {"User-Agent": "Mozilla/5.0"}
        
        response = requests.get(url, params=params, headers=headers, timeout=20)
        if response.status_code == 200 and 'qfqday' in response.text:
            json_str = response.text.split('=', 1)[1]
            data = eval(json_str)
            if data.get('code') == 0:
                klines = data['data'][market_code]['qfqday']
                records = []
                for k in klines:
                    if len(k) >= 6:
                        records.append({
                            'date': k[0],
                            'open': float(k[1]),
                            'close': float(k[2]),
                            'high': float(k[3]),
                            'low': float(k[4]),
                            'volume': float(k[5]) * 100
                        })
                df = pd.DataFrame(records[::-1])
                return df
    except Exception as e:
        print(f"   获取失败: {e}")
    return None

def calculate_signals(df: pd.DataFrame) -> pd.DataFrame:
    """计算策略信号"""
    df = df.copy()
    
    # 指标
    df['volume_ma5'] = df['volume'].rolling(5).mean()
    df['volume_ma20'] = df['volume'].rolling(20).mean()
    df['price_ma5'] = df['close'].rolling(5).mean()
    df['price_ma20'] = df['close'].rolling(20).mean()
    df['vol_change'] = (df['volume'] - df['volume_ma5']) / df['volume_ma5']
    df['return_d1'] = df['close'].pct_change(1)
    df['return_future'] = df['close'].pct_change(-HOLD_DAYS)
    
    # 点灯：缩量企稳
    df['signal_light'] = (
        (df['vol_change'] < -0.2) & 
        (df['close'].pct_change(10).abs() < 0.15)
    )
    
    # 举烛：放量上涨
    df['signal_candle'] = (df['vol_change'] > 0.3) & (df['return_d1'] > 0.01)
    
    return df

def backtest_two_stage(df: pd.DataFrame) -> dict:
    """二阶段策略回测"""
    df = calculate_signals(df)
    
    # 确保日期列是datetime
    df['date'] = pd.to_datetime(df['date'])
    
    # 找点灯后N日内举烛
    df['light_date'] = None
    for i in range(len(df)):
        if df.iloc[i]['signal_light']:
            df.iloc[i, df.columns.get_loc('light_date')] = df.iloc[i]['date']
    
    df['light_date'] = pd.to_datetime(df['light_date'], errors='coerce')
    df['days_from_light'] = None
    
    for i in range(len(df)):
        if df.iloc[i]['signal_candle'] and pd.notna(df.iloc[i]['light_date']):
            light_date = pd.to_datetime(df.iloc[i]['light_date'])
            days = (df.iloc[i]['date'] - light_date).days
            if 1 <= days <= OBS_DAYS:
                df.iloc[i, df.columns.get_loc('days_from_light')] = days
    
    df['signal_combined'] = df['days_from_light'].notna()
    
    # 统计
    combined = df[df['signal_combined']]
    if len(combined) == 0:
        return {'trades': 0, 'win_rate': 0, 'avg_return': 0}
    
    profits = []
    for idx in combined.index:
        ret = df.iloc[idx]['return_future']
        if not np.isnan(ret):
            profits.append(ret)
    
    if len(profits) == 0:
        return {'trades': 0, 'win_rate': 0, 'avg_return': 0}
    
    wins = sum(1 for p in profits if p > 0)
    return {
        'trades': len(profits),
        'wins': wins,
        'losses': len(profits) - wins,
        'win_rate': wins / len(profits),
        'avg_return': np.mean(profits),
        'max_win': max(profits),
        'max_loss': min(profits)
    }

def backtest_simple(df: pd.DataFrame, signal_col: str) -> dict:
    """简单策略回测（放量买入）"""
    df = calculate_signals(df)
    
    signals = df[df[signal_col]]
    if len(signals) == 0:
        return {'trades': 0}
    
    profits = []
    for idx in signals.index:
        ret = df.iloc[idx]['return_future']
        if not np.isnan(ret):
            profits.append(ret)
    
    if len(profits) == 0:
        return {'trades': 0}
    
    wins = sum(1 for p in profits if p > 0)
    return {
        'trades': len(profits),
        'wins': wins,
        'win_rate': wins / len(profits),
        'avg_return': np.mean(profits)
    }

def main():
    """主函数"""
    
    print("=" * 75)
    print("🔥 多行业股票策略回测")
    print(f"参数: 观察期={OBS_DAYS}日, 持有={HOLD_DAYS}日")
    print("=" * 75)
    
    all_results = {}
    
    # 遍历所有类别
    for category, stocks in STOCKS.items():
        print(f"\n{'='*75}")
        print(f"📁 {category}")
        print(f"{'='*75}")
        
        category_results = []
        
        for code, name in stocks:
            print(f"\n📊 {code} {name}...", end=" ")
            
            # 获取数据
            csv_file = f"{DATA_DIR}/{code}.csv"
            if os.path.exists(csv_file):
                df = pd.read_csv(csv_file)
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values('date').reset_index(drop=True)
                print(f"缓存")
            else:
                df = get_stock_data(code)
                if df is not None:
                    df.to_csv(csv_file, index=False)
                    print(f"下载 ({len(df)}行)")
                else:
                    print(f"❌ 失败")
                    continue
            
            # 回测
            two_stage = backtest_two_stage(df)
            simple = backtest_simple(df, 'signal_candle')  # 放量买入
            
            result = {
                'code': code,
                'name': name,
                'price_range': f"{df['close'].min():.2f}~{df['close'].max():.2f}",
                'two_stage': two_stage,
                'simple': simple
            }
            category_results.append(result)
            
            # 显示结果
            print(f"  二阶段: {two_stage['trades']}笔")
            if two_stage['trades'] > 0:
                print(f"    胜率: {two_stage['win_rate']:.1%}")
            print(f"  放量买入: {simple['trades']}笔", end="")
            if simple['trades'] > 0:
                print(f"  胜率:{simple['win_rate']:.1%}")
            else:
                print()
        
        all_results[category] = category_results
    
    # ========== 汇总结果 ==========
    print("\n" + "=" * 75)
    print("📊 多行业回测汇总")
    print("=" * 75)
    
    # 按行业汇总
    summary_data = []
    
    for category, results in all_results.items():
        if not results:
            continue
        
        total_two = sum(r['two_stage']['trades'] for r in results)
        total_simple = sum(r['simple']['trades'] for r in results)
        
        if total_two > 0:
            ts_wins = sum(r['two_stage']['wins'] for r in results)
            ts_wr = ts_wins / total_two
        else:
            ts_wr = 0
        
        if total_simple > 0:
            s_wins = sum(r['simple']['wins'] for r in results)
            s_wr = s_wins / total_simple
        else:
            s_wr = 0
        
        summary_data.append({
            'category': category,
            'two_stage_wr': ts_wr,
            'two_stage_trades': total_two,
            'simple_wr': s_wr,
            'simple_trades': total_simple
        })
    
    # 按二阶段胜率排序
    summary_data.sort(key=lambda x: x['two_stage_wr'], reverse=True)
    
    print(f"\n{'行业':<8} | {'二阶段策略':<20} | {'放量买入':<20}")
    print("-" * 60)
    
    for s in summary_data:
        ts = f"{s['two_stage_wr']:.1%} ({s['two_stage_trades']}笔)" if s['two_stage_trades'] > 0 else "N/A"
        sm = f"{s['simple_wr']:.1%} ({s['simple_trades']}笔)" if s['simple_trades'] > 0 else "N/A"
        print(f"{s['category']:<8} | {ts:<20} | {sm:<20}")
    
    # ========== 核心结论 ==========
    print("\n" + "=" * 75)
    print("💡 核心结论")
    print("=" * 75)
    
    # 找出最有效的行业
    good = [s for s in summary_data if s['two_stage_wr'] > 0.55]
    bad = [s for s in summary_data if s['two_stage_wr'] < 0.45]
    
    print("\n✅ 策略有效 (胜率>55%):")
    for s in good:
        print(f"   {s['category']}: {s['two_stage_wr']:.1%} ({s['two_stage_trades']}笔)")
    
    print("\n❌ 策略无效 (胜率<45%):")
    for s in bad:
        print(f"   {s['category']}: {s['two_stage_wr']:.1%} ({s['two_stage_trades']}笔)")
    
    # 总体统计
    total_trades = sum(s['two_stage_trades'] for s in summary_data)
    if total_trades > 0:
        total_wins = sum(s['two_stage_wr'] * s['two_stage_trades'] for s in summary_data)
        overall_wr = total_wins / total_trades
        print(f"\n📊 总体: {total_trades}笔交易, 胜率{overall_wr:.1%}")
    
    # 保存结果
    with open("industry_results.txt", 'w', encoding='utf-8') as f:
        f.write("多行业策略回测结果\n")
        f.write("=" * 75 + "\n")
        f.write(f"时间: 2025-02 ~ 2026-02\n")
        f.write(f"参数: 观察期={OBS_DAYS}日, 持有={HOLD_DAYS}日\n\n")
        
        for s in summary_data:
            f.write(f"{s['category']}: 二阶段{s['two_stage_wr']:.1%}({s['two_stage_trades']}笔), 放量{s['simple_wr']:.1%}({s['simple_trades']}笔)\n")
    
    print(f"\n💾 结果已保存到: industry_results.txt")

if __name__ == "__main__":
    main()
