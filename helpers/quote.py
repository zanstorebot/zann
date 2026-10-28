import os
from io import BytesIO

import aiofiles
import aiohttp

from config import BOT_NAME

from .tools import Tools


class QuotlyException(Exception):
    pass


class Quotly:
    GAMBAR_KONTOL = """
⣠⡶⠚⠛⠲⢄⡀
⣼⠁ ⠀⠀⠀ ⠳⢤⣄
⢿⠀⢧⡀⠀⠀⠀⠀⠀⢈⡇
⠈⠳⣼⡙⠒⠶⠶⠖⠚⠉⠳⣄
⠀⠀⠈⣇⠀⠀⠀⠀⠀⠀⠀⠈⠳⣄
⠀⠀⠀⠘⣆ ⠀⠀⠀⠀ ⠀⠈⠓⢦⣀
⠀⠀⠀⠀⠈⢳⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠲⢤
⠀⠀⠀⠀⠀⠀⠙⢦⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢧
⠀⠀⠀⠀⠀⠀⠀⡴⠋⠓⠦⣤⡀⠀⠀⠀⠀⠀⠀⠀⠈⣇
⠀⠀⠀⠀⠀⠀⣸⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡄
⠀⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇
⠀⠀⠀⠀⠀⠀⢹⡄⠀⠀⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠃
⠀⠀⠀⠀⠀⠀⠀⠙⢦⣀⣳⡀⠀⠀⠀⠀⠀⠀⠀⠀⣰⠏
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠙⠛⢦⣀⣀⣀⣀⣠⡴⠚⠉
"""

    GAMBAR_TITIT = """
😋😋
😋😋😋
  😋😋😋
    😋😋😋
     😋😋😋
       😋😋😋
        😋😋😋
         😋😋😋
          😋😋😋
          😋😋😋
      😋😋😋😋
 😋😋😋😋😋😋
 😋😋😋  😋😋😋
    😋😋       😋😋
"""
    colors = [
        "White",
        "Alice",
        "DarkBlue",
        "MediumBlue",
        "Blue",
        "DarkGreen",
        "Green",
        "Teal",
        "DarkCyan",
        "DeepSkyBlue",
        "DarkTurquoise",
        "MediumSpringGreen",
        "Lime",
        "SpringGreen",
        "Aqua",
        "Cyan",
        "MidnightBlue",
        "DodgerBlue",
        "LightSeaGreen",
        "ForestGreen",
        "SeaGreen",
        "DarkSlateGray",
        "DarkSlateGrey",
        "LimeGreen",
        "MediumSeaGreen",
        "Turquoise",
        "RoyalBlue",
        "SteelBlue",
        "DarkSlateBlue",
        "MediumTurquoise",
        "Indigo  ",
        "DarkOliveGreen",
        "CadetBlue",
        "CornflowerBlue",
        "RebeccaPurple",
        "MediumAquaMarine",
        "DimGray",
        "DimGrey",
        "SlateBlue",
        "OliveDrab",
        "SlateGray",
        "SlateGrey",
        "LightSlateGray",
        "LightSlateGrey",
        "MediumSlateBlue",
        "LawnGreen",
        "Chartreuse",
        "Aquamarine",
        "Maroon",
        "Purple",
        "Olive",
        "Gray",
        "Grey",
        "SkyBlue",
        "LightSkyBlue",
        "BlueViolet",
        "DarkRed",
        "DarkMagenta",
        "SaddleBrown",
        "DarkSeaGreen",
        "LightGreen",
        "MediumPurple",
        "DarkViolet",
        "PaleGreen",
        "DarkOrchid",
        "YellowGreen",
        "Sienna",
        "Brown",
        "DarkGray",
        "DarkGrey",
        "LightBlue",
        "GreenYellow",
        "PaleTurquoise",
        "LightSteelBlue",
        "PowderBlue",
        "FireBrick",
        "DarkGoldenRod",
        "MediumOrchid",
        "RosyBrown",
        "DarkKhaki",
        "Silver",
        "MediumVioletRed",
        "IndianRed ",
        "Peru",
        "Chocolate",
        "Tan",
        "LightGray",
        "LightGrey",
        "Thistle",
        "Orchid",
        "GoldenRod",
        "PaleVioletRed",
        "Crimson",
        "Gainsboro",
        "Plum",
        "BurlyWood",
        "LightCyan",
        "Lavender",
        "DarkSalmon",
        "Violet",
        "PaleGoldenRod",
        "LightCoral",
        "Khaki",
        "AliceBlue",
        "HoneyDew",
        "Azure",
        "SandyBrown",
        "Wheat",
        "Beige",
        "WhiteSmoke",
        "MintCream",
        "GhostWhite",
        "Salmon",
        "AntiqueWhite",
        "Linen",
        "LightGoldenRodYellow",
        "OldLace",
        "Red",
        "Fuchsia",
        "Magenta",
        "DeepPink",
        "OrangeRed",
        "Tomato",
        "HotPink",
        "Coral",
        "DarkOrange",
        "LightSalmon",
        "Orange",
        "LightPink",
        "Pink",
        "Gold",
        "PeachPuff",
        "NavajoWhite",
        "Moccasin",
        "Bisque",
        "MistyRose",
        "BlanchedAlmond",
        "PapayaWhip",
        "LavenderBlush",
        "SeaShell",
        "Cornsilk",
        "LemonChiffon",
        "FloralWhite",
        "Snow",
        "Yellow",
        "LightYellow",
        "Ivory",
        "Black",
    ]

    async def forward_info(reply):
        if reply.forward_from_chat:
            sid = reply.forward_from_chat.id
            title = reply.forward_from_chat.title
            name = title
        elif reply.forward_from:
            sid = reply.forward_from.id
            try:
                try:
                    name = first_name = reply.forward_from.first_name
                except TypeError:
                    name = "Unknown"
                if reply.forward_from.last_name:
                    last_name = reply.forward_from.last_name
                    name = f"{first_name} {last_name}"
            except AttributeError:
                pass
            title = name
        elif reply.forward_sender_name:
            title = name = sender_name = reply.forward_sender_name
            sid = 0
        elif reply.from_user:
            try:
                sid = reply.from_user.id
                try:
                    name = first_name = reply.from_user.first_name
                except TypeError:
                    name = "Unknown"
                if reply.from_user.last_name:
                    last_name = reply.from_user.last_name
                    name = f"{first_name} {last_name}"
            except AttributeError:
                pass
            title = name
        return sid, title, name

    async def t_or_c(message):
        if message.text:
            return message.text
        elif message.caption:
            return message.caption
        else:
            return ""

    async def get_emoji(message):
        if message.from_user.emoji_status:
            emoji_status = str(message.from_user.emoji_status.custom_emoji_id)
        else:
            emoji_status = ""
        return emoji_status

    async def quotly(payload):
        r = await Tools.fetch.post(
            "https://quote.yuri.ly/quote/generate.png", json=payload
        )

        if not r.is_error:
            return r.read()
        else:
            raise QuotlyException(r.json())

    @staticmethod
    async def make_carbonara(
        code: str, bg_color: str, theme: str, language: str
    ) -> BytesIO:
        url = "https://carbonara.solopov.dev/api/cook"
        json_data = {
            "code": code,
            "paddingVertical": "56px",
            "paddingHorizontal": "56px",
            "backgroundMode": "color",
            "backgroundColor": bg_color,
            "theme": theme,
            "language": language,
            "fontFamily": "Cascadia Code",
            "fontSize": "14px",
            "windowControls": True,
            "widthAdjustment": True,
            "lineNumbers": True,
            "firstLineNumber": 1,
            "name": f"{BOT_NAME}-Carbon",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=json_data) as resp:
                return BytesIO(await resp.read())

    @staticmethod
    async def get_message_content(message):
        if message.text:
            return message.text, "text"
        elif message.document:
            doc = await message.download()
            async with aiofiles.open(doc, mode="r") as f:
                content = await f.read()
            os.remove(doc)
            return content, "document"
        return None, None
