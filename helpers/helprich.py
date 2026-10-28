from pyrogram.helpers import cell, divider, paragraph, table
from pyrogram.types import InputRichMessage, RichTextBold, RichTextTextMention, RichTextCustomEmoji

from config import BOT_ID, BOT_NAME, USENAME_OWNER
from database import dB

# ---------------------------------------------------------------------------
# Saklar rich message untuk SEMUA menu help (diatur owner: helprich on/off)
# ---------------------------------------------------------------------------
HELP_RICH_OFF = "HELP_RICH_OFF"


async def help_rich_on():
    """True = help pakai rich message (default), False = teks biasa."""
    return not await dB.get_var(BOT_ID, HELP_RICH_OFF)


async def set_help_rich(on):
    if on:
        await dB.remove_var(BOT_ID, HELP_RICH_OFF)
    else:
        await dB.set_var(BOT_ID, HELP_RICH_OFF, True)


def build_help_text(user, prefix, total, text_help=None, category=None, main_page=None):
    """Versi teks biasa (HTML) dari build_help_rich, dipakai saat helprich off."""
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    prefix_text = " ".join(p for p in prefix if p) or "Tanpa prefix/CMD"
    lines = [f"<b>📚 Help Menu{' - ' + category[0] if category else ''}</b>", "<blockquote>"
             f"👤 User: <a href=tg://user?id={user.id}>{full_name}</a>\n"
             f"⌨️ Prefix/CMD: <code>{prefix_text}</code>"]
    if category:
        name, count, page, max_pages = category
        lines[-1] += f"\n📂 Kategori: <b>{name}</b>\n🧩 Total Modul: {count}</blockquote>"
        hint = "🔙 Back untuk kembali ke kategori."
        if max_pages > 1:
            hint = f"Halaman {page + 1}/{max_pages}. " + hint
    else:
        lines[-1] += f"\n🧩 Total Plugins: {total}</blockquote>"
        hint = "Pilih kategori."
        if main_page and main_page[1] > 1:
            hint += f" Halaman {main_page[0] + 1}/{main_page[1]}"
    lines.append(f"<i>{hint}</i>")
    lines.append(text_help or f"<b>🤖 {BOT_NAME} by {USENAME_OWNER}</b>")
    return "\n".join(lines)



def emo(emoji_id, alt="✨"):
    return RichTextCustomEmoji(custom_emoji_id=str(emoji_id), alternative_text=alt)

def build_help_rich(user, prefix, total, text_help=None, category=None, main_page=None):
    """
    Header inline help.
    category = None                      -> menu utama  ("Pilih kategori ...")
    category = (nama, jumlah, hal, maks) -> isi kategori ("Kembali ke kategori ...")
    main_page = (hal, maks)              -> nomor halaman menu utama
    """
    full_name = f"{user.first_name} {user.last_name or ''}".strip()
    prefix_text = " ".join(p for p in prefix if p) or "Tanpa prefix/CMD"
    rows = [
        [
            cell([emo(5197503331215361533, "💎"), RichTextBold(" Details")], is_header=True),
            cell([emo(5242278610089304739, "💎"), RichTextBold(" Information")], is_header=True),
        ],
        [cell([emo(6104631352190043951, "💎"), " User"]),
         cell([RichTextTextMention(text=full_name, user=user)])],
        [cell([emo(5262970276462745484, "💎"), " Prefix/CMD"]), cell(prefix_text)],
    ]
    if category:
        name, count, page, max_pages = category
        rows.append([cell([emo(5296606269891701356, "💎"), " Kategori"]), cell([RichTextBold(name)])])
        rows.append([cell([emo(5296606269891701356, "💎"), " Total Modul"]), cell(str(count))])
        hint = "🔙 Back untuk kembali ke kategori."
        if max_pages > 1:
            hint = f"{page + 1}/{max_pages}. " + hint
    else:
        rows.append([cell([emo(5296606269891701356, "💎"), " Total Plugins"]), cell(str(total))])
        hint = "Pilih kategori."
        if main_page and main_page[1] > 1:      # (halaman, total halaman)
            hint += f"{main_page[0] + 1}/{main_page[1]}"

    return InputRichMessage(
        blocks=[
            paragraph([emo(5330399283030013876, "💎"),
                       RichTextBold(f" Help Menu - {category[0]}" if category else " Help Menu")]),
            divider(),
            table(rows),
            paragraph([emo(5242278610089304739, "💎"), f" {hint}"]),
            divider(),
            paragraph([emo(6017150732455646343, "💎"), f" Bot by {USENAME_OWNER}"]),
        ]
    )


def build_help_list_rich(
    user,
    prefix,
    names,
    page,
    per_page=24,
    cols=3,
):
    full_name = (
        f"{user.first_name} {user.last_name or ''}"
        .strip()
    )

    prefix_text = " ".join(
        p for p in prefix if p
    ) or " "

    total_plugins = len(names)

    total_pages = max(
        (total_plugins + per_page - 1) // per_page,
        1,
    )

    page = min(
        max(page, 1),
        total_pages,
    )

    chunk = names[
        (page - 1) * per_page:
        page * per_page
    ]

    rows = []

    for i in range(0, len(chunk), cols):
        items = chunk[i:i + cols]

        row = [
            cell(
                [
                    emo(
                        6124947887529921159,
                        "💎",
                    ),
                    f" {name}",
                ]
            )
            for name in items
        ]

        while len(row) < cols:
            row.append(cell(" "))

        rows.append(row)

    return InputRichMessage(
        blocks=[
            paragraph(
                [
                    emo(
                        5330399283030013876,
                        "💎",
                    ),
                    RichTextBold(" Help Menu"),
                ]
            ),

            divider(),

            table(
                [
                    [
                        cell(
                            [
                                emo(
                                    5197503331215361533,
                                    "💎",
                                ),
                                RichTextBold(" Details"),
                            ],
                            is_header=True,
                        ),
                        cell(
                            [
                                emo(
                                    5242278610089304739,
                                    "💎",
                                ),
                                RichTextBold(" Information"),
                            ],
                            is_header=True,
                        ),
                    ],
                    [
                        cell(
                            [
                                emo(
                                    6104631352190043951,
                                    "💎",
                                ),
                                " User",
                            ]
                        ),
                        cell(
                            [
                                RichTextTextMention(
                                    text=full_name,
                                    user=user,
                                )
                            ]
                        ),
                    ],
                    [
                        cell(
                            [
                                emo(
                                    5262970276462745484,
                                    "💎",
                                ),
                                " Prefix/CMD",
                            ]
                        ),
                        cell(prefix_text),
                    ],
                    [
                        cell(
                            [
                                emo(
                                    5296606269891701356,
                                    "💎",
                                ),
                                " Total Plugins",
                            ]
                        ),
                        cell(str(total_plugins)),
                    ],
                    [
                        cell(
                            [
                                emo(
                                    5296606269891701356,
                                    "💎",
                                ),
                                " Halaman",
                            ]
                        ),
                        cell(
                            f"{page}/{total_pages}"
                        ),
                    ],
                ]
            ),

            divider(),

            table(rows),

            divider(),

            paragraph(
                [
                    emo(
                        6017150732455646343,
                        "💎",
                    ),
                    (
                        f" Buka modul: "
                        f"{prefix_text}help "
                        "(nama modul)"
                        f" Halaman lain: "
                        f"{prefix_text}help 2"
                    ),
                ]
            ),

            paragraph(
                [
                    emo(
                        6017150732455646343,
                        "💎",
                    ),
                    f" Bot by {USENAME_OWNER}",
                ]
            ),
        ]
    )