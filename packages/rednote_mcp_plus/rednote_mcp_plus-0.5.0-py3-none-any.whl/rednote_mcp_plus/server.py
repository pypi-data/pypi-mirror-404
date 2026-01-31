from mcp.server.fastmcp import FastMCP

from rednote_mcp_plus.write import publish
from rednote_mcp_plus.auth import login
from rednote_mcp_plus.write import interaction
from rednote_mcp_plus.read import dump, search
from typing import Annotated, List

mcp = FastMCP()

@mcp.tool()
async def manualLogin():
    """
    登录小红书账号，获取登录Cookies，保存登录态
    注意：需要手动操作成功登录，并且关闭浏览器后才会保存Cookies
    """
    result = await login.manualLogin()
    return result

@mcp.tool()
async def likeNote(
    noteUrl: Annotated[str, "笔记URL"]
) -> str:
    """
    点赞小红书笔记
    :param noteUrl: 笔记URL
    :return: 点赞结果
    """
    result = await interaction.likeNote(noteUrl)
    return result

@mcp.tool()
async def collectNote(
    noteUrl: Annotated[str, "笔记URL"]
) -> str:
    """
    收藏小红书笔记
    :param noteUrl: 笔记URL
    :return: 收藏结果
    """
    result = await interaction.collectNote(noteUrl)
    return result

@mcp.tool()
async def commentNote(
    noteUrl: Annotated[str, "笔记URL"],
    commentText: Annotated[str, "评论内容"]
) -> str:
    """
    评论小红书笔记
    :param noteUrl: 笔记URL
    :param commentText: 评论内容
    :return: 评论结果
    """
    result = await interaction.commentNote(noteUrl, commentText)
    return result

@mcp.tool()
async def followUser(
    noteUrl: Annotated[str, "笔记URL"]
) -> str:
    """
    关注小红书用户
    :param noteUrl: 笔记URL
    :return: 关注结果
    """
    result = await interaction.followUser(noteUrl)
    return result

@mcp.tool()
async def searchNotes(
    keyWord: Annotated[str, "搜索关键词"],
    topN: Annotated[int, "返回前N个结果,不大于10"],
    dump: Annotated[bool, "是否导出为Markdown文件"]
) -> str:
    """
    搜索小红书笔记
    :param keyWord: 搜索关键词
    :param topN: 返回前N个结果,不大于10
    :param dump: 是否导出为Markdown文件
    :return: 搜索结果的Markdown内容
    """
    result = await search.search(keyWord, topN, dump)
    return result

@mcp.tool()
async def dumpNote(
    noteUrl: Annotated[str, "笔记URL"]
) -> str:
    """
    导出小红书笔记内容
    :param noteUrl: 笔记URL
    :return: 笔记的Markdown内容
    """
    result = await dump.dumpNote(noteUrl)
    return result

@mcp.tool()
async def publishText(
    image_urls: Annotated[List[str], "图片URL列表"],
    title: Annotated[str, "笔记标题"],
    content: Annotated[str, "笔记内容"],
    tags: Annotated[List[str], "标签列表"]
) -> str:
    """
    发布小红书图文笔记
    :param image_urls: 图片URL列表
    :param title: 笔记标题
    :param content: 笔记内容
    :param tags: 标签列表
    :return: 发布结果
    """
    result = await publish.publishText(image_urls, title, content, tags)
    return result

if __name__ == "__main__":
    mcp.run(transport='stdio') 
