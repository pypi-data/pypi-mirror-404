import re
from typing import List
from playwright.async_api import async_playwright
import asyncio

class RednoteArticle:
    def __init__(self, title: str, content: str, tags: List[str], image_urls: List[str]):
        self.title = title
        self.content = content
        self.tags = tags
        self.image_urls = image_urls

    def __str__(self):
        return f"标题: {self.title}, 内容: {self.content}, 标签: {', '.join(self.tags)}, 图片: {', '.join(self.image_urls)}"

    def __repr__(self):
        return self.__str__()


async def publishText(image_urls: List[str], title: str, content: str, tags: List[str]) -> str:
    """
    发布小红书图文笔记
    :param image_urls: 图片URL列表
    :param title: 笔记标题
    :param content: 笔记内容
    :param tags: 标签列表
    """
    rednoteArticle = RednoteArticle(title, content, tags, image_urls)
    
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(storage_state="src/rednote_mcp_plus/cookie/rednote_cookies.json")
        page = await context.new_page()
        await page.goto("https://www.xiaohongshu.com/explore")
        print("🌐 导航到小红书主页...")
        await page.wait_for_timeout(10000)
        login_button = page.locator("form").get_by_role("button", name="登录")
        if(await login_button.is_visible()):
            return "❌ 未登录小红书，请先登录"
        
        await page.get_by_role("button", name="创作中心").hover()
        async with page.expect_popup() as page1_info:
            await page.get_by_role("link", name="创作服务").click()
            
        page1 = await page1_info.value
        print("🕒 等待页面跳转")
        
        await page1.get_by_text("发布图文笔记").click()
        
        # with page1.expect_file_chooser() as fc_info:
        #     page1.get_by_role("button", name="Choose File").click()
        # file_chooser = fc_info.value
        # file_chooser.set_files(image_urls)
        
        print("🖼️ 上传图片...")
        page1.on("filechooser", lambda file_chooser: file_chooser.set_files(rednoteArticle.image_urls)) # 替换为你的文件路径
        
        await page1.get_by_role("textbox", name="填写标题会有更多赞哦～").fill(rednoteArticle.title)
        final_content = rednoteArticle.content + "\n\n" + "\n".join([f"#{tag}" for tag in rednoteArticle.tags])
        await page1.get_by_role("paragraph").filter(has_text=re.compile(r"^$")).fill(final_content)
        await page1.wait_for_timeout(10000) # 等待发布内容加载完成
        await page1.get_by_role("button", name="发布").click()
        print("🕒 等待发布成功")
        await page1.wait_for_timeout(5000) # 等待发布完成
        print("✅ 发布成功")
        
        # ---------------------
        await context.close()
        await browser.close()
        
        return "✅ 笔记发布成功"

if __name__ == "__main__":
    result = asyncio.run(publishText(
        image_urls=["src/rednote_mcp_plus/static/images/ball.png"],
        title="这是一个测试标题",
        content="这是一个测试内容",
        tags=["测试", "小红书"]
    ))
    print(result) 