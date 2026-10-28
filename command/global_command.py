import asyncio
from io import BytesIO

from pyrogram.errors import (FloodWait, PeerIdInvalid, UsernameInvalid,
                             UsernameNotOccupied)
from pyrogram.raw.functions.messages import DeleteHistory
from pyrogram.types import ChatPermissions

from config import DEVS
from database import dB
from helpers import Emoji, animate_proses, task


async def gban_cmd(client, message):
    em = Emoji(client)
    await em.get()
    reply = message.reply_to_message
    proses = await animate_proses(message, em.proses)
    try:
        target = reply.from_user.id if reply else message.text.split()[1]
    except (AttributeError, IndexError):
        return await proses.edit(
            f"{em.gagal}<b>You need to specify a user to gban (either by reply or username/ID)!</b>"
        )
    task_id = task.start_task()
    prefix = client.get_prefix(client.me.id)
    try:
        user = await client.get_users(target)
    except (PeerIdInvalid, KeyError, UsernameInvalid, UsernameNotOccupied):
        return await proses.edit(f"{em.gagal}<b>You need meet before interact!!</b>")
    mention = user.mention
    user_id = user.id
    if user_id == client.me.id:
        return await proses.edit(f"{em.gagal}<b>Go to the heal now!!</b>")
    if user_id in DEVS:
        try:
            await client.send_message(
                user_id, "<b>I try to do global banned your account!!</b>"
            )
            return await proses.edit(
                f"{em.gagal}<b>User: {user_id}|{mention} is a developer!!</b>"
            )
        except Exception:
            pass
    await proses.edit(
        f"{em.proses}<i>Task gban running #<code>{task_id}</code>. "
        f"Type <code>{prefix[0]}cancel {task_id}</code> to cancel gbanned!</i>"
    )
    done = 0
    fail = 0
    chats = await client.get_chat_id("global")
    db_gban = await dB.get_list_from_var(client.me.id, "GBANNED")
    try:
        for chat in chats:
            if not task.is_active(task_id):
                return await proses.edit(f"{em.gagal}Gbanned cancelled.")
            if user_id in db_gban:
                await proses.edit(f"{em.gagal}<b>User already in gbanned</b>")
                return
            try:
                await client.ban_chat_member(chat, user_id)
                done += 1
                await asyncio.sleep(0.1)
            except Exception:
                fail += 1
            except FloodWait as e:
                await asyncio.sleep(int(e.value))
                await client.ban_chat_member(chat, user_id)
                done += 1
                await asyncio.sleep(0.1)
    finally:
        task.end_task(task_id)

    await dB.add_to_var(client.me.id, "GBANNED", user_id)
    await client.block_user(user_id)
    solve = await client.resolve_peer(user_id)
    await client.invoke(DeleteHistory(peer=(solve), max_id=0, revoke=True))
    teks = f"""
<blockquote><b>{em.warn}#GBANNED</b>
<b>{em.sukses}Success: {done}</b>
<b>{em.gagal}Failed: {fail}</b>
<b>{em.proses}Type: {message.command[0]}</b>
<b>{em.robot}Task ID: `{task_id}`</b>
<b>{em.profil}User: {mention}</b>
"""
    await proses.delete()
    return await message.reply(teks)


