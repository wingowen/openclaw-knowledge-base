#!/usr/bin/env python3
"""
沪深300成分股数据分批获取
"""

import requests
import pandas as pd
import time
import os
from datetime import datetime

DATA_DIR = "stock_data/hs300"
os.makedirs(DATA_DIR, exist_ok=True)

# 读取股票列表
stocks = []
with open('hs300_stocks.csv', 'r') as f:
    for line in f:
        line = line.strip()
        if line and ',' in line:
            parts = line.split(',')
            if len(parts) >= 3:
                stocks.append({
                    'code': parts[0].strip(),
                    'name': parts[1].strip(),
                    'industry': parts[2].strip()
                })

def get_stock_data(code):
    """获取单只股票历史数据"""
    if code.startswith('6') or code.startswith('688'):
        market = f"sh{code}"
    else:
        market = f"sz{code}"
    
    try:
        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        params = {"_var": "kline_dayqfq", "param": f"{market},day,,,250,qfq"}
        headers = {"User-Agent": "Mozilla/5.0"}
        
        resp = requests.get(url, params=params, headers=headers, timeout=20)
        if resp.status_code == 200 and 'qfqday' in resp.text:
            klines = eval(resp.text.split('=', 1)[1])['data'][market]['qfqday']
            records = [{'date': k[0], 'close': float(k[2]), 'volume': float(k[5]) * 100} 
                      for k in klines if len(k) >= 6]
            return pd.DataFrame(records[::-1])
    except Exception as e:
        pass
    return None

def main():
    print("=" * 70)
    print("🔥 沪深300成分股数据分批获取")
    print("=" * 70)
    print(f"总股票数: {len(stocks)}")
    print()
    
    batch_size = 10
    total_batches = (len(stocks) + batch_size - 1) // batch_size
    
    success = 0
    failed = 0
    
    for batch_idx in range(0, len(stocks), batch_size):
        batch = stocks[batch_idx:batch_idx + batch_size]
        batch_num = batch_idx // batch_size + 1
        
        print(f"\n{'='*70}")
        print(f"📦 第 {batch_num}/{total_batches} 批 ({len(batch)} 只)")
        print(f"{'='*70}")
        
        for i, stock in enumerate(batch):
            code = stock['code']
            name = stock['name']
            
            print(f"\r  [{i+1}/{len(batch)}] {code} {name}...", end="", flush=True)
            
            df = get_stock_data(code)
            
            if df is not None and len(df) >= 100:
                df.to_csv(f"{DATA_DIR}/{code}.csv", index=False)
                print(f" ✅ ({len(df)}行)")
                success += 1
            else:
                print(f" ❌")
                failed += 1
            
            time.sleep(0.8)  # 限速
        
        # 每批之间暂停，避免被封
        if batch_idx + batch_size < len(stocks):
            print(f"\n⏳ 暂停30秒...")
            time.sleep(30)
    
    print(f"\n{'='*70}")
    print("✅ 获取完成!")
    print(f"   成功: {success} 只")
    print(f"   失败: {failed} 只")
    print(f"{'='*70}")
    
    # 统计已获取
    files = [f for f in os.listdir(DATA_DIR) if f.endswith('.csv')]
    print(f"\n📁 数据目录: {DATA_DIR}/")
    print(f"   已获取: {len(files)} 个CSV文件")

if __name__ == "__main__":
    main()
