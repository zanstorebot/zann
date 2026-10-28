import asyncio
import os
import sys
import traceback
from datetime import datetime, timezone

from pyrogram import enums
from pyrogram.enums import ButtonStyle
from pyrogram.errors import (ChannelInvalid, ChannelPrivate,
                             ChatForwardsRestricted, FloodWait,
                             MediaCaptionTooLong, MessageIdInvalid,
                             MessageTooLong, PeerIdInvalid)
from pyrogram.helpers import ikb
from pytz import timezone

from clients import bot
from config import LOG_BACKUP
from database import dB, state
from helpers import Emoji, Tools, animate_proses
from logs import logger

logger_cache = {}
reply_cache = []
_deleted_locks = {}


def _deleted_lock(owner):
    return _deleted_locks.setdefault(owner, asyncio.Lock())


def _deleted_var(owner, chat_id):
    peer = f"n{abs(chat_id)}" if chat_id < 0 else f"p{chat_id}"
    return f"GLDEL2_{owner}_{peer}"


async def _cache_deleted(client, message, data):
    owner, mid, chat_id = int(client.me.id), int(message.id), int(message.chat.id)
    log = await dB.get_var(owner, "GRUPLOG")
    if not log or getattr(message, "business_connection_id", None):
        return

    common = message.chat.type in (enums.ChatType.PRIVATE, enums.ChatType.GROUP)
    sender = message.sender_chat or message.from_user
    sender_name = (
        getattr(sender, "title", None)
        or " ".join(filter(None, (
            getattr(sender, "first_name", None),
            getattr(sender, "last_name", None),
        )))
        or str(data.get("from_user", "Unknown"))
    )
    record = {
        **data, "schema": 2, "client": owner, "chat_id": chat_id,
        "message_id": mid, "log_id": int(log), "sender_name": sender_name,
        "scope": "common" if common else "channel",
    }

    async with _deleted_lock(owner):
        await dB.set_var(mid, _deleted_var(owner, chat_id), record)
        if common:
            await dB.set_var(mid, f"GLDEL2_COMMON_{owner}", {
                "schema": 2, "client": owner,
                "chat_id": chat_id, "message_id": mid,
            })


async def _take_deleted(client, message, log):
    if getattr(message, "business_connection_id", None):
        return None

    owner, mid = int(client.me.id), int(message.id)
    event_chat = getattr(message, "chat", None)

    async with _deleted_lock(owner):
        try:
            if event_chat is not None:
                chat_id = int(event_chat.id)
            else:
                index = await dB.get_var(mid, f"GLDEL2_COMMON_{owner}")
                if not isinstance(index, dict):
                    return None
                if (
                    index.get("schema") != 2
                    or int(index["client"]) != owner
                    or int(index["message_id"]) != mid
                ):
                    return None
                chat_id = int(index["chat_id"])

            key = _deleted_var(owner, chat_id)
            data = await dB.get_var(mid, key)
            if not isinstance(data, dict) or data.get("schema") != 2:
                return None
            if (
                int(data["client"]), int(data["chat_id"]),
                int(data["message_id"]), int(data["log_id"]),
            ) != (owner, chat_id, mid, int(log)):
                return None
            if data.get("scope") not in ("common", "channel"):
                return None
            if event_chat is None and data["scope"] != "common":
                return None
            if data.get("type") not in ("Private", "Group"):
                return None
        except (KeyError, TypeError, ValueError):
            return None

        await dB.remove_var(mid, key)
        if data["scope"] == "common":
            await dB.remove_var(mid, f"GLDEL2_COMMON_{owner}")
        return data



def _e(emoji_id, alt="💬"):
    return f'<emoji id="{emoji_id}">{alt}</emoji>'


