import asyncio
from datetime import datetime

from database import dB
from helpers import Emoji, add_auto_text, animate_proses, text_autogcast

from .spambot_command import spam_bot

AG = []
LT = []


def extract_type_and_text(message):
    args = message.text.split(None, 2)
    if len(args) < 2:
        return None, None

    type = args[1]
    msg = (
        message.reply_to_message.text
        if message.reply_to_message
        else args[2] if len(args) > 2 else None
    )
    return type, msg


async def autobc_cmd(client, message):
    em = Emoji(client)
    await em.get()

    msg = await animate_proses(message, em.proses)
    type, value = extract_type_and_text(message)
    reply = message.reply_to_message
    auto_text_vars = await dB.get_var(client.me.id, "AUTO_GCAST")
    if type == "on":
        if not auto_text_vars:
            return await msg.edit(
                f"{em.gagal}**Please add custom text before setting it on!!**"
            )
        if await dB.get_var(client.me.id, "AUTOBC"):
            return await msg.edit(f"{em.gagal}<b>Autogcast already turned on.</b>")
        else:
            await dB.set_var(client.me.id, "AUTOBC", True)
            return await msg.edit(f"{em.sukses}<b>Autogcast turned on.</b>")
    elif type == "off":
        if await dB.get_var(client.me.id, "AUTOBC"):
            await dB.remove_var(client.me.id, "AUTOBC")
            return await msg.edit(f"{em.gagal}<b>Autogcast has been stopped.</b>")
        else:
            return await msg.edit(f"{em.sukses}<b>Autogcast already off.</b>")
    elif type == "add":
        if not reply:
            return await msg.edit(
                f"{em.gagal}<b>At least reply to a text, idiot, to create the message.</b>"
            )
        await add_auto_text(message)
        return await msg.edit(
            f"{em.sukses}<b>Saved for Auto Gcast message.</b>",
        )

    elif type == "delay":
        await dB.set_var(client.me.id, "DELAY_GCAST", value)
        return await msg.edit(
            f"{em.sukses}<b>Auto Gcast delay set to: <code>{value}</code> Second.</b>"
        )

    elif type == "del":
        if not value:
            return await msg.edit(
                f"{em.gagal}<b>At least provide a number or all, idiot, which text to delete.</b>"
            )
        if value == "all":
            await dB.set_var(client.me.id, "AUTO_GCAST", [])
            return await msg.edit(
                f"{em.sukses}<b>All your annoying texts have been deleted.</b>"
            )
        try:
            value = int(value) - 1
            auto_text_vars.pop(value)
            await dB.set_var(client.me.id, "AUTO_GCAST", auto_text_vars)
            return await msg.edit(
                f"{em.sukses}<b>Text number: <code>{value+1}</code> deleted.</b>"
            )
        except Exception as error:
            return await msg.edit(str(error))

    elif type == "get":
        if not auto_text_vars:
            return await msg.edit(
                f"{em.gagal}<b>Your Auto Gcast text is empty, idiot.</b>"
            )
        txt = "<b>Your Annoying Gcast Texts</b>\n\n"
        data = await text_autogcast(client)
        for num, x in enumerate(data, 1):
            txt += f"{num}: {x}\n\n"
        return await msg.edit(txt)

    elif type == "status":
        status = await dB.get_var(client.me.id, "AUTOBC")
        delay = await dB.get_var(client.me.id, "DELAY_GCAST") or 300
        msgs = await dB.get_var(client.me.id, "AUTO_GCAST") or []
        rounds = await dB.get_var(client.me.id, "ROUNDS") or 0
        last_broadcast = await dB.get_var(client.me.id, "LAST_TIME") or 0
        status_text = f"{em.sukses}Actived" if status else f"{em.gagal}Deactivated"
        last_broadcast_time = (
            f"<code>{datetime.utcfromtimestamp(last_broadcast).strftime('%Y-%m-%d %H:%M:%S')} UTC</code>"
            if last_broadcast
            else "No broadcast yet"
        )
        total_groups = await dB.get_var(client.me.id, "SUCCES_GROUP") or 0
        await msg.edit(
            f"""
<blockquote>**__📑 Status Auto Broadcast:
👤 Status: {status_text}
🗓️ Jumlah Grup: {total_groups}
⌛ Delay: {delay}  detik 
📑 Pesan Di Simpan: {len(msgs)} Pesan
🔃 Putaran: {rounds} Kali
⏰ Terakhir Broadcast: {last_broadcast_time}__**</blockquote>"""
        )

    elif type == "limit":
        if value == "off":
            if client.me.id in LT:
                LT.remove(client.me.id)
                return await msg.edit(f"{em.gagal}<b>Auto Limit turned off.</b>")
            else:
                return await msg.delete()

        elif value == "on":
            if client.me.id not in LT:
                LT.append(client.me.id)
                await msg.edit(f"{em.sukses}<b>Auto Limit turned on.</b>")
                while client.me.id in LT:
                    for x in range(2):
                        await spam_bot(client, message)
                        await asyncio.sleep(5)
                    await asyncio.sleep(1200)
            else:
                return await msg.delete()
        else:
            return await msg.edit(
                f"{em.gagal}<b>Wrong, idiot!! At least read the  Command Help.</b>"
            )
    else:
        return await msg.edit(
            f"{em.gagal}<b>Wrong, idiot!! At least read the  Command Help.</b>"
        )
    return
