import asyncio
import os

from pyrogram import enums
from pyrogram.errors import (FloodWait, PeerIdInvalid, UsernameInvalid,
                             UsernameNotOccupied)
from pyrogram.types import ChatPermissions, ChatPrivileges

from config import DEVS
from helpers import Emoji, animate_proses


async def staff_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    chat = message.chat
    if chat.username:
        uname = chat.username
    else:
        uname = chat.id
    owner = []
    co_founder = []
    admin = []
    bot = []
    pros = await animate_proses(message, emo.proses)
    await asyncio.sleep(1)
    if uname:
        chat_link = f"<a href='t.me/{uname}'>{chat.title}</a>"
    else:
        chat_link = f"<a href='{message.link}'>{chat.title}</a>"
    async for dia in client.get_chat_members(chat.id):
        user = dia.user
        ijin = dia.privileges
        status = dia.status
        title = dia.custom_title
        botol = user.is_bot
        mention = f"<a href=tg://user?id={user.id}>{user.first_name or ''} {user.last_name or ''}</a>"
        if (
            status == enums.ChatMemberStatus.ADMINISTRATOR
            and ijin.can_promote_members
            and ijin.can_manage_chat
            and ijin.can_delete_messages
            and ijin.can_manage_video_chats
            and ijin.can_restrict_members
            and ijin.can_change_info
            and ijin.can_invite_users
            and ijin.can_pin_messages
            and not botol
        ):
            if title:
                co_founder.append(f" ┣ {mention} <u>as</u> <i>{title}</i>")
            else:
                co_founder.append(f" ┣ {mention} <u>as</u> <i>Co-Founder</i>")
        elif status == enums.ChatMemberStatus.ADMINISTRATOR and not botol:
            if title:
                admin.append(f" ┣ {mention} <u>as</u> <i>{title}</i>")
            else:
                admin.append(f" ┣ {mention} <u>as</u> <i>Admin</i>")
        elif status == enums.ChatMemberStatus.OWNER:
            if title:
                owner.append(f" ┣ {mention} <u>as</u> <i>{title}</i>")
            else:
                owner.append(f" ┣ {mention} <u>as</u> <i>Founder</i>")
        elif botol:
            if title:
                bot.append(f" ┣ {mention} <u>as</u> <i>{title}</i>")
            else:
                bot.append(f" ┣ {mention} <u>as</u> <i>Bot Admin</i>")

    result = "<b>Administrator Structure in {}</b>\n\n\n".format(chat_link)
    if owner:
        on = owner[-1].replace(" ┣", "┗")
        owner.pop(-1)
        owner.append(on)
        result += "<b>👑 Founder : </b>\n ┃\n {}\n\n".format(owner[0])
    if co_founder:
        cof = co_founder[-1].replace(" ┣", " ┗")
        co_founder.pop(-1)
        co_founder.append(cof)
        result += "<b>👨🏻‍💻 Co-Founder : </b>\n ┃\n" + "\n".join(co_founder) + "\n\n"
    if admin:
        adm = admin[-1].replace(" ┣", " ┗")
        admin.pop(-1)
        admin.append(adm)
        result += "<b>🧑🏻‍💻 Admin : </b>\n ┃\n" + "\n".join(admin) + "\n\n"
    if bot:
        botak = bot[-1].replace(" ┣", " ┗")
        bot.pop(-1)
        bot.append(botak)
        result += "<b>🤖 Bots : </b>\n ┃\n" + "\n".join(bot) + "\n"

    photo_path = None
    if message.chat.photo:
        try:
            photo_path = await client.download_media(message.chat.photo.big_file_id)
            await client.send_photo(
                message.chat.id,
                photo=photo_path,
                caption=f"{result}",
            )
        except Exception as e:
            print(f"Error sending media: {str(e)}")
            await message.reply(f"{result}", disable_web_page_preview=True)
    else:
        await message.reply(f"{result}", disable_web_page_preview=True)

    if photo_path and os.path.exists(photo_path):
        os.remove(photo_path)

    return await pros.delete()


async def admin_check(message, user_id):
    c = message._client
    status = (await c.get_chat_member(message.chat.id, user_id)).status
    admins = [enums.ChatMemberStatus.ADMINISTRATOR, enums.ChatMemberStatus.OWNER]
    if status not in admins:
        return False
    return True


async def member_check(message, user_id):
    client = message._client
    check_user = (await client.get_chat_member(message.chat.id, user_id)).privileges
    user_type = check_user.status
    if user_type == enums.ChatMemberStatus.MEMBER:
        return False
    if user_type == enums.ChatMemberStatus.ADMINISTRATORS:
        add_adminperm = check_user.can_promote_members
        return bool(add_adminperm)
    return True