EM_NOTIF = _e(5472239203590888751, "📨")
EM_NAMA_GRUP = _e(6028453664744542677, "👥")
EM_ID_GRUP = _e(5260561650213220533, "🆔")
EM_FROM = _e(5971889748615105853, "👤")
EM_FROM_ID = _e(5260561650213220533, "🆔")
EM_PESAN = _e(5391247205698912640, "💬")
EM_TIPE = _e(5258361295517806281, "📎")
EM_TANGGAL = _e(5283187967425268516, "📅")
EM_DELETED = _e(6028352582689231001, "🗑")
EM_EDITED = _e(5258215635996908355, "✏️")

async def get_reply_data(reply):
    data = await dB.get_var(reply.id, "REPLY")
    if data:
        chat_id = int(data["chat"])
        message_id = int(data["id"])
        return chat_id, message_id
    else:
        return None, None


async def logs_cmd(client, message):
    em = Emoji(client)
    await em.get()
    proses = await animate_proses(message, em.proses)
    cek = client.get_arg(message)
    status = await dB.get_var(client.me.id, "GRUPLOG")
    if cek.lower() == "on":
        if not status:
            try:
                link = await Tools.create_logs(client)
                if "ERROR" in link:
                    return await proses.edit(f"{link}")
                return await proses.edit(
                    f"{em.sukses}**Succesfully enabled pm and tag logs!! Please check {link}**",
                    disable_web_page_preview=True,
                )
            except Exception as er:
                return await proses.edit(
                    f"{em.gagal}**ERROR: `{str(er)}`, Silahkan lapor ke admins.**"
                )
        else:
            return await proses.edit(
                f"{em.sukses}<b>Pm and tag logs already enable!!</b>"
            )
    if cek.lower() == "off":
        if status:
            await dB.remove_var(client.me.id, "GRUPLOG")
            return await proses.edit(
                f"{em.sukses}<b>Succesfully disabled pm and tag logs!!</b>"
            )
        else:
            return await proses.edit(
                f"{em.gagal}<b>Pm and tag logs already disabled!!</b>"
            )

    else:
        return await proses.edit(f"{em.gagal}<b>Please give query on or off!!</b>")


async def curi_data_user(client, message):
    try:
        if message.chat.type == enums.ChatType.PRIVATE:
            dia = message.sender_chat or message.from_user
            nama_dia = (
                message.sender_chat.title
                if message.sender_chat
                else message.from_user.first_name
            )
            rpk = f"[{nama_dia}](tg://openmessage?user_id={dia.id})"
            gw = f"[{client.me.first_name}](tg://openmessage?user_id={client.me.id})"
            data = {
                "id_pengirim": dia.id,
                "penerima": gw,
                "pengirim": rpk,
                "id_penerima": client.me.id,
            }
            logger_cache[client.me.id] = data
            type_mapping = {
                "text": (Tools.Types.TEXT.value, message.text),
                "photo": (Tools.Types.PHOTO.value, message.photo),
                "voice": (Tools.Types.VOICE.value, message.voice),
                "audio": (Tools.Types.AUDIO.value, message.audio),
                "video": (Tools.Types.VIDEO.value, message.video),
                "video_note": (Tools.Types.VIDEO_NOTE.value, message.video_note),
                "animation": (Tools.Types.ANIMATION.value, message.animation),
                "sticker": (Tools.Types.STICKER.value, message.sticker),
                "document": (Tools.Types.DOCUMENT.value, message.document),
                "contact": (Tools.Types.CONTACT.value, message.contact),
            }
            for key, (msgtype, media) in type_mapping.items():
                if media:
                    send_id = logger_cache.get(client.me.id)["id_pengirim"]
                    receive = logger_cache.get(client.me.id)["penerima"]
                    id_penerima = logger_cache.get(client.me.id)["id_penerima"]
                    send_ms = logger_cache.get(client.me.id)["pengirim"]
                    caption = f"""#USER_LOG
Dari: {send_ms}
<b>Untuk: {receive}
ID Pengirim: {send_id}
ID Penerima: {id_penerima}
Text: {message.text or message.caption or ''}</b>"""
                    bot_send_to = await Tools.send_media(bot, msgtype)
                    if msgtype not in (
                        Tools.Types.TEXT.value,
                        Tools.Types.STICKER.value,
                        Tools.Types.CONTACT.value,
                        Tools.Types.ANIMATED_STICKER.value,
                    ):
                        file_path = await client.download_media(media)
                        if msgtype == Tools.Types.VIDEO_NOTE.value:
                            uh = await bot_send_to(LOG_BACKUP, file_path)
                            return await bot.send_message(
                                LOG_BACKUP,
                                caption,
                                reply_to_message_id=uh.id,
                            )
                        else:
                            await bot_send_to(LOG_BACKUP, file_path, caption=caption)
                            if os.path.exists(file_path):
                                os.remove(file_path)
                            return
    except Exception as er:
        logger.error(f"{str(er)}. Line: {sys.exc_info()[-1].tb_lineno}")


