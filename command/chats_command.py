import asyncio
import random
import traceback

from pyrogram import enums, raw
from pyrogram.enums import ChatMembersFilter
from pyrogram.errors import (ChatAdminRequired, ChatNotModified, FloodWait,
                             PeerFlood, PeerIdInvalid, RPCError,
                             UserAlreadyParticipant, UsernameInvalid,
                             UsernameNotOccupied, UserNotMutualContact,
                             UserPrivacyRestricted)
from pyrogram.types import ChatPermissions

from config import BLACKLIST_GCAST, DEVS
from database import dB
from helpers import Emoji, animate_proses, task

from .admins_command import admin_check

l_t = """
**Lock Types:**
- `all` = Everything
- `msg` = Messages
- `media` = Media, such as Photo and Video.
- `polls` = Polls
- `invite` = Add users to Group
- `pin` = Pin Messages
- `info` = Change Group Info
- `webprev` = Web Page Previews
- `inline` = Inline bots
- `games` = Game Bots
- `stickers` = Stickers
- `topic` = Manage Topics
- `gifs` = Gifs
- `audio` = Audio
- `document` = Document
- `photo` = Photo
- `plain` = Plain Text
- `video_note` = Video Note
- `video` = Video
- `voice` = Voice Messages"""

data = {
    "msg": "can_send_messages",
    "media": "can_send_media_messages",
    "stickers": "can_send_stickers",
    "gifs": "can_send_gifs",
    "games": "can_send_games",
    "inline": "can_send_inline",
    "url": "can_add_web_page_previews",
    "polls": "can_send_polls",
    "info": "can_change_info",
    "invite": "can_invite_users",
    "pin": "can_pin_messages",
    "topic": "can_manage_topics",
    "audio": "can_send_audios",
    "document": "can_send_docs",
    "photo": "can_send_photos",
    "plain": "can_send_plain",
    "video_note": "can_send_roundvideos",
    "video": "can_send_videos",
    "voice": "can_send_voices",
}


async def current_chat_permissions(client, chat_id):
    perms = []
    perm = (await client.get_chat(chat_id)).permissions or ChatPermissions()
    for k in data.values():
        if getattr(perm, k, False):
            perms.append(k)
    return perms


async def tg_lock(client, message, permissions: list, perm: str, lock: bool):
    em = Emoji(client)
    await em.get()

    if lock:
        if perm not in permissions:
            return await message.reply(f"{em.sukses}**Successfully locked.**")
        permissions.remove(perm)
    elif perm in permissions:
        return await message.reply(f"{em.sukses}**Already unlocked.**")
    else:
        permissions.append(perm)

    perms_dict = {p: True for p in permissions}

    try:
        await client.set_chat_permissions(
            message.chat.id, ChatPermissions(**perms_dict)
        )
    except ChatNotModified:
        return await message.reply(
            f"{em.gagal}**To unlock this, you have to unlock 'messages' first.**"
        )

    return await message.reply(
        (f"{em.sukses}**Successfully locked.**")
        if lock
        else (f"{em.sukses}**Successfully unlocked.**")
    )


async def lockunlock_cmd(client, message):
    em = Emoji(client)
    await em.get()
    if len(message.command) != 2:
        return await message.reply(f"{em.gagal}**Invalid command format.**")

    chat_id = message.chat.id
    parameter = message.text.strip().split(None, 1)[1].lower()
    state = message.command[0].lower()
    lock = True if state == "lock" else False

    if parameter not in data and parameter != "all":
        return await message.reply(f"{em.gagal}**Invalid lock type.**")

    permissions = await current_chat_permissions(client, chat_id)

    if parameter == "all":
        perm_values = {v: not lock for v in data.values()}
        try:
            await client.set_chat_permissions(chat_id, ChatPermissions(**perm_values))
            return await message.reply(
                f"{em.sukses}**All permissions {'locked' if lock else 'unlocked'}.**"
            )
        except ChatAdminRequired:
            return await message.reply(f"{em.gagal}**Admin privileges required.**")

    else:
        return await tg_lock(client, message, permissions, data[parameter], lock)


