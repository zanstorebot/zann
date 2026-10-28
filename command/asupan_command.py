import asyncio
import random
from random import choice

from pyrogram import enums, types
from helpers import Emoji, animate_proses

import aiohttp
from config import API_BOTCHAX  # sesuaikan nama variabel di config.py

ASUPAN_API = "https://api.botcahx.eu.org/api/asupan"
ASUPAN_TYPES = ["cecan", "hijaber", "ukhty"]


async def asupan_cmd(client, message):
    em = Emoji(client)
    await em.get()

    y = await animate_proses(message, em.proses)
    try:
        tipe = random.choice(ASUPAN_TYPES)
        url = f"{ASUPAN_API}/{tipe}?apikey={API_BOTCHAX}"

        # endpoint bisa mengembalikan video langsung atau JSON berisi url
        video_url = url
        async with aiohttp.ClientSession() as session:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as resp:
                if resp.status != 200:
                    raise Exception(f"API status {resp.status}")
                ctype = resp.headers.get("Content-Type", "")
                if "json" in ctype:
                    data = await resp.json()
                    video_url = (
                        data.get("url")
                        or data.get("result")
                        or (data.get("data") or {}).get("url")
                    )
                    if not video_url:
                        raise Exception("URL video tidak ditemukan")

        await client.send_video(
            message.chat.id,
            video=video_url,
            caption=(
                f"{em.sukses}<b>Upload by: "
                f"<a href=tg://user?id={client.me.id}>"
                f"{client.me.first_name} {client.me.last_name or ''}</a></b>"
            ),
            reply_to_message_id=message.id,
        )
        return await y.delete()
    except Exception:
        return await y.edit(f"{em.gagal}<b>Try a gain!</b>")


async def pap_cmd(client, message):
    em = Emoji(client)
    await em.get()

    y = await animate_proses(message, em.proses)
    await asyncio.sleep(3)
    await message.reply_photo(
        choice(
            [
                lol.photo.file_id
                async for lol in client.search_messages(
                    "@mm_kyran", filter=enums.MessagesFilter.PHOTO
                )
            ]
        ),
        False,
        caption=f"{em.sukses}<b>Ange ga kamu???</b>",
    )
    await y.delete()


async def ppcp_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    pros = await animate_proses(message, emo.proses)

    url = "medialuci"
    ppcp_pairs = []

    try:
        photos = []
        async for media in client.search_messages(
            url, filter=enums.MessagesFilter.PHOTO
        ):
            photos.append(media.photo.file_id)

        if len(photos) < 2:
            return await pros.edit(
                f"{emo.gagal}<b>Gagal menemukan pasangan foto profil. Coba lagi nanti.</b>"
            )

        for i in range(0, len(photos) - 1, 2):
            ppcp_pairs.append([photos[i], photos[i + 1]])

        selected_pair = random.choice(ppcp_pairs)

        media_group = [types.InputMediaPhoto(photo) for photo in selected_pair]

        await client.send_media_group(
            message.chat.id,
            media=media_group,
            reply_to_message_id=message.id,
        )
        await pros.delete()

    except Exception as error:
        await pros.edit(f"{emo.gagal}<b>Error:</b>\n<code>{error}</code>")