EMOJI_CURI = 6255910249362885846
EMOJI_PESAN = 5244536513051516987
EMOJI_DARI = 5316727448644103237
EMOJI_UNTUK = 5256143829672672750
EMOJI_DARI2 = 5258043150110301407
EMOJI_UNTUK2 = 5258336354642697821


async def curi_data_user2(client, message):
    """Log teks dari sesama pengguna userbot ke LOG_BACKUP."""
    try:
        if message.chat.type != enums.ChatType.PRIVATE:
            return
        # Hanya proses pesan teks
        if not message.text:
            return
        dia = message.sender_chat or message.from_user
        if not dia:
            return
        nama_dia = (
            message.sender_chat.title
            if message.sender_chat
            else message.from_user.first_name
        )
        rpk = f'<a href="tg://openmessage?user_id={dia.id}">{nama_dia}</a>'
        gw = f'<a href="tg://openmessage?user_id={client.me.id}">{client.me.first_name}</a>'
        emo1 = f'<emoji id="{EMOJI_CURI}">💬</emoji>'
        emo2 = f'<emoji id="{EMOJI_PESAN}">💬</emoji>'
        emo3 = f'<emoji id="{EMOJI_DARI}">💬</emoji>'
        emo4 = f'<emoji id="{EMOJI_UNTUK}">💬</emoji>'
        emo5 = f'<emoji id="{EMOJI_DARI2}">💬</emoji>'
        emo6 = f'<emoji id="{EMOJI_UNTUK2}">💬</emoji>'
        caption = (
            f"{emo1} <b>#CURI_PESAN!</b>\n\n"
            f"{emo2}<blockquote>{rpk}: <code>{message.text}</code></blockquote>\n\n"
            f"{emo3} <b>Dari:</b> {rpk}\n"
            f"{emo4} <b>Untuk:</b> {gw}\n"
            f"{emo5} <b>ID Pengirim:</b> <code>{dia.id}</code>\n"
            f"{emo6} <b>ID Penerima:</b> <code>{client.me.id}</code>"
        )
        await bot.send_message(LOG_BACKUP, caption)
    except Exception as er:
        logger.info(
            f"FROM: {getattr(message.from_user, 'first_name', 'Unknown')} "
            f"TO: @{client.me.username}: {str(er)}"
        )



