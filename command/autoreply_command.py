import asyncio
from collections import OrderedDict
from time import monotonic

from pyrogram.errors import FloodWait

from clients import alice
from database import dB

AUTOREPLY_CACHE_TTL = 30
AUTOREPLY_COOLDOWN = 3
AUTOREPLY_MAX_ACTIVE = 16
AUTOREPLY_CACHE_LIMIT = 256
AUTOREPLY_RECENT_LIMIT = 4096

_autoreply_cache = OrderedDict()
_autoreply_recent = OrderedDict()
_autoreply_busy = set()
_autoreply_cache_lock = asyncio.Lock()


async def _get_autoreply_chats(user_id):
    version = getattr(dB, "_vars_ver", {}).get(user_id, 0)
    entry = _autoreply_cache.get(user_id)
    if entry and entry[0] == version and monotonic() - entry[1] < AUTOREPLY_CACHE_TTL:
        _autoreply_cache.move_to_end(user_id)
        return entry[2]

    async with _autoreply_cache_lock:
        version = getattr(dB, "_vars_ver", {}).get(user_id, 0)
        entry = _autoreply_cache.get(user_id)
        if entry and entry[0] == version and monotonic() - entry[1] < AUTOREPLY_CACHE_TTL:
            _autoreply_cache.move_to_end(user_id)
            return entry[2]

        chats = frozenset(await dB.get_list_from_var(user_id, "MENTIONED") or [])
        if getattr(dB, "_vars_ver", {}).get(user_id, 0) == version:
            _autoreply_cache[user_id] = (version, monotonic(), chats)
            _autoreply_cache.move_to_end(user_id)
            while len(_autoreply_cache) > AUTOREPLY_CACHE_LIMIT:
                _autoreply_cache.popitem(last=False)
        return chats


def _set_autoreply_cooldown(key, seconds):
    _autoreply_recent[key] = monotonic() + seconds
    _autoreply_recent.move_to_end(key)
    while len(_autoreply_recent) > AUTOREPLY_RECENT_LIMIT:
        _autoreply_recent.popitem(last=False)


async def autoreply_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply(
            f"<b>Please usage command: `{message.text.split()} on` for turned on autoreply, `{message.text.split()} off` for turned off autoreply, and `{message.text.split()} status` to check the status in which groups this feature is active.</b>"
        )
    if message.command[1] == "on":
        await dB.add_to_var(client.me.id, "MENTIONED", message.chat.id)
        _autoreply_cache.pop(client.me.id, None)
        return await message.reply("<b>Auto reply turned on.</b>")
    elif message.command[1] == "off":
        if len(message.command) < 3:
            chat_id = message.chat.id
            if chat_id not in await dB.get_list_from_var(client.me.id, "MENTIONED"):
                return await message.reply(f"**`{chat_id}` is not found!**")
            await dB.remove_from_var(client.me.id, "MENTIONED", chat_id)
            _autoreply_cache.pop(client.me.id, None)
            name = (await client.get_chat(chat_id)).title
            return await message.reply(f"<b>Turned off autoreply for chat: {name}</b>")
        else:
            if message.command[2] == "all":
                for A in await dB.get_list_from_var(client.me.id, "MENTIONED"):
                    await dB.remove_from_var(client.me.id, "MENTIONED", A)
                    _autoreply_cache.pop(client.me.id, None)
                return await message.reply(
                    f"<b>Successfully delete all lists chat autoreply!</b>"
                )
            else:
                if len(message.command) < 3:
                    return await message.reply(
                        f"<b>Please user command `{message.text.split()} off -100434249243279`</b>"
                    )
                chat_id = message.command[2]
                try:
                    chat_id = int(chat_id)
                except ValueError:
                    return await message.reply(
                        f"**Please give a valid chat_id.Error `{chat_id}`!**"
                    )
                if chat_id not in await dB.get_list_from_var(client.me.id, "MENTIONED"):
                    return await message.reply(f"`{chat_id}` **Not found!**")
                await dB.remove_from_var(client.me.id, "MENTIONED", chat_id)
                _autoreply_cache.pop(client.me.id, None)
                name = (await client.get_chat(chat_id)).title
                return await message.reply(
                    f"<b>Turned off autoreply for chat: {name}</b>"
                )
    elif message.command[1] == "status":
        chats = await dB.get_list_from_var(client.me.id, "MENTIONED")
        if not chats:
            return await message.reply(
                "<b>You don't have any active group lists yet.</b>"
            )
        msg = ""
        for num, chat in enumerate(chats, 1):
            try:
                info = await client.get_chat(chat)
                title = info.title
                ids = info.id
            except Exception:
                continue
            msg += f"<b>{num}. {title} | `{ids}`</b>"
        return await message.reply(msg)
    else:
        return await message.reply(
            f"<b>Please usage command: `{message.text.split()} on` for turned on autoreply, `{message.text.split()} off` for turned off autoreply, and `{message.text.split()} status` to check the status in which groups this feature is active.</b>"
        )


