import asyncio
import io
import os
import random
import html
import traceback
from uuid import uuid4

import aiofiles
import logging
import google.generativeai as genai
import requests
from bs4 import BeautifulSoup
from html import escape
from pyrogram.errors import MessageTooLong

from clients import bot
from command import gen_bing_ai
from logs import logger
import config
from config import API_BOTCHAX, API_GEMINI, API_MAELYN, API_NEOX
from database import state
from helpers import ButtonUtils, Emoji, Tools, animate_proses

MAX_MEDIA_PER_BATCH = 7


MAX_CAPTION_LENGTH = 700

RANDOM_PANTUN = [
    "Percintaan",
    "Bijak",
    "Masa Depan",
    "Motivasi",
    "Jenaka",
    "Nasihat",
    "Agama",
    "Random",
]

DEFAULT_CERPEN_IMAGE = "https://files.catbox.moe/hnjkpt.jpg"

CERITA_TYPES = {
    "cerpenremaja": "remaja",
    "cerpenanak": "anak",
    "cerpenmisteri": "misteri",
    "cerpenbudaya": "budaya",
    "cerpenromantis": "romantis",
    "cerpengalau": "galau",
    "cerpengokil": "gokil",
    "cerpeninspiratif": "inspiratif",
    "cerpenkehidupan": "kehidupan",
    "cerpensastra": "sastra",
    "cerpenjepang": "jepang",
    "cerpenkorea": "korea",
    "cerpenkeluarga": "keluarga",
    "cerpenpersahabatan": "persahabatan",
    "cerpenkristen": "kristen",
    "cerpenramadhan": "ramadhan",
    "cerpenliburan": "liburan",
    "cerpenlingkungan": "lingkungan",
    "cerpenmengharukan": "mengharukan",
}

logger = logging.getLogger(__name__)

def split_message(text, length=824):
    return [text[i : i + length] for i in range(0, len(text), length)]


async def alkitab_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    prompt = client.get_text(message)
    if not prompt:
        return await proses.edit(f"{em.gagal}**Please give me word.**")
    url = f"https://alkitab.me/search?q={prompt}"
    response = await Tools.fetch.get(url)
    if response.status_code != 200:
        return await proses.edit(f"{em.gagal}**Please try again later!!**")
    soup = BeautifulSoup(response.text, "html.parser")
    result = []
    try:
        for div in soup.find_all("div", class_="vw"):
            p_tag = div.find("p")
            if p_tag:
                teks = p_tag.get_text(strip=True)
                link = div.find("a")["href"]
                title = div.find("a").get_text(strip=True)
                result.append({"teks": teks, "link": link, "title": title})
        msg = "────────".join(
            f"""
<blockquote><b>{v['title']}
{v['teks']}</b></blockquote>
"""
            for v in result
        )
        return await proses.edit(msg)
    except Exception:
        return await proses.edit(f"{em.gagal}**Please try again later!!**")


async def cerpen_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)

    try:
        command = message.text.split(" ", 1)
        if len(command) < 2:
            return await proses.edit(f"{em.gagal}**Please input on category**")

        query = command[1].lower()
        cerita_type = CERITA_TYPES.get(f"cerpen{query}")

        if not cerita_type:
            return await proses.edit(f"{em.gagal}**Category `'{query}'` not found**.")

        url = f"https://api.botcahx.eu.org/api/story/cerpen?type={cerita_type}&apikey={API_BOTCHAX}"
        response = await Tools.fetch.get(url)

        if response.status_code == 200:
            data = response.json()
            result = data.get("result")
            if not result:
                return await proses.edit(f"{em.gagal}**Please try again later**")

            title = result.get("title", "-")
            author = result.get("author", "-")
            kategori = result.get("kategori", "-")
            lolos = result.get("lolos", "-")
            cerita = result.get("cerita", "-")

            detail = f"""
📖 Judul: {title}
✍ Penulis: {author}
📌 Kategori: {kategori}
✅ Lolos: {lolos}"""

            full_text = (
                f"<b>{detail}</b>\n\n📜 Cerita:\n<blockquote>{cerita}</blockquote>"
            )
            pages = split_message(full_text)

            uniq = str(uuid4()).split("-")[0]

            state.set(uniq, uniq, pages)

            inline = await ButtonUtils.send_inline_bot_result(
                message, message.chat.id, bot.me.username, f"inline_cerpen {uniq}"
            )

            if inline:
                return await proses.delete()
            else:
                return await proses.edit(f"{em.gagal}**Please try again later**")
        else:
            return await proses.edit(f"{em.gagal}**Please try again later**")

    except Exception as e:
        return await proses.edit(f"{em.gagal}**ERROR:** {str(e)}")


