import asyncio
import random
import traceback

from html import escape as _esc

from pyrogram.errors import BadRequest
from pyrogram import enums
from pyrogram.helpers import (
    anchor,
    Button,
    RichMessageBuilder,
    heading,
    paragraph,
    divider,
    code_block,
    math_expression,
    details,
    pull_quote,
    block_quote,
    cell,
    table,
    send_rich,
    photo_block,
    video_block,
    send_markdown_rich,
)
from pyrogram.types import (
    InputRichMessage,
    RichBlockButtons,
    RichMessageButton,
    RichTextMarked,
    RichTextTextMention,
    RichTextBold,
    RichTextCustomEmoji,
)
from clients import bot
from config import DEVA, LOG_SELLER, SUDO_OWNERS, BOT_NAME
from database import dB, state
from helpers import Basic_Effect, ButtonUtils, Message, Tools, no_commands
from logs import logger
from pyrogram.types.input_content import input_rich_message as _irm


# ---------------------------------------------------------------------------
# PATCH: converter tombol bubble.
# _buttons_html bawaan fork menghasilkan <button callback_data="..."> tanpa
# <tg-button-row>, padahal format HTML Bot API 10.3 adalah:
#   <tg-button-row><tg-button type="callback_data" data="..." style="primary">
# Fungsi di bawah menggantikannya (hanya untuk proses bot ini).
# ---------------------------------------------------------------------------
BUBBLE_EMOJI = True  # False = label tombol tanpa custom emoji


def _btn_style(btn):
    st = getattr(btn, "style", None)
    if st is None:
        return None
    name = (getattr(st, "name", None) or str(st)).split(".")[-1].lower()
    return name if name in ("primary", "success", "danger") else None


def _buttons_html_fixed(block) -> str:
    rows = []
    for row in getattr(block, "buttons", []) or []:
        parts = []
        for btn in row:
            attrs = []
            if getattr(btn, "url", None):
                attrs.append('type="url"')
                attrs.append(f'url="{_esc(str(btn.url), quote=True)}"')
            else:
                data = getattr(btn, "callback_data", "") or ""
                if isinstance(data, bytes):
                    data = data.decode("utf-8", "ignore")
                attrs.append('type="callback_data"')
                attrs.append(f'data="{_esc(str(data), quote=True)}"')
            style = _btn_style(btn)
            if style:
                attrs.append(f'style="{style}"')
            label = _irm._extract_text(btn.text)
            emoji = getattr(btn, "_emoji", None)
            if BUBBLE_EMOJI and emoji:
                label = f'<tg-emoji emoji-id="{emoji[0]}">{emoji[1]}</tg-emoji> {label}'
            parts.append(f'<tg-button {" ".join(attrs)}>{label}</tg-button>')
        rows.append(f'<tg-button-row align="center">{"".join(parts)}</tg-button-row>')
    return "".join(rows)


_irm._buttons_html = _buttons_html_fixed


def _attach_emoji(btn, emoji_id, alt):
    if emoji_id:
        try:
            btn._emoji = (str(emoji_id), alt)
        except Exception:
            pass


def emo(emoji_id, alt="✨"):
    return RichTextCustomEmoji(custom_emoji_id=str(emoji_id), alternative_text=alt)


# ---------------------------------------------------------------------------
# TES BUTTON BUBBLE (tombol di dalam bubble rich message, Bot API 10.3)
# ---------------------------------------------------------------------------
def _rbtn(label, callback_data, style=None, emoji_id=None, alt="✨"):
    texts = [label]
    styles = [style]
    if style is not None:
        styles += [getattr(style, "value", str(style)), None]
    last_err = None
    for text in texts:
        for st in styles:
            kwargs = {"text": text, "callback_data": callback_data}
            if st is not None:
                kwargs["style"] = st
            try:
                btn = RichMessageButton(**kwargs)
                _attach_emoji(btn, emoji_id, alt)
                return btn
            except TypeError as er:
                last_err = er
    raise last_err
  

def _rbtn_url(label, url, style=None, emoji_id=None, alt="✨"):
    styles = [style]
    if style is not None:
        styles += [getattr(style, "value", str(style)), None]
    last_err = None
    for st in styles:
        kwargs = {"text": label, "url": url}
        if st is not None:
            kwargs["style"] = st
        try:
            btn = RichMessageButton(**kwargs)
            _attach_emoji(btn, emoji_id, alt)
            return btn
        except TypeError as er:
            last_err = er
    raise last_err
  

