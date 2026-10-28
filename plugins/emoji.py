from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import setemoji_cmd
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Emoji"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Emoji</b>
`{0}setemoji` (jenis) (emoji) : Atur emoji tampilan
Jenis: `ping`, `uptime`, `profil`, `robot`, `msg`, `warn`, `block`, `gagal`, `sukses`, `owner`, `klip`, `net`, `up`, `down`, `speed`, `proses`, `status`
`{0}id` (balas pesan) : Lihat ID emoji atau media
`{0}getemoji` : Lihat semua emoji yang diatur

Catatan: Fitur emoji hanya untuk pengguna Telegram Premium.
</blockquote>"""


@CMD.UBOT("setemoji|getemoji")
async def _(client, message):
    return await setemoji_cmd(client, message)


def _make_rich(*blocks):
    builder = RichMessageBuilder()
    for block in blocks:
        builder.add(block)
    return builder.build()


async def __HELP_RICH__(client, chat_id, prefix, text_help,
                        message_id=None, prev_page_num=0):
    rich = _make_rich(
        divider(),
        table(
            [[cell([emo(5262970276462745484, "💎"), RichTextBold(f" CMD/PREFIXES: {prefix}")], align="center", is_header=True)]],
        ),
        details(
            [emo(5242278610089304739, "🤖"), " Perintah Emoji"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}setemoji'), cell('Atur emoji tampilan')],
                    [cell('ping | uptime | profil | robot | msg | warn | block | gagal | sukses | owner | klip | net | up | down | speed | proses | status'), cell('-')],
                    [cell(f'{prefix}id'), cell('Lihat ID emoji atau media')],
                    [cell(f'{prefix}getemoji'), cell('Lihat semua emoji yang diatur')],
                ],
                bordered=True,
                striped=True,
            ),
        ),
        divider(),
        footer_table(),
    )
    button = ikb(
        [
            [
                (
                    "Back",
                    f"help_back({prev_page_num})",
                    ButtonStyle.DANGER,
                    "5258330865674494479",
                ),
            ],
        ]
    )
    if message_id:
        return await client.edit_rich_message(
            chat_id, message_id, rich, reply_markup=button
        )
    return await client.send_rich_message(chat_id, rich, reply_markup=button)
