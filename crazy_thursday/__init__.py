from random import choice
import os
from pathlib import Path
from re import match
import nonebot
from nonebot import on_command, on_regex
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, GROUP

__zx_plugin_name__ = "天天疯狂！"
__plugin_usage__ = """
usage：
天天疯狂，疯狂星期[一|二|三|四|五|六|日]；
新增：支持狂乱[月|火|水|木|金|土|日]曜日日文触发；
输入；疯狂星期四帮助以获取疯狂星期四帮助
""".strip()

__plugin_des__ = "天天疯狂，疯狂星期"
__plugin_type__ = ("群内小游戏",)
__plugin_author__ = "KafCoppelia"
__plugin_block_limit__ = {"rst": "疯了疯了！"}

__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["疯狂星期四帮助", "疯狂星期\S" "狂乱\S曜日"],
}

try:
    import ujson as json
except ModuleNotFoundError:
    import json

global_config = nonebot.get_driver().config
if not hasattr(global_config, 'crazy_path'):
    CRAZY_PATH = os.path.join(os.path.dirname(__file__), 'resource')
else:
    CRAZY_PATH = global_config.crazy_path

__crazy_vsrsion__ = 'v0.2.2'
plugin_notes = f'''
KFC疯狂星期四 {__crazy_vsrsion__}
[疯狂星期X] 随机输出KFC疯狂星期四文案
[狂乱X曜日] 随机输出KFC疯狂星期四文案'''.strip()

plugin_help = on_command('疯狂星期四帮助', permission=GROUP, priority=5, block=True)
crazy = on_regex(r'疯狂星期\S', permission=GROUP, priority=5, block=True)
crazy_jp = on_regex(r'狂乱\S曜日', permission=GROUP, priority=5, block=True)

@plugin_help.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    await plugin_help.finish(plugin_notes)

def rndKfc(msg, jp = False):
    day = (match(r'狂乱(\S)曜日', msg) if jp else match(r'疯狂星期(\S)', msg.replace('天', '日'))).group(1)
    tb = ['月', '一', '火', '二', '水', '三', '木', '四', '金', '五', '土', '六', '日', '日']
    if day not in tb:
        return '给个准确时间，OK?'
    idx = int(tb.index(day)/2)*2
    # json数据存放路径
    path = Path(CRAZY_PATH) / 'post.json'
    # 将json对象加载到数组
    with open(path, 'r', encoding='utf-8') as f:
        kfc = json.load(f).get('post')
    # 随机选取数组中的一个对象
    return choice(kfc).replace('星期四', '星期' + tb[idx+1]).replace('周四', '周' + tb[idx+1]).replace('木曜日', tb[idx] + '曜日')

@crazy.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    await crazy.finish(rndKfc(event.get_plaintext()))

@crazy_jp.handle()
async def _(bot: Bot, event: GroupMessageEvent):
    await crazy_jp.finish(rndKfc(event.get_plaintext(), True))
