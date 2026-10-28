import asyncio
import os
import random
import traceback
from datetime import datetime
from io import BytesIO
from time import time

from pyrogram import enums, raw
from pyrogram.enums import ChatMemberStatus, ChatType, StoriesPrivacyRules
from pyrogram.errors import (ChannelPrivate, FloodWait, PeerIdInvalid,
                             UsernameOccupied, UserNotParticipant)
from pyrogram.raw import functions
from pyrogram.raw.functions import Ping

from config import HELPABLE
from clients import alice
from database import dB
from helpers import (Basic_Effect, Emoji, Premium_Effect, Tools,
                     animate_proses, get_time, start_time, task)
from logs import logger

RANDOM_EMOJIS = [
    "😀",
    "😂",
    "😍",
    "😎",
    "😢",
    "😡",
    "👍",
    "👎",
    "🙏",
    "👏",
    "❤️",
    "🗿",
    "😭",
    "🔥",
]


async def set_pong_message(user_id, new_message):
    await dB.set_var(user_id, "text_ping", new_message)
    return


async def set_utime_message(user_id, new_message):
    await dB.set_var(user_id, "text_uptime", new_message)
    return


async def set_owner_message(user_id, new_message):
    await dB.set_var(user_id, "text_owner", new_message)
    return


async def set_ubot_message(user_id, new_message):
    await dB.set_var(user_id, "text_ubot", new_message)
    return


async def set_gcast_message(user_id, new_message):
    await dB.set_var(user_id, "text_gcast", new_message)
    return


async def set_sukses_message(user_id, new_message):
    await dB.set_var(user_id, "text_sukses", new_message)
    return


async def set_help_message(user_id, new_message):
    await dB.set_var(user_id, "text_help", new_message)
    return

costumtext_query = {
    "ping": set_pong_message,
    "uptime": set_utime_message,
    "owner": set_owner_message,
    "ubot": set_ubot_message,
    "proses": set_gcast_message,
    "sukses": set_sukses_message,
    "help": set_help_message,
}

async def react_all(client, message, emoji):
    target_id = (
        message.reply_to_message.id
        if message.reply_to_message
        else message.id
    )

    for ubot in alice._ubot:
        try:
            await ubot.send_reaction(
                chat_id=message.chat.id,
                message_id=target_id,
                emoji=emoji,
            )
        except Exception:
            continue


async def batu_ku(client, message):
    await react_all(client, message, "🗿")


async def love_ku(client, message):
    await react_all(client, message, "❤️")


async def nangis_ku(client, message):
    await react_all(client, message, "😭")


async def crot_ku(client, message):
    await react_all(client, message, "💦")
  

async def blocked_cmd(client, message):
    em = Emoji(client)
    await em.get()
    proses = await animate_proses(message, em.proses)
    if message.command[0] == "blocked":
        users = await client.invoke(
            raw.functions.contacts.GetBlocked(offset=0, limit=2000)
        )
        total = len([t.peer_id.user_id for t in users.blocked])
        return await proses.edit(f"{em.sukses}**Users as bloked is `{total}`.**")
    elif message.command[0] == "unblockall":
        sukses = 0
        users = await client.invoke(
            raw.functions.contacts.GetBlocked(offset=0, limit=2000)
        )
        total = [t.peer_id.user_id for t in users.blocked]
        for target in total:
            try:
                await client.unblock_user(target)
                sukses += 1
            except Exception:
                continue
        return await proses.edit(
            f"{em.gagal}**Successfully unblocked a total of `{sukses}` users out of {len(total)} users.**"
        )


async def settext_cmd(client, message):
    em = Emoji(client)
    await em.get()
    pong_, uptime_, owner_, ubot_, proses_, sukses_ = await em.get_costum_text()
    pros = await animate_proses(message, em.proses)

    args = message.text.split(maxsplit=2)
    variable = args[1]
    new_message = client.new_arg(message)
    if variable in costumtext_query:
        await costumtext_query[variable](client.me.id, new_message)
        return await pros.edit(
            f"{em.sukses}**Successfully updated custom text: <u>{variable}</u>**"
        )
    else:
        return await pros.edit(
            f"{em.gagal}**Please given text for this query: {variable}!**"
        )