async def ungban_cmd(client, message):
    em = Emoji(client)
    await em.get()

    reply = message.reply_to_message
    proses = await animate_proses(message, em.proses)
    try:
        target = reply.from_user.id if reply else message.text.split()[1]
    except (AttributeError, IndexError):
        return await proses.edit(
            f"{em.gagal}<b>You need to specify a user to ungban (either by reply or username/ID)!</b>"
        )
    task_id = task.start_task()
    prefix = client.get_prefix(client.me.id)
    try:
        user = await client.get_users(target)
    except (PeerIdInvalid, KeyError, UsernameInvalid, UsernameNotOccupied):
        return await proses.edit(f"{em.gagal}<b>You need meet before interact!!</b>")
    mention = user.mention
    user_id = user.id
    await proses.edit(
        f"{em.proses}<i>Task ungban running #<code>{task_id}</code>. "
        f"Type <code>{prefix[0]}cancel {task_id}</code> to cancel ungbanned!</i>"
    )
    done = 0
    fail = 0
    chats = await client.get_chat_id("global")
    db_gban = await dB.get_list_from_var(client.me.id, "GBANNED")
    try:
        for chat in chats:
            if not task.is_active(task_id):
                return await proses.edit(f"{em.gagal}UnGbanned cancelled.")
            if user_id not in db_gban:
                await proses.edit(f"{em.gagal}<b>User has not gbanned</b>")
                return
            try:
                await client.unban_chat_member(chat, user_id)
                done += 1
                await asyncio.sleep(0.1)
            except Exception:
                fail += 1
            except FloodWait as e:
                await asyncio.sleep(int(e.value))
                await client.unban_chat_member(chat, user_id)
                done += 1
                await asyncio.sleep(0.1)
    finally:
        task.end_task(task_id)

    await dB.remove_from_var(client.me.id, "GBANNED", user_id)
    await client.unblock_user(user_id)
    teks = f"""
<blockquote><b>{em.warn}#UNGBANNED</b>
<b>{em.sukses}Success: {done}</b>
<b>{em.gagal}Failed: {fail}</b>
<b>{em.proses}Type: {message.command[0]}</b>
<b>{em.robot}Task ID: `{task_id}`</b>
<b>{em.profil}User: {mention}</b>
"""
    await proses.delete()
    return await message.reply(teks)


async def gbanlist_cmd(client, message):
    em = Emoji(client)
    await em.get()

    db_gban = await dB.get_list_from_var(client.me.id, "GBANNED")
    proses = await animate_proses(message, em.proses)
    if not db_gban:
        return await proses.edit(f"{em.gagal}<b>There are no users yet!</b>")
    teks = f"    Users \n"
    for num, user in enumerate(db_gban, 1):
        teks += f"│ {num}. {em.warn} {user}\n"
    try:
        await message.reply_text(teks)
    except Exception:
        await proses.edit(f"{em.proses}<b>Message too long, try to send document!</b>")
        with BytesIO(str.encode(teks)) as f:
            f.name = "gbanlist.txt"
            await message.reply_document(
                document=f, caption="<b>Here list of users</b>"
            )
    return await proses.delete()


async def gmute_cmd(client, message):
    em = Emoji(client)
    await em.get()

    reply = message.reply_to_message
    proses = await animate_proses(message, em.proses)
    try:
        target = reply.from_user.id if reply else message.text.split()[1]
    except (AttributeError, IndexError):
        return await proses.edit(
            f"{em.gagal}<b>You need to specify a user to gmute (either by reply or username/ID)!</b>"
        )
    task_id = task.start_task()
    prefix = client.get_prefix(client.me.id)

    try:
        user = await client.get_users(target)
    except (PeerIdInvalid, KeyError, UsernameInvalid, UsernameNotOccupied):
        return await proses.edit(f"{em.gagal}<b>You need meet before interact!!</b>")

    mention = user.mention
    user_id = user.id
    if user_id == client.me.id:
        return await proses.edit(f"{em.gagal}<b>Go to the heal now!!</b>")
    if user_id in DEVS:
        try:
            await client.send_message(
                user_id, "<b>I try to do global mute your account!!</b>"
            )
            return await proses.edit(
                f"{em.gagal}<b>User: {user_id}|{mention} is a developer!!</b>"
            )
        except Exception:
            pass
    await proses.edit(
        f"{em.proses}<i>Task gmute running #<code>{task_id}</code>. "
        f"Type <code>{prefix[0]}cancel {task_id}</code> to cancel gmuted!</i>"
    )
    done = 0
    fail = 0
    chats = await client.get_chat_id("group")
    db_gmute = await dB.get_list_from_var(client.me.id, "GMUTE")
    try:
        for chat in chats:
            if not task.is_active(task_id):
                return await proses.edit(f"{em.gagal}Gmuted cancelled.")
            if user_id in db_gmute:
                await proses.edit(f"{em.gagal}<b>User already gmuted</b>")
                return
            try:
                await client.restrict_chat_member(chat, user_id, ChatPermissions())
                done += 1
                await asyncio.sleep(0.1)
            except Exception:
                fail += 1
            except FloodWait as e:
                await asyncio.sleep(int(e.value))
                await client.restrict_chat_member(chat, user_id, ChatPermissions())
                done += 1
                await asyncio.sleep(0.1)
    finally:
        task.end_task(task_id)

    await dB.add_to_var(client.me.id, "GMUTE", user_id)
    teks = f"""
<blockquote><b>{em.warn}#GMUTED</b>
<b>{em.sukses}Success: {done}</b>
<b>{em.gagal}Failed: {fail}</b>
<b>{em.msg}Type: {message.command[0]}</b>
<b>{em.robot}Task ID: `{task_id}`</b>
<b>{em.profil}User: {mention}</b>
"""
    await proses.delete()
    return await message.reply(teks)


