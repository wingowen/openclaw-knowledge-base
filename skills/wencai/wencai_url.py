#!/usr/bin/env python3
"""问财搜索URL构造器"""

import urllib.parse
import sys


def build_wencai_url(query: str, market: str = "stock") -> str:
    """
    构造问财搜索URL
    
    Args:
        query: 自然语言筛选条件
        market: 市场类型 (stock/etf/index等)
    
    Returns:
        完整的问财搜索URL
    """
    encoded_query = urllib.parse.quote(query)
    return f"https://www.iwencai.com/unifiedwap/result?w={encoded_query}&querytype={market}"


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python wencai_url.py <筛选条件>")
        print("示例: python wencai_url.py '近10日放量上涨，非ST'")
        sys.exit(1)
    
    query = " ".join(sys.argv[1:])
    url = build_wencai_url(query)
    print(url)
