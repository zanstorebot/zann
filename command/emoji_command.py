from uuid import uuid4

from pyrogram import types
from pyrogram.enums import ParseMode

from clients import bot
from database import dB
from helpers import ButtonUtils, Emoji, animate_proses


async def id_cmd(client, message):
    em = Emoji(client)
    await em.get()
    uniq = f"{str(uuid4())}"
    inline = await ButtonUtils.send_inline_bot_result(
        message,
        message.chat.id,
        bot.me.username,
        f"inline_cekid {uniq.split('-')[0]} {id(message)}",
    )
    if inline:
        return await message.delete()
    else:
        chat = message.chat
        your_id = message.from_user if message.from_user else message.sender_chat
        message_id = message.id
        reply = message.reply_to_message

        text = f"**Message ID:** `{message_id}`\n"
        text += f"**Your ID:** `{your_id.id}`\n"
        text += f"**Chat ID:** `{chat.id}`\n"

        if reply:
            replied_user_id = (
                reply.from_user.id
                if reply.from_user
                else reply.sender_chat.id if reply.sender_chat else None
            )
            text += "\n**Replied Message Information:**\n"
            text += f"**├ Message ID:** `{reply.id}`\n"
            if replied_user_id:
                text += f"**├ User ID:** `{replied_user_id}`\n"

            if reply.entities:
                for entity in reply.entities:
                    if entity.custom_emoji_id:
                        text += f"**╰ Emoji ID:** `{entity.custom_emoji_id}`\n"

            if reply.photo:
                text += f"**╰ Photo File ID:** `{reply.photo.file_id}`\n"
            elif reply.video:
                text += f"**╰ Video File ID:** `{reply.video.file_id}`\n"
            elif reply.sticker:
                text += f"**╰ Sticker File ID:** `{reply.sticker.file_id}`\n"
            elif reply.animation:
                text += f"**╰ GIF File ID:** `{reply.animation.file_id}`\n"
            elif reply.document:
                text += f"**╰ Document File ID:** `{reply.document.file_id}`\n"

        if len(message.command) == 2:
            try:
                split = message.text.split(None, 1)[1].strip()
                user_id = (await client.get_users(split)).id
                text += f"\n**Mentioned User ID:** `{user_id}`\n"
            except Exception:
                return await message.reply_text(f"{em.gagal}**User tidak ditemukan.**")

        return await message.reply_text(
            text,
            disable_web_page_preview=True,
            parse_mode=ParseMode.MARKDOWN,
        )


async def setemoji_cmd(client, message):
    emo = Emoji(client)
    await emo.get()

    prem = client.me.is_premium
    pros = await animate_proses(message, emo.proses)
    if message.command[0] == "getemoji":
        return await pros.edit(
            f"<b>Emoji anda saat ini:</b>\n├ Ping: {emo.ping}\n├ Msg: {emo.msg}\n├ Sukses: {emo.sukses}\n├ Gagal: {emo.gagal}\n├ Proses: {emo.proses}\n├ Warn: {emo.warn}\n├ Block: {emo.block}\n├ Owner: {emo.owner}\n├ Uptime: {emo.uptime}\n├ Robot: {emo.robot}\n├ Klip: {emo.klip}\n├ Net: {emo.net}\n├ Up: {emo.up}\n├ Down: {emo.down}\n├ Speed: {emo.speed}\n╰ Profil: {emo.profil}</b>"
        )

    elif len(message.command) < 2 and not message.reply_to_message:
        return await message.reply(
            f"{emo.gagal}<b>Gunakan Format : <code>setemoji [value]</code></b>"
        )
    variable = message.command[1].lower() if len(message.command) > 1 else None
    if variable == "status":
        return await set_emoji_status(client, message)
    value = None
    emoji_id = None

    if message.reply_to_message:
        value = message.reply_to_message.text or message.reply_to_message.caption
        if prem and message.reply_to_message.entities:
            for entity in message.reply_to_message.entities:
                if entity.custom_emoji_id:
                    emoji_id = entity.custom_emoji_id
                    break
    elif len(message.command) >= 3:
        value = " ".join(message.command[2:])
        if prem and message.entities:
            for entity in message.entities:
                if entity.custom_emoji_id:
                    emoji_id = entity.custom_emoji_id
                    break

    valid_variables = [
        "ping",
        "msg",
        "warn",
        "block",
        "proses",
        "gagal",
        "sukses",
        "profil",
        "owner",
        "robot",
        "klip",
        "net",
        "up",
        "down",
        "speed",
        "uptime",
    ]
    if (
        not variable
        or variable not in valid_variables
        or not value
        and variable != "status"
    ):
        return await pros.edit(f"{emo.gagal}<b>Query tidak ditemukan!</b>!")

    if prem and emoji_id:
        print(f"Prem: {prem}, Id: {emoji_id}, Variable: {variable}")
        await dB.set_var(client.me.id, f"emo_{variable}", emoji_id)
        return await pros.edit(
            f"{emo.sukses}<b>Berhasil set Emoji {variable.capitalize()} menjadi:</b> <emoji id={emoji_id}>{value}</emoji>"
        )
    else:
        print(f"Prem: {prem}, Emoji: {value}, Variable: {variable}")
        await dB.set_var(client.me.id, f"emo_{variable}", value)
        return await pros.edit(
            f"{emo.sukses}<b>Berhasil set Emoji {variable.capitalize()} menjadi:</b> {value}"
        )


async def set_emoji_status(client, message):
    emo = Emoji(client)
    await emo.get()
    prem = client.me.is_premium
    if not prem:
        return await message.reply(
            f"{emo.gagal}<b>Anda bukan pengguna Telegram Premium.</b>"
        )

    pros = await animate_proses(message, emo.proses)

    rep = message.reply_to_message
    if not rep:
        rep = message
    emoji_id = None

    if rep.entities:
        for entity in rep.entities:
            if entity.custom_emoji_id:
                emoji_id = entity.custom_emoji_id
    else:
        return await pros.edit(
            f"{emo.gagal}<b>Silahkan balas Custom Emoji Premium.</b>"
        )

    if prem is True:
        if emoji_id:
            await client.set_emoji_status(types.EmojiStatus(custom_emoji_id=emoji_id))
            return await pros.edit(
                f"{emo.sukses}<b>Berhasil mengubah status Emoji menjadi: <emoji id={emoji_id}>😭</emoji></b>"
            )
    else:
        return await pros.edit(
            f"{emo.gagal}<b>Anda bukan pengguna Telegram Premium.</b>"
        )
