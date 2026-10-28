import os
import re
import time
import traceback
import asyncio
from datetime import timedelta
from html import escape
from itertools import islice
from typing import List
from uuid import uuid4

import aiohttp
import wget
from pyrogram.errors import ChatForwardsRestricted
from pyrogram.types import InputMediaPhoto, InputMediaVideo

from clients import bot
from config import API_BOTCHAX, API_MAELYN, API_NEOX
from database import state
from helpers import (ButtonUtils, Emoji, Spotify, Tools, YoutubeSearch,
                     animate_proses, youtube)
from logs import logger


def chunk_media_group(media_list: list, chunk_size: int = 4) -> List[list]:
    """Split media list into chunks of specified size"""
    media_chunks = []
    iterator = iter(media_list)
    while chunk := list(islice(iterator, chunk_size)):
        media_chunks.append(chunk)
    return media_chunks


async def instadl_cmd(client, message, proses, arg):
    em = Emoji(client)
    await em.get()

    await proses.edit(
        f"{em.proses}**Wait a minute, this takes some time...**"
    )

    error_messages = []
    photo_count = 0
    video_count = 0

    try:
        endpoint = "https://api.botcahx.eu.org/api/download/igdowloader"

        params = {
            "url": arg,
            "apikey": API_BOTCHAX,
        }

        response = await Tools.fetch.get(
            endpoint,
            params=params,
        )

        if response.status_code != 200:
            return await proses.edit(
                f"{em.gagal}**Request failed: HTTP "
                f"{response.status_code}**"
            )

        data = response.json()

        # Penting: lihat respons API asli pada bot.log.
        logger.info(f"instadl API response: {data!r}")

        if not isinstance(data, dict):
            return await proses.edit(
                f"{em.gagal}**Invalid API response format**"
            )

        result = data.get("result")

        if not result:
            api_message = (
                data.get("message")
                or data.get("msg")
                or "No result data in response"
            )

            logger.error(
                f"instadl: API tidak memberikan result. "
                f"Response: {data!r}"
            )

            return await proses.edit(
                f"{em.gagal}**{api_message}**"
            )

        # Format result dapat berupa URL string, dict, atau list.
        if isinstance(result, str):
            raw_media = [{"url": result}]

        elif isinstance(result, dict):
            raw_media = (
                result.get("media")
                or result.get("medias")
                or result.get("data")
                or result.get("results")
                or result.get("url")
                or [result]
            )

            if isinstance(raw_media, str):
                raw_media = [{"url": raw_media}]

        elif isinstance(result, list):
            raw_media = result

        else:
            raw_media = [result]

        if not isinstance(raw_media, list):
            raw_media = [raw_media]

        if not raw_media:
            return await proses.edit(
                f"{em.gagal}**No media found in the Instagram link**"
            )

        await proses.edit(
            f"{em.proses}**Preparing media for sending...**"
        )

        media_group = []

        for index, item in enumerate(raw_media, start=1):
            try:
                # API dapat mengirim URL langsung sebagai string.
                if isinstance(item, str):
                    item = {"url": item}

                if not isinstance(item, dict):
                    logger.warning(
                        f"instadl: media #{index} dilewati; "
                        f"format bukan dict: {item!r}"
                    )
                    continue

                download_url = (
                    item.get("url")
                    or item.get("download_url")
                    or item.get("download")
                    or item.get("link")
                    or item.get("src")
                    or item.get("media_url")
                )

                media_type = str(
                    item.get("type")
                    or item.get("media_type")
                    or item.get("mime_type")
                    or item.get("ext")
                    or ""
                ).lower()

                if not download_url:
                    logger.warning(
                        f"instadl: media #{index} tanpa URL: {item!r}"
                    )
                    continue

                lower_url = download_url.lower().split("?")[0]

                is_photo = (
                    media_type in {
                        "image",
                        "photo",
                        "jpg",
                        "jpeg",
                        "png",
                        "webp",
                    }
                    or media_type.startswith("image/")
                    or lower_url.endswith(
                        (".jpg", ".jpeg", ".png", ".webp")
                    )
                )

                is_video = (
                    media_type in {
                        "video",
                        "reel",
                        "mp4",
                        "mov",
                        "mkv",
                        "webm",
                    }
                    or media_type.startswith("video/")
                    or lower_url.endswith(
                        (".mp4", ".mov", ".mkv", ".webm")
                    )
                )

                # Kalau API tidak memberi type atau ekstensi URL tersembunyi,
                # coba video dulu. Banyak CDN Instagram tidak menampilkan .mp4.
                if not is_photo and not is_video:
                    is_video = True

                if is_photo:
                    media = await Tools.get_media_data(
                        download_url,
                        "jpg",
                    )

                    if not media:
                        logger.warning(
                            f"instadl: foto #{index} gagal diunduh: "
                            f"{download_url}"
                        )
                        continue

                    media_group.append(
                        InputMediaPhoto(media=media)
                    )
                    photo_count += 1

                elif is_video:
                    media = await Tools.get_media_data(
                        download_url,
                        "mp4",
                    )

                    if not media:
                        logger.warning(
                            f"instadl: video #{index} gagal diunduh: "
                            f"{download_url}"
                        )
                        continue

                    media_group.append(
                        InputMediaVideo(media=media)
                    )
                    video_count += 1

            except Exception:
                logger.error(
                    f"instadl: gagal menyiapkan media #{index}:"
                    f"{traceback.format_exc()}"
                )

                error_messages.append(
                    f"Media #{index}: gagal diproses"
                )

        if not media_group:
            logger.error(
                f"instadl: media_group kosong. "
                f"Raw media: {raw_media!r}"
            )

            return await proses.edit(
                f"{em.gagal}**Failed to prepare media for sending.**"
                f"<i>Periksa bot.log untuk format response API.</i>"
            )

        media_chunks = chunk_media_group(media_group)

        await proses.delete()

        sent_count = 0

        for index, media_chunk in enumerate(media_chunks, start=1):
            try:
                await client.send_media_group(
                    chat_id=message.chat.id,
                    media=media_chunk,
                )

                sent_count += len(media_chunk)

            except Exception:
                logger.error(
                    f"instadl: gagal mengirim chunk #{index}:"
                    f"{traceback.format_exc()}"
                )

                error_messages.append(
                    f"Chunk #{index}: gagal dikirim"
                )

        result_text = (
            f"{em.sukses}**Successfully sent `{sent_count}` media**"
            f"📷 Photos: `{photo_count}`"
            f"🎬 Videos: `{video_count}`"
        )

        if error_messages:
            result_text += (
                "<b>Warning:</b>"
                + "".join(
                    f"• {error}" for error in error_messages
                )
            )

        return await message.reply(result_text)

    except Exception as error:
        logger.error(
            f"instadl fatal error:{traceback.format_exc()}"
        )

        return await proses.edit(
            f"{em.gagal}**ERROR:** <code>{error}</code>"
        )