async def mping_cmd(client, message):
    em = Emoji(client)
    await em.get()
    pong_, uptime_, owner_, ubot_, proses_, sukses_ = await em.get_costum_text()
    start = datetime.now()
    await client.invoke(Ping(ping_id=0))
    end = datetime.now()
    upnya = await get_time((time() - start_time))
    duration = round((end - start).microseconds / 100000, 2)
    _ping = f"<b>{em.ping}{pong_}:</b> <u>{duration}ms</u>\n<b>{em.uptime}{uptime_}:</b> <u>{upnya}</u>\n<b>{em.owner}{owner_}</b>"
    if message._client.me.is_premium == True:
        effect_id = random.choice(Premium_Effect)
    else:
        effect_id = random.choice(Basic_Effect)
    if message.chat.type == enums.ChatType.PRIVATE:
        return await message.reply(_ping, effect_id=effect_id)
    else:
        return await message.reply(_ping)


async def add_absen(client, text):
    auto_text = await dB.get_var(client.me.id, "TEXT_ABSEN") or []
    auto_text.append(text)
    await dB.set_var(client.me.id, "TEXT_ABSEN", auto_text)


async def absen_cmd(client, message):
    txt = await dB.get_var(client.me.id, "TEXT_ABSEN")
    if len(message.command) == 1:
        if not txt:
            return
        try:
            psn = random.choice(txt)
            return await message.reply(psn)
        except:
            pass
    else:
        command, variable = message.command[:2]
        if variable.lower() == "text":
            for x in client._ubot:
                value = " ".join(message.command[2:])
                await add_absen(x, value)

        else:
            return


async def setprefix_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    pong_, uptime_, owner_, ubot_, proses_, sukses_ = await emo.get_costum_text()
    pros = await animate_proses(message, emo.proses)
    if len(message.command) < 2:
        m = message.text.split()[0]
        return await pros.edit(
            f"{emo.gagal}<b>Please provide the Prefix/Handler you want to use.</b>\n\n"
            f"Example:\n<code>{m}setprefix , . ? : ;</code>\n\n"
            f"Or use <code>none</code> if you want to use commands without a Prefix/Handler."
        )
    ub_prefix = []
    for prefix in message.command[1:]:
        if prefix.lower() == "none":
            ub_prefix.append("")
        else:
            ub_prefix.append(prefix)
    try:
        client.set_prefix(client.me.id, ub_prefix)
        await dB.set_pref(client.me.id, ub_prefix)
        parsed_prefix = (
            " ".join(f"<code>{prefix}</code>" for prefix in ub_prefix if prefix)
            or "none"
        )
        return await pros.edit(
            f"{emo.sukses}<b>Successfully set the Prefix to: {parsed_prefix}</b>"
        )
    except Exception as error:
        return await pros.edit(f"{emo.gagal}<b>ERROR: <code>{error}</code></b>")


async def setonline_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    pref = client.get_prefix(client.me.id)
    x = next(iter(pref))
    rep = message.reply_to_message
    if len(message.command) == 1 and not rep:
        return await message.reply(
            f"{emo.gagal}<b>Use the command like this:</b>\n<code>{x}setonline</code> on/off."
        )
    pros = await animate_proses(message, emo.proses)
    handle = message.text.split(None, 1)[1]
    try:
        if handle.lower() == "off":
            await client.invoke(functions.account.UpdateStatus(offline=False))
            return await pros.edit(
                f"{emo.sukses}<b>Successfully changed online status to: <code>{handle}</code></b>"
            )
        elif handle.lower() == "on":
            await client.invoke(functions.account.UpdateStatus(offline=True))
            return await pros.edit(
                f"{emo.sukses}<b>Successfully changed online status to: <code>{handle}</code></b>"
            )
        else:
            return await pros.edit(
                f"{emo.gagal}<b>Use the command like this:</b>\n<code>{x}setonline</code> on/off."
            )
    except Exception as e:
        return await pros.edit(f"{emo.gagal}<b>Error:</b>\n<code>{e}</code>")


async def unblock_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    user_id = await client.extract_user(message)
    if not user_id:
        return await message.reply(
            f"{emo.gagal}<b>Provide username/user_id/reply to user's message.</b>"
        )
    pros = await animate_proses(message, emo.proses)
    try:
        user = await client.get_users(user_id)
    except PeerIdInvalid:
        return await pros.edit(
            f"{emo.gagal}<b>I have never interacted with <code>{user_id}</code></b>"
        )
    except Exception as e:
        return await pros.edit(f"{emo.gagal}<b>Error:</b>\n<code>{str(e)}</code>")
    if user.id == client.me.id:
        return await pros.edit(f"{emo.sukses}<b>Ok!</b>")
    await client.unblock_user(user.id)
    return await pros.edit(f"{emo.sukses}<b>Successfully unblocked {user.mention}.</b>")


