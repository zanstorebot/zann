import asyncio
import random
from collections import OrderedDict
from time import monotonic

from pyrogram import enums

import config
from clients import alice
from database import dB
from helpers import Tools
from logs import logger

HISTORY_LIMIT = 24
HISTORY_MAX_CHATS = 256
HISTORY_TTL = 3600
CHATBOT_MAX_ACTIVE = 3
CHATBOT_COOLDOWN = 3
CHATBOT_TIMEOUT = 45

_chat_history = OrderedDict()
_chatbot_busy = set()
_chatbot_recent = OrderedDict()


def _history_key(client, chat_id, user_id):
    return client, chat_id, user_id


def _prune_history():
    now = monotonic()
    while _chat_history:
        key = next(iter(_chat_history))
        timestamp, _ = _chat_history[key]
        if now - timestamp < HISTORY_TTL:
            break
        _chat_history.popitem(last=False)

    while len(_chat_history) > HISTORY_MAX_CHATS:
        _chat_history.popitem(last=False)


async def add_auto_text(message):
    data = message.reply_to_message or message
    if not data.text:
        return
    auto_text = await dB.get_var(config.BOT_ID, "CHATBOT_TEXT") or []
    auto_text.append(data.text)
    await dB.set_var(config.BOT_ID, "CHATBOT_TEXT", auto_text)


async def get_random_text():
    entries = await dB.get_var(config.BOT_ID, "CHATBOT_TEXT") or []
    return [entry for entry in entries if isinstance(entry, str) and entry.strip()]


async def get_chat_history(client, chat_id, user_id):
    _prune_history()
    key = _history_key(client, chat_id, user_id)
    entry = _chat_history.get(key)
    if entry is None:
        return []
    _, history = entry
    _chat_history[key] = (monotonic(), history)
    _chat_history.move_to_end(key)
    return list(history)


async def add_to_chat_history(client, chat_id, user_id, role, message):
    if not isinstance(message, str) or not message.strip():
        return
    key = _history_key(client, chat_id, user_id)
    history = await get_chat_history(client, chat_id, user_id)
    history.append({"role": role, "content": message})
    _chat_history[key] = (monotonic(), history[-HISTORY_LIMIT:])
    _chat_history.move_to_end(key)
    _prune_history()


async def gen_text(client, message):
    text = message.text or message.caption
    user_id = message.from_user.id
    chat_id = message.chat.id

    role_default = f"lu adalah karakter bernama {client.me.first_name}. lu asik orang nya dan cool..."
    role = await dB.get_var(client.me.id, "ROLE_CHATBOT") or role_default
    history = await get_chat_history(client.me.id, chat_id, user_id)

    messages = [{"role": "system", "content": role}] + history
    messages.append({"role": "user", "content": text})

    url = "https://api.botcahx.eu.org/api/search/openai-custom-v2"
    payload = {"message": messages, "apikey": f"{config.API_BOTCHAX}"}
    res = await asyncio.wait_for(
        Tools.fetch.post(url, json=payload), timeout=CHATBOT_TIMEOUT
    )

    if res.status_code == 200:
        result = res.json().get("result")
        if not isinstance(result, str) or not result.strip():
            return None
        await add_to_chat_history(client.me.id, chat_id, user_id, "user", text)
        await add_to_chat_history(client.me.id, chat_id, user_id, "assistant", result)
        return result
    else:
        return None


