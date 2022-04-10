from nonebot import on_command
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters.onebot.v11.event import Event
import requests

__zx_plugin_name__ = "来个猫猫"
__plugin_usage__ = """
usage：
来个猫猫
""".strip()
__plugin_des__ = "来个猫猫"
__plugin_type__ = ("一些工具",)
__plugin_cmd__ = ["来个猫猫"]

__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["来个猫猫"],
}


miao=on_command("来个猫猫")
@miao.handle()
async def hf(bot:Bot,ev:Event):
    import requests
    img=requests.get("http://edgecats.net/")
    await bot.send(event=ev,message=MessageSegment.image(img.content))