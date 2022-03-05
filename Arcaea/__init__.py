import asyncio
from services.log import logger
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageEvent,
    GroupMessageEvent,
)
from nonebot import on_command
from nonebot.typing import T_State
from nonebot.adapters.onebot.v11.permission import GROUP
from nonebot.params import CommandArg, ArgStr

from .sql import asql
from .api import *
from .draw import *

__zx_plugin_name__ = "Arcaea查分器"
__plugin_usage__ = """
usage：
    Arcaea查分器
    指令：
        arcinfo 查询b30，需等待1-2分钟
        arcre   使用本地查分器查询最近一次游玩成绩
        arcre:  指令结尾带：使用est查分器查询最近一次游玩成绩
        arcre: [arcid]  使用好友码查询TA人
        arcre: [@]  使用@ 查询好友
        
        arcbind [arcid] [arcname]   绑定用户
        arcun   解除绑定
        arcrd [定数] [难度] 随机一首该定数的曲目，例如：`arcrd 10.8`，`arcrd 10+`，`arcrd 9+ byd`
""".strip()
__plugin_superuser_usage__ = """
usage：
    超级用户额外的 Arc 指令
    指令：
        arcup   查询用账号添加完好友，使用该指令绑定查询账号，添加成功即可使用arcre指令
""".strip()
__plugin_des__ = "Arcaea查分器"
__plugin_cmd__ = [
    "arcbind [arcid] [arcname]",
    "arcinfo",
    "arcre",
    "arcre: ?*[arcid/@]",
    "arcun",
]
__plugin_type__ = ("一些工具",)
__plugin_version__ = 0.1
__plugin_author__ = "AkashiCoin"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["arcaea", "Arcaea", "arcaea查分器", "Arcaea查分器"],
}
__plugin_block_limit__ = {"rst": "您有arc数据正在处理，请稍等..."}

diffdict = {
    "0": ["pst", "past"],
    "1": ["prs", "present"],
    "2": ["ftr", "future"],
    "3": ["byd", "beyond"],
}

arcinfo = on_command("arcinfo", aliases={"ARCINFO", "Arcinfo"}, priority=5, block=True)


@arcinfo.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State, arg: Message = CommandArg()):
    qqid = event.user_id
    msg = arg.extract_plain_text().strip()
    msg_m = event.get_message()
    if isinstance(event, GroupMessageEvent):
        for msg_seg in msg_m:
            if msg_seg.type == "at":
                qqid = msg_seg.data["qq"]
                break
    result = asql.get_user(qqid)
    if msg:
        if msg.isdigit() and len(msg) == 9:
            arcid = msg
        else:
            await arcinfo.finish("仅可以使用好友码查询", at_sender=True)
    elif not result:
        await arcinfo.finish(
            "该账号尚未绑定，请输入 arcbind arcid(好友码) arcname(用户名)", at_sender=True
        )
    else:
        arcid = result[0]
    await arcinfo.send("正在查询，请耐心等待...")
    info = await draw_info(arcid)
    await arcinfo.send(info, at_sender=True)


arcre = on_command("arcre", aliases={"Arcre", "ARCRE"}, priority=5, block=True)


@arcre.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State, arg: Message = CommandArg()):
    qqid = event.user_id
    est = False
    msg = arg.extract_plain_text().strip()
    msg_m = event.get_message()
    if isinstance(event, GroupMessageEvent):
        for msg_seg in msg_m:
            if msg_seg.type == "at":
                qqid = msg_seg.data["qq"]
                break
    result = asql.get_user(qqid)
    if msg:
        if msg.isdigit() and len(msg) == 9:
            result = asql.get_user_code(msg)
            if not result:
                await arcre.finish(
                    "该账号尚未绑定，请输入 arcbind arcid(好友码) arcname(用户名)", at_sender=True
                )
            user_id = result[0]
        elif msg == ":" or msg == "：":
            if not result:
                await arcre.finish(
                    "该账号尚未绑定，请输入 arcbind arcid(好友码) arcname(用户名)", at_sender=True
                )
            else:
                est = True
                user_id = result[0]
        elif ":" in msg or "：" in msg:
            user_id = msg[1:]
            if user_id.isdigit() and len(user_id) == 9:
                est = True
            else:
                await arcre.finish("请输入正确的好友码", at_sender=True)
        else:
            await arcre.finish("仅可以使用好友码查询", at_sender=True)
    elif not result:
        await arcre.finish(
            "该账号尚未绑定，请输入 arcbind arcid(好友码) arcname(用户名)", at_sender=True
        )
    elif result[1] == None:
        await arcre.finish("该账号已绑定但尚未添加为好友，请联系BOT管理员添加好友并执行 arcup 指令", at_sender=True)
    else:
        user_id = result[1]
    info = await draw_score(user_id, est)
    await arcre.send(info, at_sender=True)


arcrd = on_command("arcrd", aliases={"ARCRD", "Arcrd"}, priority=5, block=True)