async def mentioned_trigger(client, message):
    user = message.from_user
    if not user or user.is_bot or user.is_self:
        return
    if user.id in alice._get_my_id:
        return

    reply = message.reply_to_message
    is_reply = bool(
        reply and reply.from_user and reply.from_user.id == client.me.id
    )
    username = client.me.username
    is_mention = bool(
        username and (
            username in (message.text or "")
            or username in (message.caption or "")
        )
    )
    if not is_reply and not is_mention:
        return
    if not any((
        message.text, message.photo, message.video, message.sticker,
        message.document, message.audio, message.voice, message.location,
        message.video_note if not is_reply else None,
    )):
        return

    key = (client.me.id, message.chat.id, user.id)
    if key in _autoreply_busy or len(_autoreply_busy) >= AUTOREPLY_MAX_ACTIVE:
        return
    if monotonic() < _autoreply_recent.get(key, 0):
        return

    _autoreply_busy.add(key)
    try:
        if message.chat.id not in await _get_autoreply_chats(client.me.id):
            return
        _set_autoreply_cooldown(key, AUTOREPLY_COOLDOWN)

        if is_reply:
            if message.text:
                await message.reply(message.text)
            elif message.photo:
                await message.reply_photo(
                    message.photo.file_id, caption=message.caption or None
                )
            elif message.video:
                await message.reply_video(
                    message.video.file_id, caption=message.caption or None
                )
            elif message.sticker:
                await message.reply_sticker(message.sticker.file_id)
            elif message.document:
                await message.reply_document(
                    message.document.file_id, caption=message.caption or None
                )
            elif message.audio:
                await message.reply_audio(
                    message.audio.file_id, caption=message.caption or None
                )
            elif message.voice:
                await message.reply_voice(message.voice.file_id)
            elif message.location:
                await message.reply_location(
                    longitude=message.location.longitude,
                    latitude=message.location.latitude,
                )
        elif is_mention:
            mention = user.mention()
            caption_text = (message.caption or "").replace(username, mention)
            if message.text:
                await message.reply(f"{mention}")
            elif message.photo:
                await message.reply_photo(
                    message.photo.file_id, caption=caption_text
                )
            elif message.video:
                await message.reply_video(
                    message.video.file_id, caption=caption_text
                )
            elif message.document:
                await message.reply_document(
                    message.document.file_id, caption=caption_text
                )
            elif message.sticker:
                await message.reply_sticker(message.sticker.file_id)
            elif message.video_note:
                await message.reply_video_note(message.video_note.file_id)
            elif message.audio:
                await message.reply_audio(
                    message.audio.file_id, caption=caption_text
                )
            elif message.voice:
                await message.reply_voice(
                    message.voice.file_id, caption=caption_text
                )
            elif message.location:
                await message.reply_location(
                    longitude=message.location.longitude,
                    latitude=message.location.latitude,
                )
    except FloodWait as e:
        _set_autoreply_cooldown(key, max(AUTOREPLY_COOLDOWN, e.value))
    finally:
        _autoreply_busy.discard(key)