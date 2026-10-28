import asyncio

from pyrogram import enums

from config import API_MAELYN
from database import dB
from helpers import Emoji, Tools, animate_proses, task


async def mail_cmd(client, message):
    em = Emoji(client)
    await em.get()
    prs = await animate_proses(message, em.proses)
    command = client.get_text(message)
    if not command:
        return await prs.edit(
            f"{em.gagal}**Please give query. Example: `{message.text.split()[0]} gen` (for generate mail) or `{message.text.split()[0]} otp` (for get otp)"
        )
    try:
        if message.command[1] == "gen":
            url = f"https://api.maelyn.sbs/api/tempmail/generate?apikey={API_MAELYN}"
            response = await Tools.fetch.get(url)
            if response.status_code == 200:
                data = response.json()["result"]
                await dB.set_var(client.me.id, "ID_MAIL", data.get("id_inbox"))
                return await prs.edit(
                    f"{em.sukses}**Here your temp mail**\n\n**Email**: {data.get('email')}\n**ID**: `{data.get('id_inbox')}`"
                )
            else:
                return await prs.edit(f"{em.gagal}**ERROR**: {response.status_code}")
        elif message.command[1] == "otp":
            if len(message.command) > 2:
                ids = message.command[2]
                url = f"https://api.maelyn.sbs/api/tempmail/inbox?id_inbox={ids}&apikey={API_MAELYN}"
                response = await Tools.fetch.get(url)
                if response.status_code == 200:
                    data = response.json()["result"]
                    inbox_data = data["inbox"]

                    inbox_text = ""
                    if inbox_data:
                        for idx, mail in enumerate(inbox_data, 1):
                            inbox_text += f"\n - **Mail {idx}**:\n"
                            inbox_text += (
                                f"**Sender**: {mail.get('senderName', 'N/A')}\n"
                            )
                            inbox_text += f"**From**: {mail.get('from', 'N/A')}\n"
                            inbox_text += f"**Subject**: {mail.get('subject', 'N/A')}\n"
                            inbox_text += (
                                f"**Message**: {mail.get('textBody', 'N/A')}\n"
                            )
                            inbox_text += f"**Received**: <t:{int(mail.get('receivedAt', 0)/1000)}:F>\n"
                    else:
                        inbox_text = "[]"

                    return await prs.edit(
                        f"{em.sukses}**Email**: {data.get('email')}\n"
                        f"**ID**: `{data.get('id_inbox')}`\n"
                        f"**Inbox**: {inbox_text}"
                    )
                else:
                    return await prs.edit(
                        f"{em.gagal}**ERROR**: {response.status_code}"
                    )
            else:
                ids = await dB.get_var(client.me.id, "ID_MAIL")
                if not ids:
                    return await prs.edit(f"{em.gagal}**Please give id temp mail!!**")

                url = f"https://api.maelyn.sbs/api/tempmail/inbox?id_inbox={str(ids)}&apikey={API_MAELYN}"
                response = await Tools.fetch.get(url)
                if response.status_code == 200:
                    data = response.json()["result"]
                    inbox_data = data["inbox"]

                    inbox_text = ""
                    if inbox_data:
                        for idx, mail in enumerate(inbox_data, 1):
                            inbox_text += f" - **Mail {idx}**:\n"
                            inbox_text += (
                                f"**Sender**: {mail.get('senderName', 'N/A')}\n"
                            )
                            inbox_text += f"**From**: {mail.get('from', 'N/A')}\n"
                            inbox_text += f"**Subject**: {mail.get('subject', 'N/A')}\n"
                            inbox_text += (
                                f"**Message**: {mail.get('textBody', 'N/A')}\n"
                            )
                            inbox_text += f"**Received**: <t:{int(mail.get('receivedAt', 0)/1000)}:F>\n"
                    else:
                        inbox_text = "[]"

                    return await prs.edit(
                        f"{em.sukses}**Email**: {data.get('email')}\n"
                        f"**ID**: `{data.get('id_inbox')}`\n"
                        f"**Inbox**: {inbox_text}"
                    )
                else:
                    return await prs.edit(
                        f"{em.gagal}**ERROR**: {response.status_code}"
                    )
        else:
            return await prs.edit(
                f"{em.gagal}**Please give query. Example: `{message.text.split()[0]} gen` (for generate mail) or `{message.text.split()[0]} otp` (for get otp)"
            )
    except Exception as er:
        return await prs.edit(f"{em.gagal}**ERROR**: {str(er)}")


