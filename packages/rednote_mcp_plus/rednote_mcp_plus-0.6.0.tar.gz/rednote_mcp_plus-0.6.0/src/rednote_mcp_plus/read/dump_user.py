import json
import re
from playwright.async_api import async_playwright
import asyncio
from datetime import datetime

async def dumpUser(userUrl: str) -> str:
    """
    导出小红书用户信息
    :param userUrl: 用户主页URL
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="src/rednote_mcp_plus/cookie/rednote_cookies.json")
        page = await context.new_page()
        await page.goto(userUrl)
        print("🌐 导航到小红书用户主页...")
        await page.wait_for_timeout(1000)
        login_button = page.locator("form").get_by_role("button", name="登录")
        if(await login_button.is_visible()):
            return "❌ 未登录小红书，请先登录"
        
        # 获取 HTML 内容
        html = await page.content()

        # 正则提取 JSON 字符串
        match = re.search(
            r'window\.__INITIAL_STATE__\s*=\s*({.*?})(?=</script>)', 
            html, 
            re.DOTALL
        )

        data = {}
        if match:
            json_str = match.group(1)
            cleaned_str = re.sub(r'\bundefined\b', 'null', json_str)
            data = json.loads(cleaned_str)
          
        user_info = data.get('user', {}).get('userInfo', {})
        if not user_info:
            return "❌ 未能提取到用户信息，请检查URL或登录状态"
        nickname = user_info.get('nickname', '未知用户')
        desc = user_info.get('desc', '无简介')
        
        user_page_data = data.get('user', {}).get('userPageData', {})
        tags = user_page_data.get('tags', [])
        tag_list = [tag.get('name', '') for tag in tags]
        
        interactions = user_page_data.get('interactions', {})
        interactions_info = [interaction['name'] + ":" + interaction['count'] for interaction in interactions]
        
        result = f"📋 用户信息:\n昵称: {nickname}\n简介: {desc}\n标签: {', '.join(tag_list)}\n互动信息: {', '.join(interactions_info)}"
        return result   
    
if __name__ == "__main__":
    url='https://www.xiaohongshu.com/user/profile/63d944e20000000026012158?xsec_token=AB9u7T-ZtG7Qt-PFS7HbIfqFCZcnXEUI4baNtc9ac9de4=&xsec_source=pc_note'
    result = asyncio.run(dumpUser(url))