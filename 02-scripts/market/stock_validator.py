#!/usr/bin/env python3
"""
股票代码验证工具
通过多个接口验证A股股票代码
"""

import requests
import pandas as pd
import time
from typing import Dict, Optional, List

class StockCodeValidator:
    """股票代码验证器"""
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        self.cache = {}
    
    def get_stock_by_name(self, name: str) -> List[Dict]:
        """
        通过股票名称搜索代码
        
        Args:
            name: 股票名称（如 '上海电力'）
            
        Returns:
            匹配的股票列表
        """
        results = []
        
        # 方法1: 东方财富模糊搜索
        results.extend(self._search_eastmoney(name))
        
        # 方法2: 新浪接口
        results.extend(self._search_sina(name))
        
        # 去重
        seen = set()
        unique_results = []
        for r in results:
            key = r['code']
            if key not in seen:
                seen.add(key)
                unique_results.append(r)
        
        return unique_results
    
    def _search_eastmoney(self, name: str) -> List[Dict]:
        """东方财富搜索"""
        try:
            url = "http://push2.eastmoney.com/api/qt/clist/get"
            params = {
                "pn": "1",
                "pz": "100",
                "np": "1",
                "fltt": "2",
                "invt": "2",
                "fid": "f8",
                "fields": "f12,f14,f2,f3"
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('data') and data['data'].get('list'):
                    stocks = data['data']['list']
                    matches = []
                    for s in stocks:
                        stock_name = s.get('f14', '') or ''
                        if name in stock_name:
                            matches.append({
                                'code': s.get('f12', ''),
                                'name': stock_name,
                                'price': s.get('f2', 0),
                                'change': s.get('f3', 0),
                                'source': 'eastmoney'
                            })
                    return matches
        except Exception as e:
            print(f"   东方财富搜索失败: {e}")
        return []
    
    def _search_sina(self, name: str) -> List[Dict]:
        """新浪搜索"""
        try:
            # 新浪财经股票列表
            url = "http://hq.sinajs.cn/list=sh600000,sh600010,sh600015"
            response = requests.get(url, headers=self.headers, timeout=10)
            print(f"   新浪响应: {response.text[:100]}...")
        except Exception as e:
            print(f"   新浪搜索失败: {e}")
        return []
    
    def verify_code(self, code: str) -> Optional[Dict]:
        """
        验证单个股票代码
        
        Args:
            code: 股票代码（如 '600021'）
            
        Returns:
            股票信息或None
        """
        # 确定市场前缀
        if code.startswith('6'):
            market = '1'  # 上海
            market_code = f"sh{code}"
        elif code.startswith('0') or code.startswith('3'):
            market = '0'  # 深圳
            market_code = f"sz{code}"
        else:
            return None
        
        # 东方财富验证接口
        try:
            url = "http://push2.eastmoney.com/api/qt/stock/get"
            params = {
                "secid": f"{market}.{code}",
                "fields": "f57,f58,f2,f3,f4,f5,f6"
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('data'):
                    return {
                        'code': code,
                        'name': data['data'].get('f58', ''),
                        'price': data['data'].get('f2', 0),
                        'change': data['data'].get('f3', 0),
                        'volume': data['data'].get('f6', 0),
                        'source': 'eastmoney'
                    }
        except Exception as e:
            print(f"   验证失败: {e}")
        
        return None
    
    def get_stock_data(self, code: str, days: int = 250) -> Optional[pd.DataFrame]:
        """
        获取股票历史数据
        
        Args:
            code: 股票代码
            days: 获取天数
            
        Returns:
            DataFrame或None
        """
        # 确定市场
        if code.startswith('6'):
            market_code = f"sh{code}"
        elif code.startswith('0') or code.startswith('3'):
            market_code = f"sz{code}"
        else:
            return None
        
        try:
            url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
            params = {
                "_var": "kline_dayqfq",
                "param": f"{market_code},day,,,{days},qfq"
            }
            
            response = requests.get(url, params=params, headers=self.headers, timeout=30)
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
            print(f"获取数据失败: {e}")
        
        return None


def main():
    """主函数 - 验证上海电力"""
    
    print("=" * 60)
    print("股票代码验证工具")
    print("=" * 60)
    
    validator = StockCodeValidator()
    
    # 1. 验证上海电力
    print("\n🔍 验证 '上海电力':")
    result = validator.verify_code('600021')
    
    if result:
        print(f"\n✅ 验证成功!")
        print(f"   代码: {result['code']}")
        print(f"   名称: {result['name']}")
        print(f"   价格: {result['price']}")
        print(f"   涨跌: {result['change']:.2f}%")
        print(f"   来源: {result['source']}")
    else:
        print("\n❌ 验证失败")
    
    # 2. 搜索上海电力
    print("\n🔍 搜索 '上海电力':")
    matches = validator.get_stock_by_name('上海电力')
    
    if matches:
        print(f"\n找到 {len(matches)} 个结果:")
        for m in matches:
            print(f"   {m['code']} - {m['name']} ({m['source']})")
    else:
        print("   未找到")
    
    # 3. 获取历史数据
    print("\n📊 获取历史数据:")
    df = validator.get_stock_data('600021', 250)
    
    if df is not None:
        print(f"   ✅ 获取成功! {len(df)} 行")
        print(f"   日期: {df['date'].min()} ~ {df['date'].max()}")
        print(f"   最新价: {df['close'].iloc[0]}")
    else:
        print("   ❌ 获取失败")
    
    return result


if __name__ == "__main__":
    main()
