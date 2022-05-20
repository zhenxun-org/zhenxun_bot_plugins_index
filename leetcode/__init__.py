from nonebot.rule import T_State, to_me
from nonebot import on_command, get_driver
from nonebot.adapters.onebot.v11 import Bot, GroupMessageEvent, Message
from .config import Config
from .data_source import get_leetcode_daily


__zx_plugin_name__ = "今日算法"
__plugin_usage__ = """
usage：
    今日算法
    指令：
       今日算法
""".strip()
__plugin_des__ = "今日算法"
__plugin_type__ = ("群内小游戏",)
__plugin_cmd__ = ["]"]
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["今日算法"],
}
global_config = get_driver().config
config = Config(**global_config.dict())
nickname = list(global_config.nickname)[0]
leetcode = on_command("今日算法", rule=to_me(), priority=6, aliases={"算法"}, block=True)


@leetcode.handle()
async def leetcode_handle(bot: Bot, event: GroupMessageEvent, state: T_State):
    data = await get_leetcode_daily()
    if data != "获取信息失败":
        msg = f"「{nickname}·今日算法」\n[CQ:at,qq={event.get_user_id()}]\n[链接]{data['url']}\n[题目]{data['id']}.{data['title']}\n[难度]{data['difficulty']}\n[描述内容]\n{data['content']}"
        await leetcode.finish(Message(msg))
    else:
        msg = f"「{nickname}·今日算法」\n[CQ:at,qq={event.get_user_id()}]\n{data}"
        await leetcode.finish(Message(msg))
