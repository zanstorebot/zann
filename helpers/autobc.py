import asyncio
import datetime
import random
import traceback

from pyrogram.errors import FloodWait, NotAcceptable, UserBannedInChannel

from clients import alice
from config import BLACKLIST_GCAST
from database import dB
from logs import logger

from .emoji_logs import Emoji


async def get_auto_gcast_messages(client):
    entries = await dB.get_var(client.me.id, "AUTO_GCAST") or []
    return [await client.get_messages("me", int(e["message_id"])) for e in entries]


async def text_autogcast(client):
    auto_text_vars = await dB.get_var(client.me.id, "AUTO_GCAST")
    list_ids = [int(data["message_id"]) for data in auto_text_vars]
    list_text = []
    for ids in list_ids:
        msg = await client.get_messages("me", ids)
        text = msg.text or msg.caption
        list_text.append(text)
    return list_text


async def add_auto_text(message):
    client = message._client
    auto_text = await dB.get_var(client.me.id, "AUTO_GCAST") or []
    rep = message.reply_to_message
    logs = "me"

    type_mapping = {
        "text": rep.text,
        "photo": rep.photo,
        "voice": rep.voice,
        "audio": rep.audio,
        "video": rep.video,
        "video_note": rep.video_note,
        "animation": rep.animation,
        "sticker": rep.sticker,
        "document": rep.document,
        "contact": rep.contact,
    }

    for media_type, media in type_mapping.items():
        if media:
            copied = await rep.copy(logs)
            auto_text.append(
                {
                    "type": media_type,
                    "message_id": copied.id,
                }
            )
            await dB.set_var(client.me.id, "AUTO_GCAST", auto_text)
            break


async def auto_broadcast(client):
    em = Emoji(client)
    await em.get()
    try:

        while True:
            if not await dB.get_var(client.me.id, "AUTOBC"):
                await asyncio.sleep(5)
                continue

            messages = await get_auto_gcast_messages(client)
            if not messages:
                await asyncio.sleep(5)   # tanpa jeda = loop berputar terus, CPU 100%
                continue

            done = await dB.get_var(client.me.id, "ROUNDS") or 0
            group, failed = 0, 0
            delay = await dB.get_var(client.me.id, "DELAY_GCAST") or 300
            blacklist = set(
                await dB.get_list_from_var(client.me.id, "BLACKLIST_GCAST") or []
            ) | set(BLACKLIST_GCAST)

            selected_msg = random.choice(messages)
            peer = client._get_my_peer.get(client.me.id)
            if not peer:
                chats = await client.get_chat_id("group")
            else:
                if len(peer.get("group", [])) != 0:
                    chats = peer["group"]
                else:
                    chats = await client.get_chat_id("group")

            for chat_id in chats:
                if chat_id in blacklist:
                    continue
                try:
                    await selected_msg.copy(chat_id)
                    group += 1
                    await asyncio.sleep(0.5)
                except FloodWait as e:
                    await asyncio.sleep(e.value)
                    try:
                        await selected_msg.copy(chat_id)
                        group += 1
                    except Exception as e:
                        failed += 1
                except Exception as e:
                    failed += 1
                except UserBannedInChannel:
                    failed += 1
                    await client.send_message(
                        "me", "**Your account has limited**\nAuto disable status to off"
                    )
                    await dB.remove_var(client.me.id, "AUTOBC")

            done += 1
            await dB.set_var(client.me.id, "ROUNDS", done)
            await dB.set_var(client.me.id, "SUCCES_GROUP", group)
            await dB.set_var(
                client.me.id, "LAST_TIME", datetime.datetime.utcnow().timestamp()
            )

            summary = (
                f"<b><i>{em.warn}Autobc Done\n"
                f"{em.sukses}Berhasil : {group} Chat\n"
                f"{em.gagal}Gagal : {failed} Chat\n"
                f"{em.msg}Putaran Ke {done} Delay {delay} detik</i></b>"
            )
            try:
                await client.send_message("me", summary)
            except Exception:
                await dB.remove_var(client.me.id, "AUTOBC")
            await asyncio.sleep(int(delay))
    except NotAcceptable:
        await dB.remove_var(client.me.id, "AUTOBC")


async def AutoBC():
    for userbot in alice._ubot:
        try:
            asyncio.create_task(auto_broadcast(userbot))
        except Exception as e:
            logger.error(
                f"Error in AutoBC for {userbot.me.first_name}: {e}\n{traceback.format_exc()}"
            )