async def locks_cmd(client, message):
    em = Emoji(client)
    await em.get()
    chkmsg = await animate_proses(message, em.proses)
    v_perm = message.chat.permissions

    def convert_to_emoji(val: bool):
        if val:
            return f"{em.sukses}"
        return f"{em.gagal}"

    vmsg = convert_to_emoji(v_perm.can_send_messages)
    vmedia = convert_to_emoji(v_perm.can_send_media_messages)
    vwebprev = convert_to_emoji(v_perm.can_add_web_page_previews)
    vstickers = convert_to_emoji(v_perm.can_send_stickers)
    vpolls = convert_to_emoji(v_perm.can_send_polls)
    vinfo = convert_to_emoji(v_perm.can_change_info)
    vinvite = convert_to_emoji(v_perm.can_invite_users)
    vpin = convert_to_emoji(v_perm.can_pin_messages)

    vgifs = convert_to_emoji(v_perm.can_send_gifs)
    vgames = convert_to_emoji(v_perm.can_send_games)
    vinline = convert_to_emoji(v_perm.can_send_inline)
    vtopic = convert_to_emoji(v_perm.can_manage_topics)
    vaudio = convert_to_emoji(v_perm.can_send_audios)
    vdocument = convert_to_emoji(v_perm.can_send_docs)
    vphoto = convert_to_emoji(v_perm.can_send_photos)
    vplain = convert_to_emoji(v_perm.can_send_plain)
    vvideo_note = convert_to_emoji(v_perm.can_send_roundvideos)
    vvideo = convert_to_emoji(v_perm.can_send_videos)
    vvoice = convert_to_emoji(v_perm.can_send_voices)
    if v_perm is not None:
        try:
            permission_view_str = f"""
<b>{em.warn}Chat Permissions:</b>

      <b>Manage Topic:</b> {vtopic}
      <b>Webpage Preview:</b> {vwebprev}
      <b>Change Info:</b> {vinfo}
      <b>Invite Users:</b> {vinvite}
      <b>Pin Messages:</b> {vpin}
      <b>Send Messages:</b> {vmsg}
      <b>Send Media:</b> {vmedia}
      <b>Send Stickers:</b> {vstickers}
      <b>Send Polls:</b> {vpolls}
      <b>Send Gifs:</b> {vgifs}
      <b>Send Games:</b> {vgames}
      <b>Send Inline:</b> {vinline}
      <b>Send Audio:</b> {vaudio}
      <b>Send Document:</b> {vdocument}
      <b>Send Photo:</b> {vphoto}
      <b>Send Plan:</b> {vplain}
      <b>Send Video Note:</b> {vvideo_note}
      <b>Send Video:</b> {vvideo}
      <b>Send Voice:</b> {vvoice}
      """
            return await chkmsg.edit_text(permission_view_str)

        except RPCError as e_f:
            return await message.reply_text(f"{em.gagal}Error: {str(e_f)}")


async def getmute_cmd(client, message):
    em = Emoji(client)
    await em.get()

    output = ""
    msg = await animate_proses(message, em.proses)

    async for dialog in client.get_dialogs():
        if dialog.chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
            try:
                member = await client.get_chat_member(dialog.chat.id, client.me.id)
                if member.status == enums.ChatMemberStatus.RESTRICTED:
                    chat = await client.get_chat(dialog.chat.id)
                    output += f"{chat.title} | [`{chat.id}`]\n"
            except Exception:
                continue

    if output:
        text = f"<blockquote><b>The list of groups that mute you are:</b>\n{output}</blockquote>"
    else:
        text = "<blockquote>List of groups that mute you are empty</blockquote>"

    return await msg.edit(text)


