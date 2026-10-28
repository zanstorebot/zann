import asyncio
import os
import traceback

from pyrogram import enums
from pyrogram.errors import FloodWait, RPCError

from helpers import Emoji, Tools, animate_proses
from logs import logger


async def safe_download(client, msg):
    try:
        return await client.download_media(msg)
    except FloodWait as fw:
        await asyncio.sleep(fw.value)
        return await client.download_media(msg)


async def get_thumb(client, thumbs):
    if thumbs:
        try:
            return await client.download_media(thumbs[-1])
        except Exception:
            return None
    return None


async def cleanup_media(media_path):
    try:
        if media_path and os.path.exists(media_path):
            os.remove(media_path)
    except Exception as e:
        logger.error(f"Error deleting media: {e}")


async def copyall_cmd(client, message):
    em = Emoji(client)
    await em.get()
    args = message.command[1:]

    if len(args) < 2:
        return await message.reply(
            f"**Please give link**\nExample: `{message.text.split()[0]} https://t.me/devasupport/1745 5`"
        )
    proses = await animate_proses(message, em.proses)
    chat_id = message.chat.id
    message_link = args[0]
    total = int(args[1])

    chats, links = Tools.get_link(message_link)
    if chats is None or links is None:
        return await proses.edit(
            f"**Invalid link**\nExample: `{message.text.split()[0]} https://t.me/devasupport/1745 5`"
        )
    try:
        async for msg in client.get_chat_history(chats, limit=1):
            lastnih = msg.id
            break
        else:
            return await proses.edit("<b>No messages found in the chat!</b>")
        logger.info(f"Last message ID: {lastnih}")
        counter = 0
        successful_copies = 0
        skipped_messages = 0

        for message_id in range(links, min(total + links, lastnih + 1)):
            try:
                msg = await client.get_messages(chats, message_id)

                if not msg:
                    skipped_messages += 1
                    continue
                if msg.text:
                    continue
                if msg.media in [
                    enums.MessageMediaType.VIDEO,
                    enums.MessageMediaType.PHOTO,
                ]:
                    try:
                        await msg.copy(chat_id)
                    except FloodWait as wet:
                        await asyncio.sleep(wet.value)
                        await msg.copy(chat_id)
                    except Exception:
                        cnt = await message.reply(
                            "<b>Cant copy message, try to downloading...</b>"
                        )
                        await Tools.download_media(msg, client, cnt, message)

                    successful_copies += 1
                    counter += 1

            except FloodWait as flood:
                logger.error(f"FloodWait: Waiting for {flood.value} seconds")
                await asyncio.sleep(flood.value)
            except RPCError as rpc_error:
                logger.error(f"RPC Error for message {message_id}: {rpc_error}")
                continue
            except Exception as er:
                logger.error(
                    f"Error copying message {message_id}: {traceback.format_exc()}"
                )
                continue

        await proses.delete()
        return await message.reply(
            f"<b>Copying completed.\n"
            f"Total messages attempted: {total}\n"
            f"Successfully copied: {successful_copies}\n"
            f"Skipped messages: {skipped_messages}</b>"
        )

    except Exception as e:
        logger.error(f"Overall process error: {traceback.format_exc()}")
        return await message.reply(f"An unexpected error occurred: {str(e)}")


async def copyall2_cmd(client, message):
    em = Emoji(client)
    await em.get()
    args = message.command[1:]

    if len(args) < 2:
        return await message.reply(
            f"**Please give link**\nExample: `{message.text.split()[0]} https://t.me/devasupport/1745 5`"
        )
    proses = await animate_proses(message, em.proses)
    chat_id = message.chat.id
    message_link = args[0]
    total = int(args[1])

    chats, links = Tools.get_link(message_link)
    if chats is None or links is None:
        await proses.edit(
            f"**Invalid link**\nExample: `{message.text.split()[0]} https://t.me/devasupport/1745 5`"
        )
        return
    try:
        messages = []
        async for msg in client.get_chat_history(chats, limit=total):
            messages.append(msg)
            if len(messages) >= total:
                break

        messages = list(reversed(messages))

        for msg in messages:
            try:
                caption = msg.caption or msg.text or ""
                markup = msg.reply_markup

                media_types = {
                    "video": client.send_video,
                    "photo": client.send_photo,
                    "animation": client.send_animation,
                    "voice": client.send_voice,
                    "audio": client.send_audio,
                    "document": client.send_document,
                    "sticker": client.send_sticker,
                }

                for media_type, send_method in media_types.items():
                    media_attr = getattr(msg, media_type, None)
                    if media_attr:
                        try:
                            media = await safe_download(client, msg)
                            if media:
                                send_args = {
                                    "chat_id": chat_id,
                                    media_type: media,
                                    "caption": caption,
                                    "reply_markup": markup,
                                }

                                if media_type in ["video", "audio"]:
                                    send_args.update(
                                        {
                                            "duration": media_attr.duration,
                                            "width": getattr(media_attr, "width", None),
                                            "height": getattr(
                                                media_attr, "height", None
                                            ),
                                        }
                                    )

                                await send_method(
                                    **{
                                        k: v
                                        for k, v in send_args.items()
                                        if v is not None
                                    }
                                )
                                break
                            if media:
                                await cleanup_media(media)
                        except Exception as media_err:
                            logger.error(f"Error sending {media_type}: {media_err}")
                            return await message.reply(
                                f"An error occurred: {str(media_err)}"
                            )
                else:
                    await client.copy_message(
                        chat_id, msg.chat.id, msg.id, reply_markup=markup
                    )

                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error copying message: {e}")
                return await message.reply(f"An error occurred: {str(e)}")

        await proses.delete()
        return await message.reply("<b>Copying completed!</b>")

    except Exception as e:
        logger.error(f"Copyall error: {traceback.format_exc()}")
        return await message.reply(f"An error occurred: {str(e)}")
