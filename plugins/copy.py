from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from command import copyall_cmd, copyall2_cmd
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)

IS_PRO = True
__MODULES__ = "Copy"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Copy</b>
`{0}copyall` (URL) (jumlah) : Salin media dari pesan
`{0}copyall2` (URL) (jumlah) : Salin pesan atau media dari pesan

Catatan: `{0}copyall` hanya mendukung media.
</blockquote>"""


@CMD.UBOT("curi")
async def _(client, message):
    return await copyall_cmd(client, message)


@CMD.UBOT("curi2")
async def _(client, message):
    return await copyall2_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Copy"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}curi'), cell('Salin media dari pesan')],
                    [cell(f'{prefix}curi2'), cell('Salin pesan atau media dari pesan')],
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
