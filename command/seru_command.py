import asyncio
import re
import traceback
from datetime import datetime
from html import escape

from pyrogram import raw
from pyrogram.errors import FloodWait
from pyrogram.types import InputChatPhotoPrevious, InputChatPhotoStatic

from database import dB
from helpers import Emoji, Tools, animate_proses
from helpers.fakex_render import ensure_fonts, render_fake_post
from logs import logger

# opsi hanya dibaca di depan teks
FAKEX_OPTIONS = {"dark", "dim", "light"}  # tema; centang biru & logo X selalu tampil
MAX_TEXT = 1000


def _parse(raw):
    """'.fakex dark Halo' -> ({'dark'}, 'Halo')"""
    parts = raw.split(None, 1)[1].split(" ") if len(raw.split(None, 1)) > 1 else []
    opts = set()
    while parts and parts[0].lower() in FAKEX_OPTIONS:
        opts.add(parts.pop(0).lower())
    return opts, " ".join(parts).strip()


def _identity(entity):
    """(nama tampilan, username) dari User atau Chat (sender_chat)."""
    name = " ".join(filter(None, [getattr(entity, "first_name", None),
                                  getattr(entity, "last_name", None)]))
    name = name or getattr(entity, "title", "") or "User"
    handle = getattr(entity, "username", None) or re.sub(r"\W+", "", name.lower())[:15]
    return name, handle or "user"


async def _download(client, file_id):
    if not file_id:
        return None
    try:
        return await client.download_media(file_id, in_memory=True)
    except Exception:
        logger.warning(f"fakex: gagal unduh media: {traceback.format_exc()}")
        return None


async def fakex_cmd(client, message):
    em = Emoji(client)
    await em.get()
    raw = message.text or message.caption or ""
    proses = await animate_proses(message, em.proses)

    opts, text = _parse(raw)
    rep = message.reply_to_message
    if not text and rep:
        text = (rep.text or rep.caption or "").strip()
    if not text:
        return await proses.edit(
            f"{em.gagal}<b>Tulis isi postingannya!</b>\n"
            f"Contoh: <code>{raw.split()[0]} dark Halo dunia 🔥</code>\n"
            f"Reply orang = pakai nama &amp; foto profilnya."
        )
    if len(text) > MAX_TEXT:
        return await proses.edit(f"{em.gagal}<b>Teks maksimal {MAX_TEXT} karakter.</b>")

    # identitas: user yang di-reply, kalau tidak ada = diri sendiri
    target = (rep.from_user or rep.sender_chat) if rep else (message.from_user or message.sender_chat)
    name, handle = _identity(target)

    try:
        await ensure_fonts(Tools.fetch)
        photo = getattr(target, "photo", None)
        avatar = await _download(client, photo.big_file_id if photo else None)
        media_msg = rep if rep and rep.photo else (message if message.photo else None)
        media = await _download(client, media_msg.photo.file_id) if media_msg else None

        image = await asyncio.to_thread(
            render_fake_post, name, handle, text,
            avatar=avatar,
            media=media,
            theme=next((t for t in ("dark", "dim", "light") if t in opts), "light"),
            verified=True,
            xbadge=True,
            when=datetime.now(Tools.JAKARTA_TZ),
        )
        await message.reply_photo(image)
        return await proses.delete()
    except Exception as e:
        logger.error(f"fakex gagal: {traceback.format_exc()}")
        return await proses.edit(f"{em.gagal}<b>ERROR:</b> <code>{escape(str(e))}</code>")


_CLONE_RUNNING = set()
_CLONE_BACKUP = "CLONE_PROFILE_BACKUP"


async def _profile_photos(client):
    photos = {}
    async for photo in client.get_chat_photos("me"):
        original = await InputChatPhotoPrevious(photo.file_id).write(client)
        photos[original.id] = photo
    return photos