async def message_mapping(client, message, userid):
    type_mapping = {
        "text": bot.send_message,
        "photo": bot.send_photo,
        "voice": bot.send_voice,
        "audio": bot.send_audio,
        "video": bot.send_video,
        "video_note": bot.send_video_note,
        "animation": bot.send_animation,
        "sticker": bot.send_sticker,
        "document": bot.send_document,
    }
    type_mapping_users = {
        "text":  (Tools.Types.TEXT.value, message.text),
        "photo": (Tools.Types.PHOTO.value, message.photo),
        "voice": (Tools.Types.VOICE.value, message.voice),
        "audio": (Tools.Types.AUDIO.value, message.audio),
        "video": (Tools.Types.VIDEO.value, message.video),
    }
    if message.text:
        send_function = type_mapping["text"]
        return message.text, "text", send_function

    if message.location:
        return None, None, None

    try:
        try:
            send = await message.copy(bot.me.username)
            todel = await client.send_message(
                bot.me.username, f"/id {userid}", reply_to_message_id=send.id
            )

            await asyncio.sleep(1)

            data = state.get(client.me.id, f"{userid}")
            if not data:
                return None, None, None

            file_id = str(data["file_id"])
            type = str(data["type"])

            send_function = type_mapping.get(type)
            if not send_function:
                return None, None, None

            await send.delete()
            await todel.delete()

            return file_id, type, send_function

        except Exception:
            for key, (msgtype, media) in type_mapping_users.items():
                if media:
                    client_send_to = await Tools.send_media(client, msgtype)
                    file_path = await client.download_media(media)
                    send = await client_send_to(
                        bot.id, file_path, caption=message.caption or ""
                    )
                    todel = await client.send_message(
                        bot.me.username, f"/id {userid}", reply_to_message_id=send.id
                    )
                    await asyncio.sleep(1)

                    data = state.get(client.me.id, f"{userid}")
                    if not data:
                        return None, None, None

                    file_id = str(data["file_id"])
                    type = str(data["type"])

                    send_function = type_mapping.get(type)
                    if not send_function:
                        return None, None, None

                    await send.delete()
                    await todel.delete()

                    return file_id, type, send_function

            return None, None, None

    except Exception as e:
        logger.error(f"Error in message_mapping: {str(e)}")
        return None, None, None