async def purgeme_cmd(client, message):
    em = Emoji(client)
    await em.get()
    if len(message.command) != 2:
        return await message.delete()
    n = (
        message.reply_to_message
        if message.reply_to_message
        else message.text.split(None, 1)[1].strip()
    )
    if not n.isnumeric():
        return await message.delete()
    n = int(n)
    if n < 1:
        return await message.delete()
    chat_id = message.chat.id
    message_ids = [
        message.id
        async for message in client.search_messages(
            chat_id,
            from_user=int(message.from_user.id),
            limit=n,
        )
    ]
    if not message_ids:
        return
    to_delete = [message_ids[i : i + 999] for i in range(0, len(message_ids), 999)]
    for hundred_messages_or_less in to_delete:
        return await client.delete_messages(
            chat_id=chat_id,
            message_ids=hundred_messages_or_less,
            revoke=True,
        )


async def purge_cmd(client, message):
    rep = message.reply_to_message
    if not rep:
        return await message.delete()

    chat_id = message.chat.id
    try:
        start_id = rep.id
        end_id = message.id
        message_ids = list(range(start_id, end_id))
        for i in range(0, len(message_ids), 100):
            await client.delete_messages(
                chat_id=chat_id, message_ids=message_ids[i : i + 100], revoke=True
            )
    except Exception:
        await message.delete()
    finally:
        await message.delete()


async def kick_cmd(client, message):
    em = Emoji(client)
    await em.get()
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
        return await message.reply(f"{em.gagal}<b>You need meet before interact!!</b>")

    mention = user.mention
    user_id = user.id
    if user_id == client.me.id or user_id in DEVS:
        return await message.reply_text(f"{em.gagal}<b>Go to the heal now!!</b>")

    msg = f"{em.warn}<b>Kicked user {mention}</b>"
    if message.command[0][0] == "d":
        await message.reply_to_message.delete()
        await message.delete()
    try:
        await message.chat.ban_member(user_id)
    except Exception as er:
        return await message.reply_text(f"{em.gagal}**ERROR:** {str(er)}")
    teks = await message.reply_text(msg)
    await asyncio.sleep(1)
    await teks.delete()
    return await message.chat.unban_member(user_id)


async def ban_cmd(client, message):
    em = Emoji(client)
    await em.get()

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
        return await message.reply(f"{em.gagal}<b>You need meet before interact!!</b>")
    mention = user.mention
    user_id = user.id
    if user_id == client.me.id or user_id in DEVS:
        return await message.reply_text(f"{em.gagal}<b>Go to the heal now!!</b>")

    if message.command[0] == "unban":
        try:
            await message.chat.unban_member(user_id)
        except Exception as er:
            return await message.reply_text(f"{em.gagal}**ERROR:** {str(er)}")
        teks = await message.reply_text(f"{em.sukses}<b>Unbanned: {mention}!</b>")
        await asyncio.sleep(1)
        return await teks.delete()
    else:
        msg = f"{em.block}<b>Banned user {mention}</b>"
        if message.command[0][0] == "d":
            await message.reply_to_message.delete()
            await message.delete()
        try:
            await message.chat.ban_member(user_id)
        except Exception as er:
            return await message.reply_text(f"{em.gagal}**ERROR:** {str(er)}")
        teks = await message.reply_text(msg)
        await asyncio.sleep(1)
        return await teks.delete()


async def del_cmd(client, message):
    await message.delete()
    try:
        return await message.reply_to_message.delete()
    except Exception:
        return


async def pin_cmd(client, message):
    em = Emoji(client)
    await em.get()
    if not message.reply_to_message:
        return await message.reply_text(f"{em.gagal}**Please reply to message!**")
    r = message.reply_to_message
    if message.command[0][0] == "u":
        await r.unpin()
        return await message.reply_text(
            f"{em.sukses}<b>Unpinned [this]({r.link}) message!</b>",
            disable_web_page_preview=True,
        )
    if message.chat.type == enums.ChatType.PRIVATE:
        await r.pin(disable_notification=False, both_sides=True)
    else:
        await r.pin(
            disable_notification=False,
        )
    return await message.reply(
        f"{em.sukses}<b>Pinned [this]({r.link}) message!</b>",
        disable_web_page_preview=True,
    )


async def mute_cmd(client, message):
    em = Emoji(client)
    await em.get()

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
        return await message.reply(f"{em.gagal}<b>You need meet before interact!!</b>")
    mention = user.mention
    user_id = user.id
    if user_id == client.me.id or user_id in DEVS:
        return await message.reply_text(f"{em.gagal}<b>Go to the heal now!!</b>")

    if message.command[0] == "unmute":
        try:
            await message.chat.unban_member(user_id)
            teks = await message.reply_text(f"{em.block}<b>Unmuted user {mention}</b>")
            await asyncio.sleep(1)
            return await teks.delete()
        except Exception as er:
            return await message.reply_text(f"{em.gagal}**ERROR:** {str(er)}")
    else:
        msg = f"{em.block}<b>Muted user {mention}</b>"
        if message.command[0][0] == "d":
            await message.reply_to_message.delete()
            await message.delete()
        try:
            await message.chat.restrict_member(user_id, permissions=ChatPermissions())
            teks = await message.reply_text(msg)
            await asyncio.sleep(1)
            return await teks.delete()
        except Exception as er:
            return await message.reply_text(f"{em.gagal}**ERROR:** {str(er)}")


