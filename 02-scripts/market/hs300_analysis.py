#!/usr/bin/env python3
"""
沪深300成分股策略分析 - 简化版
"""

import requests
import pandas as pd
import numpy as np
import time
import os

DATA_DIR = "stock_data/hs300"
os.makedirs(DATA_DIR, exist_ok=True)

# 沪深300代表性股票
HS300_STOCKS = [
    ("600519", "贵州茅台"), ("600887", "伊利股份"), ("000858", "五粮液"),
    ("600036", "招商银行"), ("601398", "工商银行"), ("601988", "中国银行"),
    ("600030", "中信证券"), ("601628", "中国人寿"),
    ("600276", "恒瑞医药"), ("603259", "药明康德"), ("000538", "云南白药"),
    ("002415", "海康威视"), ("688981", "中芯国际"), ("300760", "迈瑞医疗"),
    ("601857", "中国石油"), ("601899", "紫金矿业"), ("600019", "宝钢股份"),
    ("600021", "上海电力"), ("600900", "长江电力"), ("600048", "保利地产"),
    ("600050", "中国联通"), ("600037", "三峡传媒"), ("600498", "烽火通信"),
]

def get_stock_data(code):
    """获取数据"""
    if code.startswith('6') or code.startswith('688'):
        market = f"sh{code}"
    else:
        market = f"sz{code}"
    
    try:
        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        params = {"_var": "kline_dayqfq", "param": f"{market},day,,,250,qfq"}
        resp = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        if resp.status_code == 200 and 'qfqday' in resp.text:
            klines = eval(resp.text.split('=', 1)[1])['data'][market]['qfqday']
            records = [{'date': k[0], 'close': float(k[2]), 'volume': float(k[5]) * 100} for k in klines if len(k) >= 6]
            return pd.DataFrame(records[::-1])
    except:
        pass
    return None

def analyze(df):
    """分析放量买入策略"""
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # 指标
    df['v_ma5'] = df['volume'].rolling(5).mean()
    df['vc'] = (df['volume'] - df['v_ma5']) / df['v_ma5']
    df['ret_f5'] = df['close'].pct_change(-5)  # 未来5日
    
    # 放量买入
    sig = df[df['vc'] > 0.25]
    
    if len(sig) < 3:
        return None
    
    profits = []
    for idx in sig.index:
        ret = df.iloc[idx]['ret_f5']
        if not pd.isna(ret):
            profits.append(ret)
    
    if len(profits) < 3:
        return None
    
    wins = sum(1 for p in profits if p > 0)
    return {'trades': len(profits), 'wins': wins, 'wr': wins/len(profits), 'avg': np.mean(profits)}

def analyze_squeeze_then_breakout(df):
    """缩量后的放量"""
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    df['v_ma5'] = df['volume'].rolling(5).mean()
    df['vc'] = (df['volume'] - df['v_ma5']) / df['v_ma5']
    df['ret_f5'] = df['close'].pct_change(-5)
    
    # 缩量企稳
    df['squeeze'] = (df['vc'] < -0.20) & (df['close'].pct_change(10).abs() < 0.15)
    
    # 后续放量
    df['breakout'] = df['vc'] > 0.25
    
    # 找 squeeze 后 N 日内 breakout
    profits = []
    for i in range(len(df)):
        if df.iloc[i]['squeeze']:
            # 检查后续10日
            for j in range(i+1, min(i+11, len(df))):
                if df.iloc[j]['breakout']:
                    ret = df.iloc[j]['ret_f5']
                    if not pd.isna(ret):
                        profits.append(ret)
                    break
    
    if len(profits) < 3:
        return None
    
    wins = sum(1 for p in profits if p > 0)
    return {'trades': len(profits), 'wins': wins, 'wr': wins/len(profits), 'avg': np.mean(profits)}

def main():
    print("=" * 75)
    print("🔥 沪深300成分股策略分析")
    print("=" * 75)
    
    results1 = []  # 放量买入
    results2 = []  # 缩量后放量
    
    for i, (code, name) in enumerate(HS300_STOCKS):
        print(f"\r[{i+1}/{len(HS300_STOCKS)}] {code} {name}...", end="")
        
        df = get_stock_data(code)
        if df is None:
            continue
        
        df.to_csv(f"{DATA_DIR}/{code}.csv", index=False)
        
        # 放量买入
        r1 = analyze(df)
        if r1:
            r1['code'] = code
            r1['name'] = name
            results1.append(r1)
        
        # 缩量后放量
        r2 = analyze_squeeze_then_breakout(df)
        if r2:
            r2['code'] = code
            r2['name'] = name
            results2.append(r2)
        
        time.sleep(0.5)
    
    print(f"\n\n✅ 完成 {len(results1)} 只股票分析")
    
    # ========== 放量买入结果 ==========
    print("\n" + "=" * 75)
    print("📊 策略1: 放量买入")
    print("=" * 75)
    
    results1.sort(key=lambda x: x['wr'], reverse=True)
    
    print(f"\n{'代码':<8} {'名称':<10} {'信号':>4} {'胜/负':>8} {'胜率':>8} {'均收益':>10}")
    print("-" * 55)
    
    for r in results1:
        print(f"{r['code']:<8} {r['name']:<10} {r['trades']:>4} {r['wins']:>3}/{r['trades']-r['wins']:<4} {r['wr']:>7.1%} {r['avg']:>+9.2%}")
    
    t1 = sum(r['trades'] for r in results1)
    w1 = sum(r['wins'] for r in results1)
    a1 = sum(r['avg'] * r['trades'] for r in results1) / t1
    print("-" * 55)
    print(f"{'合计':<18} {t1:>4} {w1:>3}/{t1-w1:<4} {w1/t1:>7.1%} {a1:>+9.2%}")
    
    # ========== 缩量后放量结果 ==========
    print("\n" + "=" * 75)
    print("📊 策略2: 缩量后的放量")
    print("=" * 75)
    
    results2.sort(key=lambda x: x['wr'], reverse=True)
    
    print(f"\n{'代码':<8} {'名称':<10} {'信号':>4} {'胜/负':>8} {'胜率':>8} {'均收益':>10}")
    print("-" * 55)
    
    for r in results2:
        print(f"{r['code']:<8} {r['name']:<10} {r['trades']:>4} {r['wins']:>3}/{r['trades']-r['wins']:<4} {r['wr']:>7.1%} {r['avg']:>+9.2%}")
    
    if results2:
        t2 = sum(r['trades'] for r in results2)
        w2 = sum(r['wins'] for r in results2)
        a2 = sum(r['avg'] * r['trades'] for r in results2) / t2
        print("-" * 55)
        print(f"{'合计':<18} {t2:>4} {w2:>3}/{t2-w2:<4} {w2/t2:>7.1%} {a2:>+9.2%}")
    
    # ========== 结论 ==========
    print("\n" + "=" * 75)
    print("💡 核心结论")
    print("=" * 75)
    
    wr1 = w1/t1 if t1 > 0 else 0
    print(f"\n策略1 放量买入: 胜率{wr1:.1%}")
    print(f"策略2 缩量后放量: 胜率{w2/t2:.1%}" if results2 else "  无数据")
    
    if wr1 > 0.55:
        print("\n🎉 放量买入策略有效！")
    elif wr1 > 0.50:
        print("\n⚠️ 放量买入策略勉强有效")
    else:
        print("\n❌ 放量买入策略无效")

if __name__ == "__main__":
    main()
