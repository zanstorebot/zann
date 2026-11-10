import asyncio
import logging
import os
import re
import traceback
from datetime import datetime
from threading import Thread

import croniter
import uvicorn
from aiorun import run
from fastapi import FastAPI
from pyrogram.errors import (
    AuthKeyDuplicated, AuthKeyUnregistered, SessionRevoked,
    UserAlreadyParticipant, UserDeactivated, UserDeactivatedBan,
)
from pytz import timezone

from clients import UserBot, alice, bot
from config import BOT_ID, LOG_SELLER, OWNER_ID, WAJIB_JOIN
from database import dB
from helpers import CheckUsers, CleanAcces, ExpiredUser, Tools
from logs import logger

LOG_BLUE = "\033[94m"
LOG_RED = "\033[91m"
LOG_RESET = "\033[0m"
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")
_PREFIX_RE = re.compile(r"^AliceCore(\[INFO\]):")

STARTUP_CONCURRENCY = 3
BACKGROUND_TASKS = set()
list_error = []
_shutdown_started = False
app = FastAPI()


class BlueInfoFormatter(logging.Formatter):
    def __init__(self, base):
        super().__init__()
        self.base = base

    def format(self, record):
        message = self.base.format(record)
        if record.name == "AliceCore" and record.levelno == logging.INFO:
            clean = _ANSI_RE.sub("", message)
            match = _PREFIX_RE.match(clean)
            if match:
                return (
                    f"{LOG_BLUE}AliceCore{LOG_RESET}"
                    f"{LOG_RED}{match.group(1)}{LOG_RESET}:{clean[match.end():]}"
                )
        return message


def apply_blue_logs():
    seen = set()
    for log in (logging.getLogger(), logging.getLogger("AliceCore")):
        for handler in log.handlers:
            if id(handler) in seen:
                continue
            seen.add(id(handler))
            if isinstance(handler, logging.FileHandler):
                continue
            if not isinstance(handler, logging.StreamHandler):
                continue
            if not isinstance(handler.formatter, BlueInfoFormatter):
                handler.setFormatter(
                    BlueInfoFormatter(handler.formatter or logging.Formatter())
                )


@app.get("/")
async def root():
    return {"message": "Userbot API running"}


def start_api():
    key = f"API_PORT_{BOT_ID}"
    try:
        port = int(os.environ.get(key, "7860"))
        if not 1 <= port <= 65535:
            raise ValueError("Port harus berada di antara 1 dan 65535")
        logger.info(f"Starting API for bot {BOT_ID} on port {port}")
        uvicorn.run(
            app, host="0.0.0.0", port=port, loop="asyncio",
            log_level="warning", access_log=False,
        )
    except (Exception, SystemExit) as exc:
        logger.error(f"API gagal berjalan: {exc}")


async def notify(chat_id, text):
    try:
        await bot.send_message(chat_id, text)
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        logger.warning(f"Gagal mengirim notifikasi ke {chat_id}: {exc}")


def background_done(task):
    BACKGROUND_TASKS.discard(task)
    if task.cancelled():
        return
    error = task.exception()
    if error:
        logger.error(
            f"Background task {task.get_name()} berhenti: {error}",
            exc_info=(type(error), error, error.__traceback__),
        )


def start_background(coroutine, name):
    task = asyncio.create_task(coroutine, name=name)
    BACKGROUND_TASKS.add(task)
    task.add_done_callback(background_done)
    return task


async def cleanup_total(ubot_id):
    try:
        await dB.remove_ubot(ubot_id)
        logger.info(f"Deleted user {ubot_id}")
    except Exception as exc:
        logger.error(f"Failed to cleanup userbot {ubot_id}: {exc}")


async def auto_restart():
    tz = timezone("Asia/Jakarta")
    cron = croniter.croniter("45 01 * * *", datetime.now(tz))
    while True:
        next_run = cron.get_next(datetime)
        await asyncio.sleep(max(0, (next_run - datetime.now(tz)).total_seconds()))
        await notify(
            OWNER_ID,
            "<blockquote><b>Restart Daily..\n\n"
            "Tunggu beberapa menit bot sedang di Restart!!</b></blockquote>",
        )
        await stop_main()
        os.execl("/bin/bash", "bash", "start.sh")


async def handle_start_error():
    for data in list_error:
        user_id = data["user"]
        reason = data["error_msg"]
        await notify(
            LOG_SELLER,
            f"<b>Userbot {user_id} failed to start due to {reason}, "
            "deleted user on database</b>",
        )
        await notify(
            user_id, f"<b>Userbot anda telah dihapus karna {reason}.</b>"
        )
        await cleanup_total(user_id)
    list_error.clear()