async def _backup_profile(client):
    backup = await dB.get_var(client.me.id, _CLONE_BACKUP)
    if backup is not None:
        if not isinstance(backup, dict) or backup.get("version") != 1:
            raise RuntimeError("Format backup profil tidak valid; backup tidak ditimpa.")
        if backup.get("photo_pending"):
            raise RuntimeError("Unggahan foto sebelumnya belum pasti tercatat. Backup dipertahankan; periksa foto profil dahulu.")
        return backup
    me = await client.get_me()
    profile = await client.get_chat("me")
    photo_id = None
    async for photo in client.get_chat_photos("me", limit=1):
        original = await InputChatPhotoPrevious(photo.file_id).write(client)
        photo_id = original.id
        break
    if profile.photo and photo_id is None:
        raise RuntimeError("Foto profil awal tidak berhasil dibaca; clone dibatalkan.")
    backup = {
        "version": 1, "first_name": me.first_name or "", "last_name": me.last_name or "",
        "bio": profile.bio or "", "photo_id": photo_id, "clone_photo_ids": [], "photo_pending": False,
    }
    await dB.set_var(client.me.id, _CLONE_BACKUP, backup)
    return backup


async def _profile_error(message, status, action, stage, done, error):
    changed = escape(", ".join(done) if done else "belum ada")
    reason = (
        f"Tunggu {error.value} detik sebelum mencoba lagi."
        if isinstance(error, FloodWait) else f"{type(error).__name__}: {str(error)[:300]}"
    )
    text = (
        f"<b>{action} belum selesai.</b>\n<b>Tahap:</b> {escape(stage)}\n"
        f"<b>Sudah berubah:</b> {changed}\n<code>{escape(reason)}</code>\n"
        "Backup yang tersedia dipertahankan."
    )
    return await status.edit_text(text) if status is not None else await message.reply(text)


async def clone_cmd(client, message):
    sender = message.from_user
    if sender is None or sender.id != client.me.id:
        return await message.reply("<b>Clone hanya untuk pemilik akun userbot.</b>")
    reply = message.reply_to_message
    target = getattr(reply, "from_user", None)
    if reply is None or getattr(reply, "empty", False) or target is None:
        return await message.reply("<b>Raply user!.</b>")
    if target.id == client.me.id:
        return await message.reply("<b>Gausah clone profil sendiri.</b>")
    if target.is_bot or target.is_deleted:
        return await message.reply("<b>Target harus user aktif, bukan bot.</b>")
    account_id = client.me.id
    if account_id in _CLONE_RUNNING:
        return await message.reply("<b>Proses clone/restore sebelumnya masih berjalan.</b>")
    _CLONE_RUNNING.add(account_id)
    status = photo = None
    done = []
    stage = "membaca profil"
    try:
        status = await message.reply("<b>Loading...</b>")
        user = await client.get_users(target.id)
        profile = await client.get_chat(target.id)
        first_name, last_name, bio = user.first_name or "", user.last_name or "", profile.bio or ""
        if not first_name.strip():
            return await status.edit_text("<b>Nama target tidak tersedia. Profil tidak diubah.</b>")
        file_id = getattr(getattr(profile, "photo", None), "big_file_id", None)
        if file_id:
            stage = "mengunduh foto profil"
            photo = await client.download_media(file_id, in_memory=True)
            if photo is None:
                raise RuntimeError("Foto profil gagal diunduh.")
            photo.name = "clone_profile.jpg"
            photo.seek(0)
        stage = "menyimpan backup profil awal"
        backup = await _backup_profile(client)
        stage = "mengubah nama dan bio"
        if not await client.update_profile(first_name=first_name, last_name=last_name, bio=bio):
            raise RuntimeError("Telegram tidak mengonfirmasi perubahan profil.")
        done.extend(("nama", "bio"))
        if photo is not None:
            stage = "memasang dan mencatat foto clone"
            uploaded_file = await InputChatPhotoStatic(photo=photo).write(client)
            backup["photo_pending"] = True
            await dB.set_var(account_id, _CLONE_BACKUP, backup)
            try:
                result = await client.invoke(raw.functions.photos.UploadProfilePhoto(file=uploaded_file))
            except FloodWait:
                backup["photo_pending"] = False
                await dB.set_var(account_id, _CLONE_BACKUP, backup)
                raise
            done.append("foto profil")
            backup["clone_photo_ids"].append(result.photo.id)
            backup["photo_pending"] = False
            await dB.set_var(account_id, _CLONE_BACKUP, backup)
        name = escape(f"{first_name} {last_name}".strip())
        photo_result = "Berhasil disalin." if photo is not None else "Tidak tersedia/tersembunyi; foto akunmu tidak diubah."
        return await status.edit_text(
            "<b>Clone success.</b>\n"
            f"<b>Target:</b> {name}</b>.\n"
            "Gunakan perintah restore untuk kembali."
        )
    except Exception as error:
        return await _profile_error(message, status, "Clone", stage, done, error)
    finally:
        _CLONE_RUNNING.discard(account_id)
        if photo is not None:
            photo.close()


