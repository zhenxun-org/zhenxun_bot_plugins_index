from typing import Type
from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.typing import T_Handler
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message

from .data_source import get_text, commands


__zx_plugin_name__ = "抽象话火星文"
__plugin_usage__ = """
usage：
    抽象话等多种文本生成
    指令：
       抽象话 那真的牛逼
       火星文 那真的牛逼
""".strip()
__plugin_des__ = "抽象话火星文"
__plugin_type__ = ("群内小游戏",)
__plugin_cmd__ = ["]"]
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["抽象话火星文"],
}



async def handle(matcher: Type[Matcher], type: str, text: str):
    res = await get_text(type, text)
    if res:
        await matcher.finish(res)
    else:
        await matcher.finish("出错了，请稍后再试")


def create_matchers():
    def create_handler(type: str) -> T_Handler:
        async def handler(msg: Message = CommandArg()):
            text = msg.extract_plain_text().strip()
            if text:
                await handle(matcher, type, text)

        return handler

    for type, params in commands.items():
        matcher = on_command(
            f"{type}text", aliases=params["aliases"], block=True, priority=5
        )
        matcher.append_handler(create_handler(type))


create_matchers()
