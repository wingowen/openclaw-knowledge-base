#!/usr/bin/env python3
"""
沪深300成分股策略分析 - 分批获取
每批10只，获取完立即分析
"""

import requests
import pandas as pd
import numpy as np
import time
import os
from datetime import datetime

DATA_DIR = "stock_data/hs300"
os.makedirs(DATA_DIR, exist_ok=True)

# 沪深300成分股池（分批）
BATCHES = [
    # 第1批：消费金融
    ["600519", "贵州茅台"], ["600887", "伊利股份"], ["000858", "五粮液"],
    ["600036", "招商银行"], ["601398", "工商银行"], ["601988", "中国银行"],
    ["600030", "中信证券"], ["601628", "中国人寿"], ["600276", "恒瑞医药"], ["603259", "药明康德"],
    
    # 第2批：科技医药
    ["000538", "云南白药"], ["002415", "海康威视"], ["688981", "中芯国际"], ["300760", "迈瑞医疗"],
    ["002475", "立讯精密"], ["601857", "中国石油"], ["601899", "紫金矿业"], ["600019", "宝钢股份"],
    ["601088", "中国神华"], ["600362", "江西铜业"],
    
    # 第3批：电力地产通信
    ["600021", "上海电力"], ["600900", "长江电力"], ["600795", "国电电力"],
    ["600048", "保利地产"], ["600383", "金地集团"], ["601668", "中国建筑"],
    ["600050", "中国联通"], ["600037", "三峡传媒"], ["600498", "烽火通信"],
    ["600850", "华东医药"],
]

def get_stock_data(code):
    """获取单只股票数据"""
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

def analyze_strategies(df):
    """分析两种策略"""
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    
    # 指标
    df['v_ma5'] = df['volume'].rolling(5).mean()
    df['vc'] = (df['volume'] - df['v_ma5']) / df['v_ma5']
    df['ret_f5'] = df['close'].pct_change(-5)
    
    # 策略1: 放量买入
    sig1 = df[df['vc'] > 0.25]
    profits1 = []
    for idx in sig1.index:
        ret = df.iloc[idx]['ret_f5']
        if not pd.isna(ret):
            profits1.append(ret)
    
    # 策略2: 缩量后的放量
    df['squeeze'] = (df['vc'] < -0.20) & (df['close'].pct_change(10).abs() < 0.15)
    df['breakout'] = df['vc'] > 0.25
    
    profits2 = []
    for i in range(len(df)):
        if df.iloc[i]['squeeze']:
            for j in range(i+1, min(i+11, len(df))):
                if df.iloc[j]['breakout']:
                    ret = df.iloc[j]['ret_f5']
                    if not pd.isna(ret):
                        profits2.append(ret)
                    break
    
    return profits1, profits2