async def ungmute_cmd(client, message):
    em = Emoji(client)
    await em.get()

    reply = message.reply_to_message
    proses = await animate_proses(message, em.proses)
    try:
        target = reply.from_user.id if reply else message.text.split()[1]
    except (AttributeError, IndexError):
        return await proses.edit(
            f"{em.gagal}<b>You need to specify a user to ungmute (either by reply or username/ID)!</b>"
        )
    task_id = task.start_task()
    prefix = client.get_prefix(client.me.id)

    try:
        user = await client.get_users(target)
    except (PeerIdInvalid, KeyError, UsernameInvalid, UsernameNotOccupied):
        return await proses.edit(f"{em.gagal}<b>You need meet before interact!!</b>")
    mention = user.mention
    user_id = user.id
    await proses.edit(
        f"{em.proses}<i>Task ungmute running #<code>{task_id}</code>. "
        f"Type <code>{prefix[0]}cancel {task_id}</code> to cancel ungmuted!</i>"
    )
    done = 0
    fail = 0
    chats = await client.get_chat_id("group")
    db_gmute = await dB.get_list_from_var(client.me.id, "GMUTE")
    try:
        for chat in chats:
            if not task.is_active(task_id):
                return await proses.edit(f"{em.gagal}Ungmuted cancelled.")
            if user_id not in db_gmute:
                await proses.edit(f"{em.gagal}<b>User has not gmuted</b>")
                return
            try:
                await client.unban_member(chat, user_id, ChatPermissions())
                done += 1
                await asyncio.sleep(0.1)
            except Exception:
                fail += 1
            except FloodWait as e:
                await asyncio.sleep(int(e.value))
                await client.unban_member(chat, user_id, ChatPermissions())
                done += 1
                await asyncio.sleep(0.1)
    finally:
        task.end_task(task_id)

    await dB.remove_from_var(client.me.id, "GMUTE", user_id)
    teks = f"""
<blockquote><b>{em.warn}#UNGMUTED</b>
<b>{em.sukses}Success: {done}</b>
<b>{em.gagal}Failed: {fail}</b>
<b>{em.msg}Type: {message.command[0]}</b>
<b>{em.robot}Task ID: `{task_id}`</b>
<b>{em.profil}User: {mention}</b>
"""
    await proses.delete()
    return await message.reply(teks)


async def gmutelist_cmd(client, message):
    em = Emoji(client)
    await em.get()

    db_gban = await dB.get_list_from_var(client.me.id, "GMUTE")
    proses = await animate_proses(message, em.proses)
    if not db_gban:
        return await proses.edit(f"{em.gagal}<b>There are no users yet!</b>")
    teks = f"    Users \n"
    for num, user in enumerate(db_gban, 1):
        teks += f"│ {num}. {em.warn} {user}\n"
    try:
        await message.reply_text(teks)
    except Exception:
        await proses.edit(f"{em.proses}<b>Message too long, try to send document!</b>")
        with BytesIO(str.encode(teks)) as f:
            f.name = "gmutelist.txt"
            await message.reply_document(
                document=f, caption="<b>Here list of users</b>"
            )
    return await proses.delete()