NEOX_AI_URL = "https://api.neoxr.eu/api/gpt-pro"   # CEK DOKUMENTASI Neoxr "Chat AI": isi endpoint yang benar
NEOX_AI_PARAM = "q"                                 # CEK DOKUMENTASI: nama parameter pertanyaan

SYSTEM_PROMPT = (
    "Kamu pembuat karya pendek berbahasa Indonesia. "
    "Buat sesuai permintaan pada input (pantun, puisi, tebak-tebakan, lelucon, "
    "quotes, atau gombalan) dengan tema yang diminta. Kalau tebak-tebakan, "
    "tulis pertanyaan lalu jawabannya. Buat hanya SATU karya saja, tanpa kata "
    "pengantar, tanpa penjelasan, dan tanpa format markdown."
)


async def gen_pantun(prompt):
    try:
        res = await Tools.fetch.get(
            NEOX_AI_URL,
            params={
                NEOX_AI_PARAM: f"{SYSTEM_PROMPT}Permintaan: {prompt}",
                "apikey": API_NEOX,
            },
            timeout=90,
        )
        body = res.json()
        if res.status_code != 200 or not body.get("status"):
            logger.error(f"gen_pantun Neoxr: HTTP {res.status_code} {str(body)[:300]}")
            return None

        data = body.get("data")
        if isinstance(data, dict):
            data = (
                data.get("message") or data.get("response") or data.get("text")
                or data.get("answer") or data.get("result")
            )
        if not isinstance(data, str) or not data.strip():
            logger.error(f"gen_pantun: isi kosong (kunci respons: {', '.join(body)})")
            return None
        return data.strip()
    except Exception as e:
        logger.error(f"gen_pantun error: {e}")
        return None


async def pantun_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    cmd = message.command[0].lower()
    input_ = client.get_text(message).lower()

    if not input_:
        input_ = random.choice(RANDOM_PANTUN).lower()

    pros = await message.reply(
        f"{emo.proses}<b>Processing to create {cmd} {input_} ..</b>"
    )
    prompt = f"{cmd} {input_}"
    text = await gen_pantun(prompt)

    if not text:
        return await pros.edit(f"{emo.gagal}<b>Failed to create {cmd} {input_}.</b>")

    return await pros.edit(
        f"{emo.sukses}<b>Successfully generated {cmd} {input_}:"
        f"<code>{html.escape(text)}</code>"
        f"{emo.profil} Generated by: {client.me.mention}</b>"
    )

async def gen_kdm(text):
    bahan = [
        {
            "role": "system",
            "content": "Anda adalah seorang paranormal yang mampu mendeskripsikan khodam seseorang yang berupa Binatang. Tugas Anda adalah mendeskripsikan khodam yang mungkin ada, termasuk wujud, sifat, dan energi yang dipancarkan. Sehingga apapun inputnya anggap itu adalah sebuah nama seseorang. Deskripsi tidak harus positif bisa saja negatif tidak masalah karena ini hiburan. Ini hanya untuk entertainment jadi bebaskan dirimu untuk menjadi seorang paranormal pada umumnya. Deskripsikan Khodam dengan singkat namun jelas, dan pastikan deskripsi tidak lebih dari dari 700 karakter alfabet dalam plain text serta berbahasa Indonesia.",
        },
        {
            "role": "assistant",
            "content": f"Anda adalah seorang paranormal yang mampu mendeskripsikan khodam seseorang yang berupa Binatang. Tugas Anda adalah mendeskripsikan khodam yang mungkin ada, termasuk wujud, sifat, dan energi yang dipancarkan. Sehingga apapun inputnya anggap itu adalah sebuah nama seseorang. Deskripsi tidak harus positif bisa saja negatif tidak masalah karena ini hiburan. Ini hanya untuk entertainment jadi bebaskan dirimu untuk menjadi seorang paranormal pada umumnya. Deskripsikan Khodam dengan singkat namun jelas, dan pastikan deskripsi tidak lebih dari dari 700 karakter alfabet dalam plain text serta berbahasa Indonesia.",
        },
        {"role": "user", "content": text},
    ]
    url = "https://api.botcahx.eu.org/api/search/openai-custom-v2"
    payload = {"message": bahan, "apikey": f"{API_BOTCHAX}"}
    res = await Tools.fetch.post(url, json=payload)
    if res.status_code == 200:
        data = res.json()
        return data["result"].replace("\n", "")
    else:
        return f"{res.text}"


