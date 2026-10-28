import asyncio
import os
import sys
import traceback
import zipfile
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from pyrogram import enums
from pyrogram.helpers import kb
from pytz import timezone

from clients import bot, alice
from config import (AKSES_DEPLOY, BOT_ID, BOT_NAME, LOG_BACKUP, LOG_SELLER,
                    OWNER_ID)
from database import DB_PATH, dB
from logs import logger

from .auto_referal import TokenReferal
from .message import Message

waktu_jkt = timezone("Asia/Jakarta")


def find_env_file():
    for file in os.listdir():
        if file.endswith(".env"):
            return os.path.abspath(file)
    return None


async def load_user_allchats(client):
    private = []
    group = []
    globall = []
    all = []
    bots = []
    try:
        async for dialog in client.get_dialogs():
            try:
                if dialog.chat.type == enums.ChatType.PRIVATE:
                    private.append(dialog.chat.id)
                elif dialog.chat.type in (
                    enums.ChatType.GROUP,
                    enums.ChatType.SUPERGROUP,
                ):
                    group.append(dialog.chat.id)
                elif dialog.chat.type in (
                    enums.ChatType.GROUP,
                    enums.ChatType.SUPERGROUP,
                    enums.ChatType.CHANNEL,
                ):
                    globall.append(dialog.chat.id)
                elif dialog.chat.type in (
                    enums.ChatType.GROUP,
                    enums.ChatType.SUPERGROUP,
                    enums.ChatType.PRIVATE,
                ):
                    all.append(dialog.chat.id)
                if dialog.chat.type == enums.ChatType.BOT:
                    bots.append(dialog.chat.id)
            except Exception:
                continue
    except Exception:
        pass
    return private, group, globall, all, bots


async def installing_user(client):
    private, group, globall, all, bots = await load_user_allchats(client)
    client_id = client.me.id
    client._get_my_peer[client_id] = {
        "private": private,
        "group": group,
        "global": globall,
        "all": all,
        "bot": bots,
    }


async def installPeer():
    try:
        for client in alice._ubot:
            await installing_user(client)
    except Exception as er:
        await bot.send_message(
            OWNER_ID, f"Error installPeer {str(er)}, {sys.exc_info()[-1].tb_lineno}"
        )
    await bot.send_message(OWNER_ID, "✅ Sukses Install Data Pengguna.")


async def sending_user(user_id):
    try:
        return await bot.send_message(
            user_id,
            f"<blockquote><b>Akun anda tidak dapat memberikan Respon!!\n\nHarap Hentikan Sesi Perangkat dengan nama <code>{BOT_NAME}</code>. Lalu, lakukan Re-Deploy atau klik Lanjut Pembuatan Ulang Userbot di bawah (JIKA MERASA ANDA MASIH MEMILIKI SISA WAKTU EXPIRED USERBOT).</b></blockquote>",
            reply_markup=kb(
                [["✨ Pembuatan Ulang Userbot"]],
                resize_keyboard=True,
                one_time_keyboard=True,
            ),
        )
    except Exception:
        return


async def CheckUsers():
    while True:
        total = await dB.get_var(BOT_ID, "total_users")
        try:
            if len(alice._ubot) != total:
                now = datetime.now(timezone("Asia/Jakarta"))
                timestamp = now.strftime("%Y-%m-%d_%H:%M")
                zip_filename = f"{BOT_NAME}_{timestamp}.zip"
                with zipfile.ZipFile(zip_filename, "w", zipfile.ZIP_DEFLATED) as zipf:
                    if os.path.exists(".env"):
                        env_path = os.path.abspath(".env")
                        token_path = os.path.abspath("token.json")
                        zipf.write(env_path, os.path.basename(env_path))
                        zipf.write(DB_PATH, os.path.basename(DB_PATH))
                        zipf.write(token_path, os.path.basename(token_path))
                    else:
                        token_path = os.path.abspath("token.json")
                        zipf.write(DB_PATH, os.path.basename(DB_PATH))
                        zipf.write(token_path, os.path.basename(token_path))
                caption = now.strftime("%d %B %Y %H:%M")
                await bot.send_document(LOG_BACKUP, zip_filename, caption=caption)
                os.remove(zip_filename)
                return
        except Exception as e:
            return await bot.send_message(LOG_SELLER, f"CheckUsers error: {str(e)}")
        await asyncio.sleep(360)


