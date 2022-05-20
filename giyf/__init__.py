from nonebot import on_startswith
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent
from nonebot.adapters.onebot.v11.permission import GROUP

from . import config_manager
from .config import Config
from .data_source import search_handle

__zx_plugin_name__ = "快速搜索"
__plugin_usage__ = """
usage：
前缀 关键词
添加：search.add，search.add.global
删除：search.delete，search.delete.global
列表：search.list，search.list.global
""".strip()
__plugin_des__ = "功能"
__plugin_type__ = ("一些工具",)
__plugin_cmd__ = ["快速搜索"]

__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["快速搜索"],
}


search = on_startswith(("?", "？"), permission=GROUP)


@search.handle()
async def _search(bot: Bot, event: GroupMessageEvent):
    await search_handle(bot, event)