async def spotdl_cmd(client, message, proses, arg):
    em = Emoji(client)
    await em.get()
    await proses.edit(f"{em.proses}**Wait a minute this takes some time...**")
    if arg.split("/")[-2] != "track":
        return await proses.edit(
            f"{em.gagal}**Sorry only track supported!!**\n**Example:** https://open.spotify.com/track/0pmyq5KBXP3agRdxl1SZXx?si=3k3nnok6QtCkMF-XRzBo5w",
            disable_web_page_preview=True,
        )
    now = time.time()
    url = await Spotify.track(arg)
    (
        file_path,
        info,
        title,
        duration,
        views,
        channel,
        url,
        _,
        thumb,
        data_ytp,
    ) = await youtube.download(url.get("file_path"), as_video=False)
    thumbnail = wget.download(thumb)
    caption = data_ytp.format(
        info, title, timedelta(seconds=duration), views, channel, url, client.me.mention
    )
    try:
        await message.reply_audio(
            audio=file_path,
            title=title,
            thumb=thumbnail,
            performer=channel,
            duration=duration,
            caption=caption,
            progress=youtube.progress,
            progress_args=(proses, now, f"<b>Sending request...</b>", f"{title}"),
        )
        return await proses.delete()
    except Exception:
        logger.error(f"Eror download spotify: {traceback.format_exc()}")
        return await proses.edit(f"{em.gagal}**ERROR Please contact developer.*")


