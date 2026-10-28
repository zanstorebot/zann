from config import HELPABLE
from database import dB


async def _send_help(client, message, visible_helpable):
    from helpers.help_modes import send_help_menu
    return await send_help_menu(client, message, visible_helpable)


async def basic_plugins(client, message):
    user_id = message.from_user.id
    if await dB.get_var(user_id, "is_bot_pro"):
        await dB.remove_var(user_id, "is_bot_pro")
    visible = {name: data for name, data in HELPABLE.items() if not data["is_pro"]}
    await dB.set_var(user_id, "is_bot", True)
    return await _send_help(client, message, visible)


async def pro_plugins(client, message):
    user_id = message.from_user.id
    await dB.set_var(user_id, "is_bot", True)
    await dB.set_var(user_id, "is_bot_pro", True)
    return await _send_help(client, message, HELPABLE)


async def helprich_cmd(client, message):
    return await message.reply(
        "Gunakan: <code>helpmode simple</code>, <code>helpmode table</code>, "
        "atau <code>helpmode modern</code>."
    )
