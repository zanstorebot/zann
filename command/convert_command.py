import asyncio
import base64
import io
import json
import os
import random
import subprocess
from io import BytesIO

import aiohttp
import cv2
import gtts
import requests
import speech_recognition as sr
from bs4 import BeautifulSoup
from gpytranslate import Translator
from gpytranslate.exceptions import TranslationError
from PIL import Image
from pyrogram import raw, types
from pyrogram.enums import MessageMediaType
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from config import API_BOTCHAX, API_NEOX, SUDO_OWNERS
from database import dB
from helpers import (ApiImage, Emoji, Message, Quotly, Sticker, Tools,
                     animate_proses)


# ============================================================
# HELPERS
# ============================================================
def download_website(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
    }

    retries = Retry(total=5, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    session = requests.Session()
    session.mount("http://", HTTPAdapter(max_retries=retries))

    try:
        response = session.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        return f"Failed to download source code. Status code: {response.status_code}"
    except Exception as e:
        return f"An error occurred: {str(e)}"


async def ReTrieveFile(input_file_name):
    headers = {
        "X-API-Key": "3RCCWg8tMBfDWdAs44YMfJmC",
    }
    files = {
        "image_file": (input_file_name, open(input_file_name, "rb")),
    }
    return requests.post(
        "https://api.remove.bg/v1.0/removebg",
        headers=headers,
        files=files,
        allow_redirects=True,
        stream=True,
    )


def run_curl(cmd):
    process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return process.stdout.decode().strip(), process.stderr.decode().strip()


# ============================================================
# TINY STICKER
# ============================================================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BAHAN_PATH = os.path.join(BASE_DIR, "font-module", "bahan2.png")


def _load_bahan():
    if os.path.exists(BAHAN_PATH):
        return Image.open(BAHAN_PATH).convert("RGBA")
    # fallback: kanvas transparan kalau bahan2.png tidak ada
    return Image.new("RGBA", (512, 512), (0, 0, 0, 0))


def _tiny_size(im):
    z, d = im.size
    if z == d:
        return 200, 200
    t = z + d
    aa = (z / t * 100) - 50
    bb = (d / t * 100) - 50
    return int(200 + 5 * aa), int(200 + 5 * bb)


def _compose(im):
    im = im.convert("RGBA")
    # buang tepi transparan kalau ada
    bbox = im.getchannel("A").getbbox()
    if bbox:
        im = im.crop(bbox)
    # sisi terpanjang = 20px, rasio tetap
    w, h = im.size
    scale = 20 / max(w, h)
    im = im.resize(
        (max(1, round(w * scale)), max(1, round(h * scale))),
        Image.LANCZOS,
    )
    im.save("o.webp", "WEBP", quality=95)
    return "o.webp"


async def tiny_cmd(client, message):
    em = Emoji(client)
    await em.get()
    rep = message.reply_to_message

    pros = await animate_proses(message, em.proses)
    if not rep:
        return await pros.edit(f"{em.gagal}**Please reply to sticker or photo!**")

    doc = await client.download_media(rep)
    try:
        if doc.endswith(".tgs"):
            await Tools.bash(f"lottie_convert.py {doc} json.json")
            with open("json.json", "r") as f:
                jsn = f.read()
            jsn = jsn.replace("512", "2000")
            with open("json.json", "w") as f:
                f.write(jsn)
            await Tools.bash("lottie_convert.py json.json man.tgs")
            file = "man.tgs"
            os.remove("json.json")

        elif doc.endswith((".gif", ".mp4")):
            idoc = cv2.VideoCapture(doc)
            ok, frame = idoc.read()
            idoc.release()
            if not ok:
                return await pros.edit(f"{em.gagal}**Failed to read video frame!**")
            cv2.imwrite("i.png", frame)
            im = Image.open("i.png")
            file = _compose(im)
            im.close()
            os.remove("i.png")

        else:
            im = Image.open(doc)
            file = _compose(im)
            im.close()

        await asyncio.gather(
            pros.delete(),
            client.send_sticker(
                message.chat.id,
                sticker=file,
                reply_to_message_id=Message.ReplyCheck(message),
            ),
        )
        os.remove(file)
    except Exception as e:
        return await pros.edit(f"{em.gagal}**Error: `{e}`**")
    finally:
        if doc and os.path.exists(doc):
            os.remove(doc)


# ============================================================
# IMAGE TOOLS
# ============================================================
async def rbg_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    if message.reply_to_message:
        reply_message = message.reply_to_message

        try:
            if (
                isinstance(reply_message.media, raw.types.MessageMediaPhoto)
                or reply_message.media
            ):
                downloaded_file_name = await client.download_media(
                    reply_message, "./downloads/"
                )
                await proses.edit(f"<b>{em.gagal}Try removing background...</b>")
                output_file_name = await ReTrieveFile(downloaded_file_name)
                os.remove(downloaded_file_name)
            else:
                return await proses.edit(f"<b>{em.gagal}Please reply to photo!!</b>")
        except Exception as e:
            await proses.edit(f"{em.gagal}**ERROR:** {(str(e))}")
            return
        contentType = output_file_name.headers.get("content-type")
        if "image" in contentType:
            with io.BytesIO(output_file_name.content) as remove_bg_image:
                remove_bg_image.name = "rbg.png"
                await client.send_document(
                    message.chat.id,
                    document=remove_bg_image,
                    force_document=True,
                    reply_to_message_id=message.id,
                )
                return await proses.delete()
        else:
            return await proses.edit(
                "{}<b>ERROR</b>\n<i>{}</i>".format(
                    em.gagal, output_file_name.content.decode("UTF-8")
                )
            )
    else:
        return await message.reply(f"<b>{em.gagal}Please reply to photo</b>")


async def blur_cmd(client, message):
    em = Emoji(client)
    await em.get()

    reply = message.reply_to_message
    proses = await animate_proses(message, em.proses)
    if not reply:
        return await proses.edit(f"<b>{em.gagal}Please reply to photo</b>")
    yinsxd = await client.download_media(reply, "./downloads/")
    if yinsxd.endswith(".tgs"):
        cmd = ["lottie_convert.py", yinsxd, "yin.png"]
        file = "yin.png"
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()
    else:
        img = cv2.VideoCapture(yinsxd)
        heh, lol = img.read()
        cv2.imwrite("yin.png", lol)
        file = "yin.png"
    yin = cv2.imread(file)
    ayiinxd = cv2.GaussianBlur(yin, (35, 35), 0)
    cv2.imwrite("yin.jpg", ayiinxd)
    await client.send_photo(
        message.chat.id,
        "yin.jpg",
        reply_to_message_id=message.id,
    )
    os.remove("yin.png")
    os.remove("yin.jpg")
    os.remove(yinsxd)
    return await proses.delete()


async def negative_cmd(client, message):
    em = Emoji(client)
    await em.get()

    reply = message.reply_to_message
    proses = await animate_proses(message, em.proses)
    if not reply:
        return await proses.edit(f"<b>{em.gagal}Please reply to photo</b>")
    ayiinxd = await client.download_media(reply, "./downloads/")
    if ayiinxd.endswith(".tgs"):
        cmd = ["lottie_convert.py", ayiinxd, "yin.png"]
        file = "yin.png"
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()
    else:
        img = cv2.VideoCapture(ayiinxd)
        heh, lol = img.read()
        cv2.imwrite("yin.png", lol)
        file = "yin.png"
    yinsex = cv2.imread(file)
    kntlxd = cv2.bitwise_not(yinsex)
    cv2.imwrite("yin.jpg", kntlxd)
    await client.send_photo(
        message.chat.id,
        "yin.jpg",
        reply_to_message_id=message.id,
    )
    os.remove("yin.png")
    os.remove("yin.jpg")
    os.remove(ayiinxd)
    return await proses.delete()


async def miror_cmd(client, message):
    em = Emoji(client)
    await em.get()

    reply = message.reply_to_message
    proses = await animate_proses(message, em.proses)
    if not reply:
        return await proses.edit(f"<b>{em.gagal}Please reply to photo.</b>")
    xnproses = await client.download_media(reply, "./downloads/")
    if xnproses.endswith(".tgs"):
        cmd = ["lottie_convert.py", xnproses, "yin.png"]
        file = "yin.png"
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await process.communicate()
    else:
        img = cv2.VideoCapture(xnproses)
        kont, tol = img.read()
        cv2.imwrite("yin.png", tol)
        file = "yin.png"
    yin = cv2.imread(file)
    mmk = cv2.flip(yin, 1)
    ayiinxd = cv2.hconcat([yin, mmk])
    cv2.imwrite("yin.jpg", ayiinxd)
    await client.send_photo(
        message.chat.id,
        "yin.jpg",
        reply_to_message_id=message.id,
    )
    os.remove("yin.png")
    os.remove("yin.jpg")
    os.remove(xnproses)
    return await proses.delete()


async def waifu_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    if message.command[0] == "wall":
        photo = await ApiImage.wall(client)
        try:
            await photo.copy(message.chat.id, reply_to_message_id=message.id)
            return await proses.delete()
        except Exception as error:
            return await proses.edit(f"{em.gagal}**{str(error)}**")
    elif message.command[0] == "waifu":
        photo = ApiImage.waifu()
        try:
            await message.reply_photo(photo)
            return await proses.delete()
        except Exception as error:
            return await proses.edit(f"{em.gagal}**{str(error)}**")


async def pic_cmd(client, message):
    em = Emoji(client)
    await em.get()

    prompt = client.get_text(message)
    proses = await animate_proses(message, em.proses)
    await asyncio.sleep(2)
    if not prompt:
        return await proses.edit(
            f"{em.gagal}**Please use command:** <code>{message.text.split()[0]} dino kuning</code>"
        )
    x = await client.get_inline_bot_results(message.command[0], prompt)
    await proses.delete()
    get_media = []
    for _ in range(5):
        try:
            saved = await client.send_inline_bot_result(
                client.me.id, x.query_id, x.results[random.randrange(30)].id
            )
            saved = await client.get_messages(
                client.me.id, int(saved.updates[1].message.id), replies=0
            )
            get_media.append(types.InputMediaPhoto(saved.photo.file_id))
        except Exception as er:
            return await proses.edit(f"{em.gagal}<b>Image nothing found</b> {str(er)}")
    await saved.delete()
    return await client.send_media_group(
        message.chat.id,
        get_media,
        reply_to_message_id=message.id,
    )


async def gif_cmd(client, message):
    em = Emoji(client)
    await em.get()

    prompt = client.get_text(message)
    proses = await animate_proses(message, em.proses)
    await asyncio.sleep(2)
    if not prompt:
        return await proses.edit(
            f"{em.gagal}**Please use command: <code>{message.text.split()[0]} dino kuning</code>"
        )
    x = await client.get_inline_bot_results(message.command[0], prompt)
    await proses.delete()
    try:
        saved = await client.send_inline_bot_result(
            client.me.id, x.query_id, x.results[random.randrange(30)].id
        )
    except Exception as er:
        return await message.reply(f"{em.gagal}<b>Media nothing found</b> {str(er)}")
    saved = await client.get_messages(
        client.me.id, int(saved.updates[1].message.id), replies=0
    )
    await saved.delete()
    return await client.send_animation(
        message.chat.id, saved.animation.file_id, reply_to_message_id=message.id
    )


# ============================================================
# CONVERTERS
# ============================================================
async def toimg_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    reply = message.reply_to_message
    try:
        file_io = await Tools.dl_pic(client, reply)
        file_io.name = "sticker.png"
        await message.reply_photo(file_io)
        return await proses.delete()
    except Exception as e:
        return await proses.edit(f"{em.gagal}**ERROR:** {str(e)}")


async def tosticker_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    try:
        if not message.reply_to_message or not message.reply_to_message.photo:
            return await proses.edit(f"<b>{em.gagal}**Please reply to photo!!**</b>")
        sticker = await client.download_media(
            message.reply_to_message.photo.file_id,
            f"sticker_{message.from_user.id}.webp",
        )
        await message.reply_sticker(sticker)
        os.remove(sticker)
        return await proses.delete()
    except Exception as e:
        return await proses.edit(f"{em.gagal}**ERROR:** {str(e)}")


async def togif_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    if not message.reply_to_message or not message.reply_to_message.sticker:
        return await proses.edit(f"<b>{em.gagal}Please reply to sticker!!</b>")
    file = await client.download_media(
        message.reply_to_message,
        f"gift_{message.from_user.id}.mp4",
    )
    try:
        await client.send_animation(
            message.chat.id, file, reply_to_message_id=message.id
        )
        os.remove(file)
        return await proses.delete()
    except Exception as error:
        return await proses.edit(f"{em.gagal}**ERROR:** {str(error)}")


async def toaudio_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    replied = message.reply_to_message
    if not replied:
        return await proses.edit(f"<b>{em.gagal}Please reply to message video!</b>")
    if replied.media == MessageMediaType.VIDEO:
        await proses.edit(f"<b>{em.proses}Downloading video...</b>")
        file = await client.download_media(
            message=replied,
            file_name=f"toaudio_{replied.id}",
        )
        out_file = f"{file}.mp3"
        try:
            await proses.edit(f"<b>{em.proses}Converting audio...</b>")
            cmd = f"ffmpeg -i {file} -q:a 0 -map a {out_file}"
            await client.run_cmd(cmd)
            await proses.edit(f"<b>{em.proses}Try to sending audio...</b>")
            await client.send_voice(
                message.chat.id,
                voice=out_file,
                reply_to_message_id=message.id,
            )
            os.remove(file)
            return await proses.delete()
        except Exception as error:
            await proses.edit(f"{em.gagal}**ERROR:** {str(error)}")
    else:
        return await proses.edit(f"<b>{em.gagal}Please reply to video!!</b>")


# ============================================================
# IMG2TEXT (Neoxr + Catbox.moe)
# ============================================================
NEOX_IMG2PROMPT = "https://api.neoxr.eu/api/img2prompt"


async def _neox_prompt(url):
    respon = await Tools.fetch.get(
        NEOX_IMG2PROMPT,
        params={"image": url, "apikey": API_NEOX},
        timeout=60,
    )
    try:
        body = respon.json()
    except Exception:
        body = {}

    if respon.status_code == 200 and body.get("status"):
        prompt = str((body.get("data") or {}).get("prompt", "")).strip()
        if prompt:
            return prompt, None
        return None, f"prompt kosong: {str(body)[:150]}"

    return None, body.get("msg") or body.get("message") or f"HTTP {respon.status_code}"


UPLOAD_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; Bot/1.0)"}


