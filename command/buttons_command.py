import asyncio

from clients import bot
from config import DICT_BUTTON
from database import state
from helpers import ButtonUtils, Emoji


async def buttonch_cmd(client, message):
    proses = await message.reply_text("Processing...")
    rep = message.reply_to_message
    if not rep and len(message.command) < 2:
        return await proses.edit("Reply to message!!")
    state.set(client.me.id, "edit_reply_markup", rep.text)
    link = message.text.split(None, 1)[1]
    await client.send_message(bot.me.username, f"/button {link}")
    return await proses.edit("Done")


async def button_cmd(client, message):
    em = Emoji(client)
    await em.get()
    reply = message.reply_to_message
    if not reply:
        return await message.reply(
            f"{em.gagal}<b>Please reply to message with button format!</b>"
        )
    teks = client.get_text(message)
    DICT_BUTTON[client.me.id] = client.get_arg(message)
    chat_id = message.chat.id if len(message.command) < 2 else message.text.split()[1]
    if reply.media:
        copy = await reply.copy(bot.me.username)
        sent = await client.send_message(
            bot.me.username, "/id button_media", reply_to_message_id=copy.id
        )
        await asyncio.sleep(1)
        await sent.delete()
        await copy.delete()
        state.set(client.me.id, "button", DICT_BUTTON[client.me.id])
    else:
        state.set(client.me.id, "button", DICT_BUTTON[client.me.id])
    text, keyboard = ButtonUtils.parse_msg_buttons(teks)
    try:
        if keyboard:
            try:
                inline = await ButtonUtils.send_inline_bot_result(
                    message, chat_id, bot.me.username, f"make_button {client.me.id}"
                )
                if inline:
                    return await message.delete()
            except Exception as er:
                return await message.reply(f"{em.gagal}<b>ERROR: {str(er)}</b>")
        else:
            return await message.reply(
                f"{em.gagal}<b>Please reply to message with button format!</b>"
            )
    except IndexError:
        return await message.reply(
            f"{em.gagal}<b>Please reply to message with button format!</b>"
        )
