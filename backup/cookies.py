"""
/ask di bot (private & grup): jatah harian + token + blacklist grup.

File ini TERPISAH dari inline_command.py, jadi fungsi AI untuk pemakai userbot
tidak disentuh sama sekali.

Isi file (cari tanda "# ===" untuk lompat):
  1. PENGATURAN   angka, prompt AI, ID emoji
  2. TAMPILAN     semua layout respon bot (edit teks/emoji di sini saja)
  3. KUOTA        jatah harian + token (scope = chat.id)
  4. BLACKLIST    blokir user dari /ask di grup (khusus admin grup)
  5. /ask         logika tanya-jawab + tombol Lanjut / Stop
  6. TOKEN        /addtoken /deltoken /cektoken (owner bot)
  7. DISPATCH     satu pintu, dipanggil dari bot_handler

Scope token: chat.id. Di grup = token grup, di PM = token user.
"""
import asyncio
import inspect
import os
import re
import time
import traceback
from datetime import datetime

from pyrogram import enums
from pyrogram.enums import ButtonStyle
from pyrogram.helpers import (
    block_quote,
    cell,
    divider,
    ikb,
    paragraph,
    send_rich,
    table,
)
from pyrogram.types import (
    ReplyParameters,
    RichTextBold,
    RichTextCustomEmoji,
    RichTextTextMention,
)
from pytz import timezone

from config import API_BOTCHAX, SUDO_OWNERS
from database import dB
from helpers import Tools
from logs import logger


# ===========================================================================
# 1. PENGATURAN
# ===========================================================================
DAILY_LIMIT_PRIVATE = 30
DAILY_LIMIT_GROUP = 15
SESSION_TTL = 180     # mode ngobrol mati kalau user diam selama 3 menit
DELETE_AFTER = 120    # pesan bot dihapus otomatis setelah 2 menit
MAX_HISTORY = 12
QUOTE_MAX = 300       # panjang maksimal pertanyaan yang ditampilkan
LONG_ANSWER = 3500    # lebih panjang dari ini -> dikirim sebagai file

ASK_API_URL = "https://api.botcahx.eu.org/api/search/openai-custom-v2"
ASK_SYSTEM_PROMPT = (
    "Kamu adalah asisten paling canggih yang berbahasa Indonesia gaul, "
    "judes/jutek dan toxic banget, jawab singkat, padat, maximal 3-4 kalimat, "
    "jangan bertele-tele."
)

# Emoji premium
EMOJI_JAWABAN = "6334331674968458665"
EMOJI_TOKEN = "5330115548900501467"
EMOJI_SUKSES = "6253672854869511544"
EMOJI_GAGAL = "6253335038511811703"
EMOJI_CORE = "5456140674028019486"
EMOJI_STOP = "6334754651937703379"

BOT_CONVERSATIONS = {}   # (chat_id, user_id) -> riwayat chat
ASK_SESSIONS = {}        # (chat_id, user_id) -> waktu kedaluwarsa mode ngobrol
_HINTS = {}              # (chat_id, user_id) -> id pesan "mode ngobrol aktif"
_LOCKS = {}
_TASKS = set()


# ===========================================================================
# 2. TAMPILAN  (gaya start_command: satu fungsi = satu layout respon)
# ===========================================================================
def emo(emoji_id, alt=""):
    return RichTextCustomEmoji(custom_emoji_id=str(emoji_id), alternative_text=alt)


def mention(user):
    name = " ".join(filter(None, [user.first_name, user.last_name])) or "User"
    try:
        return RichTextTextMention(text=name, user=user)
    except Exception:
        return name


def _short(text, limit=QUOTE_MAX):
    text = text.strip()
    return text if len(text) <= limit else text[:limit] + "…"


try:
    from pyrogram.types import RichTextFixed   # teks mono
except ImportError:
    RichTextFixed = None

SPACER_TOKEN = 0   # paragraph kosong antara "Lagi ngobrol sama" dan Token (0 = rapat)


def mono(text):
    if RichTextFixed is None:
        return text
    try:
        return RichTextFixed(text)
    except Exception:
        return text


def _spacer(n):
    return [paragraph(["\u200b"]) for _ in range(n)]