async def stalking_cmd(client, message):
    em = Emoji(client)
    await em.get()
    await em.get_costum_text()
    proses = await animate_proses(message, em.proses)

    if len(message.command) < 2:
        return await proses.edit(
            f"{em.gagal}**Please give username without @!.\nExample: `{message.text.split()[0]} ranandam_`**"
        )

    username = message.text.split()[1]
    command = message.command[0].lower()

    args = {
        "stalkig": f"https://api.botcahx.eu.org/api/stalk/ig?username={username}&apikey={API_BOTCHAX}",
        "stalktt": f"https://api.botcahx.eu.org/api/stalk/tt?username={username}&apikey={API_BOTCHAX}",
        "stalktw": f"https://api.botcahx.eu.org/api/stalk/twitter?username={username}&apikey={API_BOTCHAX}",
        "stalkyt": f"https://api.botcahx.eu.org/api/stalk/yt?username={username}&apikey={API_BOTCHAX}",
    }

    try:
        response = await Tools.fetch.get(args[command])
        data = response.json()
        result = data["result"]
        if command == "stalkig":
            photo = result["photoUrl"]
            text = f"""
**Instagram Stalking Results**

**Full Name:** {result['fullName']}
**Username:** {result['username']}
**Bio:** {result['bio']}
**Followers:** {result['followers']}
**Following:** {result['following']}
**Posts:** {result['postsCount']}
"""

        elif command == "stalktt":

            photo = result["profile"]
            text = f"""
**TikTok Stalking Results**

**Username:** {result['username']}
**Bio:** {result['description']}
**Likes:** {result['likes']}
**Followers:** {result['followers']}
**Following:** {result['following']}
**Total post:** {result['totalPosts']}
"""

        elif command == "stalktw":
            photo = result["profileImage"]
            text = f"""
**Twitter Stalking Results**

**Full Name:** {result['fullName']}
**Username:** @{result['username']}
**Bio:** {result['bio']}
**Followers:** {result['follower']}
**Following:** {result['following']}
**Total post:** {result['totalPosts']}
**Created at:** {result['createdAt']}
"""

        elif command == "stalkyt":
            channel = result["data"][0]
            photo = channel["avatar"]

            text = f"""
**YouTube Stalking Results**
**Channel Name:** {channel['channelName']}
**Verified:** {channel['isVerified']}
**Subscribers:** {channel['subscriberH']}
**Channel URL:** {channel['url']}
**Description:** {channel.get('description', 'Not available')}
"""
        await message.reply_photo(photo, caption=text)

    except Exception as e:
        await message.reply(f"{em.gagal}**Error: {str(e)}**")
    return await proses.delete()


