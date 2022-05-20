import shlex
from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.typing import T_Handler
from nonebot.params import CommandArg
from nonebot.adapters.onebot.v11 import MessageSegment, Message

from .data_source import create_logo, commands

__zx_plugin_name__ = "logo制作"
__plugin_usage__ = """
usage：
PornHub
指令：ph /phlogo {left_text} {right_text}
示例：ph Porn Hub
YouTube
指令：yt /ytlogo {left_text} {right_text}
示例：yt You Tube
5000兆円欲しい!
指令：5000兆 {left_text} {right_text}
示例：5000兆 我去 初音未来
抖音
指令：douyin/dylogo {text}
示例：douyin douyin
谷歌
指令：google/gglogo {text}
示例：google Google
""".strip()
__plugin_des__ = "logo"
__plugin_type__ = ("群内小游戏",)
__plugin_cmd__ = [
]
__plugin_settings__ = {
    "cmd": ["logo", "logo制作"],
}
__plugin_block_limit__ = {"rst": "急了急了？"}

__help__plugin_name__ = 'logo'
__des__ = 'pornhub等风格logo生成'
__cmd__ = '''
pornhub：ph {text1} {text2}
youtube：yt {text1} {text2}
5000兆円欲しい!：5000兆 {text1} {text2}
抖音：douyin {text}
谷歌：google {text}
'''.strip()
__short_cmd__ = 'ph、yt、5000兆、douyin'
__example__ = '''
ph Porn Hub
yt You Tube
5000兆 我去 初音未来
douyin douyin
'''.strip()
__usage__ = f'{__des__}\nUsage:\n{__cmd__}\nExample:\n{__example__}'


async def handle(matcher: Matcher, style: str, text: str):
    arg_num = commands[style]['arg_num']
    texts = [text] if arg_num == 1 else shlex.split(text)
    if len(texts) != arg_num:
        await matcher.finish('参数数量不符')

    image = await create_logo(style, texts)
    if image:
        await matcher.finish(MessageSegment.image(image))
    else:
        await matcher.finish('出错了，请稍后再试')


def create_matchers():
    def create_handler(style: str) -> T_Handler:
        async def handler(msg: Message = CommandArg()):
            text = msg.extract_plain_text().strip()
            if not text:
                await matcher.finish()
            await handle(matcher, style, text)

        return handler

    for style, params in commands.items():
        matcher = on_command(style, aliases=params['aliases'],
                             priority=5, block=True)
        matcher.append_handler(create_handler(style))


create_matchers()