async def zombies_cmd(client, message):
    em = Emoji(client)
    await em.get()
    chat_id = message.chat.id
    deleted_users = []
    banned_users = 0
    failed = 0
    mt = await animate_proses(message, em.proses)

    async for i in client.get_chat_members(chat_id):
        if i.user.is_deleted:
            deleted_users.append(i.user.id)
    if len(deleted_users) > 0:
        for deleted_user in deleted_users:
            try:
                await message.chat.ban_member(deleted_user)
                banned_users += 1
            except FloodWait as e:
                await asyncio.sleep(e.value)
                await mt.edit(f"**FloodWait waiting for `{e.value}` seconds!**")
            except Exception:
                failed += 1
        return await mt.edit(
            f"{em.sukses}**Succesfuly banned deleted account: `{banned_users}`, failed: `{failed}`"
        )
    else:
        return await mt.edit(f"{em.gagal}**No deleted accounts here!**")


async def report_cmd(client, message):
    em = Emoji(client)
    await em.get()
    if not message.reply_to_message:
        return await message.reply_text(f"{em.gagal}**Please reply to message!**")

    reply = message.reply_to_message
    reply_id = reply.from_user.id if reply.from_user else reply.sender_chat.id
    user_id = message.from_user.id if message.from_user else message.sender_chat.id
    if reply_id == user_id:
        return await message.reply_text(
            f"{em.gagal}**Please reply to message to member!**"
        )

    list_of_admins = await admin_check(message, user_id)
    linked_chat = (await client.get_chat(message.chat.id)).linked_chat
    if linked_chat is not None:
        if (
            list_of_admins is True
            and reply_id == message.chat.id
            or reply_id == linked_chat.id
        ):
            return await message.reply_text(
                f"{em.gagal}**Please reply to message to member!**"
            )
    else:
        if list_of_admins is True and reply_id == message.chat.id:
            return await message.reply_text(
                f"{em.gagal}**Please reply to message to member!**"
            )

    user_mention = (
        reply.from_user.mention if reply.from_user else reply.sender_chat.title
    )
    text = f"{em.warn}<b>Reported to admins, user: {user_mention}!</b>"
    admin_data = [
        i
        async for i in client.get_chat_members(
            chat_id=message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS
        )
    ]
    for admin in admin_data:
        if admin.user.is_bot or admin.user.is_deleted:
            continue
        text += f"[\u2063](tg://user?id={admin.user.id})"
    return await message.reply_to_message.reply_text(text)


async def promote_cmd(client, message):
    em = Emoji(client)
    await em.get()
    command = message.command[0]

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
        return await message.reply(f"{em.gagal}<b>You need meet before interact!!</b>")
    user.mention
    user_id = user.id

    if user_id == client.me.id:
        return await message.reply_text(
            f"{em.gagal}**Please reply to message to member!**"
        )

    # Check admin rights
    if command != "demote":
        is_right = await client.get_chat_member(message.chat.id, client.me.id)
        if not is_right.privileges.can_promote_members:
            return await message.reply_text(
                f"{em.gagal}**You don't have the right to promote members in this group!**"
            )
    else:
        botol = await admin_check(message, client.me.id)
        if not botol:
            return await message.reply_text(
                f"{em.gagal}**You are not an admin in this group!**"
            )
        is_admin = await admin_check(message, user_id)
        if not is_admin:
            return await message.reply_text(f"{em.gagal}**Yes they are still member!**")

    try:
        if message.chat.type in [enums.ChatType.SUPERGROUP, enums.ChatType.GROUP]:
            if len(message.text.split()) >= 3 and not message.reply_to_message:
                title = " ".join(message.text.split()[2:16])
            elif len(message.text.split()) >= 2 and message.reply_to_message:
                title = " ".join(message.text.split()[1:16])
            else:
                title = f"{user.first_name}"
            if command in ["promote", "fullpromote"]:

                privileges = ChatPrivileges(
                    can_manage_chat=True,
                    can_delete_messages=True,
                    can_manage_video_chats=True,
                    can_restrict_members=True,
                    can_promote_members=command == "fullpromote",
                    can_change_info=command == "fullpromote",
                    can_post_messages=command == "fullpromote",
                    can_edit_messages=command == "fullpromote",
                    can_manage_topics=command == "fullpromote",
                    can_post_stories=command == "fullpromote",
                    can_edit_stories=command == "fullpromote",
                    can_delete_stories=command == "fullpromote",
                    can_invite_users=True,
                    can_pin_messages=True,
                    is_anonymous=False,
                )

                await client.promote_chat_member(
                    chat_id=message.chat.id,
                    user_id=user_id,
                    privileges=privileges,
                    title=title,
                )
                # await client.set_administrator_title(message.chat.id, user_id, title)

                return await message.reply_text(
                    f"{em.sukses}<b>Successfully promoted user {user.mention} to admin!</b>"
                )

            else:  # demote
                await client.promote_chat_member(
                    chat_id=message.chat.id,
                    user_id=user_id,
                    privileges=ChatPrivileges(
                        can_change_info=False,
                        can_invite_users=False,
                        can_delete_messages=False,
                        can_restrict_members=False,
                        can_pin_messages=False,
                        can_promote_members=False,
                        can_manage_chat=False,
                        can_manage_video_chats=False,
                    ),
                )
                return await message.reply_text(
                    f"{em.sukses}<b>Successfully demoted user {user.mention} from admin!</b>"
                )
    except Exception as er:
        return await message.reply_text(f"{em.gagal}**ERROR:** {str(er)}")


