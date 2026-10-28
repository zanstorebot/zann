import asyncio
import os
import traceback
from html import escape
import wget
import aiofiles
import aiohttp
from uuid import uuid4
from time import time
from datetime import datetime, timedelta

from PIL import Image
from pyrogram import StopPropagation, filters
from pyrogram.enums import ButtonStyle
from pyrogram.errors import FloodWait
from pyrogram.handlers import CallbackQueryHandler, InlineQueryHandler
from pyrogram.helpers import ikb
from pyrogram.types import InlineQueryResultPhoto
from pytgcalls.exceptions import NotInCallError
from youtubesearchpython import VideosSearch


from clients import alice, bot
from config import API_NEOX, SUDO_OWNERS, URL_LOGO
from database import dB, state
from helpers import (ButtonUtils, Emoji, Spotify, Tools, YoutubeSearch, YoutubeDownload,
                     animate_proses, gen_qthumb, stream, telegram, youtube)
from logs import logger



def download_file(url, filename, stream: False = bool):
    response = requests.get(url, stream=stream)
    if response.status_code == 200:
        with open(filename, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        logger.info(f"Downloaded: {filename}")
    else:
        return f"Failed to download: {filename}"

async def dsong(client, message, _):
    emo = Emoji(client)
    await emo.get()
    if len(message.command) < 2:
        return await message.reply("Mana judulnya!?")
    pros = await message.reply("<b>Downloading Music...</b>")
    try:
        search = VideosSearch(message.text.split(None, 1)[1], limit=1).result()["result"][0]
        link = f"https://youtu.be/{search['id']}"
    except Exception as error:
        return await pros.edit(f"{emo.gagal} Error: {error}")
    try:
        (
            file_name,
            title,
            url,
            duration,
            views,
            channel,
            thumb,
            data_ytp,
        ) = await YoutubeDownload(link, as_video=False)
    except Exception as error:
        return await pros.edit(f"{emo.gagal} Error njir: {error}")

    thumbnail = None
    try:
        thumbnail = wget.download(thumb)
        await client.send_audio(
            message.chat.id,
            audio=file_name,
            thumb=thumbnail,
            file_name=title,
            performer=channel,
            duration=duration,
            caption=data_ytp.format(
                "AUDIO",
                title,
                timedelta(seconds=duration),
                views,
                channel,
                url,
                client.me.mention,
            ),
            progress=Tools.progress,
            progress_args=(
                pros,
                time(),
                _("proses"), f"{search['id']}.mp3",
            ),
            reply_to_message_id=message.id,
        )
        await pros.delete()
        await message.delete()
    except Exception as error:
        await pros.edit(f"{emo.gagal} Gagal kirim audio: {error}")
    finally:
        for files in (thumbnail, file_name):
            if files and os.path.exists(files):
                os.remove(files)
    return


# ---------------------------------------------------------------------------
# DIPERBAIKI: skip_songs
# ---------------------------------------------------------------------------
async def skip_songs(client, chat_id):
    emo = Emoji(client)
    await emo.get()
    await Tools.get_logo()
    group_calls = stream.get_active_call(chat_id, client.me.id)
    queue = stream.get_queue(chat_id, client.me.id)

    if not group_calls:
        return await client.send_message(
            chat_id, f"{emo.gagal}<b>No media is currently playing.</b>"
        )

    if not queue or len(queue) <= 1:
        return await client.send_message(
            chat_id, f"{emo.gagal}<b>No next track available.</b>"
        )
    pros = await client.send_message(
        chat_id, f"{emo.proses}<b>Processing next media...</b>"
    )
    next_song = stream.skip(chat_id, client.me.id)
    mode_ = next_song["mode"]
    type_ = next_song["media_type"]
    name_ = next_song["song_name"]
    singer_ = next_song["singer"]
    dur = next_song["dur"]
    media_link = next_song["url"]
    thumb_ = next_song.get("thumb") or next_song.get("thumbs")
    file_path = next_song["file_name"]
    title_song = f'<a href="{media_link}">{name_}</a>'
    req_id = f"<a href='tg://user?id={client.me.id}'>{client.me.first_name} {client.me.last_name or ''}</a>"
    status = "5258077307985207053" if type_ == "Video" else "5258020476977946656"

    try:
        streaming = await stream.run_stream(file_path, type_)
        await client.group_call.play(chat_id, streaming)
    except Exception as e:
        return await pros.edit(
            f"{emo.gagal}<b>Failed to play the next song: {str(e)}</b>"
        )

    teks = stream.play_text.format(
        mode_, type_, status, title_song, singer_, dur, req_id
    )
    try:
        if thumb_:
            await client.send_photo(chat_id, photo=thumb_, caption=teks)
        else:
            await client.send_message(
                chat_id, teks, disable_web_page_preview=True
            )
    except Exception:
        await client.send_message(chat_id, teks, disable_web_page_preview=True)
    finally:
        # hanya thumbnail yang dihapus; file lagu masih dipakai ffmpeg
        if thumb_ and os.path.exists(str(thumb_)):
            os.remove(thumb_)
    await pros.delete()


async def group_call_ends(client, update):
    chat_id = update.chat_id
    logger.info(f"[DEBUG] stream_end chat={chat_id} update={update}")
    try:
        group_calls_data = stream.get_active_call(chat_id, client.mtproto_client.me.id)
    except Exception as e:
        logger.error(f"Failed to get active call data: {e}")
        return

    if not group_calls_data:
        stream.clear_queue(chat_id, client.mtproto_client.me.id)
        stream.remove_active_call(chat_id, client.mtproto_client.me.id)
        return await client.leave_call(chat_id)

    try:
        c, m = group_calls_data
        play_list = stream.get_queue(chat_id, c.me.id)
    except Exception as e:
        logger.error(f"Error fetching queue: {e}")
        return

    if not play_list or len(play_list) <= 1:
        stream.clear_queue(chat_id, c.me.id)
        stream.remove_active_call(chat_id, c.me.id)
        return await client.leave_call(chat_id)
    try:
        return await skip_songs(c, m.chat.id)
    except Exception as e:
        logger.error(f"Error in skip_cmd: {e}")


# ---------------------------------------------------------------------------
# DIPERBAIKI: play_cmd
# ---------------------------------------------------------------------------
async def _step(coro, seconds, what):
    """Jalankan satu tahap play dengan batas waktu + log, supaya tidak diam selamanya."""
    logger.info(f"play: mulai {what}")
    t0 = time()
    try:
        result = await asyncio.wait_for(coro, timeout=seconds)
    except asyncio.TimeoutError:
        logger.error(f"play: {what} timeout {seconds}s")
        raise RuntimeError(f"{what} timeout {seconds} detik")
    logger.info(f"play: selesai {what} ({time() - t0:.1f}s)")
    return result


# ---------------------------------------------------------------------------
# NEOXR: sumber audio untuk play / cplay (judul)
# ---------------------------------------------------------------------------
NEOX_PLAY = "https://api.neoxr.eu/api/play"


async def _neox_play(query):
    res = await Tools.fetch.get(
        NEOX_PLAY, params={"q": query, "apikey": API_NEOX}, timeout=60
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
    audio_url = info.get("url")
    vid = body.get("id")
    if not audio_url or not vid:
        raise RuntimeError("data audio kosong")

    os.makedirs("downloads", exist_ok=True)
    file_name = f"downloads/{vid}.{info.get('extension') or 'mp3'}"
    timeout = aiohttp.ClientTimeout(total=240, sock_connect=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(audio_url) as resp:
            if resp.status != 200:
                raise RuntimeError(f"unduh audio HTTP {resp.status}")
            async with aiofiles.open(file_name, "wb") as f:
                async for chunk in resp.content.iter_chunked(64 * 1024):
                    await f.write(chunk)

    return (
        file_name,
        "Audio",
        body.get("title"),
        int(body.get("duration_seconds") or 0),
        body.get("views") or "0",
        body.get("channel") or "Unknown",
        f"https://youtu.be/{vid}",
        vid,
        body.get("thumbnail") or f"https://img.youtube.com/vi/{vid}/hqdefault.jpg",
        "",
    )


async def _fetch_media(query, as_video):
    if not as_video:
        try:
            return await _step(_neox_play(query), 300, "download Neoxr")
        except Exception as e:
            logger.warning(f"play: Neoxr gagal ({e}), pakai yt-dlp")
    yt_search = YoutubeSearch(query, max_results=1)
    await _step(yt_search.fetch_results(), 30, "cari YouTube")
    found_link = yt_search.get_link()
    if not found_link:
        raise RuntimeError("Media not found.")
    return await _step(
        youtube.download(found_link, as_video=as_video), 300, "download YouTube"
    )


def _play_buttons(card):
    cid, uid = card["chat_id"], card["ubot"]
    owner_url = (
        f"https://t.me/{card['username']}" if card.get("username") else f"tg://user?id={uid}"
    )
    return ikb([
        [
            ("Skip", f"pl_skip_{cid}_{uid}", ButtonStyle.PRIMARY),
            ("Stop", f"pl_end_{cid}_{uid}", ButtonStyle.DANGER),
        ],
        [
            ("Playlist", f"pl_list_{cid}_{uid}", ButtonStyle.SUCCESS),
            ("Owner", owner_url, "url", ButtonStyle.PRIMARY),
        ],
        [
            ("Close", f"close inline_play {card['uniq']}", ButtonStyle.DANGER),
        ],
    ])

def _to_jpeg(path):
    out = f"{os.path.splitext(path)[0]}_card.jpg"
    Image.open(path).convert("RGB").save(out, "JPEG", quality=90)
    return out


async def _send_play_card(client, message, chat_id, photo, caption):
    """Kirim thumbnail + info + tombol lewat inline bot. Return True kalau berhasil."""
    jpg = None
    try:
        if os.path.exists(str(photo)):
            jpg = await asyncio.to_thread(_to_jpeg, photo)
            url = await Tools.upload_thumb(jpg)
        else:
            url = photo
        uniq = uuid4().hex[:8]
        state.set(uniq, "play_card", {
            "uniq": uniq, "photo": url, "caption": caption, "chat_id": chat_id,
            "ubot": client.me.id, "username": client.me.username,
        })
        return await ButtonUtils.send_inline_bot_result(
            message, message.chat.id, bot.me.username, f"inline_play {uniq}",
            reply_to_message_id=message.id,
        )
    finally:
        if jpg and os.path.exists(jpg):
            os.remove(jpg)

          
async def inline_play(results, inline_query):
    card = state.get(inline_query.query.split()[1], "play_card")
    if not card:
        return results
    results.append(
        InlineQueryResultPhoto(
            photo_url=card["photo"],
            title="Now Playing",
            caption=card["caption"],
            reply_markup=_play_buttons(card),
        )
    )
    return results


async def play_btn_callback(client, callback):
    """pl_<aksi>_<chat_id>_<id_userbot>, aksi: skip | end | list | close"""
    if callback.data.startswith("pl_close_"):
        card = state.get(callback.data.split("_", 2)[2], "play_card")
        if not card:
            return await callback.answer("Kartu sudah kedaluwarsa.", show_alert=True)
        if callback.from_user.id not in (*SUDO_OWNERS, card["ubot"]):
            return await callback.answer("Hanya pemilik userbot yang bisa.", show_alert=True)
        ubot = next((u for u in alice._ubot if u.me.id == card["ubot"]), None)
        info = card.get("msg") or {}
        try:
            await ubot.delete_messages(info["chat"], info["_id"])
            return await callback.answer("Ditutup.")
        except Exception:
            try:
                await callback.edit_message_reply_markup()
            except Exception:
                pass
            return await callback.answer("Tombol dihapus.")

    try:
        _, action, chat_id, uid = callback.data.split("_")
        chat_id, uid = int(chat_id), int(uid)
    except Exception:
        return await callback.answer("Tombol tidak valid", show_alert=True)

    ubot = next((u for u in alice._ubot if u.me.id == uid), None)
    if not ubot:
        return await callback.answer("Userbot tidak aktif.", show_alert=True)

    if action in ("skip", "end") and callback.from_user.id not in (*SUDO_OWNERS, uid):
        return await callback.answer("Hanya pemilik userbot yang bisa.", show_alert=True)

    if action == "list":
        current, upcoming = stream.get_current_and_next_media(chat_id, uid)
        if not current:
            return await callback.answer("Playlist kosong.", show_alert=True)
        lines = [f"▶ {str(current['song_name'])[:40]}"]
        lines += [f"{i}. {str(t['song_name'])[:36]}" for i, t in enumerate(upcoming[:5], 1)]
        return await callback.answer("".join(lines)[:195], show_alert=True)

    if not stream.get_active_call(chat_id, uid):
        return await callback.answer("Tidak ada media yang diputar.", show_alert=True)

    if action == "skip":
        await callback.answer("Skip...")
        return await skip_songs(ubot, chat_id)

    if action == "end":
        try:
            await ubot.group_call.leave_call(chat_id)
        except NotInCallError:
            pass
        except Exception as e:
            return await callback.answer(f"Gagal stop: {str(e)[:150]}", show_alert=True)
        stream.clear_queue(chat_id, uid)
        stream.remove_active_call(chat_id, uid)
        return await callback.answer("Pemutaran dihentikan ✅", show_alert=True)

async def _inline_play_entry(client, inline_query):
    try:
        answers = await inline_play([], inline_query)
        await client.answer_inline_query(inline_query.id, results=answers, cache_time=0)
    except Exception:
        logger.error(f"inline_play: {traceback.format_exc()}")
    raise StopPropagation


async def _play_cb_entry(client, callback):
    try:
        await play_btn_callback(client, callback)
    except Exception:
        logger.error(f"play_btn_callback: {traceback.format_exc()}")
    raise StopPropagation


bot.add_handler(InlineQueryHandler(_inline_play_entry, filters.regex(r"^inline_play ")), group=-1)
bot.add_handler(CallbackQueryHandler(_play_cb_entry, filters.regex(r"^pl_(skip|end|list)_")), group=-1)


async def play_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    audio_original = None
    uploade_r = None
    thumb_media = None
    media_title = None
    dur = None
    thumbs = None
    views = None
    vidid = None
    media_link = None
    pref = client.get_prefix(client.me.id)
    x = next(iter(pref), None)
    rep = message.reply_to_message
    if len(message.command) < 2 and not rep:
        return await message.reply(
            f"{emo.gagal}<b>Use the command by replying to a Music, Video, or provide a youtube title/link</b>"
        )

    pros = await animate_proses(message, emo.proses)

    user_mention = (
        message.sender_chat.title if message.sender_chat else message.from_user.mention
    )

    cmd = message.command[0].lower()
    is_channel_mode = cmd.startswith("c")
    chat_id = (
        await dB.get_var(client.me.id, "CHANNEL")
        if is_channel_mode
        else message.chat.id
    )
    as_video = cmd.startswith("v") or cmd.startswith("cv")
    type_media = "Video" if as_video else "Audio"
    if is_channel_mode:
        chat = await dB.get_var(client.me.id, "CHANNEL")
        if not chat:
            return await pros.edit(
                f"{emo.gagal}<b>You have not linked a Channel for {message.chat.title or 'this Group'}.\n\nUse the following command to link a Channel:\n<code>{x}channelplay linked</code></b>"
            )

    mode = "Channel" if is_channel_mode or message.sender_chat else "Group"

    await pros.edit(f"{emo.proses}<b>Downloading {type_media} for mode: {mode} ..</b>")
    duration_limit = 3 * 3600
    size_limit = 2 * 1024 ** 3
    audio_telegram = (rep.audio or rep.voice) if rep else None
    video_telegram = (rep.video or rep.document) if rep else None

    if audio_telegram:
        type_media = "Audio"
        if (audio_telegram.file_size or 0) > size_limit:
            await pros.edit(
                f"{emo.warn}<b>Audio size is too large! The maximum media size limit is 2GB.</b>"
            )
            return
        if (getattr(audio_telegram, "duration", 0) or 0) > duration_limit:
            await pros.edit(
                f"{emo.warn}<b>Audio duration is too long! The maximum media duration limit is 3 hours.</b>"
            )
            return
        file_path = await telegram.get_filepath(audio=audio_telegram)
        try:
            await telegram.download(client, message, pros, file_path)
            audio_original = file_path
        except Exception as e:
            await pros.edit(
                f"{emo.gagal}<b>Error occurred while downloading Telegram Audio:\n\n<code>{e}</code></b>"
            )
            return
        media_link = await telegram.get_link(message)
        media_title = await telegram.get_filename(audio_telegram, audio=True)
        dur = await telegram.get_duration(audio_telegram, file_path)
        a_thumbs = getattr(audio_telegram, "thumbs", None)
        file = await client.download_media(a_thumbs[-1].file_id) if a_thumbs else None
        thumbs = await Tools.upload_thumb(file) if file else URL_LOGO
        vidid = int(uuid4())
        views = Tools.gen_views()
        uploade_r = "Audio Telegram"

    elif video_telegram:
        type_media = "Video"
        if rep.document:
            try:
                ext = (video_telegram.file_name or "").split(".")[-1]
                if ext.lower() not in Tools.formats:
                    await pros.edit(
                        f"{emo.warn}<b>Unknown media format! Here is the list of supported media Tools.formats: {' | '.join(Tools.formats)}</b>"
                    )
                    return
            except Exception as e:
                await pros.edit(
                    f"{emo.gagal}<b>Error occurred while downloading Telegram Video:\n\n<code>{e}</code></b>"
                )
                return
        if (video_telegram.file_size or 0) > size_limit:
            await pros.edit(
                f"{emo.warn}<b>Video size is too large! The maximum media size limit is 2GB.</b>"
            )
            return
        if (getattr(video_telegram, "duration", 0) or 0) > duration_limit:
            await pros.edit(
                f"{emo.warn}<b>Video duration is too long! The maximum media duration limit is 3 hours.</b>"
            )
            return
        file_path = await telegram.get_filepath(video=video_telegram)
        try:
            await telegram.download(client, message, pros, file_path)
            audio_original = file_path
        except Exception as e:
            await pros.edit(
                f"{emo.gagal}<b>Error occurred while downloading Telegram Video:\n\n<code>{e}</code></b>"
            )
            return
        media_link = await telegram.get_link(message)
        media_title = await telegram.get_filename(video_telegram)
        dur = await telegram.get_duration(video_telegram, file_path)
        v_thumbs = getattr(video_telegram, "thumbs", None)
        file = await client.download_media(v_thumbs[-1].file_id) if v_thumbs else None
        thumbs = await Tools.upload_thumb(file) if file else URL_LOGO
        uploade_r = "Video Telegram"
        vidid = int(uuid4())
        views = Tools.gen_views()

    else:
        try:
            gt_txt = client.get_text(message)
            if await Spotify.valid(gt_txt):
                if "track" in gt_txt:
                    data_spotify = await Spotify.track(gt_txt)
                    if data_spotify is None:
                        return await pros.edit(f"{emo.gagal}**Sorry, try another url!!**")
                    media_title = data_spotify.get("title")
                    audio_original = data_spotify.get("file_path")
                    vidid = data_spotify.get("vidid")
                    dur = data_spotify.get("duration")
                    thumbs = data_spotify.get("thumbs")
                    uploade_r = ", ".join(data_spotify.get("uploader") or [])
                    media_link = data_spotify.get("url")
                    views = Tools.gen_views()
                elif "playlist" in gt_txt:
                    playlist = await Spotify.playlist(gt_txt)
                    if not playlist:
                        return await pros.edit(f"{emo.gagal}**Sorry, try another url!!**")
                    await pros.edit(
                        f"{emo.proses}**Processing playlist with `{len(playlist)}` songs...**"
                    )
                    first_song = playlist[0]
                    track_title = first_song["title"]
                    yt_search = YoutubeSearch(track_title, max_results=1)
                    await yt_search.fetch_results()
                    media_title = yt_search.get_title()
                    audio_original = yt_search.get_link()
                    dur = yt_search.get_duration()
                    uploade_r = yt_search.get_channel()
                    media_link = yt_search.get_link()
                    vidid = first_song["track_id"]
                    thumbs = yt_search.get_thumbnail() or URL_LOGO
                    views = Tools.gen_views()

                    async def process_remaining_songs():
                        try:
                            await asyncio.sleep(5)
                            for media in playlist[1:]:
                                track_title = media["title"]
                                yt_s = YoutubeSearch(track_title, max_results=1)
                                await yt_s.fetch_results()
                                q_info = {
                                    "song_name": yt_s.get_title(),
                                    "file_name": yt_s.get_link(),
                                    "singer": yt_s.get_channel(),
                                    "dur": yt_s.get_duration(),
                                    "url": yt_s.get_link(),
                                    "thumb": yt_s.get_thumbnail() or URL_LOGO,
                                    "mode": mode,
                                    "media_type": type_media,
                                }
                                stream.add_to_queue(chat_id, client.me.id, q_info)
                                await asyncio.sleep(0.5)
                            await message.reply(
                                f"{emo.sukses}**Successfully added `{len(playlist)-1}` more songs to queue from playlist**"
                            )
                        except Exception as e:
                            logger.error(f"Error processing playlist: {str(e)}")

                    asyncio.create_task(process_remaining_songs())
                else:
                    return await pros.edit(
                        f"{emo.gagal}<b>Only Spotify track and playlist links are supported.</b>"
                    )
            elif await youtube.valid(gt_txt):
                (
                    audio_original,
                    __,
                    media_title,
                    duration,
                    views,
                    uploade_r,
                    media_link,
                    vidid,
                    thumbs,
                    __,
                ) = await _step(youtube.download(gt_txt, as_video=as_video), 300, "download YouTube")
                dur = Tools.seconds_to_min(duration)
            else:
                # judul -> Neoxr (audio); video / Neoxr gagal -> yt-dlp
                (
                    audio_original,
                    __,
                    media_title,
                    duration,
                    views,
                    uploade_r,
                    media_link,
                    vidid,
                    thumbs,
                    __,
                ) = await _fetch_media(gt_txt, as_video)
                dur = Tools.seconds_to_min(duration)
                logger.info(f"Apa itu vidid: {vidid}")
        except Exception as e:
            # dulu error di sini hanya masuk LOG_BACKUP -> user lihat "Downloading..." terus
            logger.error(f"play: gagal ambil media: {traceback.format_exc()}")
            return await pros.edit(
                f"{emo.gagal}<b>Gagal mengambil media:</b>\n<code>{escape(str(e))[:3500]}</code>"
            )

    data = {
        "title": media_title,
        "duration": dur,
        "thumbnail": thumbs,
        "views": views,
        "channel": uploade_r,
    }
    state.set(client.me.id, "GEN_THUMB", data)
    thumb_err = None
    try:
        await pros.edit(f"{emo.proses}<b>Membuat thumbnail...</b>")
        thumb_media = await _step(gen_qthumb(client, vidid), 30, "gen_qthumb")
    except Exception as e:
        thumb_err = f"{type(e).__name__}: {e}"
        logger.error(f"play: gen_qthumb gagal: {traceback.format_exc()}")
        thumb_media = thumbs or URL_LOGO

    jadul = f"<a href='{media_link}'>{media_title}</a>"
    f_info = {
        "song_name": media_title,
        "file_name": audio_original,
        "singer": uploade_r,
        "dur": dur,
        "url": media_link,
        "thumb": thumb_media,
        "mode": mode,
        "media_type": type_media,
    }
    group_calls = stream.get_active_call(chat_id, client.me.id)
    if not group_calls:
        try:
            await pros.edit(f"{emo.proses}<b>Naik obrolan suara...</b>")
            logger.info(f"play: join VC {chat_id} file={audio_original}")
            streaming = await stream.run_stream(audio_original, type_media)
            # batasi waktu join: kalau macet, user tetap dapat respon
            await asyncio.wait_for(client.group_call.play(chat_id, streaming), timeout=60)
        except asyncio.TimeoutError:
            logger.error(f"play: join VC {chat_id} timeout")
            return await pros.edit(
                f"{emo.gagal}<b>Gagal naik obrolan suara (timeout 60 detik).</b>"
            )
        except Exception as e:
            logger.error(f"Failed to play: {traceback.format_exc()}")
            return await pros.edit(
                f"{emo.gagal}<b>Failed to play:\n<code>{e}</code></b>"
            )
        stream.add_active_call(chat_id, client.me.id, client, message)
        stream.add_to_queue(chat_id, client.me.id, f_info)
        status = (
            "5258077307985207053" if type_media == "Video" else "5258020476977946656"
        )
        teks = stream.play_text.format(
            mode, type_media, status, jadul, uploade_r, dur, user_mention
        )
        if thumb_err:   # sementara, untuk melacak kenapa thumbnail gagal dibuat
            teks += f"\n<code>[thumbnail gagal: {escape(thumb_err)[:160]}]</code>"

        sent, card_err = False, None
        try:
            sent = await _send_play_card(client, message, chat_id, thumb_media, teks)
            if not sent:
                card_err = "inline bot tidak mengembalikan hasil"
        except Exception as e:
            card_err = f"{type(e).__name__}: {e}"
            logger.error(f"play: kartu tombol gagal: {traceback.format_exc()}")
        if not sent:
            teks_fb = teks
            if card_err:
                teks_fb += f"\n<code>[tombol gagal: {escape(card_err)[:180]}]</code>"
            try:
                await message.reply_photo(photo=thumb_media, caption=teks_fb)
            except FloodWait as e:
                await asyncio.sleep(int(e.value))
            except Exception:
                await message.reply(teks_fb, disable_web_page_preview=True)
        return await pros.delete()
    else:
        stream.add_to_queue(chat_id, client.me.id, f_info)
        data = stream.get_queue(chat_id, client.me.id)
        return await pros.edit(
            f"{emo.sukses}<b>Added to queue #{len(data)}:</b> {jadul} | {type_media}",
            disable_web_page_preview=True,
        )


async def resume_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    cmd = message.command[0].lower()
    is_channel_mode = cmd.startswith("c")
    chat_id = (
        await dB.get_var(client.me.id, "CHANNEL")
        if is_channel_mode
        else message.chat.id
    )
    group_calls = stream.get_active_call(chat_id, client.me.id)
    if not group_calls:
        return await message.reply(f"{emo.gagal}<b>Is not playing the media. </b>")
    queue = stream.get_queue(chat_id, client.me.id)
    current_media = queue[0]
    current_song_name = current_media["song_name"]
    current_singer = current_media["singer"]
    current_dur = current_media["dur"]
    resumed = "<b>ðŸŽ§ Continued playing</b>\n"
    resumed += f"ðŸŽµ Title: <code>{current_song_name}</code>\n"
    resumed += f"ðŸŽ¤ Singer: <code>{current_singer}</code>\n"
    resumed += f"â²ï¸ Duration: <code>{current_dur}</code></b>\n"
    try:
        await client.group_call.resume_stream(chat_id)
        return await message.reply(f"{resumed}")
    except Exception as e:
        return await message.reply(
            f"{emo.gagal}<b>Failed to continue the media:</b>\n<code>{str(e)}</code>"
        )


async def end_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    cmd = message.command[0].lower()
    is_channel_mode = cmd.startswith("c")
    chat_id = (
        await dB.get_var(client.me.id, "CHANNEL")
        if is_channel_mode
        else message.chat.id
    )
    group_calls = stream.get_active_call(chat_id, client.me.id)
    if not group_calls:
        return await message.reply(f"{emo.gagal}<b>Is not playing the media.</b>")
    try:
        await client.group_call.leave_call(chat_id)
        stream.clear_queue(chat_id, client.me.id)
        stream.remove_active_call(chat_id, client.me.id)
        return await message.reply(
            f"{emo.sukses}<b>Successfully stopped the media.</b>"
        )
    except NotInCallError:
        return await message.reply(f"{emo.gagal}<b>Is not playing the media.</b>")
    except Exception as e:
        return await message.reply(
            f"{emo.gagal}<b>Failed to stop the media:\n<code>{str(e)}</code></b>"
        )


async def pause_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    cmd = message.command[0].lower()
    is_channel_mode = cmd.startswith("c")
    chat_id = (
        await dB.get_var(client.me.id, "CHANNEL")
        if is_channel_mode
        else message.chat.id
    )
    group_calls = stream.get_active_call(chat_id, client.me.id)
    if not group_calls:
        return await message.reply(f"{emo.gagal}<b>Is not playing the media.</b>")
    queue = stream.get_queue(chat_id, client.me.id)
    current_media = queue[0]
    current_song_name = current_media["song_name"]
    current_singer = current_media["singer"]
    current_dur = current_media["dur"]
    paused = "<b>ðŸŽ§ Paused playing</b>\n"
    paused += f"ðŸŽµ Title: <code>{current_song_name}</code>\n"
    paused += f"ðŸŽ¤ Singer: <code>{current_singer}</code>\n"
    paused += f"â²ï¸ Duration: <code>{current_dur}</code></b>\n"
    try:
        await client.group_call.pause_stream(chat_id)
        return await message.reply(f"{paused}")
    except Exception as e:
        return await message.reply(f"Failed to break the media:</b>\n<code>{e}</code>")


# ---------------------------------------------------------------------------
# DIPERBAIKI: skip_cmd
# ---------------------------------------------------------------------------
async def skip_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    await Tools.get_logo()
    cmd = message.command[0].lower()
    is_channel_mode = cmd.startswith("c")
    chat_id = (
        await dB.get_var(client.me.id, "CHANNEL")
        if is_channel_mode
        else message.chat.id
    )
    group_calls = stream.get_active_call(chat_id, client.me.id)
    queue = stream.get_queue(chat_id, client.me.id)

    if not group_calls:
        return await message.reply(f"{emo.gagal}<b>While no media is played.</b>")

    if not queue or len(queue) <= 1:
        return await message.reply(f"{emo.gagal}<b>There is no next track.</b>")
    pros = await message.reply(
        f"{emo.proses}<b>The process of turning the next media...</b>"
    )

    next_song = stream.skip(chat_id, client.me.id)
    mode_ = next_song["mode"]
    type_ = next_song["media_type"]
    name_ = next_song["song_name"]
    singer_ = next_song["singer"]
    dur = next_song["dur"]
    media_link = next_song["url"]
    thumb_ = next_song.get("thumb") or next_song.get("thumbs")
    file_path = next_song["file_name"]
    title_song = f'<a href="{media_link}">{name_}</a>'
    if message.from_user:
        req_id = f"<a href='tg://user?id={message.from_user.id}'>{message.from_user.first_name} {message.from_user.last_name or ''}</a>"
    else:
        req_id = message.sender_chat.title if message.sender_chat else "Unknown"
    status = "5258077307985207053" if type_ == "Video" else "5258020476977946656"

    try:
        streaming = await stream.run_stream(file_path, type_)
        await client.group_call.play(chat_id, streaming)
    except Exception as e:
        return await pros.edit(
            f"{emo.gagal}<b>Failed to play the next song: {str(e)}</b>"
        )

    teks = stream.play_text.format(
        mode_, type_, status, title_song, singer_, dur, req_id
    )
    try:
        if thumb_:
            await message.reply_photo(photo=thumb_, caption=teks)
        else:
            await message.reply(teks, disable_web_page_preview=True)
    except Exception:
        await message.reply(teks, disable_web_page_preview=True)
    finally:
        # hanya thumbnail yang dihapus; file lagu masih dipakai ffmpeg
        if thumb_ and os.path.exists(str(thumb_)):
            os.remove(thumb_)
    await pros.delete()


async def playlist_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    logo = await Tools.get_logo()
    cmd = message.command[0].lower()
    is_channel_mode = cmd.startswith("c")
    chat_id = (
        await dB.get_var(client.me.id, "CHANNEL")
        if is_channel_mode
        else message.chat.id
    )
    group_calls = stream.get_active_call(chat_id, client.me.id)
    if not group_calls:
        return await message.reply(f"{emo.gagal}<b>While no media is played.</b>")

    pros = await message.reply(
        f"{emo.proses}<b>The process of taking a playlist...</b>"
    )

    current_media, next_media_list = stream.get_current_and_next_media(
        chat_id, client.me.id
    )
    if not current_media:
        return await pros.edit(f"{emo.gagal}<b>There is no media in the queue.</b>")

    current_song_name = current_media["song_name"]
    current_singer = current_media["singer"]
    current_dur = current_media["dur"]
    current_thumb = current_media.get("thumb", None)

    playlist = "<b>ðŸŽ§ Currently playing</b>\n"
    playlist += f"ðŸŽµ Title: <code>{current_song_name}</code>\n"
    playlist += f"ðŸŽ¤ Singer: <code>{current_singer}</code>\n"
    playlist += f"â²ï¸ Duration: <code>{current_dur}</code>\n\n"

    if next_media_list:
        playlist += "<b>ðŸŽ§ Playlist</b>\n"
        for count, track in enumerate(next_media_list, start=1):
            lagu = track["song_name"]
            if count == len(next_media_list):
                playlist += f"<code>{lagu}</code>\n"
            else:
                playlist += f"<code>{lagu}</code>\n"

    try:
        if current_thumb:
            await message.reply_photo(
                photo=current_thumb,
                caption=f"{playlist}",
            )
        else:
            await message.reply_photo(
                photo=logo,
                caption=f"{playlist}",
            )
        return await pros.delete()
    except Exception as e:
        return await pros.edit(f"{playlist}")


async def volume_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    cmd = message.command[0].lower()
    is_channel_mode = cmd.startswith("c")
    chat_id = (
        await dB.get_var(client.me.id, "CHANNEL")
        if is_channel_mode
        else message.chat.id
    )
    nilai = client.get_text(message)
    if not nilai:
        return await message.reply(
            f"{emo.gagal}<b>Give numbers from 1 - 200 to change the volume of media.</b>"
        )
    group_calls = stream.get_active_call(chat_id, client.me.id)
    if not group_calls:
        return await message.reply(f"{emo.gagal}<b>Is not playing the media.</b>")
    try:
        await client.group_call.change_volume_call(chat_id, int(nilai))
        return await message.reply(
            f"{emo.sukses}<b>Succeeded in setting the volume of the media to be: <code>{nilai}%</code></b>"
        )
    except Exception as e:
        if "USER_VOLUME_INVALID" in str(e):
            return await message.reply(
                f"{emo.gagal}<b>Give numbers from 1 - 200 to change the volume of media.</b>"
            )
        return await message.reply(
            f"{emo.gagal}<b>Failed to use volume:\n<code>{str(e)}</code></b>"
        )


async def channelplay_cmd(client, message):
    emo = Emoji(client)
    await emo.get()
    pref = client.get_prefix(client.me.id)
    x = next(iter(pref))
    if len(message.command) not in [2, 3]:
        return await message.reply(
            f"{emo.warn}<b>You can play music on channels that are already connected to {message.chat.title or 'chat room'}.\n\nUse the following command if the channel is connected:\n<code>{x}channelplay linked</code></b>"
        )
    query = message.text.split(None, 2)[1].lower().strip()
    if str(query) == "disable":
        await dB.remove_var(client.me.id, "CHANNEL")
        return await message.reply(
            f"{emo.sukses}<b>Managed to stop and remove playback through the channel.</b>"
        )

    elif str(query) == "linked":
        try:
            chat = await client.get_chat(message.chat.id)
        except Exception as e:
            return await message.reply(
                f"{emo.gagal}<b>Error:\n<code>{str(e)}</code></b>"
            )

        if chat and chat.linked_chat:
            channel_id = chat.linked_chat.id
            try:
                members = await client.get_chat_member(channel_id, client.me.id)
                if not members.privileges.can_manage_video_chats:
                    return await message.reply(
                        f"{emo.gagal}<b>Make me an admin with permission to manage voting chat.</b>"
                    )
                await dB.set_var(client.me.id, "CHANNEL", channel_id)

                return await message.reply(
                    f"{emo.sukses}<b>Successfully set {chat.linked_chat.title} as a music playback channel.</b>"
                )
            except Exception as e:
                return await message.reply(
                    f"{emo.gagal}<b>There is an error:\n\n<code>{e}</code></b>"
                )
        else:
            if len(message.command) < 3:
                return await message.reply(
                    f"{emo.gagal}**Please user command `{message.text.split()[0]} linked` @devasupport"
                )
            chat_id = message.text.split()[2]
            try:
                if "/+" in str(chat_id):
                    gid = await client.get_chat(str(chat_id))
                    chat_id = int(gid.id)
                elif "t.me/" in str(chat_id) or "@" in str(chat_id):
                    chat_id = chat_id.replace("https://t.me/", "")
                    gid = await client.get_chat(str(chat_id))
                    chat_id = int(gid.id)
                else:
                    chat_id = int(chat_id)
                await dB.set_var(client.me.id, "CHANNEL", chat_id)
                return await message.reply(
                    f"{emo.sukses}<b>Successfully set {chat_id} as a music playback channel.</b>"
                )
            except Exception as err:
                return await message.reply(
                    f"{emo.gagal}<b>Cannot connect {chat_id}\nError: `{str(err)}`</b>"
                )

    elif str(query) == "status":
        mode = await dB.get_var(client.me.id, "CHANNEL")
        if not mode:
            return await message.reply(f"{emo.gagal}<b>No channel is linked.</b>")
        else:
            try:
                chat = await client.get_chat(int(mode))
                return await message.reply(
                    f"{emo.sukses}<b>Group {message.chat.title or 'this group'} is connected to:</b> {chat.title}"
                )
            except Exception as e:
                return await message.reply(
                    f"{emo.gagal}<b>There is an error:\n\n<code>{str(e)}</code></b>"
                )

    else:
        return await message.reply(f"{emo.gagal}<b>Invalid query!</b>")