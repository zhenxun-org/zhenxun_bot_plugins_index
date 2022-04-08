from fileinput import filename
from pathlib import Path

from nonebot.log import logger
from utils.http_utils import AsyncHttpx

base_url = "https://pan.yropo.workers.dev/source/mockingbird"


async def download_url(url: str, path: Path) -> bool:
    for i in range(3):
        try:
            url = (await AsyncHttpx.post(url)).url
            resp = await AsyncHttpx.download_file(url, path)
            if resp:
                return True
            else:
                continue
        except Exception as e:
            logger.warning(f"Error downloading {url}, retry {i}/3: {e}")
    return False


async def download_model(model_path: Path, model_name: str) -> bool:
    url = f"{base_url}/{model_name}/"
    for file_name in ["recoder.wav", "encoder.pt", "g_hifigan.pt", f"{model_name}.pt"]:
        res = await download_url(url + file_name, model_path / file_name)
        if not res:
            return False
    return True