async def _up_catbox(session, path):
    form = aiohttp.FormData()
    form.add_field("reqtype", "fileupload")
    form.add_field("fileToUpload", open(path, "rb"), filename=os.path.basename(path))
    async with session.post("https://catbox.moe/user/api.php", data=form) as r:
        return (await r.text()).strip()


async def _up_litterbox(session, path):
    form = aiohttp.FormData()
    form.add_field("reqtype", "fileupload")
    form.add_field("time", "1h")
    form.add_field("fileToUpload", open(path, "rb"), filename=os.path.basename(path))
    async with session.post(
        "https://litterbox.catbox.moe/resources/internals/api.php", data=form
    ) as r:
        return (await r.text()).strip()


async def _up_uguu(session, path):
    form = aiohttp.FormData()
    form.add_field("files[]", open(path, "rb"), filename=os.path.basename(path))
    async with session.post("https://uguu.se/upload", data=form) as r:
        data = await r.json(content_type=None)
        return data["files"][0]["url"]


async def _up_tmpfiles(session, path):
    form = aiohttp.FormData()
    form.add_field("file", open(path, "rb"), filename=os.path.basename(path))
    async with session.post("https://tmpfiles.org/api/v1/upload", data=form) as r:
        data = await r.json(content_type=None)
        url = data["data"]["url"]
        # link langsung ke file (bukan halaman preview)
        return url.replace("tmpfiles.org/", "tmpfiles.org/dl/", 1)