async def block_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    user_id = await client.extract_user(message)
    if not user_id:
        return await message.reply(
            f"{emo.gagal}<b>Provide username/user_id or reply to user's message.</b>"
        )
    pros = await animate_proses(message, emo.proses)
    try:
        user = await client.get_users(user_id)
    except PeerIdInvalid:
        return await pros.edit(
            f"{emo.gagal}<b>I have never interacted with <code>{user_id}</code></b>"
        )
    except Exception as e:
        return await pros.edit(f"{emo.gagal}<b>Error:</b>\n<code>{str(e)}</code>")
    if user.id == client.me.id:
        return await pros.edit(f"{emo.sukses}<b>Ok!</b>")
    await client.block_user(user_id)
    return await pros.edit(f"{emo.sukses}<b>Successfully blocked {user.mention}.</b>")


async def setname_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    pros = await animate_proses(message, emo.proses)
    rep = message.reply_to_message
    if len(message.command) == 1 and not rep:
        return await pros.edit(
            f"{emo.gagal}<b>Provide text or reply to a message to set as your name.</b>"
        )
    elif len(message.command) > 1:
        nama = message.text.split(None, 2)
        name = nama[1]
        namee = nama[2] if len(nama) > 2 else ""

        try:
            await client.update_profile(first_name=name)
            await client.update_profile(last_name=namee)
            return await pros.edit(
                f"{emo.sukses}<b>Successfully changed name to: <code>{name} {namee}</code></b>"
            )
        except Exception as e:
            return await pros.edit(f"{emo.gagal}<b>Error:</b>\n<code>{e}</code>")


async def setuname_cmd(client, message):
    emo = Emoji(client)
    await emo.get()

    rep = message.reply_to_message
    if len(message.command) == 1 and not rep:
        return await message.reply(
            f"{emo.gagal}<b>Provide text or reply to a message to set as your username.</b>"
        )
    pros = await animate_proses(message, emo.proses)
    if rep:
        uname = rep.text or rep.caption
    elif len(message.command) > 1:
        nama = message.text.split(None, 1)
        uname = nama[1]
    else:
        return await pros.edit(
            f"{emo.gagal}<b>Provide text or reply to a message to set as your username.</b>"
        )

    try:
        await client.set_username(username=uname)
        return await pros.edit(
            f"{emo.sukses}<b>Successfully changed username to: <code>{uname}</code></b>"
        )
    except FloodWait as e:
        wait = int(e.value)
        await asyncio.sleep(wait)
        await client.set_username(username=uname)
        return await pros.edit(
            f"{emo.sukses}<b>Successfully changed username to: <code>{uname}</code></b>"
        )
    except UsernameOccupied:
        return await pros.edit(
            f"{emo.gagal}<b><code>{uname}</code> is already taken by another user.</b>"
        )
    except Exception as e:
        return await pros.edit(f"{emo.gagal}<b>Error:</b>\n<code>{e}</code>")


async def remuname_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    pros = await animate_proses(message, emo.proses)

    try:
        await client.set_username(username="")
        return await pros.edit(f"{emo.sukses}<b>Username successfully removed.</b>")
    except Exception as e:
        return await pros.edit(f"{emo.gagal}<b>Error:</b>\n<code>{e}</code>")


async def setbio_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    pros = await animate_proses(message, emo.proses)
    rep = message.reply_to_message
    if len(message.command) == 1 and not rep:
        return await pros.edit(f"{emo.gagal}<b>Provide text or reply to a message.</b>")
    if rep:
        bio = rep.text or rep.caption
    elif len(message.command) > 1:
        bio = message.text.split(None, 1)[1]
    try:
        await client.update_profile(bio=bio)
        return await pros.edit(
            f"{emo.sukses}<b>Successfully changed bio to: <code>{bio}</b>"
        )
    except Exception as e:
        return await pros.edit(f"{emo.gagal}<b>Error:</b> <code>{e}</code>")


