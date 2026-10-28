from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import clearnotes_cmd, getnote_cmd, listnotes_cmd, savenote_cmd
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Notes"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Catatan</b>
`{0}save` (nama) (balas pesan) : Simpan catatan
`{0}get` (nama) : Ambil catatan
`{0}notes` : Lihat semua catatan
`{0}clear` (nama) : Hapus catatan
`{0}clear all` : Hapus semua catatan
</blockquote>"""


@CMD.UBOT("save")
async def _(client, message):
    return await savenote_cmd(client, message)


@CMD.UBOT("get")
async def _(client, message):
    return await getnote_cmd(client, message)


@CMD.UBOT("notes")
async def _(client, message):
    return await listnotes_cmd(client, message)


@CMD.UBOT("clear")
async def _(client, message):
    return await clearnotes_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Catatan"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}save'), cell('Simpan catatan')],
                    [cell(f'{prefix}get'), cell('Ambil catatan')],
                    [cell(f'{prefix}notes'), cell('Lihat semua catatan')],
                    [cell(f'{prefix}clear'), cell('Hapus catatan')],
                    [cell(f'{prefix}clear all'), cell('Hapus semua catatan')],
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