@arcrd.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State, arg: Message = CommandArg()):
    args: list[str] = arg.extract_plain_text().strip().split()
    diff = None
    if not args:
        await arcrd.finish("请输入定数", at_sender=False)
    elif len(args) == 1:
        try:
            rating = float(args[0]) * 10
            if not 10 <= rating < 116:
                await arcrd.finish("请输入定数：1-11.5 | 9+ | 10+")
            plus = False
        except ValueError:
            if "+" in args[0] and args[0][-1] == "+":
                rating = float(args[0][:-1]) * 10
                if rating % 10 != 0:
                    await arcrd.finish("仅允许定数为：9+ | 10+")
                if not 90 <= rating < 110:
                    await arcrd.finish("仅允许定数为：9 | 10")
                plus = True
            else:
                await arcrd.finish("请输入定数：1-11.5 | 9+ | 10+")
    elif len(args) == 2:
        try:
            rating = float(args[0]) * 10
            plus = False
            if not 10 <= rating < 116:
                await arcrd.finish("请输入定数：1-11.5 | 9+ | 10+")
            if args[1].isdigit():
                if args[1] not in diffdict:
                    await arcrd.finish("请输入正确的难度：3 | byd | beyond")
                else:
                    diff = int(args[1])
            else:
                for d in diffdict:
                    if args[1].lower() in diffdict[d]:
                        diff = int(d)
                        break
        except ValueError:
            if "+" in args[0] and args[0][-1] == "+":
                rating = float(args[0][:-1]) * 10
                if rating % 10 != 0:
                    await arcrd.finish("仅允许定数为：9+ | 10+")
                if not 90 <= rating < 110:
                    await arcrd.finish("仅允许定数为：9 | 10")
                plus = True
                if args[1].isdigit():
                    if args[1] not in diffdict:
                        await arcrd.finish("请输入正确的难度：3 | byd | beyond")
                    else:
                        diff = int(args[1])
                else:
                    for d in diffdict:
                        if args[1].lower() in diffdict[d]:
                            diff = int(d)
                            break
            else:
                await arcrd.finish("请输入定数：1-11.5 | 9+ | 10+")
    else:
        await arcrd.finish("请输入正确参数")
    if not rating >= 70 and (diff == "2" or diff == "3"):
        await arcrd.finish("ftr | byd 难度没有定数小于7的曲目")
    msg = random_music(rating, plus, diff)
    await arcrd.send(msg)


arcup = on_command("arcup", aliases={"arcupdate", "Arcup"}, priority=5, block=True)


@arcup.handle()
async def _arcup(bot: Bot, event: MessageEvent, state: T_State):
    if str(event.user_id) not in bot.config.superusers:
        await arcup.finish("请联系BOT管理员更新")
    msg = await newbind(bot)
    await arcup.send(msg, at_sender=True)


arcbind = on_command(
    "arcbind", permission=GROUP, aliases={"ARCBIND", "Arcbind"}, priority=5, block=True
)


@arcbind.handle()
async def _(bot: Bot, event: GroupMessageEvent, state: T_State, arg: Message = CommandArg()):
    qqid = event.user_id
    gid = event.group_id
    arcid = arg.extract_plain_text().strip().split()
    try:
        if not arcid[0].isdigit() and len(arcid[0]) != 9:
            await arcbind.finish(
                "请重新输入好友码和用户名\n例如：arcbind 114514810 sb616", at_sender=True
            )
        elif not arcid[1]:
            await arcbind.finish(
                "请重新输入好友码和用户名\n例如：arcbind 114514810 sb616", at_sender=True
            )
    except IndexError:
        await arcbind.finish("请重新输入好友码和用户名\n例如：arcbind 114514810 sb616", at_sender=True)
    result = asql.get_user(qqid)
    if result:
        await arcbind.finish("您已绑定，如需要解绑请输入arcun", at_sender=True)
    isTrue = f"请在10秒内再次确认您的账号是否正确，如不正确请输入arcun解绑\nArcid: {arcid[0]}\nArcname：{arcid[1]}"
    await arcbind.send(isTrue, at_sender=True)
    await asyncio.sleep(10)
    msg = bindinfo(qqid, arcid[0], arcid[1], gid)
    await arcbind.send(msg, at_sender=True)
    await bot.send_private_msg(
        user_id=int(list(bot.config.superusers)[0]),
        message=f"Code:{arcid[0]}\nName:{arcid[1]}\n申请加为好友",
    )


arcun = on_command("arcun", aliases={"ARCUN", "Arcun"}, priority=5, block=True)


@arcun.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    qqid = event.user_id
    result = asql.get_user(qqid)
    if result:
        if asql.delete_user(qqid):
            msg = "解绑成功"
        else:
            msg = "数据库错误"
    else:
        msg = "您未绑定，无需解绑"
    await arcun.send(msg, at_sender=True)
