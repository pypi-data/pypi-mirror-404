import re
from typing import List
from playwright.async_api import async_playwright
import asyncio

async def likeNote(noteUrl: str) -> str:
    """
    点赞小红书笔记
    :param noteUrl: 笔记URL
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="src/rednote_mcp_plus/cookie/rednote_cookies.json")
        page = await context.new_page()
        await page.goto(noteUrl)
        print("🌐 导航到小红书笔记页面...")
        await page.wait_for_timeout(1000)
        login_button = page.locator("form").get_by_role("button", name="登录")
        if(await login_button.is_visible()):
            return "❌ 未登录小红书，请先登录"
        
        await page.locator(".left > .like-wrapper > .like-lottie").click()

        await browser.close()
        await context.close()
            
        return "❤️ 笔记已点赞"

async def collectNote(noteUrl: str) -> str:
    """
    收藏小红书笔记
    :param noteUrl: 笔记URL
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="src/rednote_mcp_plus/cookie/rednote_cookies.json")
        page = await context.new_page()
        await page.goto(noteUrl)
        print("🌐 导航到小红书笔记页面...")
        await page.wait_for_timeout(1000)
        login_button = page.locator("form").get_by_role("button", name="登录")
        if(await login_button.is_visible()):
            return "❌ 未登录小红书，请先登录"
        
        await page.locator(".reds-icon.collect-icon").click()

        await browser.close()
        await context.close()
            
        return "📥 笔记已收藏"

async def commentNote(noteUrl: str, commentText: str) -> str:
    """
    评论小红书笔记
    :param noteUrl: 笔记URL
    :param commentText: 评论内容
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="src/rednote_mcp_plus/cookie/rednote_cookies.json")
        page = await context.new_page()
        await page.goto(noteUrl)
        print("🌐 导航到小红书笔记页面...")
        await page.wait_for_timeout(1000)
        login_button = page.locator("form").get_by_role("button", name="登录")
        if(await login_button.is_visible()):
            return "❌ 未登录小红书，请先登录"
        
        await page.locator(".chat-wrapper > .reds-icon").click()
        await page.locator("#content-textarea").fill(commentText)
        await page.get_by_role("button", name="发送").click()

        await browser.close()
        await context.close()
            
        return "💬 评论已发布"

async def followUser(noteUrl: str) -> str:
    """
    关注小红书用户
    :param noteUrl: 笔记URL
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="src/rednote_mcp_plus/cookie/rednote_cookies.json")
        page = await context.new_page()
        await page.goto(noteUrl)
        print("🌐 导航到小红书笔记页面...")
        await page.wait_for_timeout(1000)
        login_button = page.locator("form").get_by_role("button", name="登录")
        if(await login_button.is_visible()):
            return "❌ 未登录小红书，请先登录"
        
        result = "👤 用户已关注"
        try:
            await page.get_by_role("button", name="关注").click()
        except Exception as e:
            result = "⚠️ 已经关注该用户或无法关注"
            
        await browser.close()
        await context.close()

        return result

if __name__ == "__main__":
    noteUrl = "https://www.xiaohongshu.com/explore/69650e49000000000b01327c?xsec_token=ABv2EGvoPK_6ildvjUhwB5MIhms8PhQyc0IBd4jaXbb1g=&xsec_source=pc_user"
    asyncio.run(likeNote(noteUrl))
    asyncio.run(collectNote(noteUrl))
    asyncio.run(commentNote(noteUrl, "拍得真好！"))
    asyncio.run(followUser(noteUrl))