from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import autoread_cmd
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from helpers import CMD
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
IS_PRO = True

__MODULES__ = "Autoread"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Auto Read</b>
`{0}autoread group` (on/off) : Atur auto-read pesan grup
`{0}autoread private` (on/off) : Atur auto-read pesan pribadi
`{0}autoread channel` (on/off) : Atur auto-read pesan channel
`{0}autoread bot` (on/off) : Atur auto-read pesan bot
`{0}autoread tag` (on/off) : Atur auto-read pesan mention
`{0}autoread all` (on/off) : Atur auto-read semua pesan
`{0}autoread time` (detik) : Atur jeda auto-read
`{0}autoread status` : Lihat status auto-read
</blockquote>"""


@CMD.UBOT("autoread")
async def _(client, message):
    return await autoread_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Auto Read"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}autoread group'), cell('Atur auto-read pesan grup')],
                    [cell(f'{prefix}autoread private'), cell('Atur auto-read pesan pribadi')],
                    [cell(f'{prefix}autoread channel'), cell('Atur auto-read pesan channel')],
                    [cell(f'{prefix}autoread bot'), cell('Atur auto-read pesan bot')],
                    [cell(f'{prefix}autoread tag'), cell('Atur auto-read pesan mention')],
                    [cell(f'{prefix}autoread all'), cell('Atur auto-read semua pesan')],
                    [cell(f'{prefix}autoread time'), cell('Atur jeda auto-read')],
                    [cell(f'{prefix}autoread status'), cell('Lihat status auto-read')],
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