async def _up_0x0(session, path):
    form = aiohttp.FormData()
    form.add_field("file", open(path, "rb"), filename=os.path.basename(path))
    async with session.post("https://0x0.st", data=form) as r:
        return (await r.text()).strip()


def _telegraph_uploader(base):
    async def _up(session, path):
        form = aiohttp.FormData()
        form.add_field("file", open(path, "rb"), filename=os.path.basename(path))
        async with session.post(f"{base}/upload", data=form) as r:
            raw = await r.text()
            try:
                data = json.loads(raw)
                return base + data[0]["src"]
            except Exception:
                raise RuntimeError(f"respon: {raw[:80]}")

    return _up


async def _up_quax(session, path):
    form = aiohttp.FormData()
    form.add_field("files[]", open(path, "rb"), filename=os.path.basename(path))
    async with session.post("https://qu.ax/upload.php", data=form) as r:
        data = await r.json(content_type=None)
        return data["files"][0]["url"]


async def _up_imgbb(session, path):
    key = os.getenv("IMGBB_API_KEY")
    if not key:
        raise RuntimeError("IMGBB_API_KEY kosong")
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    async with session.post(
        "https://api.imgbb.com/1/upload", data={"key": key, "image": b64}
    ) as r:
        data = await r.json(content_type=None)
        return data["data"]["url"]


