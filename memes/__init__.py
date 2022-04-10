import shlex
import traceback
from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.typing import T_Handler
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import Message, MessageSegment, unescape
from nonebot.log import logger

from .models import NormalMeme
from .download import DownloadError
from .utils import help_image
from .normal_meme import normal_memes
from .gif_subtitle_meme import gif_subtitle_memes

__zx_plugin_name__ = "表情包制作"
__plugin_usage__ = """
usage：
示例：鲁迅说 我没说过这句话
示例：王境泽 我就是饿死 死外边 不会吃你们一点东西 真香
发送“表情包制作”查看支持的指令
""".strip()
__plugin_des__ = "生成各种表情"
__plugin_type__ = ("群内小游戏",)
__plugin_cmd__ = [
]
__plugin_author__ = "MeetWq佬!!!!!!!!!!!!!！"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": [
    ],
}

__plugin_block_limit__ = {"rst": "baka！没那么快！"}




help_cmd = on_command("表情包制作", block=True, priority=5)

memes = normal_memes + gif_subtitle_memes


@help_cmd.handle()
async def _():
    img = await help_image(memes)
    if img:
        await help_cmd.finish(MessageSegment.image(img))


async def handle(matcher: Matcher, meme: NormalMeme, text: str):
    arg_num = meme.arg_num
    if arg_num == 1:
        texts = [text]
    else:
        try:
            texts = shlex.split(text)
        except:
            await matcher.finish(f"参数解析错误，若包含特殊符号请转义或加引号")

    if len(texts) < arg_num:
        await matcher.finish(f"该表情包需要输入{arg_num}段文字")
    elif len(texts) > arg_num:
        await matcher.finish(f"参数数量不符，需要输入{arg_num}段文字，若包含空格请加引号")

    try:
        res = await meme.func(texts)
    except DownloadError:
        logger.warning(traceback.format_exc())
        await matcher.finish("资源下载出错，请稍后再试")
    except:
        logger.warning(traceback.format_exc())
        await matcher.finish("出错了，请稍后再试")

    if isinstance(res, str):
        await matcher.finish(res)
    else:
        await matcher.finish(MessageSegment.image(res))


def create_matchers():
    def create_handler(meme: NormalMeme) -> T_Handler:
        async def handler(matcher: Matcher, msg: Message = CommandArg()):
            text = unescape(msg.extract_plain_text()).strip()
            if not text:
                await matcher.finish()
            await handle(matcher, meme, text)

        return handler

    for meme in memes:
        on_command(
            meme.keywords[0], aliases=set(meme.keywords), block=True, priority=5
        ).append_handler(create_handler(meme))


create_matchers()
