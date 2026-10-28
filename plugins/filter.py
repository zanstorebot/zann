from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from clients import alice
from command import (FILTERS, REP_BLOCK, filter_cmd, filters_cmd,
                     getfilter_cmd, stopfilter_cmd)
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
IS_PRO = True

__MODULES__ = "Filters"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Filter</b>
`{0}filter` (nama) (balas pesan) : Simpan filter auto-reply
`{0}filters` : Lihat semua filter
`{0}getfilter` (nama) raw : Lihat format mentah filter
`{0}stop` (nama) : Hapus satu filter
`{0}stop all` : Hapus semua filter
</blockquote>"""


@CMD.NO_CMD("REP_BLOCK", alice)
async def _(client, message):
    return await REP_BLOCK(client, message)


@CMD.UBOT("filter")
async def _(client, message):
    return await filter_cmd(client, message)


@CMD.UBOT("getfilter")
async def _(client, message):
    return await getfilter_cmd(client, message)


@CMD.UBOT("filters")
async def _(client, message):
    return await filters_cmd(client, message)


@CMD.UBOT("stop")
async def _(client, message):
    return await stopfilter_cmd(client, message)


@CMD.NO_CMD("FILTERS", alice)
@CMD.capture_err
async def _(client, message):
    return await FILTERS(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Filter"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}filter'), cell('Simpan filter auto-reply')],
                    [cell(f'{prefix}filters'), cell('Lihat semua filter')],
                    [cell(f'{prefix}getfilter'), cell('Lihat format mentah filter')],
                    [cell(f'{prefix}stop'), cell('Hapus satu filter')],
                    [cell(f'{prefix}stop all'), cell('Hapus semua filter')],
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