# Neoxr menolak catbox/uguu/iili.io, jadi pakai host lain.
# Urutan: yang paling mungkin diterima Neoxr dulu.
IMG_HOSTS = [
    ("telegraph", _telegraph_uploader("https://telegra.ph")),
    ("graph.org", _telegraph_uploader("https://graph.org")),
    ("imgbb", _up_imgbb),
    ("tmpfiles", _up_tmpfiles),
    ("qu.ax", _up_quax),
    ("0x0", _up_0x0),
]


async def upload_image(path, func):
    timeout = aiohttp.ClientTimeout(total=60, sock_connect=10)
    async with aiohttp.ClientSession(timeout=timeout, headers=UPLOAD_HEADERS) as session:
        url = await func(session, path)
    if not (url and url.startswith("http")):
        raise ValueError("respon upload tidak valid")
    return url


def _cdn_rejected(err):
    err = (err or "").lower()
    return "cdn" in err or "invalid format" in err or "prompt kosong" in err


async def img2text_cmd(client, message):
    em = Emoji(client)
    await em.get()

    prs = await animate_proses(message, em.proses)
    reply = message.reply_to_message
    if not reply or not reply.photo:
        return await prs.edit(f"{em.gagal}**Please reply to image!!**")

    url = file_path = data = None
    err = None
    log = []
    try:
        file_path = await client.download_media(reply, "./downloads/")
        await prs.edit(f"{em.proses}**Generating prompt from image...**")

        for name, func in IMG_HOSTS:
            try:
                url = await upload_image(file_path, func)
            except Exception as e:
                log.append(f"{name}: upload {type(e).__name__} {str(e)[:80]}")
                continue

            data, err = await _neox_prompt(url)
            if data:
                break
            log.append(f"{name}: {err}")
            if not _cdn_rejected(err):
                break  # error lain (API key, kuota, dll), ganti host tidak membantu
    except Exception as er:
        return await prs.edit(
            f"{em.gagal}**ERROR:** `{type(er).__name__}: {er}`"
        )
    finally:
        if file_path and os.path.exists(file_path):
            os.remove(file_path)

    if not data:
        return await prs.edit(
            f"{em.gagal}**Gagal membuat prompt:**\n<code>{' | '.join(log) or err}</code>"
        )

    caption = (
        f"{em.sukses}**Media:** <a href='{reply.link}'>Here</a>\n"
        f"**Prompt:**\n`{data}`"
    )
    try:
        await message.reply(caption, disable_web_page_preview=True)
        return await prs.delete()
    except Exception:
        with io.BytesIO(data.encode()) as out_file:
            out_file.name = "prompt.txt"
            await message.reply_document(document=out_file)
        return await prs.delete()


# ============================================================
# MEME / QR
# ============================================================
async def mmf_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    pref = client.get_prefix(client.me.id)
    x = next(iter(pref))
    rep = message.reply_to_message
    meme = None
    file = None
    pros = None

    if not rep:
        return await message.reply(
            f"{emo.gagal}<b>Use the command by replying to a photo/sticker/video.</b>"
        )

    if not (rep.photo or rep.animation or rep.video or rep.sticker):
        return await message.reply(
            f"{emo.gagal}<b>Reply to a photo, sticker, or video.</b>"
        )

    try:
        file = await client.download_media(rep)
        if not file:
            return await message.reply(f"{emo.gagal}<b>Failed to download media.</b>")

        pros = await message.reply(
            f"{emo.proses}<b>Processing adding text to media ..</b>"
        )

        text = client.get_text(message)
        if len(message.command) < 2:
            await pros.edit(
                f"{emo.gagal}<b>Use the command by adding text after the command.\n\nExample:\n<code>{x}mmf Hi;Love!</code>\n\nThen the text <i><u>Hi</u></i> will be at the top of the media, and the text <i><u>Love!</u></i> will be at the bottom of the media.</b>"
            )
            return

        if rep.animation or rep.video:
            meme = await Sticker.add_text_to_video(file, text)
        else:
            meme = await Sticker.add_text_img(file, text)

        await client.send_sticker(
            message.chat.id, sticker=meme, reply_to_message_id=message.id
        )
        await pros.delete()

    except Exception as e:
        await message.reply(f"{emo.gagal}<b>Error processing media: {str(e)}</b>")
        if pros:
            await pros.delete()

    finally:
        for f in (file, meme):
            if f and os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass


