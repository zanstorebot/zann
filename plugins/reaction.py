from helpers.rich_footer import footer_table
from pyrogram.types import RichTextBold
from helpers.emoprem import emo
from command import react2_cmd, react_cmd
from helpers import CMD
from pyrogram.enums import ButtonStyle
from pyrogram.types import InlineKeyboardMarkup
from pyrogram.helpers import (ikb, RichMessageBuilder, divider, details, table, cell)
__MODULES__ = "Reaction"
__HELP__ = """<blockquote>Your Prefix/CMD: {0}

<b>Perintah Reaction</b>
`{0}react` (chatid) (emoji/random) : Beri reaksi ke chat
`{0}react2` (balas pesan) (emoji/random) : Beri banyak reaksi
`{0}cancel` (taskid) : Hentikan tugas reaksi
</blockquote>"""


@CMD.UBOT("react")
@CMD.FAKEDEV("react")
@CMD.DEV_CMD("react")
async def _(client, message):
    return await react_cmd(client, message)


@CMD.UBOT("react2")
@CMD.FAKEDEV("react2")
@CMD.DEV_CMD("react2")
async def _(client, message):
    return await react2_cmd(client, message)


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
            [emo(5242278610089304739, "🤖"), " Perintah Reaction"],
            table(
                [
                    [cell("Perintah"), cell("Keterangan")],
                    [cell(f'{prefix}react'), cell('Beri reaksi ke chat')],
                    [cell(f'{prefix}react2'), cell('Beri banyak reaksi')],
                    [cell(f'{prefix}cancel'), cell('Hentikan tugas reaksi')],
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
