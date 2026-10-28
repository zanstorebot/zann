import asyncio
import traceback
from uuid import uuid4

from pyrogram.enums import ChatType, ParseMode

from clients import bot
from config import BOT_NAME, SUDO_OWNERS
from database import dB, state
from helpers import ButtonUtils, Emoji, animate_proses
from logs import logger

flood = {}
flood2 = {}

DEFAULT_TEXT = "Hey {mention} 👋. Jangan Spam Ini Auto Protect Chat"
PM_WARN = "You've got {}/{} warnings !!"
LIMIT = 5
INLINE_WARN = """<blockquote><b>{}

You've got {}/{} warnings !!</b></blockquote>"""


async def pmpermit_cmd(client, message):
    em = Emoji(client)
    await em.get()
    proses = await animate_proses(message, em.proses)
    try:
        command, variable = message.command[:2]
    except ValueError:
        return await proses.delete()
    value = " ".join(message.command[2:])
    rep = message.reply_to_message
    if variable.lower() == "set":
        akt = ["on", "true"]
        mti = ["off", "false"]
        if value.lower() in akt:
            stat = await dB.get_var(client.me.id, "PMPERMIT")
            if stat:
                return await proses.edit(f"<blockquote></b>{em.sukses}Auto Protect Sudah Diaktifkan</b></blockquote>")
            else:
                await dB.set_var(client.me.id, "PMPERMIT", value)
                return await proses.edit(f"<blockquote>{em.sukses}**Auto Protect On.**</blockquote>")
        elif value.lower() in mti:
            stat = await dB.get_var(client.me.id, "PMPERMIT")
            if stat:
                await dB.remove_var(client.me.id, "PMPERMIT")
                return await proses.edit(f"<blockquote>{em.gagal}**Auto Protect Off.**</blockquote>")
            else:
                return await proses.edit(f"<blockquote>{em.gagal}**Auto Protect Sudah Dimatikan.**</blockquote>")
        else:
            return await proses.edit(f"{em.gagal}**Auto Protect `on` or `off`.**")
    elif variable.lower() == "media":
        if value.lower() == "off":
            await dB.remove_var(client.me.id, "PMMEDIA")
            return await proses.edit(f"{em.sukses}**PMPermit media disabled.**")
        if not rep or not rep.media:
            return await proses.edit(f"{em.gagal}**Please reply to media**")
        copy = await rep.copy(bot.me.username)
        sent = await client.send_message(
            bot.me.username, f"/id PMMEDIA", reply_to_message_id=copy.id
        )
        await asyncio.sleep(1)
        await sent.delete()
        await copy.delete()
        file_id = state.get(client.me.id, "PMMEDIA").get("file_id")
        type = state.get(client.me.id, "PMMEDIA").get("type")
        media = {"type": type, "file_id": file_id}
        await dB.set_var(client.me.id, "PMMEDIA", media)
        return await proses.edit(
            f"{em.sukses}**PMPermit media set to: [this media]({rep.link})",
            disable_web_page_preview=True,
        )

    elif variable.lower() == "teks":
        if value.lower() == "reset":
            await dB.remove_var(client.me.id, "PMTEXT")
            return await proses.edit(
                f"{em.sukses}**PMPermit text has been reset to default.**"
            )
        if message.reply_to_message:
            pice = client.new_arg(message)
        else:
            pice = value
        await dB.set_var(client.me.id, "PMTEXT", pice)
        return await proses.edit(f"{em.sukses}**PMPermit text set to: {pice}.**")
    elif variable.lower() == "warn":
        if value.lower() == "reset":
            await dB.remove_var(client.me.id, "PMLIMIT")
            return await proses.edit(
                f"{em.sukses}**PMPermit warn has been reset to default.**"
            )
        if not message.reply_to_message:
            pice = value
        else:
            pice = rep.text
        if not pice.isnumeric():
            return await proses.edit(f"{em.gagal}**Please give warn type numeric.**")
        await dB.set_var(client.me.id, "PMLIMIT", pice)
        return await proses.edit(f"{em.sukses}**PMPermit warn set to: {pice}.**")
    elif variable.lower() == "disapproved":
        if value.lower() == "all":
            pm_ok = await dB.get_list_from_var(client.me.id, "PM_OKE")
            for user in pm_ok:
                await dB.remove_from_var(client.me.id, "PM_OKE", user)
            return await proses.edit(
                f"{em.sukses}**Succesfully deleted all users in approved database.**"
            )
        else:
            try:
                user = (await client.get_users(value)).id
            except Exception:
                return await proses.edit(f"{em.gagal}**Please give me valid user!!**")
            await dB.remove_from_var(client.me.id, "PM_OKE", user)
            return await proses.edit(
                f"{em.sukses}**Succesfully deleted {user} in approved database.**"
            )
    elif variable.lower() == "get":
        if value.lower() == "teks":
            txt = await dB.get_var(client.me.id, "PMTEXT")
            pmtext = txt if txt else DEFAULT_TEXT
            await message.reply(
                f"**PMPermit text:**\n\n`{pmtext}`",
                disable_web_page_preview=True,
                parse_mode=ParseMode.DISABLED,
            )
            return await proses.delete()
        elif value.lower() == "warn":
            lmt = await dB.get_var(client.me.id, "PMLIMIT")
            lmt if lmt else LIMIT
            return await proses.edit(f"{em.sukses}**PMPermit warn: `{lmt}`.**")
        elif value.lower() == "media":
            pick = await dB.get_var(client.me.id, "PMMEDIA")
            if pick:
                return await proses.edit(f"{em.sukses}**PMPermit media: `{pick}`**")
            else:
                return await proses.edit(
                    f"{em.gagal}**PMPermit media already disable.**"
                )
        elif value.lower() == "status":
            sts = await dB.get_var(client.me.id, "PMPERMIT")
            if sts:
                return await proses.edit(f"{em.sukses}**PMPermit status:** `{sts}`")
            else:
                return await proses.edit(f"{em.gagal}**PMPermit already disable.**")
        elif value.lower() == "approved":
            pm_ok = await dB.get_list_from_var(client.me.id, "PM_OKE")
            if not pm_ok:
                return await proses.edit(f"{em.gagal}**Not users yet!!**")
            msg = ""
            for count, user in enumerate(pm_ok, 1):
                try:
                    dia = await client.get_users(user)
                    full = f"<a href=tg://user?id={dia.id}>{dia.first_name} {dia.last_name or ''}</a>"
                except Exception:
                    full = user
                msg += f"{count}. {full}\n"
            return await proses.edit(msg)
        else:
            return await proses.edit(
                f"{em.gagal}**Query not found, please read help!**"
            )
    else:
        return await proses.edit(f"{em.gagal}**Query not found, please read help!**")


