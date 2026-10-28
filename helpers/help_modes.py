import asyncio
import copy
import inspect
from collections import OrderedDict
from time import monotonic
from uuid import uuid4

from pyrogram import StopPropagation, filters
from pyrogram.enums import ButtonStyle
from pyrogram.errors import FloodWait, MessageNotModified
from pyrogram.helpers import ikb
from pyrogram.types import InlineQueryResultArticle, InputRichMessage, InputTextMessageContent, RichBlockButtons, RichMessageButton

from clients import alice, bot
from config import BOT_NAME, HELPABLE, USENAME_OWNER
from database import dB, state
from helpers.buttons import ButtonUtils, _help_categories
from helpers.helprich import build_help_rich, build_help_text, help_rich_on
from helpers.inlinerich import InputRichMessageContent
from logs import logger

MODES = ("simple", "table", "modern")
_PANELS = OrderedDict()
_TTL = 3600


async def get_help_mode(user_id):
    mode = await dB.get_var(user_id, "HELP_MODE")
    return mode if mode in MODES else ("table" if await help_rich_on() else "simple")


def _categories(visible):
    others = {key: data for key, data in visible.items() if data["module"].__MODULES__.casefold() not in ("mode", "help")}
    return [(name, keys) for name, keys in _help_categories(others) if keys]


async def _new_panel(user, visible=None, argument=""):
    for token, panel in tuple(_PANELS.items()):
        if monotonic() - panel["created"] > _TTL:
            _PANELS.pop(token, None)
    while len(_PANELS) >= 500:
        _PANELS.popitem(last=False)
    if visible is None:
        pro = await dB.get_var(user.id, "plan") == "is_pro"
        visible = {key: data for key, data in HELPABLE.items() if pro or not data["is_pro"]}
    visible = {key: data for key, data in visible.items() if hasattr(data["module"], "__MODULES__")}
    token = uuid4().hex[:12]
    panel = {
        "token": token, "user": user, "visible": visible, "categories": _categories(visible),
        "keys": list(visible), "prefix": alice.get_prefix(user.id), "mode": await get_help_mode(user.id),
        "view": "home", "category": 0, "module": 0, "page": 0, "created": monotonic(), "lock": asyncio.Lock(),
    }
    argument = argument.strip().lower()
    if argument.isdigit():
        panel["page"] = max(0, int(argument) - 1)
    elif argument:
        if argument not in visible:
            argument = next((key for key, data in visible.items() if data["module"].__MODULES__.casefold() == argument), argument)
        if argument not in visible:
            raise ValueError(f"Tidak ada modul bernama {argument}.")
        panel.update(view="module", module=panel["keys"].index(argument))
    _PANELS[token] = panel
    return panel


class _RichCapture:
    def __init__(self, client):
        self.client, self.rich = client, None

    def __getattr__(self, name):
        return getattr(self.client, name)

    async def send_rich_message(self, chat_id, rich_message, **kwargs):
        self.rich = rich_message
        return rich_message

    async def edit_rich_message(self, chat_id, message_id, rich_message, **kwargs):
        self.rich = rich_message
        return rich_message


def _with_bubbles(rich, rows):
    blocks = [RichBlockButtons(buttons=[[
        RichMessageButton(text=label, callback_data=value, style=style.name.lower())
        for label, value, style in row
    ]]) for row in rows if row]
    result = copy.copy(rich)
    if result.blocks:
        result.blocks = list(result.blocks) + blocks
    elif result.html:
        result.html += "\n" + InputRichMessage(blocks=blocks).write().html
    else:
        raise ValueError("Renderer modern membutuhkan rich blocks atau HTML.")
    return result


