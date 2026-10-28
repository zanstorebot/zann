from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import spam_cmd, spamg_cmd
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Spam"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Spam</b>
`{0}dspam` (balas pesan) (jumlah) (jeda) : Kirim spam dengan jeda
`{0}spam` (balas pesan) (jumlah) : Kirim spam tanpa jeda
`{0}spamg` (jumlah) (teks/balas pesan) : Kirim spam broadcast
`{0}cancel` (taskid) : Hentikan tugas spam
</blockquote>"""


@CMD.UBOT("spam|dspam")
async def _(client, message):
    return await spam_cmd(client, message)


@CMD.UBOT("spamg")
async def _(client, message):
    return await spamg_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Spam"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}dspam'), cell('Kirim spam dengan jeda')],
                    [cell(f'{prefix}spam'), cell('Kirim spam tanpa jeda')],
                    [cell(f'{prefix}spamg'), cell('Kirim spam broadcast')],
                    [cell(f'{prefix}cancel'), cell('Hentikan tugas spam')],
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