async def adminlist_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    pros = await animate_proses(message, emo.proses)
    a_chats = []
    me = await client.get_me()
    async for dialog in client.get_dialogs():
        try:
            tipe = dialog.chat.type
            if tipe in (enums.ChatType.SUPERGROUP, enums.ChatType.GROUP):
                try:
                    gua = await dialog.chat.get_member(int(me.id))
                    if gua.status in (
                        enums.ChatMemberStatus.OWNER,
                        enums.ChatMemberStatus.ADMINISTRATOR,
                    ):
                        a_chats.append(dialog.chat)
                except Exception:
                    continue
        except Exception:
            continue

    text = "<b>❒ LIST OF GROUPS WHERE YOU ARE AN ADMIN:</b>\n┃\n"
    if len(a_chats) == 0:
        text += "<b>You are not an admin anywhere.</b>"
        return await pros.edit(f"{text}")
    for count, chat in enumerate(a_chats, 1):
        try:
            title = chat.title
        except Exception:
            title = "Private Group"
        if count == len(a_chats):
            text += f"<b>┖ {title}</b>\n"
        else:
            text += f"<b>┣ {title}</b>\n"

    if len(text) > 4096:
        with BytesIO(str.encode(text)) as out_file:
            out_file.name = "adminlist.txt"
            await message.reply_document(
                document=out_file,
                caption=f"{emo.sukses}<b>Admin List {client.me.mention}.</b>",
            )
            os.remove(out_file)
            return await pros.delete()
    else:
        return await pros.edit(f"{text}")


async def setpp_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    po = "storage/TM_BLACK.png"
    replied = message.reply_to_message
    pros = await animate_proses(message, emo.proses)
    if (
        replied
        and replied.media
        and (
            replied.photo
            or (replied.document and "image" in replied.document.mime_type)
        )
    ):
        prop = await client.download_media(message=replied, file_name=po)
        await client.set_profile_photo(photo=prop)
        await client.send_photo(
            message.chat.id,
            prop,
            caption=f"{emo.sukses}<b>Successfully changed your profile picture.</b>",
        )
        if os.path.exists(prop):
            os.remove(prop)
        return await pros.delete()
    else:
        return await pros.edit(
            f"{emo.gagal}<b>Reply to a photo/image, or a document that is a photo/image to set as your profile picture.</b>"
        )


async def mestats_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    pros = await animate_proses(message, emo.proses)
    start = datetime.now()
    pc = 0
    groups = 0
    super_groups = 0
    channels = 0
    bots = 0
    adminchats = 0
    banned = 0
    here = set()
    gue = await client.get_me()

    try:
        async for dialog in client.get_dialogs():
            try:
                if dialog.chat.type == ChatType.PRIVATE:
                    pc += 1
                elif dialog.chat.type == ChatType.BOT:
                    bots += 1
                elif dialog.chat.type == ChatType.GROUP:
                    groups += 1
                    ucel = await dialog.chat.get_member(int(gue.id))
                    if ucel.status in (
                        ChatMemberStatus.OWNER,
                        ChatMemberStatus.ADMINISTRATOR,
                    ):
                        adminchats += 1
                elif dialog.chat.type == ChatType.SUPERGROUP:
                    super_groups += 1
                    user_s = await dialog.chat.get_member(int(gue.id))
                    if user_s.status in (
                        ChatMemberStatus.OWNER,
                        ChatMemberStatus.ADMINISTRATOR,
                    ):
                        adminchats += 1
                elif dialog.chat.type == ChatType.CHANNEL:
                    channels += 1
            except ChannelPrivate:
                banned += 1
                here.add(dialog.chat.id)
                continue
            except UserNotParticipant:
                await client.leave_chat(dialog.chat.id)
                print(f"Bot is not a member of this chat, leaving: {dialog.chat.id}")
                continue
    except ChannelPrivate:
        banned += 1
        here.add(dialog.chat.id)
    except Exception as e:
        print(f"An error occurred: {str(e)} {dialog.chat.id}")

    end = datetime.now()
    waktu = (end - start).seconds

    if not here:
        here = 0

    return await pros.edit(
        f"""
{emo.sukses}<b>Successfully extracted your data in <code>{waktu}</code> seconds:

• <code>{pc}</code> Private Messages.
• <code>{groups}</code> Groups.
• <code>{super_groups}</code> Super Groups.
• <code>{channels}</code> Channels.
• <code>{adminchats}</code> Admin Chats.
• <code>{bots}</code> Bots.
• <code>{banned}</code> Problematic Groups.

I encountered issues with these chats: 
• <code>{here}</code></b>
"""
    )


