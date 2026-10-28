import re
import traceback
from math import ceil
from typing import List, Optional, Tuple
from uuid import uuid4

from pyrogram.enums import ButtonStyle
from pyrogram.helpers import ikb, kb
from pyrogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                            WebAppInfo)

from database import dB, state
from logs import logger

from .note_rich import _extract_buttons

COLUMN_SIZE = 4  # Controls the button number of height
NUM_COLUMNS = 2  # Controls the button number of width

_STYLE_MAP = {
    "primary": ButtonStyle.PRIMARY,
    "success": ButtonStyle.SUCCESS,
    "danger": ButtonStyle.DANGER,
}


class _Btn(list):
    """[text, data] (bisa di-unpack seperti format lama) + atribut style/emo."""

    style = None
    emo = None


class EqInlineKeyboardButton(InlineKeyboardButton):
    def __init__(
        self,
        text,
        callback_data=None,
        style=ButtonStyle.DEFAULT,
        **kwargs,
    ):
        super().__init__(
            text=text,
            callback_data=callback_data,
            style=style,
            **kwargs,
        )

    def __eq__(self, other):
        return self.text == other.text

    def __lt__(self, other):
        return self.text < other.text

    def __gt__(self, other):
        return self.text > other.text

def _nav_row(prefix, modulo_page, max_num_pages, is_bot=False):
    prev_page = modulo_page - 1 if modulo_page > 0 else max_num_pages - 1
    # help di user (inline) pakai label < x >, help langsung di bot tetap kosong
    prev_text, close_text, next_text = (
        ("❮", "✖", "❯") if is_bot else ("❮", "✖", "❯")
    )
    return [
        EqInlineKeyboardButton(
            prev_text,
            callback_data=f"{prefix}_prev({prev_page})",
            style=ButtonStyle.DANGER,
            icon_custom_emoji_id="5398027047798859442",
        ),
        EqInlineKeyboardButton(
            close_text,
            callback_data="buttonclose",
            style=ButtonStyle.DANGER,
            icon_custom_emoji_id="5260293700088511294",
        ),
        EqInlineKeyboardButton(
            next_text,
            callback_data=f"{prefix}_next({modulo_page + 1})",
            style=ButtonStyle.DANGER,
            icon_custom_emoji_id="5395401448391470171",
        ),
    ]

# ---------------------------------------------------------------------------
# Kategori inline help: Kategori -> daftar modul -> help modul
# Isi = nama __MODULES__ (huruf kecil, sama dengan key HELPABLE).
# Modul yang belum masuk kategori mana pun otomatis tampil di "Lainnya".
# ---------------------------------------------------------------------------
HELP_CATEGORIES = [
    ("👮 Admins", ["admins", "locks", "global", "tagall", "invite", "chats",
                "logs", "dmute", "extras"]),
    ("🛠 Settings", ["settings", "prefix", "emoji", "sudoers", "ignore",
                  "spambot", "format", "button"]),
    ("🎉 Fun", ["x post", "merk", "fake", "efek pesan", "games",
             "wapak", "pantun", "toxic", "cat", "asupan", "reaction"]),
    ("🤖 Ai", ["chat gpt", "bingai", "textgen", "chatbot"]),
    ("🛡 Protect", ["pmpermit", "anti ucast", "blocked", "afk"]),
    ("🔎 Downloader", ["downloader", "sosmed", "webdl", "copy"]),
    ("📡 Automasi", ["autoread", "autoreply", "autofw", "filters", "broadcast", "spam"]),
    ("⚡ Akun", ["profile", "info", "story", "history", "stalking"]),
    ("🎬 Media", ["music", "vctools", "voice"]),
    ("🪄 Generate", ["image", "brat", "carbon", "quote", "memify", "maker", "textpro",
                  "fonts", "qrcode", "img2text", "webshot", "tiny", "convert", "sticker"]),
    ("🔧 Tools", ["notes", "translate", "kbbi", "lyric", "chord", "pastebin", "mail",
               "cardinfo", "news", "saweria", "graph"]),
]
OTHER_CATEGORY = "Lainnya"
CAT_ROWS = 5            # baris modul per halaman di dalam kategori
MAIN_FIRST_PAGE = 6     # jumlah kategori di halaman 1 menu utama (sisanya di halaman 2)
CAT_PAGE_BASE = 1000    # prev_page_num >= 1000 = kembali ke kategori (lihat decode_help_page)


