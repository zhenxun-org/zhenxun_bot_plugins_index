import asyncio
import gc
import os.path
from functools import partial
from multiprocessing import Event
from pathlib import Path

import langid
import nonebot
from configs.config import NICKNAME, Config
from matplotlib.style import use
from MockingBirdOnlyForUse import MockingBird, Params
from MockingBirdOnlyForUse import logger as mocking_logger
from nonebot import Driver, export, on_command
from nonebot.adapters.onebot.v11 import Message, MessageEvent, MessageSegment
from nonebot.log import logger as nonebot_logger
from nonebot.params import ArgStr, CommandArg
from nonebot.permission import SUPERUSER
from nonebot.rule import to_me
from nonebot.typing import T_State
from utils.utils import is_number

from .data_source import get_voice
from .download import download_model

__zx_plugin_name__ = "MockingBird语音"
__plugin_usage__ = """
usage：
    @Bot说 [你想要bot说的话]
""".strip()
__plugin_des__ = "利用MockingBird生成语音并发送"
__plugin_cmd__ = [
    "说",
    f"{NICKNAME}说"
]
__plugin_type__ = ("来点语音吧~",)
__plugin_superuser_usage__ = """
usage：
    MockingBird模型修改指令
    指令：
        显示模型
        修改模型 [序号]\[模型名称]
        开启/关闭tts 切换使用腾讯TTS(需要配置secret_key)
        重载模型 进行模型重载(并没有什么卵用，或许以后内存泄漏解决会有用？)
""".strip()
__plugin_version__ = 0.1
__plugin_author__ = "AkashiCoin"
__plugin_settings__ = {
    "cmd": ["说", f"{NICKNAME}说"],
}
__plugin_block_limit__ = {"rst": f"{NICKNAME}说话没有那么快啦..."}

Config.add_plugin_config(
    "mockingbird",
    "MockingBird_Model",
    "azusa",
    name="MockingBird 语音",
    help_="MockingBird 语音模型",
    default_value="azusa"
)
Config.add_plugin_config(
    "mockingbird",
    "USE_TTS",
    False,
    name="MockingBird 语音",
    help_="是否使用TTS语音，需要配置secret_key",
    default_value=False
)

root = Path() / "data" / "mockingbird"
mocking_logger.logger = nonebot_logger  # 覆盖使用nonebot的logger

driver: Driver = nonebot.get_driver()
part: partial = None
model_list = {
    "1": "azusa",
}
export = export()

@driver.on_startup
async def init_mockingbird():
    global part
    global export
    global mockingbird
    model_name = Config.get_config("mockingbird", "MockingBird_Model")
    model_path = root / model_name
    try:
        if not model_path.exists():
            mocking_logger.info("MockingBird 模型不存在...开始下载模型...")
            model_path.parent.mkdir(parents=True, exist_ok=True)
            if await download_model(model_path, model_name):
                mocking_logger.info("模型下载成功...")
            else:
                mocking_logger.error("模型下载失败，请检查网络...")
        mocking_logger.info("开始加载 MockingBird 模型...")
        MockingBird.init(
            Path(os.path.join(model_path, "encoder.pt")),
            Path(os.path.join(model_path, "g_hifigan.pt")),
            "HifiGan",
        )
        part = partial(
            Params,
            recoder_path=Path(os.path.join(model_path, "recoder.wav")),
            synthesizer_path=Path(os.path.join(model_path, f"{model_name}.pt")),
            accuracy=9,
            steps=10,
            vocoder="HifiGan",
        )
        export.MockingBird = MockingBird
        export.Params = Params
        export.part = part
        return True
    except Exception as e:
        return f"{type(e)}：{e}"

voice = on_command("说", aliases={"语音"}, block=True, rule=to_me(), priority=4)
view_model = on_command("显示所有模型", aliases={"MockingBird模型", "显示模型", "所有模型"}, block=True, permission=SUPERUSER, priority=5)
change_model = on_command("修改模型", aliases={"MockingBird模型修改"}, block=True, permission=SUPERUSER, priority=5)
reload_mockingbird = on_command("重载模型", aliases={"MockingBird模型重载"}, block=True, permission=SUPERUSER, priority=5)
switch_tts = on_command("开启tts", aliases={"关闭tts"}, block=True, permission=SUPERUSER, priority=5)

@voice.handle()
async def _(state:T_State, arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip()
    if args:
        state["words"] = args

@voice.got("words", prompt=f"想要让{NICKNAME}什么话呢?")
async def _(state: T_State,  words: str = ArgStr("words")):
    global part
    words = words.strip().replace('\n', '').replace('\r', '')
    if Config.get_config("mockingbird", "USE_TTS"):
        record = await get_voice(words)
        if record:
            await voice.finish(MessageSegment.record(record))
        else:
            await voice.finish("出错了，请稍后再试")
    if langid.classify(words)[0] == "ja":
        record = await get_voice(words)
    else:
        params = part(words)
        params.text = words
        loop = asyncio.get_event_loop()
        record = await loop.run_in_executor(None, MockingBird.genrator_voice, params)
    await voice.finish(MessageSegment.record(record))

@view_model.handle()
async def _():
    msg = "当前加载的模型为:{}\n".format(Config.get_config("mockingbird", "MockingBird_Model"))
    msg += "可以修改的模型列表:\n"
    for i, model in model_list.items():
        msg += "{}. {}".format(i, model)
    await view_model.finish(msg)

@change_model.handle()
async def _(arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip()
    if is_number(args):
        args = model_list.get(args)
        if args is None:
            await change_model.finish("该模型不存在...")
    if args not in model_list.values():
        await change_model.finish("该模型不存在...")
    else:
        if args == Config.get_config("mockingbird", "MockingBird_Model"):
            await change_model.finish("该模型正在使用，请勿重复加载...")
        Config.set_config("mockingbird", "MockingBird_Model", args)
        gc.collect()
        msg = await init_mockingbird()
        if isinstance(msg, str):
            await change_model.finish(f"修改失败...错误信息:{msg}")
        else:
            await change_model.finish(f"修改MockingBird模型为{args}成功...")

@reload_mockingbird.handle()
async def _():
    gc.collect()
    msg = await init_mockingbird()
    if isinstance(msg, str):
        await change_model.finish(f"重载失败...错误信息:{msg}")
    else:
        await change_model.finish(f"重载MockingBird模型成功...")

@switch_tts.handle()
async def _(event: MessageEvent):
    global use_tts
    msg = event.get_plaintext().strip()
    if msg.startswith("开启"):
        Config.set_config("mockingbird", "USE_TTS", True)
        await switch_tts.finish("已开启使用tts...")
    else:
        Config.set_config("mockingbird", "USE_TTS", False)
        await switch_tts.finish("已关闭tts，使用MockingBird语音...")