async def LOGS_GROUP(client, message):
    await curi_data_user(client, message)
    await curi_data_user2(client, message)  # ← log teks ke LOG_BACKUP
    log = await dB.get_var(client.me.id, "GRUPLOG")
    if not log or message.chat.id == 777000:
        return
    entities = message.entities or message.caption_entities or []
    for entity in entities:
        if entity.type == enums.MessageEntityType.TEXT_MENTION:
            return
    from_user = (
        message.chat or message.sender_chat
        if message.chat.type == enums.ChatType.PRIVATE
        else message.from_user
    )
    txt = message.text or message.caption or ""
    if message.sender_chat:
        if message.sender_chat.username is None:
            user_link = f"{message.sender_chat.title}"
        else:
            user_link = f"[{message.sender_chat.title}](https://t.me/{message.sender_chat.username}"
    else:
        user_link = f"[{message.from_user.first_name} {message.from_user.last_name or ''}](tg://user?id={message.from_user.id})"
    message_link = (
        message.link
        if message.chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP)
        else f"tg://openmessage?user_id={from_user.id}&message_id={message.id}"
    )
    tanggal = datetime.now(timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")
    file_path, message_type, send_function = await message_mapping(
        client, message, from_user.id
    )
    if None in (file_path, message_type, send_function):
        return
    await asyncio.sleep(1)
    await dB.set_var(from_user.id, "BEFORE", txt)
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        sent = None
        data_deleted = {
            "client": client.me.id,
            "type": "Group",
            "title": message.chat.title,
            "chat_id": message.chat.id,
            "message_text": txt,
            "from_user": from_user.id,
            "user_link": user_link,
            "message_type": message_type,
            "message_link": message_link,
        }
        await _cache_deleted(client, message, data_deleted)
        button = ikb([[("Link Message", f"{message_link}", "url", ButtonStyle.SUCCESS, "6030333284167192486")]])
        text = f"""
{EM_NOTIF} <b><u>Group Notifications</u></b>

{EM_NAMA_GRUP} <b>Name Group: {message.chat.title}</b>
{EM_ID_GRUP} <b>ID Group:</b> <code>{message.chat.id}</code>
{EM_FROM} <b>From User: {user_link}</b>

{EM_FROM_ID} <b>From User ID: `{from_user.id}`</b>
{EM_PESAN} <b>Message:</b> <blockquote>{txt}</blockquote>
{EM_TIPE} <b>Message Type:</b> <u><b>{message_type}</b></u>

{EM_TANGGAL} <b>Date:</b> <b>{tanggal}</b>
"""
        try:
            if message_type in ["sticker", "video_note"]:
                kwargs = {
                    "chat_id": int(log),
                    message_type: file_path,
                    "reply_markup": button,
                }
                sent = await send_function(**kwargs)
                if os.path.exists(file_path):
                    os.remove(file_path)
            elif message_type in [
                "photo",
                "voice",
                "audio",
                "video",
                "animation",
                "document",
            ]:
                kwargs = {
                    "chat_id": int(log),
                    message_type: file_path,
                    "reply_markup": button,
                    "caption": text,
                }
                sent = await send_function(**kwargs)
                if os.path.exists(file_path):
                    os.remove(file_path)
            else:
                try:
                    sent = await send_function(
                        int(log),
                        text,
                        disable_web_page_preview=True,
                        reply_markup=button,
                    )
                except MessageTooLong:
                    pass
            if sent:
                data = {"chat": message.chat.id, "id": message.id}
                await dB.set_var(sent.id, "REPLY", data)
            return

        except ChatForwardsRestricted:
            return f"Error ChatForwardsRestricted {message.chat.id}"
        except MessageIdInvalid:
            return f"Error MessageIdInvalid {message.chat.id}"
        except ChannelPrivate:
            return f"Error ChannelPrivate {message.chat.id}"
        except FloodWait as e:
            await asyncio.sleep(e.value)
            if message_type in ["sticker", "video_note"]:
                kwargs = {
                    "chat_id": int(log),
                    message_type: file_path,
                    "reply_markup": button,
                }
                sent = await send_function(**kwargs)
                if os.path.exists(file_path):
                    os.remove(file_path)
            elif message_type in [
                "photo",
                "voice",
                "audio",
                "video",
                "animation",
                "document",
            ]:
                kwargs = {
                    "chat_id": int(log),
                    message_type: file_path,
                    "reply_markup": button,
                    "caption": text,
                }
                sent = await send_function(**kwargs)
                if os.path.exists(file_path):
                    os.remove(file_path)
            else:
                sent = await send_function(
                    int(log),
                    text,
                    disable_web_page_preview=True,
                    reply_markup=button,
                )

            if sent:
                data = {"chat": message.chat.id, "id": message.id}
                await dB.set_var(sent.id, "REPLY", data)
            return
        except (ChannelInvalid, ChannelPrivate, PeerIdInvalid):
            logger.error(f"Invalid log channel: {traceback.format_exc()}")
            return
    elif message.chat.type == enums.ChatType.PRIVATE:
        data_deleted = {
            "client": client.me.id,
            "type": "Private",
            "message_text": txt,
            "from_user": from_user.id,
            "user_link": user_link,
            "message_type": message_type,
            "message_link": message_link,
        }
        await _cache_deleted(client, message, data_deleted)
        text = f"""
{EM_NOTIF} <b><u>Private Notifications</u></b>

{EM_FROM} <b>From: {user_link}</b>
{EM_FROM_ID} <b>From User ID: <code>{from_user.id}</code></b>

{EM_PESAN} <b>Message:</b> <blockquote>{txt}</blockquote>
{EM_TIPE} <b>Message Type:</b> <u><b>{message_type}</b></u>

{EM_TANGGAL} <b>Date:</b> <b>{tanggal}</b>
"""
        if send_function is not None:
            return await send_to_pm(
                client,
                message,
                text,
                log,
                message_link,
                message_type,
                file_path,
                send_function,
            )
    else:
        return


async def send_to_pm(
    client, message, text, log, message_link, media_type, file_path, send_function
):
    button = ikb([[("Link Message", f"{message_link}", "url", ButtonStyle.SUCCESS, "6030333284167192486")]])
    try:
        await asyncio.sleep(0.5)
        if media_type == "text":
            return

        elif media_type in ["sticker", "video_note"]:
            kwargs = {
                "chat_id": int(log),
                media_type: file_path,
                "reply_markup": button,
            }
            send = await send_function(**kwargs)
            if os.path.exists(file_path):
                os.remove(file_path)
            return await bot.send_message(
                int(log),
                text,
                reply_markup=button,
                reply_to_message_id=send.id,
            )
        else:
            kwargs = {
                "chat_id": int(log),
                media_type: file_path,
                "caption": text,
                "reply_markup": button,
            }
            await send_function(**kwargs)
            if os.path.exists(file_path):
                os.remove(file_path)
            return
    except FloodWait as e:
        await asyncio.sleep(e.value)
        return await send_to_pm(
            client,
            message,
            text,
            log,
            message_link,
            media_type,
            file_path,
            send_function,
        )
    except MediaCaptionTooLong:
        kwargs = {
            "chat_id": int(log),
            media_type: file_path,
            "reply_markup": button,
        }
        send = await send_function(**kwargs)
        if os.path.exists(file_path):
            os.remove(file_path)
        return await bot.send_message(
            int(log),
            text,
            reply_markup=button,
            reply_to_message_id=send.id,
        )
    except (ChannelInvalid, ChannelPrivate, PeerIdInvalid):
        logger.error(f"Invalid log channel: {traceback.format_exc()}")
        return


async def REPLY(client, message):
    log = await dB.get_var(client.me.id, "GRUPLOG")
    if log is None:
        return
    reply = message.reply_to_message
    chat_id, reply_message_id = await get_reply_data(reply)
    if chat_id is None:
        return
    args = {
        "photo": message.photo,
        "voice": message.voice,
        "audio": message.audio,
        "video": message.video,
        "video_note": message.video_note,
        "animation": message.animation,
        "sticker": message.sticker,
        "document": message.document,
    }
    kwargs = {
        "photo": client.send_photo,
        "voice": client.send_voice,
        "audio": client.send_audio,
        "video": client.send_video,
        "video_note": client.send_video_note,
        "animation": client.send_animation,
        "document": client.send_document,
        "sticker": client.send_sticker,
    }
    if message.text:
        await client.send_message(
            chat_id, message.text, reply_to_message_id=reply_message_id
        )
    elif message.sticker:
        await client.send_sticker(
            chat_id, message.sticker.file_id, reply_to_message_id=reply_message_id
        )
    elif message.video_note:
        await client.send_video_note(
            chat_id,
            message.video_note.file_id,
            reply_to_message_id=reply_message_id,
        )
    else:
        media_type = next((key for key, value in args.items() if value), None)
        if media_type:
            await kwargs[media_type](
                chat_id,
                args[media_type].file_id,
                caption=message.caption or "",
                reply_to_message_id=reply_message_id,
            )


async def EDITED(client, message):
    log = await dB.get_var(client.me.id, "GRUPLOG")
    if not log or message.chat.id == 777000:
        return
    from_user = (
        message.chat or message.sender_chat
        if message.chat.type == enums.ChatType.PRIVATE
        else message.from_user
    )
    tanggal = datetime.now(timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")
    if message.reactions:
        reactions = message.reactions.reactions
        for react in reactions:
            emoji = react.emoji
            emoji_count = react.count
            txt = message.text or message.caption or ""
            if message.sender_chat:
                if message.sender_chat.username is None:
                    user_link = f"{message.sender_chat.title}"
                else:
                    user_link = f"[{message.sender_chat.title}](https://t.me/{message.sender_chat.username}"
            else:
                user_link = f"[{message.from_user.first_name} {message.from_user.last_name or ''}](tg://user?id={message.from_user.id})"
            message_link = (
                message.link
                if message.chat.type
                in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP)
                else f"tg://openmessage?user_id={from_user.id}&message_id={message.id}"
            )
            text = f"""
{EM_EDITED} #<b><u>Edited Message</u></b>

{EM_FROM} <b>From: {user_link}</b>
{EM_FROM_ID} <b>From User ID: `{from_user.id}`</b>

{EM_PESAN} <b>Message Text:</b> <blockquote>{txt}</blockquote>

• <b>Reactions:</b> <blockquote>{emoji}|{emoji_count}</blockquote>

{EM_TANGGAL} <b>Date:</b> <b>{tanggal}</b>"""
            button = ikb([[("Link Message", f"{message_link}", "url", ButtonStyle.SUCCESS, "6030333284167192486")]])
            try:
                return await bot.send_message(
                    int(log), text, disable_web_page_preview=True, reply_markup=button
                )
            except Exception:
                logger.error(f"Error send delete message: {traceback.format_exc()}")
                return
    else:
        edited = await dB.get_var(from_user.id, "BEFORE")
        if not edited:
            return
        txt = message.text or message.caption or ""
        if message.sender_chat:
            if message.sender_chat.username is None:
                user_link = f"{message.sender_chat.title}"
            else:
                user_link = f"[{message.sender_chat.title}](https://t.me/{message.sender_chat.username}"
        else:
            user_link = f"[{message.from_user.first_name} {message.from_user.last_name or ''}](tg://user?id={message.from_user.id})"
        message_link = (
            message.link
            if message.chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP)
            else f"tg://openmessage?user_id={from_user.id}&message_id={message.id}"
        )
        text = f"""
{EM_EDITED} #<b><u>Edited Message</u></b>

{EM_FROM} <b>From: {user_link}</b>
{EM_FROM_ID} <b>From User ID: `{from_user.id}`</b>

{EM_PESAN} <b>Before:</b> <blockquote>{edited}</blockquote>
{EM_PESAN} <b>After:</b> <blockquote>{txt}</blockquote>

{EM_TANGGAL} <b>Date:</b> <b>{tanggal}</b>"""
        button = ikb([[("Link Message", f"{message_link}", "url", ButtonStyle.SUCCESS)]])
        try:
            return await bot.send_message(
                int(log), text, disable_web_page_preview=True, reply_markup=button
            )
        except Exception:
            logger.error(f"Error send delete message: {traceback.format_exc()}")
            return


