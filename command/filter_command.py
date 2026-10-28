import asyncio
import re
import traceback

from pyrogram.enums import ParseMode
from pyrogram.errors import MediaEmpty

from clients import bot
from database import dB, state
from helpers import ButtonUtils, Emoji, Message, Tools, animate_proses
from logs import logger


async def REP_BLOCK(client, message):
    em = Emoji(client)
    await em.get()
    return await message.reply_text(
        f"{em.block}**Ga usah reply apalagi tag gw, lu udah block gua anak KONTOL!!**"
    )


async def filter_cmd(client, message):
    em = Emoji(client)
    await em.get()

    xx = await animate_proses(message, em.proses)
    rep = message.reply_to_message
    if len(message.command) < 2 or not rep:
        return await xx.edit(f"{em.gagal}**Please reply message and give filter name**")
    nama = message.text.split()[1]
    getfilter = await dB.get_var(client.me.id, nama, "filter")
    if getfilter:
        return await xx.edit(f"{em.gagal}**Filter {nama} already exist!**")
    value = None

    text = rep.text or rep.caption or ""
    entities = rep.entities or rep.caption_entities
    if rep.media:
        copy = await rep.copy(bot.me.username)
        sent = await client.send_message(
            bot.me.username, f"/id {nama}", reply_to_message_id=copy.id
        )
        await asyncio.sleep(1)
        await sent.delete()
        await copy.delete()
        extract = Tools.dump_entity(text, entities)
        type = state.get(client.me.id, nama)
        value = {
            "type": type["type"],
            "file_id": type["file_id"],
            "result": extract,
        }
    else:
        extract = Tools.dump_entity(text, entities)
        value = {"type": "text", "file_id": "", "result": extract}
    if value:
        await dB.set_var(client.me.id, nama, value, "filter")
        return await xx.edit(f"{em.sukses}**Saved {nama} filter!!**")
    else:
        return await xx.edit(f"{em.gagal}**Please reply message and give filter name**")


async def getfilter_cmd(client, message):
    em = Emoji(client)
    await em.get()
    xx = await animate_proses(message, em.proses)

    try:
        if len(message.text.split()) == 3 and (message.text.split())[2] in [
            "noformat",
            "raw",
        ]:
            filter = message.text.split()[1]
            data = await dB.get_var(client.me.id, filter, "filter")
            if not data:
                return await xx.edit(f"{em.gagal}**Filter {filter} not found!**")
            return await get_raw_filter(client, message, xx, filter, data)
        else:
            return await xx.edit(
                f"{em.gagal}**Please valid command.\nExample: `{message.text.split()[0]} ciah noformat`.**"
            )
    except Exception as e:
        return await xx.edit(f"{em.gagal}**ERROR**: {str(e)}")


async def get_raw_filter(client, message, xx, filter, data):
    em = Emoji(client)
    await em.get()
    thetext = data["result"].get("text")
    _, button = ButtonUtils.parse_msg_buttons(thetext)
    try:
        if button:
            type = data["type"]
            file_id = data["file_id"]
            if type == "text":
                await message.reply(
                    data["result"].get("text"),
                    parse_mode=ParseMode.DISABLED,
                    reply_to_message_id=Message.ReplyCheck(message),
                )
            else:
                kwargs = {
                    "photo": bot.send_photo,
                    "voice": bot.send_voice,
                    "audio": bot.send_audio,
                    "video": bot.send_video,
                    "animation": bot.send_animation,
                    "document": bot.send_document,
                }
                if type in kwargs:
                    disend = await kwargs[type](
                        client.me.id,
                        file_id,
                        caption=data["result"].get("text"),
                        parse_mode=ParseMode.DISABLED,
                    )
                    async for copy_msg in client.search_messages(bot.id, limit=1):
                        await copy_msg.copy(message.chat.id)
                        break
                    await disend.delete()

        else:
            type = data["type"]
            file_id = data["file_id"]

            if type == "text":
                await message.reply(
                    data["result"].get("text"),
                    parse_mode=ParseMode.DISABLED,
                    reply_to_message_id=Message.ReplyCheck(message),
                )
            elif type == "sticker":
                await message.reply_sticker(
                    file_id,
                    reply_to_message_id=Message.ReplyCheck(message),
                )
            elif type == "video_filter":
                await message.reply_video_filter(
                    file_id, reply_to_message_id=Message.ReplyCheck(message)
                )
            else:
                kwargs = {
                    "photo": message.reply_photo,
                    "voice": message.reply_voice,
                    "audio": message.reply_audio,
                    "video": message.reply_video,
                    "animation": message.reply_animation,
                    "document": message.reply_document,
                }

                if type in kwargs:
                    await kwargs[type](
                        file_id,
                        caption=data["result"].get("text"),
                        parse_mode=ParseMode.DISABLED,
                        reply_to_message_id=Message.ReplyCheck(message),
                    )
    except Exception as er:
        logger.info(f"ERROR: {traceback.format_exc()}")
        return await message.reply(f"{em.gagal}**ERROR**: {str(er)}")
    return await xx.delete()


