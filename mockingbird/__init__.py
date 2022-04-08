import os.path
from functools import partial
from pathlib import Path

import nonebot
from configs.config import NICKNAME, Config
from MockingBirdOnlyForUse import MockingBird, Params
from MockingBirdOnlyForUse import logger as mocking_logger
from nonebot import Driver, export, on_command
from nonebot.adapters.onebot.v11 import Message, MessageSegment
from nonebot.log import logger as nonebot_logger
from nonebot.params import CommandArg
from nonebot.rule import to_me

from .download import download_model

__zx_plugin_name__ = "MockingBird 语音"
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

root = Path() / "data" / "mockingbird"
mocking_logger.logger = nonebot_logger  # 覆盖使用nonebot的logger

driver: Driver = nonebot.get_driver()
part: partial = None
export = export()

@driver.on_startup
async def init_mockingbird():
    global part
    global export
    model_name = Config.get_config("mockingbird", "MockingBird_Model")
    model_path = root / model_name
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
        synthesizer_path=Path(os.path.join(model_path, "azusa.pt")),
        vocoder="HifiGan",
    )
    export.MockingBird = MockingBird
    export.Params = Params
    export.part = part





voice = on_command("说", aliases={"语音"}, block=True, rule=to_me(), priority=4)


@voice.handle()
async def _(args: Message = CommandArg()):
    global part
    params = part(args)
    params.text = args.extract_plain_text()
    await voice.finish(MessageSegment.record(MockingBird.genrator_voice(params)))
