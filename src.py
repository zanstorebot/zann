import asyncio
import asyncio.events as _events

import logging
import os
import random
import re
import socket
import traceback
from datetime import datetime
from threading import Thread

import croniter
import psutil
import uvicorn
import uvloop
from aiorun import run
from fastapi import FastAPI
from pyrogram.errors import (AuthKeyDuplicated, AuthKeyUnregistered,
                             SessionRevoked, UserAlreadyParticipant,
                             UserDeactivated, UserDeactivatedBan)
from pytz import timezone

from clients import UserBot, bot, alice
from config import BOT_ID, LOG_SELLER, OWNER_ID, WAJIB_JOIN
from database import dB
from helpers import (AutoBC, AutoFW, CheckUsers, CleanAcces, ExpiredUser,
                     ReadUser, Tools, installPeer)
from logs import logger

# Policy tanpa child watcher (mis. uvloop) membuat asyncio.create_subprocess_exec
# gagal dengan NotImplementedError (dipakai pytgcalls untuk ffmpeg).
_CHILD_WATCHER = asyncio.ThreadedChildWatcher()
_events.AbstractEventLoopPolicy.get_child_watcher = lambda self: _CHILD_WATCHER

asyncio.set_event_loop_policy(asyncio.DefaultEventLoopPolicy())
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


# ---------------------------------------------------------------------------
# WARNA LOG: prefix "AliceCore[INFO]:" jadi biru
# ---------------------------------------------------------------------------
LOG_BLUE = "\033[94m"      # nama "AliceCore". Biru lebih gelap: "\033[34m"
LOG_RED = "\033[91m"       # tulisan "[INFO]". Merah lebih gelap: "\033[31m"
LOG_RESET = "\033[0m"
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_PREFIX_RE = re.compile(r"^AliceCore(\[INFO\]):")


class BlueInfoFormatter(logging.Formatter):
    """Membungkus formatter lama. Hanya log INFO dari logger 'AliceCore' yang
    diubah: warna lama dibuang, 'AliceCore' jadi biru dan '[INFO]' jadi merah."""

    def __init__(self, base):
        super().__init__()
        self.base = base

    def format(self, record):
        msg = self.base.format(record)
        if record.name == "AliceCore" and record.levelno == logging.INFO:
            clean = _ANSI_RE.sub("", msg)
            m = _PREFIX_RE.match(clean)
            if m:
                return (
                    f"{LOG_BLUE}AliceCore{LOG_RESET}"
                    f"{LOG_RED}{m.group(1)}{LOG_RESET}"
                    f":{clean[m.end():]}"
                )
        return msg


def apply_blue_logs():
    """Pasang formatter biru ke handler console. Aman dipanggil berulang."""
    seen = set()
    candidates = [logging.getLogger(), logging.getLogger("AliceCore")]
    for lg in candidates:
        for h in lg.handlers:
            if id(h) in seen:
                continue
            seen.add(id(h))
            # hanya console, file log tidak diberi kode warna
            if isinstance(h, logging.FileHandler):
                continue
            if not isinstance(h, logging.StreamHandler):
                continue
            if isinstance(h.formatter, BlueInfoFormatter):
                continue
            h.setFormatter(BlueInfoFormatter(h.formatter or logging.Formatter()))


apply_blue_logs()


app = FastAPI()


@app.get("/")
async def root():
    return {"message": "Userbot API running"}


def find_free_port(start=7860, end=8000):
    ports = list(range(start, end))
    random.shuffle(ports)
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("localhost", port)) != 0:
                return port
    return None


def kill_process_on_port(port):
    for proc in psutil.process_iter(["pid", "name", "connections"]):
        try:
            for conn in proc.info["connections"]:
                if conn.status == psutil.CONN_LISTEN and conn.laddr.port == port:
                    logger.info(f"⚠️ Killing process {proc.info['pid']} on port {port}")
                    proc.kill()
                    return True
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return False


def start_api():
    port_env_var = f"API_PORT_{BOT_ID}"
    port = os.environ.get(port_env_var)

    if port:
        port = int(port)
    else:
        port = find_free_port()
        os.environ[port_env_var] = str(port)
    try:
        logger.info(f"🚀 Starting API for bot {BOT_ID} on port {port}")
        uvicorn.run("src:app", host="0.0.0.0", port=port, log_level="info")
    except OSError as e:
        if e.errno == 98:
            logger.info(f"❗ Port {port} is in use. Attempting to kill...")
            if kill_process_on_port(port):
                logger.info(f"✅ Port {port} is now free. Restarting API...")
                uvicorn.run("src:app", host="0.0.0.0", port=port, log_level="info")
            else:
                logger.info(f"❌ Gagal membebaskan port {port}. Gagal start API.")
        else:
            raise


list_error = []


async def cleanup_total(ubot_id):
    """Clean up database records for a specific userbot."""
    try:
        await dB.remove_ubot(ubot_id)
        logger.info(f"Deleted user {ubot_id}")
    except Exception as e:
        logger.error(f"Failed to cleanup userbot {ubot_id}: {e}")


