import asyncio
import re
import traceback
from datetime import datetime
from html import escape

from helpers import Emoji, Tools, animate_proses
from helpers.fakex_render import ensure_fonts, render_fake_post
from logs import logger

# opsi hanya dibaca di depan teks
FAKEX_OPTIONS = {"dark", "dim", "light"}  # tema; centang biru & logo X selalu tampil
MAX_TEXT = 1000


def _parse(raw):
    """'.fakex dark Halo' -> ({'dark'}, 'Halo')"""
    parts = raw.split(None, 1)[1].split(" ") if len(raw.split(None, 1)) > 1 else []
    opts = set()
    while parts and parts[0].lower() in FAKEX_OPTIONS:
        opts.add(parts.pop(0).lower())
    return opts, " ".join(parts).strip()


def _identity(entity):
    """(nama tampilan, username) dari User atau Chat (sender_chat)."""
    name = " ".join(filter(None, [getattr(entity, "first_name", None),
                                  getattr(entity, "last_name", None)]))
    name = name or getattr(entity, "title", "") or "User"
    handle = getattr(entity, "username", None) or re.sub(r"\W+", "", name.lower())[:15]
    return name, handle or "user"


async def _download(client, file_id):
    if not file_id:
        return None
    try:
        return await client.download_media(file_id, in_memory=True)
    except Exception:
        logger.warning(f"fakex: gagal unduh media: {traceback.format_exc()}")
        return None


async def fakex_cmd(client, message):
    em = Emoji(client)
    await em.get()
    raw = message.text or message.caption or ""
    proses = await animate_proses(message, em.proses)

    opts, text = _parse(raw)
    rep = message.reply_to_message
    if not text and rep:
        text = (rep.text or rep.caption or "").strip()
    if not text:
        return await proses.edit(
            f"{em.gagal}<b>Tulis isi postingannya!</b>\n"
            f"Contoh: <code>{raw.split()[0]} dark Halo dunia 🔥</code>\n"
            f"Reply orang = pakai nama &amp; foto profilnya."
        )
    if len(text) > MAX_TEXT:
        return await proses.edit(f"{em.gagal}<b>Teks maksimal {MAX_TEXT} karakter.</b>")

    # identitas: user yang di-reply, kalau tidak ada = diri sendiri
    target = (rep.from_user or rep.sender_chat) if rep else (message.from_user or message.sender_chat)
    name, handle = _identity(target)

    try:
        await ensure_fonts(Tools.fetch)
        photo = getattr(target, "photo", None)
        avatar = await _download(client, photo.big_file_id if photo else None)
        media_msg = rep if rep and rep.photo else (message if message.photo else None)
        media = await _download(client, media_msg.photo.file_id) if media_msg else None

        image = await asyncio.to_thread(
            render_fake_post, name, handle, text,
            avatar=avatar,
            media=media,
            theme=next((t for t in ("dark", "dim", "light") if t in opts), "light"),
            verified=True,
            xbadge=True,
            when=datetime.now(Tools.JAKARTA_TZ),
        )
        await message.reply_photo(image)
        return await proses.delete()
    except Exception as e:
        logger.error(f"fakex gagal: {traceback.format_exc()}")
        return await proses.edit(f"{em.gagal}<b>ERROR:</b> <code>{escape(str(e))}</code>")
