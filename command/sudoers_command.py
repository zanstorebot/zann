from pyrogram.errors import PeerIdInvalid

from database import dB
from helpers import Emoji, animate_proses


async def addsudo_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    pros = await animate_proses(message, emo.proses)
    user_id = await client.extract_user(message)
    if not user_id:
        return await pros.edit(
            f"{emo.gagal}<b>Please reply to message from user or give username</b>"
        )

    try:
        user = await client.get_users(user_id)
    except Exception as error:
        return await pros.edit(f"{emo.gagal}<b>Error:\n\n<code>{error}</code></b>")

    sudo_users = await dB.get_list_from_var(client.me.id, "SUDOERS")

    if user.id in sudo_users:
        return await pros.edit(
            f"{emo.gagal}<b>[{user.first_name} {user.last_name or ''}](tg://user?id={user.id}) Already in sudoers.</b>"
        )

    try:
        await dB.add_to_var(client.me.id, "SUDOERS", user.id)
        return await pros.edit(
            f"{emo.sukses}<b>[{user.first_name} {user.last_name or ''}](tg://user?id={user.id}) Succesfully add to sudo users.</b>"
        )
    except Exception as error:
        return await pros.edit(f"{emo.gagal}<b>Error:\n\n<code>{error}</code></b>")


async def delsudo_cmd(client, message):
    emo = Emoji(client)
    await emo.get()

    pros = await animate_proses(message, emo.proses)
    sudo_users = await dB.get_list_from_var(client.me.id, "SUDOERS")

    if len(message.command) > 1 and message.command[1] == "all":
        for user in sudo_users:
            await dB.remove_from_var(client.me.id, "SUDOERS", user)
        return await pros.edit(f"{emo.sukses}<b>Successfully deleted all sudoers.</b>")

    user_id = await client.extract_user(message)
    if not user_id:
        return await pros.edit(
            f"{emo.gagal}<b>Please reply to a message from the user or provide a username.</b>"
        )
    if user_id not in sudo_users:
        return await pros.edit(f"{emo.gagal}<b>User {user_id} is not in sudoers.</b>")

    try:
        await dB.remove_from_var(client.me.id, "SUDOERS", user_id)
        return await pros.edit(
            f"{emo.sukses}<b>Successfully deleted user {user_id} from sudoers.</b>"
        )
    except Exception as error:
        return await pros.edit(f"{emo.gagal}<b>Error:\n\n<code>{error}</code></b>")


async def sudolist_cmd(client, message):
    emo = Emoji(client)
    await emo.get()

    pros = await animate_proses(message, emo.proses)

    sudo_users = await dB.get_list_from_var(client.me.id, "SUDOERS")

    if not sudo_users:
        return await pros.edit(f"{emo.gagal}<b>You dont have sudoers.</b>")

    sudo_list = []
    teks = "<b>❒ List of Sudoers:</b>\n"

    for index, user_id in enumerate(sudo_users, 1):
        try:
            user = await client.get_users(int(user_id))
            user_name = f"{user.first_name} {user.last_name or ''}".strip()

            prefix = "┖" if index == len(sudo_users) else "┣"
            sudo_list.append(
                f"{prefix} [{user_name}](tg://user?id={user_id}) | <code>{user_id}</code>"
            )
        except PeerIdInvalid:
            await dB.remove_from_var(client.me.id, "SUDOERS", user_id)
        except Exception as e:
            return await pros.edit(
                f"{emo.gagal}<b>Error when get sudoers:</b>\n<code>{str(e)}</code>"
            )

    if not sudo_list:
        return await pros.edit(
            f"{emo.gagal}<b>All user has been deleted because error when get sudoers.</b>"
        )
    response = teks + "\n".join(sudo_list)
    return await pros.edit(f"<b>{response}</b>")
