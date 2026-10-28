from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import gstick_cmd, kang_cmd, unkang_cmd
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Sticker"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Sticker</b>
`{0}kang` (balas stiker) : Tambahkan stiker ke pack milikmu
`{0}unkang` (balas stiker) : Hapus stiker dari pack milikmu
`{0}gstik` (balas stiker) : Lihat informasi stiker
</blockquote>"""


@CMD.UBOT("gstik|getstiker|getsticker")
async def _(client, message):
    return await gstick_cmd(client, message)


@CMD.UBOT("unkang")
async def _(client, message):
    return await unkang_cmd(client, message)


@CMD.UBOT("kang")
async def _(client, message):
    return await kang_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Sticker"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}kang'), cell('Tambahkan stiker ke pack milikmu')],
                    [cell(f'{prefix}unkang'), cell('Hapus stiker dari pack milikmu')],
                    [cell(f'{prefix}gstik'), cell('Lihat informasi stiker')],
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
