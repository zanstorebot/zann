from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import stalking_cmd
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
IS_PRO = True

__MODULES__ = "Stalking"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Stalk</b>
`{0}stalkig` (nama/username) : Cari informasi akun Instagram
`{0}stalktt` (nama/username) : Cari informasi akun TikTok
`{0}stalktw` (nama/username) : Cari informasi akun Twitter/X
`{0}stalkyt` (nama/username) : Cari informasi akun YouTube
</blockquote>"""


@CMD.UBOT("stalkig|stalktt|stalktw|stalkyt")
async def _(client, message):
    return await stalking_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Stalk"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}stalkig'), cell('Cari informasi akun Instagram')],
                    [cell(f'{prefix}stalktt'), cell('Cari informasi akun TikTok')],
                    [cell(f'{prefix}stalktw'), cell('Cari informasi akun Twitter/X')],
                    [cell(f'{prefix}stalkyt'), cell('Cari informasi akun YouTube')],
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
