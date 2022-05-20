import io
from typing import List
import imageio
import aiohttp
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

default_font, font_size = Path(__file__).parent / "font" / "consola.ttf", 15
default_font = str(default_font)

async def get_pic_text(_img: Image.Image, new_w: int = 150):
    if not _img:
        return
    str_map = "@@$$&B88QMMGW##EE93SPPDOOU**==()+^,\"--''.  "
    n = len(str_map)
    img = _img.convert("L")
    w, h = img.size
    if w > new_w:
        img = img.resize((new_w, int(new_w // 2 * h / w)))
    else:
        img = img.resize((w, h // 2))

    s = ""
    for x in range(img.height):
        for y in range(img.width):
            gray_v = img.getpixel((y, x))
            s += str_map[int(n * (gray_v / 256))]
        s += "\n"
    return s


async def self_adaption_font_of_text(font_filename, default_font_size: int, text: str):
    """
    获取一段文本所占的宽度像素值
    返回字符画的 width, height
    """
    ttfont = ImageFont.truetype(font_filename, default_font_size)
    lines = text.split("\n")
    w = ttfont.getsize(lines[2])[0]

    return (
        ttfont,
        w,
        default_font_size * len(lines) + int(1.2 * len(lines)),
    )  # 高度不会搞，1.2 是瞎jb调的，等一个大佬（


async def text2img(text: str):
    font, w, h = await self_adaption_font_of_text(default_font, font_size, text)
    img = Image.new("L", (w, h), "#FFFFFF")
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), text, fill="#000000", font=font)
    output = io.BytesIO()
    img.save(output, format="jpeg")
    return output


async def char_gif(gif: Image.Image):
    """
    合成 gif 字符画
    """
    frame_list: List[str] = []
    try:
        while True:
            t = gif.tell()
            frame_list.append(await get_pic_text(gif, new_w=80))
            gif.seek(t + 1)
    except EOFError:
        pass
    font, w, h = await self_adaption_font_of_text(
        default_font, font_size, frame_list[0]
    )
    for i in range(len(frame_list)):
        img = await get_char_frame(frame_list[i], w, h, font)
        frame_list[i] = img
    output = io.BytesIO()
    imageio.mimsave(output, frame_list, format="gif", duration=0.08)

    return output


async def get_char_frame(text: str, w: int, h: int, font_):
    img = Image.new("L", (w, h), "#FFFFFF")
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), text, fill="#000000", font=font_)
    return img


async def get_img(img_url: str):
    if not img_url:
        return
    async with aiohttp.ClientSession() as session:
        async with session.get(img_url) as resp:
            result = await resp.read()
    if not result:
        return None
    img = Image.open(io.BytesIO(result))
    return img
