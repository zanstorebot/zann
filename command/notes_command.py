import asyncio
import io
import traceback
from html import escape
from uuid import uuid4

from pyrogram import enums
from pyrogram.enums import ParseMode
from pyrogram.types import ReplyParameters

from clients import bot
from database import dB, state
from helpers import ButtonUtils, Emoji, Message, Tools, animate_proses
from helpers.note_rich import (MEDIA_KINDS, REF_FORMATS, buttons_html,
                               has_rich_markup, make_rich, only_url_rows,
                               render_note)
from logs import logger


def _pick_user(message):
    """Siapa yang jadi {mention}/{name}: yang direply > lawan chat private > pengirim."""
    rep = message.reply_to_message
    if rep and rep.from_user:
        return rep.from_user
    if message.chat.type == enums.ChatType.PRIVATE:
        return message.chat
    return message.from_user


async def _send_rich(client, chat_id, rich, reply_id):
    kw = {"reply_parameters": ReplyParameters(message_id=reply_id)} if reply_id else {}
    return await client.send_rich_message(chat_id=chat_id, rich_message=rich, **kw)


async def _userbot_file_id(client, mtype, file_id):
    """file_id tersimpan milik bot -> file_id yang bisa dipakai akun userbot."""
    cache_key = f"ubfid_{file_id}"
    if cached := state.get(client.me.id, cache_key):
        return cached
    new_id = await _convert_file_id(client, mtype, file_id)
    if new_id:
        state.set(client.me.id, cache_key, new_id)
    return new_id


async def _convert_file_id(client, mtype, file_id):
    send = getattr(bot, f"send_{mtype}", None)
    if not send:
        return None
    try:
        sent = await send(client.me.id, file_id)
        new_id = None
        async for media in client.search_messages(bot.username, limit=1):
            obj = getattr(media, mtype, None)
            new_id = getattr(obj, "file_id", None)
        await bot.delete_messages(client.me.id, sent.id)
        return new_id
    except Exception:
        logger.error(f"_userbot_file_id gagal: {traceback.format_exc()}")
        return None


async def send_rich_note(client, message, note, data):
    try:
        text = data["result"].get("text") or ""
        mtype = data["type"]
        kind = mtype if mtype in MEDIA_KINDS else None
        if mtype != "text" and not kind:
            return False  # sticker/voice/dokumen dll -> jalur lama

        rendered = render_note(text, _pick_user(message))
        for warn in rendered.warnings:
            logger.warning(f"note {note}: {warn}")
        rows, reply_id = rendered.rows, Message.ReplyCheck(message)

        if rows and not only_url_rows(rows):
            uniq = uuid4().hex[:8]
            state.set(client.me.id, f"rich_note_{uniq}", {
                "html": rendered.html,
                "text": text,
                "kind": kind,
                "file_id": data.get("file_id") or None,  # file_id milik bot
            })
            state.set(client.me.id, "in_notes", id(message))
            query = f"get_note {uniq} {note}"
            ok = await ButtonUtils.send_inline_bot_result(
                message, message.chat.id, bot.me.username, query,
                reply_to_message_id=reply_id,
            )
            if ok:
                # dipakai cb_notes: userbot yang mengedit -> emoji premium tetap
                sent = state.get(client.me.id, query) or {}
                state.set(client.me.id, f"note_msg_{uniq}",
                          {"chat": sent.get("chat"), "id": sent.get("_id"),
                           "reply": reply_id, "query": query})
            return ok

        html = rendered.html + (buttons_html(rows) if rows else "")
        file_id = None
        if kind:
            file_id = await _userbot_file_id(client, mtype, data.get("file_id", ""))
            if not file_id:
                return False

        for fmt in REF_FORMATS if kind else REF_FORMATS[:1]:
            try:
                rich = make_rich(html, kind, file_id, fmt)
                await _send_rich(client, message.chat.id, rich, reply_id)
                return True
            except Exception:
                logger.error(f"rich note [{fmt}] gagal: {traceback.format_exc()}")
        return False
    except Exception:
        logger.error(f"send_rich_note gagal: {traceback.format_exc()}")
        return False