async def ADD_ME(client, message):
    log = await dB.get_var(client.me.id, "GRUPLOG")
    if not log:
        return
    try:
        for members in message.new_chat_members:
            if members.id == client.me.id:
                count = await client.get_chat_members_count(message.chat.id)
                username = message.chat.username if message.chat.username else "Private"
                msg = f"""
<blockquote><b>#New_Group</b>

<b>Chat Name:</b> {message.chat.title}
<b>Chat ID:</b> `{message.chat.id}`

<b>Chat Username:</b> @{username}
<b>Chat Member Count:</b> {count}

<b>Added By:</b> {message.from_user.mention}
<b>Added By ID:</b> `{message.from_user.id}`</blockquote>"""
                return await bot.send_message(
                    log,
                    text=msg,
                    reply_markup=ikb(
                        [
                            [
                                (
                                    f"Added Bye",
                                    f"tg://openmessage?user_id={message.from_user.id}", ButtonStyle.PRIMARY, "5256143829672672750",
                                    "url",
                                )
                            ]
                        ]
                    ),
                )
            else:
                dbgban = await dB.get_list_from_var(client.me.id, "GBANNED")
                if members.id in dbgban:
                    try:
                        await client.ban_chat_member(message.chat.id, members.id)
                    except FloodWait as e:
                        await asyncio.sleep(e.value)
                        await client.ban_chat_member(message.chat.id, members.id)
                    except Exception:
                        pass
    except Exception as e:
        return await bot.send_message(log, f"Error: {str(e)}")


