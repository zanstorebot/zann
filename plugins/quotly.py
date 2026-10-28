from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import qcolor_cmd, qoutly_cmd
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Quote"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Quote</b>
`{0}q` (balas pesan) : Buat quote warna acak
`{0}q` (warna) (balas pesan) : Buat quote warna pilihan
`{0}q @username` (balas pesan) : Buat quote user lain
`{0}q -r` (balas pesan) : Buat quote dengan reply
`{0}q` (jumlah) (balas pesan) : Buat beberapa quote
`{0}qcolor` : Lihat daftar warna quote
</blockquote>"""


@CMD.UBOT("q|qcolor")
async def _(client, message):
    if message.command[0] == "qcolor":
        return await qcolor_cmd(client, message)
    elif message.command[0] == "q":
        return await qoutly_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Quote"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}q'), cell('Buat quote warna acak')],
                    [cell(f'{prefix}q @username'), cell('Buat quote user lain')],
                    [cell(f'{prefix}q -r'), cell('Buat quote dengan reply')],
                    [cell(f'{prefix}qcolor'), cell('Lihat daftar warna quote')],
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