async def react_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    sukses = 0
    failed = 0

    if len(message.command) not in [2, 3]:
        return await proses.edit(
            f"{em.gagal}**Please use format `{message.text.split()[0]}` [@username/chat_id] [emoji/random]**"
        )

    task_id = task.start_task()
    try:
        if len(message.command) == 3:
            chat_id = message.text.split()[1]
            emoji = message.text.split()[2]
        else:
            chat_id = message.chat.id
            emoji = message.text.split()[1]

        if emoji.lower() == "random":
            emoji = random.choice(RANDOM_EMOJIS)

        prefix = client.get_prefix(client.me.id)

        await proses.edit(
            f"{em.proses}<i>Task reaction running #<code>{task_id}</code>. Type <code>{prefix[0]}cancel {task_id}</code> to stop reaction!</i>"
        )
        try:
            for c in client._ubot:
                async for m in c.get_chat_history(chat_id):
                    if not task.is_active(task_id):
                        return await proses.edit(
                            f"{em.gagal}**Task #{task_id} has been cancelled!**"
                        )
                    await asyncio.sleep(0.5)
                    message_id = m.id
                await asyncio.sleep(0.5)
                await c.send_reaction(
                    chat_id=chat_id, message_id=message_id, emoji=emoji
                )
                sukses += 1
        except Exception:
            failed += 1
    except Exception as er:
        return await proses.edit(f"{em.gagal}**ERROR:** {str(er)}")
    finally:
        task.end_task(task_id)
    return await proses.edit(
        f"<b>{em.sukses}Succesfully send reaction to chat: {chat_id}, emoji: {emoji}.\n\nSucces: {sukses}, Failed: {failed}.</b>"
    )


async def react2_cmd(client, message):
    em = Emoji(client)
    await em.get()

    reply = message.reply_to_message or message
    proses = await animate_proses(message, em.proses)
    sukses = 0
    failed = 0

    if len(message.command) < 2:
        return await proses.edit(
            f"{em.gagal}**Please use format `{message.text.split()[0]}` [emoji/random]**"
        )

    task_id = task.start_task()
    try:
        chat_id = message.chat.id
        emoji = message.text.split()[1]

        if emoji.lower() == "random":
            emoji = random.choice(RANDOM_EMOJIS)

        prefix = client.get_prefix(client.me.id)

        await proses.edit(
            f"{em.proses}<i>Task reaction running #<code>{task_id}</code>. Type <code>{prefix[0]}cancel {task_id}</code> to stop reaction!</i>"
        )
        try:
            for c in client._ubot:
                message_id = reply.id
                await asyncio.sleep(0.5)
                await c.send_reaction(
                    chat_id=chat_id, message_id=message_id, emoji=emoji
                )
                sukses += 1
        except Exception:
            failed += 1
    except Exception as er:
        return await proses.edit(f"{em.gagal}**ERROR:** {str(er)}")
    finally:
        task.end_task(task_id)
    return await proses.edit(
        f"<b>{em.sukses}Succesfully send reaction to chat: {chat_id}\nEmoji: {emoji}\nSucces: {sukses}, Failed: {failed}.</b>"
    )


async def sangmata_cmd(client, message):
    em = Emoji(client)
    await em.get()
    reply = message.reply_to_message
    try:
        if len(message.command) < 2 and not reply:
            return await message.reply(
                f"**{em.gagal}Please reply to a message or provide a username/id**"
            )
        if reply:
            user = reply.from_user.id
        else:
            target = message.text.split()[1]
            if target.startswith("@") or not target.isdigit():
                user = (await client.get_users(target)).id
            else:
                user = int(target)

        proses = await animate_proses(message, em.proses)
        sg = "@SangMata_BOT"
        try:
            a = await client.send_message(sg, user)
            await asyncio.sleep(1)
            await a.delete()
        except Exception as e:
            return await proses.edit(f"**{em.gagal}{str(e)}**")
        async for respon in client.search_messages(a.chat.id):
            if respon.text == None:
                continue
            if not respon:
                return await message.reply(f"**{em.gagal}No response from Sangmata**")
            elif respon:
                await message.reply(f"{em.sukses} {respon.text}")
                break
        await proses.delete()
        try:
            user_info = await client.resolve_peer(sg)
            return await client.invoke(
                raw.functions.messages.DeleteHistory(
                    peer=user_info, max_id=0, revoke=True
                )
            )
        except Exception:
            pass
    except Exception as er:
        return await message.reply(f"**ERROR**: {str(er)}")