async def okpm_cmd(client, message):
    em = Emoji(client)
    await em.get()
    pm_ok = await dB.get_list_from_var(client.me.id, "PM_OKE")
    chat_type = message.chat.type
    if chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        if message.reply_to_message:
            dia = message.reply_to_message.from_user.id
        else:
            return await message.delete()
    elif chat_type == ChatType.PRIVATE:
        dia = message.chat.id
    else:
        return await message.delete()
    proses = await animate_proses(message, em.proses)
    getc_pm_warns = await dB.get_var(client.me.id, "PMLIMIT")
    custom_pm_warns = getc_pm_warns if getc_pm_warns else LIMIT
    if dia in pm_ok:
        return await proses.edit(f"{em.sukses}**User already approved.**")
    try:
        async for uh in client.get_chat_history(dia, limit=int(custom_pm_warns)):
            if uh.reply_markup:
                await uh.delete()
                try:
                    del flood[str(dia)]
                    state.delete(client.me.id, dia)
                except KeyError:
                    pass
            else:
                try:
                    await client.delete_messages(dia, message_ids=flood[dia])
                    del flood[str(dia)]
                    state.delete(client.me.id, dia)
                except KeyError:
                    pass
    except Exception:
        logger.error(f"ERROR: {traceback.format_exc()}")
    await dB.add_to_var(client.me.id, "PM_OKE", dia)
    await proses.edit(f"{em.sukses}**User approved to send message.**")
    await asyncio.sleep(0.5)
    return await proses.delete()


