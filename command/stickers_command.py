import asyncio
import os

from pyrogram import enums
from pyrogram.errors import BadRequest, PeerIdInvalid, StickersetInvalid
from pyrogram.file_id import FileId
from pyrogram.raw.functions.messages import GetStickerSet, SendMedia
from pyrogram.raw.functions.stickers import (AddStickerToSet, CreateStickerSet,
                                             RemoveStickerFromSet)
from pyrogram.raw.types import (DocumentAttributeFilename, InputDocument,
                                InputMediaUploadedDocument,
                                InputStickerSetItem, InputStickerSetShortName)

from clients import bot
from config import LOG_BACKUP
from helpers import Emoji, Sticker, Tools, animate_proses


async def make_stickers(self, message):
    prog_msg = await message.reply("Processing...")
    sticker_emojis = "🤔"
    sticker_emoji = message.command[1] if len(message.command) > 1 else sticker_emojis
    packnum = 0
    packname_found = False
    resize = False
    animated = False
    videos = False
    convert = False
    reply = message.reply_to_message
    user = await self.resolve_peer(message.from_user.username or message.from_user.id)

    if reply and reply.media:
        if reply.photo:
            resize = True
        elif reply.animation:
            videos = True
            convert = True
        elif reply.video:
            convert = True
            videos = True
        elif reply.document:
            if "image" in reply.document.mime_type:
                # mime_type: image/webp
                resize = True
            elif reply.document.mime_type in (
                enums.MessageMediaType.VIDEO,
                enums.MessageMediaType.ANIMATION,
            ):
                # mime_type: application/video
                videos = True
                convert = True
            elif "tgsticker" in reply.document.mime_type:
                # mime_type: application/x-tgsticker
                animated = True
        elif reply.sticker:
            if not reply.sticker.file_name:
                return await prog_msg.edit_text("Stiker tidak memiliki nama.")
            if reply.sticker.emoji:
                sticker_emoji = reply.sticker.emoji
            animated = reply.sticker.is_animated
            videos = reply.sticker.is_video
            if videos:
                convert = False
            elif not reply.sticker.file_name.endswith(".tgs"):
                resize = True
        else:
            return await prog_msg.edit_text()

        pack_prefix = "anim" if animated else "vid" if videos else "a"
        packname = f"{pack_prefix}_{message.from_user.id}_by_{self.me.username}"

        if (
            len(message.command) > 1
            and message.command[1].isdigit()
            and int(message.command[1]) > 0
        ):
            # provide pack number to kang in desired pack
            packnum = message.command.pop(1)
            packname = (
                f"{pack_prefix}{packnum}_{message.from_user.id}_by_{self.me.username}"
            )
        if len(message.command) > 1:
            # matches all valid emojis in input
            sticker_emoji = (
                "".join(
                    set(Sticker.get_emoji_regex().findall("".join(message.command[1:])))
                )
                or sticker_emoji
            )
        filename = await self.download_media(message.reply_to_message)
        if not filename:
            # Failed to download
            await prog_msg.delete()
            return
    elif message.entities and len(message.entities) > 1:
        pack_prefix = "a"
        filename = "sticker.png"
        packname = f"c{message.from_user.id}_by_{self.me.username}"
        img_url = next(
            (
                message.text[y.offset : (y.offset + y.length)]
                for y in message.entities
                if y.type == "url"
            ),
            None,
        )

        if not img_url:
            await prog_msg.delete()
            return
        try:
            r = await Tools.fetch.get(img_url)
            if r.status_code == 200:
                with open(filename, mode="wb") as f:
                    f.write(r.read())
        except Exception as r_e:
            return await prog_msg.edit_text(f"{r_e.__class__.__name__} : {r_e}")
        if len(message.command) > 2:
            # message.command[1] is image_url
            if message.command[2].isdigit() and int(message.command[2]) > 0:
                packnum = message.command.pop(2)
                packname = f"a{packnum}_{message.from_user.id}_by_{self.me.username}"
            if len(message.command) > 2:
                sticker_emoji = (
                    "".join(
                        set(
                            Sticker.get_emoji_regex().findall(
                                "".join(message.command[2:])
                            )
                        )
                    )
                    or sticker_emoji
                )
            resize = True
    else:
        return await prog_msg.edit_text(
            "Ingin saya menebak stikernya? Harap tandai stiker."
        )
    try:
        if resize:
            filename = Sticker.resize_image(filename)
        elif convert:
            filename = await Sticker.convert_video(filename)
            if filename is False:
                return await prog_msg.edit_text("Error")
        max_stickers = 50 if animated else 120
        while not packname_found:
            try:
                stickerset = await self.invoke(
                    GetStickerSet(
                        stickerset=InputStickerSetShortName(short_name=packname),
                        hash=0,
                    )
                )
                if stickerset.set.count >= max_stickers:
                    packnum += 1
                    packname = f"{pack_prefix}_{packnum}_{message.from_user.id}_by_{self.me.username}"
                else:
                    packname_found = True
            except StickersetInvalid:
                break
        file = await self.save_file(filename)
        media = await self.invoke(
            SendMedia(
                peer=(await self.resolve_peer(LOG_BACKUP)),
                media=InputMediaUploadedDocument(
                    file=file,
                    mime_type=self.guess_mime_type(filename),
                    attributes=[DocumentAttributeFilename(file_name=filename)],
                ),
                message=f"#Sticker kang by UserID -> {message.from_user.id}",
                random_id=self.rnd_id(),
            ),
        )
        msg_ = media.updates[-1].message
        stkr_file = msg_.media.document
        if packname_found:
            await prog_msg.edit_text("Menggunakan paket stiker yang ada...")
            await self.invoke(
                AddStickerToSet(
                    stickerset=InputStickerSetShortName(short_name=packname),
                    sticker=InputStickerSetItem(
                        document=InputDocument(
                            id=stkr_file.id,
                            access_hash=stkr_file.access_hash,
                            file_reference=stkr_file.file_reference,
                        ),
                        emoji=sticker_emoji,
                    ),
                )
            )
        else:
            await prog_msg.edit_text("Membuat paket stiker baru...")
            stkr_title = f"{message.from_user.first_name}"
            if animated:
                stkr_title += " AnimPack"
            elif videos:
                stkr_title += " VidPack"
            if packnum != 0:
                stkr_title += f" v{packnum}"
            try:
                await self.invoke(
                    CreateStickerSet(
                        user_id=user,
                        title=stkr_title,
                        short_name=packname,
                        stickers=[
                            InputStickerSetItem(
                                document=InputDocument(
                                    id=stkr_file.id,
                                    access_hash=stkr_file.access_hash,
                                    file_reference=stkr_file.file_reference,
                                ),
                                emoji=sticker_emoji,
                            )
                        ],
                        animated=animated,
                        videos=videos,
                    )
                )
            except PeerIdInvalid:
                return (
                    await prog_msg.edit_text(
                        "Tampaknya Anda belum pernah berinteraksi dengan saya dalam obrolan pribadi, Anda harus melakukannya dulu.."
                    ),
                )
    except BadRequest:
        return await prog_msg.edit_text(
            "Paket Stiker Anda penuh jika paket Anda tidak dalam Tipe v1 /kang 1, jika tidak dalam Tipe v2 /kang 2 dan seterusnya."
        )
    except Exception as all_e:
        return await prog_msg.edit_text(f"{all_e.__class__.__name__} : {all_e}")
    else:
        await prog_msg.edit_text(
            f"<b>Sticker Anda Berhasil Dibuat!</b>\n<b><a href=https://t.me/addstickers/{packname}>👀 Lihat Paket Sticker Disini</a></b>\n<b>Emoji:</b> {sticker_emoji}"
        )
        await self.delete_messages(chat_id=LOG_BACKUP, message_ids=msg_.id, revoke=True)
        try:
            os.remove(filename)
        except OSError:
            pass
    return


