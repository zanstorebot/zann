import asyncio
import importlib
import os
import re
import shlex
import subprocess
from typing import Optional

from pyrogram import Client, enums, filters, raw, types
from pyrogram.enums import ChatType
from pyrogram.errors import (ChannelInvalid, PeerIdInvalid, UsernameInvalid,
                             UsernameNotOccupied)
from pyrogram.handlers import (CallbackQueryHandler, DeletedMessagesHandler,
                               DisconnectHandler, EditedMessageHandler,
                               MessageHandler)
from pyromod import listen  # ignore
from pytgcalls import PyTgCalls
from pytgcalls import filters as fl

from config import (AKSES_DEPLOY, API_HASH, API_ID, BOT_ID, BOT_NAME,
                    BOT_TOKEN, HELPABLE, OWNER_ID, SUDO_OWNERS)
from database import dB
from logs import logger
from plugins import PLUGINS

if not os.path.exists("downloads"):
    os.makedirs("downloads")


list_error = []


class BaseClient(Client):
    _ubot = []
    _prefix = {}
    _get_my_id = []
    _translate = {}
    _get_my_peer = {}
    _sudoers = {}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def get_call(
        self, client, chat_id: int
    ) -> Optional[raw.types.InputGroupCall]:
        try:
            chat = await client.resolve_peer(chat_id)
        except (PeerIdInvalid, ChannelInvalid):
            return None

        if isinstance(chat, raw.types.InputPeerChannel):
            full_chat = await client.invoke(
                raw.functions.channels.GetFullChannel(
                    channel=raw.types.InputChannel(
                        channel_id=chat.channel_id, access_hash=chat.access_hash
                    )
                )
            )
        else:
            full_chat = await client.send(
                raw.functions.messages.GetFullChat(chat_id=chat_id)
            )

        input_call = full_chat.full_chat.call

        if input_call is not None:
            call_details = await client.invoke(
                raw.functions.phone.GetGroupCall(call=input_call, limit=-1)
            )
            call = call_details.call

            if call is not None and call.schedule_date is not None:
                return None

            return call

        return None

    async def admin_list(self, message):
        return [
            member.user.id
            async for member in message._client.get_chat_members(
                message.chat.id, filter=enums.ChatMembersFilter.ADMINISTRATORS
            )
        ]

    async def get_chat_id(self, query):
        chat_types = {
            "global": [ChatType.CHANNEL, ChatType.GROUP, ChatType.SUPERGROUP],
            "all": [ChatType.GROUP, ChatType.SUPERGROUP, ChatType.PRIVATE],
            "group": [ChatType.GROUP, ChatType.SUPERGROUP],
            "bot": [ChatType.BOT],
            "usbot": [ChatType.PRIVATE, ChatType.BOT],
            "private": [ChatType.PRIVATE],
            "channel": [ChatType.CHANNEL],
        }

        if query not in chat_types:
            return []

        valid_chat_types = chat_types[query]
        chat_ids = []

        try:
            async for dialog in self.get_dialogs():
                try:
                    chat = dialog.chat
                    if chat and chat.type in valid_chat_types:
                        chat_ids.append(chat.id)
                except Exception:
                    continue
        except Exception:
            pass

        return chat_ids

    def extract_type_and_text(self, message):
        args = message.text.split(None, 2)
        if len(args) < 2:
            return None, None

        type = args[1]
        msg = (
            message.reply_to_message.text
            if message.reply_to_message
            else args[2] if len(args) > 2 else None
        )
        return type, msg

    def new_arg(self, message):
        if message.reply_to_message and len(message.command) < 3:
            msg = message.reply_to_message.text or message.reply_to_message.caption
            if not msg:
                return ""
            msg = msg.encode().decode("UTF-8")
            msg = msg.replace(" ", "", 2) if msg[2] == " " else msg
            return msg
        elif len(message.command) > 2:
            return " ".join(message.command[2:])
        else:
            return ""

    def extract_type_and_msg(self, message, is_reply_text=False):
        args = message.text.split(None, 2)

        if len(args) < 2:
            return None, None

        type = args[1]

        if is_reply_text:
            msg = (
                message.reply_to_message.text
                if message.reply_to_message
                else args[2] if len(args) > 2 else None
            )
        else:
            msg = (
                message.reply_to_message
                if message.reply_to_message
                else args[2] if len(args) > 2 else None
            )

        return type, msg

    async def get_translate(self):
        data = await dB.get_var(self.me.id, "_translate")
        if data:
            return data
        return "id"

    def get_message(self, message):
        if message.reply_to_message:
            return message.reply_to_message
        elif len(message.command) > 1:
            return " ".join(message.command[1:])
        return ""

    def get_name(self, message):
        if message.reply_to_message:
            if message.reply_to_message.sender_chat:
                return None
            first_name = message.reply_to_message.from_user.first_name or ""
            last_name = message.reply_to_message.from_user.last_name or ""
            full_name = f"{first_name} {last_name}".strip()
            return full_name if full_name else None
        else:
            input_text = message.text.split(None, 1)
            if len(input_text) <= 1:
                first_name = message.from_user.first_name or ""
                last_name = message.from_user.last_name or ""
                full_name = f"{first_name} {last_name}".strip()
                return full_name if full_name else None
            return input_text[1].strip()

    async def get_mention(self, client, message):
        if message.reply_to_message:
            if message.reply_to_message.sender_chat:
                return None
            first_name = message.reply_to_message.from_user.first_name or ""
            last_name = message.reply_to_message.from_user.last_name or ""
            full_name = f"{first_name} {last_name}".strip()
            user_id = message.reply_to_message.from_user.id
            mention = f'<a href="tg://user?id={user_id}">{full_name}</a>'
            return mention
        else:
            if message.entities:
                for entity in message.entities:
                    if entity.type in ["mention", "text_mention"]:
                        if entity.type == "mention":
                            mention = message.text[
                                entity.offset : entity.offset + entity.length
                            ]
                            return mention
                        elif entity.type == "text_mention" and entity.user:
                            full_name = f"{entity.user.first_name} {entity.user.last_name or ''}".strip()
                            mention = f'<a href="tg://user?id={entity.user.id}">{full_name}</a>'
                            return mention
        first_name = message.from_user.first_name or ""
        last_name = message.from_user.last_name or ""
        full_name = f"{first_name} {last_name}".strip()
        mention = f'<a href="tg://user?id={message.from_user.id}">{full_name}</a>'
        return mention

    def get_arg(self, message):
        if message.reply_to_message and len(message.command) < 2:
            msg = message.reply_to_message.text or message.reply_to_message.caption
            if not msg:
                return ""
            msg = msg.encode().decode("UTF-8")
            msg = msg.replace(" ", "", 1) if msg[1] == " " else msg
            return msg
        elif len(message.command) > 1:
            return " ".join(message.command[1:])
        else:
            return ""

    def get_text(self, message):
        if message.reply_to_message:
            if len(message.command) < 2:
                text = (
                    message.reply_to_message.text
                    or message.reply_to_message.caption
                    or message.text.split(None, 1)[1]
                )
            else:
                text = (
                    (
                        message.reply_to_message.text
                        or message.reply_to_message.caption
                        or ""
                    )
                    + "\n\n"
                    + message.text.split(None, 1)[1]
                )
        else:
            if len(message.command) < 2:
                text = ""
            else:
                text = message.text.split(None, 1)[1]
        return text

    async def bash(self, cmd):
        try:
            process = await asyncio.create_subprocess_shell(
                cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            err = stderr.decode().strip()
            out = stdout.decode().strip()
            return out, err
        except NotImplementedError:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )
            stdout, stderr = process.communicate()
            err = stderr.decode().strip()
            out = stdout.decode().strip()
            return out, err

    async def run_cmd(self, cmd):
        args = shlex.split(cmd)
        try:
            process = await asyncio.create_subprocess_exec(
                *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            return (
                stdout.decode("utf-8", "replace").strip(),
                stderr.decode("utf-8", "replace").strip(),
                process.returncode,
                process.pid,
            )
        except NotImplementedError:
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )
            stdout, stderr = process.communicate()
            return (
                stdout.decode("utf-8", "replace").strip(),
                stderr.decode("utf-8", "replace").strip(),
                process.returncode,
                process.pid,
            )

    async def shell_exec(self, code, treat=True):
        process = await asyncio.create_subprocess_shell(
            code, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )

        stdout = (await process.communicate())[0]
        if treat:
            stdout = stdout.decode().strip()
        return stdout, process

    async def extract_userid(self, message, text):
        def is_int(text):
            try:
                int(text)
            except ValueError:
                return False
            return True

        text = text.strip()

        if is_int(text):
            return int(text)

        try:
            entities = message.entities
            app = message._client
            entity = entities[1 if message.text.startswith("/") else 0]
            if entity.type == enums.MessageEntityType.MENTION:
                try:
                    return (await app.get_users(text)).id
                except (UsernameNotOccupied, UsernameInvalid):
                    return None
            if entity.type == enums.MessageEntityType.TEXT_MENTION:
                return entity.user.id
        except (AttributeError, IndexError, ValueError):
            return None

    async def extract_user_and_reason(self, message, sender_chat=False):
        args = message.text.strip().split()
        text = message.text
        user = None
        reason = None
        if message.reply_to_message:
            reply = message.reply_to_message
            if not reply.from_user:
                if (
                    reply.sender_chat
                    and reply.sender_chat != message.chat.id
                    and sender_chat
                ):
                    id_ = reply.sender_chat.id
                else:
                    return None, None
            else:
                id_ = reply.from_user.id

            if len(args) < 2:
                reason = None
            else:
                reason = text.split(None, 1)[1]
            return id_, reason

        if len(args) == 2:
            user = text.split(None, 1)[1]
            return await self.extract_userid(message, user), None

        if len(args) > 2:
            user, reason = text.split(None, 2)[1:]
            return await self.extract_userid(message, user), reason

        return user, reason

    async def extract_user(self, message):
        return (await self.extract_user_and_reason(message))[0]

    async def extract_chat_and_reason(self, client, message):
        args = message.text.strip().split()
        chat_id = None
        reason = None

        if message.reply_to_message:
            chat_id = await self.extract_chat_from_reply(message.reply_to_message)
            if message.reply_to_message.caption:
                reason = message.reply_to_message.caption
            elif message.reply_to_message.text:
                reason = message.reply_to_message.text
            else:
                reason = " ".join(args[1:]) if len(args) > 1 else None
            return chat_id, reason

        if len(args) >= 2:
            chat = args[1]
            if chat.startswith("@"):
                try:
                    chats = await client.get_chat(chat)
                    chat_id = chats.id
                except Exception:
                    chat_id = None
            elif chat.startswith("-100"):
                chat_id = int(chat)
            else:
                chat_id = message.chat.id
            reason = " ".join(args[2:]) if len(args) > 2 else None
            return chat_id, reason

        return message.chat.id, " ".join(args[1:]) if len(args) > 1 else None

    async def extract_chat_from_reply(self, rep):
        reply = rep.caption if rep.caption else rep.text

        if not reply:
            return None

        patterns = [
            r"-100\d{10}",
            r"https?://t\.me/(joinchat/|)\+?[a-zA-Z0-9_-]+",
            r"@[a-zA-Z0-9_]+",
        ]

        for pattern in patterns:
            match = re.search(pattern, reply)
            if match:
                chat = match.group(0)
                return chat

        return None

    async def extract_chat(self, client, message):
        args = message.text.strip().split()
        chat_id = None
        rep = message.reply_to_message

        if rep:
            chat_id = await self.extract_chat_from_reply(rep)

        if len(args) >= 2:
            chat = args[1]

            if chat.startswith("@"):
                try:
                    chat_info = await client.get_chat(chat)
                    chat_id = chat_info.id
                except Exception as e:
                    print(f"🔴 Error saat mendapatkan chat ID: {e}")
                    chat_id = None
            elif chat.startswith("-100") or chat.isdigit():
                try:
                    chat_id = int(chat)
                except ValueError:
                    chat_id = None
            else:
                chat_id = None

        if chat_id is None:
            chat_id = message.chat.id

        return chat_id

    def get_var_and_value(self, message, is_premium):
        if len(message.command) < 3:
            return None, None
        command, variable, value = message.command[:3]

        if is_premium:
            emoji_id = None
            if message.entities:
                for entity in message.entities:
                    if entity.custom_emoji_id:
                        emoji_id = entity.custom_emoji_id
                        break
            if emoji_id:
                return variable, f"<emoji id={emoji_id}>{value}</emoji>"

        return variable, value

    def extract_var_and_value(self, message):
        args = message.text.strip().split()
        cmd = None
        var = None
        value = None

        rep = message.reply_to_message
        if rep:
            if len(args) <= 1:
                return args[0], None, None
            elif len(args) == 2:
                return args[0], args[1], None

        if len(args) < 3:
            return args[0], None, None

        cmd, var, value = args[0], args[1], " ".join(args[2:])

        return cmd, var, value

    def extract_var(self, message):
        args = message.text.strip().split()
        cmd = None
        var = None

        rep = message.reply_to_message
        if rep:
            if len(args) <= 1:
                return args[0], None
            elif len(args) == 2:
                return args[0], args[1]

        if len(args) < 3:
            return args[0], None

        cmd, var = args[0], " ".join(args[0:])

        return cmd, var

    def set_prefix(self, user_id, prefix):
        self._prefix[self.me.id] = prefix

    def get_prefix(self, user_id):
        return self._prefix.get(user_id, [".", ",", "?", "+", "!"])

    def add_sudoers(self, bot_id, user_id):
        if bot_id not in self._sudoers:
            self._sudoers[bot_id] = []

        if user_id not in self._sudoers[bot_id]:
            self._sudoers[bot_id].append(user_id)
            return True
        return False

    def remove_sudoers(self, bot_id, user_id):
        if bot_id in self._sudoers and user_id in self._sudoers[bot_id]:
            self._sudoers[bot_id].remove(user_id)
            return True
        return False

    def get_sudoers(self, user_id):
        return self._sudoers.get(user_id, [])


