from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import pantun_cmd
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
IS_PRO = True

__MODULES__ = "Pantun"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Pantun dan Teks</b>
Tema: `percintaan`, `bijak`, `masa depan`, `motivasi`, `jenaka`, `nasihat`, `agama`, `random`

`{0}pantun` (tema) : Buat pantun
`{0}tebakan` (tema) : Buat tebak-tebakan
`{0}lelucon` (tema) : Buat lelucon
`{0}quotes` (tema) : Buat quotes
`{0}puisi` (tema) : Buat puisi
</blockquote>"""


@CMD.UBOT("pantun|tebakan|lelucon|puisi|quotes")
async def _(client, message):
    return await pantun_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Pantun dan Teks"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell('percintaan | bijak | masa depan | motivasi | jenaka | nasihat | agama | random'), cell('-')],
                    [cell(f'{prefix}pantun'), cell('Buat pantun')],
                    [cell(f'{prefix}tebakan'), cell('Buat tebak-tebakan')],
                    [cell(f'{prefix}lelucon'), cell('Buat lelucon')],
                    [cell(f'{prefix}quotes'), cell('Buat quotes')],
                    [cell(f'{prefix}puisi'), cell('Buat puisi')],
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
