#!/usr/bin/env python3
"""
使用本地 Chrome 查询问财
"""

import asyncio
from playwright.async_api import async_playwright
import csv


async def query_wencai():
    # 选股条件
    query = "所属行业为近期热门版块 且近10日有放量上涨 且最近3日成交量明显萎缩 且股价在20日均线上方 且非ST股 且非创业板非科创板非北交所"
    
    # URL 编码
    import urllib.parse
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.iwencai.com/unifywap/home/index?w={encoded_query}"
    
    print(f"查询条件: {query}")
    print(f"访问: {url}")
    print("-" * 60)
    
    async with async_playwright() as p:
        # 启动本地 Chrome（无头模式）
        browser = await p.chromium.launch(
            headless=True,
            executable_path="/usr/bin/google-chrome-stable",
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ]
        )
        
        # 创建新页面
        page = await browser.new_page()
        
        # 访问问财
        print("正在加载页面...")
        await page.goto(url, wait_until="networkidle", timeout=60000)
        
        # 等待内容加载
        print("等待数据加载...")
        await asyncio.sleep(5)
        
        # 尝试提取数据
        print("提取股票数据...")
        
        # 方法1: 尝试获取表格
        try:
            # 等待表格出现
            await page.wait_for_selector("table", timeout=10000)
            
            # 提取表格数据
            rows = await page.query_selector_all("table tr")
            print(f"找到 {len(rows)} 行数据")
            
            results = []
            for row in rows:
                cells = await row.query_selector_all("td, th")
                if cells:
                    row_data = []
                    for cell in cells:
                        text = await cell.inner_text()
                        row_data.append(text.strip())
                    results.append(row_data)
            
            # 输出结果
            print("\n查询结果:")
            print("-" * 60)
            for i, row in enumerate(results[:15]):  # 只显示前15行
                print(f"{i}: {' | '.join(row[:5])}")  # 只显示前5列
            
            # 保存到 CSV
            output_file = "/root/.openclaw/workspace/wencai_result.csv"
            with open(output_file, "w", newline="", encoding="utf-8-sig") as f:
                writer = csv.writer(f)
                writer.writerows(results)
            print(f"\n结果已保存到: {output_file}")
            
        except Exception as e:
            print(f"提取表格失败: {e}")
            
            # 方法2: 尝试获取页面文本
            try:
                content = await page.content()
                print(f"\n页面 HTML 长度: {len(content)} 字符")
                
                # 保存 HTML 用于调试
                with open("/root/.openclaw/workspace/wencai_page.html", "w", encoding="utf-8") as f:
                    f.write(content)
                print("HTML 已保存到: /root/.openclaw/workspace/wencai_page.html")
                
                # 尝试获取可见文本
                text = await page.inner_text("body")
                print(f"\n页面可见文本 (前 2000 字符):\n{text[:2000]}")
                
            except Exception as e2:
                print(f"获取页面内容也失败: {e2}")
        
        # 截图
        screenshot_path = "/root/.openclaw/workspace/wencai_screenshot.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"\n截图已保存到: {screenshot_path}")
        
        await browser.close()
        print("\n完成！")


if __name__ == "__main__":
    asyncio.run(query_wencai())