async def ttdl_cmd(client, message, proses, arg):
    em = Emoji(client)
    await em.get()

    if not arg:
        return await proses.edit(f"{em.gagal}**Berikan link TikTok!**")

    await proses.edit(f"{em.proses}**Wait a minute this takes some time...**")

    url = "https://api.botcahx.eu.org/api/download/tiktok"
    params = {"url": arg, "apikey": API_BOTCHAX}
    foto, video = 0, 0
    err = ""

    try:
        response = await Tools.fetch.get(url, params=params)
        if response.status_code != 200:
            return await proses.edit(
                f"{em.gagal}**Request failed with status code {response.status_code}**"
            )

        data = response.json()
        if not data.get("result"):
            return await proses.edit(f"{em.gagal}**No result data in response**")

        result = data["result"]
        logger.info(f"ttdl result: {str(result)[:1000]}")

        def as_list(v):
            if not v:
                return []
            return v if isinstance(v, list) else [v]

        video_urls, photo_urls = [], []

        if isinstance(result, dict):
            video_urls = as_list(
                result.get("video") or result.get("nowatermark") or result.get("play")
            )
            photo_urls = as_list(result.get("images") or result.get("image"))
        else:
            for item in as_list(result):
                if isinstance(item, dict):
                    link = item.get("url")
                    if item.get("type") == "nowatermarkhd":
                        video_urls.append(link)
                    elif link:
                        photo_urls.append(link)
                elif isinstance(item, str):
                    photo_urls.append(item)

        await proses.edit(f"{em.proses}**Preparing media for sending...**")

        media_group = []

        for link in video_urls:
            if isinstance(link, str):
                media = await Tools.get_media_data(link, "mp4")
                media_group.append(InputMediaVideo(media=media))
                video += 1

        for link in photo_urls:
            if isinstance(link, str):
                media = await Tools.get_media_data(link, "jpg")
                media_group.append(InputMediaPhoto(media=media))
                foto += 1

        if not media_group:
            return await proses.edit(
                f"{em.gagal}**Failed to prepare media for sending**"
            )

        media_chunks = chunk_media_group(media_group)
        await proses.delete()

        for i, chunk in enumerate(media_chunks, 1):
            try:
                await client.send_media_group(chat_id=message.chat.id, media=chunk)
            except Exception as chunk_error:
                err += f"Error sending chunk {i}: {str(chunk_error)}\n"

        return await message.reply(
            f"{em.sukses}**Succesfully sent {len(media_group)} media, photos: `{foto}`, video: `{video}`**\n{err}"
        )

    except Exception as er:
        logger.error(f"ttdl: {traceback.format_exc()}")
        return await proses.edit(f"{em.gagal}**An error: `{str(er)}`**")

      
async def twitter_cmd(client, message, proses, arg):
    em = Emoji(client)
    await em.get()
    await proses.edit(f"{em.proses}**Wait a minute this takes some time...**")
    err = ""
    foto, video = 0, 0
    try:
        payload = {"url": arg}
        url = f"https://nolimitdev.cloud/api/downloader/twitterdl"
        response = await Tools.fetch.post(url, json=payload)
        if response.status_code != 200:
            return await proses.edit(
                f"{em.gagal}**Request failed with status code {response.status_code}**"
            )

        data = response.json()
        if not data.get("result"):
            return await proses.edit(f"{em.gagal}**No result data in response**")

        media_urls = data.get("result", [])
        if not media_urls:
            return await proses.edit(f"{em.gagal}**No media found in the tweet**")

        await proses.edit(f"{em.proses}**Preparing media for sending...**")
        media_group = []

        for url in media_urls:
            if url["type"] == "image":
                media = await Tools.get_media_data(url["url"], "jpg")
                media_group.append(
                    InputMediaPhoto(
                        media=media,
                    )
                )
                foto += 1
            else:
                media = await Tools.get_media_data(url["url"], "mp4")
                media_group.append(
                    InputMediaVideo(
                        media=media,
                    )
                )
                video += 1

        if not media_group:
            return await proses.edit(
                f"{em.gagal}**Failed to prepare media for sending**"
            )

        media_chunks = chunk_media_group(media_group)

        await proses.delete()

        for i, chunk in enumerate(media_chunks, 1):
            try:
                await client.send_media_group(chat_id=message.chat.id, media=chunk)
            except Exception as chunk_error:
                err += f"Error sending chunk {i}: {str(chunk_error)}"
        return await message.reply(
            f"{em.sukses}**Succesfully sent {len(media_group)} media, photos: `{foto}`, video: `{video}`**\n{err}"
        )

    except Exception as er:
        logger.error(f"twdl: {traceback.format_exc()}")
        return await proses.edit(f"{em.gagal}**ERROR:** {str(er)}")



