from datetime import datetime
from time import time

from pyrogram import enums
from pyrogram.errors import ChannelPrivate
from pyrogram.helpers import kb, InputRichMessage, send_rich, table, cell, divider
from pyrogram.raw.functions import Ping
from pyrogram.types import ReplyKeyboardRemove, InputRichMessage, RichTextMarked, RichTextTextMention, RichTextBold, RichTextCustomEmoji
from pytz import timezone

from clients import alice
from config import BOT_NAME, SUDO_OWNERS
from database import dB
from helpers import Emoji, TokenReferal, get_time, start_time
from logs import logger


def emo(emoji_id, alt="✨"):
    return RichTextCustomEmoji(custom_emoji_id=str(emoji_id), alternative_text=alt)

async def mestats_cmd(client, message):
    em = Emoji(client)
    await em.get()
    pong_, uptime_, owner_, ubot_, proses_, sukses_ = await em.get_costum_text()
    proses = await message.reply_text(f"{em.proses}**{proses_}**")
    start = datetime.now()
    zz = 0
    nanki = 0
    luci = 0
    tgr = 0
    ceger = 0
    kntl = 0
    benet = 0
    dimari = set()
    try:
        async for dialog in client.get_dialogs():
            try:
                if dialog.chat.type == enums.ChatType.PRIVATE:
                    zz += 1
                elif dialog.chat.type == enums.ChatType.BOT:
                    ceger += 1
                elif dialog.chat.type == enums.ChatType.GROUP:
                    nanki += 1
                elif dialog.chat.type == enums.ChatType.SUPERGROUP:
                    luci += 1
                    user_s = await dialog.chat.get_member(client.me.id)
                    if user_s.status in (
                        enums.ChatMemberStatus.OWNER,
                        enums.ChatMemberStatus.ADMINISTRATOR,
                    ):
                        kntl += 1
                elif dialog.chat.type == enums.ChatType.CHANNEL:
                    tgr += 1
            except ChannelPrivate:
                benet += 1
                dimari.add(dialog.chat.id)
                await client.leave_chat(dialog.chat.id)
                logger.info(f"Left chat: {dialog.chat.id}")
                continue
    except ChannelPrivate:
        benet += 1
        dimari.add(dialog.chat.id)

    end = datetime.now()
    ms = (end - start).seconds
    if not dimari:
        dimari = None
    await proses.delete()
    return await message.reply_text(
        """
>{} **Succesful extract your data in `{}` seconds
>`{}` Private Messages.
>`{}` Groups.
>`{}` Super Groups.
>`{}` Channels.
>`{}` Admin in Chats.
>`{}` Bots.
>`{}` Group With Trouble
>
>I've trouble with this chat : 
>- `{}`**""".format(
            em.sukses,
            ms,
            zz,
            nanki,
            luci,
            tgr,
            kntl,
            ceger,
            benet,
            dimari,
        )
    )


async def close_kb(client, message):
    return await message.reply_text(
        "<b>Keyboard Ditutup</b>", reply_markup=ReplyKeyboardRemove()
    )


async def cek_status_akun(client, message):
    tokenref = await TokenReferal.create()
    user_id = message.from_user.id
    seles = await dB.get_list_from_var(client.me.id, "SELLER")
    if user_id not in alice._get_my_id:
        status2 = [emo(5019523782004441717, "🔴"), " tidak aktif"]
    else:
        status2 = [emo(5021905410089550576, "🟢"), "aktif"]
    if user_id in SUDO_OWNERS:
        status = "Developer"
    elif user_id in seles:
        status = "Seller"
    else:
        status = "Costumer"
    uptime = await get_time((time() - start_time))
    await client.invoke(Ping(ping_id=0))
    exp = await dB.get_expired_date(user_id)
    if str(message.from_user.id) not in tokenref.users:
        Referral = await tokenref.generate_referral_code(str(message.from_user.id))
    else:
        getref = tokenref.users[str(message.from_user.id)]
        Referral = getref.get("referral_code")
    status_referal = await tokenref.get_referral_stats(str(user_id))
    habis = (
        exp.astimezone(timezone("Asia/Jakarta")).strftime("%Y-%m-%d %H:%M")
        if exp
        else "None"
    )
    prefix = client.get_prefix(user_id)
    plan = await dB.get_var(user_id, "plan")
    is_pro = "Pro" if plan == "is_pro" else "Basic"
    keyboard = kb([["↩️ Beranda"]], resize_keyboard=True, one_time_keyboard=True)

    rich = InputRichMessage(
        blocks=[
            table(
                [
                    [cell(
                        [emo(6104780447684757396, "💎"), RichTextBold(" Status Akun")],
                        is_header=True,
                    )],
                ],
            ),
            divider(),
            table(
                [
                    [cell([emo(5285314573237255035, "💎"), " Status Ubot"]), cell(status2)],
                    [cell([emo(5156877291397055163, "💎"), " Status Pengguna"]), cell(status)],
                    [cell([emo(6298790803414189709, "💎"), " Plan"]), cell(is_pro)],
                    [cell([emo(5300999883996536855, "💎"), " Prefix/CMD"]), cell(" ".join(prefix))],
                    [cell([emo(5017179932451668652, "💎"), " Expired"]), cell(habis)],
                    [cell([emo(6113669303410625425, "💎"), " Uptime Ubot"]), cell(uptime)],
                    [cell([emo(6176966310920983412, "💎"), " Token"]), cell(str(status_referal["token"]))],
                ],
            ),
            table(
                [
                    [cell(["AliceDevs Core v3.14 ", emo(5456140674028019486, "⚡")], align="center")],
                ],
            ),
            divider(),
        ]
    )
    return await client.send_rich_message(
        chat_id=message.chat.id,
        rich_message=rich,
        reply_markup=keyboard,
    )