def bubble_buttons(is_admin=False):
    PELER = enums.ButtonStyle
    rows = [
        [
            _rbtn("Mulai Buat Userbot", "btn_mulai", PELER.PRIMARY, "5456140674028019486"),
        ],
        [
            _rbtn("Trial Userbot", "btn_trial", PELER.PRIMARY, "6176861049862493512"),
            _rbtn("Cek Fitur", "btn_fitur", PELER.PRIMARY, "5282843764451195532"),
        ],
        [
            _rbtn("Referral", "btn_referral", PELER.SUCCESS, "5355235390980642171"),
            _rbtn("Token", "btn_token", PELER.SUCCESS, "6176966310920983412"),
        ],
        [
            _rbtn("Reset Prefix", "btn_resetprefix", PELER.DANGER, "5300999883996536855"),
        ],
    ]
    if is_admin:
        rows.append([_rbtn("Updates", "btn_updates", PELER.DANGER, "5300999883996536855")])
    return RichBlockButtons(buttons=rows)
  
async def addgroup_bot(client, message):
    user_id = message.from_user.id if message.from_user else message.chat.id
    bot_username = client.me.username or ""
    return await client.send_message(
        user_id,
        "<b>Tambahkan saya ke grupmu:</b>"
        f"https://t.me/{bot_username}?startgroup=true",
    )

  
async def gen_image(client):
    image = None
    file_id = await dB.get_var(client.me.id, "IMAGE_START")
    if file_id:
        image = {"photo": file_id} if file_id.startswith("AgAC") else {"video": file_id}
        return image
    return None