async def _stream_download(url, path):
    """Unduh ke file per potongan (tidak menampung video besar di RAM). Return True kalau berhasil."""
    timeout = aiohttp.ClientTimeout(total=900, sock_read=120)
    headers = {"User-Agent": "Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 Chrome/126 Mobile"}
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        async with session.get(url, allow_redirects=True) as resp:
            if resp.status != 200:
                return False
            with open(path, "wb") as f:
                async for chunk in resp.content.iter_chunked(1024 * 256):
                    f.write(chunk)
    return os.path.getsize(path) > 0


NEOX_FB = "https://api.neoxr.eu/api/fb"   # CEK DOKUMENTASI Neoxr: samakan nama endpoint

async def _fb_neox(arg):
    res = await Tools.fetch.get(
        NEOX_FB, params={"url": arg, "apikey": API_NEOX}, timeout=60
    )
    try:
        body = res.json()
    except Exception:
        body = {}
    if res.status_code != 200 or not body.get("status"):
        raise RuntimeError(
            body.get("msg") or body.get("message") or f"HTTP {res.status_code}"
        )

    data = body.get("data")
    items = data if isinstance(data, list) else ([data] if isinstance(data, dict) else [])
    found = []
    for it in items:
        if not isinstance(it, dict):
            continue
        if isinstance(it.get("url"), str):
            found.append((str(it.get("quality") or it.get("label") or "video"), it["url"]))
        for key in ("hd", "sd"):
            if isinstance(it.get(key), str):
                found.append((key, it[key]))

    def rank(item):
        label = item[0].lower()
        return 0 if ("hd" in label or label.startswith(("1080", "720"))) else 1

    found.sort(key=rank)
    title = body.get("title") or (items[0].get("title") if items and isinstance(items[0], dict) else None)
    if not found:
        raise RuntimeError(f"link video tidak ada (kunci respons: {', '.join(body)})")
    return title, [(label, url, 0) for label, url in found]


async def fbdl_cmd(client, message, proses, arg):
    em = Emoji(client)
    await em.get()
    await proses.edit(f"{em.proses}**Get Facebook video...**")
    try:
        try:
            title, candidates = await _fb_neox(arg)
        except Exception as er:
            logger.warning(f"fbdl Neoxr gagal: {er}")
            return await proses.edit(
                f"{em.gagal}**Please try again later: {escape(str(er))}**"
            )

        await proses.edit(f"{em.proses}**Downloading video...**")
        os.makedirs("downloads", exist_ok=True)
        path = f"downloads/fb_{uuid4().hex}.mp4"
        label = None
        try:
            for lbl, url, _ in candidates:      # coba HD dulu, kalau gagal turun ke SD
                try:
                    if await _stream_download(url, path):
                        label = lbl
                        break
                except Exception:
                    logger.warning(f"fbdl {lbl} gagal: {traceback.format_exc()}")
            if not label:
                return await proses.edit(f"{em.gagal}**Gagal mengunduh video Facebook.**")

            size_mb = os.path.getsize(path) / 1024 / 1024
            quality = "HD" if "hd" in label.lower() or label.startswith(("1080", "720")) else "SD"
            caption = (
                f"<blockquote>🎬 <b>{escape(title or 'Facebook Video')}</b>"
                f"📺 <b>Quality:</b> {quality} • <b>Size:</b> {size_mb:.1f} MB"
                f"🖇️ <a href='{arg}'>Facebook</a>"
                f"{client.me.mention}</blockquote>"
            )
            await proses.edit(f"{em.proses}**Uploading video...**")
            await message.reply_video(path, caption=caption, supports_streaming=True)
            return await proses.delete()
        finally:
            if os.path.exists(path):
                os.remove(path)

    except Exception as er:
        logger.error(f"fbdl: {traceback.format_exc()}")
        return await proses.edit(f"{em.gagal}**ERROR:** {escape(str(er))}")

      