async def filters_cmd(client, message):
    em = Emoji(client)
    await em.get()

    xx = await animate_proses(message, em.proses)
    getfilter = await dB.all_var(client.me.id, "filter")
    if not getfilter:
        return await xx.edit(f"{em.gagal}**You dont have any filter!**")
    rply = f"{em.msg}**List of Filters:**\n\n"
    for x, data in getfilter.items():
        type = await dB.get_var(client.me.id, x, "filter")
        rply += f"**• Name: `{x}` | Type: `{type['type']}`**\n"
    return await xx.edit(rply)


async def stopfilter_cmd(client, message):
    em = Emoji(client)
    await em.get()
    args = client.get_arg(message).split(",")

    xx = await animate_proses(message, em.proses)

    if len(args) == 0 or (len(args) == 1 and args[0].strip() == ""):
        return await xx.edit(f"{em.gagal}**Which filter do you want to delete?**")
    if message.command[1] == "all":
        if not await dB.all_var(client.me.id, "filter"):
            return await xx.edit(f"{em.gagal}**You dont have any filter!**")
        for nama in await dB.all_var(client.me.id, "filter"):
            data = await dB.get_var(client.me.id, nama, "filter")
            await dB.remove_var(client.me.id, nama, "filter")
        return await xx.edit(f"{em.sukses}**Succesfully deleted all filter!**")
    else:
        gagal_list = []
        sukses_list = []

        for arg in args:
            arg = arg.strip()
            if not arg:
                continue
            data = await dB.get_var(client.me.id, arg, "filter")
            if not data:
                gagal_list.append(arg)
            else:
                await dB.remove_var(client.me.id, arg, "filter")
                sukses_list.append(arg)

        if sukses_list:
            return await xx.edit(
                f"{em.sukses}**Filter `{', '.join(sukses_list)}` successfully deleted.**"
            )

        if gagal_list:
            return await xx.edit(
                f"{em.gagal}**Filter `{', '.join(gagal_list)}` not found!**"
            )


async def FILTERS(client, message):
    # handler ini jalan di SETIAP pesan masuk: cek yang murah dulu, DB belakangan
    text = message.text
    if not text:
        return
    try:
        getfilter = await dB.all_var(client.me.id, "filter")
        if not getfilter:
            return
        blacklist = await dB.get_list_from_var(client.me.id, "BLACKLIST_GCAST")
        reply = message.from_user or message.sender_chat
        reply.id
        for word in getfilter:
            pattern = rf"\b{re.escape(word)}\b"
            if not re.search(pattern, text, flags=re.IGNORECASE):
                continue
            if message.chat.id in blacklist:
                continue

            _filter = await dB.get_var(client.me.id, word, "filter")
            data_type, file_id = _filter["type"], _filter.get("file_id")
            data = _filter["result"].get("text")
            teks = await Tools.escape_filter(message, data, Tools.parse_words)
            if data_type != "text" and not file_id:
                continue

            if data_type:

                if data_type == "text":
                    await message.reply(
                        teks,
                        disable_web_page_preview=True,
                        parse_mode=ParseMode.HTML,
                    )
                else:
                    pre_senders = {
                        "photo": bot.send_photo,
                        "voice": bot.send_voice,
                        "audio": bot.send_audio,
                        "video": bot.send_video,
                        "animation": bot.send_animation,
                        "document": bot.send_document,
                        "sticker": bot.send_sticker,
                        "video_note": bot.send_video_note,
                    }
                    reply_senders = {
                        "photo": message.reply_photo,
                        "voice": message.reply_voice,
                        "audio": message.reply_audio,
                        "video": message.reply_video,
                        "animation": message.reply_animation,
                        "document": message.reply_document,
                        "sticker": message.reply_sticker,
                        "video_note": message.reply_video_note,
                    }
                    file_attrs = {
                        "photo": "photo",
                        "voice": "voice",
                        "audio": "audio",
                        "video": "video",
                        "animation": "animation",
                        "document": "document",
                        "sticker": "sticker",
                        "video_note": "video_note",
                    }
                    try:
                        didel = await pre_senders[data_type](client.me.id, file_id)
                    except MediaEmpty:
                        pass
                    async for media in client.search_messages(bot.username, limit=1):
                        media_obj = getattr(media, file_attrs[data_type], None)
                        new_fileid = (
                            getattr(media_obj, "file_id", None) if media_obj else None
                        )
                        break
                    else:
                        new_fileid = None

                    if not new_fileid:
                        return
                    try:
                        await bot.delete_messages(bot.username, didel.id)
                    except Exception:
                        pass
                    kwargs = {"reply_to_message_id": message.id}
                    if data_type not in ["sticker", "video_note"]:
                        kwargs["caption"] = teks
                        kwargs["parse_mode"] = ParseMode.HTML

                    await reply_senders[data_type](new_fileid, **kwargs)
    except Exception:
        logger.error(
            f"Eror filter pada pesan: {message.text}\n{traceback.format_exc()}"
        )
