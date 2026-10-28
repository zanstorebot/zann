from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from command import sosmed_cmd
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)

__MODULES__ = "Sosmed"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Sosmed</b>
`{0}sosmed` (kata kunci) : Cari media sosial

Platform: Pinterest, TikTok, Spotify, YouTube
</blockquote>"""


@CMD.UBOT("sosmed")
async def _(client, message):
    return await sosmed_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Sosmed"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}sosmed'), cell('Cari media sosial')],
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
