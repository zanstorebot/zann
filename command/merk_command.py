import asyncio
import traceback
from datetime import datetime
from html import escape

from helpers import Emoji, Tools, animate_proses
from helpers.marina_render import ensure_font as marina_font, render_marina
from helpers.fakex_render import ensure_fonts as inter_fonts
from helpers.nulis_render import ensure_font as nulis_font, render_nulis
from helpers.spanduk_render import ensure_font as spanduk_font, render_spanduk
from helpers.sutra_render import ensure_font as sutra_font, render_sutra
from helpers.waios_render import render_wa_ios, uses_sf
from logs import logger

# nama command -> (unduh font, render, maks panjang teks)
MERK = {
    "marina": (marina_font, render_marina, 20),
    "sutra": (sutra_font, render_sutra, 24),
}

# command teks -> gambar (tanpa foto profil)
TEKS = {
    "nulis": (nulis_font, render_nulis, 450),
    "spanduk": (spanduk_font, render_spanduk, 40),
}


async def _download(client, file_id):
    try:
        return await client.download_media(file_id, in_memory=True)
    except Exception:
        logger.warning(f"merk: gagal unduh foto: {traceback.format_exc()}")
        return None


async def _merk_cmd(client, message, merk):
    ensure_font, render, max_len = MERK[merk]
    em = Emoji(client)
    await em.get()
    raw = message.text or message.caption or ""
    proses = await animate_proses(message, em.proses)

    args = raw.split(None, 1)
    text = args[1].strip() if len(args) > 1 else None
    if text and len(text) > max_len:
        return await proses.edit(f"{em.gagal}<b>Teks maksimal {max_len} karakter.</b>")

    rep = message.reply_to_message
    target = (rep.from_user or rep.sender_chat) if rep else (message.from_user or message.sender_chat)
    photo = getattr(target, "photo", None)
    if not photo:
        return await proses.edit(f"{em.gagal}<b>User ini tidak punya foto profil!</b>")

    try:
        await ensure_font(Tools.fetch)
        avatar = await _download(client, photo.big_file_id)
        if not avatar:
            return await proses.edit(f"{em.gagal}<b>Gagal mengunduh foto profil.</b>")
        image = await asyncio.to_thread(render, avatar, text)
        # 2048px: Telegram menyimpan sebagai foto HD (tidak diperkecil ke 1280)
        await message.reply_photo(image)
        return await proses.delete()
    except Exception as e:
        logger.error(f"{merk} gagal: {traceback.format_exc()}")
        return await proses.edit(f"{em.gagal}<b>ERROR:</b> <code>{escape(str(e))}</code>")


async def marina_cmd(client, message):
    return await _merk_cmd(client, message, "marina")


async def sutra_cmd(client, message):
    return await _merk_cmd(client, message, "sutra")


# ======================================================================
# nulis & spanduk: teks diketik atau diambil dari pesan yang di-reply
# ======================================================================
async def _teks_cmd(client, message, mode):
    ensure_font, render, max_len = TEKS[mode]
    em = Emoji(client)
    await em.get()
    raw = message.text or message.caption or ""
    proses = await animate_proses(message, em.proses)

    args = raw.split(None, 1)
    text = args[1].strip() if len(args) > 1 else ""
    rep = message.reply_to_message
    if not text and rep:
        text = (rep.text or rep.caption or "").strip()
    if not text:
        return await proses.edit(
            f"{em.gagal}<b>Tulis teks atau reply pesan!</b>\n"
            f"Contoh: <code>{raw.split()[0]} Halo semuanya</code>"
        )
    if len(text) > max_len:
        return await proses.edit(f"{em.gagal}<b>Teks maksimal {max_len} karakter.</b>")

    try:
        await ensure_font(Tools.fetch)
        # render berat (numpy/PIL) dijalankan di thread supaya bot tidak macet
        image = await asyncio.to_thread(render, text)
        await message.reply_photo(image)
        return await proses.delete()
    except ValueError as e:  # teks tidak muat di kertas
        return await proses.edit(f"{em.gagal}<b>{escape(str(e))}</b>")
    except Exception as e:
        logger.error(f"{mode} gagal: {traceback.format_exc()}")
        return await proses.edit(f"{em.gagal}<b>ERROR:</b> <code>{escape(str(e))}</code>")


async def nulis_cmd(client, message):
    return await _teks_cmd(client, message, "nulis")


async def spanduk_cmd(client, message):
    return await _teks_cmd(client, message, "spanduk")


# ======================================================================
# ios: screenshot WhatsApp iOS (pesan ditekan lama)
# ======================================================================
IOS_THEMES = ("dark", "light")
IOS_MAX_TEXT = 500


async def ios_cmd(client, message):
    em = Emoji(client)
    await em.get()
    raw = message.text or message.caption or ""
    proses = await animate_proses(message, em.proses)

    parts = raw.split(None, 2)[1:]
    theme = parts.pop(0).lower() if parts and parts[0].lower() in IOS_THEMES else "dark"
    text = " ".join(parts).strip()
    rep = message.reply_to_message
    if not text and rep:
        text = (rep.text or rep.caption or "").strip()
    if not text:
        return await proses.edit(
            f"{em.gagal}<b>Tulis teks atau reply pesan!</b>\n"
            f"Contoh: <code>{raw.split()[0]} light I love you 💕</code>"
        )
    if len(text) > IOS_MAX_TEXT:
        return await proses.edit(f"{em.gagal}<b>Teks maksimal {IOS_MAX_TEXT} karakter.</b>")

    try:
        # Inter + emoji berwarna (cadangan kalau font SF tidak ada)
        await inter_fonts(Tools.fetch)
        if not uses_sf():
            logger.warning("ios: font SF tidak ditemukan di storage/cache, pakai Inter")
        image = await asyncio.to_thread(
            render_wa_ios, text, theme, datetime.now(Tools.JAKARTA_TZ)
        )
        # PNG sebagai foto: 1179x2556 = resolusi asli iPhone, tetap tajam (HD)
        await message.reply_photo(image)
        return await proses.delete()
    except Exception as e:
        logger.error(f"ios gagal: {traceback.format_exc()}")
        return await proses.edit(f"{em.gagal}<b>ERROR:</b> <code>{escape(str(e))}</code>")