NEOX_VIDEO = "https://api.neoxr.eu/api/video"
YT_URL = re.compile(r"(?:youtube.com|youtu.be)/", re.I)

YT_CAPTION = (
    "<blockquote><b>   「💡 Information Video」</b>"
    "🏷 Title: <code>{}</code>"
    "🧭 Duration: <code>{}</code>"
    "👀 See: <code>{}</code>"
    "📢 Channel: <code>{}</code>"
    "🔗 Link: <a href='{}'>Youtube</a>"
    "⚡Downloaded By: {}</blockquote>"
)


async def _neox_video(query):
    res = await Tools.fetch.get(
        NEOX_VIDEO, params={"q": query, "apikey": API_NEOX}, timeout=60
    )
    try:
        body = res.json()
    except Exception:
        body = {}
    if res.status_code != 200 or not body.get("status"):
        raise RuntimeError(
            body.get("msg") or body.get("message") or f"HTTP {res.status_code}"
        )

    info = body.get("data") or {}
    video_url = info.get("url")
    if not video_url:
        raise RuntimeError(f"url video kosong (kunci respons: {', '.join(body)})")

    vid = body.get("id") or uuid4().hex
    os.makedirs("downloads", exist_ok=True)
    file_name = f"downloads/{vid}.{info.get('extension') or 'mp4'}"
    if not await _stream_download(video_url, file_name):
        raise RuntimeError("gagal mengunduh file video")

    return {
        "file": file_name,
        "title": body.get("title") or "Unknown",
        "duration": int(body.get("duration_seconds") or 0),
        "views": str(body.get("views") or "0"),
        "channel": body.get("channel") or "Unknown",
        "link": f"https://youtu.be/{vid}" if body.get("id") else "https://youtube.com",
        "thumb": body.get("thumbnail"),
    }


async def _ytdlp_video(arg):
    link = arg if YT_URL.search(arg) else None
    if not link:
        yt_search = YoutubeSearch(arg, max_results=1)
        await yt_search.fetch_results()
        link = yt_search.get_link()
    if not link:
        raise RuntimeError("Video tidak ditemukan.")

    (file_name, _, title, duration, views, channel, url, _, thumb, _) = (
        await youtube.download(link, as_video=True)
    )
    if isinstance(duration, str):
        duration = duration.replace(".", "")
    return {
        "file": file_name,
        "title": title,
        "duration": int(duration or 0),
        "views": str(views),
        "channel": channel,
        "link": url,
        "thumb": thumb,
    }


async def ytvideo_cmd(client, message, proses, arg):
    emo = Emoji(client)
    await emo.get()
    arg = (arg or "").strip()
    if not arg:
        return await proses.edit(f"{emo.gagal}<b>Berikan judul atau link YouTube!</b>")

    media = None
    thumbnail = None
    try:
        await proses.edit(f"{emo.proses}**Wait a minute this takes some time...**")
        now = time.time()
        try:
            media = await _neox_video(arg)
        except Exception as error:
            logger.warning(f"ytdl: Neoxr gagal ({error}), pakai yt-dlp")
            media = await _ytdlp_video(arg)

        if media["thumb"]:
            try:
                thumbnail = await asyncio.to_thread(wget.download, media["thumb"])
            except Exception:
                thumbnail = None

        caption = YT_CAPTION.format(
            escape(str(media["title"])),
            timedelta(seconds=media["duration"]),
            media["views"],
            escape(str(media["channel"])),
            media["link"],
            bot.me.mention,
        )
        await client.send_video(
            message.chat.id,
            video=media["file"],
            thumb=thumbnail,
            file_name=media["title"],
            duration=media["duration"],
            supports_streaming=True,
            caption=caption,
            progress=youtube.progress,
            progress_args=(
                proses,
                now,
                f"{emo.proses}<b>Trying to upload...</b>",
                f"{media['title']}",
            ),
            reply_to_message_id=message.id,
        )
        await proses.delete()
    except Exception as er:
        logger.error(f"ytdl: {traceback.format_exc()}")
        await proses.edit(f"{emo.gagal}<b>ERROR:</b> <code>{escape(str(er))}</code>")
    finally:
        for path in (thumbnail, media and media["file"]):
            if path and os.path.exists(path):
                os.remove(path)