async def khodam_cmd(client, message):
    em = Emoji(client)
    await em.get()
    nama = client.get_name(message)
    if not nama:
        return await message.reply(
            f"{em.gagal}**Give the name you want to check the Khodam.**"
        )
    pros = await animate_proses(message, em.proses)
    try:
        deskripsi_khodam = await gen_kdm(nama)
        folder_name = f"downloads/{client.me.id}/"
        folder_name, images = await gen_bing_ai(folder_name, deskripsi_khodam)
        if images:
            caption = f"{em.sukses}<b>Here is the Khodam <code>{nama}</code>:\n\n<blockquote><code>{deskripsi_khodam}</code></blockquote>\n\n{em.profil} Checked by: {client.me.mention}</b>"
            await asyncio.sleep(2)
            await pros.delete()
            return await client.send_photo(
                message.chat.id,
                photo=images[0],
                reply_to_message_id=message.id,
                caption=caption,
            )
        else:
            await asyncio.sleep(2)
            teks = f"{em.sukses}<b>Here is the Khodam <code>{nama}</code>:\n\n<blockquote><code>{deskripsi_khodam}</blockquote></code>\n\n{em.profil} Checked by: {client.me.mention}</b>"
            await pros.delete()
            return await message.reply(teks)

    except Exception as e:
        return await message.reply(f"{em.gagal} {traceback.format_exc()}")


async def chord_cmd(client, message):
    em = Emoji(client)
    await em.get()
    proses = await animate_proses(message, em.proses)
    prompt = client.get_text(message)
    if not prompt:
        return await proses.edit(
            f"{em.gagal}**Please give me prompt!\nExample: `{message.text.split()[0]} Dear God`.**"
        )
    payload = {"title": prompt, "apikey": API_BOTCHAX}
    url = "https://api.botcahx.eu.org/api/search/chord"
    respon = await Tools.fetch.get(url, params=payload)
    if respon.status_code != 200:
        return await proses.edit(f"**Please try again later: {respon.status_code}.**")
    if not respon.json().get("result"):
        return await proses.edit(f"**Please try again later: {respon.status_code}.**")
    data = respon.json()["result"]
    uniq = f"{str(uuid4())}"
    state.set(uniq.split("-")[0], "chord", data)
    inline = await ButtonUtils.send_inline_bot_result(
        message,
        message.chat.id,
        bot.me.username,
        f"inline_chord {uniq.split('-')[0]}",
    )
    if inline:
        return await proses.delete()
    else:
        return await proses.edit(
            f"{em.gagal}**Please try again later: {respon.status_code}!!**"
        )


