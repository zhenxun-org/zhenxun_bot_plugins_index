import asyncio

import arrow
import nonebot
from nonebot import on_metaevent, require
from nonebot.adapters.onebot.v11 import Event, LifecycleMetaEvent
from nonebot.log import logger

from . import command
from . import my_trigger as tr
from .config import DATA_PATH, config
from .rss_class import Rss


__plugin_des__ = "rss订阅"
__plugin_type__ = ("一些工具",)
__plugin_usage__ = """
usage：
    指令：
    所有指令在群聊中都需要@bot才能触发！
    添加订阅：add/添加rss订阅 订阅名 Rss地址
    添加 RSSHub 订阅：RSSHub 路由名 订阅名 （发送命令后，按照提示依次输入RSSHub 路由、订阅名和路由参数）
    删除订阅：deldy 订阅名
    所有订阅：show_all
    查看订阅：show
    修改订阅：
    change 订阅名[,订阅名,...] 属性=值[ 属性=值 ...]
       对应参数：
       订阅名	-name	    无空格字符串	禁止将多个订阅批量改名，会因为名称相同起冲突
       订阅链接	-url	    无空格字符串	RSSHub 订阅源可以省略域名，其余需要完整的 URL 地址
       QQ号	-qq	            正整数/-1	   需要先加该对象好友；前加英文逗号表示追加；-1 设为空
       QQ群	-qun	        正整数/-1	   需要先加入该群组；前加英文逗号表示追加；-1 设为空
       更新频率	-time       正整数/crontab 字符串	值为整数时表示每 x 分钟进行一次检查更新，且必须大于等于1.
       代理	-proxy	        1/0	 是否启用代理
       翻译	-tl	            1/0	 是否翻译正文内容
       仅标题	-ot	        1/0	 是否仅发送标题
       仅图片	-op	        1/0	 是否仅发送图片(正文中只保留图片)
       仅含有图片	-ohp	1/0	 仅含有图片不同于仅图片，除了图片还会发送正文中的其他文本信息
       下载种子	-downopen	1/0	 是否进行BT下载(需要配置 qBittorrent，参考：第一次部署)
       白名单关键词	-wkey	无空格字符串/空	          支持正则表达式，匹配时推送消息及下载；设为空(wkey=)时不生效
       黑名单关键词	-bkey	无空格字符串/空	          同白名单关键词，但匹配时不推送，可在避免冲突的情况下组合使用
       种子上传到群	-upgroup  1/0	                 是否将BT下载完成的文件上传到群(需要配置 qBittorrent，参考：第一次部署)
       去重模式	-mode	     link/title/image/or/-1	分为按链接(link)、标题(title)、图片(image)判断
                                                    其中 image 模式，出于性能考虑以及避免误伤情况发生，生效对象限定为只带 1 张图片的消息
                                                   此外，如果属性中带有 or 说明判断逻辑是任一匹配即去重，默认为全匹配 -1 设为禁用
       图片数量限制	        -img_num	            正整数	只发送限定数量的图片，防止刷屏
       停止更新	-stop	    1/0	                    对订阅停止、恢复检查更新       
""".strip()
__plugin_cmd__ = ["add", "rsshub", "deldy","show_all","show","change"]
__plugin_version__ = 2.6
__plugin_author__ = "Quan666"
__plugin_settings__ = {
    "level": 5,
    "default_status": True,
    "limit_superuser": False,
    'cmd': __plugin_cmd__
}
scheduler = require("nonebot_plugin_apscheduler").scheduler
START_TIME = arrow.now()


async def check_first_connect(event: Event) -> bool:
    return isinstance(event, LifecycleMetaEvent) and arrow.now() < START_TIME.shift(
        minutes=1
    )




start_metaevent = on_metaevent(rule=check_first_connect, block=True)


# 启动时发送启动成功信息
@start_metaevent.handle()
async def start() -> None:
    bot = nonebot.get_bot()

    # 启动后检查 data 目录，不存在就创建
    if not DATA_PATH.is_dir():
        DATA_PATH.mkdir()

    boot_message = (
        f"Version: {config.version}\n"
        "Author：Quan666\n"
        "https://github.com/Quan666/ELF_RSS"
    )

    await bot.send_private_msg(
        user_id=int(list(config.superusers)[0]),
        message=f"ELF_RSS 订阅器启动成功！\n{boot_message}",
    )
    logger.info("ELF_RSS 订阅器启动成功！")
    # 创建检查更新任务
    await asyncio.gather(*[tr.add_job(rss) for rss in rss_list if not rss.stop])
