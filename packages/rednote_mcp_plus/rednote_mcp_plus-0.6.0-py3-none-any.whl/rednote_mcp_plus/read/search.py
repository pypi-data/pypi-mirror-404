from playwright.async_api import async_playwright
import asyncio

from rednote_mcp_plus.read.dump import dumpNote


async def search(keyWord: str, topN: int, dump: bool) -> str:
    """
    搜索小红书笔记
    :param keyWord: 搜索关键词
    :param topN: 返回前N个结果,不大于10
    :param dump: 是否导出为Markdown文件
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="src/rednote_mcp_plus/cookie/rednote_cookies.json")
        page = await context.new_page()
        await page.goto("https://www.xiaohongshu.com/search_result?keyword=" + keyWord)
        print("🌐 导航到小红书主页...")
        await page.wait_for_timeout(3000)
        login_button = page.locator("form").get_by_role("button", name="登录")
        if(await login_button.is_visible()):
            return "❌ 未登录小红书，请先登录"
        
        prefix = 'https://www.xiaohongshu.com'
        links = await page.query_selector_all('a.cover.mask.ld')
        # 获取所有 href 属性
        hrefs = []
        for link in links:
            href = await link.get_attribute('href')
            if href:
                href = prefix + href
                hrefs.append(href)
            if len(hrefs) >= topN:
                break
        markdown_content = []
        for href in hrefs:
            markdown_content.append(await dumpNote(href))
            
        markdown_content = "\n---\n".join(markdown_content)

        if dump:
            with open('red_note_search.md', 'w', encoding='utf-8') as f:
                f.write(markdown_content)

        await browser.close()
        await context.close()
            
        return markdown_content
            
        

if __name__ == "__main__":
    result = asyncio.run(search("测试", 5, True))
    print(result)