EXPIRED_CHECK_EVERY = 60   # detik; dulu 1 detik (baca DB + token.json tiap userbot tiap detik)


async def ExpiredUser():
    while True:
        now = datetime.now(timezone("Asia/Jakarta"))
        for client in list(alice._ubot):          # salinan: list diubah saat ada yang expired
            try:
                exp = await dB.get_expired_date(client.me.id)
                if not exp or now < exp:
                    continue
                tokenref = await TokenReferal.create()   # baca token.json hanya saat dibutuhkan
                msg = Message.expired_message(client)
                await bot.send_message(LOG_SELLER, msg)
                try:
                    await client.unblock_user(bot.me.username)
                    await bot.send_message(client.me.id, msg)
                except Exception:
                    logger.error(f"Expired error {client.me.id}: {traceback.format_exc()}")
                    await bot.send_message(
                        LOG_SELLER,
                        f"Expired error {client.me.id}: {traceback.format_exc()}",
                    )
                await dB.remove_ubot(client.me.id)
                await dB.rem_expired_date(client.me.id)
                await tokenref.delete_user_data(client.me.id)
                alice._get_my_id.remove(client.me.id)
                alice._ubot.remove(client)
                await client.log_out()
            except Exception:
                logger.error(f"Expired error {client.me.id}: {traceback.format_exc()}")
                await bot.send_message(
                    LOG_SELLER,
                    f"Expired error {client.me.id}: {traceback.format_exc()}",
                )
        await asyncio.sleep(EXPIRED_CHECK_EVERY)


async def CleanAcces():
    while True:
        for org in AKSES_DEPLOY:
            try:
                seles = await dB.get_list_from_var(BOT_ID, "SELLER")
                if org not in seles:
                    AKSES_DEPLOY.remove(org)
            except Exception as e:
                await bot.send_message(LOG_SELLER, f"Clean_Accses error: {str(e)}")
        await asyncio.sleep(3600)


async def stoped_ubot(userid):
    for client in alice._ubot:
        if client.me.id == userid:
            await dB.remove_ubot(client.me.id)
            await dB.rem_expired_date(client.me.id)
            alice._get_my_id.remove(client.me.id)
            alice._ubot.remove(client)
            await client.stop()
            await client.log_out()
            break


async def CheckSellerCount():
    while True:
        try:
            now = datetime.now(ZoneInfo("Asia/Jakarta"))
            last_check_str = await dB.get_var(BOT_ID, "last_check_seller")
            if last_check_str:
                last_check = datetime.fromisoformat(last_check_str).astimezone(
                    ZoneInfo("Asia/Jakarta")
                )
            else:
                last_check = now - timedelta(days=31)
            if (now - last_check).days >= 30:
                reseller_list = await dB.get_list_from_var(BOT_ID, "SELLER") or []
                for sellerid in reseller_list:

                    penjualan = int(await dB.get_var(sellerid, "penjualan") or 0)
                    if penjualan < 5:
                        logger.info(f"Hapus akses seller {sellerid}")
                        await dB.remove_from_var(BOT_ID, "SELLER", sellerid)
                    else:
                        logger.info(f"Reset data seller {sellerid}")
                        await dB.set_var(sellerid, "penjualan", 0)
                await dB.set_var(BOT_ID, "last_check_seller", now.isoformat())
            await asyncio.sleep(86400)
        except Exception as e:
            logger.error(f"[CheckSellerCount] Error: {e}")
            await asyncio.sleep(60)