async def pindl_cmd(client, message, proses, arg):
    em = Emoji(client)
    await em.get()
    await proses.edit(f"{em.proses}**Wait a minute this takes some time...**")
    url = f"https://api.botcahx.eu.org/api/download/pinterest?url={arg}&apikey={API_BOTCHAX}"
    response = await Tools.fetch.get(url)

    if response.status_code == 200:
        data = response.json()
        result = data.get("result", {}).get("data", {})

        if result.get("media_type") == "image":
            await message.reply_photo(result["image"], caption=result["title"] or "")
        elif result.get("media_type") == "video/mp4":
            await message.reply_video(result["video"], caption=result["title"] or "")

        return await proses.delete()
    else:
        return await proses.edit(
            f"{em.gagal}**Failed to download from the provided URL.**"
        )


async def teledl_cmd(client, message, proses, arg):
    em = Emoji(client)
    await em.get()
    chat_id = message.chat.id
    await proses.edit(f"{em.proses}**Wait a minute this takes some time...**")
    if "/s/" in arg:
        user, story_id = Tools.extract_story_link(arg)
        story = await client.get_stories(user, story_id)
        await Tools.download_media(story, client, proses, message, True)
        return await proses.delete()
    if "?single" in arg:
        arg = arg.replace("?single", "")
    if arg.startswith(("https", "t.me")):
        if "?comment=" in arg:
            arg_parts = arg.split("?comment=")
            msg_id = int(arg_parts[0].split("/")[-1])
            target = int(arg_parts[1].split("/")[-1])
            chid = str(arg.split("/")[-2])
            chat = await client.get_discussion_message(chid, msg_id)
            try:
                get_msg = await client.get_messages(chat.chat.id, target)
                try:
                    await get_msg.copy(chat_id)
                    return await proses.delete()
                except ChatForwardsRestricted:
                    return await Tools.download_media(get_msg, client, proses, message)
            except Exception as e:
                return await proses.edit(str(e))
        msg_id = int(arg.split("/")[-1])
        logger.info(f"Msg ID copy: {msg_id}")
        if "t.me/c/" in arg:
            chat = int("-100" + str(arg.split("/")[-2]))
            try:
                get_msg = await client.get_messages(chat, msg_id)
                try:
                    await get_msg.copy(chat_id)
                    return await proses.delete()
                except ChatForwardsRestricted:
                    return await Tools.download_media(get_msg, client, proses, message)
            except Exception as e:
                return await proses.edit(str(e))
        else:
            get_chat = str(arg.split("/")[-2])
            logger.info(f"Chat copy: {get_chat}")
            try:
                chat = await client.get_chat(get_chat)
                get_msg = await client.get_messages(chat.id, msg_id)
                await get_msg.copy(chat_id)
                return await proses.delete()
            except ChatForwardsRestricted:
                return await Tools.download_media(get_msg, client, proses, message)
            except Exception as e:
                return await proses.edit(str(e))

    else:
        return await proses.edit(f"{em.gagal}<b>Please give valid link!!</b>")


