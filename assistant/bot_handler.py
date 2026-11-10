import traceback

from pyrogram import filters
from clients import bot
from command import (
    addtoken_cmd,
    deltoken_cmd,
    cektoken_cmd,
    blacklist_cmd,
    unblacklist_cmd,
    listblacklist_cmd,
    add_prem_user,
    add_pro_user,
    add_seller,
    add_seller,
    addexpired_user,
    backup,
    button_bot,
    cb_evaluasi_bot,
    cb_gitpull2,
    cb_shell,
    cek_expired,
    cek_status_akun,
    close_kb,
    copymsg_bot,
    get_prem_user,
    get_seles_user,
    getid_bot,
    lapor_bug,
    make_stickers,
    mass_report,
    outgoing_reply,
    referal_command,
    remove_stickers,
    request_bot,
    restart_userbot,
    restore,
    send_broadcast,
    send_ubot_1,
    send_ubot_2,
    set_plan,
    setads_bot,
    setimg_start,
    start_home,
    token_cmd,
    un_prem_user,
    un_seller,
    unexpired,
)
from helpers import CMD
from logs import logger


@CMD.BOT(
    [
        "addtoken",
        "deltoken",
        "cektoken",
        "blacklist",
        "unblacklist",
        "listblacklist",
        "restart",
        "setimg",
        "referral",
        "start",
        "button",
        "id",
        "request",
        "bukti",
        "setads",
        "token",
        "getubot",
        "cekubot",
        "restore",
        "backup",
        "sh",
        "shell",
        "e",
        "eval",
        "reboot",
        "update",
        "kontol",
        "close",
        "status",
        "kang",
        "unkang",
        "addprem",
        "unprem",
        "listprem",
        "addexpired",
        "unexpired",
        "cek",
        "massreport",
        "addseller",
        "unseller",
        "listseller",
        "bc",
        "setplan",
        "report",
        "addpro",
    ]
)
async def _(client, message):
    try:
        command = message.command
        logger.info(f"Bot command:{command}")
        if command[0] == "restart":
            return await restart_userbot(client, message)
        elif command[0] == "addtoken":
            return await addtoken_cmd(client, message)
        elif command[0] == "deltoken":
            return await deltoken_cmd(client, message)
        elif command[0] == "cektoken":
            return await cektoken_cmd(client, message)
        elif command[0] == "bl":
            return await blacklist_cmd(client, message)
        elif command[0] == "unbl":
            return await unblacklist_cmd(client, message)
        elif command[0] == "listbl":
            return await listblacklist_cmd(client, message)
        elif command[0] == "setimg":
            return await setimg_start(client, message)
        elif command[0] == "referral":
            return await referal_command(client, message)
        elif command[0] == "start":
            return await start_home(client, message)
        elif command[0] == "button":
            return await button_bot(client, message)
        elif command[0] == "id":
            return await getid_bot(client, message)
        elif command[0] == "request":
            return await request_bot(client, message)
        elif command[0] == "bukti":
            return await lapor_bug(client, message)
        elif command[0] == "setads":
            return await setads_bot(client, message)
        elif command[0] == "token":
            return await token_cmd(client, message)
        elif command[0] == "getubot":
            return await send_ubot_1(client, message)
        elif command[0] == "cekubot":
            return await send_ubot_2(client, message)
        elif command[0] == "restore":
            return await restore(client, message)
        elif command[0] == "backup":
            return await backup(client, message)
        elif command[0] in ["sh", "shell"]:
            return await cb_shell(client, message)
        elif command[0] in ["e", "eval"]:
            return await cb_evaluasi_bot(client, message)
        elif command[0] in ["reboot", "update"]:
            return await cb_gitpull2(client, message)
        elif command[0] == "kontol":
            return await copymsg_bot(client, message)
        elif command[0] == "close":
            return await close_kb(client, message)
        elif command[0] == "status":
            return await cek_status_akun(client, message)
        elif command[0] == "kang":
            return await make_stickers(client, message)
        elif command[0] == "unkang":
            return await remove_stickers(client, message)

        elif command[0] == "massreport":
            return await mass_report(client, message)
        elif command[0] == "addprem":
            return await add_prem_user(client, message)
        elif command[0] == "addpro":
            return await add_pro_user(client, message)
        elif command[0] == "unprem":
            return await un_prem_user(client, message)
        elif command[0] == "listseller":
            return await get_seles_user(client, message)
        elif command[0] == "addexpired":
            return await addexpired_user(client, message)
        elif command[0] == "cek":
            return await cek_expired(client, message)
        elif command[0] == "unexpired":
            return await unexpired(client, message)
        elif command[0] == "unseller":
            return await un_seller(client, message)
        elif command[0] == "addseller":
            return await add_seller(client, message)
        elif command[0] == "listprem":
            return await get_prem_user(client, message)
        elif command[0] == "bc":
            return await send_broadcast(client, message)
        elif command[0] == "report":
            return await mass_report(client, message)
        elif command[0] == "setplan":
            return await set_plan(client, message)
    except Exception:
        logger.error(f"Error command bot: {traceback.format_exc()}")


@CMD.CHAT_FORWARD("OUTGOING", bot)
async def _(client, message):
    return await outgoing_reply(client, message)