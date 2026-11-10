import asyncio
import json
import re
import traceback
from collections import OrderedDict
from functools import lru_cache
from time import monotonic
from weakref import WeakKeyDictionary

from pyrogram.enums import ParseMode
from pyrogram.errors import FileReferenceExpired, FloodWait

from clients import alice, bot
from database import dB, state
from helpers import ButtonUtils, Emoji, Message, Tools, animate_proses
from logs import logger

FILTER_CACHE_TTL = 30
FILTER_CACHE_LIMIT = 256
FILTER_MEDIA_TTL = 300
FILTER_MEDIA_LIMIT = 512
FILTER_COOLDOWN = 2
FILTER_MAX_ACTIVE = 16
FILTER_RECENT_LIMIT = 4096

_filter_cache = OrderedDict()
_filter_media_cache = OrderedDict()
_filter_recent = OrderedDict()
_filter_busy = set()
_filter_cache_lock = asyncio.Lock()
_filter_media_locks = WeakKeyDictionary()

_MEDIA_SENDERS = {
    "photo": "send_photo", "voice": "send_voice", "audio": "send_audio",
    "video": "send_video", "animation": "send_animation",
    "document": "send_document", "sticker": "send_sticker",
    "video_note": "send_video_note",
}
_MEDIA_REPLIES = {
    "photo": "reply_photo", "voice": "reply_voice", "audio": "reply_audio",
    "video": "reply_video", "animation": "reply_animation",
    "document": "reply_document", "sticker": "reply_sticker",
    "video_note": "reply_video_note",
}


def _decode_filter(data):
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (TypeError, ValueError):
            return None
    return data if isinstance(data, dict) else None


@lru_cache(maxsize=2048)
def _filter_pattern(word):
    return re.compile(rf"\b{re.escape(word)}\b", flags=re.IGNORECASE)


async def _get_filter_data(user_id):
    version = getattr(dB, "_vars_ver", {}).get(user_id, 0)
    entry = _filter_cache.get(user_id)
    if entry and entry[0] == version and monotonic() - entry[1] < FILTER_CACHE_TTL:
        _filter_cache.move_to_end(user_id)
        return entry[2], entry[3]

    async with _filter_cache_lock:
        version = getattr(dB, "_vars_ver", {}).get(user_id, 0)
        entry = _filter_cache.get(user_id)
        if entry and entry[0] == version and monotonic() - entry[1] < FILTER_CACHE_TTL:
            _filter_cache.move_to_end(user_id)
            return entry[2], entry[3]

        entries = await dB.all_var(user_id, "filter") or {}
        filters = []
        for word, value in entries.items():
            data = _decode_filter(value)
            if word and data:
                filters.append((_filter_pattern(word), data))
        blacklist = frozenset(
            await dB.get_list_from_var(user_id, "BLACKLIST_GCAST") or []
        )
        filters = tuple(filters)
        if getattr(dB, "_vars_ver", {}).get(user_id, 0) == version:
            _filter_cache[user_id] = (
                version, monotonic(), filters, blacklist,
            )
            _filter_cache.move_to_end(user_id)
            while len(_filter_cache) > FILTER_CACHE_LIMIT:
                _filter_cache.popitem(last=False)
        return filters, blacklist


def _set_filter_cooldown(key, seconds):
    _filter_recent[key] = monotonic() + seconds
    _filter_recent.move_to_end(key)
    while len(_filter_recent) > FILTER_RECENT_LIMIT:
        _filter_recent.popitem(last=False)


async def _bridge_filter_media(client, data_type, file_id, **kwargs):
    sender = _MEDIA_SENDERS.get(data_type)
    if not sender:
        return None

    lock = _filter_media_locks.get(client)
    if lock is None:
        lock = asyncio.Lock()
        _filter_media_locks[client] = lock

    async with lock:
        sent = await getattr(bot, sender)(client.me.id, file_id, **kwargs)
        try:
            source = getattr(sent, data_type, None)
            unique_id = getattr(source, "file_unique_id", None)
            if not unique_id:
                return None

            async for media in client.search_messages(bot.me.username, limit=20):
                target = getattr(media, data_type, None)
                if (
                    target
                    and getattr(target, "file_unique_id", None) == unique_id
                ):
                    return media
            return None
        finally:
            try:
                await sent.delete()
            except Exception:
                pass