class UserBot(BaseClient):
    __module__ = "pyrogram.client"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_version = "18.01"
        self.device_model = BOT_NAME
        self.system_version = "KN-Devs"
        self.group_call = PyTgCalls(self)
        self.plugins = {"enabled": True, "root": "plugins", "include": "plugins"}
        self.ipv6 = False

    def on_message(self, filters=None, group=-1):
        def decorator(func):
            for ub in self._ubot:
                ub.add_handler(MessageHandler(func, filters), group)
            return func

        return decorator

    def on_edited_message(self, filters=None, group=-1):
        def decorator(func):
            for ub in self._ubot:
                ub.add_handler(EditedMessageHandler(func, filters), group)
            return func

        return decorator

    def on_deleted_messages(self, filters=None, group=-1):
        # FIX: sebelumnya salah mendaftar ke group_call.on_update(stream_end)
        def decorator(func):
            for ub in self._ubot:
                ub.add_handler(DeletedMessagesHandler(func, filters), group)
            return func

        return decorator

    def on_disconnect(self):
        def decorator(func):
            for ub in self._ubot:
                ub.add_handler(DisconnectHandler(func))
            return func

        return decorator

    def group_call_ends(self):
        def decorator(func):
            for ub in self._ubot:
                # FIX: stream_end adalah class, wajib dipanggil dengan kurung
                ub.group_call.on_update(fl.stream_end())(func)
            return func

        return decorator

    def user_prefix(self, cmd):
        command_re = re.compile(r"([\"'])(.*?)(?<!\\)\1|(\S+)")

        async def func(_, client, message):
            if message.text:
                text = message.text.strip().encode("utf-8").decode("utf-8")
                username = client.me.username or ""
                prefixes = self.get_prefix(client.me.id)

                if not text:
                    return False

                for prefix in prefixes:
                    if not text.startswith(prefix):
                        continue

                    without_prefix = text[len(prefix) :]

                    for command in cmd.split("|"):
                        if not re.match(
                            rf"^(?:{command}(?:@?{username})?)(?:\s|$)",
                            without_prefix,
                            flags=re.IGNORECASE | re.UNICODE,
                        ):
                            continue

                        without_command = re.sub(
                            rf"{command}(?:@?{username})?\s?",
                            "",
                            without_prefix,
                            count=1,
                            flags=re.IGNORECASE | re.UNICODE,
                        )
                        message.command = [command] + [
                            re.sub(r"\\([\"'])", r"\1", m.group(2) or m.group(3) or "")
                            for m in command_re.finditer(without_command)
                        ]

                        return True

                return False

        return filters.create(func)

    async def start(self):
        await super().start()
        await self.group_call.start()
        prefixes = await dB.get_pref(self.me.id)
        if prefixes:
            self._prefix[self.me.id] = prefixes
        else:
            self._prefix[self.me.id] = [".", ",", "?", "+", "!"]
        self._ubot.append(self)
        self._get_my_id.append(self.me.id)
        logger.info(f"Starting Userbot {self.me.id}|@{self.me.username}")