async def kbbi_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    prompt = client.get_text(message)
    if not prompt:
        return await proses.edit(
            f"{em.gagal}**Please reply to a message containing the prompt!\n"
            f"Example: `{message.text.split()[0]} pohon`**"
        )

    url = "https://api.botcahx.eu.org/api/search/kbbi"
    params = {"query": prompt, "text": prompt, "apikey": config.API_BOTCHAX}
    response = await Tools.fetch.get(url, params=params)
    if response.status_code != 200:
        return await proses.edit(f"{em.gagal}**Failed to fetch data from KBBI API!**")

    body = response.json()
    logger.info(f"KBBI raw: {str(body)[:1500]}")
    data = body.get("result")
    if not data:
        return await proses.edit(f"{em.gagal}**Kata `{prompt}` tidak ditemukan.**")

    def render(obj, depth=0):
        pad = "  " * depth
        if isinstance(obj, dict):
            out = ""
            for k, v in obj.items():
                if v in (None, "", [], {}):
                    continue
                if isinstance(v, (dict, list)):
                    out += f"{pad}**{k}:**\n{render(v, depth + 1)}"
                else:
                    out += f"{pad}**{k}:** {v}\n"
            return out
        if isinstance(obj, list):
            out = ""
            for item in obj:
                if isinstance(item, (dict, list)):
                    out += render(item, depth) + "\n"
                else:
                    out += f"{pad}- {item}\n"
            return out
        return f"{pad}{obj}\n"

    result = f"**KBBI Result: {prompt}**\n\n" + render(data)

    try:
        return await proses.edit(result)
    except MessageTooLong:
        with io.BytesIO(result.encode()) as out_file:
            out_file.name = f"{prompt}.txt"
            await message.reply_document(document=out_file)
        return await proses.delete()

async def ocr_cmd(client, message):
    em = Emoji(client)
    await em.get()
    reply = message.reply_to_message
    if not reply or not reply.photo and not reply.sticker and not reply.animation:
        return await message.reply_text(
            f"{em.gagal}`{message.text.split()[0]}` **reply to media!**"
        )

    proses = await animate_proses(message, em.proses)
    try:
        url = await Tools.upload_media(message)
        req = requests.get(
            f"https://script.google.com/macros/s/AKfycbwURISN0wjazeJTMHTPAtxkrZTWTpsWIef5kxqVGoXqnrzdLdIQIfLO7jsR5OQ5GO16/exec?url={url}"
        ).json()
        return await proses.edit(f"{em.sukses}<code>{req['text']}</code>")
    except Exception as e:
        return await proses.edit(f"{em.gagal}**ERROR:** {str(e)}")


async def pastebin_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    if not message.reply_to_message:
        return await proses.edit(f"{em.gagal}**Please reply to message!!**")
    r = message.reply_to_message
    if not r.text and not r.document:
        return await proses.edit(
            f"{em.gagal}**Please reply to message text or document!!**"
        )
    if r.text:
        content = str(r.text)
    else:
        if r.document.file_size > 40000:
            return await proses.edit(f"{em.gagal}**Maximum size is 40000!!**")
        doc = await message.reply_to_message.download()
        async with aiofiles.open(doc, mode="r") as f:
            content = await f.read()
        os.remove(doc)
    link = await Tools.paste(content)
    photo = await Tools.screen_web(link, True)
    try:
        await message.reply_document(
            photo, caption=f"{em.sukses}<b>Succesed <a href='{link}'>link</a></b>"
        )
        return await proses.delete()
    except Exception:
        await message.reply(f"{em.sukses}<b>Succesed <a href='{link}'>link</a></b>")
        return await proses.delete()


