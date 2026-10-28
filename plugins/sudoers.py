from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import addsudo_cmd, delsudo_cmd, sudolist_cmd
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Sudoers"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Sudo</b>
`{0}addsudo` (username/balas user) : Tambahkan user sebagai sudo
`{0}delsudo` (username/balas user) : Hapus user dari sudo
`{0}sudolist` : Lihat daftar sudo
`{0}delsudo all` : Hapus seluruh daftar sudo
</blockquote>"""


@CMD.UBOT("addsudo")
async def _(client, message):
    return await addsudo_cmd(client, message)


@CMD.UBOT("delsudo")
async def _(client, message):
    return await delsudo_cmd(client, message)


@CMD.UBOT("sudolist|listsudo")
async def _(client, message):
    return await sudolist_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Sudo"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}addsudo'), cell('Tambahkan user sebagai sudo')],
                    [cell(f'{prefix}delsudo'), cell('Hapus user dari sudo')],
                    [cell(f'{prefix}sudolist'), cell('Lihat daftar sudo')],
                    [cell(f'{prefix}delsudo all'), cell('Hapus seluruh daftar sudo')],
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
