import aiofiles
from utils.http_utils import AsyncHttpx
from configs.path_config import IMAGE_PATH
import hashlib
from aiocache import cached
from services.log import logger

data_path = IMAGE_PATH / "petpet"
data_path.mkdir(exist_ok=True, parents=True)



class DownloadError(Exception):
    pass


class ResourceError(Exception):
    pass


async def download_url(url: str) -> bytes:
    try:
        response = await AsyncHttpx.get(url)
        return response.content
    except Exception as e:
        logger.warning(f"Error downloading {url}: {e}")
    raise DownloadError



async def get_resource(path: str, name: str) -> bytes:
    file_path = data_path / path / name
    if not file_path.exists():
        file_path.parent.mkdir(parents=True, exist_ok=True)
        url = f"https://cdn.jsdelivr.net/gh/MeetWq/nonebot-plugin-petpet@master/resources/{path}/{name}"
        data = await download_url(url)
        if data:
            async with aiofiles.open(str(file_path), "wb") as f:
                await f.write(data)
    if not file_path.exists():
        raise ResourceError
    async with aiofiles.open(str(file_path), "rb") as f:
        return await f.read()


@cached(ttl=600)
async def get_image(name: str) -> bytes:
    return await get_resource("images", name)


@cached(ttl=600)
async def get_font(name: str) -> bytes:
    return await get_resource("fonts", name)


@cached(ttl=60)
async def download_avatar(user_id: str) -> bytes:
    url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=640"
    data = await download_url(url)
    if not data or hashlib.md5(data).hexdigest() == "acef72340ac0e914090bd35799f5594e":
        url = f"http://q1.qlogo.cn/g?b=qq&nk={user_id}&s=100"
        data = await download_url(url)
        if not data:
            raise DownloadError
    return data