async def remove_stickers(self, message):
    rep = message.reply_to_message.sticker

    try:
        sticker_id = rep.file_id
        decoded = FileId.decode(sticker_id)
        sticker = InputDocument(
            id=decoded.media_id,
            access_hash=decoded.access_hash,
            file_reference=decoded.file_reference,
        )
        await bot.invoke(RemoveStickerFromSet(sticker=sticker))
        await message.reply(f"Stiker berhasil dihapus dari paket Anda.")
        return
    except Exception as e:
        await message.reply(
            f"Gagal menghapus stiker dari paket Anda.\n\nError: <code>{e}</code>"
        )
        return


async def download_and_reply(client, message, stick, file_extension):
    em = Emoji(client)
    await em.get()
    pat = await client.download_media(
        stick, file_name=f"{stick.set_name}.{file_extension}"
    )
    await message.reply_to_message.reply_document(
        document=pat,
        caption=f"📂 **File Name:** `{stick.set_name}.{file_extension}`\n📦 **File Size:** `{stick.file_size}`\n📆 **File Date:** `{stick.date}`\n📤 **File ID:** `{stick.file_id}`",
    )


async def gstick_cmd(client, message):
    em = Emoji(client)
    await em.get()
    reply = message.reply_to_message
    if reply and reply.sticker:
        stick = reply.sticker
        if stick.is_video:
            return await download_and_reply(client, message, stick, "mp4")
        elif stick.is_animated:
            return await message.reply(
                f"{em.gagal} Animated stickers are not supported."
            )
        else:
            return await download_and_reply(client, message, stick, "png")
    else:
        return await message.reply(
            f"{em.gagal} Reply to a sticker to get its information."
        )