async def setimg_start(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in DEVA:
        return
    if message.reply_to_message:
        proses = await message.reply("<blockquote>**Tunggu sebentar..**</blockquote>")
        reply = message.reply_to_message
        if not reply.media:
            return await proses.edit(
                "<blockquote>**Silahkan balas ke pesan foto atau video**</blockquote>"
            )
        file_id = Tools.get_file_id(reply).get("file_id")
        await dB.set_var(client.me.id, "IMAGE_START", file_id)
        return await proses.edit(
            f"<blockquote>**Berhasil mengatur media start ke: <a href='{reply.link}'>pesan ini</a>**</blockquote>",
            disable_web_page_preview=True,
        )
    else:
        if len(message.command) == 2:
            args = message.command[1]
            if args in ["off", "disable"]:
                await dB.remove_var(client.me.id, "IMAGE_START")
                return await message.reply(
                    "<blockquote>**Media start dinon-aktifkan**</blockquote>"
                )
            else:
                return await message.reply(
                    "<blockquote>**Silahkan balas ke media jika ingin mengatur pesan start media, atau ketik `/setimg off` untuk menon-aktifkan pesan media start.**</blockquote>"
                )
        else:
            return await message.reply(
                "<blockquote>**Silahkan balas ke media jika ingin mengatur pesan start media, atau ketik `/setimg off` untuk menon-aktifkan pesan media start.**</blockquote>"
            )


async def setads_bot(client, message):
    user = message.from_user if message.from_user else message.sender_chat
    if user.id not in DEVA:
        return
    if not message.reply_to_message:
        return await message.reply("**Silahkan balas ke teks**")
    proses = await message.reply("**Tunggu sebentar..**")
    reply = message.reply_to_message
    text = reply.text or reply.caption or ""
    await dB.set_var(client.me.id, "ads", text)
    return await proses.edit(
        f"**Pesan ads berhasil diatur ke: <a href='{reply.link}'>pesan ini</a>**"
    )


def _format_user_mention(user):
    """user = objek pyrogram.types.User asli (mis. message.from_user).
    Return RichTextTextMention supaya mention jadi link aktif, bukan teks HTML mentah."""
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    return RichTextBold(
        text=RichTextTextMention(
            text=full_name,
            user=user,
        )
    )


def _welcome_blocks(user_mention):
    return [
        paragraph([emo(5472164874886846699), RichTextBold(" Hi \n"), user_mention]),
        paragraph([
            emo(5328175963144466763, "🤖"),
            f" Saya adalah {BOT_NAME}, Userbot & Ai bot, "
            "Untuk fitur ai tambahkan saya dalam grup anda.",
        ]),
        divider(),
        details(
            [emo(5870692618244984670, "🤖"), " Klik fitur unggulan Userbot"],
            table(
                [
                    [cell(
                        [emo(5298711594140724699, "💎"), RichTextBold(" Ultra Premium")],
                        is_header=True,
                    )],
                    [cell([emo(6240210026477130678, "🎮"), " 78 Fitur"])],
                    [cell([emo(5298609030321691620, "✅"), " Anti Ucast"])],
                    [cell([emo(5220195537520711716, "✅"), " Afk effects"])],
                    [cell([emo(5796185041717433060, "✅"), " Fitur Ai Ready"])],
                    [cell([emo(5170574646478635764, "💰"), " Rp. 15.000,-"])],
                ],
            ),
        ),
        details(
            [emo(5870692618244984670, "🤖"), " Klik disini untuk penjelasan bot ini"],
            paragraph([
                emo(6269255258212404947, "🤖"),
                " Bot ini adalah asisten telegram cerdas atau userbot "
                "sekaligus bot ai percakapan untuk digrup, maupun dibot ini langsung ",
            ]),
        ),
        table(
            [
                [cell(["zanstore Core v3.14 ", emo(5456140674028019486, "⚡")], is_header=True, align="center")],
            ],
        ),
        divider(),
    ]


async def welcome_rich_table(
    client,
    message,
    reply_markup=None,
    effect_id=None,
    **_diabaikan,
):
    user_mention = _format_user_mention(message.from_user)
    blocks = _welcome_blocks(user_mention)
    is_admin = message.from_user.id in SUDO_OWNERS
    try:
        rich = InputRichMessage(blocks=blocks + [bubble_buttons(is_admin)])
        sent = await client.send_rich_message(
            chat_id=message.chat.id,
            rich_message=rich,
            reply_markup=reply_markup,
            effect_id=effect_id,
        )
        try:
            rm = getattr(sent, "rich_message", None)
            names = [type(b).__name__ for b in (getattr(rm, "blocks", None) or [])]
            logger.info(f"balik dari server: {names}")
        except Exception as er:
            logger.info(f"debug balik dari server gagal: {er}")
        return sent
    except Exception:
        err = traceback.format_exc()
        print(err)
        logger.error(f"Bubble button gagal, kirim tanpa bubble: {err}")
        rich = InputRichMessage(blocks=blocks)
        return await client.send_rich_message(
            chat_id=message.chat.id,
            rich_message=rich,
            reply_markup=reply_markup,
            effect_id=effect_id,
        )


async def start_home(client, message):
    if message.chat.type != enums.ChatType.PRIVATE:
        return

    user = message.from_user
    if user is None:
        return

    draft_id = client.rnd_id() or 1
    draft_ready = False
    thinking_html = (
        "<tg-thinking>"
        '<tg-emoji emoji-id="5258077393884562645">\U0001f4ad</tg-emoji>'
        " Thinking..."
        "</tg-thinking>"
    )

    try:
        try:
            await client.send_rich_message_draft(
                chat_id=message.chat.id,
                draft_id=draft_id,
                rich_message=InputRichMessage(html=thinking_html),
                can_stop=False,
            )
        except BadRequest:
            logger.warning(
                "start: thinking beremoji ditolak; memakai teks biasa",
                exc_info=True,
            )
            await client.send_rich_message_draft(
                chat_id=message.chat.id,
                draft_id=draft_id,
                rich_message=InputRichMessage(
                    html="<tg-thinking>Thinking...</tg-thinking>"
                ),
                can_stop=False,
            )

        draft_ready = True
        await asyncio.sleep(2.2)

    except Exception:
        logger.warning(
            "start: thinking gagal; menu tetap dilanjutkan",
            exc_info=True,
        )

    broadcast = await dB.get_list_from_var(client.me.id, "BROADCAST") or []
    if user.id not in broadcast:
        await dB.add_to_var(client.me.id, "BROADCAST", user.id)

    if user.id not in SUDO_OWNERS:
        try:
            await client.send_message(
                LOG_SELLER,
                f"<b>User: {user.mention}\n"
                f"ID: <code>{user.id}</code>\n"
                f"Name: {_esc(user.first_name or '')}\n"
                "Has started your bot.</b>",
            )
        except Exception:
            logger.warning(
                "start: gagal mengirim log pengguna",
                exc_info=True,
            )

    if draft_ready:
        full_name = " ".join(filter(None, (
            user.first_name, user.last_name,
        ))) or "User"
        greeting = (
            f"Hi {full_name}\n\n"
            f"Saya adalah {BOT_NAME}, Userbot & Ai bot, "
            "Untuk fitur ai tambahkan saya dalam grup anda."
        )

        step = 16
        for end in range(step, len(greeting) + step, step):
            preview = greeting[:end]
            html = "".join(
                f"<p>{_esc(part)}</p>"
                for part in preview.split("\n\n")
            )

            try:
                await client.send_rich_message_draft(
                    chat_id=message.chat.id,
                    draft_id=draft_id,
                    rich_message=InputRichMessage(html=html),
                    can_stop=False,
                )
            except Exception:
                logger.warning(
                    "start: animasi draft gagal; mengirim menu final",
                    exc_info=True,
                )
                break

            await asyncio.sleep(0.35)

    return await welcome_rich_table(
        client,
        message,
        effect_id=5104841245755180586,
    )


async def button_bot(client, message):
    link = message.text.split(None, 1)[1]
    tujuan, _id = Tools.extract_ids_from_link(link)
    txt = state.get(message.from_user.id, "edit_reply_markup")
    teks, button_kbd = ButtonUtils.parse_msg_buttons(txt)
    if button_kbd:
        button_kbd = await ButtonUtils.create_inline_keyboard(button_kbd)
    return await client.edit_message_reply_markup(
        chat_id=tujuan, message_id=_id, reply_markup=button_kbd
    )


async def getid_bot(client, message):
    if len(message.command) < 2:
        return
    query = message.text.split()[1]
    try:
        reply = message.reply_to_message
        media = Tools.get_file_id(reply)
        data = {"file_id": media["file_id"], "type": media["message_type"]}
        state.set(message.from_user.id, query, data)
        return
    except Exception as er:
        logger.error(f"{str(er)}")


async def request_bot(client, message):
    user_id = message.from_user.id
    if not message.reply_to_message:
        reply_text = (
            "<b>English:</b> Please use the /request command by replying to a text message or media with a caption. And explain the features you want in detail to make it easier for the admin."
            "<b>Indonesia:</b> Silahkan gunakan perintah /request dengan cara membalas pesan teks atau media dengan caption. Serta jelaskan fitur yang anda inginkan dengan detail agar memudahkan admin."
        )
        return await message.reply(reply_text)

    forward = await client.forward_messages(
        chat_id=LOG_SELLER,
        from_chat_id=message.chat.id,
        message_ids=message.reply_to_message.id,
    )
    await dB.set_var(forward.id, f"REQUEST_{forward.id}", user_id)
    return await message.reply(
        "<b>English:</b> Your report has been successfully submitted. Please wait for a response from the admin."
        "<b>Indonesia:</b> Laporan kamu berhasil dikirimkan. Silahkan tunggu jawaban dari admin."
    )


async def lapor_bug(client, message):
    if client.me.id != bot.id:
        return
    user_id = message.from_user.id
    if not message.reply_to_message:
        reply_text = (
            "<b>Cara Kirim:Kirim Screenshot Transaksi pembelian userbot dibot ini, Sertakan caption `Plan Basic/Pro` Lalu reply bukti dengan perintah /bukti.</b>"
        )
        return await message.reply(reply_text)
    forward = await client.forward_messages(
        chat_id=LOG_SELLER,
        from_chat_id=message.chat.id,
        message_ids=message.reply_to_message.id,
    )
    await dB.set_var(forward.id, f"BUG_{forward.id}", user_id)

    return await message.reply(
        "<b>✅ Bukti sukses dikirim ke admin, tunggu admin memberi akses userbot</b>."
    )


async def incoming_message(client, message):
    if message.chat.type != enums.ChatType.PRIVATE:
        return
    if message.sticker:
        return
    text = message.text or message.caption or ""
    if (
        text
        and text.startswith("/")
        or text in no_commands
        or not text.startswith("#bukti")
    ):
        return
    user_id = message.from_user.id
    forward = await client.forward_messages(
        chat_id=LOG_SELLER, from_chat_id=message.chat.id, message_ids=message.id
    )
    await dB.set_var(forward.id, f"FORWARD_{forward.id}", user_id)


async def outgoing_reply(client, message):
    rep = message.reply_to_message
    if not rep:
        return
    for prefix in ("REQUEST_", "BUG_", "FORWARD_"):
        user_id = await dB.get_var(rep.id, f"{prefix}{rep.id}")
        if user_id:
            return await client.copy_message(
                chat_id=user_id, from_chat_id=message.chat.id, message_id=message.id
            )