def _help_categories(module_dict):
    """[(nama_kategori, [key modul yang terlihat])] - kategori kosong tidak ditampilkan."""
    visible = {k for k, v in module_dict.items() if hasattr(v["module"], "__MODULES__")}
    used, cats = set(), []
    for name, keys in HELP_CATEGORIES:
        mods = sorted(k for k in keys if k in visible)
        used.update(mods)
        cats.append((name, mods))
    cats.append((OTHER_CATEGORY, sorted(visible - used)))
    return cats


def encode_help_page(cat_idx, page):
    """Nomor halaman yang dibawa tombol modul -> Back dari help modul kembali ke kategorinya."""
    return CAT_PAGE_BASE + cat_idx * 100 + page


def decode_help_page(num):
    """Return (cat_idx, page) atau None kalau num = halaman menu utama (format lama)."""
    if num < CAT_PAGE_BASE:
        return None
    num -= CAT_PAGE_BASE
    return num // 100, num % 100


def _main_pages(module_dict):
    """Kategori yang terlihat dibagi per halaman: [ [(idx, nama), ...6], [(idx, nama), ...sisa] ]."""
    visible = [(idx, name) for idx, (name, mods) in enumerate(_help_categories(module_dict)) if mods]
    pages = [visible[:MAIN_FIRST_PAGE], visible[MAIN_FIRST_PAGE:]]
    return [p for p in pages if p] or [[]]


def main_page_of(cat_idx, module_dict):
    """Halaman menu utama tempat kategori cat_idx berada (untuk tombol Back)."""
    for page, items in enumerate(_main_pages(module_dict)):
        if any(idx == cat_idx for idx, _ in items):
            return page
    return 0


def paginate_modules(page_n, module_dict, prefix, is_bot=False):
    """Menu utama inline help: tombol kategori (2 per baris), 2 halaman (6 + sisanya)."""
    pages = _main_pages(module_dict)
    page = page_n % len(pages)
    buttons = [
        EqInlineKeyboardButton(
            name,
            callback_data=f"{prefix}_cat({idx},0)",
            style=ButtonStyle.PRIMARY,
        )
        for idx, name in pages[page]
    ]
    rows = [buttons[i : i + NUM_COLUMNS] for i in range(0, len(buttons), NUM_COLUMNS)]
    if len(pages) > 1:
        rows.append(_nav_row(prefix, page, len(pages), is_bot))   # ❮ ✖ ❯
    else:
        rows.append(
            [
                EqInlineKeyboardButton(
                    "✖" if is_bot else "✖",
                    callback_data="buttonclose",
                    style=ButtonStyle.DANGER,
                    icon_custom_emoji_id="5260293700088511294",
                )
            ]
        )
    return rows


def help_main_info(page_n, module_dict):
    """(halaman, total halaman) menu utama untuk header help."""
    pages = _main_pages(module_dict)
    return page_n % len(pages), len(pages)


def help_category_info(cat_idx, page_n, module_dict):
    """(nama kategori, jumlah modul, halaman, total halaman) untuk header help."""
    cats = _help_categories(module_dict)
    cat_idx = cat_idx if 0 <= cat_idx < len(cats) else 0
    name, mods = cats[cat_idx]
    max_pages = max(1, ceil(len(mods) / (CAT_ROWS * NUM_COLUMNS)))
    return name, len(mods), page_n % max_pages, max_pages


def paginate_category(cat_idx, page_n, module_dict, prefix, is_bot=False):
    """Isi satu kategori: tombol modul + navigasi halaman + Back ke menu kategori."""
    cats = _help_categories(module_dict)
    cat_idx = cat_idx if 0 <= cat_idx < len(cats) else 0
    _, mods = cats[cat_idx]

    per_page = CAT_ROWS * NUM_COLUMNS
    max_pages = max(1, ceil(len(mods) / per_page))
    page = page_n % max_pages
    back_num = encode_help_page(cat_idx, page)

    buttons = [
        EqInlineKeyboardButton(
            module_dict[key]["module"].__MODULES__,
            callback_data=f"{prefix}_module({key},{back_num})",
            style=ButtonStyle.SUCCESS,
        )
        for key in mods[page * per_page : (page + 1) * per_page]
    ]
    rows = [buttons[i : i + NUM_COLUMNS] for i in range(0, len(buttons), NUM_COLUMNS)]

    back = EqInlineKeyboardButton(
        "🔙 Back",
        callback_data=f"{prefix}_back({main_page_of(cat_idx, module_dict)})",
        style=ButtonStyle.DANGER,
    )
    if max_pages > 1:
        prev_text, next_text = ("❮", "❯") if is_bot else ("❮", "❯")
        rows.append(
            [
                EqInlineKeyboardButton(
                    prev_text,
                    callback_data=f"{prefix}_cat({cat_idx},{(page - 1) % max_pages})",
                    style=ButtonStyle.DANGER,
                    icon_custom_emoji_id="5398027047798859442",
                ),
                back,
                EqInlineKeyboardButton(
                    next_text,
                    callback_data=f"{prefix}_cat({cat_idx},{(page + 1) % max_pages})",
                    style=ButtonStyle.DANGER,
                    icon_custom_emoji_id="5395401448391470171",
                ),
            ]
        )
    else:
        rows.append([back])
    return rows


