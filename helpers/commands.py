import asyncio
import sys
import traceback
from functools import wraps

from pyrogram import enums, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InlineQueryResultArticle, InputTextMessageContent

from clients import bot, alice
from config import (BOT_ID, FAKE_DEVS, DEVA, LOG_BACKUP, LOG_SELLER, OWNER_ID,
                    SUDO_OWNERS)
from database import dB

from .emoji_logs import Emoji

trigger = r"^(💬 Jawab Pesan|👤 Akun|❌ Batalkan|Mulai Buat Userbot|Trial Userbot|Status Akun|Reset Emoji|Reset Prefix|Restart Userbot|Reset Text|Updates|👥 Cek User|Cek Fitur|🤔 Pertanyaan|↩️ Beranda|✨ Pembuatan Ulang Userbot|Hubungi Admins|/copy|/close|/get|/restart|/id|/button|✅ Lanjutkan Buat Userbot|start|restart|/start|ask|/ask|Referral|Token|Plan Basic|Cek Fitur)"
words = trigger.replace("^(", "").replace(")", "").split("|")
wrapped_words = [f'"{word}"' for word in words]
no_trigger = "[" + ", ".join(wrapped_words) + "]"
no_commands = [
    "💬 Jawab Pesan",
    "Plan Basic",
    "Plan Pro",
    "Token",
    "👤 Akun",
    " Referral",
    "❌ Batalkan",
    "Mulai Buat Userbot",
    "Trial Userbot",
    "Status Akun",
    "Reset Emoji",
    "Reset Prefix",
    "Restart Userbot",
    "Reset Text",
    "✅ Lanjutkan Buat Userbot",
    "Updates",
    "Cek User",
    "Cek Fitur",
    "🤔 Pertanyaan",
    "↩️ Beranda",
    "✨ Pembuatan Ulang Userbot",
    "Hubungi Admins",
    "📃 Saya Setuju",
    "ask",
    "tanya",
    "kontol",
    "close",
    "restart",
    "id",
    "button",
    "token",
    "referral",
    "sh",
    "eval",
    "update",
    "restore",
    "backup",
    "reboot",
    "setimg",
    "setads",
    "cancel",
]


async def verified_sudo(_, client, message):
    sudo_users = await dB.get_list_from_var(client.me.id, "SUDOERS")
    is_user = message.from_user if message.from_user else message.sender_chat
    is_self = bool(
        message.from_user
        and message.from_user.is_self
        or getattr(message, "outgoing", False)
    )
    return is_user.id in sudo_users or is_self


async def is_blocked(_, __, message):
    if message.sender_chat:
        return
    return bool(
        message.from_user and message.from_user.status == enums.UserStatus.LONG_AGO
    )


class FILTERS:
    PRIVATE = filters.private
    OWNER = filters.user(OWNER_ID)
    FAKE_DEV2 = filters.user(OWNER_ID)
    DEVELOPER = filters.user(DEVA) & ~filters.me
    FAKE_DEV = filters.user(FAKE_DEVS) & ~filters.me


