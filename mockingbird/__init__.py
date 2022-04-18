import asyncio
import gc
import os.path
from functools import partial
from pathlib import Path

import langid
import nonebot
from configs.config import NICKNAME, Config
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
from .download import check_resource, download_resource

__zx_plugin_name__ = "MockingBird语音"
__plugin_usage__ = """
usage：
    @Bot说 [你想要bot说的话]
    超级用户指令:
        显示模型
        修改模型 [序号]\[模型名称]
        开启/关闭tts 切换使用腾讯TTS(需要配置secret_key)
        重载模型 进行模型重载(并没有什么卵用，或许以后内存泄漏解决会有用？)
        调整/修改精度 修改语音合成精度(对TTS无效)
        调整/修改句长 修改语音合成最大句长(对TTS无效)
""".strip()
__plugin_des__ = "利用MockingBird生成语音并发送"
__plugin_cmd__ = [
    "说",
    f"{NICKNAME}说"
]
__plugin_type__ = ("来点语音吧~",)
__plugin_superuser_usage__ = """
usage： MockingBird模型修改指令 显示模型 | 修改模型 [序号]\[模型名称] | 开启/关闭tts | 重载模型 | 调整/修改精度 | 调整/修改句长
""".strip()
__plugin_version__ = 0.2
__plugin_author__ = "AkashiCoin"
__plugin_settings__ = {
    "cmd": ["说", f"{NICKNAME}说"],
}
__plugin_block_limit__ = {"rst": f"{NICKNAME}说话没有那么快啦..."}

Config.add_plugin_config(
    "mockingbird",
    "MOCKINGBIRD_MODEL",
    "azusa",
    name="MockingBird模型选择",
    help_="MockingBird模型，请不要直接修改，而是使用命令修改",
    default_value="azusa"
)
Config.add_plugin_config(
    "mockingbird",
    "USE_TTS",
    False,
    name="TTS语音是否启用",
    help_="是否使用TTS语音，需要配置tecent_secret_id和key，在 https://console.cloud.tencent.com/tts 启用",
    default_value=False
)
Config.add_plugin_config(
    "mockingbird",
    "VOICE_ACCURACY",
    9,
    name="MockingBird语音精度",
    help_="MockingBird的语音精度，影响语音效果，请不要直接修改，而是使用命令修改",
    default_value=9
)
Config.add_plugin_config(
    "mockingbird",
    "MAX_STEPS",
    4,
    name="MockingBird语音最大句长",
    help_="MockingBird语音的最大句长，请不要直接修改，而是使用命令修改",
    default_value=4
)
Config.add_plugin_config(
    "mockingbird",
    "TENCENT_SECRET_ID",
    "",
    name="TTS的tencent_secret_id",
    help_="TTS的tencent_secret_id，在 https://console.cloud.tencent.com/cam/capi 设置",
    default_value=""
)
Config.add_plugin_config(
    "mockingbird",
    "TENCENT_SECRET_KEY",
    "",
    name="TTS的tencent_secret_key",
    help_="TTS的tencent_secret_key，在 https://console.cloud.tencent.com/cam/capi 设置",
    default_value=""
)
mockingbired_path = Path() / "data" / "mockingbird"
mocking_logger.logger = nonebot_logger  # 覆盖使用nonebot的logger

driver: Driver = nonebot.get_driver()
part: partial = None
model_list = {
    "1": ["azusa", "阿梓语音"],
    "2": ["nanami1", "七海语音1"],
    "3": ["nanami2", "七海语音2"],
    "4": ["nanmei", "小南莓语音"],
    "5": ["ltyai", "洛天依语音"],
    "6": ["tianyi", "洛天依语音-wq"],
}
export = export()

