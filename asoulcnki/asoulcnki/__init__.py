from nonebot import on_command
from nonebot.typing import T_State
from nonebot.adapters.cqhttp import Bot, Event

from .data_source import check_text

__zx_plugin_name__ = "枝网查重"
__plugin_usage__ = """
usage：
    查找最相似的小作文
    指令：
        查重/枝网查重
""".strip()
__plugin_des__ = "枝网查重"
__plugin_cmd__ = [
    "查重/枝网查重",
]
__plugin_type__ = ("一些工具",)
__plugin_version__ = 1.0
__plugin_author__ = "MeetWq"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": [
        "查重",
        "枝网查重",
    ],
}


asoulcnki = on_command('asoulcnki', aliases={'枝网查重', '查重'})


@asoulcnki.handle()
async def _(bot: Bot, event: Event, state: T_State):
    text = event.get_plaintext().strip()
    if not text:
        await asoulcnki.finish()

    if len(text) >= 1000:
        await asoulcnki.finish('小作文太长啦，长度须在10-1000之间')
    elif len(text) <= 10:
        await asoulcnki.finish('你怎么这么短，长度须在10-1000之间')

    msg = await check_text(text)
    if msg:
        await asoulcnki.finish(msg)
    else:
        await asoulcnki.finish('服务器宕机惹，过会再来吧')
