import base64
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Event, MessageSegment, Message
from nonebot.typing import T_State
from nonebot.params import CommandArg

from .data_source import *

__zx_plugin_name__ = "字符画"
__plugin_usage__ = """
usage：
    生成字符画
    指令：
        字符画+图片
""".strip()
__plugin_des__ = "字符画"
__plugin_type__ = ("群内小游戏",)
__plugin_cmd__ = ["字符画"]
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["字符画"],
}


pic2text = on_command("字符画", priority=5, block=True)


@pic2text.handle()
async def _(args: Message = CommandArg(), state: T_State):
    for seg in args:
        if seg.type == 'image':
            state['image'] = Message(seg)


@pic2text.got('image', prompt='图呢？')
async def generate_(bot: Bot, event: Event, state: T_State):
    msg = state['image']
    if msg[0].type == "image":
        url = msg[0].data["url"]  # 图片链接
        await pic2text.send("努力生成中...")
        
        pic = await get_img(url)  # 取图
        if not pic:
            await pic2text.finish(event, message="图片未获取到，请稍后再试")

        if pic.format == 'GIF':
            res = await char_gif(pic) 
            await pic2text.finish(
                MessageSegment.image(
                       f"base64://{base64.b64encode(res.getvalue()).decode()}"
                   )
            )
        text = await get_pic_text(pic)
        if text:
            res = await text2img(text)  
            await pic2text.finish(
                MessageSegment.image(
                       f"base64://{base64.b64encode(res.getvalue()).decode()}"
                   )
            )
    else:
        await pic2text.finish('要的是图')