# Mode blockquote jawaban:
#   "auto"   = baca signature block_quote di fork, pilih bentuk yang cocok
#   "blocks" = block_quote(paragraph([...]))   (isi = blok anak, seperti details())
#   "text"   = block_quote("teks polos")
#   "off"    = tanpa blockquote, jawaban tampil sebagai paragraf biasa
QUOTE_MODE = "auto"

try:
    _BQ_PARAMS = list(inspect.signature(block_quote).parameters)
except Exception:
    _BQ_PARAMS = []
logger.info(f"block_quote signature params: {_BQ_PARAMS}")


def _normalize(text):
    """Buang fence ``` dan pecah list yang menempel dalam satu baris."""
    text = re.sub(r"```\w*\n?", "", text)
    if "\n" not in text:
        text = re.sub(r"\s+(?=\d{1,2}\.\s)", "\n", text)
        text = re.sub(r"\s+-\s+(?=\*\*)", "\n- ", text)
    return text.strip()


def _plain(text):
    """Jawaban AI tanpa penanda markdown (untuk blockquote)."""
    return re.sub(r"\*\*(.+?)\*\*", r"\1", _normalize(text), flags=re.S)


def _md_parts(text):
    """Jawaban AI: **bold** jadi tebal (untuk tampilan tanpa blockquote)."""
    parts = []
    for i, chunk in enumerate(re.split(r"\*\*(.+?)\*\*", _normalize(text), flags=re.S)):
        if chunk:
            parts.append(RichTextBold(chunk) if i % 2 else chunk)
    return parts


def _quote(text):
    """Blockquote jawaban. Gagal / mode "off" -> paragraf biasa (jawaban tetap tampil)."""
    mode = QUOTE_MODE
    if mode == "auto":
        first = _BQ_PARAMS[0] if _BQ_PARAMS else ""
        mode = "text" if first in ("text", "content_text", "message") else "blocks"
    try:
        if mode == "blocks":
            return block_quote(paragraph(_md_parts(text)))
        if mode == "text":
            return block_quote(_plain(text))
    except Exception:
        logger.error(traceback.format_exc())
    return paragraph(_md_parts(text))


def _footer():
    return [
        divider(),
        table([[cell(["AliceDevs Core v3.14 ", emo(EMOJI_CORE, "⚡")],
                     is_header=True, align="center")]]),
    ]


def _buttons(user_id, active=False):
    stop = (" Stop", f"askbot_stop_{user_id}", ButtonStyle.DANGER, EMOJI_STOP)
    if active:
        return ikb([[stop]])
    lanjut = (" Lanjut Ngobrol", f"askbot_next_{user_id}",
              ButtonStyle.PRIMARY, EMOJI_JAWABAN)
    return ikb([[lanjut, stop]])


# --- layout respon ----------------------------------------------------------
def blocks_jawaban(prompt, result, user, info):
    # catatan: "\n" di dalam paragraph tidak jadi baris baru -> satu baris = satu paragraph
    return [
        paragraph([RichTextBold("Pertanyaan:")]),
        paragraph([mono(_short(prompt))]),
        paragraph([emo(EMOJI_JAWABAN, "✨"), RichTextBold(" Jawaban:")]),
        _quote(result),
        paragraph(["Lagi ngobrol sama: ", mention(user)]),
        *_spacer(SPACER_TOKEN),
        paragraph([f"{info} ", emo(EMOJI_TOKEN, "🪙")]),
    ]


def blocks_info(emoji_id, alt, judul, isi=""):
    """Layout umum: [emoji] **Judul** + isi (tiap baris = satu paragraph)."""
    blocks = [paragraph([emo(emoji_id, alt), RichTextBold(f" {judul}")])]
    blocks += [paragraph([line]) for line in isi.split("\n") if line]
    return blocks


def blocks_habis(limit, group, chat_id):
    extra = (
        f"Beli token ke owner bot untuk grup ini.\nID grup: {chat_id}"
        if group
        else "Beli token ke owner bot kalau mau lanjut sekarang."
    )
    return blocks_info(
        EMOJI_GAGAL, "🚫", f"Token /ask hari ini habis ({limit}/{limit}).",
        f"Token reset tiap jam 00:00 WIB.\n{extra}",
    )


def blocks_error():
    return blocks_info(
        EMOJI_GAGAL, "⚠️", "Ai lagi error.", "Token tidak dipotong, coba lagi nanti."
    )