async def qrcode_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    if len(message.command) < 2:
        return await proses.edit(
            f"{em.gagal}**Please give valid query `{message.text.split()[0]}` [gen or read]!**"
        )
    query = message.command[1]
    reply = message.reply_to_message or message

    if query == "gen":
        if not reply or reply and not reply.text:
            return await proses.edit(f"{em.gagal}**Please give barcode text**")
        text = reply.text or reply.caption
        data = (
            Tools.qr_gen(text)
            if reply
            else Tools.qr_gen(message.text.split(None, 2)[2])
        )
        try:
            QRcode = (
                requests.post(
                    "https://api.qrcode-monkey.com//qr/custom",
                    json=data,
                )
                .json()["imageUrl"]
                .replace("//api", "https://api")
            )
            await client.send_photo(
                message.chat.id, QRcode, reply_to_message_id=reply.id
            )
            return await proses.delete()
        except Exception as error:
            return await proses.edit(f"{em.gagal}**ERROR**: {str(error)}")

    elif query == "read":
        if not (reply and reply.media and (reply.photo or reply.sticker)):
            await proses.edit(f"{em.gagal}**Please reply to valid barcode!**")
            return
        if not os.path.isdir("storage/cache/"):
            os.makedirs("storage/cache/")
        down_load = await client.download_media(
            message=reply, file_name="storage/cache/"
        )
        cmd = [
            "curl",
            "-X",
            "POST",
            "-F",
            "f=@" + down_load,
            "https://zxing.org/w/decode",
        ]
        stdout, stderr = await asyncio.to_thread(run_curl, cmd)
        os.remove(down_load)
        if not (stdout or stderr):
            await proses.edit(f"{em.gagal}**Something error, try again!**")
            return
        try:
            soup = BeautifulSoup(stdout, "html.parser")
            qr_contents = soup.find_all("pre")[0].text
        except IndexError:
            await proses.edit(f"{em.gagal}**Something error, try again!**")
            return
        return await proses.edit(
            f"{em.sukses}<b>Qr Text:</b>\n<code>{qr_contents}</code>"
        )
    else:
        return await proses.edit(
            f"{em.gagal}**Please give valid query `{message.text.split()[0]}` [gen or read]!**"
        )


# ============================================================
# QUOTLY
# ============================================================
async def consu(dok):
    with open(dok, "rb") as file:
        data_bytes = file.read()
    json_data = json.loads(data_bytes)
    image_data_base64 = json_data.get("image")
    if not image_data_base64:
        raise ValueError("Tidak ada data gambar dalam JSON")
    image_data = base64.b64decode(image_data_base64)
    image_io = io.BytesIO(image_data)
    image_io.name = "Quotly.webp"
    return image_io


async def qcolor_cmd(client, message):
    em = Emoji(client)
    await em.get()
    iymek = "\n•".join(Quotly.colors)
    jadi = f"{em.sukses}Color for quotly\n•"
    if len(iymek) > 4096:
        with open("qcolor.txt", "w") as file:
            file.write(iymek)
        await message.reply_document(
            "qcolor.txt", caption=f"{em.sukses}Color for quotly"
        )
        os.remove("qcolor.txt")
        return
    return await message.reply(jadi + iymek)