async def savenote_cmd(client, message):
    em = Emoji(client)
    await em.get()

    xx = await animate_proses(message, em.proses)
    rep = message.reply_to_message
    if len(message.command) < 2 or not rep:
        return await xx.edit(f"{em.gagal}**Please reply message and give note name**")
    nama = message.text.split()[1]
    getnotes = await dB.get_var(client.me.id, nama, "notes")
    if getnotes:
        return await xx.edit(f"{em.gagal}**Note {nama} already exist!**")
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
        await dB.set_var(client.me.id, nama, value, "notes")
        return await xx.edit(f"{em.sukses}**Saved {nama} note!!**")
    else:
        return await xx.edit(f"{em.gagal}**Please reply message and give note name**")


async def getnote_cmd(client, message):
    em = Emoji(client)
    await em.get()

    xx = await animate_proses(message, em.proses)

    try:
        if len(message.text.split()) == 2:
            note = message.text.split()[1]
            data = await dB.get_var(client.me.id, note, "notes")
            if not data:
                return await xx.edit(f"{em.gagal}**Note {note} not found!**")
            return await getnotes_(client, message, xx, note, data)
        elif len(message.text.split()) == 3 and (message.text.split())[2] in [
            "noformat",
            "raw",
        ]:
            note = message.text.split()[1]
            data = await dB.get_var(client.me.id, note, "notes")
            if not data:
                return await xx.edit(f"{em.gagal}**Note {note} not found!**")
            return await get_raw_note(client, message, xx, note, data)
        else:
            return await xx.edit(f"{em.gagal}**Please give note name!**")
    except Exception as e:
        return await xx.edit(f"{em.gagal}**ERROR**: {str(e)}")


async def getnotes_(client, message, xx, note, data):
    em = Emoji(client)
    await em.get()
    thetext = data["result"].get("text")

    # note rich (teks atau media): tabel/divider/emoji premium/tombol bergaya
    if has_rich_markup(thetext or ""):
        if await send_rich_note(client, message, note, data):
            return await xx.delete()

    uniq = str(uuid4())
    _, button = ButtonUtils.parse_msg_buttons(thetext)

    if button:
        state.set(client.me.id, "in_notes", id(message))
        try:
            inline = await ButtonUtils.send_inline_bot_result(
                message,
                message.chat.id,
                bot.me.username,
                f"get_note {uniq.split('-')[0]} {note}",
                reply_to_message_id=Message.ReplyCheck(message),
            )
            if inline:
                return await xx.delete()
        except Exception as e:
            return await xx.edit(f"{em.gagal}**ERROR:** {str(e)}")
    else:
        type = data["type"]
        file_id = data["file_id"]

        if type == "text":
            entities = [
                Tools.convert_entity(ent) for ent in data["result"].get("entities", [])
            ]
            await message.reply(
                data["result"].get("text"),
                entities=entities,
                reply_to_message_id=Message.ReplyCheck(message),
            )
            return await xx.delete()
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
                didel = await pre_senders[type](client.me.id, file_id)
                async for media in client.search_messages(bot.username, limit=1):
                    media_obj = getattr(media, file_attrs[type], None)
                    new_fileid = (
                        getattr(media_obj, "file_id", None) if media_obj else None
                    )
                    break
                else:
                    new_fileid = None

                if not new_fileid:
                    return await message.reply(f"{em.gagal}**Error!! data not found.**")
                await bot.delete_messages(bot.username, didel.id)
                kwargs = {"reply_to_message_id": Message.ReplyCheck(message)}
                if type not in ["sticker", "video_note"]:
                    kwargs["caption"] = data["result"].get("text")
                    kwargs["caption_entities"] = [
                        Tools.convert_entity(ent)
                        for ent in data["result"].get("entities", [])
                    ]

                await reply_senders[type](new_fileid, **kwargs)

            except Exception as e:
                await message.reply(f"{em.gagal}**Send failed:** `{e}`")

        return await xx.delete()


