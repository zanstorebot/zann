import asyncio
import io
import json
import math
import multiprocessing
import os
import random
import re
import subprocess
import time
import traceback
from base64 import b64decode
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from enum import IntEnum, unique
from html import escape
from re import compile as compilere
from re import sub
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4
from pathlib import Path

import mimetypes
import aiofiles
import aiohttp
import pytz
import qrcode
import requests
from httpx import AsyncClient, Timeout
from pyrogram import enums
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.types import ChatPrivileges, MessageEntity

from clients import bot
from config import API_BOTCHAX, BOT_ID, BOT_NAME, CODEQR, URL_LOGO
from database import dB
from logs import logger

CATBOX_API = "https://catbox.moe/user/api.php"

max_workers = multiprocessing.cpu_count() * 5
exc_ = ThreadPoolExecutor(max_workers=max_workers)


class HTML:
    @staticmethod
    async def cleanhtml(raw_html: str) -> str:
        """Clean html data."""
        cleanr = compilere("<.*?>")
        return sub(cleanr, "", raw_html)

    @staticmethod
    async def escape_markdown(text: str) -> str:
        """Escape markdown data."""
        escape_chars = r"\*_`\["
        return sub(r"([%s])" % escape_chars, r"\\\1", text)

    @staticmethod
    async def mention_html(name: str, user_id: int) -> str:
        """Mention user in html format."""
        name = escape(name)
        return f'<a href="tg://user?id={user_id}">{name}</a>'

    @staticmethod
    async def mention_markdown(name: str, user_id: int) -> str:
        """Mention user in markdown format."""
        return f"[{(await HTML.escape_markdown(name))}](tg://user?id={user_id})"


class ApiImage:
    async def wall(client):
        anime_channel = random.choice(["@animehikarixa", "@Anime_WallpapersHD"])
        animenya = [
            anime
            async for anime in client.search_messages(
                anime_channel, filter=enums.MessagesFilter.PHOTO
            )
        ]
        return random.choice(animenya)

    def waifu():
        url = "https://www.waifu.im/search"
        response = requests.get(url)
        content = response.text
        start_index = content.find("var files = [") + len("var files = ")
        end_index = content.find("]", start_index)
        files_str = content[start_index:end_index]
        files = [file.strip('" ') for file in files_str.split(",")]
        return random.choice(files)


