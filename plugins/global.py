from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import (gban_cmd, gbanlist_cmd, gmute_cmd, gmutelist_cmd,
                     ungban_cmd, ungmute_cmd)
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
IS_PRO = True

__MODULES__ = "Global"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Global</b>
`{0}gban` (username) : Blokir user di semua grup admin
`{0}ungban` (username) : Buka global ban user
`{0}gbanlist` : Lihat daftar global ban
`{0}gmute` (username) : Bisukan user di semua grup admin
`{0}ungmute` (username) : Buka global mute user
`{0}gmutelist` : Lihat daftar global mute
</blockquote>"""


@CMD.UBOT("gban")
@CMD.FAKEDEV("gban")
async def _(client, message):
    return await gban_cmd(client, message)


@CMD.UBOT("ungban")
@CMD.FAKEDEV("ungban")
async def _(client, message):
    return await ungban_cmd(client, message)


@CMD.UBOT("gbanlist")
@CMD.FAKEDEV("gbanlist")
async def _(client, message):
    return await gbanlist_cmd(client, message)


@CMD.UBOT("gmute")
@CMD.FAKEDEV("gmute")
async def _(client, message):
    return await gmute_cmd(client, message)


@CMD.UBOT("ungmute")
@CMD.FAKEDEV("ungmute")
async def _(client, message):
    return await ungmute_cmd(client, message)


@CMD.UBOT("gmutelist")
@CMD.FAKEDEV("gmutelist")
async def _(client, message):
    return await gmutelist_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Global"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}gban'), cell('Blokir user di semua grup admin')],
                    [cell(f'{prefix}ungban'), cell('Buka global ban user')],
                    [cell(f'{prefix}gbanlist'), cell('Lihat daftar global ban')],
                    [cell(f'{prefix}gmute'), cell('Bisukan user di semua grup admin')],
                    [cell(f'{prefix}ungmute'), cell('Buka global mute user')],
                    [cell(f'{prefix}gmutelist'), cell('Lihat daftar global mute')],
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