def blocks_diblokir():
    return blocks_info(
        EMOJI_GAGAL, "🚫", "Maaf, kamu tidak bisa menggunakan fitur ini.",
        "Mungkin kamu diblokir. Hubungi admin grup untuk membebaskannya.",
    )


def blocks_cara_pakai(isi):
    return blocks_info(EMOJI_GAGAL, "❓", "Cara pakai:", isi)


def blocks_mode_aktif(user, cara):
    return [
        paragraph([emo(EMOJI_SUKSES, "💬"), RichTextBold(" Mode ngobrol aktif "),
                   mention(user)]),
        paragraph([cara]),
        paragraph([f"Berhenti otomatis setelah {SESSION_TTL // 60} menit tanpa balasan."]),
    ]


def blocks_blacklist(judul, user):
    return [paragraph([emo(EMOJI_SUKSES, "✅"), RichTextBold(f" {judul} "), mention(user)])]


# --- kirim ------------------------------------------------------------------
def _delete_later(client, chat_id, msg, delay=DELETE_AFTER):
    mid = getattr(msg, "id", None)
    if not mid:
        return

    async def _run():
        await asyncio.sleep(delay)
        try:
            await client.delete_messages(chat_id, mid)
        except Exception:
            pass

    task = asyncio.create_task(_run())
    _TASKS.add(task)
    task.add_done_callback(_TASKS.discard)


async def _kirim(client, chat_id, blocks, reply_to=None, markup=None, delete=True):
    """Kirim rich message + footer tabel, hapus otomatis."""
    params = ReplyParameters(message_id=reply_to) if reply_to else None
    msg = await send_rich(
        client, chat_id, *blocks, *_footer(),
        reply_markup=markup, reply_parameters=params,
    )
    if delete:
        _delete_later(client, chat_id, msg)
    return msg


# ===========================================================================
# 3. KUOTA
# ===========================================================================
def _today():
    return datetime.now(timezone("Asia/Jakarta")).strftime("%Y-%m-%d")


def _is_group(chat):
    return chat.type in (enums.ChatType.GROUP, enums.ChatType.SUPERGROUP)


def _limit(is_group):
    return DAILY_LIMIT_GROUP if is_group else DAILY_LIMIT_PRIVATE


async def _load(scope):
    data = await dB.get_var(scope, "ASK_QUOTA") or {}
    if data.get("date") != _today():
        data["date"] = _today()
        data["used"] = 0
    data.setdefault("used", 0)
    data.setdefault("tokens", 0)
    return data


async def _save(scope, data):
    await dB.set_var(scope, "ASK_QUOTA", data)


async def _consume(scope, is_group):
    """Potong jatah gratis dulu, lalu token. Return (bucket, data)."""
    data = await _load(scope)
    if data["used"] < _limit(is_group):
        data["used"] += 1
        bucket = "free"
    elif data["tokens"] > 0:
        data["tokens"] -= 1
        bucket = "token"
    else:
        return None, data
    await _save(scope, data)
    return bucket, data


async def _refund(scope, bucket):
    if bucket not in ("free", "token"):
        return
    data = await _load(scope)
    if bucket == "free":
        data["used"] = max(0, data["used"] - 1)
    else:
        data["tokens"] += 1
    await _save(scope, data)


def _info_text(data, is_group, owner=False):
    if owner:
        return "Token: Unlimited"
    limit = _limit(is_group)
    return f"Free Token: {max(0, limit - data['used'])}/{limit} • Token: {data['tokens']}"


# ===========================================================================
# 4. BLACKLIST (khusus admin grup)
# ===========================================================================
async def _bl_load(chat_id):
    return await dB.get_var(chat_id, "ASK_BLACKLIST") or []


async def is_blacklisted(chat_id, user_id):
    """Bisa dipakai juga di fitur bot lain: if await is_blacklisted(chat.id, user.id)."""
    return user_id in await _bl_load(chat_id)


async def _is_admin(client, chat_id, user_id):
    if user_id in SUDO_OWNERS:
        return True
    try:
        member = await client.get_chat_member(chat_id, user_id)
        return member.status in (
            enums.ChatMemberStatus.OWNER,
            enums.ChatMemberStatus.ADMINISTRATOR,
        )
    except Exception:
        return False