async def downloader_cmd(client, message):
    em = Emoji(client)
    await em.get()
    await em.get_costum_text()
    arg = client.get_text(message)
    prefix = client.get_prefix(client.me.id)
    if not arg:
        return await message.reply(
            f"{em.gagal}<b>Please give a link!\nExample: `{message.text.split()[0]} https://x.com/eskacangkhu/status/1921732123213398212?t=72ASOxnYYvYCltwOHzuXrw&s=19`</b>"
        )
    if not arg.startswith("https"):
        return await message.reply(
            f"{em.gagal}<b>Only link supported, if you want search with query use command: `{prefix[0]}sosmed bh terbang`.</b>"
        )
    proses = await animate_proses(message, em.proses)
    await proses.edit(f"{em.proses}**Wait a minute this takes some time...**")

    try:
        # INSTAGRAM
        if "instagram.com" in arg:
            await proses.edit(f"{em.proses}**Detected Instagram link...**")
            return await instadl_cmd(client, message, proses, arg)

        # PINTEREST
        elif "pin.it" in arg:
            await proses.edit(f"{em.proses}**Detected Pinterest link...**")
            return await pindl_cmd(client, message, proses, arg)

        # TWITTER
        elif "x.com" in arg or "twitter.com" in arg:
            await proses.edit(f"{em.proses}**Detected Twitter link...**")
            return await twitter_cmd(client, message, proses, arg)

        # FACEBOOK
        elif any(d in arg for d in ("facebook.com", "fb.watch", "fb.com")):
            await proses.edit(f"{em.proses}**Detected Facebook link...**")
            return await fbdl_cmd(client, message, proses, arg)

        # TELEGRAM
        elif "t.me" in arg:
            await proses.edit(f"{em.proses}**Detected Telegram link...**")
            return await teledl_cmd(client, message, proses, arg)

        # TIKTOK
        elif "tiktok.com" in arg or "vt.tiktok.com" in arg:
            await proses.edit(f"{em.proses}**Detected TikTok link...**")
            return await ttdl_cmd(client, message, proses, arg)

        # SPOTIFY
        elif "spotify.com" in arg:
            await proses.edit(f"{em.proses}**Detected Spotify link...**")
            return await spotdl_cmd(client, message, proses, arg)

        # YOUTUBE
        elif "youtube.com" in arg or "youtu.be" in arg:
            await proses.edit(f"{em.proses}**Detected YouTube link...**")
            return await ytvideo_cmd(client, message, proses, arg)

        else:
            return await proses.edit(
                f"{em.gagal}**Unsupported link detected! Only support:**\n• Instagram\n• Facebook\n• Pinterest\n• Twitter/X\n• Telegram\n• TikTok\n• Spotify\n• YouTube"
            )

    except Exception as er:
        logger.error(f"sosmeddl: {traceback.format_exc()}")
        return await proses.edit(f"{em.gagal}**An error occurred:** `{str(er)}`")


async def sosmed_cmd(client, message):
    em = Emoji(client)
    await em.get()
    arg = client.get_text(message)
    prefix = client.get_prefix(client.me.id)
    if not arg:
        return await message.reply(
            f"{em.gagal}<b>Please give query\nExample: `{message.text.split()[0]} bh terbang` or `{message.text.split()[0]} garam & madu`</b>"
        )
    if arg.startswith("https"):
        return await message.reply(
            f"{em.gagal}<b>Only supported query!! If you want download bye link use command: `{prefix[0]}dl https://x.com/eskacangkhu/status/1921732123213398212?t=72ASOxnYYvYCltwOHzuXrw&s=19`</b>"
        )
    proses = await animate_proses(message, em.proses)
    uniq = f"{str(uuid4())}"
    state.set(uniq.split("-")[0], "query", arg)
    state.set(uniq.split("-")[0], "idm", id(message))
    inline = await ButtonUtils.send_inline_bot_result(
        message, message.chat.id, bot.me.username, f"inline_sosmed {uniq.split('-')[0]}"
    )
    if inline:
        return await proses.delete()
    else:
        return await proses.edit(f"{em.gagal}**ERROR Please contact developer.*")
