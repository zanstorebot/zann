import asyncio
import datetime
import traceback

from pyrogram.errors import FloodWait, UserBannedInChannel

from clients import alice
from config import BLACKLIST_GCAST
from database import dB
from logs import logger

from .emoji_logs import Emoji
from .tools import Tools


async def autofw_broadcast(client):
    em = Emoji(client)
    await em.get()

    while True:
        link = await dB.get_var(client.me.id, "AUTOFW_GCAST_TEXT")
        if not await dB.get_var(client.me.id, "AUTOFW"):
            await asyncio.sleep(5)
            continue

        if not link:
            await asyncio.sleep(5)   # tanpa jeda = loop berputar terus, CPU 100%
            continue

        chatids, messageids = Tools.get_link(link)
        # status = await client.get_messages(chatids, messageids)
        # if status.empty == True:
        # continue

        done = await dB.get_var(client.me.id, "ROUNDSFW") or 0
        group, failed = 0, 0
        delay = await dB.get_var(client.me.id, "DELAY_AUTOFW") or 300
        blacklist = set(
            await dB.get_list_from_var(client.me.id, "BLACKLIST_GCAST") or []
        ) | set(BLACKLIST_GCAST)

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
                await client.forward_messages(chat_id, chatids, message_ids=messageids)
                group += 1
                await asyncio.sleep(0.5)
            except FloodWait as e:
                await asyncio.sleep(e.value)
                try:
                    await client.forward_messages(
                        chat_id, chatids, message_ids=messageids
                    )
                    group += 1
                except Exception:
                    failed += 1
            except Exception:
                failed += 1
            except UserBannedInChannel:
                failed += 1
                await client.send_message(
                    "me", "**Your account has limited**\nAuto disable status to off"
                )
                await dB.remove_var(client.me.id, "AUTOFW")
                break

        done += 1
        await dB.set_var(client.me.id, "ROUNDSFW", done)
        await dB.set_var(client.me.id, "SUCCESFW_GROUP", group)
        await dB.set_var(
            client.me.id, "LAST_TIME", datetime.datetime.utcnow().timestamp()
        )
        summary = (
            f"<b><i>{em.warn}AUTOFW Done\n"
            f"{em.sukses}Berhasil : {group} Chat\n"
            f"{em.gagal}Gagal : {failed} Chat\n"
            f"{em.msg}Putaran Ke {done} Delay {delay} detik</i></b>"
        )
        try:
            await client.send_message("me", summary)
        except Exception:
            await dB.remove_var(client.me.id, "AUTOFW")
        await asyncio.sleep(int(delay))


async def AutoFW():
    for userbot in alice._ubot:
        try:
            asyncio.create_task(autofw_broadcast(userbot))
        except Exception as e:
            logger.error(
                f"Error in AutoFW for {userbot.me.first_name}: {e}\n{traceback.format_exc()}"
            )