async def qoutly_cmd(client, message):
    em = Emoji(client)
    await em.get()

    if not message.reply_to_message:
        return await message.reply(f"{em.gagal}**Please reply to a message!**")

    pros = await animate_proses(message, em.proses)
    reply_msg = message.reply_to_message
    cmd = message.command[1:]

    def get_color(index=0):
        return cmd[index] if len(cmd) > index else random.choice(Quotly.colors)

    try:
        if not cmd:
            payload = {
                "type": "quote",
                "format": "png",
                "backgroundColor": get_color(),
                "messages": [],
            }
            sid, title, name = await Quotly.forward_info(reply_msg)
            payload["messages"].append({
                "chatId": reply_msg.from_user.id,
                "entities": Tools.get_msg_entities(reply_msg),
                "avatar": True,
                "from": {
                    "id": reply_msg.from_user.id,
                    "title": name,
                    "name": name,
                    "emoji_status": await Quotly.get_emoji(reply_msg),
                },
                "text": await Quotly.t_or_c(reply_msg),
                "replyMessage": {},
            })

        elif cmd[0].startswith("@"):
            color = get_color(1)
            include_reply = len(cmd) > 2 and cmd[2] == "-r"
            payload = {
                "type": "quote",
                "format": "png",
                "backgroundColor": color,
                "messages": [],
            }

            username = cmd[0][1:]
            user = await client.get_users(username)

            if user.id in SUDO_OWNERS:
                return await pros.edit(f"{em.gagal}**You can't quote this user**")

            name = user.first_name
            if user.last_name:
                name += f" {user.last_name}"

            emoji_status = None
            if user.emoji_status:
                emoji_status = str(user.emoji_status.custom_emoji_id)

            reply_message = {}
            if include_reply:
                replied = reply_msg.reply_to_message
                replied_name = replied.from_user.first_name
                if replied.from_user.last_name:
                    replied_name += f" {replied.from_user.last_name}"

                emoji_status_reply = None
                if replied.from_user.emoji_status:
                    emoji_status_reply = str(
                        replied.from_user.emoji_status.custom_emoji_id
                    )

                reply_message = {
                    "chatId": replied.from_user.id,
                    "entities": Tools.get_msg_entities(replied),
                    "name": replied_name,
                    "text": replied.text or replied.caption or "",
                    "emoji_status": emoji_status_reply,
                }

            payload["messages"].append({
                "chatId": user.id,
                "entities": Tools.get_msg_entities(reply_msg),
                "avatar": True,
                "from": {
                    "id": user.id,
                    "title": name,
                    "name": name,
                    "emoji_status": emoji_status,
                },
                "text": await Quotly.t_or_c(reply_msg),
                "replyMessage": reply_message,
            })

        elif cmd[0].startswith("-r"):
            replied = reply_msg.reply_to_message
            replied_name = replied.from_user.first_name
            if replied.from_user.last_name:
                replied_name += f" {replied.from_user.last_name}"

            emoji_status = None
            if replied.from_user.emoji_status:
                emoji_status = str(replied.from_user.emoji_status.custom_emoji_id)

            payload = {
                "type": "quote",
                "format": "png",
                "backgroundColor": get_color(1),
                "messages": [],
            }

            sid, title, name = await Quotly.forward_info(reply_msg)
            payload["messages"].append({
                "chatId": reply_msg.from_user.id,
                "entities": Tools.get_msg_entities(reply_msg),
                "avatar": True,
                "from": {
                    "id": reply_msg.from_user.id,
                    "title": name,
                    "name": name,
                    "emoji_status": await Quotly.get_emoji(reply_msg),
                },
                "text": await Quotly.t_or_c(reply_msg),
                "replyMessage": {
                    "chatId": replied.from_user.id,
                    "entities": Tools.get_msg_entities(replied),
                    "name": replied_name,
                    "text": replied.text or replied.caption or "",
                    "emoji_status": emoji_status,
                },
            })

        elif cmd[0].isdigit():
            count = int(cmd[0])

            if count > 10:
                return await pros.edit(f"{em.gagal}**Max 10 messages!**")

            payload = {
                "type": "quote",
                "format": "png",
                "backgroundColor": get_color(1),
                "messages": [],
                "scale": 2,
            }

            sid, title, name = await Quotly.forward_info(reply_msg)
            payload["messages"].append({
                "chatId": reply_msg.from_user.id,
                "entities": Tools.get_msg_entities(reply_msg),
                "avatar": True,
                "from": {
                    "id": reply_msg.from_user.id,
                    "title": name,
                    "name": name,
                    "emoji_status": await Quotly.get_emoji(reply_msg),
                },
                "text": await Quotly.t_or_c(reply_msg),
                "replyMessage": {},
            })

            async for msg in client.get_chat_history(
                reply_msg.chat.id,
                limit=count - 1,
                offset_id=reply_msg.id,
            ):
                sid, title, name = await Quotly.forward_info(msg)
                payload["messages"].append({
                    "chatId": msg.from_user.id,
                    "entities": Tools.get_msg_entities(msg),
                    "avatar": True,
                    "from": {
                        "id": msg.from_user.id,
                        "title": name,
                        "name": name,
                        "emoji_status": await Quotly.get_emoji(msg),
                    },
                    "text": await Quotly.t_or_c(msg),
                    "replyMessage": {},
                })

            payload["messages"].reverse()

        else:
            payload = {
                "type": "quote",
                "format": "png",
                "backgroundColor": cmd[0],
                "messages": [],
            }

            sid, title, name = await Quotly.forward_info(reply_msg)
            payload["messages"].append({
                "chatId": reply_msg.from_user.id,
                "entities": Tools.get_msg_entities(reply_msg),
                "avatar": True,
                "from": {
                    "id": reply_msg.from_user.id,
                    "title": name,
                    "name": name,
                    "emoji_status": await Quotly.get_emoji(reply_msg),
                },
                "text": await Quotly.t_or_c(reply_msg),
            })

        quote_apis = [
            ("LOCAL", "http://localhost:3000/generate"),
            ("LYO", "https://bot.lyo.su/quote/generate"),
        ]

        image_data = None
        errors = []

        async with aiohttp.ClientSession() as session:
            for api_name, api_url in quote_apis:
                try:
                    async with session.post(
                        api_url,
                        json=payload,
                        timeout=aiohttp.ClientTimeout(total=60),
                    ) as response:
                        content_type = response.headers.get("Content-Type", "")

                        if "application/json" not in content_type:
                            errors.append(f"{api_name}: {response.status} bukan JSON")
                            continue

                        result = await response.json()

                        if result.get("error"):
                            errors.append(f"{api_name}: {result['error']}")
                            continue

                        image_data_raw = (
                            result.get("image")
                            or result.get("result", {}).get("image")
                            or result.get("data", {}).get("image")
                            or result.get("url")
                            or result.get("result", {}).get("url")
                        )

                        if not image_data_raw:
                            print(f"{api_name} RESPONSE: {result}")
                            errors.append(f"{api_name}: gambar tidak ditemukan")
                            continue

                        if image_data_raw.startswith("http"):
                            async with session.get(image_data_raw) as image_response:
                                image_data = await image_response.read()
                        else:
                            image_data = base64.b64decode(image_data_raw)

                        break

                except Exception as e:
                    errors.append(f"{api_name}: {str(e)[:200]}")
                    continue

        if not image_data:
            return await pros.edit(
                f"{em.gagal}<b>Gagal membuat quote:</b>\n<code>{' | '.join(errors)}</code>"
            )

        bio_sticker = BytesIO(image_data)
        bio_sticker.name = "quote.png"

        try:
            image = Image.open(bio_sticker).convert("RGBA")
            width, height = image.size
            scale = 512 / max(width, height)
            new_size = (int(width * scale), int(height * scale))
            image = image.resize(new_size, Image.LANCZOS)

            bio_sticker = BytesIO()
            bio_sticker.name = "quote.webp"
            image.save(bio_sticker, format="WEBP", quality=90)
            bio_sticker.seek(0)
        except Exception:
            bio_sticker = BytesIO(image_data)
            bio_sticker.name = "quote.webp"

        await message.reply_sticker(bio_sticker)
        await pros.delete()

    except Exception as e:
        await pros.edit(f"{em.gagal}<b>Error:</b>\n<code>{str(e)[:500]}</code>")


