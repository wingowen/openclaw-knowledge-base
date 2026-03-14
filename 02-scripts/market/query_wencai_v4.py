#!/usr/bin/env python3
"""
用 Playwright 直接启动 Chrome 查询问财
"""

import asyncio
from playwright.async_api import async_playwright
import urllib.parse
import csv


async def main():
    query = "所属行业为近期热门版块 且近10日有放量上涨 且最近3日成交量明显萎缩 且股价在20日均线上方 且非ST股 且非创业板非科创板非北交所"
    
    encoded = urllib.parse.quote(query)
    url = f"https://www.iwencai.com/unifywap/home/index?w={encoded}"
    
    print(f"查询: {query}")
    print(f"URL: {url}")
    print("-" * 50)
    
    async with async_playwright() as p:
        # 直接启动 Chrome
        browser = await p.chromium.launch(
            headless=True,
            executable_path="/usr/bin/google-chrome-stable",
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox", 
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--window-size=1920,1080",
                "--start-maximized",
            ]
        )
        
        # 创建上下文
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
        )
        
        page = await context.new_page()
        
        # 访问首页
        print("1. 访问首页...")
        await page.goto("https://www.iwencai.com/", wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(2)
        print(f"   标题: {await page.title()}")
        
        # 访问查询页
        print("2. 执行查询...")
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await asyncio.sleep(5)
        
        title = await page.title()
        print(f"   标题: {title}")
        
        # 截图
        await page.screenshot(path="/root/.openclaw/workspace/wencai_result.png", full_page=True)
        print("   截图已保存")
        
        # 保存 HTML
        content = await page.content()
        with open("/root/.openclaw/workspace/wencai_result.html", "w", encoding="utf-8") as f:
            f.write(content)
        
        # 获取文本
        text = await page.inner_text("body")
        print(f"   HTML: {len(content)} 字符, 文本: {len(text)} 字符")
        
        # 查找股票表格
        print("\n3. 提取数据...")
        tables = await page.query_selector_all("table")
        print(f"   找到 {len(tables)} 个表格")
        
        results = []
        for table in tables[:3]:  # 只检查前3个表格
            rows = await table.query_selector_all("tr")
            for row in rows:
                cells = await row.query_selector_all("td, th")
                if cells:
                    row_texts = [await c.inner_text() for c in cells]
                    results.append([t.strip()[:20] for t in row_texts])
        
        print(f"   提取 {len(results)} 行数据")
        
        # 显示前10行
        for i, row in enumerate(results[:10]):
            print(f"   {i}: {' | '.join(row[:5])}")
        
        # 保存 CSV
        if results:
            with open("/root/.openclaw/workspace/wencai_result.csv", "w", encoding="utf-8-sig", newline="") as f:
                writer = csv.writer(f)
                writer.writerows(results)
            print(f"\nCSV 已保存: /root/.openclaw/workspace/wencai_result.csv")
        
        await browser.close()
        print("\n完成!")


if __name__ == "__main__":
    asyncio.run(main())