async def _send_note_media(client, message, mtype, file_id, reply_id):
    """Kirim media note tanpa caption. file_id milik bot -> bot kirim ke userbot, lalu di-copy."""
    send = getattr(bot, f"send_{mtype}", None)
    if not send:
        return
    sent = await send(client.me.id, file_id)
    try:
        async for media in client.search_messages(bot.id, limit=1):
            await media.copy(message.chat.id, reply_to_message_id=reply_id)
    finally:
        await sent.delete()


async def _send_raw_text(message, note, text, reply_id):
    """Teks mentah dalam blok <pre> (sekali tap salin); kepanjangan -> file .txt."""
    if len(text) <= 4000:
        return await message.reply(
            f"{escape(text)}",
            parse_mode=ParseMode.HTML,
            reply_to_message_id=reply_id,
        )
    doc = io.BytesIO(text.encode("utf-8"))
    doc.name = f"{note}.txt"
    return await message.reply_document(
        doc, caption=f"<b>Raw note:</b> <code>{escape(note)}</code>",
        reply_to_message_id=reply_id,
    )


async def get_raw_note(client, message, xx, note, data):
    """get <nama> raw : tampilkan media (kalau ada) + isi note apa adanya."""
    em = Emoji(client)
    await em.get()
    text = data["result"].get("text") or ""
    mtype, file_id = data["type"], data.get("file_id")
    reply_id = Message.ReplyCheck(message)
    try:
        if mtype != "text" and file_id:
            await _send_note_media(client, message, mtype, file_id, reply_id)
        if text:
            await _send_raw_text(message, note, text, reply_id)
        elif mtype == "text":
            return await xx.edit(f"{em.gagal}**Note {note} kosong!**")
        return await xx.delete()
    except Exception as e:
        logger.error(f"get_raw_note gagal: {traceback.format_exc()}")
        return await xx.edit(f"{em.gagal}**ERROR:** `{e}`")


async def listnotes_cmd(client, message):
    em = Emoji(client)
    await em.get()

    xx = await animate_proses(message, em.proses)
    getnotes = await dB.all_var(client.me.id, "notes")
    if not getnotes:
        return await xx.edit(f"{em.gagal}**You dont have any notes!**")
    rply = f"{em.msg}**List of Notes:**\n\n"
    for x, data in getnotes.items():
        type = await dB.get_var(client.me.id, x, "notes")
        rply += f"**• Name: `{x}` | Type: `{type['type']}`**\n"
    return await xx.edit(rply)


async def clearnotes_cmd(client, message):
    em = Emoji(client)
    await em.get()
    xx = await animate_proses(message, em.proses)
    raw_args = message.text.split(maxsplit=1)[1] if len(message.command) > 1 else ""
    names = [n for n in raw_args.replace(",", " ").split() if n]
    notes = await dB.all_var(client.me.id, "notes") or {}

    if not notes:
        return await xx.edit(f"{em.gagal}**You dont have any notes!**")
    if not names or names == ["all"]:
        for nama in list(notes):
            await dB.remove_var(client.me.id, nama, "notes")
        return await xx.edit(f"{em.sukses}**Successfully deleted {len(notes)} notes!**")

    sukses = [n for n in names if n in notes]
    gagal = [n for n in names if n not in notes]
    for nama in sukses:
        await dB.remove_var(client.me.id, nama, "notes")

    text = ""
    if sukses:
        text += f"{em.sukses}**Deleted:** `{', '.join(sukses)}`\n"
    if gagal:
        text += f"{em.gagal}**Not found:** `{', '.join(gagal)}`"
    return await xx.edit(text.strip())