async def nopm_cmd(client, message):
    em = Emoji(client)
    await em.get()
    pm_ok = await dB.get_list_from_var(client.me.id, "PM_OKE")
    proses = await animate_proses(message, em.proses)
    chat_type = message.chat.type
    if chat_type in [ChatType.GROUP, ChatType.SUPERGROUP]:
        if message.reply_to_message:
            user_id = message.reply_to_message.from_user.id
        else:
            return await message.delete()
    elif chat_type == ChatType.PRIVATE:
        user_id = message.chat.id
    else:
        return await message.delete()

    if user_id not in pm_ok:
        return await proses.edit(
            f"{em.gagal}**User already disapproved to send message**"
        )
    await dB.remove_from_var(client.me.id, "PM_OKE", user_id)
    await proses.edit(f"{em.sukses}**User disapproved to send message**")
    await asyncio.sleep(0.5)
    return await proses.delete()


async def PMPERMIT(client, message):
    em = Emoji(client)
    await em.get()
    gw = client.me.id
    dia = message.from_user

    pm_oke = await dB.get_list_from_var(client.me.id, "PM_OKE")
    ong = await dB.get_var(gw, "PMPERMIT")
    if not ong or dia.id in pm_oke:
        return
    if dia.is_fake or dia.is_scam:
        return await client.block_user(dia.id)
    if dia.is_support or dia.is_verified or dia.is_self or dia.is_contact:
        return
    if dia.id in SUDO_OWNERS:
        try:
            await client.send_message(
                dia.id,
                f"<b>Approved {dia.mention} has Owner {BOT_NAME}!!</b>",
                parse_mode=ParseMode.HTML,
            )
            await dB.add_to_var(client.me.id, "PM_OKE", dia.id)
        except BaseException:
            pass
        return
    pmtok = await dB.get_var(gw, "PMTEXT")
    pmtok if pmtok else DEFAULT_TEXT
    pm_warns = await dB.get_var(gw, "PMLIMIT") or LIMIT
    async for aks in client.get_chat_history(dia.id, limit=int(pm_warns)):
        if aks.reply_markup:
            await aks.delete()
    if str(dia.id) in flood:
        flood[str(dia.id)] += 1
    else:
        flood[str(dia.id)] = 1
    if flood[str(dia.id)] > int(pm_warns):
        del flood[str(dia.id)]
        await message.reply_text(
            f"{em.sukses}**SPAM DETECTED, {em.block}BLOCKED USER AUTOMATICALLY!**"
        )
        return await client.block_user(dia.id)
    state.set(gw, dia.id, flood[str(dia.id)])
    full = f"<a href=tg://user?id={dia.id}>{dia.first_name} {dia.last_name or ''}</a>"
    await dB.add_userdata(
        dia.id, dia.first_name, dia.last_name, dia.username, dia.mention, full, dia.id
    )
    try:
        uniq = f"{str(uuid4())}"
        state.set(uniq.split("-")[0], f"idm_{dia.id}", id(message))
        query = f"pmpermit_inline {uniq.split('-')[0]} {dia.id}"
        await ButtonUtils.send_inline_bot_result(
            message, dia.id, bot.me.username, query
        )
    except Exception:
        logger.error(f"PMPermit Inline: {traceback.format_exc()}")


async def AUTO_APPROVE(client, message):
    if not await dB.get_var(client.me.id, "PMPERMIT"):
        return
    pm_ok = await dB.get_list_from_var(client.me.id, "PM_OKE")
    pm_warns = await dB.get_var(client.me.id, "PMLIMIT") or LIMIT
    if message.chat.id not in pm_ok:
        if message.chat.type == ChatType.BOT:
            return
        try:
            async for uh in client.get_chat_history(
                message.chat.id, limit=int(pm_warns)
            ):
                if uh.reply_markup:
                    await uh.delete()
                    try:
                        del flood[str(message.chat.id)]
                        state.delete(client.me.id, message.chat.id)
                    except KeyError:
                        pass
                else:
                    try:
                        del flood[str(message.chat.id)]
                        state.delete(client.me.id, message.chat.id)
                    except KeyError:
                        pass
        except Exception:
            logger.error(f"ERROR: {traceback.format_exc()}")
        return await dB.add_to_var(client.me.id, "PM_OKE", message.chat.id)
