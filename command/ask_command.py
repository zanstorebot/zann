"""
/ask di bot (private & grup): mode karakter AI, jatah harian + token,
blacklist grup, dan ringkasan obrolan grup (Alice Daily).

File ini TERPISAH dari inline_command.py, jadi fungsi AI untuk pemakai userbot
tidak disentuh sama sekali.

Isi file (cari tanda "# ===" untuk lompat):
  1. PENGATURAN   angka, ID emoji, MODE karakter AI
  2. TAMPILAN     semua layout respon bot (edit teks/emoji di sini saja)
  3. KUOTA        jatah harian + token (scope = chat.id)
  4. BLACKLIST    blokir user dari /ask di grup (khusus admin grup)
  5. /ask         pilih mode -> tanya-jawab + tombol Lanjut / Stop
  6. TOKEN        /addtoken /deltoken /cektoken (owner bot)
  7. DISPATCH     satu pintu, dipanggil dari bot_handler
  8. DAILY        ringkasan obrolan grup berkala + tag username

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
from pyrogram.errors import BadRequest
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
    InputRichMessage,
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
DAILY_LIMIT_GROUP = 25
SESSION_TTL = 180     # mode ngobrol mati kalau user diam selama 3 menit
GROUP_FOLLOWUP = True   # True = di grup, reply ke pesan jawaban bot dijawab AI saat mode ngobrol aktif
DELETE_AFTER = 300    # pesan bot dihapus otomatis setelah 5 menit
MAX_HISTORY = 12
QUOTE_MAX = 300       # panjang maksimal pertanyaan yang ditampilkan
LONG_ANSWER = 3500    # lebih panjang dari ini -> dikirim sebagai file

ASK_API_URL = "https://api.botcahx.eu.org/api/search/openai-custom-v2"
DEFAULT_MODE = "jutek"
PICK_TTL = DELETE_AFTER    # pilihan mode kedaluwarsa (detik) kalau tidak diklik
REFUSE_TAG = "[GAMAU]"     # AI membuka jawabannya dengan tag ini kalau tidak sesuai mode

# aturan yang ditempel ke semua prompt mode
_RULE = (
    " ATURAN MODE: kalau pesan user TIDAK sesuai mode ini, jangan dijawab. "
    f"Balas diawali tepat {REFUSE_TAG} lalu SATU kalimat penolakan singkat "
    "dengan gaya mode ini, dan sarankan pakai mode lain."
)

# Emoji premium
EMOJI_JAWABAN = "6334331674968458665"
EMOJI_TOKEN = "5330115548900501467"
EMOJI_SUKSES = "6253672854869511544"
EMOJI_GAGAL = "6253335038511811703"
EMOJI_CORE = "5456140674028019486"
EMOJI_STOP = "6334754651937703379"
EMOJI_JUTEK = "5775954354183868805"
EMOJI_CERDAS = "6163356019121460519"
EMOJI_CURHAT = "5778663434870592039"
EMOJI_USER = "6255904322308017507"
EMOJI_TANYA = "6253333475143715943"
EMOJI_PAKAI = "5870692618244984670"
EMOJI_LAMP = "5328175963144466763"

# ---------------------------------------------------------------------------
# MODE KARAKTER AI. Mau tambah mode? Cukup tambah satu entri di sini:
# tombol, daftar mode di pesan pilihan, dan prompt AI ikut otomatis.
# emoji = salah satu ID emoji premium di atas (ganti kapan saja)
# ---------------------------------------------------------------------------
MODES = {
    "jutek": {
        "label": "Mode Jutek",
        "name": "Jutek",
        "emoji": EMOJI_JUTEK,
        "desc": "receh, bercanda, ngeledek. [Respon Jutek]",
        "prompt": (
            "Kamu AI berbahasa Indonesia gaul, judes/jutek dan toxic banget, "
            "jawab singkat padat maksimal 3-4 kalimat. Mode ini HANYA untuk ngobrol "
            "santai, receh, bercanda, dan ngeledek. Tolak kalau user minta hal serius: "
            "tutorial/teknis panjang, tugas, pengetahuan mendalam, atau curhat serius."
            + _RULE
        ),
    },
    "cerdas": {
        "label": "Mode Cerdas",
        "name": "Cerdas",
        "emoji": EMOJI_CERDAS,
        "desc": "tanya jawab, penjelasan, tutorial, belajar, coding",
        "prompt": (
            "Kamu asisten cerdas berbahasa Indonesia yang ramah, jelas, dan akurat. "
            "Mode ini HANYA untuk tanya jawab pengetahuan, penjelasan, tutorial, coding, "
            "dan belajar. Jawab ringkas dan terstruktur, maksimal 6 kalimat kecuali "
            "memang butuh langkah-langkah. Tolak kalau user curhat/cerita perasaan "
            "atau cuma basa-basi dan ngeledek."
            + _RULE
        ),
    },
    "curhat": {
        "label": "Mode Curhat",
        "name": "Curhat",
        "emoji": EMOJI_CURHAT,
        "desc": "curhat, cerita, masalah perasaan, cinta",
        "prompt": (
            "Kamu pendengar yang hangat dan empatik, berbahasa Indonesia santai. "
            "Mode ini HANYA untuk curhat, cerita, dan masalah perasaan. Validasi perasaan "
            "user, boleh tanya balik dengan lembut, beri saran ringan, maksimal 4 kalimat. "
            "Kalau ada tanda user ingin menyakiti diri sendiri, tanggapi dengan peduli "
            "dan sarankan menghubungi orang terdekat atau layanan darurat. "
            "Tolak kalau user minta info/pengetahuan teknis, tutorial, kode, atau ngeledek."
            + _RULE
        ),
    },
}

BOT_CONVERSATIONS = {}   # (chat_id, user_id) -> riwayat chat
ASK_SESSIONS = {}        # (chat_id, user_id) -> waktu kedaluwarsa mode ngobrol
ASK_MODES = {}           # (chat_id, user_id) -> mode yang sedang dipakai
PENDING = {}             # (chat_id, user_id) -> pertanyaan yang menunggu pilih mode
DAILY_MSG_IDS = {}       # chat_id -> set id pesan daily (reply ke sini tidak dijawab AI)
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


def _fmt_interval(seconds):
    """Durasi otomatis: < 1 menit = detik, < 1 jam = menit, selebihnya jam.
    15 -> '15 detik', 90 -> '1 menit 30 detik', 300 -> '5 menit', 3600 -> '1 jam'."""
    sec = int(seconds)
    if sec < 60:
        return f"{sec} detik"
    if sec < 3600:
        menit, sisa = divmod(sec, 60)
        return f"{menit} menit" + (f" {sisa} detik" if sisa else "")
    jam, sisa = divmod(sec, 3600)
    menit = sisa // 60
    return f"{jam} jam" + (f" {menit} menit" if menit else "")


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
        table([[cell(
            [
                emo(EMOJI_LAMP, "💎"),
                RichTextBold(" AliceDevs Core & ALICE-Ai [v3.9] "),
                emo(EMOJI_CORE, "⚡"),
            ],
            is_header=True,
            align="center",
        )]]),
    ]


def _buttons(user_id, active=False, group=False):
    stop = (" Stop", f"askbot_stop_{user_id}", ButtonStyle.DANGER, EMOJI_STOP)
    if active or (group and not GROUP_FOLLOWUP):
        return ikb([[stop]])
    lanjut = (" Lanjut Ngobrol", f"askbot_next_{user_id}",
              ButtonStyle.PRIMARY, EMOJI_JAWABAN)
    return ikb([[lanjut, stop]])


def _mode_buttons(user_id):
    """Tombol tiap mode + Batal, 2 per baris. callback: askbot_pick_<uid>_<mode>."""
    items = [
        (f" {m['label']}", f"askbot_pick_{user_id}_{key}", ButtonStyle.PRIMARY, m["emoji"])
        for key, m in MODES.items()
    ]
    items.append((" Batal", f"askbot_cancel_{user_id}", ButtonStyle.DANGER, EMOJI_STOP))
    return ikb([items[i:i + 2] for i in range(0, len(items), 2)])


# --- layout respon ----------------------------------------------------------
def blocks_pilih_mode(prompt):
    blocks = [
        paragraph([emo(EMOJI_JAWABAN, "✨"), RichTextBold(" Pilih mode dulu")]),
        paragraph([emo(EMOJI_TANYA, "💎"), RichTextBold(" Pertanyaanmu:")]),
        paragraph([mono(_short(prompt, 120))]),
    ]
    for m in MODES.values():
        blocks.append(paragraph([RichTextBold(f"{m['label']}: "), m["desc"]]))
    return blocks


def blocks_jawaban(prompt, result, user, info, mode=DEFAULT_MODE):
    # catatan: "\n" di dalam paragraph tidak jadi baris baru -> satu baris = satu paragraph
    return [
        paragraph([RichTextBold("Pertanyaan:")]),
        paragraph([mono(_short(prompt))]),
        paragraph([emo(EMOJI_JAWABAN, "✨"),
                   RichTextBold(f" Jawaban Mode ({MODES[mode]['name']}):")]),
        _quote(result),
        paragraph([emo(EMOJI_USER, "💎"), " Lagi ngobrol sama: ", mention(user)]),
        *_spacer(SPACER_TOKEN),
        paragraph([emo(EMOJI_TOKEN, "🪙"), f" {info}"]),
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
    return blocks_info(EMOJI_PAKAI, "❓", "Cara pakai:", isi)


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


async def _kirim(client, chat_id, blocks, reply_to=None, markup=None, delete=True,
                 footer=True):
    """Kirim rich message (+ footer tabel kalau footer=True), hapus otomatis."""
    params = ReplyParameters(message_id=reply_to) if reply_to else None
    msg = await send_rich(
        client, chat_id, *blocks, *(_footer() if footer else []),
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
            blocks_cara_pakai("Balas pesan user lalu ketik /bl\natau /bl id|@username"),
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
            blocks_cara_pakai("Balas pesan user lalu ketik /unbl\natau /unbl id|@username"),
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
    ASK_MODES.pop(key, None)
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
            caption=f"✨ Jawaban terlalu panjang, dikirim sebagai file.\n{info}\n✅ AliceDevs Core & ALICE-Ai [v3.9]",
            reply_markup=markup,
            reply_to_message_id=message.id,
        )
        _delete_later(client, message.chat.id, sent)
        return sent
    finally:
        if os.path.exists(path):
            os.remove(path)


async def _call_ai_with_thinking(client, message, conv):
    chat = message.chat
    loading = None
    refresher = None
    draft_id = client.rnd_id() or 1
    plain_html = "<tg-thinking>Thinking...</tg-thinking>"
    emoji_html = (
        "<tg-thinking>"
        '<tg-emoji emoji-id="5258077393884562645">\U0001f4ad</tg-emoji>'
        " Thinking...</tg-thinking>"
    )

    async def send_draft(html):
        await client.send_rich_message_draft(
            chat_id=chat.id,
            draft_id=draft_id,
            rich_message=InputRichMessage(html=html),
            can_stop=False,
        )

    async def refresh_draft(html):
        while True:
            await asyncio.sleep(3)
            try:
                await send_draft(html)
            except Exception:
                logger.warning(
                    "ask: refresh thinking gagal",
                    exc_info=True,
                )
                return

    try:
        try:
            if chat.type == enums.ChatType.PRIVATE:
                html = emoji_html
                try:
                    await send_draft(html)
                except BadRequest:
                    html = plain_html
                    await send_draft(html)

                refresher = asyncio.create_task(refresh_draft(html))
                _TASKS.add(refresher)
                refresher.add_done_callback(_TASKS.discard)

            else:
                try:
                    loading = await _kirim(
                        client, chat.id,
                        [paragraph([
                            emo("5258077393884562645", "\U0001f4ad"),
                            RichTextBold(" Thinking..."),
                        ])],
                        reply_to=message.id,
                        delete=False,
                        footer=False,
                    )
                except BadRequest:
                    loading = await client.send_message(
                        chat.id,
                        "Thinking...",
                        reply_to_message_id=message.id,
                    )

        except Exception:
            logger.warning(
                "ask: thinking gagal; tetap memanggil AI",
                exc_info=True,
            )

        return await _call_ai(conv)

    finally:
        if refresher is not None:
            refresher.cancel()
            try:
                await refresher
            except asyncio.CancelledError:
                pass

        if loading is not None:
            await _del(client, chat.id, loading.id)

async def _ask(client, message, prompt, mode=DEFAULT_MODE, active=False):
    mode = mode if mode in MODES else DEFAULT_MODE
    user, chat = message.from_user, message.chat
    group = _is_group(chat)
    key = (chat.id, user.id)
    owner = user.id in SUDO_OWNERS

    async with _LOCKS.setdefault(key, asyncio.Lock()):
        bucket, data = None, {"used": 0, "tokens": 0}

        if not owner:
            bucket, data = await _consume(chat.id, group)
            if bucket is None:
                return await _kirim(
                    client, chat.id,
                    blocks_habis(_limit(group), group, chat.id),
                    reply_to=message.id,
                )

        if ASK_MODES.get(key) != mode:
            BOT_CONVERSATIONS.pop(key, None)
            ASK_MODES[key] = mode

        if key not in BOT_CONVERSATIONS and len(BOT_CONVERSATIONS) > 500:
            BOT_CONVERSATIONS.pop(next(iter(BOT_CONVERSATIONS)))

        conv = BOT_CONVERSATIONS.setdefault(
            key, [{"role": "system", "content": MODES[mode]["prompt"]}],
        )
        conv.append({"role": "user", "content": prompt})

        try:
            await client.send_chat_action(chat.id, enums.ChatAction.TYPING)
        except Exception:
            pass

        result = await _call_ai_with_thinking(client, message, conv)

        if not result:
            conv.pop()
            await _refund(chat.id, bucket)
            return await _kirim(
                client, chat.id, blocks_error(),
                reply_to=message.id,
            )

        result = str(result).strip()

        if result.upper().startswith(REFUSE_TAG):
            result = (
                result[len(REFUSE_TAG):].strip()
                or "Pertanyaan ini tidak sesuai mode."
            )
            result += " Ketik /ask lagi untuk ganti mode."
            conv.pop()
            await _refund(chat.id, bucket)

            if not owner:
                data = await _load(chat.id)
        else:
            conv.append({"role": "assistant", "content": result})
            _trim(conv)

        markup = _buttons(user.id, active=active, group=group)
        info = _info_text(data, group, owner)

        if len(result) > LONG_ANSWER:
            return await _send_long(client, message, result, info, markup)

        return await _kirim(
            client, chat.id,
            blocks_jawaban(prompt, result, user, info, mode),
            reply_to=message.id,
            markup=markup,
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
    # simpan pertanyaan, user pilih mode dulu (lanjut di ask_callback -> _pick_mode)
    if len(PENDING) > 200:
        PENDING.pop(next(iter(PENDING)))
    PENDING[(chat.id, user.id)] = {"message": message, "prompt": prompt, "ts": time.time()}
    return await _kirim(
        client, chat.id, blocks_pilih_mode(prompt),
        reply_to=message.id, markup=_mode_buttons(user.id),
    )


async def ask_followup(client, message):
    """Teks biasa saat mode ngobrol aktif. Return True kalau dipakai."""
    if not message.text or message.text.startswith("/") or not message.from_user:
        return False
    chat, user = message.chat, message.from_user
    if _is_group(chat) and not GROUP_FOLLOWUP:
        return False        # grup: reply ke bot tidak dijawab AI, ngobrol pakai /ask
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
        if rep.id in DAILY_MSG_IDS.get(chat.id, ()):    # reply ke pesan daily: tidak dijawab AI
            return False
        if await is_blacklisted(chat.id, user.id):
            _end_session(key)
            return False
    ASK_SESSIONS[key] = time.time() + SESSION_TTL
    await _ask(client, message, message.text, ASK_MODES.get(key, DEFAULT_MODE), active=True)
    return True


async def _del(client, chat_id, message_id):
    try:
        await client.delete_messages(chat_id, message_id)
    except Exception:
        pass


async def _pick_mode(client, callback, owner_id, mode):
    """User klik salah satu tombol mode -> jalankan pertanyaan yang tertunda."""
    msg = callback.message
    chat = msg.chat
    pending = PENDING.pop((chat.id, owner_id), None)

    if mode not in MODES or not pending or time.time() - pending["ts"] > PICK_TTL:
        await callback.answer("Pilihan kedaluwarsa, ketik /ask lagi.", show_alert=True)
        return await _del(client, chat.id, msg.id)
    if _is_group(chat) and await is_blacklisted(chat.id, owner_id):
        await callback.answer("Kamu diblokir dari fitur ini. Hubungi admin grup.",
                              show_alert=True)
        return await _del(client, chat.id, msg.id)

    await callback.answer(f"{MODES[mode]['label']} dipilih ✅")
    await _del(client, chat.id, msg.id)
    await _ask(client, pending["message"], pending["prompt"], mode)


async def ask_callback(client, callback):
    """Tombol pilih mode / Batal / Lanjut Ngobrol / Stop.
    Format callback: askbot_<aksi>_<user_id>[_<mode>]"""
    try:
        parts = callback.data.split("_")
        action, owner_id = parts[1], int(parts[2])
        extra = parts[3] if len(parts) > 3 else ""
    except Exception:
        return await callback.answer("Tombol tidak valid", show_alert=True)

    # tombol Alice Daily: boleh ditekan admin grup mana pun (bukan cuma si penanya)
    if action in ("dailyoff", "dailyon"):
        return await callback.answer(
            "Alice Daily dinonaktifkan.", show_alert=True,
        )
    if callback.from_user.id != owner_id:
        return await callback.answer(
            "Jangan dipencet lagi ngobrol sama yang lain.", show_alert=True
        )

    msg = callback.message
    chat = msg.chat
    key = (chat.id, owner_id)

    if action == "pick":
        return await _pick_mode(client, callback, owner_id, extra)

    if action == "cancel":
        PENDING.pop(key, None)
        await callback.answer("Dibatalkan.")
        return await _del(client, chat.id, msg.id)

    if action == "stop":
        _end_session(key)
        await callback.answer("Percakapan diakhiri.")
        for mid in (msg.id, _HINTS.pop(key, None)):
            if mid:
                await _del(client, chat.id, mid)
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
            "Balas pesan jawaban bot ini dengan pertanyaanmu."
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
    "bl": blacklist_cmd,
    "unbl": unblacklist_cmd,
    "listbl": listblacklist_cmd,
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


# ===========================================================================
# 8. DAILY (ringkasan obrolan grup berkala + tag username)
# ===========================================================================
DAILY_INTERVAL = 7200         # detik. 15 = tes; produksi mis. 3600 (1 jam) / 86400 (1 hari)
DAILY_MIN_MESSAGES = 1      # minimal pesan baru supaya ringkasan dikirim (produksi: 5-10)
DAILY_STORE_MAX = 200       # maksimal pesan tersimpan per grup
DAILY_AUTO_DELETE = False   # True = ringkasan ikut terhapus otomatis (DELETE_AFTER)
DAILY_FOOTER = False        # True = pesan daily ikut footer tabel AliceDevs

DAILY_KEY = "ASK_DAILY"                # on/off per grup      (scope = chat.id)
DAILY_CHAT_KEY = "ASK_DAILY_CHAT"      # isi obrolan per grup (scope = chat.id)
DAILY_CHATS_KEY = "ASK_DAILY_CHATS"    # daftar grup aktif    (scope = id bot)

DAILY_PROMPT = (
    "Kamu AI yang meringkas obrolan grup Telegram dalam bahasa Indonesia gaul "
    "dengan sindiran ringan yang lucu. Tulis maksimal 1 baris, SATU KOMENTAR "
    "SINGKAT PER BARIS. Baris pertama: topik utama obrolan. Baris berikutnya: "
    "komentar lucu tentang member yang aktif; tiap baris WAJIB menyebut tag member "
    "PERSIS seperti yang tertulis di log (contoh: @username), boleh di awal atau "
    "di akhir kalimat. Contoh gaya: 'dipaling dingin banget @budi' atau "
    "'@sari kalau ada maunya aja nimbrung grup heleh'. "
    "Hanya pakai tag yang ada di log, jangan mengarang. Member tanpa tag cukup "
    "disebut namanya. Candaan ringan saja: jangan menghina SARA, fisik, atau keluarga. "
    "Tanpa markdown, tanpa nomor, tanpa pembuka atau penutup."
)

_DAILY_TASK = None


def _daily_track(chat_id, msg):
    """Catat id pesan daily supaya reply ke pesan itu tidak dijawab AI."""
    mid = getattr(msg, "id", None)
    if not mid:
        return
    ids = DAILY_MSG_IDS.setdefault(chat_id, set())
    if len(ids) > 50:
        ids.clear()
    ids.add(mid)


async def _daily_enabled(chat_id):
    return False


async def _daily_set(chat_id, enabled):
    await dB.set_var(chat_id, DAILY_KEY, bool(enabled))


async def _daily_chats(client):
    """Daftar id grup yang pernah mengaktifkan daily."""
    return await dB.get_list_from_var(client.me.id, DAILY_CHATS_KEY) or []


async def _daily_mark(client, chat_id):
    """Catat grup ke daftar scheduler.
    Scope HARUS integer (id bot), bukan "global": kolom id di database berupa
    INTEGER, string "global" bikin sqlite3 "datatype mismatch"."""
    sudah = {str(c) for c in await _daily_chats(client)}
    if str(chat_id) not in sudah:
        await dB.add_to_var(client.me.id, DAILY_CHATS_KEY, chat_id)


async def _daily_store(client, message):
    """Simpan pesan obrolan grup (beserta username) untuk bahan ringkasan."""
    chat, user = message.chat, message.from_user
    if not _is_group(chat) or not user or user.is_bot:
        return
    if not await _daily_enabled(chat.id):
        return
    text = (message.text or message.caption or "").strip()
    if not text or text.startswith("/"):
        return
    items = await dB.get_var(chat.id, DAILY_CHAT_KEY) or []
    if not items:                       # awal siklus: pastikan grup terdaftar di scheduler
        await _daily_mark(client, chat.id)
    items.append({
        "u": user.first_name or "User",
        "un": user.username or "",
        "t": text[:300],
    })
    await dB.set_var(chat.id, DAILY_CHAT_KEY, items[-DAILY_STORE_MAX:])


# --- layout & tombol Alice Daily (simpel, tanpa footer tabel) ----------------
def blocks_daily_aktif():
    return [
        paragraph([emo(EMOJI_SUKSES, "🤖"), RichTextBold(" Alice Daily aktif")]),
        paragraph(["Terima kasih yakz sudah menambahkan ku digrup ini!"]),
        paragraph([f"Aku bakal ngerangkum obrolan tiap {_fmt_interval(DAILY_INTERVAL)}. "
                   "Mau ngobrol? Pakai /ask."]),
    ]


def blocks_daily(text):
    """Ringkasan: judul, satu baris = satu komentar (ber-@tag), lalu contoh /ask."""
    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    return [
        paragraph([emo(EMOJI_JAWABAN, "🌅"), RichTextBold(" Ringkasan Alice Daily")]),
        *[paragraph([ln]) for ln in lines],
        paragraph([RichTextBold("Mau ngobrol? Coba:")]),
        paragraph([mono("/ask ranking level chaos anggota grup")]),
    ]


def _daily_buttons(on=True):
    """Satu tombol lebar: Matikan <-> Aktifkan lagi."""
    if on:
        btn = (" Matikan Alice Daily", "askbot_dailyoff_0", ButtonStyle.DANGER, EMOJI_STOP)
    else:
        btn = (" Aktifkan Alice Daily", "askbot_dailyon_0", ButtonStyle.SUCCESS, EMOJI_SUKSES)
    return ikb([[btn]])


async def _daily_toggle(client, callback, enable):
    """Tombol matikan / aktifkan lagi Alice Daily (khusus admin grup)."""
    msg = callback.message
    chat = msg.chat
    if not _is_group(chat) or not await _is_admin(client, chat.id, callback.from_user.id):
        return await callback.answer("Khusus admin grup.", show_alert=True)

    await _daily_set(chat.id, enable)
    if enable:
        await _daily_mark(client, chat.id)
        start_daily(client)
    else:
        await dB.set_var(chat.id, DAILY_CHAT_KEY, [])     # buang obrolan yang tersimpan
    await callback.answer("Alice Daily diaktifkan ✅" if enable else "Alice Daily dimatikan ✅")
    try:
        await msg.edit_reply_markup(_daily_buttons(enable))
    except Exception:
        pass


def _daily_label(item):
    return f"@{item['un']}" if item.get("un") else item["u"]


def _daily_clean(result, items):
    """Rapikan hasil AI; @tag yang tidak ada di log dibuang '@'-nya (anti ngarang)."""
    known = {i["un"].lower() for i in items if i.get("un")}
    result = _plain(str(result))
    return re.sub(
        r"@(\w+)",
        lambda m: m.group(0) if m.group(1).lower() in known else m.group(1),
        result,
    )


async def daily_on_added(client, update):
    """Dipanggil saat bot ditambahkan ke grup -> aktifkan daily otomatis."""
    chat = update.chat
    if not _is_group(chat):
        return
    await _daily_set(chat.id, True)
    await _daily_mark(client, chat.id)
    start_daily(client)

    sent = await _kirim(
        client, chat.id, blocks_daily_aktif(),
        markup=_daily_buttons(True), footer=DAILY_FOOTER,
    )
    _daily_track(chat.id, sent)


async def daily_summary_now(client, chat_id, quiet=False):
    """Buat dan kirim ringkasan. quiet=True: grup sepi dilewati diam-diam."""
    items = await dB.get_var(chat_id, DAILY_CHAT_KEY) or []
    if len(items) < DAILY_MIN_MESSAGES:
        if quiet:
            return
        return await _kirim(
            client, chat_id,
            blocks_info(EMOJI_GAGAL, "📭", "Belum ada obrolan untuk diringkas."),
        )

    recent = items[-100:]
    conv = [
        {"role": "system", "content": DAILY_PROMPT},
        {"role": "user", "content": "\n".join(f"{_daily_label(i)}: {i['t']}" for i in recent)},
    ]
    result = await _call_ai(conv)
    if not result:
        logger.error(f"Daily: AI tidak merespon untuk grup {chat_id}")
        return
    await dB.set_var(chat_id, DAILY_CHAT_KEY, [])
    sent = await _kirim(
        client, chat_id, blocks_daily(_daily_clean(result, recent)),
        markup=_daily_buttons(True), footer=DAILY_FOOTER, delete=DAILY_AUTO_DELETE,
    )
    _daily_track(chat_id, sent)


async def daily_scheduler(client):
    """Kirim ringkasan tiap DAILY_INTERVAL detik untuk semua grup yang aktif."""
    logger.info(f"Alice Daily jalan, interval {_fmt_interval(DAILY_INTERVAL)}")
    while True:
        await asyncio.sleep(DAILY_INTERVAL)
        try:
            for chat_id in await _daily_chats(client):
                try:
                    if not await _daily_enabled(int(chat_id)):
                        continue
                    await daily_summary_now(client, int(chat_id), quiet=True)
                    await asyncio.sleep(1)      # jeda antar grup, hindari flood
                except Exception:
                    logger.error(traceback.format_exc())
        except Exception:
            logger.error(traceback.format_exc())


def start_daily(client):
    return None