async def restore_profile_cmd(client, message):
    sender = message.from_user
    if sender is None or sender.id != client.me.id:
        return await message.reply("<b>Restore hanya untuk pemilik akun userbot.</b>")
    account_id = client.me.id
    if account_id in _CLONE_RUNNING:
        return await message.reply("<b>Proses clone/restore sebelumnya masih berjalan.</b>")
    _CLONE_RUNNING.add(account_id)
    status = None
    done = []
    stage = "membaca backup"
    try:
        backup = await dB.get_var(account_id, _CLONE_BACKUP)
        if backup is None:
            return await message.reply(
                "<b>Belum ada backup profil.</b>."
            )
        if not isinstance(backup, dict) or backup.get("version") != 1:
            raise RuntimeError("Format backup profil tidak valid.")
        if backup.get("photo_pending"):
            raise RuntimeError("Ada unggahan foto yang belum pasti tercatat. Backup dipertahankan; periksa foto profil dahulu.")
        status = await message.reply("<b>Sedang memulihkan profil awal...</b>")
        stage = "memeriksa foto profil awal"
        photos = await _profile_photos(client)
        original_id = backup["photo_id"]
        clone_ids = set(backup["clone_photo_ids"])
        if original_id is not None and original_id not in photos:
            raise RuntimeError("Foto profil awal tidak ada lagi di Telegram. Backup tetap disimpan.")
        if original_id is None and set(photos) - clone_ids:
            raise RuntimeError("Ada foto tambahan bukan hasil clone; tidak dihapus otomatis. Backup tetap disimpan.")
        stage = "memulihkan nama dan bio"
        if not await client.update_profile(
            first_name=backup["first_name"], last_name=backup["last_name"], bio=backup["bio"],
        ):
            raise RuntimeError("Telegram tidak mengonfirmasi pemulihan profil.")
        done.extend(("nama", "bio"))
        stage = "memulihkan foto profil"
        if original_id is not None and next(iter(photos), None) != original_id:
            if not await client.set_profile_photo(photo=InputChatPhotoPrevious(photos[original_id].file_id)):
                raise RuntimeError("Telegram tidak mengonfirmasi pemulihan foto.")
        cloned = [p.file_id for key, p in photos.items() if key in clone_ids and key != original_id]
        if cloned and not await client.delete_profile_photos(cloned):
            raise RuntimeError("Foto hasil clone belum berhasil dihapus; ulangi restore.")
        done.append("foto profil")
        stage = "menyelesaikan restore"
        await dB.remove_var(account_id, _CLONE_BACKUP)
        return await status.edit_text(
            "<b>Restore profile successfully.</b>"
        )
    except Exception as error:
        return await _profile_error(message, status, "Restore", stage, done, error)
    finally:
        _CLONE_RUNNING.discard(account_id)