async def _bl_guard(client, message):
    """True kalau pengirim boleh pakai perintah blacklist."""
    chat = message.chat
    if not _is_group(chat):
        await _kirim(client, chat.id,
                     blocks_info(EMOJI_GAGAL, "🚫", "Fitur ini hanya untuk grup."),
                     reply_to=message.id)
        return False
    if not await _is_admin(client, chat.id, message.from_user.id):
        await _kirim(client, chat.id,
                     blocks_info(EMOJI_GAGAL, "🚫", "Khusus admin grup."),
                     reply_to=message.id)
        return False
    return True


async def _bl_target(client, message):
    """Target dari balasan pesan, atau argumen id / @username."""
    rep = message.reply_to_message
    if rep and rep.from_user:
        return rep.from_user
    args = message.text.split()[1:]
    if not args:
        return None
    try:
        arg = args[0]
        return await client.get_users(int(arg) if arg.lstrip("-").isdigit() else arg)
    except Exception:
        return None


async def blacklist_cmd(client, message):
    if not await _bl_guard(client, message):
        return
    chat = message.chat
    user = await _bl_target(client, message)
    if not user:
        return await _kirim(
            client, chat.id,
            blocks_cara_pakai("Balas pesan user lalu ketik /blacklist\natau /blacklist id|@username"),
            reply_to=message.id,
        )
    if user.is_bot or user.id == message.from_user.id or await _is_admin(client, chat.id, user.id):
        return await _kirim(
            client, chat.id,
            blocks_info(EMOJI_GAGAL, "🚫", "Admin, bot, dan dirimu sendiri tidak bisa diblacklist."),
            reply_to=message.id,
        )
    ids = await _bl_load(chat.id)
    if user.id not in ids:
        ids.append(user.id)
        await dB.set_var(chat.id, "ASK_BLACKLIST", ids)
    _end_session((chat.id, user.id))
    await _kirim(client, chat.id, blocks_blacklist("Diblacklist:", user), reply_to=message.id)


async def unblacklist_cmd(client, message):
    if not await _bl_guard(client, message):
        return
    chat = message.chat
    user = await _bl_target(client, message)
    if not user:
        return await _kirim(
            client, chat.id,
            blocks_cara_pakai("Balas pesan user lalu ketik /unblacklist\natau /unblacklist id|@username"),
            reply_to=message.id,
        )
    ids = await _bl_load(chat.id)
    if user.id in ids:
        ids.remove(user.id)
        await dB.set_var(chat.id, "ASK_BLACKLIST", ids)
    await _kirim(client, chat.id, blocks_blacklist("Dibebaskan:", user), reply_to=message.id)


async def listblacklist_cmd(client, message):
    if not await _bl_guard(client, message):
        return
    ids = await _bl_load(message.chat.id)
    isi = "\n".join(f"• {uid}" for uid in ids) if ids else "Kosong."
    await _kirim(
        client, message.chat.id,
        blocks_info(EMOJI_TOKEN, "📋", f"Blacklist /ask ({len(ids)})", isi),
        reply_to=message.id,
    )


# ===========================================================================
# 5. /ask
# ===========================================================================
def _trim(conv):
    if len(conv) > MAX_HISTORY + 1:
        conv[:] = conv[:1] + conv[-MAX_HISTORY:]


def _end_session(key):
    ASK_SESSIONS.pop(key, None)
    BOT_CONVERSATIONS.pop(key, None)


async def _call_ai(conv):
    try:
        r = await Tools.fetch.post(
            ASK_API_URL, json={"message": conv, "apikey": API_BOTCHAX}
        )
        if r.status_code == 200:
            return r.json().get("result")
    except Exception:
        logger.error(traceback.format_exc())
    return None


async def _send_long(client, message, result, info, markup):
    path = f"ask_{message.chat.id}_{message.id}.txt"
    with open(path, "wb") as f:
        f.write(result.encode("utf-8"))
    try:
        sent = await client.send_document(
            message.chat.id, path,
            caption=f"✨ Jawaban terlalu panjang, dikirim sebagai file.\n{info}\n✅ AliceDevs Core v3.14",
            reply_markup=markup,
            reply_to_message_id=message.id,
        )
        _delete_later(client, message.chat.id, sent)
        return sent
    finally:
        if os.path.exists(path):
            os.remove(path)