def main():
    """主函数"""
    
    print("=" * 75)
    print("🔥 沪深300成分股策略分析 - 分批获取")
    print("=" * 75)
    
    all_results = []
    
    # 分批处理
    batch_size = 10
    for batch_idx in range(0, len(BATCHES), batch_size):
        batch = BATCHES[batch_idx:batch_idx+batch_size]
        batch_num = batch_idx // batch_size + 1
        
        print(f"\n{'='*75}")
        print(f"📦 第 {batch_num} 批 ({len(batch)} 只)")
        print(f"{'='*75}")
        
        batch_results = []
        
        for i, (code, name) in enumerate(batch):
            print(f"\r  [{i+1}/{len(batch)}] {code} {name}...", end="", flush=True)
            
            df = get_stock_data(code)
            if df is None:
                print(" ❌ 失败")
                continue
            
            df.to_csv(f"{DATA_DIR}/{code}.csv", index=False)
            
            # 分析
            profits1, profits2 = analyze_strategies(df)
            
            if len(profits1) >= 3:
                wins1 = sum(1 for p in profits1 if p > 0)
                batch_results.append({
                    'code': code, 'name': name,
                    's1_trades': len(profits1), 's1_wins': wins1, 's1_wr': wins1/len(profits1), 's1_avg': np.mean(profits1),
                    's2_trades': len(profits2), 's2_wins': sum(1 for p in profits2 if p > 0) if profits2 else 0,
                    's2_wr': sum(1 for p in profits2 if p > 0)/len(profits2) if profits2 else 0,
                    's2_avg': np.mean(profits2) if profits2 else 0
                })
            
            time.sleep(0.8)
        
        print(f"\n\n✅ 第 {batch_num} 批完成 {len(batch_results)} 只")
        
        # 显示本批结果
        if batch_results:
            batch_results.sort(key=lambda x: x['s1_wr'], reverse=True)
            
            print(f"\n{'代码':<8} {'放量买入(胜率/信号)':<22} {'缩量后放量(胜率/信号)':<22}")
            print("-" * 55)
            for r in batch_results:
                s1 = f"{r['s1_wr']:.1%}({r['s1_trades']})"
                s2 = f"{r['s2_wr']:.1%}({r['s2_trades']})" if r['s2_trades'] > 0 else "N/A"
                print(f"{r['code']:<8} {s1:<22} {s2:<22}")
            
            all_results.extend(batch_results)
        
        # 每批之间暂停
        if batch_idx + batch_size < len(BATCHES):
            print("\n⏳ 暂停30秒...")
            time.sleep(30)
    
    # ========== 汇总 ==========
    print("\n\n" + "=" * 75)
    print("📊 全量汇总")
    print("=" * 75)
    
    # 策略1
    s1_trades = sum(r['s1_trades'] for r in all_results)
    s1_wins = sum(r['s1_wins'] for r in all_results)
    s1_avg = sum(r['s1_avg'] * r['s1_trades'] for r in all_results) / s1_trades if s1_trades > 0 else 0
    s1_wr = s1_wins / s1_trades if s1_trades > 0 else 0
    
    # 策略2
    s2_trades = sum(r['s2_trades'] for r in all_results)
    s2_wins = sum(r['s2_wins'] for r in all_results)
    s2_avg = sum(r['s2_avg'] * r['s2_trades'] for r in all_results) / s2_trades if s2_trades > 0 else 0
    s2_wr = s2_wins / s2_trades if s2_trades > 0 else 0
    
    print(f"\n策略1 放量买入: 胜率{s1_wr:.1%} ({s1_wins}/{s1_trades}), 均收益{s1_avg:+.2%}")
    print(f"策略2 缩量后放量: 胜率{s2_wr:.1%} ({s2_wins}/{s2_trades}), 均收益{s2_avg:+.2%}")
    
    # TOP/BOTTOM
    print(f"\n🏆 放量买入 TOP 5:")
    for r in sorted(all_results, key=lambda x: x['s1_wr'], reverse=True)[:5]:
        print(f"   {r['code']} {r['name']}: {r['s1_wr']:.1%}")
    
    print(f"\n⚠️ 放量买入 BOTTOM 5:")
    for r in sorted(all_results, key=lambda x: x['s1_wr'])[:5]:
        print(f"   {r['code']} {r['name']}: {r['s1_wr']:.1%}")
    
    # 保存
    df = pd.DataFrame(all_results)
    df.to_csv("hs300_batch_results.csv", index=False)
    print(f"\n💾 结果已保存: hs300_batch_results.csv")
    
    # 结论
    print("\n" + "=" * 75)
    print("💡 核心结论")
    print("=" * 75)
    
    if s1_wr > 0.55:
        print(f"\n🎉 放量买入策略有效！胜率{s1_wr:.1%}")
    elif s1_wr > 0.50:
        print(f"\n⚠️ 放量买入策略勉强有效，胜率{s1_wr:.1%}")
    else:
        print(f"\n❌ 放量买入策略无效，胜率{s1_wr:.1%}")

if __name__ == "__main__":
    main()