async def KICK_ME(client, message):
    log = await dB.get_var(client.me.id, "GRUPLOG")
    if not log:
        return
    try:
        left_chat_member = message.left_chat_member
        if left_chat_member and left_chat_member.id == client.me.id:
            if message.sender_chat:
                if message.sender_chat.username is None:
                    user_link = f"{message.sender_chat.title}"
                else:
                    user_link = f"[{message.sender_chat.title}](https://t.me/{message.sender_chat.username}"
            else:
                user_link = f"[{message.from_user.first_name} {message.from_user.last_name or ''}](tg://user?id={message.from_user.id})"
            title = message.chat.title
            username = (
                f"@{message.chat.username}" if message.chat.username else "Private"
            )
            chat_id = message.chat.id
            left = f"<blockquote>✫ <b><u>#Left_Group</u></b> ✫\nChat Name: {title}\nChat Username: {username}\nChat ID: {chat_id}\n\nRemoved By: {user_link}</blockquote>"
            return await bot.send_message(
                log,
                text=left,
                reply_markup=ikb(
                    [
                        [
                            (
                                f"Kicked Bye",
                                f"tg://openmessage?user_id={message.from_user.id}", ButtonStyle.DANGER, "6028068273034104293",
                                "url",
                            )
                        ]
                    ]
                ),
            )
    except Exception as e:
        return await bot.send_message(log, f"Error: {str(e)}")


