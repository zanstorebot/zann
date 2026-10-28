import asyncio
import importlib

from pyrogram.helpers import kb

from clients import UserBot, bot, alice
from config import BOT_NAME
from database import dB
from helpers import Emoji
from plugins import PLUGINS

keyboard = kb([["↩️ Beranda"]], resize_keyboard=True, one_time_keyboard=True)
DEFAULT_PREFIX = [".", ",", "?", "+", "!"]


async def reset_costum_text(client, message):
    user_id = message.from_user.id
    proses = await message.reply("<b>Processing...</b>")
    if user_id not in alice._get_my_id:
        return await proses.edit(
            f"<b>You are not user @{bot.me.username}!!</b>", reply_markup=keyboard
        )
    try:
        await dB.set_var(user_id, "text_ping", "Ping")
        await dB.set_var(user_id, "text_uptime", "Uptime")
        owner_name = f"<a href=tg://user?id={message.from_user.id}>{message.from_user.first_name} {message.from_user.last_name or ''}</a>"
        await dB.set_var(user_id, "text_owner", f"Owner: {owner_name}")
        await dB.set_var(user_id, "text_ubot", f"{BOT_NAME}")
        await dB.set_var(user_id, "text_gcast", "Proses")
        await dB.set_var(user_id, "text_sukses", "Gcast Sukses")
        await asyncio.sleep(1)
        return await proses.edit(
            "<b>Your costum text has been reset</b>", reply_markup=keyboard
        )
    except Exception as er:
        return await proses.edit(f"<b>ERROR: `{str(er)}`</b>", reply_markup=keyboard)


async def reset_emoji(client, message):
    user_id = message.from_user.id
    proses = await message.reply("<b>Processing...</b>")
    if user_id not in alice._get_my_id:
        return await proses.edit(
            f"<b>You are not user @{bot.me.username}!!</b>", reply_markup=keyboard
        )
    for User in alice._ubot:
        if user_id == User.me.id:
            try:
                em = Emoji(User)
                await em.reset_emoji()
                await asyncio.sleep(1)
                return await proses.edit(
                    "<b>Your costum emoji has been reset.!!</b>", reply_markup=keyboard
                )
            except Exception as er:
                return await proses.edit(
                    f"<b>ERROR: `{str(er)}`</b>", reply_markup=keyboard
                )


async def reset_prefix(client, message):
    proses = await message.reply("<b>Processing...</b>")
    user_id = message.from_user.id
    if user_id not in alice._get_my_id:
        return await proses.edit(
            f"<b>You are not user @{bot.me.username}!!</b>", reply_markup=keyboard
        )
    ubot = next((x for x in alice._ubot if x.me.id == user_id), None)
    if ubot is None:
        return await proses.edit(
            "<b>Userbot kamu belum aktif, coba /restart dulu.</b>",
            reply_markup=keyboard,
        )
    try:
        await dB.set_pref(user_id, DEFAULT_PREFIX)
        ubot.set_prefix(user_id, DEFAULT_PREFIX)
    except Exception as er:
        return await proses.edit(f"<b>ERROR: `{str(er)}`</b>", reply_markup=keyboard)
    return await proses.edit(
        f"<b>Your prefix has been reset to: `{' '.join(DEFAULT_PREFIX)}` .</b>",
        reply_markup=keyboard,
    )


async def restart_userbot(client, message):
    proses = await message.reply("<b>Processing...</b>")
    user_id = message.from_user.id
    get_id = next(
        (X for X in await dB.get_userbots() if user_id == int(X["name"])), None
    )
    if get_id is None:
        return await proses.edit(
            f"<b>You are not user @{bot.me.username}!!</b>", reply_markup=keyboard
        )
    try:
        ubot = UserBot(**get_id)
        alice._get_my_id.remove(user_id)
        await ubot.start()
        for modul in PLUGINS:
            importlib.reload(importlib.import_module(f"plugins.{modul}"))
        return await proses.edit(
            f"<b>✅ Userbot has been restarted {ubot.me.first_name} {ubot.me.last_name or ''} | {ubot.me.id}.</b>",
            reply_markup=keyboard,
        )
    except Exception as error:
        await dB.remove_ubot(user_id)
        return await proses.edit(f"<b>{error}</b>", reply_markup=keyboard)