async def spekhp_cmd(client, message):
    em = Emoji(client)
    await em.get()
    proses = await animate_proses(message, em.proses)

    if len(message.command) < 2:
        return await proses.edit(
            f"{em.gagal}**Usage:** `{message.text.split()[0]} Infinix Smart 8`"
        )

    query = message.text.split(None, 1)[1]

    try:
        payload = {"name": query}
        url = "https://nolimitdev.cloud/api/tools/gsmarena"
        result = await Tools.fetch.post(url, json=payload)

        if result.status_code != 200:
            return await proses.edit(f"{em.gagal}**Gagal mengambil data dari API!**")

        data = result.json().get("result")
        if not data:
            return await proses.edit(f"{em.gagal}**Data tidak ditemukan.**")

        name = data.get("name", "-")
        rilis = data.get("releaseDate", "-")
        os = data.get("os", "-")
        chipset = data.get("chipset", "-")
        ram = data.get("ram", "-")
        storage = data.get("storage", "-")
        kamera = data.get("camera", "-") + " MP"
        video = data.get("video", "-")
        baterai = data.get("battery", "-") + " mAh"
        charging = data.get("charging", "-")
        display = data.get("displaySize", "-") + " " + data.get("displayResolution", "")
        image = data.get("imageUrl", None)

        teks = (
            f"📱 **{name}**\n"
            f"🗓️ Rilis: `{rilis}`\n"
            f"💽 OS: `{os}`\n"
            f"⚙️ Chipset: `{chipset}`\n"
            f"💾 RAM: `{ram} GB`\n"
            f"📦 Penyimpanan: `{storage}`\n"
            f"📷 Kamera: `{kamera}`\n"
            f"🎞️ Video: `{video}`\n"
            f"🔋 Baterai: `{baterai}`\n"
            f"⚡ Charging: `{charging}`\n"
            f"🖥️ Layar: `{display}`\n"
        )

        if image:
            await message.reply_photo(photo=image, caption=teks)
        else:
            await message.reply(teks)

    except Exception as err:
        await message.reply(f"{em.gagal}**Gagal memuat spesifikasi HP!\n\n`{err}`**")

    return await proses.delete()


async def infoanime_cmd(client, message):
    em = Emoji(client)
    await em.get()
    proses = await animate_proses(message, em.proses)
    url = "https://nolimitdev.cloud/api/search/anime"
    response = await Tools.fetch.post(url)
    if response.status_code != 200:
        return await proses.edit(
            f"{em.gagal}**Please try again later: {response.status_code}!!**"
        )
    if not response.json().get("result"):
        return await proses.edit(
            f"{em.gagal}**Please try again later: {response.status_code}!!**"
        )
    data = response.json()["result"]
    uniq = f"{str(uuid4())}"
    state.set(uniq.split("-")[0], "anime", data)
    inline = await ButtonUtils.send_inline_bot_result(
        message,
        message.chat.id,
        bot.me.username,
        f"inline_anime {uniq.split('-')[0]}",
    )
    if inline:
        return await proses.delete()
    else:
        return await proses.edit(
            f"{em.gagal}**Please try again later: {response.status_code}!!**"
        )


async def lyric_cmd(client, message):
    em = Emoji(client)
    await em.get()
    proses = await animate_proses(message, em.proses)
    prompt = client.get_text(message)
    if not prompt:
        return await proses.edit(
            f"{em.gagal}**Please give me prompt!\nExample: `{message.text.split()[0]} Dear God`.**"
        )

    url = "https://api.maelyn.eu/api/tools/search-lyrics"
    headers = {"x-maelyn-auth": API_MAELYN}
    try:
        respon = await Tools.fetch.get(url, headers=headers, params={"search": prompt})
    except Exception as er:
        return await proses.edit(f"{em.gagal}**ERROR:** {str(er)}")

    try:
        body = respon.json()
    except Exception:
        body = {}

    if respon.status_code != 200 or not body.get("success"):
        pesan = body.get("message") or f"HTTP {respon.status_code}"
        return await proses.edit(f"{em.gagal}**Please try again later: {pesan}**")

    data = body.get("result") or {}
    lyrics = (data.get("lyrics") or "").strip()
    if not lyrics:
        return await proses.edit(f"{em.gagal}**Lirik tidak ditemukan.**")

    title = escape(data.get("title") or prompt)
    artist = escape(data.get("artist") or "-")
    link = data.get("url") or ""
    header = f"{em.sukses}<b>{title}</b>\n<b>Artist:</b> {artist}\n"
    if link:
        header += f"<a href='{escape(link)}'>Genius</a>\n"

    teks = f"{header}\n<blockquote expandable>{escape(lyrics)}</blockquote>"
    if len(teks) <= 4000:
        try:
            await message.reply(teks, disable_web_page_preview=True)
            return await proses.delete()
        except Exception:
            pass

    # lirik terlalu panjang atau format gagal: kirim sebagai file
    with io.BytesIO(f"{data.get('title', prompt)}\n\n{lyrics}".encode()) as out_file:
        out_file.name = f"{prompt[:40]}.txt"
        await message.reply_document(document=out_file, caption=header)
    return await proses.delete()