class Tools:
    interact_with_to_delete = []
    JAKARTA_TZ = pytz.timezone("Asia/Jakarta")

    fetch = AsyncClient(
        http2=True,
        verify=False,
        headers={
            "Accept-Language": "en-US,en;q=0.9,id-ID;q=0.8,id;q=0.7",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edge/107.0.1418.42",
        },
        timeout=Timeout(300),
    )

    @classmethod
    async def close_fetch(cls):
        await cls.fetch.aclose()

    BASE = "https://batbin.me/"

    dev_paste = {
        "nekobin": {
            "URL": "https://nekobin.com/api/documents",
            "RAV": "result.key",
            "GAS": "https://github.com/nekobin/nekobin",
        },
        "pasty": {
            "URL": "https://pasty.lus.pm/api/v2/pastes",
            "HEADERS": {
                "User-Agent": "PyroGramBot/6.9",
                "Content-Type": "application/json",
            },
            "RAV": "id",
            "GAS": "https://github.com/lus/pasty",
            "AVDTS": "modificationToken",
        },
        "pasting": {
            "URL": "https://pasting.codes/api",
        },
    }
    formats = [
        "webm",
        "mkv",
        "flv",
        "vob",
        "ogv",
        "ogg",
        "rrc",
        "gifv",
        "mng",
        "mov",
        "avi",
        "qt",
        "wmv",
        "yuv",
        "rm",
        "asf",
        "amv",
        "mp4",
        "m4p",
        "m4v",
        "mpg",
        "mp2",
        "mpeg",
        "mpe",
        "mpv",
        "m4v",
        "svi",
        "3gp",
        "3g2",
        "mxf",
        "roq",
        "nsv",
        "flv",
        "f4v",
        "f4p",
        "f4a",
        "f4b",
    ]
    parse_words = [
        "first",
        "last",
        "fullname",
        "id",
        "mention",
        "username",
        "chatname",
        "day",
        "date",
        "month",
        "year",
        "hour",
        "minutes",
    ]
    kode_bahasa = {
        "Afrikaans": "af",
        "Arabic": "ar",
        "Chinese": "zh-cn",
        "Czech": "cs",
        "German": "de",
        "Greek": "el",
        "English": "en",
        "Spanish": "es",
        "French": "fr",
        "Hindi": "hi",
        "Indonesian": "id",
        "Icelandic": "is",
        "Italian": "it",
        "Japanese": "ja",
        "Javanese": "jw",
        "Korean": "ko",
        "Latin": "la",
        "Myanmar": "my",
        "Nepali": "ne",
        "Dutch": "nl",
        "Portuguese": "pt",
        "Russian": "ru",
        "Sundanese": "su",
        "Swedish": "sv",
        "Thailand": "th",
        "Filipino": "tl",
        "Turkish": "tr",
        "Vietnamese": "vi",
        "Catalan": "ca",
        "Danish": "da",
        "Finnish": "fi",
        "Hungarian": "hu",
        "Polish": "pl",
        "Ukrainian": "uk",
        "Taiwan": "zh-tw",
    }

    @staticmethod
    async def paste_content(content: str) -> Optional[str]:
        service_url = "https://paste.rs"

        async with aiohttp.ClientSession() as session:
            async with session.post(service_url, data=content) as response:
                if response.status != 201:
                    return None

                raw_url = await response.text()
                return raw_url.strip()

        return None

    @staticmethod
    def check_duration(file_path):
        command = [
            "ffprobe",
            "-loglevel",
            "quiet",
            "-print_format",
            "json",
            "-show_format",
            "-show_streams",
            file_path,
        ]

        pipe = subprocess.Popen(
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        )
        out, err = pipe.communicate()
        _json = json.loads(out)

        if "format" in _json:
            if "duration" in _json["format"]:
                return float(_json["format"]["duration"])

        if "streams" in _json:
            for s in _json["streams"]:
                if "duration" in s:
                    return float(s["duration"])

        return "Unknown"

    @staticmethod
    def get_readable_time(seconds: int) -> str:
        count = 0
        ping_time = ""
        time_list = []
        time_suffix_list = ["d", "m", "j", "h"]
        while count < 4:
            count += 1
            if count < 3:
                remainder, result = divmod(seconds, 60)
            else:
                remainder, result = divmod(seconds, 24)
            if seconds == 0 and remainder == 0:
                break
            time_list.append(int(result))
            seconds = int(remainder)
        for i in range(len(time_list)):
            time_list[i] = str(time_list[i]) + time_suffix_list[i]
        if len(time_list) == 4:
            ping_time += time_list.pop() + ", "
        time_list.reverse()
        ping_time += ":".join(time_list)
        return ping_time

    @staticmethod
    def convert_bytes(size: float) -> str:
        if not size:
            return ""
        power = 1024
        t_n = 0
        power_dict = {0: " ", 1: "Kb", 2: "Mb", 3: "Gb", 4: "Tb"}
        while size > power:
            size /= power
            t_n += 1
        return "{:.2f} {}B".format(size, power_dict[t_n])

    @staticmethod
    def seconds_to_min(seconds):
        if seconds is not None:
            seconds = int(seconds)
            d, h, m, s = (
                seconds // (3600 * 24),
                seconds // 3600 % 24,
                seconds % 3600 // 60,
                seconds % 3600 % 60,
            )
            if d > 0:
                return "{:02d}:{:02d}:{:02d}:{:02d}".format(d, h, m, s)
            elif h > 0:
                return "{:02d}:{:02d}:{:02d}".format(h, m, s)
            elif m > 0:
                return "{:02d}:{:02d}".format(m, s)
            elif s > 0:
                return "00:{:02d}".format(s)
        return "-"

    @staticmethod
    def humanbytes(size):
        if not size:
            return ""
        power = 2**10
        raised_to_pow = 0
        dict_power_n = {0: "", 1: "Ki", 2: "Mi", 3: "Gi", 4: "Ti"}
        while size > power:
            size /= power
            raised_to_pow += 1
        return str(round(size, 2)) + " " + dict_power_n[raised_to_pow] + "B"

    @staticmethod
    def convert_seconds(seconds: Union[int, float]) -> str:
        if seconds == 0:
            return "-"

        result_converted = []
        if seconds >= 1:
            result_converted.append(
                f"{int(seconds)} Second{'s' if int(seconds) > 1 else ''}"
            )
        elif seconds > 0:
            result_converted.append(
                f"{'{:.3f}'.format(seconds).rstrip('0').rstrip('.')} Seconds"
            )

        return ", ".join(result_converted)

    @staticmethod
    def time_formatter(milliseconds: int) -> str:
        seconds, milliseconds = divmod(int(milliseconds), 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        days, hours = divmod(hours, 24)
        tmp = (
            ((str(days) + " day(s), ") if days else "")
            + ((str(hours) + " hour(s), ") if hours else "")
            + ((str(minutes) + " minute(s), ") if minutes else "")
            + ((str(seconds) + " second(s), ") if seconds else "")
            + ((str(milliseconds) + " millisecond(s), ") if milliseconds else "")
        )
        return tmp[:-2]

    @staticmethod
    async def progress(current, total, message, start, type_of_ps, file_name=None):
        now = time.time()
        diff = now - start
        if round(diff % 10.00) == 0 or current == total:
            percentage = current * 100 / total
            speed = current / diff
            elapsed_time = round(diff) * 1000
            if elapsed_time == 0:
                return
            time_to_completion = round((total - current) / speed) * 1000
            estimated_total_time = elapsed_time + time_to_completion
            progress_str = "{0}{1} {2}%\n".format(
                "".join(["●" for i in range(math.floor(percentage / 10))]),
                "".join(["○" for i in range(10 - math.floor(percentage / 10))]),
                round(percentage, 2),
            )
            tmp = progress_str + "{0} of {1}\nETA: {2}".format(
                Tools.humanbytes(current),
                Tools.humanbytes(total),
                Tools.time_formatter(estimated_total_time),
            )
            if file_name:
                try:
                    await message.edit(
                        "{}\n**File Name:** `{}`\n{}".format(type_of_ps, file_name, tmp)
                    )
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                except MessageNotModified:
                    pass
            else:
                try:
                    await message.edit("{}\n{}".format(type_of_ps, tmp))
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                except MessageNotModified:
                    pass

    @staticmethod
    def parse_text(reply):
        msg = reply.text.split()
        return msg[0], msg[1]

    @staticmethod
    async def dl_pic(client, download):
        path = await client.download_media(download)
        with open(path, "rb") as f:
            content = f.read()
        os.remove(path)
        get_photo = io.BytesIO(content)
        return get_photo

    @staticmethod
    def gen_views():
        views = random.randint(1000000, 10000000)
        formatted_views = f"{views:,} views"
        return formatted_views

    @staticmethod
    async def get_logo():
        photo = "storage/cache/LOGO_BOT.jpg"
        if not os.path.exists(photo):
            await Tools.bash(f"wget {URL_LOGO} -O {photo}")
            return photo
        return photo

    @staticmethod
    async def create_logs(client):
        try:
            chat_id = None
            nama = f"{BOT_NAME} ⚡️ Logs"
            async for dialog in client.get_dialogs():
                if dialog.chat.type == enums.ChatType.SUPERGROUP:
                    if dialog.chat.title == nama:
                        chat_id = dialog.chat.id
            if chat_id:
                logger.info(f"{nama} {chat_id}")
                await dB.set_var(client.me.id, "GRUPLOG", chat_id)
                try:
                    await client.add_chat_members(chat_id, bot.me.username)
                    privileges = ChatPrivileges()
                    await client.promote_chat_member(
                        chat_id=chat_id,
                        user_id=BOT_ID,
                        privileges=privileges,
                    )
                except Exception:
                    logger.error(f"error: {traceback.format_exc()}")
                link = await client.export_chat_invite_link(chat_id)
                if chat_id not in await dB.get_list_from_var(
                    client.me.id, "BLACKLIST_GCAST"
                ):
                    await dB.add_to_var(client.me.id, "BLACKLIST_GCAST", chat_id)
                return link
            else:
                des = "Jangan Keluar Dari Grup Log Ini\n\nPowered by: AliceCodes"
                gc = await client.create_supergroup(nama, des)
                photo = await Tools.get_logo()
                gmbr = {"video": photo} if photo.endswith(".mp4") else {"photo": photo}
                await client.set_chat_photo(gc.id, **gmbr)
                await dB.set_var(client.me.id, "GRUPLOG", gc.id)
                if os.path.exists(photo):
                    os.remove(photo)
                link = await client.export_chat_invite_link(gc.id)
                await client.add_chat_members(gc.id, bot.me.username)
                privileges = ChatPrivileges()
                await client.promote_chat_member(
                    chat_id=gc.id,
                    user_id=BOT_ID,
                    privileges=privileges,
                )

                if gc.id not in await dB.get_list_from_var(
                    client.me.id, "BLACKLIST_GCAST"
                ):
                    await dB.add_to_var(client.me.id, "BLACKLIST_GCAST", gc.id)
                return link
        except Exception as er:
            logger.error(traceback.format_exc())
            return f"<b>ERROR:</b> {str(er)}"

    @staticmethod
    async def send_media(client, msgtype: int):
        GET_FORMAT = {
            Tools.Types.TEXT.value: client.send_message,
            Tools.Types.DOCUMENT.value: client.send_document,
            Tools.Types.PHOTO.value: client.send_photo,
            Tools.Types.VIDEO.value: client.send_video,
            Tools.Types.STICKER.value: client.send_sticker,
            Tools.Types.AUDIO.value: client.send_audio,
            Tools.Types.VOICE.value: client.send_voice,
            Tools.Types.VIDEO_NOTE.value: client.send_video_note,
            Tools.Types.ANIMATION.value: client.send_animation,
            Tools.Types.ANIMATED_STICKER.value: client.send_sticker,
            Tools.Types.CONTACT: client.send_contact,
        }
        return GET_FORMAT[msgtype]
      
    @staticmethod
    async def send_message(client, msgtype2: int):
        GET_FORMAT = {
            Tools.Types.TEXT.value: client.send_message,
            Tools.Types.DOCUMENT.value: client.send_document,
            Tools.Types.PHOTO.value: client.send_photo,
            Tools.Types.VIDEO.value: client.send_video,
            Tools.Types.STICKER.value: client.send_sticker,
            Tools.Types.AUDIO.value: client.send_audio,
            Tools.Types.VOICE.value: client.send_voice,
            Tools.Types.VIDEO_NOTE.value: client.send_video_note,
            Tools.Types.ANIMATION.value: client.send_animation,
            Tools.Types.ANIMATED_STICKER.value: client.send_sticker,
            Tools.Types.CONTACT: client.send_contact,
        }
        return GET_FORMAT[msgtype2]

    
    @staticmethod
    @unique
    class Types(IntEnum):
        TEXT = 1
        DOCUMENT = 2
        PHOTO = 3
        VIDEO = 4
        STICKER = 5
        AUDIO = 6
        VOICE = 7
        VIDEO_NOTE = 8
        ANIMATION = 9
        ANIMATED_STICKER = 10
        CONTACT = 11

    @staticmethod
    async def escape_tag(
        c,
        ore: int,
        text: str,
        parse_words: list,
    ) -> str:
        orang = await dB.get_userdata(ore)
        if not orang:
            return ""
        text = re.sub(r"~ \[.*?\|.*?\]", "", text)
        days_mapping = {
            "Monday": "Senin",
            "Tuesday": "Selasa",
            "Wednesday": "Rabu",
            "Thursday": "Kamis",
            "Friday": "Jumat",
            "Saturday": "Sabtu",
            "Sunday": "Minggu",
        }
        months_mapping = {
            "January": "Januari",
            "February": "Februari",
            "March": "Maret",
            "April": "April",
            "May": "Mei",
            "June": "Juni",
            "July": "Juli",
            "August": "Agustus",
            "September": "September",
            "October": "Oktober",
            "November": "November",
            "December": "Desember",
        }
        now = datetime.now(Tools.JAKARTA_TZ)
        current_time = {
            "day": days_mapping[now.strftime("%A")],
            "date": now.strftime("%d"),
            "month": months_mapping[now.strftime("%B")],
            "year": now.strftime("%Y"),
            "hour": now.strftime("%H"),
            "minutes": now.strftime("%M"),
        }
        teks = await Tools.escape_one(text, Tools.parse_words)
        if teks:
            teks = teks.format(
                first=orang["depan"],
                last=orang["belakang"],
                mention=orang["full"],
                username=orang["username"],
                fullname=orang["full"],
                id=orang["_id"],
                **current_time,
            )
        else:
            teks = ""

        return teks

    @staticmethod
    async def escape_one(text: str, valids: List[str]) -> str:
        new_text = ""
        idx = 0
        while idx < len(text):
            if text[idx] == "{":
                if idx + 1 < len(text) and text[idx + 1] == "{":
                    idx += 2
                    new_text += "{{{{"
                    continue
                success = False
                for v in valids:
                    if text[idx:].startswith("{" + v + "}"):
                        success = True
                        break
                if success:
                    new_text += text[idx : idx + len(v) + 2]
                    idx += len(v) + 2
                    continue
                new_text += "{{"

            elif text[idx] == "}":
                if idx + 1 < len(text) and text[idx + 1] == "}":
                    idx += 2
                    new_text += "}}}}"
                    continue
                new_text += "}}"

            else:
                new_text += text[idx]
            idx += 1

        return new_text

    @staticmethod
    def get_file_id(message):
        media_types = {
            "photo": "photo",
            "animation": "animation",
            "audio": "audio",
            "document": "document",
            "video": "video",
            "video_note": "video_note",
            "voice": "voice",
            "sticker": "sticker",
        }

        if message.media:
            for media_type in media_types:
                media_obj = getattr(message, media_type, None)
                if media_obj is not None:
                    if media_type == "photo":
                        media_obj = message.photo

                    return {
                        "file_id": media_obj.file_id,
                        "file_unique_id": media_obj.file_unique_id,
                        "message_type": media_type,
                        "file_name": getattr(media_obj, "file_name", None),
                        "mime_type": getattr(media_obj, "mime_type", None),
                        "file_size": getattr(media_obj, "file_size", None),
                        "width": getattr(media_obj, "width", None),
                        "height": getattr(media_obj, "height", None),
                        "duration": getattr(media_obj, "duration", None),
                    }
        return False

    @staticmethod
    async def screen_web(url, full: bool = False):
        url = "https://" + url if not url.startswith("http") else url
        payload = {
            "url": url,
            "width": 1920,
            "height": 1080,
            "scale": 1,
            "format": "jpeg",
        }
        if full:
            payload["full"] = True
        data = await Tools.post(
            "https://webscreenshot.vercel.app/api",
            data=payload,
        )
        if "image" not in data:
            return None
        b = data["image"].replace("data:image/jpeg;base64,", "")
        file = io.BytesIO(b64decode(b))
        file.name = "webss.jpg"
        return file

    @staticmethod
    def qr_gen(content):
        return {
            "data": content,
            "config": {
                "body": "circle-zebra",
                "eye": "frame13",
                "eyeBall": "ball14",
                "erf1": [],
                "erf2": [],
                "erf3": [],
                "brf1": [],
                "brf2": [],
                "brf3": [],
                "bodyColor": "#000000",
                "bgColor": "#FFFFFF",
                "eye1Color": "#000000",
                "eye2Color": "#000000",
                "eye3Color": "#000000",
                "eyeBall1Color": "#000000",
                "eyeBall2Color": "#000000",
                "eyeBall3Color": "#000000",
                "gradientColor1": "",
                "gradientColor2": "",
                "gradientType": "linear",
                "gradientOnEyes": "true",
                "logo": "",
                "logoMode": "default",
            },
            "size": 1000,
            "download": "imageUrl",
            "file": "png",
        }



    @staticmethod
    async def upload_thumb(media):
        media_path = Path(media)
        if not media_path.is_file():
            raise FileNotFoundError(f"File tidak ditemukan: {media}")

        content_type = mimetypes.guess_type(media_path.name)[0] or "application/octet-stream"
        timeout = aiohttp.ClientTimeout(total=120)

        async with aiohttp.ClientSession(timeout=timeout) as session:
            form_data = aiohttp.FormData()
            form_data.add_field("reqtype", "fileupload")
            async with aiofiles.open(media_path, mode="rb") as file:
                form_data.add_field(
                    "fileToUpload",
                    await file.read(),
                    filename=media_path.name,
                    content_type=content_type,
                )
            async with session.post(CATBOX_API, data=form_data) as response:
                response.raise_for_status()
                result = (await response.text()).strip()
                if not result.startswith("https://"):
                    raise ValueError(f"Upload gagal: {result}")
                return result

    @staticmethod
    async def upload_media(message):
        media = message.reply_to_message
        if not media:
            raise Exception("Silakan balas ke media.")

        file_path = await media.download()
        media_path = Path(file_path)

        try:
            if not media_path.is_file():
                raise Exception("Gagal mengunduh media.")
            if media_path.stat().st_size == 0:
                raise Exception("File media kosong.")

            filename = media_path.name
            content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
            async with aiofiles.open(media_path, "rb") as file:
                file_data = await file.read()

            timeout = aiohttp.ClientTimeout(total=300, sock_connect=30, sock_read=120)
            errors = []

            for _ in range(3):
                try:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        form_data = aiohttp.FormData()
                        form_data.add_field("reqtype", "fileupload")
                        form_data.add_field(
                            "fileToUpload",
                            file_data,
                            filename=filename,
                            content_type=content_type,
                        )
                        async with session.post(CATBOX_API, data=form_data) as response:
                            result = (await response.text()).strip()
                            if response.status == 200 and result.startswith("https://"):
                                return result
                            errors.append(f"{response.status} {result[:100]}")
                except Exception as exc:
                    errors.append(str(exc)[:100])
                await asyncio.sleep(2)

            raise Exception(f"Catbox gagal setelah 3 percobaan. {errors}")
        finally:
            if media_path.exists():
                media_path.unlink()
                  
    @staticmethod
    async def interact_with(message):
        await asyncio.sleep(1)
        response = [
            msg
            async for msg in message._client.get_chat_history(message.chat.id, limit=1)
        ]
        seconds_waiting = 0

        while response[0].from_user.is_self:
            seconds_waiting += 1
            if seconds_waiting >= 5:
                raise RuntimeError("bot didn't answer in 5 seconds")

            await asyncio.sleep(1)
            response = [
                msg
                async for msg in message._client.get_chat_history(
                    message.chat.id, limit=1
                )
            ]

        Tools.interact_with_to_delete.append(message.id)
        Tools.interact_with_to_delete.append(response[0].id)

        return response[0]
      
        @staticmethod
        async def get(url: str, *args, **kwargs) -> Any:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, *args, **kwargs) as resp:
                    try:
                        data = await resp.json()
                    except Exception:
                        data = await resp.text()
                return data

    @staticmethod
    async def head(url: str, *args, **kwargs) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.head(url, *args, **kwargs) as resp:
                try:
                    data = await resp.json()
                except Exception:
                    data = await resp.text()
            return data

    @staticmethod
    async def post(url: str, *args, **kwargs) -> Any:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, *args, **kwargs) as resp:
                try:
                    data = await resp.json()
                except Exception:
                    data = await resp.text()
            return data

    @staticmethod
    async def paste(content: str) -> Optional[str]:
        if "&quot;" in content:
            content = content.replace("&quot;", "'")
        resp = await Tools.post(f"{Tools.BASE}api/v2/paste", data=content)
        if not resp["success"]:
            return None
        return Tools.BASE + resp["message"]

    @staticmethod
    async def copy_link(client, link):
        try:
            if "?single" in link:
                link = link.replace("?single", "")
            msg_id = int(link.split("/")[-1])

            if "t.me/c/" in link:
                return link

            get_chat = str(link.split("/")[-2])

            if "-100" not in link:
                chat = await client.get_chat(get_chat)
                chat_id = str(chat.id)
                if chat_id.startswith("-100"):
                    chat_id = chat_id[4:]

                new_link = f"https://t.me/c/{chat_id}/{msg_id}"
                return new_link

            return link

        except Exception as e:
            return f"Error: {str(e)}"

    @staticmethod
    def extract_ids_from_link(link):
        type = "t.me/c/" in link
        chat_id = (
            int("-100" + str(link.split("/")[-2])) if type else str(link.split("/")[-2])
        )
        msg_id = int(link.split("/")[-1])
        return chat_id, msg_id

    @staticmethod
    def get_link(link):
        chatid, msgid = None, None
        if "https://t.me/" not in link:
            return None, None
        try:
            datas = link.split("/")
            if len(datas) == 4:
                chatid = datas[3]
                msgid = None
                return chatid, msgid
            if len(datas) >= 5:
                if "https://t.me/c/" in link:
                    chatid = int("-100" + datas[-2])
                    msgid = int(datas[-1].split("?")[0])
                else:
                    chatid = datas[-2]
                    msgid = int(datas[-1].split("?")[0])
        except (ValueError, IndexError) as e:
            return None, None
        return chatid, msgid

    @staticmethod
    def extract_story_link(link):
        type = "t.me/c/" in link
        chat_id = (
            int("-100" + str(link.split("/")[-2])) if type else str(link.split("/")[-3])
        )
        msg_id = int(link.split("/")[-1])
        return chat_id, msg_id

    @staticmethod
    async def download_media(type, client, proses, message, story: bool = False):
        msg = message.reply_to_message or message
        text = type.caption or ""
        if story:
            if type.photo:
                media = await client.download_media(
                    type.photo.file_id,
                )
                await client.send_photo(
                    message.chat.id,
                    media,
                    caption=text,
                    reply_to_message_id=msg.id,
                )
                await proses.delete()
                os.remove(media)

            elif type.video:
                media = await client.download_media(
                    type.video.file_id,
                )
                thumbnail = await client.download_media(type.video.thumbs[-1]) or None
                await client.send_video(
                    message.chat.id,
                    video=media,
                    duration=type.video.duration,
                    caption=text,
                    thumb=thumbnail,
                    reply_to_message_id=msg.id,
                )
                await proses.delete()
                os.remove(media)
                os.remove(thumbnail)
        else:
            if type.photo:
                media = await client.download_media(
                    type,
                    progress=Tools.progress,
                    progress_args=(
                        proses,
                        time.time(),
                        "Download Photo",
                        type.photo.file_id,
                    ),
                )
                await client.send_photo(
                    message.chat.id,
                    media,
                    caption=text,
                    reply_to_message_id=msg.id,
                )
                await proses.delete()
                os.remove(media)

            elif type.animation:
                media = await client.download_media(
                    type,
                    progress=Tools.progress,
                    progress_args=(
                        proses,
                        time.time(),
                        "Download Animation",
                        type.animation.file_id,
                    ),
                )
                await client.send_animation(
                    message.chat.id,
                    animation=media,
                    caption=text,
                    reply_to_message_id=msg.id,
                )
                await proses.delete()
                os.remove(media)

            elif type.voice:
                media = await client.download_media(
                    type,
                    progress=Tools.progress,
                    progress_args=(
                        proses,
                        time.time(),
                        "Download Voice",
                        type.voice.file_id,
                    ),
                )
                await client.send_voice(
                    message.chat.id,
                    voice=media,
                    caption=text,
                    reply_to_message_id=msg.id,
                )
                await proses.delete()
                os.remove(media)

            elif type.audio:
                media = await client.download_media(
                    type,
                    progress=Tools.progress,
                    progress_args=(
                        proses,
                        time.time(),
                        "Download Audio",
                        type.audio.file_id,
                    ),
                )
                thumbnail = await client.download_media(type.audio.thumbs[-1]) or None
                await client.send_audio(
                    message.chat.id,
                    audio=media,
                    duration=type.audio.duration,
                    caption=text,
                    thumb=thumbnail,
                    reply_to_message_id=msg.id,
                )
                await proses.delete()
                os.remove(media)
                os.remove(thumbnail)

            elif type.document:
                media = await client.download_media(
                    type,
                    progress=Tools.progress,
                    progress_args=(
                        proses,
                        time.time(),
                        "Download Document",
                        type.document.file_id,
                    ),
                )
                await client.send_document(
                    message.chat.id,
                    document=media,
                    caption=text,
                    reply_to_message_id=msg.id,
                )
                await proses.delete()
                os.remove(media)

            elif type.video:
                media = await client.download_media(
                    type,
                    progress=Tools.progress,
                    progress_args=(
                        proses,
                        time.time(),
                        "Download Video",
                        type.video.file_id,
                    ),
                )
                thumbnail = await client.download_media(type.video.thumbs[-1]) or None
                await client.send_video(
                    message.chat.id,
                    video=media,
                    duration=type.video.duration,
                    caption=text,
                    thumb=thumbnail,
                    reply_to_message_id=msg.id,
                )
                await proses.delete()
                os.remove(media)
                os.remove(thumbnail)

    query_textpro = [
        [
            {"Magma": "magma"},
            {"Valentine": "valentine"},
            {"Neon Light": "neon-light"},
            {"Neon Galaxy": "neon-galaxy"},
            {"Art Papper": "art-papper"},
            {"Glossy": "glossy"},
        ],
        [
            {"Water Color": "water-color"},
            {"Robot": "robot"},
            {"Neon Devil": "neon-devil"},
            {"Sky Text": "sky-text"},
            {"Writing": "writing"},
            {"Porn Hub": "pornhub"},
        ],
        [
            {"Holographic": "holographic"},
            {"Horror Blood": "horor-blood"},
            {"Larva": "larva"},
            {"Toxic": "toxic-bokeh"},
            {"Stroberi": "stroberi"},
            {"Koi Pish": "koi"},
        ],
        [
            {"Rusty": "rusty"},
            {"Captain Amerika": "captain"},
            {"Christmas": "christmas"},
            {"Black Pink": "black-pink"},
            {"Thunder": "thunder2"},
            {"3D Stone": "3dstone"},
        ],
        [
            {"Harry Potter": "harry-potter"},
            {"Natural Leaves": "natural-leaves"},
            {"Space": "space"},
            {"Joker Logo": "joker-logo"},
            {"Blood": "blood"},
            {"Astone": "astone"},
        ],
        [
            {"Grafity Text": "grafity-text"},
            {"Grafity Text2": "grafity-text2"},
            {"Ninja Logo": "ninja-logo"},
            {"Lion Logo": "lion-logo"},
            {"Avengers Logo": "avengers-logo"},
        ],
    ]

    @staticmethod
    async def gen_text_pro(args, command):
        text = args.replace(" ", "%20")
        if command in ["pornhub", "astone", "avengers-logo", "grafity-text2"]:
            text1 = text.split("%20")[0]
            text2 = text.split("%20")[1]
            url = f"https://api.botcahx.eu.org/api/textpro/{command}?text={text1}&text2={text2}&apikey={API_BOTCHAX}"
        else:
            url = f"https://api.botcahx.eu.org/api/textpro/{command}?text={text}&apikey={API_BOTCHAX}"
        result = await Tools.fetch.get(url)
        if result.status_code == 200:
            logger.info(f"Url: {url}")
            return url
        else:
            return f"ERROR: {result.status_code}"

    @staticmethod
    async def bash(cmd):
        try:
            process = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            err = stderr.decode().strip()
            out = stdout.decode().strip()
            return out, err
        except NotImplementedError:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )
            stdout, stderr = process.communicate()
            err = stderr.decode().strip()
            out = stdout.decode().strip()
            return out, err

    @staticmethod
    def extract_filename(url):
        try:
            parts = url.split("/")
            for part in parts:
                if ".jpg" in part:
                    filename = part.split("?")[0]
                    return filename

            return ""

        except Exception as e:
            logger.error(f"Error extracting filename: {str(e)}")
            return ""

    @staticmethod
    async def get_media_data(url, format):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        media_data = await response.read()
                        media = io.BytesIO(media_data)
                        media.name = f"{str(uuid4())}.{format}"
                        return media
                    else:
                        return None
        except aiohttp.client_exceptions.InvalidURL as e:
            print(f"Invalid URL: {url} - {str(e)}")
            return None

    OPTIONAL_ATTRS = {
        "url": str,
        "user": dict,
        "language": str,
        "custom_emoji_id": int,
        "text": str,
        "phone_number": str,
        "email": str,
        "bot_command": str,
        "hashtag": str,
        "cashtag": str,
        "bank_card": str,
        "bold": bool,
        "italic": bool,
        "underline": bool,
        "strikethrough": bool,
        "code": bool,
        "pre": bool,
        "text_link": str,
        "text_mention": dict,
    }

    @staticmethod
    def get_entity(entity: MessageEntity) -> Dict:
        entity_dict = {
            "type": str(entity.type),
            "offset": entity.offset,
            "length": entity.length,
        }

        for attr, attr_type in Tools.OPTIONAL_ATTRS.items():
            if hasattr(entity, attr):
                value = getattr(entity, attr)
                if value is not None:
                    entity_dict[attr] = value

        return entity_dict

    @staticmethod
    def convert_entity(entity_dict):
        entity_type = entity_dict["type"].replace("MessageEntityType.", "")
        try:
            entity_type = enums.MessageEntityType[entity_type]
        except KeyError as e:
            raise ValueError(f"Invalid entity type: {entity_type}") from e
        entity = MessageEntity(
            type=entity_type, offset=entity_dict["offset"], length=entity_dict["length"]
        )
        if "url" in entity_dict:
            entity.url = entity_dict["url"]
        if "user" in entity_dict:
            entity.user = entity_dict["user"]
        if "language" in entity_dict:
            entity.language = entity_dict["language"]
        if "custom_emoji_id" in entity_dict:
            entity.custom_emoji_id = entity_dict["custom_emoji_id"]

        return entity

    @staticmethod
    def dump_entity(text: str, entities: Optional[List[MessageEntity]] = None) -> Dict:
        return {
            "text": text,
            "entities": [Tools.get_entity(entity) for entity in (entities or [])],
        }

    @staticmethod
    def get_msg_entities(message) -> List[dict]:
        entities = []

        if message.entities:
            entities.extend(
                {
                    "type": entity.type.name.lower(),
                    "offset": entity.offset,
                    "length": entity.length,
                }
                for entity in message.entities
            )
        elif message.caption_entities:
            entities.extend(
                {
                    "type": entity.type.name.lower(),
                    "offset": entity.offset,
                    "length": entity.length,
                }
                for entity in message.entities
            )
        return entities

    @staticmethod
    def jakartaTime(data):
        from datetime import datetime

        import pytz

        utc_time = datetime.fromisoformat(data.replace("Z", "+00:00"))
        jakarta_tz = pytz.timezone("Asia/Jakarta")
        jakarta_time = utc_time.astimezone(jakarta_tz)
        date = jakarta_time.strftime("%Y-%m-%d %H:%M:%S")
        return date

    @staticmethod
    async def escape_filter(
        m,
        text: str,
        parse_words: list,
    ) -> str:
        if m.chat.type in [
            enums.ChatType.SUPERGROUP,
            enums.ChatType.GROUP,
            enums.ChatType.CHANNEL,
        ]:
            chat_name = escape(m.chat.title)
        else:
            chat_name = escape(m.from_user.first_name)
        days_mapping = {
            "Monday": "Senin",
            "Tuesday": "Selasa",
            "Wednesday": "Rabu",
            "Thursday": "Kamis",
            "Friday": "Jumat",
            "Saturday": "Sabtu",
            "Sunday": "Minggu",
        }
        months_mapping = {
            "January": "Januari",
            "February": "Februari",
            "March": "Maret",
            "April": "April",
            "May": "Mei",
            "June": "Juni",
            "July": "Juli",
            "August": "Agustus",
            "September": "September",
            "October": "Oktober",
            "November": "November",
            "December": "Desember",
        }
        now = datetime.now(Tools.JAKARTA_TZ)
        current_time = {
            "day": days_mapping[now.strftime("%A")],
            "date": now.strftime("%d"),
            "month": months_mapping[now.strftime("%B")],
            "year": now.strftime("%Y"),
            "hour": now.strftime("%H"),
            "minutes": now.strftime("%M"),
        }
        teks = await Tools.escape_one(text, parse_words)
        if teks:
            teks = teks.format(
                first=escape(m.from_user.first_name),
                last=escape(m.from_user.last_name or m.from_user.first_name),
                mention=m.from_user.mention,
                username=(
                    "@" + (await HTML.escape_markdown(escape(m.from_user.username)))
                    if m.from_user.username
                    else m.from_user.mention
                ),
                fullname=" ".join(
                    (
                        [
                            escape(m.from_user.first_name),
                            escape(m.from_user.last_name),
                        ]
                        if m.from_user.last_name
                        else [escape(m.from_user.first_name)]
                    ),
                ),
                chatname=chat_name,
                id=m.from_user.id,
                **current_time,
            )
        else:
            teks = ""

        return teks

    @staticmethod
    def extract_user(message):
        user_id = None
        user_first_name = None
        user = None

        if len(message.command) > 1:
            entities = message.entities or []
            if (
                len(entities) > 1
                and entities[1].type == enums.MessageEntityType.TEXT_MENTION
            ):
                required_entity = message.entities[1]
                user_id = required_entity.user.id
                user_first_name = required_entity.user.first_name
                user = required_entity.user
            else:
                user_id = message.command[1]
                user_first_name = user_id
                user = True

            try:
                user_id = int(user_id)
            except ValueError:
                pass

        elif message.reply_to_message:
            user_id, user_first_name, user = Tools.is_valid(message.reply_to_message)

        elif message:
            user_id, user_first_name, user = Tools.is_valid(message)

        return (user_id, user_first_name, user)

    @staticmethod
    def is_valid(message):
        user_id = None
        user_first_name = None
        user = None

        if message.from_user:
            user = message.from_user
            user_id = user.id
            user_first_name = user.first_name

        elif message.sender_chat:
            user = message.sender_chat
            user_id = user.id
            user_first_name = user.title

        return (user_id, user_first_name, user)

    @staticmethod
    def char_code_at(string, index):
        return ord(string[index])

    @staticmethod
    def to_crc16(data):
        crc = 0xFFFF
        for char in data:
            crc ^= ord(char) << 8
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
        crc &= 0xFFFF
        hex_crc = hex(crc)[2:].upper()
        return hex_crc.zfill(4)

    @staticmethod
    def qris_dinamis(nominal, path):
        qris2 = CODEQR[:-4]
        replace_qris = qris2.replace("010211", "010212")
        pecah_qris = replace_qris.split("5802ID")
        uang = f"54{str(len(nominal)).zfill(2)}{nominal}5802ID"

        output = pecah_qris[0] + uang + pecah_qris[1]
        crc16 = Tools.to_crc16(output)
        output += crc16

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=2,
        )
        qr.add_data(output)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(path)

        return path