async def _ask(client, message, prompt, active=False):
    user, chat = message.from_user, message.chat
    group = _is_group(chat)
    key = (chat.id, user.id)
    owner = user.id in SUDO_OWNERS

    async with _LOCKS.setdefault(key, asyncio.Lock()):
        # 1. potong jatah / token (owner bebas)
        bucket, data = None, {"used": 0, "tokens": 0}
        if not owner:
            bucket, data = await _consume(chat.id, group)
            if bucket is None:
                return await _kirim(client, chat.id,
                                    blocks_habis(_limit(group), group, chat.id),
                                    reply_to=message.id)

        # 2. riwayat percakapan
        if key not in BOT_CONVERSATIONS and len(BOT_CONVERSATIONS) > 500:
            BOT_CONVERSATIONS.pop(next(iter(BOT_CONVERSATIONS)))
        conv = BOT_CONVERSATIONS.setdefault(
            key, [{"role": "system", "content": ASK_SYSTEM_PROMPT}]
        )
        conv.append({"role": "user", "content": prompt})

        try:
            await client.send_chat_action(chat.id, enums.ChatAction.TYPING)
        except Exception:
            pass

        # 3. tanya AI (gagal -> token dikembalikan)
        result = await _call_ai(conv)
        if not result:
            conv.pop()
            await _refund(chat.id, bucket)
            return await _kirim(client, chat.id, blocks_error(), reply_to=message.id)

        result = str(result)
        conv.append({"role": "assistant", "content": result})
        _trim(conv)

        # 4. kirim jawaban
        markup = _buttons(user.id, active=active)
        info = _info_text(data, group, owner)
        if len(result) > LONG_ANSWER:
            return await _send_long(client, message, result, info, markup)
        return await _kirim(
            client, chat.id, blocks_jawaban(prompt, result, user, info),
            reply_to=message.id, markup=markup,
        )


async def ask_command(client, message):
    chat, user = message.chat, message.from_user
    if _is_group(chat) and await is_blacklisted(chat.id, user.id):
        return await _kirim(client, chat.id, blocks_diblokir(), reply_to=message.id)

    parts = (message.text or "").split(None, 1)
    prompt = parts[1].strip() if len(parts) > 1 else ""
    if not prompt and message.reply_to_message:
        rep = message.reply_to_message
        prompt = (rep.text or rep.caption or "").strip()
    if not prompt:
        return await _kirim(
            client, chat.id,
            blocks_cara_pakai("/ask gw jelek ga?\nAtau balas sebuah pesan lalu ketik /ask."),
            reply_to=message.id,
        )
    return await _ask(client, message, prompt)


async def ask_followup(client, message):
    """Teks biasa saat mode ngobrol aktif. Return True kalau dipakai."""
    if not message.text or message.text.startswith("/") or not message.from_user:
        return False
    chat, user = message.chat, message.from_user
    key = (chat.id, user.id)
    expires = ASK_SESSIONS.get(key)
    if not expires:
        return False
    if expires < time.time():
        _end_session(key)
        return False
    if _is_group(chat):
        rep = message.reply_to_message
        if not (rep and rep.from_user and rep.from_user.id == client.me.id):
            return False
        if await is_blacklisted(chat.id, user.id):
            _end_session(key)
            return False
    ASK_SESSIONS[key] = time.time() + SESSION_TTL
    await _ask(client, message, message.text, active=True)
    return True


async def ask_callback(client, callback):
    """Tombol Lanjut Ngobrol / Stop."""
    try:
        _, action, owner_id = callback.data.split("_", 2)
        owner_id = int(owner_id)
    except Exception:
        return await callback.answer("Tombol tidak valid", show_alert=True)

    if callback.from_user.id != owner_id:
        return await callback.answer("Ini bukan percakapanmu.", show_alert=True)

    msg = callback.message
    chat = msg.chat
    key = (chat.id, owner_id)

    if action == "stop":
        _end_session(key)
        await callback.answer("Percakapan diakhiri.")
        for mid in (msg.id, _HINTS.pop(key, None)):
            if mid:
                try:
                    await client.delete_messages(chat.id, mid)
                except Exception:
                    pass
        return

    if action == "next":
        if _is_group(chat) and await is_blacklisted(chat.id, owner_id):
            return await callback.answer(
                "Kamu diblokir dari fitur ini. Hubungi admin grup.", show_alert=True
            )
        ASK_SESSIONS[key] = time.time() + SESSION_TTL
        await callback.answer("Mode ngobrol aktif ✅")
        try:
            await msg.edit_reply_markup(_buttons(owner_id, active=True))
        except Exception:
            pass
        cara = (
            "Balas salah satu pesan bot ini dengan pertanyaanmu."
            if _is_group(chat)
            else "Ketik pesanmu langsung di sini."
        )
        hint = await _kirim(client, chat.id,
                            blocks_mode_aktif(callback.from_user, cara),
                            reply_to=msg.id)
        _HINTS[key] = getattr(hint, "id", None)
        return

    return await callback.answer("Tombol tidak dikenal", show_alert=True)