@driver.on_startup
async def init_mockingbird():
    global part
    global export
    global mockingbird
    model_name = Config.get_config("mockingbird", "MOCKINGBIRD_MODEL")
    model_path = mockingbired_path / model_name
    try:
        if not model_path.exists():
            mocking_logger.info("MockingBird 模型不存在...开始下载模型...")
            model_path.parent.mkdir(parents=True, exist_ok=True)
        if not await check_resource(mockingbired_path, model_name):
            if await download_resource(mockingbired_path, model_name):
                mocking_logger.info("模型下载成功...")
            else:
                mocking_logger.error("模型下载失败，请检查网络...")
                return False
        mocking_logger.info("开始加载 MockingBird 模型...")
        MockingBird.init(
            Path(os.path.join(mockingbired_path, "encoder.pt")),
            Path(os.path.join(mockingbired_path, "g_hifigan.pt")),
            "HifiGan",
        )
        part = partial(
            Params,
            recoder_path=Path(os.path.join(model_path, "record.wav")),
            synthesizer_path=Path(os.path.join(model_path, f"{model_name}.pt")),
            accuracy=Config.get_config("mockingbird", "VOICE_ACCURACY"),
            steps=Config.get_config("mockingbird", "MAX_STEPS"),
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
adjust_accuracy = on_command("调整语音精度", aliases={"调整精度", "修改精度"}, block=True, permission=SUPERUSER, priority=5)
adjust_steps = on_command("调整语音句长", aliases={"调整句长", "修改句长"}, block=True, permission=SUPERUSER, priority=5)

@voice.handle()
async def _(state:T_State, arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip()
    if args:
        state["words"] = args

@voice.got("words", prompt=f"想要让{NICKNAME}说什么话呢?")
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
        record = await asyncio.get_event_loop().run_in_executor(None, MockingBird.genrator_voice, params)
    await voice.finish(MessageSegment.record(record))

@view_model.handle()
async def _():
    msg = "当前加载的模型为:{}\n".format(Config.get_config("mockingbird", "MOCKINGBIRD_MODEL"))
    msg += "当前精度: {} , 最大句长: {}\n".format(Config.get_config("mockingbird", "VOICE_ACCURACY"), Config.get_config("mockingbird", "MAX_STEPS"))
    msg += "可以修改的模型列表:"
    for i, model in model_list.items():
        msg += "\n{}. {} --- {}".format(i, model[0], model[1])
    await view_model.finish(msg)

@change_model.handle()
async def _(arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip()
    if is_number(args):
        args = model_list.get(args)
        if args is None:
            await change_model.finish("该模型不存在...")
        else:
            args = args[0]
    models = []
    for model in model_list.values():
        models.append(model[0])
    if args not in models:
        await change_model.finish("该模型不存在...")
    else:
        if args == Config.get_config("mockingbird", "MOCKINGBIRD_MODEL"):
            await change_model.finish("该模型正在使用，请勿重复加载...")
        Config.set_config("mockingbird", "MOCKINGBIRD_MODEL", args)
        Config.save(save_simple_data=True)
        gc.collect()
        msg = await init_mockingbird()
        if isinstance(msg, str):
            await change_model.finish(f"修改失败...错误信息:{msg}")
        else:
            await change_model.finish(f"修改MockingBird模型为{args}成功...")

@reload_mockingbird.handle()
async def reload_model():
    gc.collect()
    msg = await init_mockingbird()
    if isinstance(msg, str):
        await reload_mockingbird.finish(f"重载失败...错误信息:{msg}")
    else:
        await reload_mockingbird.finish(f"重载MockingBird模型成功...")

@switch_tts.handle()
async def _(event: MessageEvent):
    global use_tts
    msg = event.get_plaintext().strip()
    if Config.get_config("mockingbird", "TENCENT_SECRET_KEY") == "":
        await switch_tts.finish("无法启用TTS，请先配置tencent_secret_key...")
    if msg.startswith("开启"):
        Config.set_config("mockingbird", "USE_TTS", True)
        Config.save(save_simple_data=True)
        await switch_tts.finish("已开启使用tts...")
    else:
        Config.set_config("mockingbird", "USE_TTS", False)
        Config.save(save_simple_data=True)
        await switch_tts.finish("已关闭tts，使用MockingBird语音...")

@adjust_accuracy.handle()
async def _(arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip()
    if not is_number(args):
        await adjust_accuracy.finish("请输入数字...")
    num = int(args)
    if num > 2 and num < 10:
        Config.set_config("mockingbird", "VOICE_ACCURACY", num)
        Config.save(save_simple_data=True)
        msg = await init_mockingbird()
        if isinstance(msg, str):
            await adjust_accuracy.finish(f"调整失败...错误信息:{msg}")
        await adjust_accuracy.finish(f"已修改精度为: {num}")
    else:
        await adjust_accuracy.finish("请输入3-9以内的数字！")
        
@adjust_steps.handle()
async def _(arg: Message = CommandArg()):
    args = arg.extract_plain_text().strip()
    if not is_number(args):
        await adjust_steps.finish("请输入数字...")
    num = int(args)
    if num > 0 and num < 11:
        Config.set_config("mockingbird", "MAX_STEPS", num)
        Config.save(save_simple_data=True)
        msg = await init_mockingbird()
        if isinstance(msg, str):
            await adjust_steps.finish(f"调整失败...错误信息:{msg}")
        await adjust_steps.finish(f"已修改最大句长为: {num}")
    else:
        await adjust_steps.finish("请输入1-10以内的数字！")