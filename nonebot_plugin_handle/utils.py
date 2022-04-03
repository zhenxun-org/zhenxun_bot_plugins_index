import random
from io import BytesIO
from utils.http_utils import AsyncHttpx
from configs.path_config import IMAGE_PATH, TEXT_PATH, FONT_PATH
from typing import List, Tuple
from pypinyin import pinyin, Style
from PIL import ImageFont
from PIL.Image import Image as IMG
from PIL.ImageFont import FreeTypeFont
from services.log import logger
from pathlib import Path

resource_dir = Path(__file__).parent / "resources"
fonts_dir = resource_dir / "fonts"
handle_txt_path = TEXT_PATH / "handle"
idiom_path = handle_txt_path / "idioms.txt"
handle_txt_path.mkdir(exist_ok=True, parents=True)


async def random_idiom() -> str:
    if not idiom_path.exists():
        url = "https://cdn.jsdelivr.net/gh/MeetWq/nonebot-plugin-handle@master/nonebot_plugin_handle/resources/data/idioms.txt"
        try:
            response = await AsyncHttpx.get(url)
            idiom_txt = response.text
            idiom_list = idiom_txt.split('\n')
            with idiom_path.open("w", encoding="utf-8") as f:
                f.write(idiom_txt)
                f.close()
            return random.choice(idiom_list).strip()
        except Exception as e:
            logger.warning(f"Error downloading {url}: {e}")
    with idiom_path.open("r", encoding="utf-8") as f:
        return random.choice(f.readlines()).strip()


# fmt: off
# 声母
INITIALS = ["zh", "z", "y", "x", "w", "t", "sh", "s", "r", "q", "p", "n", "m", "l", "k", "j", "h", "g", "f", "d", "ch",
            "c", "b"]
# 韵母
FINALS = [
    "ün", "üe", "üan", "ü", "uo", "un", "ui", "ue", "uang", "uan", "uai", "ua", "ou", "iu", "iong", "ong", "io", "ing",
    "in", "ie", "iao", "iang", "ian", "ia", "er", "eng", "en", "ei", "ao", "ang", "an", "ai", "u", "o", "i", "e", "a"
]


# fmt: on


def get_pinyin(idiom: str) -> List[Tuple[str, str, str]]:
    pys = pinyin(idiom, style=Style.TONE3, v_to_u=True)
    results = []
    for p in pys:
        py = p[0]
        if py[-1].isdigit():
            tone = py[-1]
            py = py[:-1]
        else:
            tone = ""
        initial = ""
        for i in INITIALS:
            if py.startswith(i):
                initial = i
                break
        final = ""
        for f in FINALS:
            if py.endswith(f):
                final = f
                break
        results.append((initial, final, tone))  # 声母，韵母，声调
    return results


def save_jpg(frame: IMG) -> BytesIO:
    output = BytesIO()
    frame = frame.convert("RGB")
    frame.save(output, format="jpeg")
    return output


def load_font(name: str, fontsize: int) -> FreeTypeFont:
    return ImageFont.truetype(str(fonts_dir / name), fontsize, encoding="utf-8")
