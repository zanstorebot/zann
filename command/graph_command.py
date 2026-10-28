import aiofiles
import aiohttp
from pathlib import Path

from helpers import Emoji, Tools, animate_proses

TELEGRAPH_BASE_URL = "https://telegra.ph"


async def upload_to_telegraph(file_path):
    media_path = Path(file_path)

    if not media_path.is_file():
        raise Exception("Gagal mengunduh foto.")

    if media_path.stat().st_size == 0:
        raise Exception("File foto kosong.")

    filename = media_path.name
    timeout = aiohttp.ClientTimeout(total=120)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        form = aiohttp.FormData()
        async with aiofiles.open(media_path, "rb") as file:
            form.add_field(
                "file",
                file,
                filename=filename,
                content_type="image/jpeg",
            )
            async with session.post(
                f"{TELEGRAPH_BASE_URL}/upload",
                data=form,
            ) as response:
                result = await response.json()

                if response.status != 200 or not result:
                    raise Exception(
                        f"Telegraph upload gagal: {response.status} {str(result)[:200]}"
                    )
                return f"{TELEGRAPH_BASE_URL}{result[0]['src']}"


async def tg_cmd(client, message):
    emo = Emoji(client)
    await emo.get()

    processing = await animate_proses(message, emo.proses)
    reply = message.reply_to_message

    if not reply:
        return await processing.edit(
            f"{emo.gagal}<b>Please reply to a text message or media!</b>"
        )

    try:
        if reply.photo or reply.video or reply.document:
            url = await Tools.upload_media(message)

        elif reply.text or reply.caption:
            return await processing.edit(
                f"{emo.gagal}<b>Fitur ini khusus untuk media.</b>"
            )

        else:
            return await processing.edit(
                f"{emo.gagal}<b>Unsupported message type.</b>"
            )

        return await processing.edit(
            f"{emo.sukses}<b>Successfully uploaded:</b> <a href='{url}'>Click Here</a>",
            disable_web_page_preview=True,
        )

    except Exception as exc:
        return await processing.edit(
            f"{emo.gagal}<b>Error:</b> <code>{str(exc)[:500]}</code>"
        )