# ===========================================================================
# 6. TOKEN (owner bot)
# ===========================================================================
def _target(message, args, idx):
    """id_chat opsional; kalau kosong = chat ini (grup / PM)."""
    return int(args[idx]) if len(args) > idx else message.chat.id


async def addtoken_cmd(client, message):
    if message.from_user.id not in SUDO_OWNERS:
        return
    args = message.text.split()[1:]
    try:
        jumlah = int(args[0])
        target = _target(message, args, 1)
        if jumlah <= 0:
            raise ValueError
    except Exception:
        return await _kirim(
            client, message.chat.id,
            blocks_cara_pakai("/addtoken jumlah [id_chat]\nTanpa id_chat = chat/grup ini."),
            reply_to=message.id,
        )

    data = await _load(target)
    data["tokens"] += jumlah
    await _save(target, data)

    await _kirim(
        client, message.chat.id,
        blocks_info(EMOJI_SUKSES, "✅", f"+{jumlah} token untuk {target}.",
                    f"Total token: {data['tokens']}"),
        reply_to=message.id,
    )
    if target != message.chat.id:
        try:
            await _kirim(
                client, target,
                blocks_info(EMOJI_SUKSES, "✅", f"Chat ini mendapat +{jumlah} token /ask.",
                            f"Total token: {data['tokens']}"),
            )
        except Exception:
            pass


async def deltoken_cmd(client, message):
    if message.from_user.id not in SUDO_OWNERS:
        return
    args = message.text.split()[1:]
    try:
        semua = args[0].lower() == "all"
        jumlah = 0 if semua else int(args[0])
        target = _target(message, args, 1)
        if not semua and jumlah <= 0:
            raise ValueError
    except Exception:
        return await _kirim(
            client, message.chat.id,
            blocks_cara_pakai("/deltoken jumlah|all [id_chat]"),
            reply_to=message.id,
        )

    data = await _load(target)
    data["tokens"] = 0 if semua else max(0, data["tokens"] - jumlah)
    await _save(target, data)
    await _kirim(
        client, message.chat.id,
        blocks_info(EMOJI_SUKSES, "✅", f"Token {target} sekarang: {data['tokens']}"),
        reply_to=message.id,
    )


async def cektoken_cmd(client, message):
    target = message.chat.id
    args = message.text.split()[1:]
    if args and message.from_user.id in SUDO_OWNERS:
        try:
            target = int(args[0])
        except ValueError:
            pass

    group = target < 0
    data = await _load(target)
    limit = _limit(group)
    judul = f"Token {'grup' if group else 'user'}: {target}"
    await _kirim(
        client, message.chat.id,
        blocks_info(
            EMOJI_TOKEN, "📊", judul,
            f"• Gratis hari ini: {max(0, limit - data['used'])}/{limit}\n"
            f"• Token: {data['tokens']}",
        ),
        reply_to=message.id,
    )


# ===========================================================================
# 7. DISPATCH (panggil dari bot_handler)
# ===========================================================================
_COMMANDS = {
    "ask": ask_command,
    "addtoken": addtoken_cmd,
    "deltoken": deltoken_cmd,
    "cektoken": cektoken_cmd,
    "blacklist": blacklist_cmd,
    "unblacklist": unblacklist_cmd,
    "listblacklist": listblacklist_cmd,
}


async def ask_dispatch(client, message):
    if not message.from_user:
        return False
    text = message.text or ""
    if text.startswith("/"):
        head = text.split(None, 1)[0][1:]
        name, _, uname = head.partition("@")
        if uname and uname.lower() != (client.me.username or "").lower():
            return False
        fn = _COMMANDS.get(name.lower())
        if not fn:
            return False
        await fn(client, message)
        return True
    return await ask_followup(client, message)
