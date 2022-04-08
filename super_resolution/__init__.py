import asyncio
import time
from asyncio import Semaphore
from pathlib import Path

import numpy as np
from configs.path_config import TEMP_PATH
from nonebot import on_command
from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent
from nonebot.params import Arg, Depends
from nonebot.typing import T_State
from PIL import Image as IMG
from utils.http_utils import AsyncHttpx
from utils.image_utils import pic2b64
from utils.message_builder import image as image_builder
from utils.utils import get_message_img

try:
    from basicsr.archs.rrdbnet_arch import RRDBNet
    from realesrgan import RealESRGANer

    enable = True
except ImportError:
    enable = False

__zx_plugin_name__ = "超分"
__plugin_usage__ = """
usage：
    一个图片超分插件
    指令：
        超分 [图片]
""".strip()
__plugin_des__ = "超级分辨率图片？"
__plugin_cmd__ = [
    "超分 [image]",
]
__plugin_type__ = ("一些工具",)
__plugin_version__ = 0.1
__plugin_author__ = "AkashiCoin"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    "cmd": ["超分"],
}
__plugin_block_limit__ = {"rst": "您有超分图片正在处理，请稍等..."}


upsampler = (
    RealESRGANer(
        scale=4,
        model_path=str(
            Path(__file__).parent.joinpath("RealESRGAN_x4plus_anime_6B.pth")
        ),
        model=RRDBNet(
            num_in_ch=3,
            num_out_ch=3,
            num_feat=64,
            num_block=6,
            num_grow_ch=32,
            scale=4,
        ),
        tile=0,
        tile_pad=10,
        pre_pad=0,
        half=False,
    )
    if enable
    else None
)

max_size = 691200
mutex = Semaphore(1)
resize = True
processing = False

superResolution = on_command("超分", priority=5, block=True)

def parse_image(key: str):
    async def _key_parser(
        state: T_State, img: Message = Arg(key)
    ):
        if not get_message_img(img):
            await superResolution.finish(key, "格式错误，超分已取消...")
        state[key] = img
    return _key_parser

@superResolution.handle()
async def _(bot: Bot, event: MessageEvent, state: T_State):
    if get_message_img(event.json()):
        state["img"] = event.message


@superResolution.got(
    "img", prompt="请发送需要处理的图片...", parameterless=[Depends(parse_image("img"))]
)
async def _(
    bot: Bot,
    event: MessageEvent,
    state: T_State,
    img: Message = Arg("img"),
):
    global processing
    img_url = get_message_img(event.message)[0]
    if processing:
        await superResolution.finish("有超分正在运行...此次请求已取消...")
    await mutex.acquire()
    processing = True
    mutex.release()
    await superResolution.send("开始处理图片...")
    if await AsyncHttpx.download_file(
            img_url, TEMP_PATH / f"{event.user_id}_super.png"
        ):
        image = IMG.open(TEMP_PATH / f"{event.user_id}_super.png")
    else:
        await mutex.acquire()
        processing=False
        mutex.release()
        await superResolution.finish("图片下载失败...")
    start = time.time()
    image_size = image.size[0] * image.size[1]
    if image_size > max_size:
        if not resize:
            await superResolution.finish(f"图片尺寸过大！请发送720p以内即像素数小于 960×720=691200的照片！\n此图片尺寸为：{image.size[0]}×{image.size[1]}={image_size}！")
        length = 1
        for b in str(max_size / image_size).split(".")[1]:
            if b == "0":
                length += 1
            else:
                break
        magnification = round(max_size / image_size, length + 1)
        image = image.resize(
            (
                round(image.size[0] * magnification),
                round(image.size[1] * magnification),
            )
        )
    image_array: np.ndarray = image.__array__()
    loop = asyncio.get_event_loop()
    output, _ = await loop.run_in_executor(None, upsampler.enhance, image_array, 2)
    await mutex.acquire()
    processing = False
    mutex.release()
    img = IMG.fromarray(output)
    end = time.time()
    use_time = round(end - start, 2)
    await superResolution.send(Message(f"超分完成！处理用时：{use_time}s\n" + (f"由于像素过大，图片已进行缩放，结果可能不如原图片清晰" if resize else "")))
    await superResolution.finish(image_builder(b64=pic2b64(img)))
