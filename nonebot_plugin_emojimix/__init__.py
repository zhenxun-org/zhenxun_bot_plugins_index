from nonebot import on_regex
from nonebot.params import RegexDict
from nonebot.adapters.onebot.v11 import MessageSegment
from .data_source import mix_emoji


__zx_plugin_name__ = "emojimix"
__plugin_usage__ = """
usage：
    emoji合成器
    指令：
        {emoji1}+{emoji2}
""".strip()
__plugin_des__ = "emoji合成器"
__plugin_type__ = ("功能",)
__plugin_cmd__ = ["{emoji1}+{emoji2}"]
__plugin_version__ = 0.1
__plugin_author__ = "MeetWq"

__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["{emoji1}+{emoji2}"],
}


pattern = "[\u200d-\U0001fab5]"
emojimix = on_regex(
    rf"^(?P<code1>{pattern})\s*\+\s*(?P<code2>{pattern})$", block=True, priority=5)





@emojimix.handle()
async def _(msg: dict = RegexDict()):
    emoji_code1 = msg["code1"]
    emoji_code2 = msg["code2"]
    result = await mix_emoji(emoji_code1, emoji_code2)
    if isinstance(result, str):
        await emojimix.finish(result)
    else:
        await emojimix.finish(MessageSegment.image(result))