async def join_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    if len(message.command) < 2:
        return await proses.edit(
            f"{em.gagal}**Please give me link or username group/channel to join!**"
        )
    arg = message.text.split()[1]
    try:
        await client.join_chat(arg)
        return await proses.edit(
            f"{em.sukses}**Succesfully joined chat: {arg}",
            disable_web_page_preview=True,
        )
    except Exception as ex:
        await proses.edit(f"{em.gagal}**Error:** {str(ex)}")
        return


async def kickme_cmd(client, message):
    em = Emoji(client)
    await em.get()
    chat_id = message.chat.id if len(message.command) < 2 else message.text.split()[1]
    status = None
    if chat_id in BLACKLIST_GCAST:
        return await message.edit(f"{em.gagal}**Sorry, you cant leave this group!**")
    try:
        chat_id = int(chat_id)
    except ValueError:
        chat_id = str(chat_id)
    try:
        chat_member = await client.get_chat_member(chat_id, "me")
        if chat_member.status == enums.ChatMemberStatus.ADMINISTRATOR:
            status = "admin"
        elif chat_member.status == enums.ChatMemberStatus.OWNER:
            status = "owner"
        elif chat_member.status == enums.ChatMemberStatus.MEMBER:
            status = "member"
    except Exception as er:
        return await message.edit(f"{em.gagal}**Error:** {str(er)}")
    if status in ["admin", "owner"]:
        return await message.edit(
            f"{em.gagal}**Sorry you cant leave this chat because you as: {status} in this chat.!**"
        )
    else:
        return await client.leave_chat(chat_id)


async def leave_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    no_leave = await dB.get_list_from_var(client.me.id, "NO_LEAVE")
    no_leave.append(-1001818398503)
    no_leave.append(-1001537280879)
    if len(message.command) < 2 and message.command not in [
        "group",
        "channel",
        "global",
        "mute",
    ]:
        return await proses.edit(
            f"{em.gagal}**Please specify command!**\n**Example: `{message.text.split()[0]}` [group, channel, mute or global].**"
        )
    command = message.text.split()[1]
    if command == "mute":
        sukses = await leave_mute(client)
        await proses.delete()
        return await message.reply(
            f"{em.sukses}**Succesfully leaved muted group, succesed: {sukses}**"
        )
    sukses = 0
    arg = 0
    chats = await client.get_chat_id(command)
    for chat in chats:
        if chat in no_leave:
            continue
        try:
            chat_info = await client.get_chat_member(chat, "me")
            user_status = chat_info.status
            if user_status not in (
                enums.ChatMemberStatus.OWNER,
                enums.ChatMemberStatus.ADMINISTRATOR,
            ):
                sukses += 1
                await client.leave_chat(chat)
        except FloodWait as e:
            await asyncio.sleep(e)
            await client.leave_chat(chat)
            sukses += 1
        except Exception:
            arg += 1
    await proses.delete()
    return await message.reply(
        f"{em.sukses}**Succesfully leave {command}, succesed: {sukses} failed: {arg}.**"
    )