async def story_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    args = ["cek", "del", "get", "post"]
    query = message.command[1]
    if len(message.command) < 2 and query not in args:
        return await proses.edit(
            f"{em.gagal}<b>Please give query [post, cek, get, or del]</b>"
        )
    prefix = client.get_prefix(client.me.id)
    if query == "cek":
        text = f"{em.owner}<b>Your stories:</b>\n\n"
        async for story in client.get_all_stories():
            if story.from_user.id == client.me.id:
                story_link = await client.export_story_link("me", story.id)
                text += f"{em.sukses}<b>• Story ID: `{story.id}` | Story Link: [Click Here]({story_link})</b>\n"
        await message.reply(text, disable_web_page_preview=True)
        return await proses.delete()

    elif query == "del":
        if len(message.command) < 3:
            return await proses.edit(
                f"<b>{em.gagal} That's not how it works!! Provide your story ID.\nExample: `{prefix[0]}story del` 5\n\nOr you can type `{prefix[0]}story cek` to see your story IDs!! </b>"
            )
        story_id = message.text.split()[2]
        if not story_id.isnumeric():
            return await proses.edit(
                f"{em.gagal}<b>ID should be a number, not letters or symbols.</b>"
            )
        await client.delete_stories(story_ids=int(story_id))
        return await proses.edit(
            f"{em.sukses}<b>Successfully deleted Story ID: `{story_id}`!!</b>"
        )

    elif query == "get":
        if len(message.command) < 3:
            return await proses.edit(f"{em.gagal}**Please give link story!**")
        link = message.text.split()[2]
        if "/s/" not in link:
            return await proses.edit(
                f"{em.gagal}<b>Please provide a valid Telegram stories link!!</b>"
            )
        user, story_id = Tools.extract_story_link(link)
        story = await client.get_stories(user, story_id)
        await Tools.download_media(story, client, proses, message, True)
        return await proses.delete()

    elif query == "post":
        reply = message.reply_to_message
        if not reply or reply and not reply.media:
            return await proses.edit(f"{em.gagal}**Please reply to photo or video**")
        kwargs = reply.photo.file_id or reply.video.file_id
        text = reply.caption or ""
        try:
            target = "me" if len(message.command) < 3 else message.text.split()[2]
            story = await client.send_story(
                target, kwargs, caption=text, privacy=StoriesPrivacyRules.PUBLIC
            )
            this = await client.export_story_link("me", story.id)
            return await proses.edit(
                f"{em.sukses}<b>Succesfully upload to [Story]({this})!</b>",
                disable_web_page_preview=True,
            )
        except Exception as e:
            logger.error(f"Error: {traceback.format_exc()}")
            return await proses.edit(f"{em.gagal}**ERROR:** {str(e)}")
    else:
        return await proses.edit(
            f"{em.gagal}<b>Please give query [post, cek, get, or del]</b>"
        )


async def ignore_cmd(client, message):
    data = await dB.get_var(client.me.id, "IGNORE_MODULES") or []
    if message.command[0] == "ignore":
        if len(message.command) < 2:
            return await message.reply("**Please give plugins name for disable**")
        name = client.get_text(message)
        ada = next((n for n in HELPABLE if name.lower() == n), None)
        if ada is None:
            return await message.reply(f"**Plugins {name} is not defined**")
        if name.lower() in data:
            return await message.reply(f"**Plugins {name} already disabled**")
        data.append(name.lower())
        await dB.set_var(client.me.id, "IGNORE_MODULES", data)
        return await message.reply(f"**Disabled plugins: `{name}`.**")
    elif message.command[0] == "reignore":
        if len(message.command) < 2:
            return await message.reply("**Please give plugins name for enable**")
        name = client.get_text(message)
        ada = next((n for n in HELPABLE if name.lower() == n), None)
        if ada is None:
            return await message.reply(f"**Plugins {name} is not defined**")
        if name.lower() not in data:
            return await message.reply(f"**Plugins {name} already enable**")
        data.remove(name.lower())
        await dB.set_var(client.me.id, "IGNORE_MODULES", data)
        return await message.reply(f"**Enabled plugins: `{name}`.**")
    elif message.command[0] == "ignored":
        msg = ""
        for count, name in enumerate(data, 1):
            msg += f"**{count}**. `{name}`\n"
        return await message.reply(msg)