class CMD:
    @staticmethod
    def split_limits(text):
        if len(text) < 2048:
            return [text]

        lines = text.splitlines(True)
        small_msg = ""
        result = []
        for line in lines:
            if len(small_msg) + len(line) < 2048:
                small_msg += line
            else:
                result.append(small_msg)
                small_msg = line
        else:
            result.append(small_msg)

        return result

    @staticmethod
    def capture_err(func):
        @wraps(func)
        async def capture(client, message):
            try:
                return await func(client, message)
            except Exception as err:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                errors = traceback.format_exception(exc_type, exc_value, exc_traceback)
                msg = message.chat or message.from_user
                error_feedback = CMD.split_limits(
                    "❌**ERROR** | `{}` | `{}`\n\n<pre>{}</pre>\n\n<pre>{}</pre>\n".format(
                        client.me.id,
                        msg.id,
                        message.text or message.caption,
                        "".join(errors),
                    ),
                )
                for x in error_feedback:
                    await bot.send_message(LOG_BACKUP, x)
                raise err

        return capture

    @staticmethod
    def FLOOD_HANDLER(func):
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except FloodWait as e:
                await asyncio.sleep(e.value)
                return await func(*args, **kwargs)

        return wrapper

    @staticmethod
    def BOT(command, filter=None):
        def wrapper(func):
            message_filters = (
                filters.command(command) & filter
                if filter
                else filters.command(command)
            )

            @bot.on_message(message_filters)
            @CMD.FLOOD_HANDLER
            @CMD.capture_err
            async def wrapped_func(client, message):
                user = message.from_user if message.from_user else message.sender_chat
                if user.id in await dB.get_list_from_var(client.me.id, "BANNED_USERS"):
                    return
                return await func(client, message)

            return wrapped_func

        return wrapper

    @staticmethod
    def UBOT(command, sudo=True):
        if sudo:
            filter = filters.create(verified_sudo)
        else:
            filter = filters.me

        def wrapper(func):
            module_tag = func.__globals__.get("__MODULES__", "").lower()
            module_plan = func.__globals__.get("IS_PRO", None)

            @alice.on_message(alice.user_prefix(command) & filter)
            @CMD.FLOOD_HANDLER
            @CMD.capture_err
            async def wrapped_func(client, message):
                IGNORE_MODULES = await dB.get_var(client.me.id, "IGNORE_MODULES") or []
                if module_tag in IGNORE_MODULES:
                    print(f"[SKIPPED] {client.me.id} ignore: {module_tag}")
                    return
                plan = await dB.get_var(client.me.id, "plan")
                is_pro = True if plan == "is_pro" else False
                if module_plan is not None and module_plan != is_pro:
                    return

                return await func(client, message)

            return wrapped_func

        return wrapper

    @staticmethod
    def UBOT_REGEX(command, filter=None):
        if filter is None:
            filter = filters.create(verified_sudo)

        def wrapper(func):
            @alice.on_message(filters.regex(command) & filters.me & filter)
            @CMD.FLOOD_HANDLER
            async def wrapped_func(client, message):

                return await func(client, message)

            return wrapped_func

        return wrapper

    @staticmethod
    def DELETED():
        def wrapper(func):
            @alice.on_deleted_messages(filters.incoming & ~filters.me)
            async def wrapped_func(client, messages):
                return await func(client, messages)

            return wrapped_func

        return wrapper

    @staticmethod
    def EDITED():
        def wrapper(func):
            @alice.on_edited_message(
                (
                    filters.mentioned
                    & filters.incoming
                    & ~filters.bot
                    & ~filters.via_bot
                    & ~filters.me
                )
                | (
                    filters.private
                    & filters.incoming
                    & ~filters.me
                    & ~filters.bot
                    & ~filters.service
                )
            )
            @CMD.capture_err
            async def wrapped_func(client, message):

                return await func(client, message)

            return wrapped_func

        return wrapper

    @staticmethod
    def OWNER(func):
        async def function(client, message):
            user = message.from_user if message.from_user else message.sender_chat
            if user.id != OWNER_ID:
                return
            return await func(client, message)

        return function

    @staticmethod
    def NLX(func):
        async def function(client, message):
            user = message.from_user if message.from_user else message.sender_chat
            if user.id not in DEVA:
                return
            return await func(client, message)

        return function

    @staticmethod
    def FAKE_NLX(func):
        async def function(client, message):
            user = message.from_user if message.from_user else message.sender_chat
            if user.id not in SUDO_OWNERS:
                return
            return await func(client, message)

        return function

    @staticmethod
    def DEV_CMD(command, filter=FILTERS.DEVELOPER):
        def wrapper(func):
            @alice.on_message(filters.command(command, "") & filter)
            @CMD.FLOOD_HANDLER
            async def wrapped_func(client, message):
                await func(client, message)

            return wrapped_func

        return wrapper

    @staticmethod
    def FAKEDEV(command, filter=FILTERS.FAKE_DEV):
        def wrapper(func):
            @alice.on_message(filters.command(command, "c") & filter)
            @CMD.FLOOD_HANDLER
            async def wrapped_func(client, message):
                await func(client, message)

            return wrapped_func

        return wrapper

    @staticmethod
    def INLINE():
        def wrapper(func):
            @bot.on_inline_query()
            @CMD.FLOOD_HANDLER
            async def wrapped_func(client, inline_query):
                return await func(client, inline_query)

            return wrapped_func

        return wrapper

    @staticmethod
    def CALLBACK():
        def wrapper(func):
            @bot.on_callback_query()
            async def wrapped_func(client, callback_query):
                return await func(client, callback_query)

            return wrapped_func

        return wrapper

    @staticmethod
    def REGEX(command):
        def wrapper(func):
            @bot.on_message(filters.regex(command))
            @CMD.FLOOD_HANDLER
            async def wrapped_func(client, message):
                return await func(client, message)

            return wrapped_func

        return wrapper

    @staticmethod
    def CHAT_FORWARD(result, bot):
        query_mapping = {
            "OUTGOING": {
                "query": (
                    filters.reply
                    & filters.chat(LOG_SELLER)
                    & ~filters.command(no_commands)
                ),
                "group": 20,
            },
        }
        result_query = query_mapping.get(result)

        def wrapper(func):
            if result_query:

                async def wrapped_func(client, message):
                    return await func(client, message)

                bot.on_message(result_query["query"], group=int(result_query["group"]))(
                    wrapped_func
                )

                return wrapped_func
            else:
                return func

        return wrapper

    @staticmethod
    def NO_CMD(result, client):
        query_mapping = {
            "PMPERMIT": {
                "query": (
                    filters.private
                    & filters.incoming
                    & ~filters.me
                    & ~filters.contact
                    & ~filters.bot
                    & ~filters.via_bot
                    & ~filters.service
                ),
                "group": 1,
            },
            "FILTERS": {
                "query": ~filters.service
                & ~filters.bot
                & ~filters.me
                & filters.incoming,
                "group": 2,
            },
            "LOGS_GROUP": {
                "query": (
                    filters.mentioned
                    & filters.incoming
                    & ~filters.bot
                    & ~filters.via_bot
                    & ~filters.me
                )
                | (
                    filters.private
                    & filters.incoming
                    & ~filters.me
                    & ~filters.bot
                    & ~filters.service
                ),
                "group": 3,
            },
            "AFK": {
                "query": (
                    (filters.mentioned | filters.private)
                    & ~filters.bot
                    & ~filters.me
                    & filters.incoming
                ),
                "group": 4,
            },
            "REP_BLOCK": {
                "query": (
                    filters.mentioned
                    & ~filters.bot
                    & ~filters.me
                    & filters.incoming
                    & filters.create(is_blocked)
                ),
                "group": 5,
            },
            "REPLY": {
                "query": (filters.reply & filters.me),
                "group": 6,
            },
            "ADD_ME": {
                "query": (filters.new_chat_members),
                "group": 7,
            },
            "KICK_ME": {
                "query": (filters.left_chat_member),
                "group": 8,
            },
            "MENTIONED": {
                "query": (
                    filters.mentioned & ~filters.bot & ~filters.me & filters.incoming
                ),
                "group": 9,
            },
            "CHATBOT": {
                "query": (~filters.bot & filters.incoming),
                "group": 10,
            },
            "AUTO_APPROVE": {
                "query": (
                    filters.private
                    & filters.outgoing
                    & filters.me
                    & ~filters.bot
                    & ~filters.via_bot
                    & ~filters.service
                ),
                "group": 11,
            },
            "FORCE_DEL": {
                "query": ((filters.incoming | filters.group) & ~filters.me),
                "group": 14,
            },
        }
        result_query = query_mapping.get(result)

        def decorator(func):
            if result_query:

                async def wrapped_func(client, message):
                    await func(client, message)

                client.on_message(
                    result_query["query"], group=int(result_query["group"])
                )(wrapped_func)
                return wrapped_func
            else:
                return func

        return decorator

    @staticmethod
    def IS_LOG(func):
        async def function(client, message):
            logs = await dB.get_var(client.me.id, "GRUPLOG")
            if logs:
                if message.chat.id != int(logs):
                    return
            else:
                pass
            return await func(client, message)

        return function

    @staticmethod
    def SELLER_AND_GC(func):
        async def function(client, message):
            user = message.from_user
            reseller = await dB.get_list_from_var(BOT_ID, "SELLER")
            if user.id not in reseller:
                return await message.reply("<b>Kamu bukan reseller!!</b>")

            return await func(client, message)

        return function

    @staticmethod
    def DB_BROADCAST(func):
        async def function(client, message):
            broadcast = await dB.get_list_from_var(client.me.id, "BROADCAST")
            user = message.from_user
            if user.id not in broadcast:
                await dB.add_to_var(client.me.id, "BROADCAST", user.id)
            return await func(client, message)

        return function

    @staticmethod
    def ADMIN(func):
        async def function(client, message):
            emo = Emoji(client)
            await emo.get()
            user = message.from_user if message.from_user else message.sender_chat
            if user.id not in await client.admin_list(message):
                return await message.reply(
                    f"<blockquote>{emo.gagal}<b>Anda bukan admin di grup ini.</b>blockquote>"
                )
            return await func(client, message)

        return function

    @staticmethod
    def ONLY_GROUP(func):
        async def function(client, message):
            if message.chat.type not in [
                enums.ChatType.GROUP,
                enums.ChatType.SUPERGROUP,
            ]:
                emo = Emoji(client)
                await emo.get()
                return await message.reply(
                    f"{emo.gagal}<b>This command only for group.</b>"
                )
            return await func(client, message)

        return function

    @staticmethod
    def ONLY_PRIVATE(func):
        async def function(client, message):
            if message.chat.type != enums.ChatType.PRIVATE:
                emo = Emoji(client)
                await emo.get()
                return await message.reply(
                    f"{emo.gagal}<b>This command only for private.</b>"
                )
            return await func(client, message)

        return function

    @staticmethod
    def INLINE_QUERY(func):
        async def wrapper(client, iq):
            users = alice._get_my_id
            if iq.from_user.id not in users:
                return await client.answer_inline_query(
                    iq.id,
                    cache_time=0,
                    results=[
                        InlineQueryResultArticle(
                            title=f"Anda Belum Melakukan Pembelian @{client.me.username}",
                            input_message_content=InputTextMessageContent(
                                f"Kamu Bisa Melakukan Pembelian @{client.me.username} Agar Bisa Menggunakan"
                            ),
                        )
                    ],
                )
            else:

                return await func(client, iq)

        return wrapper

    @staticmethod
    def CALLBACK_DATA(func):
        async def wrapper(client, cq):
            users = alice._get_my_id
            if cq.from_user.id not in users:
                return await cq.answer(
                    f"Silakan Order Bot @{client.me.username} Agar Bisa Menggunakan Bot Ini",
                    True,
                )
            else:

                return await func(client, cq)

        return wrapper
