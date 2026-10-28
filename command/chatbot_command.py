import random

from pyrogram import enums

import config
from database import dB, state
from helpers import Tools


async def add_auto_text(message):
    data = message.reply_to_message or message
    auto_text = await dB.get_var(config.BOT_ID, "CHATBOT_TEXT") or []
    auto_text.append(data.text)
    await dB.set_var(config.BOT_ID, "CHATBOT_TEXT", auto_text)


async def get_random_text():
    entries = await dB.get_var(config.BOT_ID, "CHATBOT_TEXT") or []
    return [e for e in entries]


async def get_chat_history(client, chat_id, user_id):
    key = f"chat_history_{chat_id}_{user_id}"
    return state.get(client, key) or []


async def add_to_chat_history(client, chat_id, user_id, role, message):
    key = f"chat_history_{chat_id}_{user_id}"
    history = await get_chat_history(client, chat_id, user_id)
    history.append({"role": role, "content": message})
    history = history[-500:]
    state.set(client, key, history)


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
    res = await Tools.fetch.post(url, json=payload)

    if res.status_code == 200:
        result = res.json().get("result")
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
                title = (await client.get_chat(chat)).title
                ids = (await client.get_chat(chat)).id
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
    if message.chat.id not in await dB.get_list_from_var(client.me.id, "CHATBOT"):
        return
    text = message.text or message.caption
    if text:
        if message.reply_to_message:
            if message.reply_to_message.from_user.id == client.me.id:
                await client.send_chat_action(
                    chat_id=message.chat.id, action=enums.ChatAction.TYPING
                )
                data = await gen_text(client, message)
                if data is not None:
                    await message.reply(data)
                else:
                    data = await get_random_text()
                    await message.reply(random.choice(data))
                await client.send_chat_action(
                    chat_id=message.chat.id, action=enums.ChatAction.CANCEL
                )
