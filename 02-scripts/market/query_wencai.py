#!/usr/bin/env python3
"""
问财选股查询脚本
使用 mcp_query_table 查询符合用户条件的股票
"""

import asyncio
import sys
import os

# 添加 mcp_query_table 到路径
try:
    from mcp_query_table import query, BrowserManager, QueryType, Site
except ImportError:
    print("请先安装: pip install mcp_query_table")
    sys.exit(1)


async def main():
    # 用户的选股条件
    query_text = "所属行业为近期热门版块 且近10日有放量上涨 且最近3日成交量明显萎缩 且股价在20日均线上方 且非ST股 且非创业板非科创板非北交所"
    
    # 连接到用户的 Chrome（chrome-lan profile 使用端口 18792）
    # 或使用环境变量 CHROME_CDP_ENDPOINT 指定
    endpoint = os.environ.get("CHROME_CDP_ENDPOINT", "http://127.0.0.1:18792")
    
    print(f"连接 Chrome CDP: {endpoint}")
    print(f"查询条件: {query_text}")
    print("-" * 50)
    
    try:
        # 使用 BrowserManager 连接浏览器
        async with BrowserManager(endpoint=endpoint, executable_path=None, devtools=True) as bm:
            page = await bm.get_page()
            
            # 查询问财
            df = await query(
                page, 
                query_text, 
                query_type=QueryType.Stock,  # 查询股票
                max_page=1,  # 只查第一页
                site=Site.THS  # 使用同花顺问财
            )
            
            # 输出结果
            print("\n查询结果:")
            print(df.to_markdown())
            
            # 保存到文件
            result_file = "/root/.openclaw/workspace/wencai_result.csv"
            df.to_csv(result_file, index=False, encoding="utf-8-sig")
            print(f"\n结果已保存到: {result_file}")
            
            bm.release_page(page)
            
    except Exception as e:
        print(f"错误: {e}")
        print("\n提示: 请确保 Chrome 已开启 CDP 调试端口:")
        print("  1. 关闭所有 Chrome 窗口")
        print("  2. 使用命令启动: chrome --remote-debugging-port=9222")
        print("  3. 或在 Windows: 'C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe' --remote-debugging-port=9222")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