# ============================================================
# TEXT GENERATOR
# ============================================================
async def textgen_cmd(client, message):
    em = Emoji(client)
    await em.get()

    prs = await animate_proses(message, em.proses)
    prompt = client.get_text(message)

    if not prompt:
        return await prs.edit(
            f"{em.gagal}<b>Give the query you want to generate prompt!\n\nExample: \n<code>{message.text.split()[0]} cat on the beach</code></b>"
        )

    url = "https://api.botcahx.eu.org/api/search/openai-custom-v2"
    payload = {
        "message": [
            {
                "role": "system",
                "content": (
                    "Kamu adalah pembuat prompt gambar AI. Ubah ide user menjadi "
                    "satu prompt bahasa Indonesia yang sangat detail sekali (subjek, objek, gaya, pencahayaan, "
                    "komposisi, kualitas, resolusi). Balas hanya prompt-nya saja."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "apikey": API_BOTCHAX,
    }
    try:
        respon = await Tools.fetch.post(url, json=payload)
    except Exception as er:
        return await prs.edit(f"{em.gagal}**ERROR:** {str(er)}")

    if respon.status_code != 200:
        return await prs.edit(f"**{em.gagal}Please try again: {respon.status_code}!**")

    data = respon.json().get("result")
    if not data:
        return await prs.edit(f"{em.gagal}**Gagal membuat prompt, coba lagi nanti.**")

    try:
        await prs.edit(f"`{data}`")
    except Exception as er:
        await prs.delete()
        return await message.reply(f"{em.gagal}**ERROR:** {str(er)}")


# ============================================================
# TRANSLATE
# ============================================================
_TR_CACHE = {}


async def _mymemory(text, target):
    # batas 500 karakter per request
    r = await Tools.fetch.get(
        "https://api.mymemory.translated.net/get",
        params={"q": text[:500], "langpair": f"autodetect|{target}"},
    )
    if r.status_code != 200:
        return None
    return (r.json().get("responseData") or {}).get("translatedText")


async def safe_translate(trans, text, target):
    key = (text, target)
    if key in _TR_CACHE:
        return _TR_CACHE[key]
    out = None
    try:
        res = await trans.translate(text, sourcelang="auto", targetlang=target)
        out = res.text
    except TranslationError:
        # Google menolak: jangan diulang, langsung fallback
        try:
            out = await _mymemory(text, target)
        except Exception:
            out = None
    if out:
        if len(_TR_CACHE) > 500:
            _TR_CACHE.clear()
        _TR_CACHE[key] = out
    return out


async def tr_cmd(client, message):
    em = Emoji(client)
    await em.get()
    trans = Translator()

    pros = await animate_proses(message, em.proses)
    bhs = await client.get_translate()

    if message.reply_to_message:
        txt = message.reply_to_message.text or message.reply_to_message.caption
    else:
        if len(message.command) < 2:
            return await pros.edit(
                f"{em.gagal}**Please reply to message text or give text!**"
            )
        txt = message.text.split(None, 1)[1]

    if not txt:
        return await pros.edit(
            f"{em.gagal}**Please reply to message text or give text!**"
        )

    hasil = await safe_translate(trans, txt, bhs)
    if not hasil:
        return await pros.edit(
            f"{em.gagal}**Translate gagal, semua layanan sedang membatasi. Coba lagi nanti.**"
        )

    reply = f"{em.sukses} Translated:\n\n{hasil}"
    rep = message.reply_to_message or message
    await pros.delete()
    return await client.send_message(message.chat.id, reply, reply_to_message_id=rep.id)


async def lang_cmd(client, message):
    em = Emoji(client)
    await em.get()
    try:
        bhs_list = "\n".join(
            f"- **{lang}**: `{code}`" for lang, code in Tools.kode_bahasa.items()
        )
        return await message.reply(f"{em.sukses}**Language codes:**\n\n{bhs_list}")
    except Exception as e:
        return await message.reply(f"{em.gagal}**Error: {str(e)}**")


async def setlang_cmd(client, message):
    em = Emoji(client)
    await em.get()

    pros = await message.reply(f"{em.proses}**Processing...**")
    if len(message.command) < 2:
        return await pros.edit(
            f"{em.gagal}**Please reply to message text or give text!**"
        )

    kd = message.text.split(None, 1)[1]
    for lang, code in Tools.kode_bahasa.items():
        if kd.lower() == code.lower():
            await dB.set_var(client.me.id, "_translate", kd.lower())
            return await pros.edit(
                f"{em.sukses}**Successfully changed translate language to: {lang}-{kd}**"
            )

    return await pros.edit(f"{em.gagal}**Language code not found!**")


# ============================================================
# AUDIO / VOICE
# ============================================================
async def vremover_cmd(client, message):
    em = Emoji(client)
    await em.get()

    prs = await animate_proses(message, em.proses)
    rep = message.reply_to_message or message
    if not rep or not (rep.audio or rep.video):
        return await prs.edit(f"{em.gagal}**Please reply to audio or video!!**")
    arg = await Tools.upload_media(message)
    url = f"https://api.botcahx.eu.org/api/tools/voiceremover?url={arg}&apikey={API_BOTCHAX}"
    respon = await Tools.fetch.get(url)
    ex = await message.reply(f"{em.proses}**Try to extract of instruments...**")

    if respon.status_code == 200:
        data = respon.json()["result"]
        try:
            await prs.delete()
            voice = data["vocal_path"]
            audio = data["instrumental_path"]
            send_voice = await client.send_audio(
                message.chat.id, voice, caption="<b>Vocal</b>"
            )
            send_audio = await client.send_audio(
                message.chat.id, audio, caption="<b>Instruments</b>"
            )
            await ex.delete()
            return await message.reply(
                f"{em.sukses}<blockquote>**Status error:** {data['error']}\n**Status message:** {data['message']}\n**Vocal of the <a href='{rep.link}'>media</a>:** <a href='{send_voice.link}'>here</a>\n**Instruments of the <a href='{rep.link}'>media</a>:** <a href='{send_audio.link}'>here</a></blockquote>",
                disable_web_page_preview=True,
            )
        except Exception as er:
            await ex.delete()
            return await message.reply(f"{em.gagal}**ERROR:** {str(er)}")
    else:
        return await message.reply(
            f"**{em.gagal}Please try again: {respon.status_code}!**"
        )


async def tts_cmd(client, message):
    em = Emoji(client)
    await em.get()

    pros = await animate_proses(message, em.proses)
    bhs = await client.get_translate()
    if message.reply_to_message:
        kata = message.reply_to_message.text or message.reply_to_message.caption
    else:
        if len(message.command) < 2:
            return await pros.edit(
                f"{em.gagal}**Please reply to message text or give text!**"
            )
        kata = message.text.split(None, 1)[1]

    gts = gtts.gTTS(kata, lang=bhs)
    gts.save("trs.oog")
    rep = message.reply_to_message or message
    try:
        await client.send_voice(
            chat_id=message.chat.id,
            voice="trs.oog",
            reply_to_message_id=rep.id,
        )
        await pros.delete()
        os.remove("trs.oog")
        return
    except Exception as er:
        return await pros.edit(f"{em.gagal}**Error: {str(er)}**")


async def stt_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    reply = message.reply_to_message
    if not reply:
        return await proses.edit(f"{em.gagal}**Please reply to message**")
    bhs = await client.get_translate()
    try:
        file_path = await reply.download()
        wav_path = file_path + ".wav"
        subprocess.run(
            [
                "ffmpeg",
                "-i",
                file_path,
                "-acodec",
                "pcm_s16le",
                "-ar",
                "16000",
                wav_path,
            ],
            check=True,
        )

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language=bhs)
                await proses.edit(
                    f"{em.sukses}**Converted [message]({reply.link}):**\n{text}",
                    disable_web_page_preview=True,
                )
            except sr.UnknownValueError:
                return await proses.edit(
                    f"{em.gagal}**Sorry, I can't recognize the sound.**"
                )
            except sr.RequestError:
                return await proses.edit(
                    f"{em.gagal}**Sorry, there is a problem with the voice recognition service.**"
                )
            finally:
                if os.path.exists(wav_path):
                    os.remove(wav_path)
                if os.path.exists(file_path):
                    os.remove(file_path)

    except subprocess.CalledProcessError:
        return await proses.edit(f"{em.gagal}**Failed to convert audio files.**")


# ============================================================
# WEB TOOLS
# ============================================================
async def webdl_cmd(client, message):
    if len(message.command) == 1:
        await message.reply_text(
            "**Please enter a URL along with the /webdl command.**"
        )
        return

    url = message.command[1]

    source_code = download_website(url)
    if source_code.startswith("An error occurred") or source_code.startswith(
        "Failed to download"
    ):
        return await message.reply_text(source_code)

    with open("website.txt", "w", encoding="utf-8") as file:
        file.write(source_code)
    return await message.reply_document(
        document="website.txt", caption=f"**Source code of {url}**"
    )


async def webss_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    upload = None
    if len(message.command) < 2:
        return await proses.edit(
            f"{em.gagal}**Please give valid link! Example: `{message.text.split()[0]}webss https://youtube.com`**"
        )
    url = (
        message.text.split(None, 1)[1]
        if len(message.command) < 3
        else message.text.split(None, 2)[1]
    )
    if "https://" not in url:
        return await proses.edit(f"{em.gagal}**Please give valid link!**")
    full = len(message.command) >= 3
    try:
        photo = await Tools.screen_web(url, full)
        if not photo:
            return await proses.edit(
                f"{em.gagal}**Something went wrong, please try again!**"
            )

        await proses.delete()
        upload = await message.reply(f"{em.proses}**Uploading media...**")
        if not full:
            await message.reply_photo(photo)
        else:
            await message.reply_document(photo)
        return await upload.delete()
    except Exception as r:
        return await (upload or proses).edit(f"{em.gagal}**ERROR:** {str(r)}")