async def _get_filter_media_id(client, data_type, file_id):
    key = (client.me.id, data_type, file_id)
    entry = _filter_media_cache.get(key)
    if entry and monotonic() - entry[0] < FILTER_MEDIA_TTL:
        _filter_media_cache.move_to_end(key)
        return entry[1]

    _filter_media_cache.pop(key, None)
    media = await _bridge_filter_media(client, data_type, file_id)
    target = getattr(media, data_type, None) if media else None
    new_fileid = getattr(target, "file_id", None)
    if new_fileid:
        _filter_media_cache[key] = (monotonic(), new_fileid)
        _filter_media_cache.move_to_end(key)
        while len(_filter_media_cache) > FILTER_MEDIA_LIMIT:
            _filter_media_cache.popitem(last=False)
    return new_fileid


async def _reply_filter_media(client, message, data_type, file_id, **kwargs):
    sender = _MEDIA_REPLIES.get(data_type)
    if not sender:
        return

    key = (client.me.id, data_type, file_id)
    new_fileid = await _get_filter_media_id(client, data_type, file_id)
    if not new_fileid:
        return
    try:
        await getattr(message, sender)(new_fileid, **kwargs)
    except FileReferenceExpired:
        _filter_media_cache.pop(key, None)
        new_fileid = await _get_filter_media_id(client, data_type, file_id)
        if new_fileid:
            await getattr(message, sender)(new_fileid, **kwargs)


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
        sent = None
        try:
            sent = await client.send_message(
                bot.me.username, f"/id {nama}", reply_to_message_id=copy.id
            )
            await asyncio.sleep(1)
            extract = Tools.dump_entity(text, entities)
            type = state.get(client.me.id, nama)
            if not type:
                return await xx.edit(
                    f"{em.gagal}**Data media belum tersedia. Silakan coba lagi.**"
                )
            value = {
                "type": type["type"],
                "file_id": type["file_id"],
                "result": extract,
            }
        finally:
            for item in (sent, copy):
                if item:
                    try:
                        await item.delete()
                    except Exception:
                        pass
    else:
        extract = Tools.dump_entity(text, entities)
        value = {"type": "text", "file_id": "", "result": extract}
    if value:
        await dB.set_var(client.me.id, nama, value, "filter")
        _filter_cache.pop(client.me.id, None)
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
            elif type in (
                "photo", "voice", "audio", "video", "animation", "document",
            ):
                media = await _bridge_filter_media(
                    client, type, file_id,
                    caption=data["result"].get("text"),
                    parse_mode=ParseMode.DISABLED,
                )
                if media:
                    await media.copy(message.chat.id)
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
        type = _decode_filter(data)
        if type:
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
        getfilter = await dB.all_var(client.me.id, "filter")
        if not getfilter:
            return await xx.edit(f"{em.gagal}**You dont have any filter!**")
        for nama in getfilter:
            await dB.remove_var(client.me.id, nama, "filter")
            _filter_cache.pop(client.me.id, None)
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
                _filter_cache.pop(client.me.id, None)
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
    text = message.text
    if not text:
        return
    user = message.from_user
    if user and (
        user.is_bot or user.is_self or user.id in alice._get_my_id
    ):
        return
    sender = user or message.sender_chat
    if not sender:
        return

    key = (client.me.id, message.chat.id, sender.id)
    if key in _filter_busy or len(_filter_busy) >= FILTER_MAX_ACTIVE:
        return
    if monotonic() < _filter_recent.get(key, 0):
        return

    _filter_busy.add(key)
    try:
        getfilter, blacklist = await _get_filter_data(client.me.id)
        if not getfilter or message.chat.id in blacklist:
            return

        matched = False
        for index, (pattern, _filter) in enumerate(getfilter, 1):
            if index % 50 == 0:
                await asyncio.sleep(0)
            if not pattern.search(text):
                continue

            data_type = _filter.get("type")
            file_id = _filter.get("file_id")
            if data_type != "text" and (
                not file_id or data_type not in _MEDIA_REPLIES
            ):
                continue

            data = (_filter.get("result") or {}).get("text") or ""
            teks = await Tools.escape_filter(message, data, Tools.parse_words)
            if not matched:
                _set_filter_cooldown(key, FILTER_COOLDOWN)
                matched = True

            if data_type == "text":
                await message.reply(
                    teks,
                    disable_web_page_preview=True,
                    parse_mode=ParseMode.HTML,
                )
            else:
                kwargs = {"reply_to_message_id": message.id}
                if data_type not in ("sticker", "video_note"):
                    kwargs["caption"] = teks
                    kwargs["parse_mode"] = ParseMode.HTML
                await _reply_filter_media(
                    client, message, data_type, file_id, **kwargs
                )
    except FloodWait as e:
        _set_filter_cooldown(key, max(FILTER_COOLDOWN, e.value))
    except Exception:
        logger.error(
            f"Eror filter pada chat {message.chat.id}:\n{traceback.format_exc()}"
        )
    finally:
        _filter_busy.discard(key)