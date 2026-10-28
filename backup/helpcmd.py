from pyrogram.types import InlineKeyboardMarkup

from clients import alice
from config import BOT_NAME, HELPABLE, USENAME_OWNER
from database import dB
from helpers import paginate_modules


async def basic_plugins(client, message):
    user_id = message.from_user.id
    if await dB.get_var(message.from_user.id, "is_bot_pro"):
        await dB.remove_var(message.from_user.id, "is_bot_pro")
    is_pro = False
    visible_helpable = {
        name: data for name, data in HELPABLE.items() if is_pro or not data["is_pro"]
    }
    prefix = alice.get_prefix(user_id)
    text_help = (
        await dB.get_var(user_id, "text_help")
        or f"**🤖 {BOT_NAME} by {USENAME_OWNER}**"
    )
    full = f"<a href=tg://user?id={message.from_user.id}>{message.from_user.first_name} {message.from_user.last_name or '' }</a>"
    msg = """<b>
Inline Help 
    Prefixes: <code>{}</code>
    Plugins: <code>{}</code>
    {} </b>
<blockquote>{}</blockquote>""".format(
        " ".join(prefix), len(visible_helpable), full, text_help
    )
    await dB.set_var(user_id, "is_bot", True)
    return await message.reply_text(
        msg,
        reply_markup=InlineKeyboardMarkup(
            paginate_modules(0, visible_helpable, "help", is_bot=True)
        ),
    )


async def pro_plugins(client, message):
    user_id = message.from_user.id
    prefix = alice.get_prefix(user_id)
    text_help = (
        await dB.get_var(user_id, "text_help")
        or f"**🤖 {BOT_NAME} by {USENAME_OWNER}**"
    )
    full = f"<a href=tg://user?id={message.from_user.id}>{message.from_user.first_name} {message.from_user.last_name or '' }</a>"
    msg = """<b>
Inline Help 
    Prefixes: <code>{}</code>
    Plugins: <code>{}</code>
    {} </b>
<blockquote>{}</blockquote>""".format(
        " ".join(prefix), len(HELPABLE), full, text_help
    )
    await dB.set_var(user_id, "is_bot", True)
    await dB.set_var(user_id, "is_bot_pro", True)
    return await message.reply_text(
        msg,
        reply_markup=InlineKeyboardMarkup(
            paginate_modules(0, HELPABLE, "help", is_bot=True)
        ),
    )


async def help_cmd(client, message):
    em = Emoji(client)
    await em.get()
    plan = await dB.get_var(client.me.id, "plan")
    is_pro = True if plan == "is_pro" else False
    visible_helpable = {
        name: data for name, data in HELPABLE.items() if is_pro or not data["is_pro"]
    }
    if not client.get_arg(message):
        query = "help"
        chat_id = (
            message.chat.id if len(message.command) < 2 else message.text.split()[1]
        )
        try:
            inline = await ButtonUtils.send_inline_bot_result(
                message,
                chat_id,
                bot.me.username,
                query,
            )
            if inline:
                return await message.edit()
        except Exception as error:
            return await message.reply(f"{em.gagal}Error: {str(error)}")
    else:
        nama = f"{client.get_arg(message)}"
        pref = client.get_prefix(client.me.id)
        x = next(iter(pref))
        text_help2 = f"<blockquote>**🤖 {BOT_NAME} by {USENAME_OWNER}**</blockquote>"
        if nama in visible_helpable:
            module = visible_helpable[nama]["module"]
            if hasattr(module, "__HELP_RICH__"):
                return await module.__HELP_RICH__(client, message.chat.id, x, text_help2)
            return await message.reply(
                f"{module.__HELP__.format(x, text_help2)}",
            )
        else:
            return await message.reply(
                f"{em.gagal}<b>Tidak ada modul bernama <code>{nama}</code></b>"
            )