async def send_action_for_duration(
    message, emo, proses, task_id, chat_id, action, duration, interval=5
):
    client = message._client
    loop = asyncio.get_event_loop()
    end_time = loop.time() + duration

    try:
        while task.is_active(task_id) and loop.time() < end_time:
            try:
                await client.send_chat_action(chat_id=chat_id, action=action)
            except Exception as e:
                await proses.edit(
                    f"{emo.gagal}Terjadi kesalahan saat mengirim aksi: {e}"
                )
                break
            await asyncio.sleep(interval)
    finally:
        await client.send_chat_action(chat_id=chat_id, action=enums.ChatAction.CANCEL)
        task.end_task(task_id)
        return


async def ftype_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    await message.delete()

    turu = client.get_text(message)
    try:
        turu = int(turu)
        if turu <= 0 or turu > 86400:
            raise ValueError("Durasi tidak valid.")
    except ValueError:
        turu = 3600
    proses_ = await emo.get_costum_text()
    proses = await message.reply(f"{emo.proses}**{proses_[4]}**")
    chat_id = message.chat.id

    try:
        task_id = task.start_task()
    except Exception as e:
        return await proses.edit(f"{emo.gagal}**Failed started task:** {e}")

    prefix = client.get_prefix(client.me.id)
    await proses.edit(
        f"{emo.proses}<i>Task {message.command[0]} running #<code>{task_id}</code>. Type <code>{prefix[0]}cancel {task_id}</code> to stop {message.command[0]}!</i>"
    )
    return await send_action_for_duration(
        message, emo, proses, task_id, chat_id, enums.ChatAction.TYPING, turu
    )


async def fvoice_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    await message.delete()
    turu = client.get_text(message)

    try:
        turu = int(turu)
        if turu <= 0 or turu > 86400:
            raise ValueError("Durasi tidak valid.")
    except ValueError:
        turu = 3600
    proses_ = await emo.get_costum_text()
    proses = await message.reply(f"{emo.proses}**{proses_[4]}**")
    chat_id = message.chat.id

    try:
        task_id = task.start_task()
    except Exception as e:
        return await proses.edit(f"{emo.gagal}**Failed started task:** {e}")

    prefix = client.get_prefix(client.me.id)
    await proses.edit(
        f"{emo.proses}<i>Task {message.command[0]} running #<code>{task_id}</code>. Type <code>{prefix[0]}cancel {task_id}</code> to stop {message.command[0]}!</i>"
    )
    return await send_action_for_duration(
        message, emo, proses, task_id, chat_id, enums.ChatAction.RECORD_AUDIO, turu
    )


async def fvideo_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    await message.delete()
    turu = client.get_text(message)

    try:
        turu = int(turu)
        if turu <= 0 or turu > 86400:
            raise ValueError("Durasi tidak valid.")
    except ValueError:
        turu = 3600
    proses_ = await emo.get_costum_text()
    proses = await message.reply(f"{emo.proses}**{proses_[4]}**")
    chat_id = message.chat.id

    try:
        task_id = task.start_task()
    except Exception as e:
        return await proses.edit(f"{emo.gagal}**Failed started task:** {e}")

    prefix = client.get_prefix(client.me.id)
    await proses.edit(
        f"{emo.proses}<i>Task {message.command[0]} running #<code>{task_id}</code>. Type <code>{prefix[0]}cancel {task_id}</code> to stop {message.command[0]}!</i>"
    )
    return await send_action_for_duration(
        message, emo, proses, task_id, chat_id, enums.ChatAction.UPLOAD_VIDEO, turu
    )


async def fstik_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    await message.delete()
    turu = client.get_text(message)

    try:
        turu = int(turu)
        if turu <= 0 or turu > 86400:
            raise ValueError("Durasi tidak valid.")
    except ValueError:
        turu = 3600
    proses_ = await emo.get_costum_text()
    proses = await message.reply(f"{emo.proses}**{proses_[4]}**")
    chat_id = message.chat.id

    try:
        task_id = task.start_task()
    except Exception as e:
        return await proses.edit(f"{emo.gagal}**Failed started task:** {e}")

    prefix = client.get_prefix(client.me.id)
    await proses.edit(
        f"{emo.proses}<i>Task {message.command[0]} running #<code>{task_id}</code>. Type <code>{prefix[0]}cancel {task_id}</code> to stop {message.command[0]}!</i>"
    )
    return await send_action_for_duration(
        message, emo, proses, task_id, chat_id, enums.ChatAction.CHOOSE_STICKER, turu
    )


async def task_cmd(client, message):
    data = task.get_active_tasks()
    if not data:
        return await message.reply("**No task running!**")
    msg = "<b>List task:\n\n</b>"
    for num, X in enumerate(data, 1):
        msg += f"<b>{num}. <code>{X}</code></b>"
    return await message.reply(msg)