async def discard_failed_client(client):
    if getattr(client, "is_initialized", False):
        try:
            await client.stop()
        except Exception:
            logger.warning("Gagal menutup client setelah startup gagal")

    group_call = getattr(client, "group_call", None)
    if group_call is not None:
        try:
            await group_call.stop()
        except Exception:
            pass

    if client in alice._ubot:
        alice._ubot.remove(client)
        user_id = getattr(getattr(client, "me", None), "id", None)
        if user_id in alice._get_my_id:
            alice._get_my_id.remove(user_id)


async def start_ubot(ubot):
    from command import register_antiucast

    userbot = UserBot(**ubot)
    try:
        await userbot.start()
    except (AuthKeyUnregistered, AuthKeyDuplicated, SessionRevoked):
        list_error.append({
            "user": int(ubot["name"]), "error_msg": "Session Ended",
        })
        await discard_failed_client(userbot)
        return False
    except (UserDeactivated, UserDeactivatedBan):
        list_error.append({
            "user": int(ubot["name"]),
            "error_msg": "Account Banned by Telegram",
        })
        await discard_failed_client(userbot)
        return False
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.error(
            f"Startup userbot {ubot.get('name')} gagal; data tidak dihapus:\n"
            f"{traceback.format_exc()}"
        )
        await discard_failed_client(userbot)
        return False

    try:
        register_antiucast(userbot)
    except Exception:
        logger.error(f"Antiucast gagal didaftarkan:\n{traceback.format_exc()}")

    for chat in WAJIB_JOIN:
        try:
            await userbot.join_chat(chat)
        except UserAlreadyParticipant:
            pass
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning(f"Wajib join {userbot.me.id} ke {chat} gagal: {exc}")
        await asyncio.sleep(0.5)
    return True


async def start_userbots():
    logger.info("Starting userbots with limited concurrency...")
    userbots = await dB.get_userbots()
    semaphore = asyncio.Semaphore(STARTUP_CONCURRENCY)

    async def limited_start(data):
        async with semaphore:
            result = await start_ubot(data)
            await asyncio.sleep(0.5)
            return result

    results = await asyncio.gather(*(limited_start(data) for data in userbots))
    successful = sum(results)
    logger.info(
        f"Startup selesai: {successful}/{len(results)} userbot berhasil, "
        f"{len(results) - successful} gagal."
    )


async def start_main_bot():
    logger.info("Starting main bot...")
    await bot.start()
    await bot.add_reseller()
    total = len(alice._ubot)
    await dB.set_var(bot.id, "total_users", total)
    await notify(
        OWNER_ID,
        "<blockquote><b>Bot berhasil diaktifkan\n"
        f"Total User: {total}</b></blockquote>",
    )
    logger.info("Main bot started successfully.")


async def task_2():
    for name, coroutine in (
        ("expired-users", ExpiredUser()),
        ("check-users", CheckUsers()),
        ("clean-access", CleanAcces()),
        ("daily-restart", auto_restart()),
    ):
        start_background(coroutine, name)
    logger.info("Started 4 maintenance tasks; startup dialog scan disabled.")


async def stop_main():
    global _shutdown_started
    if _shutdown_started:
        return
    _shutdown_started = True
    current = asyncio.current_task()

    try:
        tasks = [
            task for task in tuple(BACKGROUND_TASKS)
            if task is not current and not task.done()
        ]
        for task in tasks:
            task.cancel()
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        async def stop_client(client):
            group_call = getattr(client, "group_call", None)
            if group_call is not None:
                try:
                    await asyncio.wait_for(group_call.stop(), timeout=10)
                except Exception as exc:
                    logger.warning(f"Gagal menutup group call: {exc}")
            if getattr(client, "is_initialized", False):
                try:
                    await asyncio.wait_for(client.stop(), timeout=15)
                except Exception as exc:
                    logger.warning(f"Gagal menutup client {client.name}: {exc}")

        for client in tuple(alice._ubot):
            await stop_client(client)
        await stop_client(bot)
    finally:
        try:
            await Tools.close_fetch()
        except Exception as exc:
            logger.warning(f"Gagal menutup HTTP client: {exc}")
        try:
            await dB.close()
        except Exception as exc:
            logger.warning(f"Gagal menutup database: {exc}")
        logger.info("Shutdown selesai.")


async def main():
    apply_blue_logs()
    try:
        await dB.initialize()
        Thread(target=start_api, name="userbot-api", daemon=True).start()
        await start_userbots()
        await start_main_bot()
        await task_2()
        await handle_start_error()
    except asyncio.CancelledError:
        raise
    except Exception:
        logger.error(f"Startup gagal:\n{traceback.format_exc()}")
        await stop_main()
        raise


if __name__ == "__main__":
    run(main(), loop=bot.loop, shutdown_callback=stop_main())