async def bl_leave(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    chat_id = message.command[1] if len(message.command) > 1 else message.chat.id
    blacklist = await dB.get_list_from_var(client.me.id, "NO_LEAVE")
    try:
        chat_id = int(chat_id)
    except ValueError:
        return await proses.edit(
            "{}<b>KONTOL KONTOL KALO PAKE NONE PREFIX JANGAN ASAL KETIK GOBLOK\n\n BOT GW YANG EROR ANJ!!!</b>".format(
                em.gagal
            )
        )
    if chat_id in blacklist:
        return await proses.edit(
            f"{em.sukses}**{chat_id} Already in database blacklist leave!**"
        )
    await dB.add_to_var(client.me.id, "NO_LEAVE", chat_id)
    return await proses.edit(
        f"{em.sukses}**Added {chat_id} to database blacklist leave.**"
    )


async def unbl_leave(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    blacklist = await dB.get_list_from_var(client.me.id, "NO_LEAVE")
    try:
        chat_id = (
            int(message.command[1]) if len(message.command) > 1 else message.chat.id
        )
        if chat_id not in blacklist:
            return await proses.edit(
                f"{em.gagal}**{chat_id} Not in database blacklist leave!**"
            )
        await dB.remove_from_var(client.me.id, "NO_LEAVE", chat_id)
        return await proses.edit(
            f"{em.sukses}**Removed {chat_id} from database blacklist leave.**"
        )
    except Exception as error:
        return await proses.edit(str(error))


async def getbl_leave(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    msg = f"{em.sukses} List blacklist leave:\n\n"
    listbc = await dB.get_list_from_var(client.me.id, "NO_LEAVE")
    for num, x in enumerate(listbc, 1):
        try:
            get = await client.get_chat(x)
            msg += f"{num}. {get.title} - {get.id}\n"
        except Exception:
            msg += f"{num}. {x}\n"
    await proses.delete()
    return await message.reply(msg)


async def cleardb_leave(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    get_bls = await dB.get_list_from_var(client.me.id, "NO_LEAVE")
    if not get_bls:
        return await proses.edit(f"{em.gagal}**You dont have blacklist leave!**")
    for x in get_bls:
        await dB.remove_from_var(client.me.id, "NO_LEAVE", x)
    return await proses.edit(
        f"{em.sukses}**Succesfully removed all group in blacklist leave!**"
    )


async def leave_mute(client):
    sukses = 0
    async for dialog in client.get_dialogs():
        if dialog.chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP):
            try:
                member = await client.get_chat_member(dialog.chat.id, client.me.id)
                if member.status == enums.ChatMemberStatus.RESTRICTED:
                    sukses += 1
                    await client.leave_chat(dialog.chat.id)
            except FloodWait as e:
                await asyncio.sleep(e)
                await client.leave_chat(dialog.chat.id)
                sukses += 1
            except Exception:
                continue
    return sukses


async def cc_cmd(client, message):
    em = Emoji(client)
    await em.get()
    reply = message.reply_to_message
    if reply and reply.sender_chat and reply.sender_chat != message.chat.id:
        aan = await message.reply_text(f"{em.gagal}**Please reply to valid user_id!**")
        await asyncio.sleep(0.5)
        return await aan.delete()
    if len(message.command) == 2:
        user = message.text.split(None, 1)[1]
    elif len(message.command) == 1 and reply:
        user = message.reply_to_message.from_user.id
    else:
        aa = await message.reply_text(
            f"{em.gagal}**Please reply to user or give username!**"
        )
        await asyncio.sleep(0.5)
        return await aa.delete()
    await message.delete()
    try:
        return await client.delete_user_history(message.chat.id, user)
    except Exception:
        pass


async def endchat_cmd(client, message):
    em = Emoji(client)
    await em.get()
    reply = message.reply_to_message

    proses = await animate_proses(message, em.proses)
    query = ["bot", "private", "all"]
    if len(message.command) < 2 and not reply:
        return await proses.edit(f"{em.gagal}**Please give query or username!**")
    if len(message.command) == 1 and reply:
        who = reply.from_user.id
        try:
            info = await client.resolve_peer(who)
            await client.invoke(
                raw.functions.messages.DeleteHistory(peer=info, max_id=0, revoke=True)
            )
        except PeerIdInvalid:
            pass
        await message.reply(f"{em.sukses}<b>Succesfully endchat: {who}</b>")
    elif message.command[1] in query:
        target = await client.get_chat_id(message.command[1])
        for ids in target:
            try:
                info = await client.resolve_peer(ids)
                await client.invoke(
                    raw.functions.messages.DeleteHistory(
                        peer=info, max_id=0, revoke=True
                    )
                )
            except PeerIdInvalid:
                continue
            except FloodWait as e:
                await asyncio.sleep(e.value)
                info = await client.resolve_peer(ids)
                await client.invoke(
                    raw.functions.messages.DeleteHistory(
                        peer=info, max_id=0, revoke=True
                    )
                )
        await message.reply(
            f"{em.sukses}**Succesfully endchat: `{message.command[1]}`, total: `{len(target)}`**"
        )
    else:
        who = message.text.split()[1]
        try:
            info = await client.resolve_peer(who)
            await client.invoke(
                raw.functions.messages.DeleteHistory(peer=info, max_id=0, revoke=True)
            )
        except PeerIdInvalid:
            pass
        await message.reply(f"{em.sukses}<b>Succesfully endchat: {who}</b>")
    return await proses.delete()


async def create_cmd(client, message):
    em = Emoji(client)
    await em.get()

    if len(message.command) < 3:
        return await message.reply(
            f"{em.gagal}<b>Please `{message.text.split()[0]}` `gc` to create a group, or `ch` to create a channel.</b>"
        )
    group_type = message.command[1]
    split = message.command[2:]
    group_name = " ".join(split)
    proses = await animate_proses(message, em.proses)
    args = ["gc", "ch"]
    if message.command[1] not in args:
        return await proses.edit(
            f"{em.gagal}<b>Please `{message.text.split()[0]}` `gc` to create a group, or `ch` to create a channel.</b>"
        )
    try:
        desc = "Welcome To My " + ("Group" if group_type == "gc" else "Channel")
        if group_type == "gc":
            _id = await client.create_supergroup(group_name, desc)
            link = await client.get_chat(_id.id)
            return await proses.edit(
                f"{em.sukses}<b>Succesfully created group: [{group_name}]({link.invite_link})</b>",
                disable_web_page_preview=True,
            )
        elif group_type == "ch":
            _id = await client.create_channel(group_name, desc)
            link = await client.get_chat(_id.id)
            return await proses.edit(
                f"{em.sukses}<b>Succesfully created channel: [{group_name}]({link.invite_link})</b>",
                disable_web_page_preview=True,
            )
    except Exception as err:
        return await proses.edit(f"{em.gagal}**ERROR:** {str(err)}")


async def getlink_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    chat_id = message.chat.id if len(message.command) < 2 else message.text.split()[1]
    try:
        link = await client.export_chat_invite_link(chat_id)
        return await proses.edit(
            f"{em.sukses}**This is invite link: {chat_id}\n\n{link}",
            disable_web_page_preview=True,
        )
    except Exception as er:
        return await proses.edit(f"{em.gagal}**ERROR:** `{str(er)}`")


async def cekmember_cmd(client, message):
    em = Emoji(client)
    await em.get()
    chat_id = message.command[1] if len(message.command) > 1 else message.chat.id

    proses = await animate_proses(message, em.proses)
    try:
        member_count = await client.get_chat_members_count(chat_id)
        await asyncio.sleep(1)
        return await proses.edit(
            f"{em.sukses}**Total members in group: {chat_id} is `{member_count}` members.**"
        )
    except Exception as e:
        return await proses.edit(f"{em.gagal}**ERROR:** {str(e)}")


async def cekonline_cmd(client, message):
    em = Emoji(client)
    await em.get()
    chat_id = message.command[1] if len(message.command) > 1 else message.chat.id

    proses = await animate_proses(message, em.proses)
    try:
        member_online = await client.get_chat_online_count(chat_id)
        await asyncio.sleep(1)
        return await proses.edit(
            f"{em.sukses}**Total members online in group: {chat_id} is `{member_online}` members.**"
        )
    except Exception as e:
        return await proses.edit(f"{em.gagal}**ERROR:** {str(e)}")


async def cekmsg_cmd(client, message):
    em = Emoji(client)
    await em.get()

    chat_id = message.chat.id
    user_id = None

    if len(message.command) > 1:
        chat_id = message.command[1] if message.command[1].isdigit() else chat_id
        user_id = message.command[2] if len(message.command) > 2 else message.command[1]
    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id

    if not user_id:
        return await message.reply_text(
            f"{em.gagal}**Please reply to a user or provide a username/ID!**"
        )

    try:
        user = await client.get_users(user_id)
        umention = user.mention
    except (PeerIdInvalid, KeyError):
        return await message.reply_text(
            f"{em.gagal}**Error: PeerIdInvalid or invalid user ID/username.**"
        )

    proses = await animate_proses(message, em.proses)

    try:

        total_msg = await client.search_messages_count(chat_id, from_user=user.id)
        await asyncio.sleep(1)
        await proses.edit(
            f"{em.sukses}**Total messages by {umention} in chat `{chat_id}`: `{total_msg}` messages.**"
        )
    except Exception as e:
        await proses.edit(f"{em.gagal}**Error:** `{str(e)}`")


async def invite_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    users = message.text.split()[1:]
    if not users:
        await proses.edit(f"{em.gagal}<b>Please provide a list of users to invite.</b>")
        return
    chat_id = message.chat.id
    for user in users:
        try:
            await client.add_chat_members(chat_id, user)
            await proses.edit(f"{em.sukses}<b>Succesfully adding {user}</b>")
        except UserNotMutualContact:
            await proses.edit(
                f"{em.gagal}<b>Failed to invite {user}: User not mutual contact.</b>"
            )
        except UserPrivacyRestricted:
            await proses.edit(
                f"{em.gagal}<b>Failed to invite {user}: User privacy restricted.</b>"
            )
        except FloodWait as e:
            await asyncio.sleep(e.value)
            await proses.edit(f"{em.uptime}<b>Flood wait for {e.value} seconds.</b>")
            await client.add_chat_members(chat_id, user)
        except Exception as e:
            await proses.edit(f"{em.gagal}<b>Failed to invite {user}: {str(e)}</b>")
    return


def random_emoji():
    emojis = "🍦 🎈 🎸 🌼 🌳 🚀 🎩 📷 💡 🏄‍♂️ 🎹 🚲 🍕 🌟 🎨 📚 🚁 🎮 🍔 🍉 🎉 🎵 🌸 🌈 🏝️ 🌞 🎢 🚗 🎭 🍩 🎲 📱 🏖️ 🛸 🧩 🚢 🎠 🏰 🎯 🥳 🎰 🛒 🧸 🛺 🧊 🛷 🦩 🎡 🎣 🏹 🧁 🥨 🎻 🎺 🥁 🛹".split(
        " "
    )
    return random.choice(emojis)


async def all_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    botol = await admin_check(message, client.me.id)
    if not botol:
        return await proses.edit(f"{em.gagal}**You are not an admin in this group!**")

    task_id = task.start_task()
    replied = message.reply_to_message
    prefix = client.get_prefix(client.me.id)
    if len(message.command) < 2 and not replied:
        return await proses.edit(f"{em.gagal}**Please reply to text or give text!**")

    await proses.edit(
        f"{em.proses}<i>Task mention running #<code>{task_id}</code>. Type <code>{prefix[0]}cancel {task_id}</code> to cancel mention! Will timeout after 5 minutes.</i>"
    )

    async def tag_members():
        if replied:
            usernum = 0
            usertxt = ""
            try:
                async for m in client.get_chat_members(message.chat.id):
                    if not task.is_active(task_id):
                        return await proses.edit(
                            f"{em.gagal}**Task #{task_id} has been cancelled!**"
                        )

                    if m.user.is_deleted or m.user.is_bot:
                        continue
                    usernum += 1
                    usertxt += f"[{random_emoji()}](tg://user?id={m.user.id}) "
                    if usernum == 7:
                        await replied.reply_text(
                            usertxt,
                            disable_web_page_preview=True,
                        )
                        await asyncio.sleep(1)
                        usernum = 0
                        usertxt = ""
                if usernum != 0:
                    await replied.reply_text(
                        usertxt,
                        disable_web_page_preview=True,
                    )
            except FloodWait as e:
                await asyncio.sleep(e.value)
            finally:
                task.end_task(task_id)
        else:
            try:
                usernum = 0
                usertxt = ""
                text = message.text.split(maxsplit=1)[1]
                async for m in client.get_chat_members(message.chat.id):
                    if m.user.is_deleted or m.user.is_bot:
                        continue
                    if not task.is_active(task_id):
                        await proses.edit(
                            f"{em.gagal}**Task #{task_id} has been cancelled!**"
                        )
                        return
                    usernum += 1
                    usertxt += f"[{random_emoji()}](tg://user?id={m.user.id}) "
                    if usernum == 7:
                        await client.send_message(
                            message.chat.id,
                            f"{text}\n{usertxt}",
                            disable_web_page_preview=True,
                        )
                        await asyncio.sleep(2)
                        usernum = 0
                        usertxt = ""
                if usernum != 0:
                    await client.send_message(
                        message.chat.id,
                        f"<b>{text}</b>\n\n{usertxt}",
                        disable_web_page_preview=True,
                    )
            except FloodWait as e:
                await asyncio.sleep(e.value)
            finally:
                task.end_task(task_id)

    try:
        await asyncio.wait_for(tag_members(), timeout=300)  # 300 seconds = 5 minutes
    except asyncio.TimeoutError:
        task.end_task(task_id)
        await proses.edit(f"{em.gagal}**Task #{task_id} timed out after 5 minutes!**")
        return

    return await proses.delete()


async def tagadmins_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    task_id = task.start_task()
    replied = message.reply_to_message
    prefix = client.get_prefix(client.me.id)
    if not replied and len(message.text.split()) == 1:
        return await proses.edit(f"{em.gagal}**Please reply to text or give text!**")
    await proses.edit(
        f"{em.proses}<i>Task mention running #<code>{task_id}</code>. Type <code>{prefix[0]}cancel {task_id}</code> to cancel mention!</i>"
    )
    if replied:
        usernum = 0
        usertxt = ""
        try:
            async for m in client.get_chat_members(
                message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS
            ):
                if not task.is_active(task_id):
                    return await proses.edit(
                        f"{em.gagal}**Task #{task_id} has been cancelled!**"
                    )
                if m.user.is_deleted or m.user.is_bot:
                    continue
                usernum += 1
                usertxt += f"[{random_emoji()}](tg://user?id={m.user.id})  "
                if usernum == 7:
                    await replied.reply_text(
                        usertxt,
                        disable_web_page_preview=True,
                    )
                    await asyncio.sleep(1)
                    usernum = 0
                    usertxt = ""
            if usernum != 0:
                await replied.reply_text(
                    usertxt,
                    disable_web_page_preview=True,
                )
        except FloodWait as e:
            await asyncio.sleep(e.value)
        finally:
            task.end_task(task_id)
    else:
        usernum = 0
        usertxt = ""
        try:
            text = message.text.split(maxsplit=1)[1]
            async for m in client.get_chat_members(
                message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS
            ):
                if not task.is_active(task_id):
                    return await proses.edit(
                        f"{em.gagal}**Task #{task_id} has been cancelled!**"
                    )
                if m.user.is_deleted or m.user.is_bot:
                    continue
                usernum += 1
                usertxt += f"[{random_emoji()}](tg://user?id={m.user.id}) "
                if usernum == 7:
                    await client.send_message(
                        message.chat.id,
                        f"{text}\n{usertxt}",
                        disable_web_page_preview=True,
                    )
                    await asyncio.sleep(2)
                    usernum = 0
                    usertxt = ""
            if usernum != 0:
                await client.send_message(
                    message.chat.id,
                    f"<b>{text}</b>\n\n{usertxt}",
                    disable_web_page_preview=True,
                )
        except FloodWait as e:
            await asyncio.sleep(e.value)
        finally:
            task.end_task(task_id)
    return await proses.delete()


async def inviteall_cmd(client, message):
    em = Emoji(client)
    await em.get()

    proses = await animate_proses(message, em.proses)
    if len(message.command) < 2:
        return await proses.edit(
            f"{em.gagal}**Invalid command, Example: `{message.text.split()[0]} @disinialice`"
        )
    source_chat_username = message.command[1]
    try:
        source_chat = await client.get_chat(source_chat_username)
        target_chat = message.chat
    except Exception:
        return await proses.edit(
            f"{em.gagal}**ERROR**: {traceback.format_exc()}\n**Maybe you need interact chat.**"
        )

    status_msg = await proses.edit(
        f"{em.proses}**Trying to invite members from** `{source_chat_username}` **to** `{target_chat.title}`"
    )
    invited = 0
    skipped = 0
    total = 0

    async for member in client.get_chat_members(source_chat.id):
        user = member.user
        total += 1

        if user.is_bot or user.is_deleted:
            skipped += 1
            continue

        try:
            await client.add_chat_members(target_chat.id, user.id)
            invited += 1
            await asyncio.sleep(2)

        except (UserAlreadyParticipant, UserPrivacyRestricted):
            skipped += 1

        except PeerFlood:
            await status_msg.edit(
                f"{em.gagal}**Process terminated!! Because your account is currently limited**"
            )
            break

        except FloodWait as e:
            await status_msg.edit(
                f"{em.proses}**FloodWait {e.value} seconds, waiting.**"
            )
            await asyncio.sleep(e.value)

        except Exception:
            skipped += 1
            await asyncio.sleep(1)

    return await status_msg.edit(
        f"{em.sukses}**Process done.\nUser total: `{total}`\nSuccesed: `{invited}`\nSkipped: `{skipped}`**"
    )


async def force_del_cmd(client, message):
    data = await dB.get_var(client.me.id, "FORCE_DEL") or []
    if not data:
        return
    user = message.from_user if message.from_user else message.sender_chat
    target = next((i for i in data if user.id == int(i["target"])), None)
    if target:
        # print(f"Target deleter: {target}")
        try:
            await client.delete_messages(message.chat.id, message.id)
        except Exception:
            print(f"Eror deleted: {traceback.format_exc()}")


async def deleter_cmd(client, message):
    em = Emoji(client)
    await em.get()
    if message.command[0] == "dmute":
        reply = message.reply_to_message
        try:
            target = reply.from_user.id if reply else message.text.split()[1]
        except (AttributeError, IndexError):
            return await message.reply(
                f"{em.gagal}<b>You need to specify a user (either by reply or username/ID)!</b>"
            )
        try:
            user = await client.get_users(target)
        except (PeerIdInvalid, KeyError, UsernameInvalid, UsernameNotOccupied):
            return await message.reply(
                f"{em.gagal}<b>You need meet before interact!!</b>"
            )
        mention = user.mention
        user_id = user.id
        title = message.chat.title
        if user_id == client.me.id or user_id in DEVS:
            return await message.reply_text(f"{em.gagal}<b>Go to the heal now!!</b>")
        data = await dB.get_var(client.me.id, "FORCE_DEL") or []
        target = next((i for i in data if user_id == int(i["target"])), None)
        if target:
            return await message.reply(f"**User {mention} already dmuted.**")
        added = {
            "chat_id": message.chat.id,
            "title": title,
            "target": user_id,
            "mention": mention,
        }
        data.append(added)
        await dB.set_var(client.me.id, "FORCE_DEL", data)
        return await message.reply(f"**Dmuted user: {mention}.**")
    elif message.command[0] == "undmute":
        data = await dB.get_var(client.me.id, "FORCE_DEL") or []
        if len(message.command) < 2:
            return await message.reply(f"**Please give me number for delete**")
        try:
            value = int(message.command[1])
        except Exception:
            return await message.reply(f"**Please give me number for delete**")
        try:
            value = int(value) - 1
            data.pop(value)
            await dB.set_var(client.me.id, "FORCE_DEL", data)
            return await message.reply(f"**Deleted number: `{value+1}`.**")
        except Exception as error:
            return await message.reply(f"**Error:** {str(error)}")
    elif message.command[0] == "getdmute":
        data = await dB.get_var(client.me.id, "FORCE_DEL") or []
        if not data:
            return await message.reply("**Ups, maybe you haven't added a user**")
        msg = ""
        for count, name in enumerate(data, 1):
            msg += f"**{count}. {name.get('title')} | {name.get('mention')}**\n"
        return await message.reply(msg)