async def unkang_cmd(self, message):
    em = Emoji(self)
    await em.get()
    reply = message.reply_to_message
    await self.unblock_user(bot.me.username)
    if not reply or not reply.sticker:
        return await message.reply(f"{em.gagal} Reply to a sticker to remove")

    pros = await animate_proses(message, em.proses)
    ai = await self.forward_messages(
        bot.me.username, message.chat.id, message_ids=reply.id
    )
    await self.send_message(bot.me.username, "/unkang", reply_to_message_id=ai.id)
    await asyncio.sleep(0.5)

    if await resleting(self, message) == "Stiker berhasil dihapus dari paket Anda.":
        return await pros.edit(f"{em.sukses} Sticker removed from your pack.")
    else:
        return await pros.edit(f"{em.gagal} Failed to remove sticker from your pack.")


async def kang_cmd(self, message):
    em = Emoji(self)
    await em.get()
    reply = message.reply_to_message
    cekemo = self.get_arg(message)
    await self.unblock_user(bot.me.username)
    if not reply:
        return await message.reply(f"{em.gagal} Reply to a sticker to add")

    pros = await animate_proses(message, em.proses)
    await self.send_message(bot.me.username, "/kang")
    try:
        ai = await self.forward_messages(
            bot.me.username, message.chat.id, message_ids=reply.id
        )
    except Exception:
        bh = await self.get_messages(message.chat.id, reply.id)
        ai = await bh.copy(bot.me.username)
    if len(message.command) == 2:
        await self.send_message(
            bot.me.username, f"/kang {cekemo}", reply_to_message_id=ai.id
        )
    else:
        await self.send_message(bot.me.username, "/kang", reply_to_message_id=ai.id)

    await asyncio.sleep(5)
    async for tai in self.search_messages(
        bot.me.username, query="Sticker Anda Berhasil Dibuat!", limit=1
    ):
        await asyncio.sleep(5)
        await tai.copy(message.chat.id)

    await ai.delete()
    await pros.delete()


async def resleting(self, message):
    return [x async for x in self.get_chat_history(bot.me.username, limit=1)][0].text