async def group_cmd(client, message):
    em = Emoji(client)
    await em.get()
    prefix = next(iter(client.get_prefix(client.me.id)))

    if len(message.text.split()) == 1 and not message.reply_to_message:
        return await message.reply(
            f"{em.gagal}**Please provide command specifications!**"
        )

    command = message.command[0]

    try:
        if command == "group":
            return await handle_group_command(client, message, em, prefix)
        elif command == "title":
            return await handle_title_command(client, message, em, prefix)
        else:
            await message.reply(f"{em.gagal}**Please provide command specifications!**")
    except Exception as e:
        await message.reply(f"{em.gagal}**ERROR: `{str(e)}`**")


async def handle_group_command(client, message, em, prefix):
    if len(message.command) < 2:
        return await message.reply(
            f"{em.gagal}**Please provide command specifications! Example: `{prefix}group [desc or title]` [text here or reply to text]!**"
        )

    query = message.command[1]
    valid_queries = ["desc", "title", "media"]

    if query not in valid_queries:
        return await message.reply(
            f"{em.gagal}**Please provide command specifications! Example: `{prefix}group [desc or title]` [text here or reply to text]!**"
        )

    reply = message.reply_to_message
    content = None

    if query in ["desc", "title"]:
        if reply:
            content = reply.text or reply.caption
        elif len(message.command) > 2:
            content = message.text.split(None, 2)[2]

        if not content:
            return await message.reply(
                f"{em.gagal}**Please give me description to set. Example: `{prefix}group [desc or title]` [text here or reply to text]!**"
            )

        chat = await client.get_chat(message.chat.id)

        if query == "desc":
            await message.chat.set_description(content)
            return await message.reply(
                f"{em.sukses}**Successfully set description group: `{chat.description}` to: `{content}`**"
            )
        else:  # title
            await message.chat.set_title(content)
            return await message.reply(
                f"{em.sukses}**Successfully set title group: `{chat.title}` to: `{content}`**"
            )

    else:  # media
        if not reply or not (reply.photo or reply.video):
            return await message.reply(f"{em.gagal}**Please reply to photo or video**")

        media = reply.photo or reply.video
        kwargs = {"photo": media.file_id} if reply.photo else {"video": media.file_id}
        await client.set_chat_photo(message.chat.id, **kwargs)
        return await message.reply(
            f"{em.sukses}<b>Successfully changed [media]({reply.link}) to profile group!</b>",
            disable_web_page_preview=True,
        )


async def handle_title_command(client, message, em, prefix):
    reply = message.reply_to_message
    user_id = None
    title = None
    if reply:
        user_id = reply.from_user.id
        if len(message.command) > 1:
            title = message.text.split(None, 1)[1]
    elif len(message.command) > 2:
        user_id = message.text.split()[1]
        title = message.text.split(None, 2)[2]

    if not all([user_id, title]):
        return await message.reply(
            f"{em.gagal}**Please give me title to set. Example: `{prefix}title [user_id] [title]` or reply to user with title!**"
        )

    try:
        user = await client.get_users(user_id)
        current_title = (
            await client.get_chat_member(message.chat.id, user.id)
        ).custom_title
        mention = user.mention
        await client.set_administrator_title(message.chat.id, user.id, title)
        return await message.reply(
            f"{em.sukses}<b>Successfully set title user: {mention} `{current_title}` to: `{title}`</b>"
        )
    except Exception as e:
        return await message.reply(f"{em.gagal}**ERROR: `{str(e)}`**")