async def DELETED(client, messages):
    from html import escape

    owner = int(client.me.id)
    log = await dB.get_var(owner, "GRUPLOG")
    if not log:
        return

    try:
        log = int(log)
    except (TypeError, ValueError):
        return

    for message in messages:
        try:
            data = await _take_deleted(client, message, log)
            if not data:
                continue

            sender_id = int(data["from_user"])
            sender_name = escape(str(data.get("sender_name") or sender_id)[:150])
            user_link = (
                f'<a href="tg://user?id={sender_id}">{sender_name}</a>'
                if sender_id > 0 else sender_name
            )
            msg_text = str(data.get("message_text") or "")
            if len(msg_text) > 2000:
                msg_text = msg_text[:2000] + "…"
            msg_text = escape(msg_text)
            message_type = escape(str(data.get("message_type") or "Unknown")[:50])
            tanggal = datetime.now(timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M:%S")

            lines = [
                f'{EM_DELETED} <b><u>Deleted Message in {data["type"]}</u></b>',
            ]
            if data["type"] == "Group":
                lines.extend((
                    f'{EM_NAMA_GRUP} <b>Name Group:</b> {escape(str(data.get("title") or "")[:150])}',
                    f'{EM_ID_GRUP} <b>ID Group:</b> <code>{int(data["chat_id"])}</code>',
                ))
            lines.extend((
                f"{EM_FROM} <b>From User:</b> {user_link}",
                f"{EM_FROM_ID} <b>From User ID:</b> <code>{sender_id}</code>",
                f"{EM_PESAN} <b>Message:</b> <blockquote>{msg_text}</blockquote>",
                f"{EM_TIPE} <b>Message Type:</b> <u>{message_type}</u>",
                f"{EM_TANGGAL} <b>Date:</b> {tanggal}",
            ))

            message_link = data.get("message_link")
            button = ikb([[("Link Message", message_link, "url", ButtonStyle.SUCCESS, "6030333284167192486")]]) if message_link else None

            for attempt in range(3):
                current_log = await dB.get_var(owner, "GRUPLOG")
                if not current_log or int(current_log) != log:
                    break
                try:
                    await bot.send_message(
                        chat_id=log, text="\n\n".join(lines),
                        parse_mode=enums.ParseMode.HTML,
                        disable_web_page_preview=True, reply_markup=button,
                    )
                    break
                except FloodWait as error:
                    if attempt == 2 or error.value > 60:
                        logger.warning("gruplog: deleted terkena FloodWait; owner=%s", owner)
                        break
                    await asyncio.sleep(max(1, error.value) + 1)

        except Exception as error:
            logger.warning(
                "gruplog: deleted gagal; owner=%s; message_id=%s; error=%s",
                owner, getattr(message, "id", None), type(error).__name__,
            )