async def _render(panel):
    user, visible = panel["user"], panel["visible"]
    prefix = panel["prefix"]
    p = next((item for item in prefix if item), ".")
    data = lambda action: f"hm:{panel['token']}:{action}"
    rows, category = [], None
    rich, plain = None, ""
    pages = 1
    text_help = await dB.get_var(user.id, "text_help") or f"**{BOT_NAME} by {USENAME_OWNER}**"

    if panel["view"] == "module":
        module = visible[panel["keys"][panel["module"]]]["module"]
        plain = getattr(module, "__HELP__", "Bantuan belum tersedia.").format(p, text_help)
        if panel["mode"] != "simple":
            renderer = getattr(module, "__HELP_RICH__", None)
            if renderer is not None:
                capture = _RichCapture(bot)
                params = inspect.signature(renderer).parameters
                options = {key: value for key, value in {"message_id": 1, "prev_page_num": 0}.items() if key in params}
                await renderer(capture, 0, p, text_help, **options)
                rich = capture.rich
                if rich is None:
                    raise RuntimeError("__HELP_RICH__ tidak menghasilkan rich message.")
            else:
                rich = InputRichMessage(html=plain)
    else:
        if panel["view"] == "category":
            title, keys = panel["categories"][panel["category"]]
            entries = [(visible[key]["module"].__MODULES__, f"module:{panel['keys'].index(key)}") for key in keys]
            per_page = 10
        else:
            entries = [(name, f"category:{index}") for index, (name, _) in enumerate(panel["categories"])]
            per_page = 6
        pages = max(1, (len(entries) + per_page - 1) // per_page)
        panel["page"] = min(max(panel["page"], 0), pages - 1)
        start = panel["page"] * per_page
        items = [(label, data(action), ButtonStyle.PRIMARY) for label, action in entries[start:start + per_page]]
        rows = [items[i:i + 2] for i in range(0, len(items), 2)]
        if panel["view"] == "category":
            category = (title, len(keys), panel["page"], pages)
        plain = build_help_text(user, prefix, len(visible), text_help, category=category, main_page=(panel["page"], pages))
        if panel["mode"] != "simple":
            rich = build_help_rich(user, prefix, len(visible), text_help, category=category, main_page=(panel["page"], pages))

    if panel["view"] == "home":
        mode_key = next((key for key, item in visible.items() if item["module"].__MODULES__.casefold() in ("mode", "help")), None)
        if mode_key is not None:
            rows.append([("Mode", data(f"module:{panel['keys'].index(mode_key)}"), ButtonStyle.PRIMARY)])
    if pages > 1:
        rows.append([
            ("\u276e", data(f"page:{(panel['page'] - 1) % pages}"), ButtonStyle.PRIMARY),
            ("\u2716", data("close"), ButtonStyle.DANGER),
            ("\u276f", data(f"page:{(panel['page'] + 1) % pages}"), ButtonStyle.PRIMARY),
        ])
    else:
        rows.append([("\u2716", data("close"), ButtonStyle.DANGER)])
    if panel["view"] != "home":
        rows.append([("Back", data("back"), ButtonStyle.DANGER)])
    if panel["mode"] == "modern":
        return _with_bubbles(rich, rows), plain, None
    return rich, plain, ikb(rows)


async def send_help_menu(client, message, visible=None):
    panel = await _new_panel(message.from_user, visible)
    rich, text, markup = await _render(panel)
    if rich is not None:
        return await client.send_rich_message(message.chat.id, rich, reply_markup=markup)
    return await message.reply_text(text, reply_markup=markup, disable_web_page_preview=True)


async def help_cmd(client, message):
    panel = await _new_panel(client.me, argument=client.get_arg(message) or "")
    query = f"help panel {panel['token']}"
    panel["query"] = query
    sent = await ButtonUtils.send_inline_bot_result(message, message.chat.id, bot.me.username, query)
    if not sent:
        return await message.reply("Gagal membuka help. Periksa izin inline dan log server.")
    panel["message"] = state.get(client.me.id, query)
    try:
        await message.delete()
    except Exception:
        pass


async def helpmode_cmd(client, message):
    user_id = message.from_user.id if client.me.is_bot else client.me.id
    parts = (message.text or "").split()
    mode = parts[1].lower() if len(parts) == 2 else ""
    if mode not in MODES:
        current = await get_help_mode(user_id)
        return await message.reply(f"Mode help: <b>{current}</b>\nGunakan <code>helpmode simple</code>, <code>helpmode table</code>, atau <code>helpmode modern</code>.")
    await dB.set_var(user_id, "HELP_MODE", mode)
    return await message.reply(f"Mode Help ({mode}) aktif")


@bot.on_message(filters.command("helpmode") & filters.incoming, group=-15)
async def _mode_message(client, message):
    try:
        banned = await dB.get_list_from_var(client.me.id, "BANNED_USERS") or []
        if message.from_user and message.from_user.id not in banned:
            await helpmode_cmd(client, message)
    finally:
        raise StopPropagation


@bot.on_inline_query(filters.regex(r"(?i)^help(?:\s|$)"), group=-15)
async def _inline_help(client, query):
    try:
        banned = await dB.get_list_from_var(client.me.id, "BANNED_USERS") or []
        if query.from_user.id in banned:
            return await query.answer([], cache_time=0, is_personal=True)
        parts = (query.query or "").split(None, 2)
        if len(parts) == 3 and parts[1] == "panel":
            panel = _PANELS.get(parts[2])
            if not panel or panel["user"].id != query.from_user.id:
                raise ValueError("Menu kedaluwarsa. Buka help lagi.")
        else:
            argument = (query.query or "").split(None, 1)
            panel = await _new_panel(query.from_user, argument=argument[1] if len(argument) > 1 else "")
        rich, text, markup = await _render(panel)
        content = InputRichMessageContent(rich) if rich is not None else InputTextMessageContent(text, disable_web_page_preview=True)
        await query.answer([InlineQueryResultArticle(id=panel["token"], title="Help Menu", input_message_content=content, reply_markup=markup)], cache_time=0, is_personal=True)
    except FloodWait:
        raise
    except Exception:
        logger.exception("helpmode: inline gagal")
        await query.answer([InlineQueryResultArticle(title="Help gagal dibuka", input_message_content=InputTextMessageContent("Help gagal dimuat. Periksa log server."))], cache_time=0, is_personal=True)
    finally:
        raise StopPropagation


async def _close_help(callback, panel):
    if callback.message:
        await callback.message.delete()
        return True
    owner_id = panel["user"].id
    sender = next((client for client in alice._ubot if client.me.id == owner_id), None)
    query = panel.get("query")
    info = panel.get("message") or (state.get(owner_id, query) if query else None)
    if not sender or not isinstance(info, dict) or info.get("me") != owner_id:
        return False
    if not info.get("chat") or not info.get("_id"):
        return False
    await sender.delete_messages(info["chat"], info["_id"])
    return True


@bot.on_callback_query(filters.regex(r"^hm:"), group=-15)
async def _help_callback(client, callback):
    try:
        _, token, action, *values = callback.data.split(":")
        panel = _PANELS.get(token)
        if not panel or monotonic() - panel["created"] > _TTL:
            return await callback.answer("Menu kedaluwarsa. Buka help lagi.", show_alert=True)
        if callback.from_user.id != panel["user"].id:
            return await callback.answer("Buka help milikmu sendiri.", show_alert=True)
        banned = await dB.get_list_from_var(client.me.id, "BANNED_USERS") or []
        if callback.from_user.id in banned:
            return await callback.answer("Akun diblokir.", show_alert=True)
        async with panel["lock"]:
            if action == "close":
                if not await _close_help(callback, panel):
                    return await callback.answer("Pesan tidak dapat dihapus. Buka ulang lewat command help pada userbot aktif.", show_alert=True)
                _PANELS.pop(token, None)
                return await callback.answer()
            if action == "category":
                panel.update(view="category", category=int(values[0]), page=0)
            elif action == "module":
                panel.update(view="module", module=int(values[0]), page=0)
            elif action == "page":
                panel["page"] = int(values[0])
            elif action == "back":
                key = panel["keys"][panel["module"]] if panel["view"] == "module" else None
                parent = next(((index, keys.index(key) // 10) for index, (_, keys) in enumerate(panel["categories"]) if key in keys), None)
                if parent is not None:
                    panel.update(view="category", category=parent[0], page=parent[1])
                else:
                    panel.update(view="home", page=0)
            else:
                return await callback.answer("Ubah mode lewat command helpmode, bukan tombol.", show_alert=True)
            panel["mode"] = await get_help_mode(panel["user"].id)
            await callback.answer()
            rich, text, markup = await _render(panel)
            if callback.inline_message_id:
                await client.edit_inline_text(callback.inline_message_id, text=text if rich is None else None, rich_message=rich, reply_markup=markup)
            elif rich is not None:
                await client.edit_rich_message(callback.message.chat.id, callback.message.id, rich, reply_markup=markup)
            else:
                await client.edit_message_text(callback.message.chat.id, callback.message.id, text, reply_markup=markup, disable_web_page_preview=True)
    except MessageNotModified:
        pass
    except FloodWait:
        raise
    except Exception:
        logger.exception("helpmode: callback gagal")
        try:
            await callback.answer("Help gagal diproses. Periksa log server.", show_alert=True)
        except Exception:
            pass
    finally:
        raise StopPropagation
