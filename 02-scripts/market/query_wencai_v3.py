#!/usr/bin/env python3
"""
直接连接 WSL 中的 Chrome 查询问财
"""

import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import csv


async def main():
    # 选股条件
    query = "所属行业为近期热门版块 且近10日有放量上涨 且最近3日成交量明显萎缩 且股价在20日均线上方 且非ST股 且非创业板非科创板非北交所"
    
    encoded = urllib.parse.quote(query)
    url = f"https://www.iwencai.com/unifywap/home/index?w={encoded}"
    
    print(f"查询: {query}")
    print(f"URL: {url}")
    print("-" * 50)
    
    async with async_playwright() as p:
        # 连接到本地 Chrome (端口 9222)
        browser = await p.chromium.connect_over_cdp("ws://127.0.0.1:9222")
        
        # 获取或创建页面
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 访问页面
        print("1. 访问问财首页...")
        await page.goto("https://www.iwencai.com/", wait_until="networkidle", timeout=30000)
        print(f"   标题: {await page.title()}")
        
        print("2. 访问查询页...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        await asyncio.sleep(3)
        
        title = await page.title()
        print(f"   标题: {title}")
        
        # 截图
        await page.screenshot(path="/root/.openclaw/workspace/wencai_result.png", full_page=True)
        print("   截图已保存")
        
        # 获取内容
        content = await page.content()
        text = await page.inner_text("body")
        
        print(f"\nHTML 长度: {len(content)}")
        print(f"文本长度: {len(text)}")
        
        # 保存
        with open("/root/.openclaw/workspace/wencai_result.html", "w", encoding="utf-8") as f:
            f.write(content)
        print("HTML 已保存")
        
        # 尝试提取股票
        try:
            table = await page.query_selector("table")
            if table:
                rows = await table.query_selector_all("tr")
                print(f"\n表格行数: {len(rows)}")
                
                results = []
                for row in rows[:15]:
                    cells = await row.query_selector_all("td, th")
                    row_texts = [await c.inner_text() for c in cells]
                    results.append([t.strip() for t in row_texts])
                    if len(results) <= 10:
                        print(f"  {len(results)}: {row_texts[:4]}")
                
                # 保存 CSV
                with open("/root/.openclaw/workspace/wencai_result.csv", "w", encoding="utf-8-sig", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerows(results)
                print(f"\nCSV 已保存 ({len(results)} 行)")
            else:
                print("\n未找到表格")
                print(f"页面文本:\n{text[:500]}")
        except Exception as e:
            print(f"提取失败: {e}")
        
        await browser.close()
        print("\n完成!")


if __name__ == "__main__":
    asyncio.run(main())
