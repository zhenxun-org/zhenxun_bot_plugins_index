import base64

from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Message, MessageSegment, MessageEvent
from nonebot.adapters.onebot.v11.helpers import HandleCancellation
from nonebot.params import CommandArg
from nonebot.typing import T_State

from .data_source import color_car, get_img, gray_car

__zx_plugin_name__ = "幻影坦克"
__plugin_usage__ = """
usage：
    生成幻影坦克图（在黑白背景下显示不同的图）
    指令：
        /幻影坦克
""".strip()
__plugin_des__ = "幻影坦克"
__plugin_type__ = ("群内小游戏",)
__plugin_cmd__ = ["幻影坦克"]
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["幻影坦克"],
}
mirage_tank = on_command("幻影坦克", aliases={"miragetank"}, priority=5)


@mirage_tank.handle()
async def handle_first(
    bot: Bot, event: MessageEvent, state: T_State, args: Message = CommandArg()
):
    images = []
    for seg in args:
        if seg.type == "text":
            state["mod"] = seg.data["text"].strip()
        elif seg.type == "image":
            images.append(seg)
    if len(images) >= 1:
        state['img1'] = images[0]
    if len(images) >= 2:
        state['img2'] = images[1]


@mirage_tank.got("mod", prompt="需要指定结果类型: gray | color")
async def get_mod(
    state: T_State,
    args: Message = CommandArg(),
    cancel=HandleCancellation("已取消"),
):
    mod = args.extract_plain_text().strip()
    if mod in ["gray", "color"]:
        state["mod"] = mod
    else:
        await mirage_tank.reject('"gray" | "color", 二选一')


@mirage_tank.got("img1", prompt="请发送两张图，按表里顺序")
@mirage_tank.got("img2", prompt="还需要一张图")
async def get_images(
    state: T_State, cancel=HandleCancellation("已取消")
):
    img_urls = []
    mod = str(state["mod"])
    for seg in state["img1"] + state["img2"]:
        img_urls.append(await get_img(seg.data['url']))

    await mirage_tank.send("开始合成")

    res = None
    if mod == "gray":
        res = await gray_car(img_urls[0], img_urls[1])
    elif mod == "color":
        res = await color_car(img_urls[0], img_urls[1])
    if res:
        img_urls = []
        await mirage_tank.finish(
            MessageSegment.image(
                f"base64://{base64.b64encode(res.getvalue()).decode()}"
            )
        )
