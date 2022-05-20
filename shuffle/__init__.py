from random import shuffle

import jieba
from nonebot import logger, on_command
from nonebot.adapters.onebot.v11 import Message
from nonebot.matcher import Matcher
from nonebot.params import CommandArg

__zx_plugin_name__ = "打乱"
__plugin_usage__ = """
usage：
    打乱
    指令：
       打乱
""".strip()
__plugin_des__ = "打乱"
__plugin_type__ = ("群内小游戏",)
__plugin_cmd__ = [""]
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["打乱"],
}

@on_command('打乱').handle()
async def _(matcher: Matcher, args: Message = CommandArg()):
    cut = list(jieba.cut(args.extract_plain_text()))
    shuffled = cut.copy()
    shuffle(shuffled)
    await matcher.send(f'原句：{"/".join(cut)}\n'
                       f'打乱：{"".join(shuffled)}')


logger.info('初始化结巴分词')
jieba.initialize()
# jieba.enable_paddle()  # py3.10无法使用，需求py3.7

__version__ = '0.1.0'