async def chatbot_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply(
            f"<b>Please usage command: `{message.text.split()[0]} on` for turned on chatbot, `{message.text.split()[0]} off` for turned off chatbot, and `{message.text.split()[0]} status` to check the status in which groups this feature is active.</b>"
        )
    if message.command[1] == "on":
        await dB.add_to_var(client.me.id, "CHATBOT", message.chat.id)
        return await message.reply("<b>Chatbot turned on.</b>")
    elif message.command[1] == "off":
        if len(message.command) < 3:
            chat_id = message.chat.id
            if chat_id not in await dB.get_list_from_var(client.me.id, "CHATBOT"):
                return await message.reply(f"**`{chat_id}` is not found!**")
            await dB.remove_from_var(client.me.id, "CHATBOT", chat_id)
            name = (await client.get_chat(chat_id)).title
            return await message.reply(f"<b>Turned off chatbot for chat: {name}</b>")
        else:
            if message.command[2] == "all":
                for A in await dB.get_list_from_var(client.me.id, "CHATBOT"):
                    await dB.remove_from_var(client.me.id, "CHATBOT", A)
                return await message.reply(
                    f"<b>Successfully delete all lists chat chatbot!</b>"
                )
            else:
                if len(message.command) < 3:
                    return await message.reply(
                        f"<b>Please use command `{message.text.split()[0]} off -100434249243279`</b>"
                    )
                chat_id = message.command[2]
                try:
                    chat_id = int(chat_id)
                except ValueError:
                    return await message.reply(
                        f"**Please give a valid chat_id.Error `{chat_id}`!**"
                    )
                if chat_id not in await dB.get_list_from_var(client.me.id, "CHATBOT"):
                    return await message.reply(f"`{chat_id}` **Not found!**")
                await dB.remove_from_var(client.me.id, "CHATBOT", chat_id)
                name = (await client.get_chat(chat_id)).title
                return await message.reply(
                    f"<b>Turned off chatbot for chat: {name}</b>"
                )
    elif message.command[1] == "status":
        chats = await dB.get_list_from_var(client.me.id, "CHATBOT")
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
    elif message.command[1] == "role":
        if not message.reply_to_message:
            return await message.reply(
                f"<b>Please use command `{message.text.split()[0]} role lu adalah karakter cewe bernama nisa, sikap lu ngeselin lucu dan imut dan lu ga gampang baper`</b>"
            )
        role = message.reply_to_message.text or message.reply_to_message.caption
        await dB.set_var(client.me.id, "ROLE_CHATBOT", role)
        return await message.reply(f"<b>Role chatbot set to: `{role}`.</b>")

    else:
        return await message.reply(
            f"<b>Please usage command: `{message.text.split()[0]} on` for turned on chatbot, `{message.text.split()[0]} off` for turned off chatbot, and `{message.text.split()[0]} status` to check the status in which groups this feature is active.</b>"
        )


async def chatbot_trigger(client, message):
    user = message.from_user
    reply = message.reply_to_message
    text = message.text or message.caption

    if not text or not user or user.is_bot or user.is_self:
        return
    if user.id in alice._get_my_id:
        return
    if not reply or not reply.from_user:
        return
    if reply.from_user.id != client.me.id:
        return

    key = _history_key(client.me.id, message.chat.id, user.id)
    now = monotonic()
    if key in _chatbot_busy or len(_chatbot_busy) >= CHATBOT_MAX_ACTIVE:
        return
    if now - _chatbot_recent.get(key, float("-inf")) < CHATBOT_COOLDOWN:
        return

    _chatbot_busy.add(key)
    _chatbot_recent[key] = now
    _chatbot_recent.move_to_end(key)
    while len(_chatbot_recent) > HISTORY_MAX_CHATS:
        _chatbot_recent.popitem(last=False)

    typing = False
    try:
        chats = await dB.get_list_from_var(client.me.id, "CHATBOT") or []
        if message.chat.id not in chats:
            return

        try:
            await client.send_chat_action(
                chat_id=message.chat.id, action=enums.ChatAction.TYPING
            )
            typing = True
        except Exception:
            pass

        try:
            data = await gen_text(client, message)
        except asyncio.TimeoutError:
            logger.warning(f"Chatbot timeout: {client.me.id}/{message.chat.id}")
            data = None
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(f"Chatbot request gagal: {client.me.id}/{message.chat.id}")
            data = None

        if data is None:
            entries = await get_random_text()
            if not entries:
                return
            data = random.choice(entries)

        await message.reply(data)
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.exception(f"Chatbot handler gagal: {client.me.id}/{message.chat.id}")
    finally:
        _chatbot_busy.discard(key)
        if typing:
            try:
                await asyncio.wait_for(
                    client.send_chat_action(
                        chat_id=message.chat.id, action=enums.ChatAction.CANCEL
                    ),
                    timeout=3,
                )
            except Exception:
                pass