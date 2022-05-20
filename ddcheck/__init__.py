import traceback
from loguru import logger
from nonebot import on_command
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.log import logger

from .data_source import get_reply

__zx_plugin_name__ = "成分姬"
__plugin_usage__ = """
usage：
查成分 {用户名/UID}
示例：查成分 小南莓Official
""".strip()
__plugin_des__ = "成分姬"
__plugin_type__ = ("一些工具",)
__plugin_cmd__ = ["查成分 {用户名/UID}"]
__plugin_author__ = "wq!!!!"

__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["查成分 {用户名/UID}"],
}

ddcheck = on_command("查成分", block=True, priority=5)


@ddcheck.handle()
async def _(msg: Message = CommandArg()):
    text = msg.extract_plain_text().strip()
    if not text:
        await ddcheck.finish()

    try:
        res = await get_reply(text)
    except:
        logger.warning(traceback.format_exc())
        await ddcheck.finish("出错了，请稍后再试")

    if isinstance(res, str):
        await ddcheck.finish(res)
    else:
        await ddcheck.finish(MessageSegment.image(res))
