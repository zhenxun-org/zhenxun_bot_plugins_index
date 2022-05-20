import traceback
from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.typing import T_Handler
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message
from nonebot.log import logger

from .data_source import sources, Source

__zx_plugin_name__ = "点歌1"
__plugin_usage__ = """
usage：
    点歌
    指令：
        点歌/qq点歌/网易点歌/酷我点歌/酷狗点歌/咪咕点歌/b站点歌 + 关键词，默认为qq点歌
""".strip()
__plugin_des__ = "点歌1"
__plugin_type__ = ("功能",)
__plugin_cmd__ = ["点歌"]
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["点歌", ],
}




def create_matchers():
    def create_handler(source: Source) -> T_Handler:
        async def handler(matcher: Matcher, msg: Message = CommandArg()):
            keyword = msg.extract_plain_text().strip()
            if keyword:
                try:
                    res = await source.func(keyword)
                except:
                    logger.warning(traceback.format_exc())
                    await matcher.finish("出错了，请稍后再试")

                if res:
                    await matcher.finish(res)

        return handler

    for source in sources:
        matcher = on_command(
            source.keywords[0],
            aliases=set(source.keywords),
            block=True,
            priority=12,
        )
        matcher.append_handler(create_handler(source))


create_matchers()