async def auto_restart():
    tz = timezone("Asia/Jakarta")
    cron = croniter.croniter("45 01 * * *", datetime.now(tz))
    while True:
        now = datetime.now(tz)
        next_run = cron.get_next(datetime)

        wait_time = (next_run - now).total_seconds()
        await asyncio.sleep(wait_time)
        try:
            await bot.send_message(
                OWNER_ID,
                "<blockquote><b>Restart Daily..\n\nTunggu beberapa menit bot sedang di Restart!!</b></blockquote>",
            )

            await stop_main()
            os.execl("/bin/bash", "bash", "start.sh")
        except Exception as e:
            logger.error(f"Error during restart: {e}")


async def handle_start_error():
    if list_error:
        for data in list_error:
            ubot = data["user"]
            reason = data["error_msg"]
            await bot.send_message(
                LOG_SELLER,
                f"<b>Userbot {ubot} failed to start due to {reason}, deleted user on database</b>",
            )
            try:
                await bot.send_message(
                    int(ubot), f"<b>Userbot anda telah dihapus karna {reason}.</b>"
                )
            except Exception:
                pass
            await cleanup_total(ubot)


async def start_ubot(ubot):
    """Start a userbot instance and handle setup."""
    from command import register_antiucast  # import di dalam fungsi, hindari circular import

    userbot = UserBot(**ubot)
    try:
        await userbot.start()
        try:
            register_antiucast(userbot)
        except Exception:
            logger.error(f"Antiucast gagal didaftarkan: {traceback.format_exc()}")
        for chat in WAJIB_JOIN:
            try:
                await userbot.join_chat(chat)
            except UserAlreadyParticipant:
                pass
            except Exception:
                continue
    except (AuthKeyUnregistered, AuthKeyDuplicated, SessionRevoked):
        reason = "Session Ended"
        data = {"user": int(ubot["name"]), "error_msg": reason}
        list_error.append(data)
    except (UserDeactivated, UserDeactivatedBan):
        reason = "Account Banned by Telegram"
        data = {"user": int(ubot["name"]), "error_msg": reason}
        list_error.append(data)


async def start_main_bot():
    """Start the main bot after userbots."""
    logger.info("🤖 Starting main bot...")
    await bot.start()
    await bot.add_reseller()
    logger.info("✅ Main bot started successfully.")
    total_bots = len(alice._ubot)
    message = "🔥**Bot berhasil diaktifkan**🔥\n" f"✅ **Total User: {total_bots}**"
    await dB.set_var(bot.id, "total_users", total_bots)
    try:
        await bot.send_message(OWNER_ID, f"<blockquote>{message}</blockquote>")
    except Exception:
        pass


async def start_userbots():
    logger.info("🔄 Starting userbots...")
    userbots = await dB.get_userbots()
    tasks = [asyncio.create_task(start_ubot(ubot)) for ubot in userbots]
    await asyncio.gather(*tasks, return_exceptions=False)
    logger.info("✅ All userbots started successfully.")


async def task_2():
    background_tasks = [
        ExpiredUser(),
        installPeer(),
        CheckUsers(),
        CleanAcces(),
        auto_restart(),
    ]
    for task in background_tasks:
        asyncio.create_task(task)
    logger.info(f"Started {len(background_tasks)} background tasks 2")


async def task_1():
    await AutoBC()
    await ReadUser()
    await AutoFW()
    logger.info(f"Started background tasks 1")


async def stop_main():
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    logger.info(f"📌 Total task yang akan dihentikan: {len(tasks)}")

    if not tasks:
        logger.info("✅ Tidak ada task yang berjalan.")
        return

    for task in tasks:
        if not task.done():
            task.cancel()

    await asyncio.sleep(1)

    results = []
    for task in tasks:
        try:
            result = await asyncio.wait_for(asyncio.shield(task), timeout=5)
            results.append(result)
        except asyncio.TimeoutError:
            logger.error(
                f"⏳ Timeout saat menghentikan task: {task.get_name() or task}"
            )
            results.append(None)
        except asyncio.CancelledError:
            continue
        except Exception as e:
            logger.error(f"⚠️ Task {task.get_name() or task} mengalami error: {e}")

    logger.info("⚠️ Menutup database...")
    await Tools.close_fetch()
    await dB.close()
    logger.info("✅ Semua task dihentikan dan database telah ditutup.")


async def main():
    try:
        apply_blue_logs()   # jaga-jaga kalau handler log baru dibuat setelah import
        await dB.initialize()
        api_thread = Thread(target=start_api, daemon=True)
        api_thread.start()
        await start_userbots()
        await start_main_bot()
        await task_1()
        await task_2()
        await handle_start_error()

    except asyncio.CancelledError:
        logger.warning("Stopped All.")
    except Exception:
        logger.error(f"{traceback.format_exc()}")


if __name__ == "__main__":

    run(
        main(),
        loop=bot.loop,
        shutdown_callback=stop_main(),
    )
