import shlex
import traceback
from typing import List, Type
from nonebot import on_command
from nonebot.matcher import Matcher
from nonebot.typing import T_Handler, T_RuleChecker, T_State
from nonebot.params import CommandArg, State
from nonebot.adapters.onebot.v11 import (
    Bot,
    Message,
    MessageSegment,
    MessageEvent,
    GroupMessageEvent,
)
from nonebot.log import logger

from .data_source import make_image, commands
from .download import DownloadError, ResourceError
from .utils import help_image
from .models import UserInfo, Command

__zx_plugin_name__ = "头像表情包"
__plugin_usage__ = """
usage：
    触发方式：指令 + @user/qq/自己/图片
    发送“头像表情包”查看支持的指令
    指令：
        摸 @任何人
        摸 qq号
        摸 自己
        摸 [图片]
""".strip()
__plugin_des__ = "生成各种表情"
__plugin_type__ = ("功能",)
__plugin_cmd__ = [
    "头像表情包", "头像相关表情包", "头像相关表情制作",
    "摸", "摸摸", "摸头", "摸摸头", "rua",
    "亲", "亲亲",
    "贴", "贴贴", "蹭", "蹭蹭",
    "顶", "玩",
    "拍",
    "撕",
    "丢", "扔",
    "抛", "掷",
    "爬",
    "精神支柱",
    "一直",
    "加载中",
    "转",
    "小天使",
    "不要靠近",
    "一样",
    "滚",
    "玩游戏", "来玩游戏",
    "膜", "膜拜",
    "吃",
    "啃",
    "出警",
    "警察",
    "问问", "去问问",
    "舔", "舔屏", "prpr",
    "搓",
    "墙纸",
    "国旗",
    "交个朋友",
    "继续干活",
    "完美", "完美的",
    "关注",
    "我朋友说", "我有个朋友说",
    "这像画吗",
    "震惊",
    "兑换券",
    "听音乐",
    "典中典",
    "哈哈镜",
    "永远爱你",
    "对称",
    "安全感",
    "永远喜欢", "我永远喜欢",
    "采访",
    "打拳",
    "群青",
    "捣",
    "捶",
    "需要", "你可能需要",
    "捂脸",
]
__plugin_version__ = 0.3
__plugin_author__ = "MeetWq"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
}

help_cmd = on_command("头像表情包", aliases={"头像相关表情包", "头像相关表情制作"}, block=True, priority=5)


@help_cmd.handle()
async def _():
    img = await help_image(commands)
    if img:
        await help_cmd.finish(MessageSegment.image(img))


def is_qq(msg: str):
    return msg.isdigit() and 11 >= len(msg) >= 5


async def get_user_info(bot: Bot, user: UserInfo):
    if not user.qq:
        return

    if user.group:
        info = await bot.get_group_member_info(
            group_id=int(user.group), user_id=int(user.qq)
        )
        user.name = info.get("card", "") or info.get("nickname", "")
        user.gender = info.get("sex", "")
    else:
        info = await bot.get_stranger_info(user_id=int(user.qq))
        user.name = info.get("nickname", "")
        user.gender = info.get("sex", "")


def check_args_rule(command: Command) -> T_RuleChecker:
    async def check_args(
            bot: Bot,
            event: MessageEvent,
            state: T_State = State(),
            msg: Message = CommandArg(),
    ) -> bool:

        users: List[UserInfo] = []
        args: List[str] = []

        if event.reply:
            reply_imgs = event.reply.message["image"]
            for reply_img in reply_imgs:
                users.append(UserInfo(img_url=reply_img.data["url"]))

        for msg_seg in msg:
            if msg_seg.type == "at":
                users.append(
                    UserInfo(
                        qq=msg_seg.data["qq"],
                        group=str(event.group_id)
                        if isinstance(event, GroupMessageEvent)
                        else "",
                    )
                )
            elif msg_seg.type == "image":
                users.append(UserInfo(img_url=msg_seg.data["url"]))
            elif msg_seg.type == "text":
                raw_text = str(msg_seg)
                try:
                    texts = shlex.split(raw_text)
                except:
                    texts = raw_text.split()
                for text in texts:
                    if is_qq(text):
                        users.append(UserInfo(qq=text))
                    elif text == "自己":
                        users.append(
                            UserInfo(
                                qq=str(event.user_id),
                                group=str(event.group_id)
                                if isinstance(event, GroupMessageEvent)
                                else "",
                            )
                        )
                    else:
                        text = text.strip()
                        if text:
                            args.append(text)

        if len(args) > command.arg_num:
            return False
        if not users and isinstance(event, GroupMessageEvent) and event.is_tome():
            users.append(UserInfo(qq=str(event.self_id), group=str(event.group_id)))
        if not users:
            return False

        sender = UserInfo(qq=str(event.user_id))
        await get_user_info(bot, sender)
        for user in users:
            await get_user_info(bot, user)
        state["sender"] = sender
        state["users"] = users
        state["args"] = args
        return True

    return check_args


async def handle(
        matcher: Type[Matcher],
        command: Command,
        sender: UserInfo,
        users: List[UserInfo],
        args: List[str],
):
    try:
        res = await make_image(command, sender, users, args=args)
    except DownloadError:
        await matcher.finish("图片下载出错，请稍后再试")
    except ResourceError:
        await matcher.finish("资源下载出错，请稍后再试")
    except:
        logger.warning(traceback.format_exc())
        await matcher.finish("出错了，请稍后再试")

    if not res:
        await matcher.finish("出错了，请稍后再试")
    if isinstance(res, str):
        await matcher.finish(res)
    else:
        await matcher.finish(MessageSegment.image(res))


def create_matchers():
    def create_handler(command: Command) -> T_Handler:
        async def handler(state: T_State = State()):
            await handle(
                matcher, command, state["sender"], state["users"], state["args"]
            )

        return handler

    for command in commands:
        matcher = on_command(
            command.keywords[0],
            aliases=set(command.keywords),
            rule=check_args_rule(command),
            block=True,
            priority=5,
        )
        matcher.append_handler(create_handler(command))


create_matchers()
