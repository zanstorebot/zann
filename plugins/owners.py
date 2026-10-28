from clients import alice, bot
from command import (add_prem_user, add_pro_user, add_seller, cb_evalusi, cb_evalusi2,
                     cb_gitpull2, cb_shell, code_cmd, edit_cmd, plugins_cmd, seller_cmd,
                     set_cmd, set_plan, undo_cmd, un_prem_user, un_seller, getubot_cmd,
                     batu_ku, love_ku, nangis_ku, crot_ku, helprich_cmd, update_push_kode)
from helpers import CMD
from config import SUDO_OWNERS


@CMD.UBOT("batu")
@CMD.DEV_CMD("batu")
@CMD.FAKEDEV("batu")
@CMD.NLX
async def _(client: alice, message):
    return await batu_ku(client, message)

@CMD.UBOT("love")
@CMD.DEV_CMD("love")
@CMD.FAKEDEV("love")
@CMD.NLX
async def _(client: alice, message):
    return await love_ku(client, message)


@CMD.UBOT("nangis")
@CMD.DEV_CMD("nangis")
@CMD.FAKEDEV("nangis")
@CMD.NLX
async def _(client: alice, message):
    return await nangis_ku(client, message)


@CMD.UBOT("crot")
@CMD.DEV_CMD("nangis")
@CMD.FAKEDEV("nangis")
@CMD.NLX
async def _(client: alice, message):
    return await crot_ku(client, message)


@CMD.UBOT("addprem")
@CMD.SELLER_AND_GC
async def _(client, message):
    return await add_prem_user(client, message)


@CMD.UBOT("addpro")
@CMD.SELLER_AND_GC
async def _(client, message):
    return await add_pro_user(client, message)


@CMD.UBOT("set_plan")
@CMD.SELLER_AND_GC
async def _(client, message):
    return await set_plan(client, message)


@CMD.UBOT("unprem")
@CMD.SELLER_AND_GC
async def _(client, message):
    return await un_prem_user(client, message)


@CMD.UBOT("addseller")
@CMD.FAKE_NLX
async def _(client, message):
    return await add_seller(client, message)


@CMD.UBOT("unseller")
@CMD.FAKE_NLX
async def _(client, message):
    return await un_seller(client, message)


@CMD.UBOT("getubot")
@CMD.FAKE_NLX
async def _(client, message):
    return await getubot_cmd(client, message)


@CMD.UBOT("shell|sh")
@CMD.NLX
async def _(client: alice, message):
    return await cb_shell(client, message)


@CMD.UBOT("code|line")
@CMD.NLX
async def _(client, message):
    return await code_cmd(client, message)


@CMD.UBOT("edit")
@CMD.NLX
async def _(client, message):
    return await edit_cmd(client, message)


@CMD.UBOT("set|setvar")
@CMD.NLX
async def _(client, message):
    return await set_cmd(client, message)


@CMD.UBOT("undo")
@CMD.NLX
async def _(client, message):
    return await undo_cmd(client, message)


@CMD.UBOT("x|xeval")
@CMD.NLX
@CMD.DEV_CMD("xeval")
async def _(client: alice, message):
    return await cb_evalusi2(client, message)


@CMD.UBOT("eval|ev")
@CMD.NLX
@CMD.DEV_CMD("ceval")
async def _(client: alice, message):
    return await cb_evalusi(client, message)


@CMD.UBOT("e")
async def _(client: alice, message):
    deva = message.from_user or message.sender_chat
    if deva.id not in SUDO_OWNERS:
        return
    return await cb_evalusi(client, message)


@CMD.UBOT("e")
@CMD.NLX
async def _(client: bot, message, _):
    return await cb_evalusi(client, message)


@CMD.UBOT("p")
async def _(client: alice, message):
    return await cb_evalusi(client, message)


@CMD.UBOT("reboot|update")
@CMD.FAKE_NLX
async def _(client: alice, message):
    return await cb_gitpull2(client, message)

@CMD.UBOT("updatee")
@CMD.FAKE_NLX
async def _(client: alice, message):
    return await update_push_kode(client, message)

@CMD.UBOT("seller")
@CMD.FAKE_NLX
async def _(client, message):
    return await seller_cmd(client, message)


@CMD.UBOT("loadplugins|unloadplugins|listplugins")
@CMD.NLX
async def _(client, message):
    return await plugins_cmd(client, message)


@CMD.UBOT("helprich")
@CMD.OWNER
async def _(client, message):
    return await helprich_cmd(client, message)
