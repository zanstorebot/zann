from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from command import story_cmd
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)

__MODULES__ = "Story"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Story</b>
`{0}story post` (balas media) : Unggah media ke Telegram Story
`{0}story cek` : Lihat semua story pada akunmu
`{0}story del` (ID story) : Hapus story
`{0}story get` (URL) : Ambil story dari user lain
</blockquote>"""


@CMD.UBOT("story")
async def _(client, message):
    return await story_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Story"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}story post'), cell('Unggah media ke Telegram Story')],
                    [cell(f'{prefix}story cek'), cell('Lihat semua story pada akunmu')],
                    [cell(f'{prefix}story del'), cell('Hapus story')],
                    [cell(f'{prefix}story get'), cell('Ambil story dari user lain')],
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
