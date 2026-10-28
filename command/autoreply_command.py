from database import dB


async def autoreply_cmd(client, message):
    if len(message.command) < 2:
        return await message.reply(
            f"<b>Please usage command: `{message.text.split()} on` for turned on autoreply, `{message.text.split()} off` for turned off autoreply, and `{message.text.split()} status` to check the status in which groups this feature is active.</b>"
        )
    if message.command[1] == "on":
        await dB.add_to_var(client.me.id, "MENTIONED", message.chat.id)
        return await message.reply("<b>Auto reply turned on.</b>")
    elif message.command[1] == "off":
        if len(message.command) < 3:
            chat_id = message.chat.id
            if chat_id not in await dB.get_list_from_var(client.me.id, "MENTIONED"):
                return await message.reply(f"**`{chat_id}` is not found!**")
            await dB.remove_from_var(client.me.id, "MENTIONED", chat_id)
            name = (await client.get_chat(chat_id)).title
            return await message.reply(f"<b>Turned off autoreply for chat: {name}</b>")
        else:
            if message.command[2] == "all":
                for A in await dB.get_list_from_var(client.me.id, "MENTIONED"):
                    await dB.remove_from_var(client.me.id, "MENTIONED", A)
                return await message.reply(
                    f"<b>Successfully delete all lists chat autoreply!</b>"
                )
            else:
                if len(message.command) < 3:
                    return await message.reply(
                        f"<b>Please user command `{message.text.split()} off -100434249243279`</b>"
                    )
                chat_id = message.command[2]
                try:
                    chat_id = int(chat_id)
                except ValueError:
                    return await message.reply(
                        f"**Please give a valid chat_id.Error `{chat_id}`!**"
                    )
                if chat_id not in await dB.get_list_from_var(client.me.id, "MENTIONED"):
                    return await message.reply(f"`{chat_id}` **Not found!**")
                await dB.remove_from_var(client.me.id, "MENTIONED", chat_id)
                name = (await client.get_chat(chat_id)).title
                return await message.reply(
                    f"<b>Turned off autoreply for chat: {name}</b>"
                )
    elif message.command[1] == "status":
        chats = await dB.get_list_from_var(client.me.id, "MENTIONED")
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
    else:
        return await message.reply(
            f"<b>Please usage command: `{message.text.split()} on` for turned on autoreply, `{message.text.split()} off` for turned off autoreply, and `{message.text.split()} status` to check the status in which groups this feature is active.</b>"
        )


async def mentioned_trigger(client, message):
    if message.chat.id not in await dB.get_list_from_var(client.me.id, "MENTIONED"):
        return
    if (
        message.reply_to_message
        and message.reply_to_message.from_user.id == client.me.id
    ):
        if message.text:
            await message.reply(message.text)

        elif message.photo:
            await message.reply_photo(
                message.photo.file_id, caption=message.caption or None
            )
        elif message.video:
            await message.reply_video(
                message.video.file_id, caption=message.caption or None
            )
        elif message.sticker:
            await message.reply_sticker(message.sticker.file_id)
        elif message.document:
            await message.reply_document(
                message.document.file_id, caption=message.caption or None
            )
        elif message.audio:
            await message.reply_audio(
                message.audio.file_id, caption=message.caption or None
            )
        elif message.voice:
            await message.reply_voice(message.voice.file_id)
        elif message.location:
            await message.reply_location(
                longitude=message.location.longitude,
                latitude=message.location.latitude,
            )

    elif client.me.username in (message.text or "") or client.me.username in (
        message.caption or ""
    ):
        mention = message.from_user.mention()
        caption_text = (message.caption or "").replace(client.me.username, mention)
        if message.text:
            await message.reply(f"{mention}")
        elif message.photo:
            await message.reply_photo(
                message.photo.file_id,
                caption=caption_text,
            )
        elif message.video:
            await message.reply_video(
                message.video.file_id,
                caption=caption_text,
            )
        elif message.document:
            await message.reply_document(
                message.document.file_id,
                caption=caption_text,
            )
        elif message.sticker:
            await message.reply_sticker(message.sticker.file_id)
        elif message.video_note:
            await message.reply_video_note(message.video_note.file_id)
        elif message.audio:
            await message.reply_audio(
                message.audio.file_id,
                caption=caption_text,
            )
        elif message.voice:
            await message.reply_voice(message.voice.file_id, caption=caption_text)
        elif message.location:
            await message.reply_location(
                longitude=message.location.longitude,
                latitude=message.location.latitude,
            )