class ButtonUtils:
    # Compile regex patterns for better performance
    URL_PATTERN = re.compile(
        r"(?:https?://)?(?:www\.)?[a-zA-Z0-9.-]+(?:\.[a-zA-Z]{2,})+(?:[/?]\S+)?|tg://\S+"
    )
    BUTTON_PATTERN = re.compile(r"\[(.*?)\|(.*?)\]")
    FORMAT_TAGS = {
        "<b>": "**",
        "<i>": "__",
        "<strike>": "~~",
        "<spoiler>": "||",
        "<u>": "--",
    }

    @staticmethod
    def is_url(text: str) -> bool:
        """Check if text is a URL (di awal teks)."""
        return bool(ButtonUtils.URL_PATTERN.match(text))

    @staticmethod
    def is_number(text: str) -> bool:
        """Check if text is a number."""
        return text.isdigit()

    @staticmethod
    def is_copy(text: str) -> bool:
        return text.startswith("copy:")

    @staticmethod
    def is_alert(text: str) -> bool:
        return text.startswith("alert:")

    @staticmethod
    def is_web(text: str) -> bool:
        return text.startswith("web:")

    @staticmethod
    def cek_tg(text):
        tg_pattern = r"https?:\/\/files\.catbox\.moe\/\S+"
        match = re.search(tg_pattern, text)

        if match:
            tg_link = match.group(0)
            non_tg_text = text.replace(tg_link, "").strip()
            return tg_link, non_tg_text
        else:
            return (None, text)

    @staticmethod
    def parse_msg_buttons(texts: str) -> Tuple[str, List[List]]:
        """
        Format tombol di teks:
            [Teks|data]                       satu tombol
            [Teks|data|danger, emo="123"]     dengan style (primary/success/danger) + emoji premium
            [Teks|data|same]                  sebaris dengan tombol sebelumnya (aturan lama)
        Tombol yang ditulis berdampingan dalam satu baris = satu deret; baris baru = deret baru.
        Return (teks_tanpa_tombol, rows) dengan rows = [[[teks, data], ...], ...].
        Tiap tombol bisa di-unpack seperti [teks, data] dan punya atribut .style/.emo.
        """
        clean, rows = _extract_buttons(texts or "")
        btn = []
        for row in rows:
            line = []
            for b in row:
                item = _Btn([b["text"], b["data"]])
                item.style = b["style"]
                item.emo = b["emo"]
                line.append(item)
            btn.append(line)
        return clean.strip(), btn

    @staticmethod
    async def create_button(
        text: str,
        data: str,
        with_suffix: str = "",
        style: Optional[str] = None,
        emo: Optional[str] = None,
    ) -> InlineKeyboardButton:
        """Create an InlineKeyboardButton based on data type."""
        data = data.strip()
        extra = {}
        if style in _STYLE_MAP:
            extra["style"] = _STYLE_MAP[style]
        if emo:
            extra["icon_custom_emoji_id"] = str(emo)

        # awalan khusus dicek dulu, supaya "web:https://..." tidak dianggap URL biasa
        if ButtonUtils.is_copy(data):
            return InlineKeyboardButton(
                text=text, copy_text=data[len("copy:"):], **extra
            )
        elif ButtonUtils.is_alert(data):
            alert_text = data[len("alert:"):]
            uniq = str(uuid4().int)[:8]
            await dB.set_var(int(uniq), int(uniq), alert_text)
            cb_data = f"alertcb_{int(uniq)}"
            return InlineKeyboardButton(text=text, callback_data=cb_data, **extra)
        elif ButtonUtils.is_web(data):
            url = data[len("web:"):]
            logger.info(f"Type data:{url} ")
            return InlineKeyboardButton(text=text, web_app=WebAppInfo(url=url), **extra)
        elif ButtonUtils.is_url(data):
            return InlineKeyboardButton(text=text, url=data, **extra)
        elif ButtonUtils.is_number(data):
            return InlineKeyboardButton(text=text, user_id=int(data), **extra)
        return InlineKeyboardButton(
            text=text,
            callback_data=f"{data}_{with_suffix}" if with_suffix else data,
            **extra,
        )

    @staticmethod
    async def create_inline_keyboard(
        buttons: List[List], suffix: str = ""
    ) -> InlineKeyboardMarkup:
        """Create InlineKeyboardMarkup from button data."""
        keyboard = []
        for row in buttons:
            keyboard.append(
                [
                    await ButtonUtils.create_button(
                        item[0],
                        item[1],
                        suffix,
                        style=getattr(item, "style", None),
                        emo=getattr(item, "emo", None),
                    )
                    for item in row
                ]
            )
        return InlineKeyboardMarkup(keyboard)

    """Pre-defined keyboard templates for Pyrogram."""

    @staticmethod
    def start_menu(is_admin: bool = False) -> kb:
        """Generate start menu keyboard."""
        common_buttons = [
        [
          (("Mulai Buat Userbot"), ButtonStyle.PRIMARY, "5456140674028019486"),
        ],
        [
          (("Trial Userbot"), ButtonStyle.PRIMARY, "6176861049862493512"),
          (("Cek Fitur"), ButtonStyle.PRIMARY, "5282843764451195532"),
        ],
        [
          (("Referral"), ButtonStyle.SUCCESS, "5355235390980642171"),
          (("Token"), ButtonStyle.SUCCESS, "6176966310920983412"),
        ],
    ]
        
        if is_admin:
            common_buttons.extend(
                [
                    ["Updates"],
                ]
            )
        else:
            common_buttons.extend([["Hubungi Admins"]])

        return kb(common_buttons, resize_keyboard=True, one_time_keyboard=True)

    @staticmethod
    def userbot(user_id, count):
        button = ikb(
            [
                [
                    (
                        (("Delete User"),
                        f"del_ubot {int(user_id)}", ButtonStyle.DANGER, "5445267414562389170")
                    ),
                    (
                        (("Check Phone"),
                        f"get_phone {int(count)}", ButtonStyle.SUCCESS, "5314277491924284293")
                    ),
                ],
                [
                    (
                        (("Check Expired"),
                        f"cek_masa_aktif {int(user_id)}", ButtonStyle.PRIMARY, "5413879192267805083")
                    )
                ],
                [
                    (
                        (("Get Otp"),
                        f"get_otp {int(count)}", ButtonStyle.DANGER, "5406809207947142040")
                    ),
                    (
                        (("Get V2L"),
                        f"get_faktor {int(count)}", ButtonStyle.SUCCESS, "5472308992514464048")
                    ),
                ],
                [
                    (
                        (("Delete Account"),
                        f"ub_deak {int(count)}", ButtonStyle.DANGER, "6114074516395134769")
                    )
                ],
                [
                    ("❮", f"prev_ub {int(count)}"),
                    ("Close", "buttonclose"),
                    ("❯", f"next_ub {int(count)}"),
                ],
            ]
        )
        return button


    @staticmethod
    def fake_userbot(user_id, count):
        button = ikb(
            [
                [
                    (
                        "Delete User",
                        f"del_ubot {int(user_id)}",
                    ),
                ],
                [
                    (
                        "Check Expired",
                        f"cek_masa_aktif {int(user_id)}",
                    )
                ],
                [
                    ("❮", f"fakeprev_ub {int(count)}"),
                    ("Close", "buttonclose"),
                    ("❯", f"fakenext_ub {int(count)}"),
                ],
            ]
        )
        return button

    @staticmethod
    def deak(user_id, count):
        button = ikb(
            [[("⬅️", f"prev_ub {int(count)}"), ("Approve", f"deak_akun {int(count)}")]]
        )
        return button

    @staticmethod
    async def generate_inline_query(message, chat_id, bot_username, query):
        try:
            client = message._client
            results = await client.get_inline_bot_results(bot_username, query)
            if results and results.results:
                return {
                    "query_id": results.query_id,
                    "result_id": results.results[0].id,
                    "results": results.results,
                    "query": query,
                }
            return None
        except Exception:
            return None

    @staticmethod
    async def send_inline_bot_result(
        message,
        chat_id,
        bot_username,
        query,
        reply_to_message_id: Optional[int] = None,
    ) -> bool:
        """
        Send inline bot result to chat.

        Args:
            client: Pyrogram Client instance
            message: Original message to reply to
            bot_username: Username of the bot to query
            query: Query string to send to the bot
            reply_to_message_id: Optional message ID to reply to

        Returns:
            Boolean indicating success/failure
        """
        client = message._client
        try:
            query_results = await ButtonUtils.generate_inline_query(
                message, chat_id, bot_username, query
            )

            if not query_results:
                return False

            data = await client.send_inline_bot_result(
                chat_id,
                query_results["query_id"],
                query_results["result_id"],
                reply_to_message_id=reply_to_message_id,
            )
            # logger.warning(f"line 273 {data}")
            msg_id = data.id if not hasattr(data, "updates") else data.updates[0].id
            inline_id = {
                "chat": chat_id,
                "_id": msg_id,
                "me": client.me.id,
                "idm": id(message),
            }
            state.set(query, query, inline_id)           # lama, biarkan
            state.set(client.me.id, query, inline_id)    # BARU: simpan per user
            return True


        except Exception:
            logger.error(f"Error in send_inline_bot_result: {traceback.format_exc()}")
            return False

    @staticmethod
    def plus_minus(bulan, harga, plan):
        button = ikb(
            [
                [
                    (("⁻1 bulan"), f"kurang {bulan} {harga} {plan}", ButtonStyle.DANGER, "5229113891081956317"),
                    (("⁺1 bulan"), f"tambah {bulan} {harga} {plan}", ButtonStyle.PRIMARY, "5226945370684140473"),
                ],
                [(("Konfirmasi"), f"confirm {bulan} {harga} {plan}", ButtonStyle.SUCCESS, "6296367896398399651")],
                [(("Batal"), "buttonclose", ButtonStyle.DANGER, "5260293700088511294")],
            ]
        )
        return button

    @staticmethod
    def chose_plan():
        button = ikb(
            [
                [
                    ((" ULTRA PREMIUM"), f"planusers is_pro", ButtonStyle.PRIMARY, "5296606269891701356"),
                ],
                [(("Batal"), "buttonclose", ButtonStyle.DANGER, "5260293700088511294")],
            ]
        )
        return button

    @staticmethod
    def cek_masa_aktif(user_id):
        button = ikb(
            [
                [
                    (("Cek Expired"),
                    f"cek_masa_aktif {int(user_id)}", ButtonStyle.PRIMARY, "5413879192267805083"),
                ],
            ]
        )
        return button
      
    @staticmethod
    def create_font_keyboard(font_list, get_id, current_batch):
        keyboard = []
        for font_dict in font_list:
            for key, value in font_dict.items():
                keyboard.append(
                    InlineKeyboardButton(
                        key, callback_data=f"get_font {get_id} {value}",
                    )
                )

        rows = [keyboard[i : i + 2] for i in range(0, len(keyboard), 2)]

        while len(rows) < 3:
            rows.append([])

        rows.append(
            [
                InlineKeyboardButton(
                    "⬅️", callback_data=f"prev_font {get_id} {current_batch}",
                ),
                InlineKeyboardButton("❌", callback_data=f"close inline_font {get_id}",),
                InlineKeyboardButton(
                    "➡️", callback_data=f"next_font {get_id} {current_batch}",
                ),
            ]
        )
        return rows

    @staticmethod
    def create_buttons_textpro(font_list, get_id, current_batch):
        keyboard = []
        for font_dict in font_list:
            for key, value in font_dict.items():
                keyboard.append(
                    InlineKeyboardButton(key, callback_data=f"genpro {get_id} {value}")
                )

        rows = [keyboard[i : i + 2] for i in range(0, len(keyboard), 2)]

        while len(rows) < 3:
            rows.append([])

        rows.append(
            [
                InlineKeyboardButton(
                    "⬅️", callback_data=f"prev_textpro {get_id} {current_batch}",
                ),
                InlineKeyboardButton(
                    "❌", callback_data=f"close inline_textpro {get_id}",
                ),
                InlineKeyboardButton(
                    "➡️", callback_data=f"next_textpro {get_id} {current_batch}",
                ),
            ]
        )
        return rows
