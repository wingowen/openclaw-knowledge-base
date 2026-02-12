#!/usr/bin/env python3
"""
股票数据缓存系统
目标：确保数据获取稳定性，支持离线回测
"""

import pandas as pd
import requests
import time
import os
from datetime import datetime

# ========== 配置 ==========
DATA_DIR = "stock_data"
os.makedirs(DATA_DIR, exist_ok=True)

# ========== 数据源 ==========
SOURCES = {
    "tencent": {
        "name": "腾讯财经",
        "url": "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get",
        "params": {"_var": "kline_dayqfq", "param": "sh600519,day,,,500,qfq"},
        "parser": "parse_tencent"
    }
}

def parse_tencent(response_text):
    """解析腾讯财经数据"""
    json_str = response_text.split('=', 1)[1]
    data = eval(json_str)
    if data.get('code') == 0:
        klines = data['data']['sh600519']['qfqday']
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
    return None

def get_stock_data(stock_code, source="tencent", force_update=False):
    """
    获取股票数据，自动缓存到CSV
    
    Args:
        stock_code: 股票代码，如 '600519'
        source: 数据源 ('tencent')
        force_update: 是否强制更新
    
    Returns:
        DataFrame: 股票数据
    """
    csv_path = f"{DATA_DIR}/{stock_code}.csv"
    
    # 1. 优先从CSV读取（未过期）
    if not force_update and os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        # 检查是否过期（超过7天）
        if len(df) > 0:
            last_date = pd.to_datetime(df['date'].max())
            if (datetime.now() - last_date).days < 7:
                print(f"📁 从缓存读取: {stock_code}.csv ({len(df)} 行)")
                return df
    
    # 2. 从API获取
    print(f"🌐 从{source}获取: {stock_code}...")
    
    headers = {"User-Agent": "Mozilla/5.0"}
    source_info = SOURCES[source]
    
    for attempt in range(3):
        try:
            response = requests.get(
                source_info["url"], 
                params=source_info["params"], 
                headers=headers, 
                timeout=30
            )
            
            if response.status_code == 200:
                parser = globals()[source_info["parser"]]
                df = parser(response.text)
                
                if df is not None and len(df) > 0:
                    # 保存到CSV
                    df.to_csv(csv_path, index=False)
                    print(f"✅ 保存到: {csv_path} ({len(df)} 行)")
                    return df
                    
        except Exception as e:
            print(f"   尝试 {attempt+1}/3 失败: {e}")
            time.sleep(2)
    
    # 3. 失败时尝试使用旧缓存
    if os.path.exists(csv_path):
        print(f"⚠️ API失败，使用旧缓存: {csv_path}")
        return pd.read_csv(csv_path)
    
    print(f"❌ 无法获取 {stock_code} 数据")
    return None

def list_cached_stocks():
    """列出已缓存的股票"""
    print(f"\n📁 {DATA_DIR}/ 缓存的股票数据:")
    print("-" * 40)
    
    for f in os.listdir(DATA_DIR):
        if f.endswith('.csv'):
            df = pd.read_csv(f"{DATA_DIR}/{f}")
            if len(df) > 0:
                last_date = df['date'].max()
                print(f"  {f.replace('.csv','')}: {len(df)} 行, 最新: {last_date}")
    
    print()

def backup_data():
    """备份所有数据到 timestamp 目录"""
    import shutil
    backup_dir = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copytree(DATA_DIR, backup_dir)
    print(f"📦 备份到: {backup_dir}")

# ========== 主函数测试 ==========
if __name__ == "__main__":
    print("=" * 60)
    print("股票数据缓存系统")
    print("=" * 60)
    
    # 获取贵州茅台
    df = get_stock_data("600519", source="tencent")
    
    if df is not None:
        print(f"\n数据预览:")
        print(df.head())
        print(f"\n总行数: {len(df)}")
    
    # 列出缓存
    list_cached_stocks()
