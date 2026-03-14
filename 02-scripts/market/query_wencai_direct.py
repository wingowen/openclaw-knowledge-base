#!/usr/bin/env python3
"""
直接使用 Playwright 查询问财
无需依赖 mcp_query_table MCP 工具
"""

import asyncio
from playwright.async_api import async_playwright
import os


async def query_wencai():
    # 选股条件
    query = "所属行业为近期热门版块 且近10日有放量上涨 且最近3日成交量明显萎缩 且股价在20日均线上方 且非ST股 且非创业板非科创板非北交所"
    
    # 编码条件
    encoded_query = query.replace(" ", "%20").replace("，", "%EF%BC%8C")
    url = f"https://www.iwencai.com/unifywap/home/index?w={encoded_query}"
    
    print(f"访问: {url}")
    
    # 启动浏览器（使用用户现有的 Chrome CDP 连接）
    cdp_endpoint = os.environ.get("CHROME_CDP_ENDPOINT", "ws://127.0.0.1:18792")
    
    async with async_playwright() as p:
        # 连接到现有的 Chrome
        browser = await p.chromium.connect_over_cdp(cdp_endpoint)
        
        # 获取页面
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        # 导航到问财
        await page.goto(url)
        
        # 等待结果加载
        await page.wait_for_load_state("networkidle")
        
        # 等待一下让内容完全加载
        await asyncio.sleep(3)
        
        # 获取页面标题
        title = await page.title()
        print(f"页面标题: {title}")
        
        # 尝试提取股票表格
        try:
            # 查找表格
            tables = await page.query_selector_all("table")
            print(f"找到 {len(tables)} 个表格")
            
            # 提取第一个表格的数据
            if tables:
                table = tables[0]
                rows = await table.query_selector_all("tr")
                
                if rows:
                    print("\n股票列表:")
                    print("-" * 60)
                    
                    # 提取前10行
                    for i, row in enumerate(rows[:11]):  # 标题 + 10行数据
                        cells = await row.query_selector_all("td, th")
                        cell_texts = []
                        for cell in cells:
                            text = await cell.inner_text()
                            cell_texts.append(text.strip()[:30])  # 限制每个单元格长度
                        
                        if cell_texts:
                            print(f"{i}: {' | '.join(cell_texts)}")
                    
                    # 保存到文件
                    with open("/root/.openclaw/workspace/wencai_result.txt", "w", encoding="utf-8") as f:
                        for row in rows:
                            cells = await row.query_selector_all("td, th")
                            cell_texts = [await cell.inner_text() for cell in cells]
                            f.write(" | ".join(cell_texts) + "\n")
                    
                    print(f"\n结果已保存到: /root/.openclaw/workspace/wencai_result.txt")
            
        except Exception as e:
            print(f"提取表格失败: {e}")
        
        # 获取页面 HTML（用于调试）
        html = await page.content()
        print(f"\n页面HTML长度: {len(html)} 字符")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(query_wencai())
