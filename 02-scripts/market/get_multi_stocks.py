#!/usr/bin/env python3
"""
多股票数据获取
"""

import pandas as pd
import requests
import time
import os

DATA_DIR = "stock_data"
os.makedirs(DATA_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

STOCKS = {
    "600519": "贵州茅台",
    "600036": "招商银行",
    "601398": "工商银行",
    "600887": "伊利股份",
    "000001": "上证指数",
}

def get_tencent_stock(stock_code):
    """腾讯数据源"""
    code = f"sh{stock_code}" if stock_code.startswith("6") else f"sz{stock_code}"
    url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
    params = {"_var": "kline_dayqfq", "param": f"{code},day,,,500,qfq"}
    
    for attempt in range(2):
        try:
            response = requests.get(url, params=params, headers=HEADERS, timeout=15)
            if response.status_code == 200:
                text = response.text
                if 'qfqday' in text and 'param error' not in text:
                    json_str = text.split('=', 1)[1]
                    data = eval(json_str)
                    if data.get('code') == 0:
                        klines = data['data'][code]['qfqday']
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
                        return pd.DataFrame(records[::-1])
        except Exception as e:
            pass
        time.sleep(3)
    return None

def get_akshare_stocks():
    """akshare数据源"""
    try:
        import akshare as ak
        print("\n📡 akshare...")
        
        for code, name in STOCKS.items():
            if not code.startswith("000"):
                print(f"  {code} {name}...", end=" ")
                try:
                    df = ak.stock_zh_a_hist(symbol=code, period="daily", adjust="qfq")
                    if len(df) > 50:
                        df = df.rename(columns={'成交量': 'volume', '收盘': 'close'})
                        df.to_csv(f"{DATA_DIR}/{code}.csv", index=False)
                        print(f"✅ {len(df)}行")
                    else:
                        print("❌ 数据不足")
                except Exception as e:
                    print(f"❌ {e}")
                time.sleep(1)
    except Exception as e:
        print(f"akshare失败: {e}")

# ========== 主程序 ==========
print("=" * 60)
print("获取多只股票数据")
print("=" * 60)

# 腾讯
print("\n📡 腾讯财经...")
for code, name in STOCKS.items():
    print(f"  {code} {name}...", end=" ")
    df = get_tencent_stock(code)
    if df is not None and len(df) > 50:
        df.to_csv(f"{DATA_DIR}/{code}.csv", index=False)
        print(f"✅ {len(df)}行")
    else:
        print("❌")
    time.sleep(2)

# akshare
get_akshare_stocks()

# 显示
print("\n" + "=" * 60)
print("📁 已缓存:")
for f in sorted(os.listdir(DATA_DIR)):
    if f.endswith('.csv'):
        try:
            df = pd.read_csv(f"{DATA_DIR}/{f}")
            if 'date' in df.columns:
                print(f"  {f}: {len(df)}行")
        except:
            pass