class Bot(BaseClient):
    def __init__(self, **kwargs):
        super().__init__(
            name="Bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            device_model=BOT_NAME,
            workers=min(32, 4 + 4),
            plugins=dict(root="assistant"),
            **kwargs,
        )

    def on_message(self, filters=None, group=-1):
        def decorator(function):
            self.add_handler(MessageHandler(function, filters), group)
            return function

        return decorator

    def on_callback_query(self, filters=None, group=-1):
        def decorator(function):
            self.add_handler(CallbackQueryHandler(function, filters), group)
            return function

        return decorator

    async def add_reseller(self):
        for user in SUDO_OWNERS:
            if user not in await dB.get_list_from_var(BOT_ID, "SELLER"):
                await dB.add_to_var(BOT_ID, "SELLER", user)
        if OWNER_ID not in await dB.get_list_from_var(BOT_ID, "SELLER"):
            await dB.add_to_var(BOT_ID, "SELLER", OWNER_ID)
        for user in await dB.get_list_from_var(BOT_ID, "SELLER"):
            if user not in AKSES_DEPLOY:
                AKSES_DEPLOY.append(user)
        for u in await dB.get_list_from_var(BOT_ID, "SELLER"):
            await dB.set_var(u, "plan", "is_pro")

    async def start(self):
        await super().start()
        self.id = self.me.id
        self.fullname = f"{self.me.first_name} {self.me.last_name or ''}"
        self.username = self.me.username
        self.mention = self.me.mention

        await self.set_bot_commands(
            [
                types.BotCommand("start", "Start the bot."),
                types.BotCommand("status", "Status account."),
                types.BotCommand("restart", "Restart userbots."),              
            ]
        )
        for modul in PLUGINS:
            imported_module = importlib.import_module(f"plugins.{modul}")
            is_pro_plugin = getattr(imported_module, "IS_PRO", False)
            module_name = getattr(imported_module, "__MODULES__", "").lower()
            if module_name:
                HELPABLE[module_name] = {
                    "module": imported_module,
                    "is_pro": is_pro_plugin,
                }
        logger.info(f"🔥 {self.username} Bot Started 🔥")


alice = UserBot(name="Clients", plugins=dict(root="plugins"))
bot = Bot()
