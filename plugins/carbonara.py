from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import carbon_cmd
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
IS_PRO = True

__MODULES__ = "Carbon"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Carbon</b>
`{0}carbon` (balas teks) : Buat gambar kode Carbon
</blockquote>"""


@CMD.UBOT("carbon|carbonara")
async def _(client, message):
    return await carbon_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Carbon"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}carbon'), cell('Buat gambar kode Carbon')],
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
