from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import autofw_cmd
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
IS_PRO = True

__MODULES__ = "Autofw"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Auto Forward</b>
`{0}autofw add` (link) : Tambahkan link pesan untuk forward otomatis
`{0}autofw` (on/off) : Aktifkan atau nonaktifkan auto forward
`{0}autofw del` : Hapus data auto forward
`{0}autofw delay` (angka) : Atur jeda auto forward
`{0}autofw get` : Lihat data auto forward

Catatan: Tambahkan link terlebih dahulu sebelum mengaktifkan fitur.
</blockquote>"""


@CMD.UBOT("autofw")
async def _(client, message):
    return await autofw_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Auto Forward"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}autofw add'), cell('Tambahkan link pesan untuk forward otomatis')],
                    [cell(f'{prefix}autofw'), cell('Aktifkan atau nonaktifkan auto forward')],
                    [cell(f'{prefix}autofw del'), cell('Hapus data auto forward')],
                    [cell(f'{prefix}autofw delay'), cell('Atur jeda auto forward')],
                    [cell(f'{prefix}autofw get'), cell('Lihat data auto forward')],
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
